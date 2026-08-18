using CaroClient.Core;
Console.OutputEncoding = System.Text.Encoding.UTF8;

Console.Write("Địa chỉ server (Enter để dùng mặc định ws://localhost:8765): ");
string? uriInput = Console.ReadLine();

Uri serverUri = string.IsNullOrWhiteSpace(uriInput)
    ? new Uri("ws://localhost:8765")
    : new Uri(uriInput.Trim());

await using var connection = new CaroConnection();

connection.MessageReceived += json => Console.WriteLine($"[nhận] {json}");
connection.Disconnected += reason => Console.WriteLine($"[mất kết nối] {reason}");

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

while (true)
{
    Console.Write("Gửi: ");
    string? input = Console.ReadLine();

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
Console.WriteLine("Đã đóng kết nối.");