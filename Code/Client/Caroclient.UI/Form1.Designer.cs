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
        menuStrip1 = new MenuStrip();
        menuToolStripMenuItem = new ToolStripMenuItem();
        newGameToolStripMenuItem = new ToolStripMenuItem();
        quitToolStripMenuItem = new ToolStripMenuItem();
        thôngTinToolStripMenuItem = new ToolStripMenuItem();
        tàiKhoảnCủaTôiToolStripMenuItem = new ToolStripMenuItem();
        hồSơCủaTôiToolStripMenuItem = new ToolStripMenuItem();
        tínhNăngToolStripMenuItem = new ToolStripMenuItem();
        bạnBèToolStripMenuItem = new ToolStripMenuItem();
        nhắnTinToolStripMenuItem = new ToolStripMenuItem();
        lịchSửToolStripMenuItem = new ToolStripMenuItem();
        tlpRoot = new TableLayoutPanel();
        flpActions = new FlowLayoutPanel();
        btnInvitePlayer = new Button();
        btnSpectateMatch = new Button();
        btnLeaveRoom = new Button();
        tlpCenter = new TableLayoutPanel();
        ptbTitle = new PictureBox();
        tlpScore = new TableLayoutPanel();
        txbPlayerName1 = new TextBox();
        txtScorePlayer1 = new TextBox();
        pctbMark = new PictureBox();
        txtScorePlayer2 = new TextBox();
        txtPlayerName2 = new TextBox();
        pnlChessBoard = new Panel();
        lblTurnClock = new Label();
        tlpOnline = new TableLayoutPanel();
        lblOnline = new Label();
        lstOnlinePlayers = new ListBox();
        btnRefreshPlayers = new Button();
        gbInviteMessage = new GroupBox();
        lblInviteMessage = new Label();
        btnAccept = new Button();
        btnReject = new Button();
        rtbLog = new RichTextBox();
        menuStrip1.SuspendLayout();
        tlpRoot.SuspendLayout();
        flpActions.SuspendLayout();
        tlpCenter.SuspendLayout();
        ((System.ComponentModel.ISupportInitialize)ptbTitle).BeginInit();
        tlpScore.SuspendLayout();
        ((System.ComponentModel.ISupportInitialize)pctbMark).BeginInit();
        tlpOnline.SuspendLayout();
        gbInviteMessage.SuspendLayout();
        SuspendLayout();
        // 
        // menuStrip1
        // 
        menuStrip1.ImageScalingSize = new Size(20, 20);
        menuStrip1.Items.AddRange(new ToolStripItem[] { menuToolStripMenuItem, thôngTinToolStripMenuItem, tínhNăngToolStripMenuItem });
        menuStrip1.Location = new Point(0, 0);
        menuStrip1.Name = "menuStrip1";
        menuStrip1.Size = new Size(1060, 28);
        menuStrip1.TabIndex = 0;
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
        newGameToolStripMenuItem.Size = new Size(164, 26);
        newGameToolStripMenuItem.Text = "New game";
        newGameToolStripMenuItem.Click += newGameToolStripMenuItem_Click;
        // 
        // quitToolStripMenuItem
        // 
        quitToolStripMenuItem.Name = "quitToolStripMenuItem";
        quitToolStripMenuItem.Size = new Size(164, 26);
        quitToolStripMenuItem.Text = "Quit";
        quitToolStripMenuItem.Click += quitToolStripMenuItem_Click;
        // 
        // thôngTinToolStripMenuItem
        // 
        thôngTinToolStripMenuItem.DropDownItems.AddRange(new ToolStripItem[] { tàiKhoảnCủaTôiToolStripMenuItem, hồSơCủaTôiToolStripMenuItem });
        thôngTinToolStripMenuItem.Name = "thôngTinToolStripMenuItem";
        thôngTinToolStripMenuItem.Size = new Size(92, 24);
        thôngTinToolStripMenuItem.Text = "Thông tin";
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
        // tínhNăngToolStripMenuItem
        // 
        tínhNăngToolStripMenuItem.DropDownItems.AddRange(new ToolStripItem[] { bạnBèToolStripMenuItem, nhắnTinToolStripMenuItem, lịchSửToolStripMenuItem });
        tínhNăngToolStripMenuItem.Name = "tínhNăngToolStripMenuItem";
        tínhNăngToolStripMenuItem.Size = new Size(92, 24);
        tínhNăngToolStripMenuItem.Text = "Tính năng";
        // 
        // bạnBèToolStripMenuItem
        // 
        bạnBèToolStripMenuItem.Name = "bạnBèToolStripMenuItem";
        bạnBèToolStripMenuItem.Size = new Size(164, 26);
        bạnBèToolStripMenuItem.Text = "Bạn bè";
        bạnBèToolStripMenuItem.Click += bạnBèToolStripMenuItem_Click;
        // 
        // nhắnTinToolStripMenuItem
        // 
        nhắnTinToolStripMenuItem.Name = "nhắnTinToolStripMenuItem";
        nhắnTinToolStripMenuItem.Size = new Size(164, 26);
        nhắnTinToolStripMenuItem.Text = "Nhắn tin";
        nhắnTinToolStripMenuItem.Click += nhắnTinToolStripMenuItem_Click;
        // 
        // lịchSửToolStripMenuItem
        // 
        lịchSửToolStripMenuItem.Name = "lịchSửToolStripMenuItem";
        lịchSửToolStripMenuItem.Size = new Size(164, 26);
        lịchSửToolStripMenuItem.Text = "Lịch sử";
        lịchSửToolStripMenuItem.Click += lịchSửToolStripMenuItem_Click;
        // 
        // tlpRoot
        // 
        // 3 cot: hanh dong van dau | ban co | phan choi mang.
        // Hai cot bien co be rong co dinh, cot giua an het cho con lai.
        tlpRoot.BackColor = Color.Transparent;
        tlpRoot.ColumnCount = 3;
        tlpRoot.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 170F));
        tlpRoot.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F));
        tlpRoot.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 330F));
        tlpRoot.Controls.Add(flpActions, 0, 0);
        tlpRoot.Controls.Add(tlpCenter, 1, 0);
        tlpRoot.Controls.Add(tlpOnline, 2, 0);
        tlpRoot.Dock = DockStyle.Fill;
        tlpRoot.Location = new Point(0, 28);
        tlpRoot.Name = "tlpRoot";
        tlpRoot.RowCount = 1;
        tlpRoot.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
        tlpRoot.Size = new Size(1060, 672);
        tlpRoot.TabIndex = 1;
        // 
        // flpActions
        // 
        flpActions.BackColor = Color.Transparent;
        flpActions.Controls.Add(btnInvitePlayer);
        flpActions.Controls.Add(btnSpectateMatch);
        flpActions.Controls.Add(btnLeaveRoom);
        flpActions.Dock = DockStyle.Fill;
        flpActions.FlowDirection = FlowDirection.TopDown;
        flpActions.Location = new Point(3, 3);
        flpActions.Name = "flpActions";
        flpActions.Padding = new Padding(8, 24, 8, 8);
        flpActions.Size = new Size(164, 666);
        flpActions.TabIndex = 0;
        // 
        // btnInvitePlayer
        // 
        btnInvitePlayer.Location = new Point(11, 27);
        btnInvitePlayer.Margin = new Padding(3, 3, 3, 12);
        btnInvitePlayer.Name = "btnInvitePlayer";
        btnInvitePlayer.Size = new Size(140, 36);
        btnInvitePlayer.TabIndex = 0;
        btnInvitePlayer.Text = "Mời đấu";
        btnInvitePlayer.UseVisualStyleBackColor = true;
        // 
        // btnSpectateMatch
        // 
        btnSpectateMatch.Location = new Point(11, 78);
        btnSpectateMatch.Margin = new Padding(3, 3, 3, 12);
        btnSpectateMatch.Name = "btnSpectateMatch";
        btnSpectateMatch.Size = new Size(140, 36);
        btnSpectateMatch.TabIndex = 1;
        btnSpectateMatch.Text = "Xem trận";
        btnSpectateMatch.UseVisualStyleBackColor = true;
        // 
        // btnLeaveRoom
        // 
        btnLeaveRoom.Enabled = false;
        btnLeaveRoom.Location = new Point(11, 129);
        btnLeaveRoom.Margin = new Padding(3, 3, 3, 12);
        btnLeaveRoom.Name = "btnLeaveRoom";
        btnLeaveRoom.Size = new Size(140, 36);
        btnLeaveRoom.TabIndex = 2;
        btnLeaveRoom.Text = "Rời phòng";
        btnLeaveRoom.UseVisualStyleBackColor = true;
        // 
        // tlpCenter
        // 
        // 4 hang: tieu de | bang ti so | ban co | dong ho.
        // Chi hang ban co gian ra, ba hang con lai cao co dinh.
        tlpCenter.BackColor = Color.Transparent;
        tlpCenter.ColumnCount = 1;
        tlpCenter.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F));
        tlpCenter.Controls.Add(ptbTitle, 0, 0);
        tlpCenter.Controls.Add(tlpScore, 0, 1);
        tlpCenter.Controls.Add(pnlChessBoard, 0, 2);
        tlpCenter.Controls.Add(lblTurnClock, 0, 3);
        tlpCenter.Dock = DockStyle.Fill;
        tlpCenter.Location = new Point(173, 3);
        tlpCenter.Name = "tlpCenter";
        tlpCenter.RowCount = 4;
        tlpCenter.RowStyles.Add(new RowStyle(SizeType.Absolute, 84F));
        tlpCenter.RowStyles.Add(new RowStyle(SizeType.Absolute, 68F));
        tlpCenter.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
        tlpCenter.RowStyles.Add(new RowStyle(SizeType.Absolute, 34F));
        tlpCenter.Size = new Size(554, 666);
        tlpCenter.TabIndex = 1;
        // 
        // ptbTitle
        // 
        ptbTitle.Dock = DockStyle.Fill;
        ptbTitle.Image = Properties.Resources.title;
        ptbTitle.Location = new Point(3, 3);
        ptbTitle.Name = "ptbTitle";
        ptbTitle.Size = new Size(548, 78);
        ptbTitle.SizeMode = PictureBoxSizeMode.Zoom;
        ptbTitle.TabIndex = 0;
        ptbTitle.TabStop = false;
        // 
        // tlpScore
        // 
        // Ten X | diem X | quan dang di | diem O | ten O
        tlpScore.BackColor = Color.Transparent;
        tlpScore.ColumnCount = 5;
        tlpScore.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50F));
        tlpScore.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 56F));
        tlpScore.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 62F));
        tlpScore.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 56F));
        tlpScore.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50F));
        tlpScore.Controls.Add(txbPlayerName1, 0, 0);
        tlpScore.Controls.Add(txtScorePlayer1, 1, 0);
        tlpScore.Controls.Add(pctbMark, 2, 0);
        tlpScore.Controls.Add(txtScorePlayer2, 3, 0);
        tlpScore.Controls.Add(txtPlayerName2, 4, 0);
        tlpScore.Dock = DockStyle.Fill;
        tlpScore.Location = new Point(3, 87);
        tlpScore.Name = "tlpScore";
        tlpScore.RowCount = 1;
        tlpScore.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
        tlpScore.Size = new Size(548, 62);
        tlpScore.TabIndex = 1;
        // 
        // txbPlayerName1
        // 
        txbPlayerName1.Anchor = AnchorStyles.Left | AnchorStyles.Right;
        txbPlayerName1.Location = new Point(3, 17);
        txbPlayerName1.Name = "txbPlayerName1";
        txbPlayerName1.ReadOnly = true;
        txbPlayerName1.Size = new Size(180, 27);
        txbPlayerName1.TabIndex = 0;
        // 
        // txtScorePlayer1
        // 
        txtScorePlayer1.Anchor = AnchorStyles.Left | AnchorStyles.Right;
        txtScorePlayer1.Location = new Point(189, 17);
        txtScorePlayer1.Name = "txtScorePlayer1";
        txtScorePlayer1.ReadOnly = true;
        txtScorePlayer1.Size = new Size(50, 27);
        txtScorePlayer1.TabIndex = 1;
        txtScorePlayer1.TextAlign = HorizontalAlignment.Center;
        // 
        // pctbMark
        // 
        pctbMark.Dock = DockStyle.Fill;
        pctbMark.Location = new Point(245, 3);
        pctbMark.Name = "pctbMark";
        pctbMark.Size = new Size(56, 56);
        pctbMark.SizeMode = PictureBoxSizeMode.Zoom;
        pctbMark.TabIndex = 2;
        pctbMark.TabStop = false;
        // 
        // txtScorePlayer2
        // 
        txtScorePlayer2.Anchor = AnchorStyles.Left | AnchorStyles.Right;
        txtScorePlayer2.Location = new Point(307, 17);
        txtScorePlayer2.Name = "txtScorePlayer2";
        txtScorePlayer2.ReadOnly = true;
        txtScorePlayer2.Size = new Size(50, 27);
        txtScorePlayer2.TabIndex = 3;
        txtScorePlayer2.TextAlign = HorizontalAlignment.Center;
        // 
        // txtPlayerName2
        // 
        txtPlayerName2.Anchor = AnchorStyles.Left | AnchorStyles.Right;
        txtPlayerName2.Location = new Point(363, 17);
        txtPlayerName2.Name = "txtPlayerName2";
        txtPlayerName2.ReadOnly = true;
        txtPlayerName2.Size = new Size(182, 27);
        txtPlayerName2.TabIndex = 4;
        // 
        // pnlChessBoard
        // 
        // 15 o x 30px = 450. Anchor None de TableLayoutPanel tu canh giua o.
        pnlChessBoard.Anchor = AnchorStyles.None;
        pnlChessBoard.BackColor = SystemColors.ButtonFace;
        pnlChessBoard.BackgroundImage = Properties.Resources.abfa03f6_6d65_453f_9081_0ae2d9165caa;
        pnlChessBoard.BackgroundImageLayout = ImageLayout.Stretch;
        pnlChessBoard.ForeColor = SystemColors.ButtonHighlight;
        pnlChessBoard.Location = new Point(52, 179);
        pnlChessBoard.Name = "pnlChessBoard";
        pnlChessBoard.Size = new Size(450, 450);
        pnlChessBoard.TabIndex = 2;
        // 
        // lblTurnClock
        // 
        lblTurnClock.Dock = DockStyle.Fill;
        lblTurnClock.Font = new Font("Segoe UI", 12F, FontStyle.Bold);
        lblTurnClock.Location = new Point(3, 632);
        lblTurnClock.Name = "lblTurnClock";
        lblTurnClock.Size = new Size(548, 34);
        lblTurnClock.TabIndex = 3;
        lblTurnClock.TextAlign = ContentAlignment.MiddleCenter;
        lblTurnClock.Visible = false;
        // 
        // tlpOnline
        // 
        // 5 hang: nhan | danh sach | lam moi | loi moi | nhat ky.
        // Danh sach va nhat ky chia nhau phan chieu cao du ra.
        tlpOnline.BackColor = Color.Transparent;
        tlpOnline.ColumnCount = 1;
        tlpOnline.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F));
        tlpOnline.Controls.Add(lblOnline, 0, 0);
        tlpOnline.Controls.Add(lstOnlinePlayers, 0, 1);
        tlpOnline.Controls.Add(btnRefreshPlayers, 0, 2);
        tlpOnline.Controls.Add(gbInviteMessage, 0, 3);
        tlpOnline.Controls.Add(rtbLog, 0, 4);
        tlpOnline.Dock = DockStyle.Fill;
        tlpOnline.Location = new Point(733, 3);
        tlpOnline.Name = "tlpOnline";
        tlpOnline.Padding = new Padding(0, 24, 8, 8);
        tlpOnline.RowCount = 5;
        tlpOnline.RowStyles.Add(new RowStyle(SizeType.Absolute, 28F));
        tlpOnline.RowStyles.Add(new RowStyle(SizeType.Percent, 50F));
        tlpOnline.RowStyles.Add(new RowStyle(SizeType.Absolute, 42F));
        tlpOnline.RowStyles.Add(new RowStyle(SizeType.Absolute, 112F));
        tlpOnline.RowStyles.Add(new RowStyle(SizeType.Percent, 50F));
        tlpOnline.Size = new Size(324, 666);
        tlpOnline.TabIndex = 2;
        // 
        // lblOnline
        // 
        lblOnline.Dock = DockStyle.Fill;
        lblOnline.Location = new Point(3, 27);
        lblOnline.Name = "lblOnline";
        lblOnline.Size = new Size(310, 28);
        lblOnline.TabIndex = 0;
        lblOnline.Text = "Người chơi online";
        lblOnline.TextAlign = ContentAlignment.MiddleLeft;
        // 
        // lstOnlinePlayers
        // 
        lstOnlinePlayers.Dock = DockStyle.Fill;
        lstOnlinePlayers.ItemHeight = 20;
        lstOnlinePlayers.Location = new Point(3, 58);
        lstOnlinePlayers.Name = "lstOnlinePlayers";
        lstOnlinePlayers.Size = new Size(310, 226);
        lstOnlinePlayers.TabIndex = 1;
        // 
        // btnRefreshPlayers
        // 
        btnRefreshPlayers.Dock = DockStyle.Fill;
        btnRefreshPlayers.Location = new Point(3, 290);
        btnRefreshPlayers.Margin = new Padding(3, 3, 3, 9);
        btnRefreshPlayers.Name = "btnRefreshPlayers";
        btnRefreshPlayers.Size = new Size(310, 30);
        btnRefreshPlayers.TabIndex = 2;
        btnRefreshPlayers.Text = "Làm mới danh sách";
        btnRefreshPlayers.UseVisualStyleBackColor = true;
        // 
        // gbInviteMessage
        // 
        gbInviteMessage.Controls.Add(lblInviteMessage);
        gbInviteMessage.Controls.Add(btnAccept);
        gbInviteMessage.Controls.Add(btnReject);
        gbInviteMessage.Dock = DockStyle.Fill;
        gbInviteMessage.Location = new Point(3, 332);
        gbInviteMessage.Name = "gbInviteMessage";
        gbInviteMessage.Size = new Size(310, 106);
        gbInviteMessage.TabIndex = 3;
        gbInviteMessage.TabStop = false;
        gbInviteMessage.Text = "Lời mời";
        gbInviteMessage.Visible = false;
        // 
        // lblInviteMessage
        // 
        lblInviteMessage.Dock = DockStyle.Top;
        lblInviteMessage.Location = new Point(3, 23);
        lblInviteMessage.Name = "lblInviteMessage";
        lblInviteMessage.Size = new Size(304, 38);
        lblInviteMessage.TabIndex = 0;
        // 
        // btnAccept
        // 
        btnAccept.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
        btnAccept.Location = new Point(12, 66);
        btnAccept.Name = "btnAccept";
        btnAccept.Size = new Size(140, 30);
        btnAccept.TabIndex = 1;
        btnAccept.Text = "Chấp nhận";
        btnAccept.UseVisualStyleBackColor = true;
        // 
        // btnReject
        // 
        btnReject.Anchor = AnchorStyles.Bottom | AnchorStyles.Right;
        btnReject.Location = new Point(158, 66);
        btnReject.Name = "btnReject";
        btnReject.Size = new Size(140, 30);
        btnReject.TabIndex = 2;
        btnReject.Text = "Từ chối";
        btnReject.UseVisualStyleBackColor = true;
        // 
        // rtbLog
        // 
        rtbLog.Dock = DockStyle.Fill;
        rtbLog.Location = new Point(3, 444);
        rtbLog.Name = "rtbLog";
        rtbLog.ReadOnly = true;
        rtbLog.Size = new Size(310, 214);
        rtbLog.TabIndex = 4;
        rtbLog.Text = "";
        // 
        // Form1
        // 
        AutoScaleDimensions = new SizeF(8F, 20F);
        AutoScaleMode = AutoScaleMode.Font;
        BackColor = SystemColors.ControlLight;
        BackgroundImage = Properties.Resources.abfa03f6_6d65_453f_9081_0ae2d9165caa;
        BackgroundImageLayout = ImageLayout.Stretch;
        ClientSize = new Size(1060, 700);
        Controls.Add(tlpRoot);
        Controls.Add(menuStrip1);
        ForeColor = SystemColors.ActiveCaptionText;
        MainMenuStrip = menuStrip1;
        Name = "Form1";
        Text = "Form1";
        FormClosing += Form1_FormClosing;
        Load += Form1_Load;
        menuStrip1.ResumeLayout(false);
        menuStrip1.PerformLayout();
        tlpRoot.ResumeLayout(false);
        flpActions.ResumeLayout(false);
        tlpCenter.ResumeLayout(false);
        ((System.ComponentModel.ISupportInitialize)ptbTitle).EndInit();
        tlpScore.ResumeLayout(false);
        tlpScore.PerformLayout();
        ((System.ComponentModel.ISupportInitialize)pctbMark).EndInit();
        tlpOnline.ResumeLayout(false);
        gbInviteMessage.ResumeLayout(false);
        ResumeLayout(false);
        PerformLayout();
    }

    #endregion

    private MenuStrip menuStrip1;
    private ToolStripMenuItem menuToolStripMenuItem;
    private ToolStripMenuItem newGameToolStripMenuItem;
    private ToolStripMenuItem quitToolStripMenuItem;
    private ToolStripMenuItem thôngTinToolStripMenuItem;
    private ToolStripMenuItem tàiKhoảnCủaTôiToolStripMenuItem;
    private ToolStripMenuItem hồSơCủaTôiToolStripMenuItem;
    private ToolStripMenuItem tínhNăngToolStripMenuItem;
    private ToolStripMenuItem bạnBèToolStripMenuItem;
    private ToolStripMenuItem nhắnTinToolStripMenuItem;
    private ToolStripMenuItem lịchSửToolStripMenuItem;

    private TableLayoutPanel tlpRoot;

    private FlowLayoutPanel flpActions;
    private Button btnInvitePlayer;
    private Button btnSpectateMatch;
    private Button btnLeaveRoom;

    private TableLayoutPanel tlpCenter;
    private PictureBox ptbTitle;
    private TableLayoutPanel tlpScore;
    private TextBox txbPlayerName1;
    private TextBox txtScorePlayer1;
    private PictureBox pctbMark;
    private TextBox txtScorePlayer2;
    private TextBox txtPlayerName2;
    private Panel pnlChessBoard;
    private Label lblTurnClock;

    private TableLayoutPanel tlpOnline;
    private Label lblOnline;
    private ListBox lstOnlinePlayers;
    private Button btnRefreshPlayers;
    private GroupBox gbInviteMessage;
    private Label lblInviteMessage;
    private Button btnAccept;
    private Button btnReject;
    private RichTextBox rtbLog;
}
