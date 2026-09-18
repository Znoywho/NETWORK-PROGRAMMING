using System.Text.Json.Serialization;

namespace CaroClient.Core;

// ===== Client -> Server =====

public class LoginMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "login";

    [JsonPropertyName("username")]
    public string Username { get; set; } = string.Empty;

    [JsonPropertyName("password")]
    public string Password { get; set; } = string.Empty;
}

public class CreateUserMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "create_user";

    [JsonPropertyName("username")]
    public string Username { get; set; } = string.Empty;

    [JsonPropertyName("password")]
    public string Password { get; set; } = string.Empty;
}

public class GetOnlinePlayersMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "online_players";
}

public class InviteMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "invite";

    [JsonPropertyName("toPlayerId")]
    public string ToPlayerId { get; set; } = string.Empty;

    [JsonPropertyName("inviteId")]
    public string InviteId { get; set; } = string.Empty;
}

public class AcceptInviteMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "accept_invite";

    [JsonPropertyName("inviteId")]
    public string InviteId { get; set; } = string.Empty;
}

public class RejectInviteMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "reject_invite";

    [JsonPropertyName("inviteId")]
    public string InviteId { get; set; } = string.Empty;

    [JsonPropertyName("reason")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Reason { get; set; }
}

public class MakeMoveMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "make_move";

    [JsonPropertyName("room_id")]
    public string RoomId { get; set; } = string.Empty;

    [JsonPropertyName("playerId")]
    public string PlayerId { get; set; } = string.Empty;

    [JsonPropertyName("row")]
    public int Row { get; set; }

    [JsonPropertyName("col")]
    public int Col { get; set; }
}

/// <summary>Xin danh sách các trận đang diễn ra để chọn phòng khán giả.</summary>
public class GetMatchListMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "match_list";
}

public class SpectateMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "spectate";

    [JsonPropertyName("room_id")]
    public string RoomId { get; set; } = string.Empty;
}

public class LeaveRoomMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "leave_room";

    [JsonPropertyName("room_id")]
    public string RoomId { get; set; } = string.Empty;
}

// ===== Server -> Client =====

/// <summary>Server trả về sau khi login hoặc create_user thành công.</summary>
public class AuthResultMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("username")]
    public string Username { get; set; } = string.Empty;

    [JsonPropertyName("playerId")]
    public string PlayerId { get; set; } = string.Empty;
}

public class OnlinePlayersMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "online_players";

    [JsonPropertyName("players")]
    public List<PlayerInfo> Players { get; set; } = new();
}

public class PlayerInfo
{
    [JsonPropertyName("playerId")]
    public string PlayerId { get; set; } = string.Empty;

    [JsonPropertyName("username")]
    public string Username { get; set; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;
}

/// <summary>Lời mời do người chơi khác gửi tới (server gửi type "invite").</summary>
public class InviteReceivedMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "invite";

    [JsonPropertyName("inviteId")]
    public string InviteId { get; set; } = string.Empty;

    [JsonPropertyName("fromPlayerId")]
    public string FromPlayerId { get; set; } = string.Empty;

    [JsonPropertyName("fromUsername")]
    public string FromUsername { get; set; } = string.Empty;
}

/// <summary>Xác nhận cho chính người gửi lời mời.</summary>
public class InviteResultMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "invite_result";

    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("inviteId")]
    public string InviteId { get; set; } = string.Empty;

    [JsonPropertyName("toPlayerId")]
    public string ToPlayerId { get; set; } = string.Empty;
}

/// <summary>Người được mời đã từ chối.</summary>
public class InviteRejectedMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "invite_rejected";

    [JsonPropertyName("inviteId")]
    public string InviteId { get; set; } = string.Empty;

    [JsonPropertyName("byPlayerId")]
    public string ByPlayerId { get; set; } = string.Empty;
}

