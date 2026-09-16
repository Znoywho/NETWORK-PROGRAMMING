using CaroClient.Core;
using System.Text;

Console.OutputEncoding = System.Text.Encoding.UTF8;

int[][] board = Array.Empty<int[]>();

bool gameEnded = false;

Console.Write("Địa chỉ server (Enter để dùng mặc định tcp://localhost:8765): ");
string? uriInput = Console.ReadLine();

string serverAddress = string.IsNullOrWhiteSpace(uriInput)
    ? "tcp://localhost:8765"
    : uriInput.Trim();

await using var connection = new CaroConnection();
var client = new GameClient(connection);

client.OnGameStateReceived += state =>
{
    board = state.Board;

    Console.WriteLine();
    Console.WriteLine("========================================");
    Console.WriteLine($"[game_state] matchId={state.MatchId}");
    Console.WriteLine($"currentPlayerId: {state.CurrentPlayerId}");
    Console.WriteLine($"status: {state.Status}");
    Console.WriteLine("========================================");

    // Nếu sau này server trả thêm lastMove, có thể truyền vào đây.
    // Hiện tại chưa có lastMove, nên truyền null.
    PrintBoard(board, null);
};

client.OnGameResultReceived += result =>
{
    Console.WriteLine();
    Console.WriteLine("========== KẾT QUẢ TRẬN ĐẤU ==========");

    string text = result.Result switch
    {
        "win" => "Bạn thắng!",
        "lose" => "Bạn thua!",
        "draw" => "Ván đấu hòa!",
        _ => $"Kết quả không xác định: {result.Result}"
    };
    Console.WriteLine(text);
    Console.WriteLine($"Match: {result.MatchId}");

    if (!string.IsNullOrWhiteSpace(result.WinnerId))
    {
        Console.WriteLine($"Người thắng: {result.WinnerId}");
    }
    
    Console.WriteLine("========================================");
    gameEnded = true;
};

client.OnOnlinePlayersReceived += onlinePlayers =>
{
    Console.WriteLine();
    Console.WriteLine("===== NGƯỜI CHƠI ĐANG ONLINE =====");
    if (onlinePlayers.Players.Count == 0)
    {
        Console.WriteLine("Không có người chơi nào đang online.");
    }
    else
    {
        foreach (PlayerInfo player in onlinePlayers.Players)
        {
            Console.WriteLine($"- {player.Username} (ID: {player.PlayerId})");
        }
    }
    Console.WriteLine("===================================");
};

client.OnInviteReceived += invite =>
{
    Console.WriteLine();
    Console.WriteLine($"[Lời mời] {invite.FromUsername} (ID: {invite.FromPlayerId}) mời bạn thi đấu.");
    Console.WriteLine($"Gõ /accept {invite.InviteId} để chấp nhận hoặc /reject {invite.InviteId} để từ chối.");
};

client.OnInviteAccepted += invite =>
{
    Console.WriteLine($"[Lời mời] Đã được chấp nhận. Match ID: {invite.MatchId}; X: {invite.PlayerXId}; O: {invite.PlayerOId}.");
};

client.OnInviteRejected += invite =>
{
    string reason = string.IsNullOrWhiteSpace(invite.Reason) ? "Không có lý do." : invite.Reason;
    Console.WriteLine($"[Lời mời] Bị từ chối. ID: {invite.InviteId}. Lý do: {reason}");
};

connection.Disconnected += reason =>
{
    Console.WriteLine($"[mất kết nối] {reason}");
};

try
{
    await connection.ConnectAsync(new Uri(serverAddress));
    Console.WriteLine($"Đã kết nối tới {serverAddress}");
}
catch (Exception ex)
{
    Console.WriteLine($"Không kết nối được: {ex.Message}");
    return;
}

Console.Write("Username: ");
string username = Console.ReadLine() ?? "player1";

Console.Write("PlayerId: ");
string playerId = Console.ReadLine() ?? "p1";

Console.Write("MatchId: ");
string matchId = Console.ReadLine() ?? "match-1";

try
{
    await client.LoginAsync(username, playerId);
    Console.WriteLine("Đã gửi login.");
}
catch (Exception ex)
{
    Console.WriteLine($"Login lỗi: {ex.Message}");
    return;
}

Console.WriteLine("Nhập nước đi theo dạng: row col");
Console.WriteLine("Ví dụ: 2 3");
PrintHelp();

