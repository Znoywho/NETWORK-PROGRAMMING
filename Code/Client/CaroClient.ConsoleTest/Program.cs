using CaroClient.Core;
using System.Text;

Console.OutputEncoding = System.Text.Encoding.UTF8;

int connectionLost = 0;
int reconnecting = 0;

Console.Write("Địa chỉ server (Enter để dùng mặc định tcp://localhost:8765): ");
string? uriInput = Console.ReadLine();

Uri serverUri = string.IsNullOrWhiteSpace(uriInput)
    ? new Uri("tcp://localhost:8765")
    : new Uri(uriInput.Trim());

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

connection.MessageReceived += json => Console.WriteLine($"[nhận] {json}");
connection.Disconnected += reason =>
{
    if (Interlocked.Exchange(ref reconnecting, 1) == 1)
    {
        return;
    }

    Console.WriteLine();
    Console.WriteLine($"[MẤT KẾT NỐI] {reason}");
    Console.WriteLine("Đang thử kết nối lại tối đa 3 lần...");

    _ = Task.Run(async () =>
    {
        try
        {
            bool reconnected = await connection.ReconnectAsync(3, TimeSpan.FromSeconds(2));
            if (!reconnected)
            {
                Volatile.Write(ref connectionLost, 1);
                Console.WriteLine("Không thể kết nối lại. Phiên làm việc sẽ kết thúc.");
            }
        }
        catch (Exception ex)
        {
            Volatile.Write(ref connectionLost, 1);
            Console.WriteLine($"Kết nối lại thất bại: {ex.Message}");
        }
        finally
        {
            Volatile.Write(ref reconnecting, 0);
        }
    });
};

connection.Reconnected += () => Console.WriteLine("[KẾT NỐI LẠI] Đã kết nối lại TCP thành công.");

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

while (Volatile.Read(ref connectionLost) == 0)
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

    if (Volatile.Read(ref connectionLost) == 1)
    {
        break;
    }

    if (Volatile.Read(ref reconnecting) == 1)
    {
        Console.WriteLine("Đang kết nối lại, vui lòng chờ.");
        continue;
    }

    if (input is null || input.Trim().Equals("/quit", StringComparison.OrdinalIgnoreCase))
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
Console.WriteLine(Volatile.Read(ref connectionLost) == 1
    ? "Phiên làm việc đã kết thúc do mất kết nối."
    : "Đã đóng kết nối.");
