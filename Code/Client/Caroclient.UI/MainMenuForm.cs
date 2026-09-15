using System;
using System.Drawing;
using System.Windows.Forms;

namespace Caroclient.UI;

/// <summary>Sảnh chính sau đăng nhập, hiển thị hồ sơ và rank người chơi.</summary>
public sealed class MainMenuForm : Form
{
    private readonly string playerName;

    public MainMenuForm(string playerName)
    {
        this.playerName = playerName;
        Text = "Caro - Menu chính";
        StartPosition = FormStartPosition.CenterScreen;
        ClientSize = new Size(680, 410);
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        var title = new Label { Text = "CARO ONLINE", Font = new Font(Font.FontFamily, 22, FontStyle.Bold), AutoSize = true, Location = new Point(225, 30) };
        var profile = new GroupBox { Text = "Thông tin người chơi", Location = new Point(45, 100), Size = new Size(270, 210) };
        profile.Controls.AddRange(new Control[] { CreateInfoLabel("Người chơi:", playerName, 30), CreateInfoLabel("Rank:", "Tân binh", 75), CreateInfoLabel("Điểm rank:", "0 RP", 120), CreateInfoLabel("Thắng / Thua:", "0 / 0", 165) });
        var playButton = new Button { Text = "Chơi ngay", Location = new Point(385, 125), Size = new Size(230, 48) };
        playButton.Click += (_, _) => OpenGame();
        var rankingButton = new Button { Text = "Bảng xếp hạng", Location = new Point(385, 190), Size = new Size(230, 48) };
        rankingButton.Click += (_, _) => MessageBox.Show("Bảng xếp hạng sẽ được cập nhật từ máy chủ.", "Caro");
        var logoutButton = new Button { Text = "Đăng xuất", Location = new Point(385, 255), Size = new Size(230, 48) };
        logoutButton.Click += (_, _) => Close();
        Controls.AddRange(new Control[] { title, profile, playButton, rankingButton, logoutButton });
    }

    private static Label CreateInfoLabel(string caption, string value, int top) => new() { Text = $"{caption} {value}", AutoSize = true, Location = new Point(20, top) };

    private void OpenGame()
    {
        Hide();
        using var gameForm = new Form1(playerName);
        gameForm.ShowDialog(this);
        Show();
    }
}