while (!gameEnded)
{
    Console.Write("Nước đi/lệnh: ");
    string? input = Console.ReadLine();

    if (gameEnded)
    {
        break;
    }

    if (input is null)
    {
        break;
    }

    string command = input.Trim();
    if (command.Equals("/quit", StringComparison.OrdinalIgnoreCase))
    {
        break;
    }

    if (command.Equals("/help", StringComparison.OrdinalIgnoreCase))
    {
        PrintHelp();
        continue;
    }

    if (command.Equals("/online", StringComparison.OrdinalIgnoreCase))
    {
        await client.GetOnlinePlayersAsync();
        continue;
    }

    string[] commandParts = command.Split(' ', 3, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
    if (commandParts[0].Equals("/invite", StringComparison.OrdinalIgnoreCase))
    {
        if (commandParts.Length < 2)
        {
            Console.WriteLine("Cú pháp: /invite <playerId>");
            continue;
        }

        await client.SendInviteAsync(commandParts[1], Guid.NewGuid().ToString("N"));
        Console.WriteLine($"Đã gửi lời mời đến {commandParts[1]}.");
        continue;
    }

    if (commandParts[0].Equals("/accept", StringComparison.OrdinalIgnoreCase))
    {
        if (commandParts.Length < 2)
        {
            Console.WriteLine("Cú pháp: /accept <inviteId>");
            continue;
        }

        await client.AcceptInviteAsync(commandParts[1]);
        continue;
    }

    if (commandParts[0].Equals("/reject", StringComparison.OrdinalIgnoreCase))
    {
        if (commandParts.Length < 2)
        {
            Console.WriteLine("Cú pháp: /reject <inviteId> [lý do]");
            continue;
        }

        string? reason = commandParts.Length == 3 ? commandParts[2] : null;
        await client.RejectInviteAsync(commandParts[1], reason);
        continue;
    }

    if (!TryParseMove(input, out int row, out int col))
    {
        Console.WriteLine("Sai định dạng. Hãy nhập theo ví dụ: 2 3");
        continue;
    }

    if (row < 0 || col < 0)
    {
        Console.WriteLine("Tọa độ phải >= 0.");
        continue;
    }

    try
    {
        await client.MakeMoveAsync(matchId, playerId, row, col);
        Console.WriteLine($"Đã gửi nước đi: ({row}, {col})");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Gửi nước đi lỗi: {ex.Message}");
    }
}

await connection.DisconnectAsync();
Console.WriteLine("Đã đóng kết nối.");

static bool TryParseMove(string input, out int row, out int col)
{
    row = -1;
    col = -1;

    var parts = input.Split(
        new[] { ' ', ',', ';', '\t' },
        StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

    if (parts.Length != 2)
    {
        return false;
    }

    return int.TryParse(parts[0], out row) &&
           int.TryParse(parts[1], out col);
}

static void PrintHelp()
{
    Console.WriteLine("Lệnh: /online | /invite <playerId> | /accept <inviteId> | /reject <inviteId> [lý do] | /quit");
}

static void PrintBoard(int[][] board, (int Row, int Col)? lastMove = null)
{
    if (board == null || board.Length == 0 || board[0].Length == 0)
    {
        Console.WriteLine("Bàn cờ trống.");
        return;
    }

    Console.Write("    ");
    for (int col = 0; col < board[0].Length; col++)
    {
        Console.Write($"{col + 1,3}");
    }
    Console.WriteLine();

    Console.Write("   ");
    for (int col = 0; col < board[0].Length; col++)
    {
        Console.Write("----");
    }
    Console.WriteLine();

    for (int row = 0; row < board.Length; row++)
    {
        Console.Write($"{row + 1,2} |");

        for (int col = 0; col < board[row].Length; col++)
        {
            int value = board[row][col];
            char cell = value switch
            {
                1 => 'X',
                2 => 'O',
                _ => '.'
            };

            bool isLastMove = lastMove.HasValue && lastMove.Value.Row == row && lastMove.Value.Col == col;

            if (isLastMove)
            {
                Console.BackgroundColor = ConsoleColor.DarkYellow;
                Console.ForegroundColor = ConsoleColor.Black;
                Console.Write($"{cell,3}");
                Console.ResetColor();
            }
            else
            {
                Console.ForegroundColor = value switch
                {
                    1 => ConsoleColor.Cyan,
                    2 => ConsoleColor.Magenta,
                    _ => ConsoleColor.Gray
                };

                Console.Write($"{cell,3}");
                Console.ResetColor();
            }
        }

        Console.WriteLine();
    }

    Console.WriteLine();
}
