using CaroClient.Core;
Console.OutputEncoding = System.Text.Encoding.UTF8;

bool connectionLost = false;

Console.Write("Địa chỉ server (Enter để dùng mặc định tcp://localhost:8765): ");
string? uriInput = Console.ReadLine();

Uri serverUri = string.IsNullOrWhiteSpace(uriInput)
    ? new Uri("tcp://localhost:8765")
    : new Uri(uriInput.Trim());

await using var connection = new CaroConnection();

connection.MessageReceived += json => Console.WriteLine($"[nhận] {json}");
connection.Disconnected += reason =>
{
    connectionLost = true;
    Console.WriteLine();
    Console.WriteLine($"[MẤT KẾT NỐI] {reason}");
    Console.WriteLine("Không thể gửi thêm message. Phiên làm việc sẽ kết thúc.");
};

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

while (!connectionLost)
{
    Console.Write("Gửi: ");
    string? input = Console.ReadLine();

    if (connectionLost)
    {
        break;
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
Console.WriteLine(connectionLost
    ? "Phiên làm việc đã kết thúc do mất kết nối."
    : "Đã đóng kết nối.");
