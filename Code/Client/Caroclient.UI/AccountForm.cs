using System.Windows.Forms;

namespace Caroclient.UI;

public partial class AccountForm : Form
{
    public AccountForm(string username = "Player_01", string playerId = "player-001")
    {
        InitializeComponent();
        txtUsername.Text = username;
        txtPlayerId.Text = playerId;
    }

    private void btnUpdate_Click(object? sender, EventArgs e)
    {
        if (string.IsNullOrWhiteSpace(txtUsername.Text))
        {
            MessageBox.Show("Tên người chơi không được để trống.", "Thiếu thông tin", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            txtUsername.Focus();
            return;
        }

        MessageBox.Show("Thông tin tài khoản đã được cập nhật trên giao diện.", "Cập nhật tài khoản", MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    private void btnDelete_Click(object? sender, EventArgs e)
    {
        DialogResult confirm = MessageBox.Show(
            "Bạn có chắc muốn xóa tài khoản? Thao tác này sẽ được kết nối với server sau.",
            "Xóa tài khoản",
            MessageBoxButtons.YesNo,
            MessageBoxIcon.Warning);

        if (confirm == DialogResult.Yes)
        {
            MessageBox.Show("Yêu cầu xóa tài khoản đã được xác nhận trên giao diện.", "Xóa tài khoản", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
    }
}
