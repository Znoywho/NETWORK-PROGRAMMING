using System;
using System.Collections.Generic;
using System.Diagnostics.Eventing.Reader;
using System.Text;

namespace Caroclient.UI
{
    public class ChessBoardManager
    {
        #region Properties  
        private Panel chessBoard;

        public Panel ChessBoard { get => chessBoard; set => chessBoard = value; }

        private List<Player> player; //Danh sách người chơi
        public List<Player> Player { get => player; set => player = value; }

        private int CurrentPlayer;

        public int CurrentPlayer1 { get => CurrentPlayer; set => CurrentPlayer = value; }

        private TextBox playerName;
        public TextBox PlayerName { get => playerName; set => playerName = value; }

        private PictureBox playerMark;
        public PictureBox PlayerMark { get => playerMark; set => playerMark = value; }

        private List<List<Button>> Matrix;
        public List<List<Button>> Matrix1 { get => Matrix; set => Matrix = value; }

        public event Action<int>? GameEnded;

        #endregion

        #region Initialize
        public ChessBoardManager(Panel chessBoard, TextBox playerName, PictureBox mark)
        {
            this.ChessBoard = chessBoard;
            this.PlayerName = playerName;
            this.PlayerMark = mark;

            this.Player = new List<Player>()
            {
                new Player("NgocHan", Image.FromFile(Application.StartupPath + "\\Resources\\image_x.png")),
                new Player("Bot", Image.FromFile(Application.StartupPath + "\\Resources\\image_o.png"))
            };

            CurrentPlayer1 = 0;
            
            ChangePlayer();
                
        }
        #endregion

        #region Methods
        public void DrawChessBoard()
        {
            ChessBoard.Enabled = true;
            ChessBoard.Controls.Clear();
            CurrentPlayer = 0;

            Matrix = new List<List<Button>>();

            Button oldButton = new Button() { Width = 0, Location = new Point(0, 0) }; //Canh chuẩn kích thước trái phải
            for (int i = 0; i < Cons.CHESS_BOARD_HEIGHT; i++)
            {
                Matrix.Add(new List<Button>());

                for (int j = 0; j < Cons.CHESS_BOARD_WIDTH; j++)
                {
                    Button btn = new Button()
                    {
                        Width = Cons.CHESS_WIDTH,
                        Height = Cons.CHESS_HEIGHT,
                        Location = new Point(oldButton.Location.X + oldButton.Width, oldButton.Location.Y),
                        BackgroundImageLayout = ImageLayout.Stretch,
                        Tag = i.ToString() //Xac dinh
                    };

                    btn.Click += Btn_Click;

                    ChessBoard.Controls.Add(btn);

                    Matrix[i].Add(btn);

                    oldButton = btn;
                }
                oldButton.Location = new Point(0, oldButton.Location.Y + Cons.CHESS_HEIGHT);
                oldButton.Width = 0;
                oldButton.Height = 0;
            }

            ChangePlayer();

        }

        void Btn_Click(object? sender, EventArgs e)
        {
            if (sender is not Button btn)
                return;

            if (btn.BackgroundImage != null) //Không cho thay đổi khi đã đánh 
                return;

            int movePlayer = CurrentPlayer;
            Mark(btn);

            List<Button>? winningCells = FindWinningCells(btn);
            if (winningCells is not null)
            {
                EndGame(movePlayer, winningCells);
                return;
            }

            ChangePlayer();
        }

        private void EndGame(int winnerIndex, IEnumerable<Button> winningCells)
        {
            ChessBoard.Enabled = false;
            HighlightWinningCells(winningCells);
            GameEnded?.Invoke(winnerIndex);
        }

        private List<Button>? FindWinningCells(Button lastMove)
        {
            Point point = GetChessPoint(lastMove);
            Image? mark = lastMove.BackgroundImage;
            if (mark is null)
            {
                return null;
            }

            // Ngang, dọc, chéo chính và chéo phụ.
            (int Dx, int Dy)[] directions = [(1, 0), (0, 1), (1, 1), (1, -1)];
            foreach ((int dx, int dy) in directions)
            {
                var before = CollectMatchingCells(point, -dx, -dy, mark);
                var after = CollectMatchingCells(point, dx, dy, mark);
                before.Reverse();

                var line = new List<Button>(before.Count + after.Count + 1);
                line.AddRange(before);
                line.Add(lastMove);
                line.AddRange(after);

                if (line.Count >= 5)
                {
                    return line;
                }
            }

            return null;
        }

