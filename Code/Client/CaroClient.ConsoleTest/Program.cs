using CaroClient.Core;

Console.OutputEncoding = System.Text.Encoding.UTF8;

Console.Write("Địa chỉ server (Enter để dùng mặc định tcp://localhost:8765): ");
string? uriInput = Console.ReadLine();

string serverAddress = string.IsNullOrWhiteSpace(uriInput)
    ? "tcp://localhost:8765"
    : uriInput.Trim();

await using var connection = new CaroConnection();
var client = new GameClient(connection);

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