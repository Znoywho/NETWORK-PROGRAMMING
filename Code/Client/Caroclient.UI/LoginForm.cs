using System.Windows.Forms;

namespace Caroclient.UI;

public partial class LoginForm : Form
{
    public string Username { get; private set; } = string.Empty;
    public string ServerAddress { get; private set; } = string.Empty;

    public LoginForm()
    {
        InitializeComponent();
    }

    private void btnLogin_Click(object? sender, EventArgs e)
    {
        string username = txtLoginUsername.Text.Trim();
        string serverAddress = txtServerAddress.Text.Trim();

        if (string.IsNullOrWhiteSpace(username))
        {
            MessageBox.Show("Vui lòng nhập tên người chơi.", "Thiếu thông tin", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            txtLoginUsername.Focus();
            return;
        }

        if (!Uri.TryCreate(serverAddress, UriKind.Absolute, out Uri? serverUri) ||
            !serverUri.Scheme.Equals("tcp", StringComparison.OrdinalIgnoreCase))
        {
            MessageBox.Show("Địa chỉ server phải có dạng tcp://host:port.", "Địa chỉ không hợp lệ", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            txtServerAddress.Focus();
            return;
        }

        Username = username;
        ServerAddress = serverAddress;
        DialogResult = DialogResult.OK;
        Close();
    }

    private void lblTitle_Click(object sender, EventArgs e)
    {

    }

    private void label1_Click(object sender, EventArgs e)
    {

    }
}
