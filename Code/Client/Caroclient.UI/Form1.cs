using System;
using System.Drawing;
using System.Threading.Tasks;
using System.Windows.Forms;
using CaroClient.Core;

namespace Caroclient.UI
{
    public partial class Form1 : Form
    {
        #region Properties
        ChessBoardManager ChessBoard;
        public string Username { get; }
        public string Password { get; }
        public string ServerAddress { get; }

        private readonly CaroConnection connection = new();
        private readonly GameClient client;

        private string? myPlayerId;
        private string? roomId;
        private string? pendingInviteId;
        private string? pendingInviteFrom;
        private bool isSpectator;
        private bool dangXinXemTran;   // đã gửi spectate, chờ server xác nhận
        private bool dangChoXacNhanNuocDi;
        private int PlayerOneWins;
        private int PlayerTwoWins;
        #endregion

        public Form1() : this("Player_01", "", "tcp://localhost:8765")
        {
        }

        public Form1(string username, string password, string serverAddress)
        {
            InitializeComponent();

            Username = username;
            Password = password;
            ServerAddress = serverAddress;
            Text = $"Caro - {Username}";

            ChessBoard = new ChessBoardManager(pnlChessBoard, txbPlayerName1, pctbMark)
            {
                OnlineMode = true
            };
            ChessBoard.GameEnded += ChessBoard_GameEnded;
            ChessBoard.CellClicked += ChessBoard_CellClicked;

            BuildOnlineUi();
            ConfigurePlayerInfo();
            ChessBoard.DrawChessBoard();
            ChessBoard.SetInteractive(false);

            client = new GameClient(connection);
            RegisterClientEvents();
        }

        #region Online UI

        /// <summary>
        /// Khởi tạo các control phần chơi mạng. Chúng đã được khai báo trong
        /// Form1.Designer.cs nhưng chưa được dựng, nên dựng ở đây để không phải
        /// sửa file designer.
        /// </summary>
        private void BuildOnlineUi()
        {
            ClientSize = new Size(1190, 600);

            var lblOnline = new Label
            {
                AutoSize = true,
                Location = new Point(OnlinePanelX, 112),
                Text = "Người chơi online"
            };

            lstOnlinePlayers = new ListBox
            {
                Location = new Point(OnlinePanelX, 135),
                Size = new Size(320, 150)
            };
            lstOnlinePlayers.DoubleClick += (_, _) => InviteSelectedPlayer();

            btnRefreshPlayers = new Button
            {
                Location = new Point(OnlinePanelX, 292),
                Size = new Size(100, 29),
                Text = "Làm mới"
            };
            btnRefreshPlayers.Click += async (_, _) => await SafeSendAsync(client.GetOnlinePlayersAsync());

            var btnInvitePlayer = new Button
            {
                Location = new Point(OnlinePanelX + 108, 292),
                Size = new Size(100, 29),
                Text = "Mời đấu"
            };
            btnInvitePlayer.Click += (_, _) => InviteSelectedPlayer();

            btnSpectate2 = new Button
            {
                Location = new Point(OnlinePanelX + 216, 292),
                Size = new Size(104, 29),
                Text = "Xem trận"
            };
            btnSpectate2.Click += (_, _) => SpectateSelectedPlayer();

            gbInviteMessage = new GroupBox
            {
                Location = new Point(OnlinePanelX, 331),
                Size = new Size(320, 100),
                Text = "Lời mời",
                Visible = false
            };

            lblInviteMessage = new Label
            {
                AutoSize = false,
                Location = new Point(12, 25),
                Size = new Size(296, 30),
                Text = ""
            };

            btnAccept = new Button
            {
                Location = new Point(12, 60),
                Size = new Size(140, 29),
                Text = "Chấp nhận"
            };
            btnAccept.Click += async (_, _) => await RespondToInviteAsync(accept: true);

            btnReject = new Button
            {
                Location = new Point(168, 60),
                Size = new Size(140, 29),
                Text = "Từ chối"
            };
            btnReject.Click += async (_, _) => await RespondToInviteAsync(accept: false);

            gbInviteMessage.Controls.AddRange(new Control[] { lblInviteMessage, btnAccept, btnReject });

            btnSurrender = new Button
            {
                Location = new Point(OnlinePanelX, 441),
                Size = new Size(320, 29),
                Text = "Rời phòng / Đầu hàng",
                Enabled = false
            };
            btnSurrender.Click += async (_, _) => await LeaveRoomAsync();

            rtbLog = new RichTextBox
            {
                Location = new Point(OnlinePanelX, 480),
                Size = new Size(320, 100),
                ReadOnly = true
            };

            Controls.AddRange(new Control[]
            {
                lblOnline, lstOnlinePlayers, btnRefreshPlayers, btnInvitePlayer,
                btnSpectate2, gbInviteMessage, btnSurrender, rtbLog
            });

            // Nút này trong designer đang là "Chơi với máy"; ở chế độ online nó
            // dùng để rời phòng nên đổi nhãn cho khớp.
            btnLeave.Text = "Rời phòng";
            btnLeave.Click += async (_, _) => await LeaveRoomAsync();
        }

