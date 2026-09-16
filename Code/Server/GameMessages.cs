using System;
using System.Text.Json.Serialization;

namespace CaroClient.Core
{
    public class BaseMessage
    {
        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;
    }
//Gói tin Client gửi lên Server để Login
    public class LoginMessage : BaseMessage
    {
        [JsonPropertyName("playerId")]
        public string PlayerId { get; set; } = string.Empty;

        public LoginMessage()
        {
            Type = "login";
        }
    }
    //Gói tin Client gửi lên Server khi đánh 1 nước cờ
    public class MakeMoveMessage : BaseMessage
    {
        [JsonPropertyName("matchId")]
        public string MatchId { get; set; } = string.Empty;

        [JsonPropertyName("playerId")]
        public string PlayerId { get; set; } = string.Empty;

        [JsonPropertyName("row")]
        public int Row { get; set; }

        [JsonPropertyName("col")]
        public int Col { get; set; }

        public MakeMoveMessage()
        {
            Type = "make_move";
        }
    }
    //Gói tin Server gửi về Client để cập nhật bàn cờ 
    public class GameStateMessage : BaseMessage
    {
        [JsonPropertyName("matchId")]
        public string MatchId { get; set; } = string.Empty;

        [JsonPropertyName("board")]
        public int[][] Board { get; set; } = Array.Empty<int[]>();

        [JsonPropertyName("currentTurn")]
        public string CurrentTurn { get; set; } = string.Empty;
        public GameStateMessage()
        {
            Type = "game_state";
        }
    }
    //Gói tin Server gửi về bảo kết quả thắng, thua, hòa
    public class GameResultMessage : BaseMessage
    {
        [JsonPropertyName("matchId")]
        public string MatchId { get; set; } = string.Empty;
        
        [JsonPropertyName("winnerId")]
        public string? WinnerId { get; set; }

        [JsonPropertyName("result")]
        public string Result { get; set; } = string.Empty;

        public GameResultMessage()
        {
            Type = "game_result";
        }
    }

}

