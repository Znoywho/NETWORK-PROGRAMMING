using System;
using System.Text.Json;
using System.Threading.Tasks;

namespace CaroClient.Core
{
    public class GameClient
    {
        private readonly CaroConnection _connection;
        private static readonly JsonSerializerOptions JsonOptions = new()
        {
            PropertyNameCaseInsensitive = true
        };

        public event Action<GameStateMessage>? OnGameStateReceived;
        public event Action<GameResultMessage>? OnGameResultReceived;
        public event Action<OnlinePlayersMessage>? OnOnlinePlayersReceived;
        public event Action<InviteReceivedMessage>? OnInviteReceived;
        public event Action<InviteAcceptedMessage>? OnInviteAccepted;
        public event Action<InviteRejectedMessage>? OnInviteRejected;
        public event Action<string>? OnErrorReceived;

        public GameClient(CaroConnection connection)
        {
            _connection = connection;
            _connection.MessageReceived += HandleIncomingMessage;
        }

        public async Task ConnectAsync(string uri)
        {
            await _connection.ConnectAsync(new Uri(uri));
        }

        public async Task LoginAsync(string username, string? playerId = null)
        {
            var msg = new LoginMessage
            {
                Username = username,
                PlayerId = playerId
            };

            string json = JsonSerializer.Serialize(msg, JsonOptions);
            await _connection.SendAsync(json);
        }

        public async Task MakeMoveAsync(string matchId, string playerId, int row, int col)
        {
            var msg = new MakeMoveMessage
            {
                MatchId = matchId,
                PlayerId = playerId,
                Row = row,
                Col = col
            };

            string json = JsonSerializer.Serialize(msg, JsonOptions);
            await _connection.SendAsync(json);
        }

        public async Task SendInviteAsync(string toPlayerId, string inviteId)
        {
            var msg = new InviteMessage
            {
                ToPlayerId = toPlayerId,
                InviteId = inviteId
            };

            string json = JsonSerializer.Serialize(msg, JsonOptions);
            await _connection.SendAsync(json);
        }

        public async Task GetOnlinePlayersAsync()
        {
            string json = JsonSerializer.Serialize(new GetOnlinePlayersMessage(), JsonOptions);
            await _connection.SendAsync(json);
        }

        public async Task AcceptInviteAsync(string inviteId)
        {
            var msg = new AcceptInviteMessage { InviteId = inviteId };
            string json = JsonSerializer.Serialize(msg, JsonOptions);
            await _connection.SendAsync(json);
        }

        public async Task RejectInviteAsync(string inviteId, string? reason = null)
        {
            var msg = new RejectInviteMessage
            {
                InviteId = inviteId,
                Reason = reason
            };

            string json = JsonSerializer.Serialize(msg, JsonOptions);
            await _connection.SendAsync(json);
        }

        private void HandleIncomingMessage(string json)
        {
            try
            {
                using var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;

                if (!root.TryGetProperty("type", out var typeElement))
                {
                    return;
                }

                string type = typeElement.GetString() ?? "";

                switch (type)
                {
                    case "game_state":
                        var stateMsg = JsonSerializer.Deserialize<GameStateMessage>(json, JsonOptions);
                        if (stateMsg != null) OnGameStateReceived?.Invoke(stateMsg);
                        break;

                    case "game_result":
                        var resultMsg = JsonSerializer.Deserialize<GameResultMessage>(json, JsonOptions);
                        if (resultMsg != null) OnGameResultReceived?.Invoke(resultMsg);
                        break;

                    case "online_players":
                        var playersMsg = JsonSerializer.Deserialize<OnlinePlayersMessage>(json, JsonOptions);
                        if (playersMsg != null) OnOnlinePlayersReceived?.Invoke(playersMsg);
                        break;

                    case "invite_received":
                        var inviteMsg = JsonSerializer.Deserialize<InviteReceivedMessage>(json, JsonOptions);
                        if (inviteMsg != null) OnInviteReceived?.Invoke(inviteMsg);
                        break;

                    case "invite_accepted":
                        var acceptedMsg = JsonSerializer.Deserialize<InviteAcceptedMessage>(json, JsonOptions);
                        if (acceptedMsg != null) OnInviteAccepted?.Invoke(acceptedMsg);
                        break;

                    case "invite_rejected":
                        var rejectedMsg = JsonSerializer.Deserialize<InviteRejectedMessage>(json, JsonOptions);
                        if (rejectedMsg != null) OnInviteRejected?.Invoke(rejectedMsg);
                        break;

                    case "error":
                        if (root.TryGetProperty("message", out var msgElement))
                        {
                            OnErrorReceived?.Invoke(msgElement.GetString() ?? "Lỗi không xác định từ Server");
                        }
                        break;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[GameClient] Lỗi phân tích JSON: {ex.Message}");
            }
        }
    }
}