        private List<Button> CollectMatchingCells(Point start, int dx, int dy, Image mark)
        {
            var cells = new List<Button>();
            int x = start.X + dx;
            int y = start.Y + dy;

            while (x >= 0 && x < Cons.CHESS_BOARD_WIDTH && y >= 0 && y < Cons.CHESS_BOARD_HEIGHT)
            {
                Button cell = Matrix[y][x];
                if (cell.BackgroundImage != mark)
                {
                    break;
                }

                cells.Add(cell);
                x += dx;
                y += dy;
            }

            return cells;
        }

        private static void HighlightWinningCells(IEnumerable<Button> winningCells)
        {
            foreach (Button cell in winningCells)
            {
                cell.UseVisualStyleBackColor = false;
                cell.FlatStyle = FlatStyle.Flat;
                cell.FlatAppearance.BorderSize = 3;
                cell.FlatAppearance.BorderColor = Color.OrangeRed;
                cell.BackColor = Color.Gold;
            }
        }

        private bool isEndGame(Button btn)
        {
            return isEndHorizontal(btn) || isEndVertical(btn) || isEndPrimary(btn) || isEndSub(btn); ;
        }

        private Point GetChessPoint(Button btn)
        {

            int vertical = Convert.ToInt32(btn.Tag);
            int horizoltal = Matrix[vertical].IndexOf(btn);

            Point point = new Point(horizoltal, vertical);
            return point;
        }
        private bool isEndHorizontal(Button btn)
        {
            Point point = GetChessPoint(btn);

            int countLeft = 0;
            for (int i = point.X; i >= 0; i--)
            {
                if (Matrix[point.Y][i].BackgroundImage == btn.BackgroundImage) 
                {
                    countLeft++;
                }
                else
                    break;
            }
            
            int countRight = 0;
            for (int i = point.X + 1; i < Cons.CHESS_BOARD_WIDTH; i++)
            {
                if (Matrix[point.Y][i].BackgroundImage == btn.BackgroundImage) 
                {
                    countRight++;
                }
               else
                    break;
            }

            return countLeft + countRight >= 5;
        }
        private bool isEndVertical(Button btn)
        {
            Point point = GetChessPoint(btn);
         
            int countTop = 0;
            for (int i = point.Y; i >= 0; i--)
            {
                if (Matrix[i][point.X].BackgroundImage == btn.BackgroundImage)
                {
                    countTop++;
                }
                else
                    break;
            }

            int countBottom = 0;
            for (int i = point.Y + 1; i < Cons.CHESS_BOARD_HEIGHT; i++)
            {
                if (Matrix[i][point.X].BackgroundImage == btn.BackgroundImage)
                {
                    countBottom++;
                }
                else
                    break;
            }

            return countTop + countBottom >= 5;
        }
        private bool isEndPrimary(Button btn)
        {
            Point point = GetChessPoint(btn);

            int countTop = 0;
            for (int i = 0; i <= point.X; i++)
            {
                if (point.X - i < 0 || point.Y - i < 0)
                    break;

                if (Matrix[point.Y - i][point.X - i].BackgroundImage == btn.BackgroundImage)
                {
                    countTop++;
                }
                else
                    break;
            }

            int countBottom = 0;
            for (int i = 1; i <= Cons.CHESS_BOARD_WIDTH - point.X; i++)
            {
                if (point.Y + i >= Cons.CHESS_BOARD_HEIGHT || point.X + i >= Cons.CHESS_BOARD_WIDTH)
                    break;

                if (Matrix[point.Y + i][point.X + i].BackgroundImage == btn.BackgroundImage)
                {
                    countBottom++;
                }
                else
                    break;
            }

            return countTop + countBottom >= 5;
        }
        private bool isEndSub(Button btn)
        {
            Point point = GetChessPoint(btn);

            int countTop = 0;
            for (int i = 0; i <= point.X; i++)
            {
                if (point.X + i >= Cons.CHESS_BOARD_WIDTH || point.Y - i < 0)
                    break;

                if (Matrix[point.Y - i][point.X + i].BackgroundImage == btn.BackgroundImage)
                {
                    countTop++;
                }
                else
                    break;
            }

            int countBottom = 0;
            for (int i = 1; i <= Cons.CHESS_BOARD_WIDTH - point.X; i++)
            {
                if (point.Y + i >= Cons.CHESS_BOARD_HEIGHT || point.X - i < 0)
                    break;

                if (Matrix[point.Y + i][point.X - i].BackgroundImage == btn.BackgroundImage)
                {
                    countBottom++;
                }
                else
                    break;
            }

            return countTop + countBottom >= 5;
        }

        private void Mark(Button btn)
        {
            btn.BackgroundImage = Player[CurrentPlayer].Mark; //Thay đổi x hoặc o sau mỗi lần click

            CurrentPlayer = CurrentPlayer == 1 ? 0 : 1;
        }

        private void ChangePlayer()
        {
            PlayerMark.Image = Player[CurrentPlayer].Mark;
        }
        #endregion


    }
}
