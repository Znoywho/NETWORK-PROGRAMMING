using System;
using System.Drawing;
using System.Windows.Forms;

namespace Caroclient.UI;

/// <summary>Màn hình đăng nhập độc lập, chỉ chịu trách nhiệm nhận tên người chơi.</summary>
public sealed class LoginForm : Form
{
    private readonly TextBox txtPlayerName = new();
    public string PlayerName { get; private set; } = string.Empty;

    public LoginForm()
    {
        Text = "Caro - Đăng nhập";
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        ClientSize = new Size(390, 245);

        var title = new Label { Text = "CARO ONLINE", Font = new Font(Font.FontFamily, 20, FontStyle.Bold), AutoSize = true, Location = new Point(105, 32) };
        var prompt = new Label { Text = "Tên người chơi", AutoSize = true, Location = new Point(48, 105) };
        txtPlayerName.Location = new Point(48, 130);
        txtPlayerName.Size = new Size(294, 27);
        txtPlayerName.MaxLength = 30;
        txtPlayerName.PlaceholderText = "Nhập tên của bạn";
        txtPlayerName.KeyDown += (_, e) => { if (e.KeyCode == Keys.Enter) Submit(); };
        var loginButton = new Button { Text = "Đăng nhập", Location = new Point(130, 180), Size = new Size(130, 34) };
        loginButton.Click += (_, _) => Submit();
        Controls.AddRange(new Control[] { title, prompt, txtPlayerName, loginButton });
        AcceptButton = loginButton;
    }

    private void Submit()
    {
        var name = txtPlayerName.Text.Trim();
        if (string.IsNullOrWhiteSpace(name))
        {
            MessageBox.Show("Vui lòng nhập tên người chơi.", "Đăng nhập", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            txtPlayerName.Focus();
            return;
        }
        PlayerName = name;
        DialogResult = DialogResult.OK;
    }
}
