using System;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace CaroClient.Core
{
    public class CaroConnection
    {
        private ClientWebSocket _client;
        private CancellationTokenSource _cts;

        public CaroConnection()
        {
            _client = new ClientWebSocket();
            _cts = new CancellationTokenSource();
        }
    public async Task ConnectAsync(string serverUrl)
    {
            try
            {
                Uri serverUri = new Uri(serverUrl);
                await _client.ConnectAsync(serverUri, _cts.Token);
                Console.Writeline("Đã kết nối thành công tới Server WebSocket.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Lỗi kết nối: {ex.Message}");
                throw;
            }
    }
    public async Task<string> ReceiveAsync()
    {
            if (_client.State != WebSocketState.Open)
            {
                return string.Empty;
            }

            byte[] buffer = new byte[4096];
            var result = await _client.ReceiveAsync(new AraySegment<byte>(buffer), _cts.Token);

            if (result.MessageType == WebSocketMessageType.Close)
            {
                await DisconnectAsync();
                return string.Empty;
            }
            string decoded = Encoding.UTF8.GetString(bufer, 0, result.Count);
            return decoded;
    }
    public async Task DisconnectAsync()
        {
            if (_client.State == WebSocketState.Open)
            {
                await _client.CloseAsync(WebsocketCloseStatus.NorMalClosure, "Client chủ động đóng", _cts.Token);
                Cononsole.WriteLine("Đã đóng kết nối")
            }    
        }
    }
}