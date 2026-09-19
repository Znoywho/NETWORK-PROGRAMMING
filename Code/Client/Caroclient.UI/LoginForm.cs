using System.Windows.Forms;

namespace Caroclient.UI;

public partial class LoginForm : Form
{
    public string Username { get; private set; } = string.Empty;
    public string Password { get; private set; } = string.Empty;
    public string ServerAddress { get; private set; } = string.Empty;
    public bool RegisterRequested { get; private set; }

    public LoginForm()
    {
        InitializeComponent();

        if (string.IsNullOrWhiteSpace(txtServerAddress.Text))
        {
            txtServerAddress.Text = "tcp://localhost:8765";
        }
    }

    private void btnLogin_Click(object? sender, EventArgs e)
    {
        Submit(register: false);
    }

    private void btnRegister_Click(object? sender, EventArgs e)
    {
        Submit(register: true);
    }

    private void Submit(bool register)
    {
        string username = txtLoginUsername.Text.Trim();
        string password = txtPassword.Text;
        string serverAddress = txtServerAddress.Text.Trim();

        if (string.IsNullOrWhiteSpace(username))
        {
            MessageBox.Show("Vui lòng nhập tên người chơi.", "Thiếu thông tin", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            txtLoginUsername.Focus();
            return;
        }

        if (string.IsNullOrEmpty(password))
        {
            MessageBox.Show("Vui lòng nhập mật khẩu.", "Thiếu thông tin", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            txtPassword.Focus();
            return;
        }

        if (register && password.Length < 6)
        {
            MessageBox.Show("Mật khẩu đăng ký phải có ít nhất 6 ký tự.", "Mật khẩu chưa hợp lệ", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            txtPassword.Focus();
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
        Password = password;
        ServerAddress = serverAddress;
        RegisterRequested = register;
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
