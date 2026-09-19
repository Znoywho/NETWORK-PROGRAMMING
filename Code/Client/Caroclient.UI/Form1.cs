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
        private bool dangChonTranDeXem; // đã xin match_list để mở bảng chọn phòng
        private bool dangChoXacNhanNuocDi;

        /// <summary>Quân mà mình đang chơi: 0 = X, 1 = O. -1 = chưa vào trận.</summary>
        private int mySymbol = -1;

        // Đồng hồ hiển thị: server gửi số giây còn lại trong game_state, client
        // chỉ đếm ngược tại chỗ nên không cần server bắn message mỗi giây.
        private readonly System.Windows.Forms.Timer turnClockTimer = new() { Interval = 1000 };
        private int turnSecondsLeft;
        private int reconnectSecondsLeft;
        private string? waitingForPlayerId;
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

            WireUpControls();
            ConfigurePlayerInfo();
            ChessBoard.DrawChessBoard();
            ChessBoard.SetInteractive(false);

            turnClockTimer.Tick += TurnClockTick;

            client = new GameClient(connection);
            RegisterClientEvents();
        }

        #region Online UI

        /// <summary>
        /// Toan bo layout nam trong Form1.Designer.cs. O day chi noi su kien
        /// cho cac control do designer tao ra.
        /// </summary>
        private void WireUpControls()
        {
            btnInvitePlayer.Click += (_, _) => InviteSelectedPlayer();
            lstOnlinePlayers.DoubleClick += (_, _) => InviteSelectedPlayer();

            btnSpectateMatch.Click += (_, _) => ChooseMatchToSpectate();

            btnLeaveRoom.Click += async (_, _) => await LeaveRoomAsync();

            btnRefreshPlayers.Click += async (_, _) => await SafeSendAsync(client.GetOnlinePlayersAsync());

            btnAccept.Click += async (_, _) => await RespondToInviteAsync(accept: true);
            btnReject.Click += async (_, _) => await RespondToInviteAsync(accept: false);
        }

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

            client.OnMatchListReceived += list => RunOnUi(() =>
            {
                if (!dangChonTranDeXem)
                {
                    return;
                }

                dangChonTranDeXem = false;
                ShowMatchPicker(list);
            });

            client.OnPlayerDisconnected += notice => RunOnUi(() =>
            {
                waitingForPlayerId = notice.PlayerId;
                reconnectSecondsLeft = notice.ReconnectTimeLeft;
                ChessBoard.SetInteractive(false);
                UpdateClockLabel();
                Log($"Người chơi {notice.PlayerId} mất kết nối. Ván tạm dừng, "
                    + $"chờ tối đa {notice.ReconnectTimeLeft} giây.");
            });

            client.OnPlayerReconnected += notice => RunOnUi(() =>
            {
                waitingForPlayerId = null;
                reconnectSecondsLeft = 0;
                Log($"Người chơi {notice.PlayerId} đã kết nối lại. Ván tiếp tục.");
            });

            client.OnGameStateReceived += state => RunOnUi(() => ApplyGameState(state));

            client.OnGameResultReceived += result => RunOnUi(() => ApplyGameResult(result));

            client.OnLeaveRoomResult += result => RunOnUi(() =>
            {
                roomId = null;
                isSpectator = false;
                btnLeaveRoom.Enabled = false;
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

            connection.Disconnected += reason =>
            {
                RunOnUi(() =>
                {
                    Log($"Mất kết nối: {reason}. Đang thử kết nối lại...");
                    ChessBoard.SetInteractive(false);
                    btnLeaveRoom.Enabled = false;
                });

                _ = TryReconnectAsync();
            };

            connection.Reconnected += () => RunOnUi(() => Log("Đã kết nối lại TCP."));
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
            btnLeaveRoom.Enabled = !isSpectator && state.Status == "playing";
            gbInviteMessage.Visible = false;

            // --- Cập nhật icon X/O và tên dựa theo quân được server giao ---
            if (!isSpectator && !string.IsNullOrEmpty(myPlayerId))
            {
                bool iAmX = state.PlayerXId == myPlayerId;
                mySymbol = iAmX ? 0 : 1;

                // Đổi icon giữa bảng tỉ số sang đúng quân của mình
                ChessBoard.ShowMark(mySymbol);

                txbPlayerName1.Text = iAmX
                    ? $"X - {Username}"
                    : $"O - {Username}";
                txtPlayerName2.Text = iAmX
                    ? "O - Đối thủ"
                    : "X - Đối thủ";
            }
            else
            {
                txtPlayerName2.Text = isSpectator ? "Đang xem" : "O - Đối thủ";
            }

            // Khán giả vào giữa trận cũng nhận đúng đồng hồ này trong game_state.
            waitingForPlayerId = state.WaitingForPlayerId;
            reconnectSecondsLeft = state.ReconnectTimeLeft ?? 0;
            turnSecondsLeft = state.TurnTimeLeft;
            if (state.Status == "playing")
            {
                lblTurnClock.Visible = true;
                UpdateClockLabel();
                turnClockTimer.Start();
            }
            else
            {
                StopTurnClock();
            }

            Log(myTurn
                ? $"Phòng {state.RoomId}: đến lượt bạn."
                : $"Phòng {state.RoomId}: chờ đối thủ ({state.CurrentPlayerId}).");
        }

        private void TurnClockTick(object? sender, EventArgs e)
        {
            if (waitingForPlayerId is not null)
            {
                if (reconnectSecondsLeft > 0)
                {
                    reconnectSecondsLeft--;
                }
            }
            else if (turnSecondsLeft > 0)
            {
                turnSecondsLeft--;
            }

            UpdateClockLabel();
        }

        private void UpdateClockLabel()
        {
            lblTurnClock.Visible = true;
            if (waitingForPlayerId is not null)
            {
                lblTurnClock.ForeColor = Color.DarkOrange;
                lblTurnClock.Text = $"Chờ {waitingForPlayerId} kết nối lại: {reconnectSecondsLeft}s";
                return;
            }

            lblTurnClock.ForeColor = turnSecondsLeft <= 5 ? Color.Firebrick : Color.Black;
            lblTurnClock.Text = $"Thời gian suy nghĩ: {turnSecondsLeft}s";
        }

        private void StopTurnClock()
        {
            turnClockTimer.Stop();
            lblTurnClock.Visible = false;
            waitingForPlayerId = null;
        }

        private void ApplyGameResult(GameResultMessage result)
        {
            ChessBoard.SetInteractive(false);
            btnLeaveRoom.Enabled = false;
            roomId = null;
            StopTurnClock();

            string text = result.Result switch
            {
                "win" => "Bạn thắng!",
                "lose" => "Bạn thua!",
                "draw" => "Ván đấu hòa!",
                _ => $"Kết thúc: {result.Result}"
            };

            text += result.Reason switch
            {
                "timeout" => "\n(Hết thời gian suy nghĩ của một lượt.)",
                "disconnect" => "\n(Một bên mất kết nối quá thời gian cho phép.)",
                "forfeit" => "\n(Một bên rời phòng giữa trận.)",
                _ => ""
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

        /// <summary>
        /// Xin danh sách trận đang diễn ra. Bảng chọn phòng được mở khi
        /// match_list về, ở handler OnMatchListReceived.
        /// </summary>
        private async void ChooseMatchToSpectate()
        {
            dangChonTranDeXem = true;
            await SafeSendAsync(client.GetMatchListAsync());
        }

        private async void ShowMatchPicker(MatchListMessage list)
        {
            if (list.Matches.Count == 0)
            {
                MessageBox.Show("Hiện không có trận nào đang diễn ra.", "Xem trận", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            string? room = PromptMatchChoice(list);
            if (string.IsNullOrWhiteSpace(room))
            {
                return;
            }

            dangXinXemTran = true;
            await SafeSendAsync(client.SpectateAsync(room));
        }

        private static string? PromptMatchChoice(MatchListMessage list)
        {
            using var dialog = new Form
            {
                Text = "Chọn trận để xem",
                FormBorderStyle = FormBorderStyle.FixedDialog,
                StartPosition = FormStartPosition.CenterParent,
                ClientSize = new Size(460, 260),
                MinimizeBox = false,
                MaximizeBox = false
            };

            var label = new Label { AutoSize = true, Location = new Point(12, 12), Text = "Các trận đang diễn ra:" };
            var listBox = new ListBox { Location = new Point(12, 40), Size = new Size(436, 164) };
            foreach (MatchSummary match in list.Matches)
            {
                listBox.Items.Add(new MatchEntry(match));
            }
            listBox.SelectedIndex = 0;

            var ok = new Button { DialogResult = DialogResult.OK, Location = new Point(272, 218), Size = new Size(85, 29), Text = "Xem" };
            var cancel = new Button { DialogResult = DialogResult.Cancel, Location = new Point(363, 218), Size = new Size(85, 29), Text = "Huỷ" };
            listBox.DoubleClick += (_, _) => { dialog.DialogResult = DialogResult.OK; };

            dialog.Controls.AddRange(new Control[] { label, listBox, ok, cancel });
            dialog.AcceptButton = ok;
            dialog.CancelButton = cancel;

            return dialog.ShowDialog() == DialogResult.OK && listBox.SelectedItem is MatchEntry entry
                ? entry.RoomId
                : null;
        }

        /// <summary>
        /// Nối lại TCP rồi đăng nhập lại ngay. Nếu còn trong thời gian cho phép,
        /// server trả về luôn game_state của ván đang dở.
        /// </summary>
        private async Task TryReconnectAsync()
        {
            bool reconnected;
            try
            {
                reconnected = await connection.ReconnectAsync(3, TimeSpan.FromSeconds(2));
            }
            catch (Exception ex)
            {
                RunOnUi(() => Log($"Kết nối lại thất bại: {ex.Message}"));
                return;
            }

            if (!reconnected)
            {
                RunOnUi(() =>
                {
                    Log("Không kết nối lại được. Ván đang dở sẽ bị xử thua khi hết thời gian chờ.");
                    StopTurnClock();
                });
                return;
            }

            if (string.IsNullOrEmpty(Password))
            {
                RunOnUi(() => Log("Chưa có mật khẩu đã lưu, hãy đăng nhập lại thủ công."));
                return;
            }

            RunOnUi(() => Log($"Đang đăng nhập lại bằng tài khoản {Username}..."));
            await SafeSendAsync(client.LoginAsync(Username, Password));
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

        private sealed class MatchEntry
        {
            public MatchEntry(MatchSummary match)
            {
                RoomId = match.RoomId;
                Text = $"Phòng {match.RoomId}: {match.PlayerXName} (X) vs {match.PlayerOName} (O)"
                    + $" - {match.MoveCount} nước, {match.SpectatorCount} khán giả, còn {match.TurnTimeLeft}s";
            }

            public string RoomId { get; }
            public string Text { get; }

            public override string ToString() => Text;
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



        private async void Form1_Load(object sender, EventArgs e)
        {
            // Chot kich thuoc khoi dong lam min: keo nho hon nua thi bang co
            // (neo ca trai lan phai) bi co ve 0 va bien mat. Lay Size o Load
            // de da tinh ca DPI scaling, khoi phai hardcode con so.
            MinimumSize = Size;

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

    }
}
