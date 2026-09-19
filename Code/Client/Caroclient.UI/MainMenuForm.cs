using System;
using System.Drawing;
using System.Windows.Forms;

namespace Caroclient.UI;

/// <summary>Sảnh chính sau đăng nhập.</summary>
public sealed class MainMenuForm : Form
{
    private readonly string playerName;
    private readonly string password;
    private readonly string serverAddress;

    public MainMenuForm(string playerName, string password = "", string serverAddress = "tcp://localhost:8765")
    {
        this.playerName = playerName;
        this.password = password;
        this.serverAddress = serverAddress;
        Text = "Caro - Menu chính";
        StartPosition = FormStartPosition.CenterScreen;
        ClientSize = new Size(680, 410);
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        var title = new Label { Text = "CARO ONLINE", Font = new Font(Font.FontFamily, 22, FontStyle.Bold), AutoSize = true, Location = new Point(225, 30) };
        var profile = new GroupBox { Text = "Thông tin người chơi", Location = new Point(45, 100), Size = new Size(270, 100) };
        profile.Controls.Add(CreateInfoLabel("Người chơi:", playerName, 30));
        var playButton = new Button { Text = "Chơi ngay", Location = new Point(385, 125), Size = new Size(230, 48) };
        playButton.Click += (_, _) => OpenGame();
        var logoutButton = new Button { Text = "Đăng xuất", Location = new Point(385, 190), Size = new Size(230, 48) };
        logoutButton.Click += (_, _) => Close();
        Controls.AddRange(new Control[] { title, profile, playButton, logoutButton });
    }

    private static Label CreateInfoLabel(string caption, string value, int top) => new() { Text = $"{caption} {value}", AutoSize = true, Location = new Point(20, top) };

    private void OpenGame()
    {
        Hide();
        using var gameForm = new Form1(playerName, password, serverAddress);
        gameForm.ShowDialog(this);
        Show();
    }
}
