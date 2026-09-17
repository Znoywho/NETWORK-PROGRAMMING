using CaroClient.Core;

Console.OutputEncoding = System.Text.Encoding.UTF8;

// Các biến dưới đây bị ghi từ luồng nhận message và đọc ở vòng lặp chính,
// nên luôn truy cập qua Volatile giống connectionLost/reconnecting.
int connectionLost = 0;
int reconnecting = 0;
int gameEnded = 0;
string? roomId = null;
string? myPlayerId = null;
int[][] board = Array.Empty<int[]>();

Console.Write("Địa chỉ server (Enter để dùng mặc định tcp://localhost:8765): ");
string? uriInput = Console.ReadLine();

Uri serverUri = string.IsNullOrWhiteSpace(uriInput)
    ? new Uri("tcp://localhost:8765")
    : new Uri(uriInput.Trim());

await using var connection = new CaroConnection();
var client = new GameClient(connection);

client.OnLoginSucceeded += auth =>
{
    Volatile.Write(ref myPlayerId, auth.PlayerId);
    Console.WriteLine();
    Console.WriteLine($"[login] Đăng nhập thành công: {auth.Username} (ID: {auth.PlayerId})");
};

client.OnUserCreated += auth =>
{
    Console.WriteLine();
    Console.WriteLine($"[create_user] Đã tạo tài khoản {auth.Username} (ID: {auth.PlayerId}). Hãy /login để đăng nhập.");
};

