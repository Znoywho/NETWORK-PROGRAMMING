using System.Text.Json.Serialization;

namespace CaroClient.Core;

public class LoginMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "login";

    [JsonPropertyName("username")]
    public string Username { get; set; } = string.Empty;

    [JsonPropertyName("playerId")]
    public string? PlayerId { get; set; }
}

public class OnlinePlayersMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "online_players";

    [JsonPropertyName("players")]
    public List<PlayerInfo> Players { get; set; } = new();
}

public class GetOnlinePlayersMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "get_online_players";
}

public class PlayerInfo
{
    [JsonPropertyName("playerId")]
    public string PlayerId { get; set; } = string.Empty;

    [JsonPropertyName("username")]
    public string Username { get; set; } = string.Empty;
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

public class InviteReceivedMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "invite_received";

    [JsonPropertyName("inviteId")]
    public string InviteId { get; set; } = string.Empty;

    [JsonPropertyName("fromPlayerId")]
    public string FromPlayerId { get; set; } = string.Empty;

    [JsonPropertyName("fromUsername")]
    public string FromUsername { get; set; } = string.Empty;
}

public class InviteAcceptedMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "invite_accepted";

    [JsonPropertyName("inviteId")]
    public string InviteId { get; set; } = string.Empty;

    [JsonPropertyName("matchId")]
    public string MatchId { get; set; } = string.Empty;

    [JsonPropertyName("playerXId")]
    public string PlayerXId { get; set; } = string.Empty;

    [JsonPropertyName("playerOId")]
    public string PlayerOId { get; set; } = string.Empty;
}

public class InviteRejectedMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "invite_rejected";

    [JsonPropertyName("inviteId")]
    public string InviteId { get; set; } = string.Empty;

    [JsonPropertyName("reason")]
    public string? Reason { get; set; }
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
    public string? Reason { get; set; }
}

public class MakeMoveMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "make_move";

    [JsonPropertyName("matchId")]
    public string MatchId { get; set; } = string.Empty;

    [JsonPropertyName("playerId")]
    public string PlayerId { get; set; } = string.Empty;

    [JsonPropertyName("row")]
    public int Row { get; set; }

    [JsonPropertyName("col")]
    public int Col { get; set; }
}

public class GameStateMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "game_state";

    [JsonPropertyName("matchId")]
    public string MatchId { get; set; } = string.Empty;

    [JsonPropertyName("board")]
    public int[][] Board { get; set; } = Array.Empty<int[]>();

    [JsonPropertyName("currentPlayerId")]
    public string CurrentPlayerId { get; set; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;
}

public class GameResultMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "game_result";

    [JsonPropertyName("matchId")]
    public string MatchId { get; set; } = string.Empty;

    [JsonPropertyName("result")]
    public string Result { get; set; } = string.Empty;

    [JsonPropertyName("winnerId")]
    public string? WinnerId { get; set; }
}

public class SpectateMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "spectate";

    [JsonPropertyName("matchId")]
    public string MatchId { get; set; } = string.Empty;
}

public class LeaveRoomMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "leave_room";

    [JsonPropertyName("matchId")]
    public string MatchId { get; set; } = string.Empty;
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
