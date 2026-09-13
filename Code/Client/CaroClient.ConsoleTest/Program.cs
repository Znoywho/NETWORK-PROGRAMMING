using CaroClient.Core;
Console.OutputEncoding = System.Text.Encoding.UTF8;

int connectionLost = 0;
int reconnecting = 0;

Console.Write("Địa chỉ server (Enter để dùng mặc định tcp://localhost:8765): ");
string? uriInput = Console.ReadLine();

Uri serverUri = string.IsNullOrWhiteSpace(uriInput)
    ? new Uri("tcp://localhost:8765")
    : new Uri(uriInput.Trim());

await using var connection = new CaroConnection();

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
    await connection.ConnectAsync(serverUri);
    Console.WriteLine($"Đã kết nối tới {serverUri}");
}
catch (Exception ex)
{
    Console.WriteLine($"Không kết nối được: {ex.Message}");
    return;
}

Console.WriteLine("Nhập JSON message để gửi. Gõ /quit để thoát.");

while (Volatile.Read(ref connectionLost) == 0)
{
    Console.Write("Gửi: ");
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

    if (string.IsNullOrWhiteSpace(input))
    {
        continue;
    }

    try
    {
        await connection.SendAsync(input.Trim());
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Gửi lỗi: {ex.Message}");
    }
}

await connection.DisconnectAsync();
Console.WriteLine(Volatile.Read(ref connectionLost) == 1
    ? "Phiên làm việc đã kết thúc do mất kết nối."
    : "Đã đóng kết nối.");
