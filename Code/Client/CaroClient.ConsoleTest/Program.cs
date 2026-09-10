using CaroClient.Core;
using System.Text;

Console.OutputEncoding = System.Text.Encoding.UTF8;

int[][] board = Array.Empty<int[]>();

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
Console.WriteLine("Gõ /quit để thoát.");

while (true)
{
    Console.Write("Nước đi: ");
    string? input = Console.ReadLine();

    if (input is null || input.Trim().Equals("/quit", StringComparison.OrdinalIgnoreCase))
    {
        break;
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