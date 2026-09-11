using System;
using System.Text.Json;
using System.Threading.Tasks;

namespace CaroClient.Core
{
    public class GameClient
    {
        private readonly CaroConnection _connection;

        // Các event để Giao diện (UI) lắng nghe và hiển thị lên màn hình
        public event Action<GameStateMessage>? OnGameStateReceived;
        public event Action<GameResultMessage>? OnGameResultReceived;
        public event Action<string>? OnErrorReceived;

        public GameClient(CaroConnection connection)
        {
            _connection = connection;
            // Đăng ký nghe ngóng: khi có tin nhắn từ Server thì chạy hàm HandleIncomingMessage
            _connection.MessageReceived += HandleIncomingMessage;
        }

        public async Task ConnectAsync(string uri)
        {
            await _connection.ConnectAsync(uri);
        }

        // Hàm gửi gói tin Đăng nhập
        public async Task LoginAsync(string playerId)
        {
            var msg = new LoginMessage { PlayerId = playerId };
            string json = JsonSerializer.Serialize(msg);
            await _connection.SendAsync(json);
        }

        // Hàm gửi gói tin Đánh cờ
        public async Task MakeMoveAsync(string matchId, string playerId, int row, int col)
        {
            var msg = new MakeMoveMessage { MatchId = matchId, PlayerId = playerId, Row = row, Col = col };
            string json = JsonSerializer.Serialize(msg);
            await _connection.SendAsync(json);
        }

        // Hàm Xử lý tin nhắn JSON từ Server đổ về
        private void HandleIncomingMessage(string json)
        {
            try
            {
                // Đọc sơ chuỗi JSON để lấy trường "type"
                using var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;

                if (root.TryGetProperty("type", out var typeElement))
                {
                    string type = typeElement.GetString() ?? "";

                    // Tùy theo type mà dịch ngược (Deserialize) thành class tương ứng
                    switch (type)
                    {
                        case "game_state":
                            var stateMsg = JsonSerializer.Deserialize<GameStateMessage>(json);
                            if (stateMsg != null) OnGameStateReceived?.Invoke(stateMsg);
                            break;
                        case "game_result":
                            var resultMsg = JsonSerializer.Deserialize<GameResultMessage>(json);
                            if (resultMsg != null) OnGameResultReceived?.Invoke(resultMsg);
                            break;
                        case "error":
                            if (root.TryGetProperty("message", out var msgElement))
                            {
                                OnErrorReceived?.Invoke(msgElement.GetString() ?? "Lỗi không xác định từ Server");
                            }
                            break;
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[GameClient] Lỗi phân tích JSON: {ex.Message}");
            }
        }
    }
}