        private const int OnlinePanelX = 840;
        private Button btnRefreshPlayers = null!;
        private Button btnSpectate2 = null!;

        #endregion

        #region Client events

        private void RegisterClientEvents()
        {
            client.OnLoginSucceeded += auth => RunOnUi(() =>
            {
                myPlayerId = auth.PlayerId;
                Text = $"Caro - {auth.Username} (ID: {auth.PlayerId})";
                Log($"Đăng nhập thành công: {auth.Username} (ID: {auth.PlayerId})");
                _ = SafeSendAsync(client.GetOnlinePlayersAsync());
            });

            client.OnOnlinePlayersReceived += message => RunOnUi(() =>
            {
                string? selected = lstOnlinePlayers.SelectedItem is PlayerEntry current ? current.PlayerId : null;

                lstOnlinePlayers.BeginUpdate();
                lstOnlinePlayers.Items.Clear();
                foreach (PlayerInfo player in message.Players)
                {
                    if (player.PlayerId == myPlayerId)
                    {
                        continue;
                    }

                    lstOnlinePlayers.Items.Add(new PlayerEntry(player));
                }
                lstOnlinePlayers.EndUpdate();

                if (selected is not null)
                {
                    for (int i = 0; i < lstOnlinePlayers.Items.Count; i++)
                    {
                        if (lstOnlinePlayers.Items[i] is PlayerEntry entry && entry.PlayerId == selected)
                        {
                            lstOnlinePlayers.SelectedIndex = i;
                            break;
                        }
                    }
                }
            });

            client.OnInviteReceived += invite => RunOnUi(() =>
            {
                pendingInviteId = invite.InviteId;
                pendingInviteFrom = invite.FromUsername;
                lblInviteMessage.Text = $"{invite.FromUsername} (ID: {invite.FromPlayerId}) mời bạn thi đấu.";
                gbInviteMessage.Visible = true;
                Log($"Nhận lời mời từ {invite.FromUsername}.");
            });

            client.OnInviteResult += result => RunOnUi(() =>
                Log($"Đã gửi lời mời tới người chơi {result.ToPlayerId}, đang chờ trả lời."));

            client.OnInviteRejected += rejected => RunOnUi(() =>
                Log($"Lời mời bị từ chối (người chơi {rejected.ByPlayerId})."));

            client.OnGameStateReceived += state => RunOnUi(() => ApplyGameState(state));

            client.OnGameResultReceived += result => RunOnUi(() => ApplyGameResult(result));

            client.OnLeaveRoomResult += result => RunOnUi(() =>
            {
                roomId = null;
                isSpectator = false;
                btnSurrender.Enabled = false;
                ChessBoard.SetInteractive(false);
                Log($"Đã rời phòng (vai trò {result.Role}).");
            });

            client.OnErrorReceived += error => RunOnUi(() =>
            {
                Log($"[{error.Code}] {error.Message}");

                // Các lỗi chặn đăng nhập thì cần báo rõ ràng cho người dùng.
                if (error.Code is "USER_NOT_EXIST" or "WRONG_PASSWORD" or "ALREADY_ONLINE" or "DATABASE_ERROR")
                {
                    MessageBox.Show(error.Message, "Không đăng nhập được", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }

                // Bất kỳ lỗi nào cũng huỷ yêu cầu đang chờ, khỏi phải liệt kê mã lỗi.
                dangXinXemTran = false;

                if (dangChoXacNhanNuocDi)
                {
                    dangChoXacNhanNuocDi = false;
                    ChessBoard.SetInteractive(true);
                }
            });

            connection.Disconnected += reason => RunOnUi(() =>
            {
                Log($"Mất kết nối: {reason}");
                ChessBoard.SetInteractive(false);
                btnSurrender.Enabled = false;
            });

            connection.Reconnected += () => RunOnUi(() => Log("Đã kết nối lại. Hãy đăng nhập lại."));
        }

        private void ApplyGameState(GameStateMessage state)
        {
            if (dangXinXemTran)
            {
                isSpectator = true;
                dangXinXemTran = false;
            }

            dangChoXacNhanNuocDi = false;
            roomId = state.RoomId;
            ChessBoard.RenderBoard(state.Board);

            bool myTurn = !isSpectator
                && state.CurrentPlayerId == myPlayerId
                && state.Status == "playing";

            ChessBoard.SetInteractive(myTurn);
            btnSurrender.Enabled = !isSpectator && state.Status == "playing";
            gbInviteMessage.Visible = false;

            txtPlayerName2.Text = isSpectator ? "Đang xem" : "O - Đối thủ";
            Log(myTurn
                ? $"Phòng {state.RoomId}: đến lượt bạn."
                : $"Phòng {state.RoomId}: chờ đối thủ ({state.CurrentPlayerId}).");
        }

        private void ApplyGameResult(GameResultMessage result)
        {
            ChessBoard.SetInteractive(false);
            btnSurrender.Enabled = false;
            roomId = null;

            string text = result.Result switch
            {
                "win" => "Bạn thắng!",
                "lose" => "Bạn thua!",
                "draw" => "Ván đấu hòa!",
                _ => $"Kết thúc: {result.Result}"
            };

            if (result.Result == "win")
            {
                PlayerOneWins++;
                txtScorePlayer1.Text = PlayerOneWins.ToString();
            }
            else if (result.Result == "lose")
            {
                PlayerTwoWins++;
                txtScorePlayer2.Text = PlayerTwoWins.ToString();
            }

            Log($"Kết quả phòng {result.RoomId}: {text}");
            MessageBox.Show(text, "Kết thúc ván", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        #endregion

        #region Actions

        private async void ChessBoard_CellClicked(int row, int col)
        {
            if (string.IsNullOrWhiteSpace(roomId) || string.IsNullOrWhiteSpace(myPlayerId))
            {
                Log("Chưa vào phòng nào.");
                return;
            }

            if (isSpectator)
            {
                Log("Bạn đang ở chế độ xem, không thể đánh.");
                return;
            }

            // Khoá bàn cờ cho tới khi server xác nhận bằng game_state mới.
            ChessBoard.SetInteractive(false);
            dangChoXacNhanNuocDi = true;
            await SafeSendAsync(client.MakeMoveAsync(roomId, myPlayerId, row, col));
        }

        private async void InviteSelectedPlayer()
        {
            if (lstOnlinePlayers.SelectedItem is not PlayerEntry entry)
            {
                MessageBox.Show("Hãy chọn một người chơi trong danh sách.", "Caro", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            await SafeSendAsync(client.SendInviteAsync(entry.PlayerId, Guid.NewGuid().ToString("N")));
        }

        private async void SpectateSelectedPlayer()
        {
            if (lstOnlinePlayers.SelectedItem is not PlayerEntry entry)
            {
                MessageBox.Show("Hãy chọn một người chơi đang thi đấu.", "Caro", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            string? room = PromptRoomId();
            if (string.IsNullOrWhiteSpace(room))
            {
                return;
            }

            dangXinXemTran = true;
            await SafeSendAsync(client.SpectateAsync(room));
        }

        private static string? PromptRoomId()
        {
            using var dialog = new Form
            {
                Text = "Xem trận",
                FormBorderStyle = FormBorderStyle.FixedDialog,
                StartPosition = FormStartPosition.CenterParent,
                ClientSize = new Size(320, 120),
                MinimizeBox = false,
                MaximizeBox = false
            };

            var label = new Label { AutoSize = true, Location = new Point(12, 15), Text = "Nhập room_id muốn xem:" };
            var input = new TextBox { Location = new Point(12, 45), Size = new Size(296, 27) };
            var ok = new Button { DialogResult = DialogResult.OK, Location = new Point(132, 82), Size = new Size(85, 29), Text = "Xem" };
            var cancel = new Button { DialogResult = DialogResult.Cancel, Location = new Point(223, 82), Size = new Size(85, 29), Text = "Huỷ" };

            dialog.Controls.AddRange(new Control[] { label, input, ok, cancel });
            dialog.AcceptButton = ok;
            dialog.CancelButton = cancel;

            return dialog.ShowDialog() == DialogResult.OK ? input.Text.Trim() : null;
        }

        private async Task RespondToInviteAsync(bool accept)
        {
            if (string.IsNullOrWhiteSpace(pendingInviteId))
            {
                return;
            }

            string inviteId = pendingInviteId;
            pendingInviteId = null;
            gbInviteMessage.Visible = false;

            if (accept)
            {
                isSpectator = false;
                dangXinXemTran = false;
                await SafeSendAsync(client.AcceptInviteAsync(inviteId));
            }
            else
            {
                await SafeSendAsync(client.RejectInviteAsync(inviteId));
                Log($"Đã từ chối lời mời của {pendingInviteFrom}.");
            }
        }

        private async Task LeaveRoomAsync()
        {
            if (string.IsNullOrWhiteSpace(roomId))
            {
                Log("Bạn không ở trong phòng nào.");
                return;
            }

            await SafeSendAsync(client.LeaveRoomAsync(roomId));
        }

        private async Task SafeSendAsync(Task sendTask)
        {
            try
            {
                await sendTask;
            }
            catch (Exception ex)
            {
                Log($"Gửi thất bại: {ex.Message}");
            }
        }

        #endregion

        #region Helpers

        private void RunOnUi(Action action)
        {
            if (IsDisposed || Disposing)
            {
                return;
            }

            if (InvokeRequired)
            {
                try
                {
                    BeginInvoke(action);
                }
                catch (ObjectDisposedException)
                {
                    // Form đã đóng trong lúc message đang tới.
                }
            }
            else
            {
                action();
            }
        }

        private void Log(string message)
        {
            rtbLog.AppendText($"[{DateTime.Now:HH:mm:ss}] {message}{Environment.NewLine}");
            rtbLog.ScrollToCaret();
        }

        private sealed class PlayerEntry
        {
            public PlayerEntry(PlayerInfo info)
            {
                PlayerId = info.PlayerId;
                Username = info.Username;
                Status = info.Status;
            }

            public string PlayerId { get; }
            public string Username { get; }
            public string Status { get; }

            public override string ToString() => $"{Username} (ID: {PlayerId}) - {Status}";
        }

        #endregion

        private void ConfigurePlayerInfo()
        {
            // X là người chơi thứ nhất, O là người chơi thứ hai.
            txbPlayerName1.Text = $"X - {Username}";
            txtPlayerName2.Text = "O - Chưa có đối thủ";
            txtScorePlayer1.Text = "0";
            txtScorePlayer2.Text = "0";
        }

        private void ChessBoard_GameEnded(int winnerIndex)
        {
            // Ở chế độ online kết quả do server quyết định (game_result),
            // nên nhánh này chỉ dùng cho chế độ chơi cục bộ.
            if (ChessBoard.OnlineMode)
            {
                return;
            }

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

        void NewGame()
        {
            ChessBoard.DrawChessBoard();
            ChessBoard.SetInteractive(false);
        }

        void Quit()
        {
            Application.Exit();
        }

        private void ChessNode_Click(object sender, EventArgs e)
        {

        }

        private void pnlChessBoard_Paint(object sender, PaintEventArgs e)
        {

        }

        private async void Form1_Load(object sender, EventArgs e)
        {
            await ConnectAndLoginAsync();
        }

        private async Task ConnectAndLoginAsync()
        {
            try
            {
                Log($"Đang kết nối tới {ServerAddress}...");
                await client.ConnectAsync(ServerAddress);
                Log("Đã kết nối TCP.");
            }
            catch (Exception ex)
            {
                Log($"Không kết nối được: {ex.Message}");
                MessageBox.Show($"Không kết nối được tới server:\n{ex.Message}", "Lỗi kết nối", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            if (string.IsNullOrEmpty(Password))
            {
                Log("Chưa có mật khẩu, bỏ qua bước đăng nhập.");
                return;
            }

            await SafeSendAsync(client.LoginAsync(Username, Password));
        }

        private void button2_Click(object sender, EventArgs e)
        {
            InviteSelectedPlayer();
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
            if (MessageBox.Show("Bạn có chắc muốn thoát?", "Thông báo", MessageBoxButtons.OKCancel) != DialogResult.OK)
            {
                e.Cancel = true;
                return;
            }

            try
            {
                // Chờ có giới hạn: async void ở đây sẽ để form đóng trước khi
                // kết nối kịp đóng sạch.
                connection.DisconnectAsync().Wait(TimeSpan.FromSeconds(2));
            }
            catch (Exception)
            {
                // Đang đóng form, lỗi ngắt kết nối không cần báo.
            }
        }

        private void thôngTinToolStripMenuItem_Click(object sender, EventArgs e)
        {

        }

        private void tàiKhoảnCủaTôiToolStripMenuItem_Click(object? sender, EventArgs e)
        {
            using var accountForm = new AccountForm(Username, myPlayerId ?? "-");
            accountForm.ShowDialog(this);
        }

        private void hồSơCủaTôiToolStripMenuItem_Click(object? sender, EventArgs e)
        {
            using var profileForm = new ProfileForm(Username, myPlayerId ?? "-");
            profileForm.ShowDialog(this);
        }

        private void pictureBox1_Click_1(object sender, EventArgs e)
        {

        }
    }
}
