using System.Net.WebSockets;
using System.Text;

namespace CaroClient.Core;

public sealed class CaroConnection : IAsyncDisposable
{
    private readonly ClientWebSocket _socket = new();
    private CancellationTokenSource? _receiveLoopCts;
    private Task? _receiveLoopTask;

    // event để UI/console đăng ký nghe, mỗi khi có message mới từ server thì báo ra ngoài
    public event Action<string>? MessageReceived;

    // báo khi bị mất kết nối bất ngờ (server tắt, mất mạng...)
    public event Action<string>? Disconnected;

    public bool IsConnected => _socket.State == WebSocketState.Open;

    public async Task ConnectAsync(Uri serverUri, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(serverUri);
        if (_socket.State != WebSocketState.None)
        {
            throw new InvalidOperationException("Kết nối này đã mở hoặc đã đóng rồi, tạo CaroConnection mới đi.");
        }

        await _socket.ConnectAsync(serverUri, cancellationToken);

        _receiveLoopCts = new CancellationTokenSource();
        _receiveLoopTask = ReceiveLoopAsync(_receiveLoopCts.Token);
    }

    public async Task SendAsync(string jsonMessage, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(jsonMessage))
        {
            throw new ArgumentException("Không được gửi message rỗng.", nameof(jsonMessage));
        }

        if (!IsConnected)
        {
            throw new InvalidOperationException("Chưa kết nối server mà đòi gửi message.");
        }
        byte[] data = Encoding.UTF8.GetBytes(jsonMessage);

        await _socket.SendAsync(
            new ArraySegment<byte>(data),
            WebSocketMessageType.Text,
            endOfMessage: true,
            cancellationToken);
    }

    private async Task ReceiveLoopAsync(CancellationToken cancellationToken)
    {
        var buffer = new byte[8192];

        try
        {          
            while (_socket.State == WebSocketState.Open && !cancellationToken.IsCancellationRequested)
            {
                using var messageStream = new MemoryStream();
                WebSocketReceiveResult result;
                do
                {
                    result = await _socket.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationToken);

                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        await _socket.CloseAsync(
                            WebSocketCloseStatus.NormalClosure, "Server yêu cầu đóng", cancellationToken);
                        Disconnected?.Invoke("Server đã đóng kết nối.");
                        return;
                    }

                    messageStream.Write(buffer, 0, result.Count);
                }
                while (!result.EndOfMessage);

                string json = Encoding.UTF8.GetString(messageStream.ToArray());

                if (!string.IsNullOrWhiteSpace(json))
                {
                    MessageReceived?.Invoke(json);
                }
            }
        }
        catch (OperationCanceledException)
        {
            
        }
        catch (WebSocketException ex)
        {
            // trường hợp này là mất mạng (ví dụ rút dây mạng giữa chừng)
            Disconnected?.Invoke($"Mất kết nối bất ngờ: {ex.Message}");
        }
    }

    public async Task DisconnectAsync()
    {
        _receiveLoopCts?.Cancel();

        if (_socket.State == WebSocketState.Open)
        {
            await _socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Client tự đóng kết nối", CancellationToken.None);
        }

        if (_receiveLoopTask is not null)
        {
            try
            {
                await _receiveLoopTask;
            }
            catch (OperationCanceledException)
            {
             
            }
        }
    }

    public async ValueTask DisposeAsync()
    {
        await DisconnectAsync();
        _socket.Dispose();
        _receiveLoopCts?.Dispose();
    }
}