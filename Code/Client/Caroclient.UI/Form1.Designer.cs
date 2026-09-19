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
        ptbTitle = new PictureBox();
        btnInvite = new Button();
        btnSpectate = new Button();
        btnLeave = new Button();
        txbPlayerName1 = new TextBox();
        pctbMark = new PictureBox();
        menuStrip1 = new MenuStrip();
        menuToolStripMenuItem = new ToolStripMenuItem();
        newGameToolStripMenuItem = new ToolStripMenuItem();
        thôngTinToolStripMenuItem = new ToolStripMenuItem();
        tàiKhoảnCủaTôiToolStripMenuItem = new ToolStripMenuItem();
        hồSơCủaTôiToolStripMenuItem = new ToolStripMenuItem();
        quitToolStripMenuItem = new ToolStripMenuItem();
        button1 = new Button();
        button2 = new Button();
        txtPlayerName2 = new TextBox();
        txtScorePlayer2 = new TextBox();
        txtScorePlayer1 = new TextBox();
        ((System.ComponentModel.ISupportInitialize)ptbTitle).BeginInit();
        ((System.ComponentModel.ISupportInitialize)pctbMark).BeginInit();
        menuStrip1.SuspendLayout();
        SuspendLayout();
        // 
        // pnlChessBoard
        // 
        pnlChessBoard.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
        pnlChessBoard.BackColor = SystemColors.ButtonFace;
        pnlChessBoard.BackgroundImage = Properties.Resources.abfa03f6_6d65_453f_9081_0ae2d9165caa;
        pnlChessBoard.BackgroundImageLayout = ImageLayout.Stretch;
        pnlChessBoard.ForeColor = SystemColors.ButtonHighlight;
        pnlChessBoard.Location = new Point(187, 112);
        pnlChessBoard.Name = "pnlChessBoard";
        // 15 o x 30px = 450. De 424 thi ban co bi cat mat 26px ben phai.
        pnlChessBoard.Size = new Size(450, 450);
        pnlChessBoard.TabIndex = 0;
        pnlChessBoard.Paint += pnlChessBoard_Paint;
        // 
        // ptbTitle
        // 
        ptbTitle.Anchor = AnchorStyles.Top;
        ptbTitle.Image = Properties.Resources.title;
        ptbTitle.Location = new Point(287, 31);
        ptbTitle.Name = "ptbTitle";
        ptbTitle.Size = new Size(237, 75);
        ptbTitle.SizeMode = PictureBoxSizeMode.Zoom;
        ptbTitle.TabIndex = 20;
        ptbTitle.TabStop = false;
        // 
        // btnInvite
        // 
        btnInvite.Anchor = AnchorStyles.Top | AnchorStyles.Left;
        btnInvite.Location = new Point(24, 214);
        btnInvite.Name = "btnInvite";
        btnInvite.Size = new Size(129, 29);
        btnInvite.TabIndex = 6;
        btnInvite.Text = "Bạn bè";
        btnInvite.UseVisualStyleBackColor = true;
        btnInvite.Click += btnInvite_Click;
        // 
        // btnSpectate
        // 
        btnSpectate.Anchor = AnchorStyles.Top | AnchorStyles.Left;
        btnSpectate.Location = new Point(24, 286);
        btnSpectate.Name = "btnSpectate";
        btnSpectate.Size = new Size(129, 29);
        btnSpectate.TabIndex = 7;
        btnSpectate.Text = "Lịch sử ";
        btnSpectate.UseVisualStyleBackColor = true;
        btnSpectate.Click += btnSpectate_Click;
        // 
        // btnLeave
        // 
        btnLeave.Anchor = AnchorStyles.Top | AnchorStyles.Left;
        btnLeave.Location = new Point(24, 425);
        btnLeave.Name = "btnLeave";
        btnLeave.Size = new Size(129, 29);
        btnLeave.TabIndex = 8;
        btnLeave.Text = "Chơi với máy";
        btnLeave.UseVisualStyleBackColor = true;
        // 
        // txbPlayerName1
        // 
        txbPlayerName1.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        txbPlayerName1.Location = new Point(684, 134);
        txbPlayerName1.Name = "txbPlayerName1";
        txbPlayerName1.ReadOnly = true;
        txbPlayerName1.Size = new Size(125, 27);
        txbPlayerName1.TabIndex = 15;
        // 
        // pctbMark
        // 
        pctbMark.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        pctbMark.Location = new Point(693, 227);
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
        menuStrip1.Size = new Size(858, 28);
        menuStrip1.TabIndex = 17;
        menuStrip1.Text = "menuStrip1";
        // 
        // menuToolStripMenuItem
        // 
        menuToolStripMenuItem.DropDownItems.AddRange(new ToolStripItem[] { newGameToolStripMenuItem, thôngTinToolStripMenuItem, quitToolStripMenuItem });
        menuToolStripMenuItem.Name = "menuToolStripMenuItem";
        menuToolStripMenuItem.Size = new Size(60, 24);
        menuToolStripMenuItem.Text = "Menu";
        // 
        // newGameToolStripMenuItem
        // 
        newGameToolStripMenuItem.Name = "newGameToolStripMenuItem";
        newGameToolStripMenuItem.Size = new Size(164, 26);
        newGameToolStripMenuItem.Text = "New game";
        newGameToolStripMenuItem.Click += newGameToolStripMenuItem_Click;
        // 
        // thôngTinToolStripMenuItem
        // 
        thôngTinToolStripMenuItem.DropDownItems.AddRange(new ToolStripItem[] { tàiKhoảnCủaTôiToolStripMenuItem, hồSơCủaTôiToolStripMenuItem });
        thôngTinToolStripMenuItem.Name = "thôngTinToolStripMenuItem";
        thôngTinToolStripMenuItem.Size = new Size(164, 26);
        thôngTinToolStripMenuItem.Text = "Thông tin ";
        thôngTinToolStripMenuItem.Click += thôngTinToolStripMenuItem_Click;
        // 
        // tàiKhoảnCủaTôiToolStripMenuItem
        // 
        tàiKhoảnCủaTôiToolStripMenuItem.Name = "tàiKhoảnCủaTôiToolStripMenuItem";
        tàiKhoảnCủaTôiToolStripMenuItem.Size = new Size(203, 26);
        tàiKhoảnCủaTôiToolStripMenuItem.Text = "Tài khoản của tôi";
        tàiKhoảnCủaTôiToolStripMenuItem.Click += tàiKhoảnCủaTôiToolStripMenuItem_Click;
        // 
        // hồSơCủaTôiToolStripMenuItem
        // 
        hồSơCủaTôiToolStripMenuItem.Name = "hồSơCủaTôiToolStripMenuItem";
        hồSơCủaTôiToolStripMenuItem.Size = new Size(203, 26);
        hồSơCủaTôiToolStripMenuItem.Text = "Hồ sơ của tôi";
        hồSơCủaTôiToolStripMenuItem.Click += hồSơCủaTôiToolStripMenuItem_Click;
        // 
        // quitToolStripMenuItem
        // 
        quitToolStripMenuItem.Name = "quitToolStripMenuItem";
        quitToolStripMenuItem.Size = new Size(164, 26);
        quitToolStripMenuItem.Text = "Quit";
        quitToolStripMenuItem.Click += quitToolStripMenuItem_Click;
        // 
        // button1
        // 
        button1.Anchor = AnchorStyles.Top | AnchorStyles.Left;
        button1.Location = new Point(24, 151);
        button1.Name = "button1";
        button1.Size = new Size(129, 29);
        button1.TabIndex = 18;
        button1.Text = "Nhắn tin";
        button1.UseVisualStyleBackColor = true;
        button1.Click += button1_Click;
        // 
        // button2
        // 
        button2.Anchor = AnchorStyles.Top | AnchorStyles.Left;
        button2.Location = new Point(24, 358);
        button2.Name = "button2";
        button2.Size = new Size(129, 29);
        button2.TabIndex = 19;
        button2.Text = "Mời đấu";
        button2.UseVisualStyleBackColor = true;
        button2.Click += button2_Click;
        // 
        // txtPlayerName2
        // 
        txtPlayerName2.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        txtPlayerName2.Location = new Point(684, 341);
        txtPlayerName2.Name = "txtPlayerName2";
        txtPlayerName2.ReadOnly = true;
        txtPlayerName2.Size = new Size(125, 27);
        txtPlayerName2.TabIndex = 15;
        // 
        // txtScorePlayer2
        // 
        txtScorePlayer2.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        txtScorePlayer2.Location = new Point(684, 377);
        txtScorePlayer2.Name = "txtScorePlayer2";
        txtScorePlayer2.ReadOnly = true;
        txtScorePlayer2.Size = new Size(125, 27);
        txtScorePlayer2.TabIndex = 15;
        txtScorePlayer2.TextAlign = HorizontalAlignment.Center;
        // 
        // txtScorePlayer1
        // 
        txtScorePlayer1.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        txtScorePlayer1.Location = new Point(684, 167);
        txtScorePlayer1.Name = "txtScorePlayer1";
        txtScorePlayer1.ReadOnly = true;
        txtScorePlayer1.Size = new Size(125, 27);
        txtScorePlayer1.TabIndex = 15;
        txtScorePlayer1.TextAlign = HorizontalAlignment.Center;
        // 
        // Form1
        // 
        AutoScaleDimensions = new SizeF(8F, 20F);
        AutoScaleMode = AutoScaleMode.Font;
        BackColor = SystemColors.ControlLight;
        BackgroundImage = Properties.Resources.abfa03f6_6d65_453f_9081_0ae2d9165caa;
        BackgroundImageLayout = ImageLayout.Stretch;
        // Khop voi kich thuoc that luc chay: BuildOnlineUi dung panel online
        // toi x=1160, de 858 thi designer va runtime lech nhau, Anchor tinh sai.
        ClientSize = new Size(1190, 600);
        Controls.Add(button1);
        Controls.Add(button2);
        Controls.Add(ptbTitle);
        Controls.Add(pctbMark);
        Controls.Add(txtPlayerName2);
        Controls.Add(txtScorePlayer1);
        Controls.Add(txtScorePlayer2);
        Controls.Add(txbPlayerName1);
        Controls.Add(btnLeave);
        Controls.Add(btnSpectate);
        Controls.Add(btnInvite);
        Controls.Add(pnlChessBoard);
        Controls.Add(menuStrip1);
        ForeColor = SystemColors.ActiveCaptionText;
        MainMenuStrip = menuStrip1;
        Name = "Form1";
        Text = "Form1";
        FormClosing += Form1_FormClosing;
        Load += Form1_Load;
        ((System.ComponentModel.ISupportInitialize)ptbTitle).EndInit();
        ((System.ComponentModel.ISupportInitialize)pctbMark).EndInit();
        menuStrip1.ResumeLayout(false);
        menuStrip1.PerformLayout();
        ResumeLayout(false);
        PerformLayout();
    }

    #endregion

    private Panel pnlChessBoard;
    private PictureBox ptbTitle;
    private RichTextBox rtbLog;
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
    private PictureBox pctbMark;
    private TextBox txbPlayerName1;
    private MenuStrip menuStrip1;
    private ToolStripMenuItem menuToolStripMenuItem;
    private ToolStripMenuItem newGameToolStripMenuItem;
    private ToolStripMenuItem quitToolStripMenuItem;
    private ToolStripMenuItem thôngTinToolStripMenuItem;
    private ToolStripMenuItem tàiKhoảnCủaTôiToolStripMenuItem;
    private ToolStripMenuItem hồSơCủaTôiToolStripMenuItem;
    private Button button1;
    private Button button2;
    private TextBox txtPlayerName2;
    private TextBox txtScorePlayer2;
    private TextBox txtScorePlayer1;
}
