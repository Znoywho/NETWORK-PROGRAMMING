namespace Caroclient.UI;

partial class ProfileForm
{
    private System.ComponentModel.IContainer components = null!;
    private Label lblTitle = null!;
    private GroupBox grpAccount = null!;
    private Label lblUsername = null!;
    private Label lblPlayerId = null!;
    private Label lblUsernameValue = null!;
    private Label lblPlayerIdValue = null!;
    private GroupBox grpRank = null!;
    private Label lblRankPoints = null!;
    private Label lblRankPointsValue = null!;
    private Button btnClose = null!;

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            components?.Dispose();
        }
        base.Dispose(disposing);
    }

    private void InitializeComponent()
    {
        lblTitle = new Label();
        grpAccount = new GroupBox();
        lblPlayerIdValue = new Label();
        lblUsernameValue = new Label();
        lblPlayerId = new Label();
        lblUsername = new Label();
        grpRank = new GroupBox();
        lblRankPointsValue = new Label();
        lblRankPoints = new Label();
        btnClose = new Button();
        grpAccount.SuspendLayout();
        grpRank.SuspendLayout();
        SuspendLayout();
        // 
        // lblTitle
        // 
        lblTitle.AutoSize = true;
        lblTitle.Font = new Font("Segoe UI", 14F, FontStyle.Bold);
        lblTitle.Location = new Point(112, 24);
        lblTitle.Name = "lblTitle";
        lblTitle.Size = new Size(181, 32);
        lblTitle.TabIndex = 0;
        lblTitle.Text = "HỒ SƠ CỦA TÔI";
        // 
        // grpAccount
        // 
        grpAccount.Controls.Add(lblPlayerIdValue);
        grpAccount.Controls.Add(lblUsernameValue);
        grpAccount.Controls.Add(lblPlayerId);
        grpAccount.Controls.Add(lblUsername);
        grpAccount.Location = new Point(30, 79);
        grpAccount.Name = "grpAccount";
        grpAccount.Size = new Size(340, 108);
        grpAccount.TabIndex = 1;
        grpAccount.TabStop = false;
        grpAccount.Text = "Thông tin người chơi";
        // 
        // lblUsername
        // 
        lblUsername.AutoSize = true;
        lblUsername.Location = new Point(18, 32);
        lblUsername.Name = "lblUsername";
        lblUsername.Size = new Size(42, 20);
        lblUsername.TabIndex = 0;
        lblUsername.Text = "Tên:";
        // 
        // lblUsernameValue
        // 
        lblUsernameValue.AutoSize = true;
        lblUsernameValue.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
        lblUsernameValue.Location = new Point(128, 32);
        lblUsernameValue.Name = "lblUsernameValue";
        lblUsernameValue.Size = new Size(63, 20);
        lblUsernameValue.TabIndex = 1;
        lblUsernameValue.Text = "Player_01";
        // 
        // lblPlayerId
        // 
        lblPlayerId.AutoSize = true;
        lblPlayerId.Location = new Point(18, 68);
        lblPlayerId.Name = "lblPlayerId";
        lblPlayerId.Size = new Size(28, 20);
        lblPlayerId.TabIndex = 2;
        lblPlayerId.Text = "ID:";
        // 
        // lblPlayerIdValue
        // 
        lblPlayerIdValue.AutoSize = true;
        lblPlayerIdValue.Location = new Point(128, 68);
        lblPlayerIdValue.Name = "lblPlayerIdValue";
        lblPlayerIdValue.Size = new Size(73, 20);
        lblPlayerIdValue.TabIndex = 3;
        lblPlayerIdValue.Text = "player-001";
        // 
        // grpRank
        // 
        grpRank.Controls.Add(lblRankPointsValue);
        grpRank.Controls.Add(lblRankPoints);
        grpRank.Location = new Point(30, 207);
        grpRank.Name = "grpRank";
        grpRank.Size = new Size(340, 108);
        grpRank.TabIndex = 2;
        grpRank.TabStop = false;
        grpRank.Text = "Điểm người chơi";
        // 
        // lblRankPoints
        // 
        lblRankPoints.AutoSize = true;
        lblRankPoints.Location = new Point(18, 42);
        lblRankPoints.Name = "lblRankPoints";
        lblRankPoints.Size = new Size(85, 20);
        lblRankPoints.TabIndex = 0;
        lblRankPoints.Text = "Điểm:";
        // 
        // lblRankPointsValue
        // 
        lblRankPointsValue.AutoSize = true;
        lblRankPointsValue.Location = new Point(128, 42);
        lblRankPointsValue.Name = "lblRankPointsValue";
        lblRankPointsValue.Size = new Size(17, 20);
        lblRankPointsValue.TabIndex = 1;
        lblRankPointsValue.Text = "0";
        // 
        // btnClose
        // 
        btnClose.DialogResult = DialogResult.Cancel;
        btnClose.Location = new Point(265, 334);
        btnClose.Name = "btnClose";
        btnClose.Size = new Size(105, 32);
        btnClose.TabIndex = 3;
        btnClose.Text = "Đóng";
        btnClose.UseVisualStyleBackColor = true;
        // 
        // ProfileForm
        // 
        AutoScaleDimensions = new SizeF(8F, 20F);
        AutoScaleMode = AutoScaleMode.Font;
        CancelButton = btnClose;
        ClientSize = new Size(400, 386);
        Controls.Add(btnClose);
        Controls.Add(grpRank);
        Controls.Add(grpAccount);
        Controls.Add(lblTitle);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        Name = "ProfileForm";
        StartPosition = FormStartPosition.CenterParent;
        Text = "Hồ sơ của tôi";
        grpAccount.ResumeLayout(false);
        grpAccount.PerformLayout();
        grpRank.ResumeLayout(false);
        grpRank.PerformLayout();
        ResumeLayout(false);
        PerformLayout();
    }
}