/// <summary>Danh sách trận đang diễn ra, dùng cho màn hình chọn phòng xem.</summary>
public class MatchListMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "match_list";

    [JsonPropertyName("matches")]
    public List<MatchSummary> Matches { get; set; } = new();
}

public class MatchSummary
{
    [JsonPropertyName("room_id")]
    public string RoomId { get; set; } = string.Empty;

    [JsonPropertyName("playerXId")]
    public string PlayerXId { get; set; } = string.Empty;

    [JsonPropertyName("playerXName")]
    public string PlayerXName { get; set; } = string.Empty;

    [JsonPropertyName("playerOId")]
    public string PlayerOId { get; set; } = string.Empty;

    [JsonPropertyName("playerOName")]
    public string PlayerOName { get; set; } = string.Empty;

    [JsonPropertyName("spectatorCount")]
    public int SpectatorCount { get; set; }

    [JsonPropertyName("moveCount")]
    public int MoveCount { get; set; }

    [JsonPropertyName("turnTimeLeft")]
    public int TurnTimeLeft { get; set; }
}

/// <summary>
/// Một người chơi mất kết nối. Ván CHƯA kết thúc: đồng hồ suy nghĩ tạm dừng
/// và họ còn <see cref="ReconnectTimeLeft"/> giây để đăng nhập lại.
/// </summary>
public class PlayerDisconnectedMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "player_disconnected";

    [JsonPropertyName("room_id")]
    public string RoomId { get; set; } = string.Empty;

    [JsonPropertyName("playerId")]
    public string PlayerId { get; set; } = string.Empty;

    [JsonPropertyName("reconnectTimeLeft")]
    public int ReconnectTimeLeft { get; set; }
}

/// <summary>Người mất kết nối đã quay lại kịp hạn; server gửi kèm game_state mới.</summary>
public class PlayerReconnectedMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "player_reconnected";

    [JsonPropertyName("room_id")]
    public string RoomId { get; set; } = string.Empty;

    [JsonPropertyName("playerId")]
    public string PlayerId { get; set; } = string.Empty;
}

public class GameStateMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "game_state";

    [JsonPropertyName("room_id")]
    public string RoomId { get; set; } = string.Empty;

    [JsonPropertyName("board")]
    public int[][] Board { get; set; } = Array.Empty<int[]>();

    [JsonPropertyName("currentPlayerId")]
    public string CurrentPlayerId { get; set; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    /// <summary>Tổng thời gian suy nghĩ của một lượt, tính bằng giây.</summary>
    [JsonPropertyName("turnTimeLimit")]
    public int TurnTimeLimit { get; set; }

    /// <summary>Số giây còn lại của lượt hiện tại; client tự đếm ngược từ mốc này.</summary>
    [JsonPropertyName("turnTimeLeft")]
    public int TurnTimeLeft { get; set; }

    /// <summary>Khác null khi phòng đang chờ một người chơi kết nối lại.</summary>
    [JsonPropertyName("waitingForPlayerId")]
    public string? WaitingForPlayerId { get; set; }

    [JsonPropertyName("reconnectTimeLeft")]
    public int? ReconnectTimeLeft { get; set; }
}

public class GameResultMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "game_result";

    [JsonPropertyName("room_id")]
    public string RoomId { get; set; } = string.Empty;

    [JsonPropertyName("result")]
    public string Result { get; set; } = string.Empty;

    [JsonPropertyName("winnerId")]
    public string? WinnerId { get; set; }

    /// <summary>timeout | disconnect | forfeit. Null nghĩa là thắng thua bình thường trên bàn cờ.</summary>
    [JsonPropertyName("reason")]
    public string? Reason { get; set; }
}

public class LeaveRoomResultMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "leave_room_result";

    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("winnerId")]
    public string? WinnerId { get; set; }
}

public class ErrorMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "error";

    [JsonPropertyName("code")]
    public string Code { get; set; } = string.Empty;

    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;

    [JsonPropertyName("details")]
    public object? Details { get; set; }
}
