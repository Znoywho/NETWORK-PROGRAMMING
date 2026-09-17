using System;
using System.Text.Json;
using System.Threading.Tasks;

namespace CaroClient.Core
{
    /// <summary>
    /// Lớp nghiệp vụ: chuyển các thao tác của người chơi thành message JSON theo
    /// Shared/message-schema.json và phân phối message nhận được thành event.
    /// </summary>
    public class GameClient
    {
        private readonly CaroConnection _connection;
        private static readonly JsonSerializerOptions JsonOptions = new()
        {
            PropertyNameCaseInsensitive = true
        };

        public event Action<AuthResultMessage>? OnLoginSucceeded;
        public event Action<AuthResultMessage>? OnUserCreated;
        public event Action<GameStateMessage>? OnGameStateReceived;
        public event Action<GameResultMessage>? OnGameResultReceived;
        public event Action<OnlinePlayersMessage>? OnOnlinePlayersReceived;
        public event Action<InviteReceivedMessage>? OnInviteReceived;
        public event Action<InviteResultMessage>? OnInviteResult;
        public event Action<InviteRejectedMessage>? OnInviteRejected;
        public event Action<LeaveRoomResultMessage>? OnLeaveRoomResult;
        public event Action<ErrorMessage>? OnErrorReceived;

        /// <summary>PlayerId do server cấp sau khi login thành công.</summary>
        public string? PlayerId { get; private set; }

        /// <summary>Username đã đăng nhập.</summary>
        public string? Username { get; private set; }

        public GameClient(CaroConnection connection)
        {
            _connection = connection;
            _connection.MessageReceived += HandleIncomingMessage;
        }

        public async Task ConnectAsync(string uri)
        {
            await _connection.ConnectAsync(new Uri(uri));
        }

        public Task LoginAsync(string username, string password)
            => SendAsync(new LoginMessage { Username = username, Password = password });

        public Task CreateUserAsync(string username, string password)
            => SendAsync(new CreateUserMessage { Username = username, Password = password });

        public Task GetOnlinePlayersAsync()
            => SendAsync(new GetOnlinePlayersMessage());

        public Task SendInviteAsync(string toPlayerId, string inviteId)
            => SendAsync(new InviteMessage { ToPlayerId = toPlayerId, InviteId = inviteId });

        public Task AcceptInviteAsync(string inviteId)
            => SendAsync(new AcceptInviteMessage { InviteId = inviteId });

        public Task RejectInviteAsync(string inviteId, string? reason = null)
            => SendAsync(new RejectInviteMessage { InviteId = inviteId, Reason = reason });

        public Task MakeMoveAsync(string roomId, string playerId, int row, int col)
            => SendAsync(new MakeMoveMessage
            {
                RoomId = roomId,
                PlayerId = playerId,
                Row = row,
                Col = col
            });

        public Task SpectateAsync(string roomId)
            => SendAsync(new SpectateMessage { RoomId = roomId });

        public Task LeaveRoomAsync(string roomId)
            => SendAsync(new LeaveRoomMessage { RoomId = roomId });

        private Task SendAsync<T>(T message)
        {
            string json = JsonSerializer.Serialize(message, JsonOptions);
            return _connection.SendAsync(json);
        }

        private void HandleIncomingMessage(string json)
        {
            try
            {
                using var doc = JsonDocument.Parse(json);
                if (!doc.RootElement.TryGetProperty("type", out var typeElement))
                {
                    return;
                }

                string type = typeElement.GetString() ?? "";

                switch (type)
                {
                    case "login":
                        var login = Deserialize<AuthResultMessage>(json);
                        if (login != null)
                        {
                            PlayerId = login.PlayerId;
                            Username = login.Username;
                            OnLoginSucceeded?.Invoke(login);
                        }
                        break;

                    case "create_user":
                        var created = Deserialize<AuthResultMessage>(json);
                        if (created != null) OnUserCreated?.Invoke(created);
                        break;

                    case "game_state":
                        var state = Deserialize<GameStateMessage>(json);
                        if (state != null) OnGameStateReceived?.Invoke(state);
                        break;

                    case "game_result":
                        var result = Deserialize<GameResultMessage>(json);
                        if (result != null) OnGameResultReceived?.Invoke(result);
                        break;

                    case "online_players":
                        var players = Deserialize<OnlinePlayersMessage>(json);
                        if (players != null) OnOnlinePlayersReceived?.Invoke(players);
                        break;

                    // Server gửi lời mời với type "invite" (không phải "invite_received").
                    case "invite":
                        var invite = Deserialize<InviteReceivedMessage>(json);
                        if (invite != null) OnInviteReceived?.Invoke(invite);
                        break;

                    case "invite_result":
                        var inviteResult = Deserialize<InviteResultMessage>(json);
                        if (inviteResult != null) OnInviteResult?.Invoke(inviteResult);
                        break;

                    case "invite_rejected":
                        var rejected = Deserialize<InviteRejectedMessage>(json);
                        if (rejected != null) OnInviteRejected?.Invoke(rejected);
                        break;

                    case "leave_room_result":
                        var leave = Deserialize<LeaveRoomResultMessage>(json);
                        if (leave != null) OnLeaveRoomResult?.Invoke(leave);
                        break;

                    case "error":
                        var error = Deserialize<ErrorMessage>(json);
                        if (error != null) OnErrorReceived?.Invoke(error);
                        break;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[GameClient] Lỗi phân tích JSON: {ex.Message}");
            }
        }

        private static T? Deserialize<T>(string json) => JsonSerializer.Deserialize<T>(json, JsonOptions);
    }
}
