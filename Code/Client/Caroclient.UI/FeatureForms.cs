using System.Drawing;
using System.Windows.Forms;

namespace Caroclient.UI;

public sealed class ChatForm : Form
{
    private readonly TextBox _messageInput = new();
    private readonly RichTextBox _conversation = new();

    public ChatForm()
    {
        Text = "Nhắn tin";
        StartPosition = FormStartPosition.CenterParent;
        ClientSize = new Size(620, 430);

        var contacts = new ListBox { Location = new Point(15, 45), Size = new Size(150, 320) };
        contacts.Items.AddRange(["Bạn bè", "Player_02", "Player_03"]);
        contacts.SelectedIndex = 0;

        var contactsLabel = new Label { AutoSize = true, Location = new Point(15, 18), Text = "Danh sách trò chuyện" };
        var conversationLabel = new Label { AutoSize = true, Location = new Point(185, 18), Text = "Nội dung tin nhắn" };
        _conversation.Location = new Point(185, 45);
        _conversation.ReadOnly = true;
        _conversation.Size = new Size(420, 260);
        _conversation.Text = "Chọn một người chơi để bắt đầu trò chuyện.";

        _messageInput.Location = new Point(185, 323);
        _messageInput.Size = new Size(310, 27);
        var sendButton = new Button { Location = new Point(505, 321), Size = new Size(100, 30), Text = "Gửi" };
        sendButton.Click += (_, _) => SendMessage();
        var closeButton = new Button { DialogResult = DialogResult.Cancel, Location = new Point(505, 375), Size = new Size(100, 30), Text = "Đóng" };

        AcceptButton = sendButton;
        CancelButton = closeButton;
        Controls.AddRange([contactsLabel, conversationLabel, contacts, _conversation, _messageInput, sendButton, closeButton]);
    }

    private void SendMessage()
    {
        string message = _messageInput.Text.Trim();
        if (message.Length == 0)
        {
            return;
        }

        _conversation.AppendText($"{Environment.NewLine}Bạn: {message}");
        _messageInput.Clear();
    }
}

public sealed class FriendsForm : Form
{
    public FriendsForm()
    {
        Text = "Bạn bè";
        StartPosition = FormStartPosition.CenterParent;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        ClientSize = new Size(440, 380);

        var title = new Label { AutoSize = true, Font = new Font("Segoe UI", 14F, FontStyle.Bold), Location = new Point(150, 20), Text = "BẠN BÈ" };
        var friends = new ListBox { Location = new Point(25, 70), Size = new Size(265, 220) };
        friends.Items.AddRange(["Player_02  -  Đang online", "Player_03  -  Đang online", "Player_04  -  Ngoại tuyến"]);

        var addButton = new Button { Location = new Point(305, 70), Size = new Size(110, 32), Text = "Thêm bạn" };
        var removeButton = new Button { Location = new Point(305, 112), Size = new Size(110, 32), Text = "Xóa bạn" };
        var inviteButton = new Button { Location = new Point(305, 154), Size = new Size(110, 32), Text = "Mời đấu" };
        var closeButton = new Button { DialogResult = DialogResult.Cancel, Location = new Point(305, 318), Size = new Size(110, 32), Text = "Đóng" };

        addButton.Click += (_, _) => MessageBox.Show("Chức năng thêm bạn sẽ được kết nối server sau.", "Bạn bè");
        removeButton.Click += (_, _) => MessageBox.Show("Chức năng xóa bạn sẽ được kết nối server sau.", "Bạn bè");
        inviteButton.Click += (_, _) => MessageBox.Show("Hãy dùng màn hình Mời đấu để gửi lời mời.", "Bạn bè");
        CancelButton = closeButton;
        Controls.AddRange([title, friends, addButton, removeButton, inviteButton, closeButton]);
    }
}

public sealed class MatchHistoryForm : Form
{
    public MatchHistoryForm()
    {
        Text = "Lịch sử thi đấu";
        StartPosition = FormStartPosition.CenterParent;
        ClientSize = new Size(700, 390);

        var title = new Label { AutoSize = true, Font = new Font("Segoe UI", 14F, FontStyle.Bold), Location = new Point(250, 20), Text = "LỊCH SỬ THI ĐẤU" };
        var history = new DataGridView
        {
            AllowUserToAddRows = false,
            AllowUserToDeleteRows = false,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
            Location = new Point(20, 70),
            ReadOnly = true,
            RowHeadersVisible = false,
            Size = new Size(660, 240)
        };
        history.Columns.Add("date", "Thời gian");
        history.Columns.Add("opponent", "Đối thủ");
        history.Columns.Add("result", "Kết quả");
        history.Columns.Add("score", "Tỉ số");
        history.Columns.Add("points", "Điểm rank");
        history.Rows.Add("Chưa có dữ liệu", "-", "-", "-", "-");

        var closeButton = new Button { DialogResult = DialogResult.Cancel, Location = new Point(575, 330), Size = new Size(105, 32), Text = "Đóng" };
        CancelButton = closeButton;
        Controls.AddRange([title, history, closeButton]);
    }
}

public sealed class InviteForm : Form
{
    public InviteForm()
    {
        Text = "Mời đấu";
        StartPosition = FormStartPosition.CenterParent;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        ClientSize = new Size(460, 390);

        var title = new Label { AutoSize = true, Font = new Font("Segoe UI", 14F, FontStyle.Bold), Location = new Point(168, 20), Text = "MỜI ĐẤU" };
        var info = new Label { AutoSize = true, Location = new Point(25, 70), Text = "Người chơi đang online" };
        var players = new ListBox { Location = new Point(25, 98), Size = new Size(275, 210) };
        players.Items.AddRange(["Player_02", "Player_03", "Player_05"]);

        var inviteButton = new Button { Location = new Point(315, 98), Size = new Size(120, 34), Text = "Gửi lời mời" };
        var refreshButton = new Button { Location = new Point(315, 142), Size = new Size(120, 34), Text = "Làm mới" };
        var closeButton = new Button { DialogResult = DialogResult.Cancel, Location = new Point(315, 335), Size = new Size(120, 32), Text = "Đóng" };

        inviteButton.Click += (_, _) =>
        {
            if (players.SelectedItem is null)
            {
                MessageBox.Show("Vui lòng chọn người chơi để mời.", "Mời đấu", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            MessageBox.Show($"Đã tạo lời mời đấu cho {players.SelectedItem} trên giao diện.", "Mời đấu");
        };
        refreshButton.Click += (_, _) => MessageBox.Show("Danh sách online sẽ được lấy từ server ở bước tích hợp network.", "Mời đấu");
        CancelButton = closeButton;
        Controls.AddRange([title, info, players, inviteButton, refreshButton, closeButton]);
    }
}
