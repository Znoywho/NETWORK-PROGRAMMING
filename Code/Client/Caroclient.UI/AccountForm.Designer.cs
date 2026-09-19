namespace Caroclient.UI;

partial class AccountForm
{
    private System.ComponentModel.IContainer components = null!;
    private Label lblTitle = null!;
    private Label lblUsername = null!;
    private Label lblPlayerId = null!;
    private TextBox txtUsername = null!;
    private TextBox txtPlayerId = null!;
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
        lblUsername = new Label();
        lblPlayerId = new Label();
        txtUsername = new TextBox();
        txtPlayerId = new TextBox();
        btnClose = new Button();
        SuspendLayout();
        // 
        // lblTitle
        // 
        lblTitle.AutoSize = true;
        lblTitle.Font = new Font("Segoe UI", 14F, FontStyle.Bold);
        lblTitle.Location = new Point(101, 23);
        lblTitle.Name = "lblTitle";
        lblTitle.Size = new Size(231, 32);
        lblTitle.TabIndex = 0;
        lblTitle.Text = "TÀI KHOẢN CỦA TÔI";
        // 
        // lblUsername
        // 
        lblUsername.AutoSize = true;
        lblUsername.Location = new Point(30, 86);
        lblUsername.Name = "lblUsername";
        lblUsername.Size = new Size(110, 20);
        lblUsername.TabIndex = 1;
        lblUsername.Text = "Tên người chơi";
        // 
        // lblPlayerId
        // 
        lblPlayerId.AutoSize = true;
        lblPlayerId.Location = new Point(30, 132);
        lblPlayerId.Name = "lblPlayerId";
        lblPlayerId.Size = new Size(102, 20);
        lblPlayerId.TabIndex = 2;
        lblPlayerId.Text = "ID người chơi";
        // 
        // txtUsername
        // 
        txtUsername.Location = new Point(155, 82);
        txtUsername.MaxLength = 30;
        txtUsername.Name = "txtUsername";
        txtUsername.ReadOnly = true;
        txtUsername.Size = new Size(215, 27);
        txtUsername.TabIndex = 0;
        // 
        // txtPlayerId
        // 
        txtPlayerId.Location = new Point(155, 128);
        txtPlayerId.Name = "txtPlayerId";
        txtPlayerId.ReadOnly = true;
        txtPlayerId.Size = new Size(215, 27);
        txtPlayerId.TabIndex = 1;
        // 
        // btnClose
        // 
        btnClose.DialogResult = DialogResult.Cancel;
        btnClose.Location = new Point(265, 177);
        btnClose.Name = "btnClose";
        btnClose.Size = new Size(105, 32);
        btnClose.TabIndex = 2;
        btnClose.Text = "Đóng";
        btnClose.UseVisualStyleBackColor = true;
        // 
        // AccountForm
        // 
        AcceptButton = btnClose;
        AutoScaleDimensions = new SizeF(8F, 20F);
        AutoScaleMode = AutoScaleMode.Font;
        CancelButton = btnClose;
        ClientSize = new Size(400, 229);
        Controls.Add(btnClose);
        Controls.Add(txtPlayerId);
        Controls.Add(txtUsername);
        Controls.Add(lblPlayerId);
        Controls.Add(lblUsername);
        Controls.Add(lblTitle);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        Name = "AccountForm";
        StartPosition = FormStartPosition.CenterParent;
        Text = "Tài khoản của tôi";
        ResumeLayout(false);
        PerformLayout();
    }
}
