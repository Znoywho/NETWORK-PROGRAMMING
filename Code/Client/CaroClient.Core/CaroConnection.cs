using System.Net.Sockets;
using System.Text;

namespace CaroClient.Core;

/// <summary>
/// Kết nối TCP gửi và nhận các message JSON UTF-8, mỗi message kết thúc bằng \n.
/// </summary>
public sealed class CaroConnection : IAsyncDisposable
{
    private readonly SemaphoreSlim _sendLock = new(1, 1);
    private readonly SemaphoreSlim _reconnectLock = new(1, 1);
    private TcpClient? _client;
    private NetworkStream? _stream;
    private CancellationTokenSource? _receiveLoopCts;
    private Task? _receiveLoopTask;
    private Uri? _serverUri;

    public event Action<string>? MessageReceived;
    public event Action<string>? Disconnected;
    public event Action? Reconnected;

    public bool IsConnected => _client?.Connected == true && _stream is not null;

    public async Task ConnectAsync(Uri serverUri, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(serverUri);
        ValidateServerUri(serverUri);

        if (IsConnected)
        {
            throw new InvalidOperationException("Kết nối đã mở.");
        }

        _serverUri = serverUri;
        await OpenTransportAsync(serverUri, cancellationToken);
    }

    /// <summary>
    /// Thử mở lại kết nối tới endpoint gần nhất. Trả về false khi hết số lần thử.
    /// </summary>
    public async Task<bool> ReconnectAsync(
        int maxAttempts = 3,
        TimeSpan? retryDelay = null,
        CancellationToken cancellationToken = default)
    {
        if (_serverUri is null)
        {
            throw new InvalidOperationException("Chưa có endpoint để kết nối lại.");
        }

        if (maxAttempts < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(maxAttempts));
        }

        TimeSpan delay = retryDelay ?? TimeSpan.FromSeconds(2);
        await _reconnectLock.WaitAsync(cancellationToken);
        try
        {
            if (IsConnected)
            {
                return true;
            }

            CloseTransport();

            for (int attempt = 1; attempt <= maxAttempts; attempt++)
            {
                try
                {
                    await OpenTransportAsync(_serverUri, cancellationToken);
                    Reconnected?.Invoke();
                    return true;
                }
                catch (Exception) when (attempt < maxAttempts && !cancellationToken.IsCancellationRequested)
                {
                    await Task.Delay(delay, cancellationToken);
                }
                catch (Exception) when (!cancellationToken.IsCancellationRequested)
                {
                    CloseTransport();
                }
            }

            return false;
        }
        finally
        {
            _reconnectLock.Release();
        }
    }

    public async Task SendAsync(string jsonMessage, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(jsonMessage);

        TcpClient? client = _client;
        NetworkStream? stream = _stream;
        if (!IsConnected || client is null || stream is null)
        {
            throw new InvalidOperationException("Chưa kết nối TCP tới server.");
        }

        byte[] data = Encoding.UTF8.GetBytes(jsonMessage + "\n");

        await _sendLock.WaitAsync(cancellationToken);
        try
        {
            await stream.WriteAsync(data, cancellationToken);
        }
        catch (Exception ex)
        {
            CloseTransportIfCurrent(client);
            Disconnected?.Invoke($"Mất kết nối TCP khi gửi dữ liệu: {ex.Message}");
            throw;
        }
        finally
        {
            _sendLock.Release();
        }
    }

    public async Task DisconnectAsync()
    {
        CloseTransport();

        Task? receiveLoopTask = _receiveLoopTask;
        if (receiveLoopTask is not null)
        {
            try
            {
                await receiveLoopTask;
            }
            catch (OperationCanceledException)
            {
                // Cancellation khi đóng kết nối là bình thường.
            }
        }
    }

    private async Task OpenTransportAsync(Uri serverUri, CancellationToken cancellationToken)
    {
        var client = new TcpClient();
        try
        {
            int port = serverUri.Port > 0 ? serverUri.Port : 8765;
            await client.ConnectAsync(serverUri.Host, port, cancellationToken);

            NetworkStream stream = client.GetStream();
            var receiveLoopCts = new CancellationTokenSource();

            _client = client;
            _stream = stream;
            _receiveLoopCts = receiveLoopCts;
            _receiveLoopTask = ReceiveLoopAsync(client, stream, receiveLoopCts.Token);
        }
        catch
        {
            client.Dispose();
            throw;
        }
    }

    private async Task ReceiveLoopAsync(TcpClient client, NetworkStream stream, CancellationToken cancellationToken)
    {
        byte[] buffer = new byte[8192];
        var pending = new StringBuilder();

        try
        {
            while (!cancellationToken.IsCancellationRequested && client.Connected)
            {
                int bytesRead = await stream.ReadAsync(buffer.AsMemory(), cancellationToken);
                if (bytesRead == 0)
                {
                    CloseTransportIfCurrent(client);
                    Disconnected?.Invoke("Server đã đóng kết nối TCP.");
                    return;
                }

                pending.Append(Encoding.UTF8.GetString(buffer, 0, bytesRead));

                while (true)
                {
                    int newlineIndex = pending.ToString().IndexOf('\n');
                    if (newlineIndex < 0)
                    {
                        break;
                    }

                    string json = pending.ToString(0, newlineIndex).Trim();
                    pending.Remove(0, newlineIndex + 1);

                    if (!string.IsNullOrWhiteSpace(json))
                    {
                        MessageReceived?.Invoke(json);
                    }
                }
            }
        }
        catch (OperationCanceledException)
        {
            // Client chủ động đóng hoặc đang kết nối lại.
        }
        catch (Exception ex)
        {
            CloseTransportIfCurrent(client);
            Disconnected?.Invoke($"Mất kết nối TCP bất ngờ: {ex.Message}");
        }
    }

    private void CloseTransportIfCurrent(TcpClient client)
    {
        if (ReferenceEquals(_client, client))
        {
            CloseTransport();
        }
    }

    private void CloseTransport()
    {
        _receiveLoopCts?.Cancel();
        _receiveLoopCts?.Dispose();
        _receiveLoopCts = null;

        _stream?.Dispose();
        _stream = null;

        _client?.Dispose();
        _client = null;
    }

    private static void ValidateServerUri(Uri serverUri)
    {
        if (!serverUri.Scheme.Equals("tcp", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("Địa chỉ server phải có dạng tcp://host:port.", nameof(serverUri));
        }
    }

    public async ValueTask DisposeAsync()
    {
        await DisconnectAsync();
        _sendLock.Dispose();
        _reconnectLock.Dispose();
    }
}
