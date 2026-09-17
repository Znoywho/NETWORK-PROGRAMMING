using System;
using System.Drawing;
using System.Windows.Forms;

namespace Caroclient.UI
{
    public partial class Form1 : Form
    {
        #region Properties
        ChessBoardManager ChessBoard;
        public string Username { get; }
        public string ServerAddress { get; }
        private int PlayerOneWins;
        private int PlayerTwoWins;
        #endregion
        public Form1() : this("Player_01", "tcp://localhost:8765")
        {
        }

        public Form1(string username, string serverAddress)
        {
            InitializeComponent();

            Username = username;
            ServerAddress = serverAddress;
            Text = $"Caro - {Username}";

            ChessBoard = new ChessBoardManager(pnlChessBoard, txbPlayerName1, pctbMark);
            ChessBoard.GameEnded += ChessBoard_GameEnded;
            ConfigurePlayerInfo();

            ChessBoard.DrawChessBoard();
        }

        private void ConfigurePlayerInfo()
        {
            // X là người chơi thứ nhất, O là người chơi thứ hai.
            txbPlayerName1.Text = $"X - {Username}";
            txtPlayerName2.Text = "O - Người chơi 2";
            txtScorePlayer1.Text = "0";
            txtScorePlayer2.Text = "0";
        }

        private void ChessBoard_GameEnded(int winnerIndex)
        {
            if (winnerIndex == 0)
            {
                PlayerOneWins++;
                txtScorePlayer1.Text = PlayerOneWins.ToString();
                MessageBox.Show($"X chiến thắng!\nTỉ số: X {PlayerOneWins} - {PlayerTwoWins} O", "Kết thúc game", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            else
            {
                PlayerTwoWins++;
                txtScorePlayer2.Text = PlayerTwoWins.ToString();
                MessageBox.Show($"O chiến thắng!\nTỉ số: X {PlayerOneWins} - {PlayerTwoWins} O", "Kết thúc game", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
        }
        void DrawChessBoard()
        {
            Button oldButton = new Button() { Width = 0, Location = new Point(0, 0) }; //Canh chuẩn kích thước trái phải
            for (int i = 0; i < Cons.CHESS_BOARD_HEIGHT; i++)
            {
                for (int j = 0; j < Cons.CHESS_BOARD_WIDTH; j++)
                {
                    Button btn = new Button()
                    {
                        Width = Cons.CHESS_WIDTH,
                        Height = Cons.CHESS_HEIGHT,
                        Location = new Point(oldButton.Location.X + oldButton.Width, oldButton.Location.Y),
                        BackgroundImageLayout = ImageLayout.Stretch
                    };

                    btn.Click += btn_Click;

                    pnlChessBoard.Controls.Add(btn);

                    oldButton = btn;
                }
                oldButton.Location = new Point(0, oldButton.Location.Y + Cons.CHESS_HEIGHT);
                oldButton.Width = 0;
                oldButton.Height = 0;
            }

        }

        void NewGame()
        {
            ChessBoard.DrawChessBoard();
        }

        void Quit()
        {
            Application.Exit();
        }

        private void btn_Click(object? sender, EventArgs e)
        {
            if (sender is not Button btn)
            {
                return;
            }

            btn.BackgroundImage = Image.FromFile(Application.StartupPath + "\\Resources\\image_x.png");
        }

        private void ChessNode_Click(object sender, EventArgs e)
        {

        }

        private void pnlChessBoard_Paint(object sender, PaintEventArgs e)
        {

        }

        private void Form1_Load(object sender, EventArgs e)
        {

        }

        private void button2_Click(object sender, EventArgs e)
        {
            using var inviteForm = new InviteForm();
            inviteForm.ShowDialog(this);
        }

        private void groupBox1_Enter(object sender, EventArgs e)
        {

        }

        private void label1_Click(object sender, EventArgs e)
        {

        }

        private void txtChatInput_TextChanged(object sender, EventArgs e)
        {

        }
        private void button1_Click(object sender, EventArgs e)
        {
            using var chatForm = new ChatForm();
            chatForm.ShowDialog(this);
        }

        private void btnInvite_Click(object? sender, EventArgs e)
        {
            using var friendsForm = new FriendsForm();
            friendsForm.ShowDialog(this);
        }

        private void btnSpectate_Click(object? sender, EventArgs e)
        {
            using var historyForm = new MatchHistoryForm();
            historyForm.ShowDialog(this);
        }

        private void txtUsername_TextChanged(object sender, EventArgs e)
        {

        }

        private void pictureBox1_Click(object sender, EventArgs e)
        {

        }

        private void newGameToolStripMenuItem_Click(object sender, EventArgs e)
        {
            NewGame();
        }

        private void quitToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Quit();
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (MessageBox.Show("Bạn có chắc muốn thoát?", "Thông báo", MessageBoxButtons.OKCancel) != System.Windows.Forms.DialogResult.OK)
                e.Cancel = true;
        }

        private void thôngTinToolStripMenuItem_Click(object sender, EventArgs e)
        {

        }

        private void tàiKhoảnCủaTôiToolStripMenuItem_Click(object? sender, EventArgs e)
        {
            using var accountForm = new AccountForm(Username, "player-001");
            accountForm.ShowDialog(this);
        }

        private void hồSơCủaTôiToolStripMenuItem_Click(object? sender, EventArgs e)
        {
            using var profileForm = new ProfileForm(Username, "player-001");
            profileForm.ShowDialog(this);
        }

        private void pictureBox1_Click_1(object sender, EventArgs e)
        {

        }
    }
}
