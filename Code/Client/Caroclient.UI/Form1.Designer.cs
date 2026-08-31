namespace Caroclient.UI;

partial class Form1
{
    /// <summary>
    ///  Required designer variable.
    /// </summary>
    private System.ComponentModel.IContainer components = null;

    /// <summary>
    ///  Clean up any resources being used.
    /// </summary>
    /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
    protected override void Dispose(bool disposing)
    {
        if (disposing && (components != null))
        {
            components.Dispose();
        }
        base.Dispose(disposing);
    }

    #region Windows Form Designer generated code

    /// <summary>
    ///  Required method for Designer support - do not modify
    ///  the contents of this method with the code editor.
    /// </summary>
    private void InitializeComponent()
    {
        pnlChessBoard = new Panel();
        btnConnect = new Button();
        rtbLog = new RichTextBox();
        txtUsername = new TextBox();
        btnLogin = new Button();
        lstOnlinePlayers = new ListBox();
        btnInvite = new Button();
        btnSpectate = new Button();
        btnLeave = new Button();
        btnAccept = new Button();
        btnReject = new Button();
        btnSurrender = new Button();
        txtChatInput = new TextBox();
        gbInviteMessage = new GroupBox();
        lblInviteMessage = new Label();
        gpChat = new GroupBox();
        btnSendChat = new Button();
        txbPlayerName = new TextBox();
        pctbMark = new PictureBox();
        menuStrip1 = new MenuStrip();
        menuToolStripMenuItem = new ToolStripMenuItem();
        newGameToolStripMenuItem = new ToolStripMenuItem();
        quitToolStripMenuItem = new ToolStripMenuItem();
        gbInviteMessage.SuspendLayout();
        gpChat.SuspendLayout();
        ((System.ComponentModel.ISupportInitialize)pctbMark).BeginInit();
        menuStrip1.SuspendLayout();
        SuspendLayout();
        // 
        // pnlChessBoard
        // 
        pnlChessBoard.BackColor = SystemColors.ButtonFace;
        pnlChessBoard.BackgroundImage = Properties.Resources.abfa03f6_6d65_453f_9081_0ae2d9165caa;
        pnlChessBoard.ForeColor = SystemColors.ButtonHighlight;
        pnlChessBoard.Location = new Point(26, 119);
        pnlChessBoard.Name = "pnlChessBoard";
        pnlChessBoard.Size = new Size(450, 450);
        pnlChessBoard.TabIndex = 0;
        pnlChessBoard.Paint += pnlChessBoard_Paint;
        // 
        // btnConnect
        // 
        btnConnect.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        btnConnect.Location = new Point(515, 73);
        btnConnect.Name = "btnConnect";
        btnConnect.Size = new Size(341, 32);
        btnConnect.TabIndex = 1;
        btnConnect.Text = "Kết nối WebSocket";
        btnConnect.UseVisualStyleBackColor = true;
        // 
        // rtbLog
        // 
        rtbLog.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        rtbLog.Location = new Point(519, 390);
        rtbLog.Name = "rtbLog";
        rtbLog.Size = new Size(337, 94);
        rtbLog.TabIndex = 2;
        rtbLog.Text = "";
        // 
        // txtUsername
        // 
        txtUsername.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        txtUsername.Location = new Point(515, 40);
        txtUsername.Name = "txtUsername";
        txtUsername.Size = new Size(175, 27);
        txtUsername.TabIndex = 3;
        txtUsername.Text = "Player_01";
        // 
        // btnLogin
        // 
        btnLogin.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        btnLogin.Location = new Point(702, 40);
        btnLogin.Name = "btnLogin";
        btnLogin.Size = new Size(154, 28);
        btnLogin.TabIndex = 4;
        btnLogin.Text = "Đăng nhập";
        btnLogin.UseVisualStyleBackColor = true;
        // 
        // lstOnlinePlayers
        // 
        lstOnlinePlayers.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        lstOnlinePlayers.FormattingEnabled = true;
        lstOnlinePlayers.Location = new Point(515, 119);
        lstOnlinePlayers.Name = "lstOnlinePlayers";
        lstOnlinePlayers.Size = new Size(339, 84);
        lstOnlinePlayers.TabIndex = 5;
        // 
        // btnInvite
        // 
        btnInvite.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        btnInvite.Location = new Point(519, 213);
        btnInvite.Name = "btnInvite";
        btnInvite.Size = new Size(102, 29);
        btnInvite.TabIndex = 6;
        btnInvite.Text = "Mời đấu";
        btnInvite.UseVisualStyleBackColor = true;
        // 
        // btnSpectate
        // 
        btnSpectate.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        btnSpectate.Location = new Point(639, 213);
        btnSpectate.Name = "btnSpectate";
        btnSpectate.Size = new Size(102, 29);
        btnSpectate.TabIndex = 7;
        btnSpectate.Text = "Xem trận";
        btnSpectate.UseVisualStyleBackColor = true;
        btnSpectate.Click += button2_Click;
        // 
        // btnLeave
        // 
        btnLeave.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        btnLeave.Location = new Point(754, 213);
        btnLeave.Name = "btnLeave";
        btnLeave.Size = new Size(102, 29);
        btnLeave.TabIndex = 8;
        btnLeave.Text = "Rời phòng";
        btnLeave.UseVisualStyleBackColor = true;
        // 
        // btnAccept
        // 
        btnAccept.Location = new Point(33, 71);
        btnAccept.Name = "btnAccept";
        btnAccept.Size = new Size(94, 29);
        btnAccept.TabIndex = 9;
        btnAccept.Text = "Chấp nhận";
        btnAccept.UseVisualStyleBackColor = true;
        // 
        // btnReject
        // 
        btnReject.Location = new Point(198, 71);
        btnReject.Name = "btnReject";
        btnReject.Size = new Size(94, 29);
        btnReject.TabIndex = 10;
        btnReject.Text = "Từ chối";
        btnReject.UseVisualStyleBackColor = true;
        // 
        // btnSurrender
        // 
        btnSurrender.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        btnSurrender.Location = new Point(558, 357);
        btnSurrender.Name = "btnSurrender";
        btnSurrender.Size = new Size(94, 29);
        btnSurrender.TabIndex = 11;
        btnSurrender.Text = "Đầu hàng";
        btnSurrender.UseVisualStyleBackColor = true;
        // 
        // txtChatInput
        // 
        txtChatInput.Location = new Point(15, 26);
        txtChatInput.Name = "txtChatInput";
        txtChatInput.Size = new Size(216, 27);
        txtChatInput.TabIndex = 12;
        txtChatInput.Text = "Nhập tin nhắn: ";
        // 
        // gbInviteMessage
        // 
        gbInviteMessage.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        gbInviteMessage.Controls.Add(lblInviteMessage);
        gbInviteMessage.Controls.Add(btnReject);
        gbInviteMessage.Controls.Add(btnAccept);
        gbInviteMessage.Location = new Point(519, 248);
        gbInviteMessage.Name = "gbInviteMessage";
        gbInviteMessage.Size = new Size(335, 106);
        gbInviteMessage.TabIndex = 13;
        gbInviteMessage.TabStop = false;
        gbInviteMessage.Text = "Lời mời thách đấu";
        gbInviteMessage.Enter += groupBox1_Enter;
        // 
        // lblInviteMessage
        // 
        lblInviteMessage.AutoSize = true;
        lblInviteMessage.Location = new Point(95, 35);
        lblInviteMessage.Name = "lblInviteMessage";
        lblInviteMessage.Size = new Size(152, 20);
        lblInviteMessage.TabIndex = 11;
        lblInviteMessage.Text = "Chưa có lời mời nào...";
        lblInviteMessage.Click += label1_Click;
        // 
        // gpChat
        // 
        gpChat.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        gpChat.Controls.Add(btnSendChat);
        gpChat.Controls.Add(txtChatInput);
        gpChat.Location = new Point(521, 490);
        gpChat.Name = "gpChat";
        gpChat.Size = new Size(335, 69);
        gpChat.TabIndex = 14;
        gpChat.TabStop = false;
        gpChat.Text = "Trò chuyện";
        // 
        // btnSendChat
        // 
        btnSendChat.Location = new Point(235, 26);
        btnSendChat.Name = "btnSendChat";
        btnSendChat.Size = new Size(94, 29);
        btnSendChat.TabIndex = 13;
        btnSendChat.Text = "Gửi";
        btnSendChat.UseVisualStyleBackColor = true;
        // 
        // txbPlayerName
        // 
        txbPlayerName.Location = new Point(122, 54);
        txbPlayerName.Name = "txbPlayerName";
        txbPlayerName.Size = new Size(125, 27);
        txbPlayerName.TabIndex = 15;
        // 
        // pctbMark
        // 
        pctbMark.Location = new Point(272, 29);
        pctbMark.Name = "pctbMark";
        pctbMark.Size = new Size(106, 88);
        pctbMark.SizeMode = PictureBoxSizeMode.StretchImage;
        pctbMark.TabIndex = 16;
        pctbMark.TabStop = false;
        pctbMark.Click += pictureBox1_Click;
        // 
        // menuStrip1
        // 
        menuStrip1.ImageScalingSize = new Size(20, 20);
        menuStrip1.Items.AddRange(new ToolStripItem[] { menuToolStripMenuItem });
        menuStrip1.Location = new Point(0, 0);
        menuStrip1.Name = "menuStrip1";
        menuStrip1.Size = new Size(888, 28);
        menuStrip1.TabIndex = 17;
        menuStrip1.Text = "menuStrip1";
        // 
        // menuToolStripMenuItem
        // 
        menuToolStripMenuItem.DropDownItems.AddRange(new ToolStripItem[] { newGameToolStripMenuItem, quitToolStripMenuItem });
        menuToolStripMenuItem.Name = "menuToolStripMenuItem";
        menuToolStripMenuItem.Size = new Size(60, 24);
        menuToolStripMenuItem.Text = "Menu";
        // 
        // newGameToolStripMenuItem
        // 
        newGameToolStripMenuItem.Name = "newGameToolStripMenuItem";
        newGameToolStripMenuItem.Size = new Size(224, 26);
        newGameToolStripMenuItem.Text = "New game";
        newGameToolStripMenuItem.Click += newGameToolStripMenuItem_Click;
        // 
        // quitToolStripMenuItem
        // 
        quitToolStripMenuItem.Name = "quitToolStripMenuItem";
        quitToolStripMenuItem.Size = new Size(224, 26);
        quitToolStripMenuItem.Text = "Quit";
        quitToolStripMenuItem.Click += quitToolStripMenuItem_Click;
        // 
        // Form1
        // 
        AutoScaleDimensions = new SizeF(8F, 20F);
        AutoScaleMode = AutoScaleMode.Font;
        BackColor = SystemColors.ControlLight;
        BackgroundImage = Properties.Resources.abfa03f6_6d65_453f_9081_0ae2d9165caa;
        ClientSize = new Size(888, 571);
        Controls.Add(pctbMark);
        Controls.Add(txbPlayerName);
        Controls.Add(gpChat);
        Controls.Add(gbInviteMessage);
        Controls.Add(btnSurrender);
        Controls.Add(btnLeave);
        Controls.Add(btnSpectate);
        Controls.Add(btnInvite);
        Controls.Add(lstOnlinePlayers);
        Controls.Add(btnLogin);
        Controls.Add(txtUsername);
        Controls.Add(rtbLog);
        Controls.Add(btnConnect);
        Controls.Add(pnlChessBoard);
        Controls.Add(menuStrip1);
        ForeColor = SystemColors.ActiveCaptionText;
        MainMenuStrip = menuStrip1;
        Name = "Form1";
        Text = "Form1";
        FormClosing += Form1_FormClosing;
        Load += Form1_Load;
        gbInviteMessage.ResumeLayout(false);
        gbInviteMessage.PerformLayout();
        gpChat.ResumeLayout(false);
        gpChat.PerformLayout();
        ((System.ComponentModel.ISupportInitialize)pctbMark).EndInit();
        menuStrip1.ResumeLayout(false);
        menuStrip1.PerformLayout();
        ResumeLayout(false);
        PerformLayout();
    }

    #endregion

    private Panel pnlChessBoard;
    private Button btnConnect;
    private RichTextBox rtbLog;
    private TextBox txtUsername;
    private Button btnLogin;
    private ListBox lstOnlinePlayers;
    private Button btnInvite;
    private Button btnSpectate;
    private Button btnLeave;
    private Button btnAccept;
    private Button btnReject;
    private Button btnSurrender;
    private TextBox txtChatInput;
    private GroupBox gbInviteMessage;
    private Label lblInviteMessage;
    private GroupBox gpChat;
    private Button btnSendChat;
    private TextBox textBox1;
    private PictureBox pctbMark;
    private TextBox txbPlayerName;
    private MenuStrip menuStrip1;
    private ToolStripMenuItem menuToolStripMenuItem;
    private ToolStripMenuItem newGameToolStripMenuItem;
    private ToolStripMenuItem quitToolStripMenuItem;
}
