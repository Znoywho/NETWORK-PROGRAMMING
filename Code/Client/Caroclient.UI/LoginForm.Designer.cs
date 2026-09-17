namespace Caroclient.UI;

partial class LoginForm
{
    private System.ComponentModel.IContainer components = null!;
    private Label lblTitle = null!;
    private Label lblUsername = null!;
    private Label lblServerAddress = null!;
    private TextBox txtLoginUsername = null!;
    private TextBox txtServerAddress = null!;
    private Button btnLogin = null!;
    private Button btnCancel = null!;

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
        components = new System.ComponentModel.Container();
        lblTitle = new Label();
        lblUsername = new Label();
        lblServerAddress = new Label();
        txtLoginUsername = new TextBox();
        txtServerAddress = new TextBox();
        btnLogin = new Button();
        btnCancel = new Button();
        lblPassWord = new Label();
        contextMenuStrip1 = new ContextMenuStrip(components);
        txtPassword = new TextBox();
        SuspendLayout();
        // 
        // lblTitle
        // 
        lblTitle.AutoSize = true;
        lblTitle.Font = new Font("Segoe UI", 14F, FontStyle.Bold);
        lblTitle.Location = new Point(550, 44);
        lblTitle.Name = "lblTitle";
        lblTitle.Size = new Size(161, 32);
        lblTitle.TabIndex = 0;
        lblTitle.Text = "ĐĂNG NHẬP";
        lblTitle.Click += lblTitle_Click;
        // 
        // lblUsername
        // 
        lblUsername.AutoSize = true;
        lblUsername.Location = new Point(461, 119);
        lblUsername.Name = "lblUsername";
        lblUsername.Size = new Size(107, 20);
        lblUsername.TabIndex = 1;
        lblUsername.Text = "Tên người chơi";
        // 
        // lblServerAddress
        // 
        lblServerAddress.AutoSize = true;
        lblServerAddress.Location = new Point(461, 209);
        lblServerAddress.Name = "lblServerAddress";
        lblServerAddress.Size = new Size(98, 20);
        lblServerAddress.TabIndex = 2;
        lblServerAddress.Text = "Địa chỉ server";
        // 
        // txtLoginUsername
        // 
        txtLoginUsername.Location = new Point(586, 115);
        txtLoginUsername.MaxLength = 30;
        txtLoginUsername.Name = "txtLoginUsername";
        txtLoginUsername.Size = new Size(215, 27);
        txtLoginUsername.TabIndex = 0;
        // 
        // txtServerAddress
        // 
        txtServerAddress.Location = new Point(586, 206);
        txtServerAddress.Name = "txtServerAddress";
        txtServerAddress.Size = new Size(215, 27);
        txtServerAddress.TabIndex = 1;
        txtServerAddress.Text = "tcp://localhost:8765";
        // 
        // btnLogin
        // 
        btnLogin.Location = new Point(586, 249);
        btnLogin.Name = "btnLogin";
        btnLogin.Size = new Size(105, 32);
        btnLogin.TabIndex = 2;
        btnLogin.Text = "Đăng nhập";
        btnLogin.UseVisualStyleBackColor = true;
        btnLogin.Click += btnLogin_Click;
        // 
        // btnCancel
        // 
        btnCancel.DialogResult = DialogResult.Cancel;
        btnCancel.Location = new Point(697, 249);
        btnCancel.Name = "btnCancel";
        btnCancel.Size = new Size(105, 32);
        btnCancel.TabIndex = 3;
        btnCancel.Text = "Thoát";
        btnCancel.UseVisualStyleBackColor = true;
        // 
        // lblPassWord
        // 
        lblPassWord.AutoSize = true;
        lblPassWord.Location = new Point(461, 163);
        lblPassWord.Name = "lblPassWord";
        lblPassWord.Size = new Size(70, 20);
        lblPassWord.TabIndex = 1;
        lblPassWord.Text = "Password";
        lblPassWord.Click += label1_Click;
        // 
        // contextMenuStrip1
        // 
        contextMenuStrip1.ImageScalingSize = new Size(20, 20);
        contextMenuStrip1.Name = "contextMenuStrip1";
        contextMenuStrip1.Size = new Size(61, 4);
        // 
        // txtPassword
        // 
        txtPassword.Location = new Point(586, 162);
        txtPassword.Name = "txtPassword";
        txtPassword.Size = new Size(215, 27);
        txtPassword.TabIndex = 5;
        // 
        // LoginForm
        // 
        AcceptButton = btnLogin;
        AutoScaleDimensions = new SizeF(8F, 20F);
        AutoScaleMode = AutoScaleMode.Font;
        BackgroundImage = Properties.Resources.nền_dn1;
        CancelButton = btnCancel;
        ClientSize = new Size(839, 518);
        Controls.Add(txtPassword);
        Controls.Add(btnCancel);
        Controls.Add(btnLogin);
        Controls.Add(txtServerAddress);
        Controls.Add(txtLoginUsername);
        Controls.Add(lblServerAddress);
        Controls.Add(lblPassWord);
        Controls.Add(lblUsername);
        Controls.Add(lblTitle);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        Name = "LoginForm";
        StartPosition = FormStartPosition.CenterScreen;
        Text = "Đăng nhập Caro";
        ResumeLayout(false);
        PerformLayout();
    }

    private Label lblPassWord;
    private ContextMenuStrip contextMenuStrip1;
    private TextBox txtPassword;
}
