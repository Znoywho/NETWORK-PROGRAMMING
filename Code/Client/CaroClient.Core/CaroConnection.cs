using System.Net.Sockets;
using System.Text;

namespace CaroClient.Core;

/// <summary>
/// Kết nối TCP gửi và nhận các message JSON UTF-8, mỗi message kết thúc bằng \n.
/// </summary>
public sealed class CaroConnection : IAsyncDisposable
{
    private readonly TcpClient _client = new();
    private readonly SemaphoreSlim _sendLock = new(1, 1);
    private NetworkStream? _stream;
    private CancellationTokenSource? _receiveLoopCts;
    private Task? _receiveLoopTask;

    public event Action<string>? MessageReceived;
    public event Action<string>? Disconnected;

    public bool IsConnected => _client.Connected && _stream is not null;

    public async Task ConnectAsync(Uri serverUri, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(serverUri);

        if (IsConnected)
        {
            throw new InvalidOperationException("Kết nối đã mở.");
        }

        if (!serverUri.Scheme.Equals("tcp", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("Địa chỉ server phải có dạng tcp://host:port.", nameof(serverUri));
        }

        int port = serverUri.Port > 0 ? serverUri.Port : 8765;
        await _client.ConnectAsync(serverUri.Host, port, cancellationToken);

        _stream = _client.GetStream();
        _receiveLoopCts = new CancellationTokenSource();
        _receiveLoopTask = ReceiveLoopAsync(_receiveLoopCts.Token);
    }

    public async Task SendAsync(string jsonMessage, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(jsonMessage);

        if (!IsConnected || _stream is null)
        {
            throw new InvalidOperationException("Chưa kết nối TCP tới server.");
        }

        byte[] data = Encoding.UTF8.GetBytes(jsonMessage + "\n");

        await _sendLock.WaitAsync(cancellationToken);
        try
        {
            await _stream.WriteAsync(data, cancellationToken);
        }
        finally
        {
            _sendLock.Release();
        }
    }

    private async Task ReceiveLoopAsync(CancellationToken cancellationToken)
    {
        byte[] buffer = new byte[8192];
        var pending = new StringBuilder();

        try
        {
            while (!cancellationToken.IsCancellationRequested && _client.Connected)
            {
                int bytesRead = await _stream!.ReadAsync(buffer.AsMemory(), cancellationToken);
                if (bytesRead == 0)
                {
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
            // Client chủ động đóng kết nối.
        }
        catch (Exception ex)
        {
            Disconnected?.Invoke($"Mất kết nối TCP bất ngờ: {ex.Message}");
        }
    }

    public async Task DisconnectAsync()
    {
        _receiveLoopCts?.Cancel();

        if (_stream is not null)
        {
            await _stream.DisposeAsync();
            _stream = null;
        }

        _client.Dispose();

        if (_receiveLoopTask is not null)
        {
            try
            {
                await _receiveLoopTask;
            }
            catch (OperationCanceledException)
            {
                // Cancellation khi đóng kết nối là bình thường.
            }
        }
    }

    public async ValueTask DisposeAsync()
    {
        await DisconnectAsync();
        _receiveLoopCts?.Dispose();
        _sendLock.Dispose();
    }
}