client.OnGameStateReceived += state =>
{
    Volatile.Write(ref board, state.Board);
    Volatile.Write(ref roomId, state.RoomId);

    Console.WriteLine();
    Console.WriteLine("========================================");
    Console.WriteLine($"[game_state] room_id={state.RoomId}");
    Console.WriteLine($"currentPlayerId: {state.CurrentPlayerId}"
        + (state.CurrentPlayerId == Volatile.Read(ref myPlayerId) ? "  <-- ĐẾN LƯỢT BẠN" : ""));
    Console.WriteLine($"status: {state.Status}");
    Console.WriteLine("========================================");

    PrintBoard(board);
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
    Console.WriteLine($"Room: {result.RoomId}");

    if (!string.IsNullOrWhiteSpace(result.WinnerId))
    {
        Console.WriteLine($"Người thắng: {result.WinnerId}");
    }

    Console.WriteLine("========================================");
    Volatile.Write(ref gameEnded, 1);
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
            string self = player.PlayerId == Volatile.Read(ref myPlayerId) ? " (bạn)" : "";
            Console.WriteLine($"- {player.Username} (ID: {player.PlayerId}) [{player.Status}]{self}");
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

client.OnInviteResult += result =>
{
    Console.WriteLine($"[Lời mời] Đã gửi tới {result.ToPlayerId}. Invite ID: {result.InviteId}");
};

client.OnInviteRejected += rejected =>
{
    Console.WriteLine($"[Lời mời] Bị từ chối bởi {rejected.ByPlayerId}. Invite ID: {rejected.InviteId}");
};

client.OnLeaveRoomResult += leave =>
{
    Volatile.Write(ref roomId, null);
    Console.WriteLine($"[leave_room] Đã rời phòng với vai trò {leave.Role}."
        + (string.IsNullOrWhiteSpace(leave.WinnerId) ? "" : $" Người thắng: {leave.WinnerId}"));
};

client.OnErrorReceived += error =>
{
    Console.WriteLine($"[LỖI {error.Code}] {error.Message}");
};

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

connection.Reconnected += () =>
    Console.WriteLine("[KẾT NỐI LẠI] Đã kết nối lại TCP thành công. Hãy /login lại.");

try
{
    await connection.ConnectAsync(serverUri);
    Console.WriteLine($"Đã kết nối tới {serverUri}");
}
catch (Exception ex)
{
    Console.WriteLine($"Không kết nối được: {ex.Message}");
    return;
}

Console.Write("Username: ");
string username = (Console.ReadLine() ?? "").Trim();

Console.Write("Password: ");
string password = Console.ReadLine() ?? "";

try
{
    await client.LoginAsync(username, password);
}
catch (Exception ex)
{
    Console.WriteLine($"Login lỗi: {ex.Message}");
    return;
}

PrintHelp();

while (Volatile.Read(ref gameEnded) == 0 && Volatile.Read(ref connectionLost) == 0)
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

    if (input is null)
    {
        break;
    }

    string command = input.Trim();
    if (command.Length == 0)
    {
        continue;
    }

    if (command.Equals("/quit", StringComparison.OrdinalIgnoreCase))
    {
        break;
    }

    if (command.Equals("/help", StringComparison.OrdinalIgnoreCase))
    {
        PrintHelp();
        continue;
    }

    if (command.Equals("/board", StringComparison.OrdinalIgnoreCase))
    {
        PrintBoard(Volatile.Read(ref board));
        continue;
    }

    try
    {
        if (command.StartsWith('/'))
        {
            await HandleCommandAsync(command);
        }
        else
        {
            await HandleMoveAsync(command);
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Gửi lệnh lỗi: {ex.Message}");
    }
}

await connection.DisconnectAsync();
Console.WriteLine(Volatile.Read(ref connectionLost) == 1
    ? "Phiên làm việc đã kết thúc do mất kết nối."
    : "Đã đóng kết nối.");

async Task HandleCommandAsync(string command)
{
    string[] parts = command.Split(' ', 3, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
    string verb = parts[0];

    if (verb.Equals("/online", StringComparison.OrdinalIgnoreCase))
    {
        await client.GetOnlinePlayersAsync();
        return;
    }

    if (verb.Equals("/register", StringComparison.OrdinalIgnoreCase))
    {
        if (parts.Length < 3)
        {
            Console.WriteLine("Cú pháp: /register <username> <password>  (mật khẩu tối thiểu 10 ký tự)");
            return;
        }

        await client.CreateUserAsync(parts[1], parts[2]);
        return;
    }

    if (verb.Equals("/login", StringComparison.OrdinalIgnoreCase))
    {
        if (parts.Length < 3)
        {
            Console.WriteLine("Cú pháp: /login <username> <password>");
            return;
        }

        await client.LoginAsync(parts[1], parts[2]);
        return;
    }

    if (verb.Equals("/invite", StringComparison.OrdinalIgnoreCase))
    {
        if (parts.Length < 2)
        {
            Console.WriteLine("Cú pháp: /invite <playerId> [inviteId]");
            return;
        }

        string inviteId = parts.Length >= 3 ? parts[2] : Guid.NewGuid().ToString("N");
        await client.SendInviteAsync(parts[1], inviteId);
        return;
    }

    if (verb.Equals("/accept", StringComparison.OrdinalIgnoreCase))
    {
        if (parts.Length < 2)
        {
            Console.WriteLine("Cú pháp: /accept <inviteId>");
            return;
        }

        await client.AcceptInviteAsync(parts[1]);
        return;
    }

    if (verb.Equals("/reject", StringComparison.OrdinalIgnoreCase))
    {
        if (parts.Length < 2)
        {
            Console.WriteLine("Cú pháp: /reject <inviteId> [lý do]");
            return;
        }

        await client.RejectInviteAsync(parts[1], parts.Length == 3 ? parts[2] : null);
        return;
    }

    if (verb.Equals("/spectate", StringComparison.OrdinalIgnoreCase))
    {
        if (parts.Length < 2)
        {
            Console.WriteLine("Cú pháp: /spectate <room_id>");
            return;
        }

        await client.SpectateAsync(parts[1]);
        return;
    }

    if (verb.Equals("/leave", StringComparison.OrdinalIgnoreCase))
    {
        string? target = parts.Length >= 2 ? parts[1] : Volatile.Read(ref roomId);
        if (string.IsNullOrWhiteSpace(target))
        {
            Console.WriteLine("Chưa ở trong phòng nào. Cú pháp: /leave [room_id]");
            return;
        }

        await client.LeaveRoomAsync(target);
        return;
    }

    Console.WriteLine($"Lệnh không hợp lệ: {verb}. Gõ /help để xem danh sách.");
}

async Task HandleMoveAsync(string input)
{
    if (!TryParseMove(input, out int row, out int col))
    {
        Console.WriteLine("Sai định dạng. Hãy nhập theo ví dụ: 2 3");
        return;
    }

    string? currentRoomId = Volatile.Read(ref roomId);
    if (string.IsNullOrWhiteSpace(currentRoomId))
    {
        Console.WriteLine("Chưa vào phòng nào. Hãy /invite hoặc /accept trước.");
        return;
    }

    string? currentPlayerId = Volatile.Read(ref myPlayerId);
    if (string.IsNullOrWhiteSpace(currentPlayerId))
    {
        Console.WriteLine("Chưa đăng nhập. Hãy /login <username> <password>.");
        return;
    }

    await client.MakeMoveAsync(currentRoomId, currentPlayerId, row, col);
    Console.WriteLine($"Đã gửi nước đi: ({row}, {col})");
}

static bool TryParseMove(string input, out int row, out int col)
{
    row = 0;
    col = 0;

    string[] parts = input.Split(
        new[] { ' ', ',', '\t' },
        StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

    return parts.Length == 2
        && int.TryParse(parts[0], out row)
        && int.TryParse(parts[1], out col)
        && row >= 0
        && col >= 0;
}

static void PrintHelp()
{
    Console.WriteLine();
    Console.WriteLine("===== LỆNH =====");
    Console.WriteLine("  <row> <col>                  Đánh một nước, ví dụ: 7 7");
    Console.WriteLine("  /online                      Xem danh sách người chơi online");
    Console.WriteLine("  /invite <playerId> [id]      Mời một người chơi");
    Console.WriteLine("  /accept <inviteId>           Chấp nhận lời mời");
    Console.WriteLine("  /reject <inviteId> [lý do]   Từ chối lời mời");
    Console.WriteLine("  /spectate <room_id>          Xem một trận đang diễn ra");
    Console.WriteLine("  /leave [room_id]             Rời phòng hiện tại");
    Console.WriteLine("  /login <user> <pass>         Đăng nhập lại");
    Console.WriteLine("  /register <user> <pass>      Tạo tài khoản mới (pass >= 10 ký tự)");
    Console.WriteLine("  /board                       In lại bàn cờ");
    Console.WriteLine("  /help                        Xem trợ giúp");
    Console.WriteLine("  /quit                        Thoát");
    Console.WriteLine("================");
}

static void PrintBoard(int[][] board)
{
    if (board.Length == 0)
    {
        Console.WriteLine("(chưa có bàn cờ)");
        return;
    }

    Console.Write("    ");
    for (int c = 0; c < board[0].Length; c++)
    {
        Console.Write($"{c,2} ");
    }
    Console.WriteLine();

    for (int r = 0; r < board.Length; r++)
    {
        Console.Write($"{r,3} ");
        for (int c = 0; c < board[r].Length; c++)
        {
            char symbol = board[r][c] switch
            {
                1 => 'X',
                2 => 'O',
                _ => '.'
            };
            Console.Write($" {symbol} ");
        }
        Console.WriteLine();
    }
}
