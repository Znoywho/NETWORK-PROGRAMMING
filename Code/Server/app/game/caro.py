import random


class Caro:

    EMPTY = None  # Trạng thái ô trống
 
    PLAYER_X = "X"
    PLAYER_O = "O"
 
    STATUS_PLAYING = "playing"   # đang chơi
    STATUS_ENDED = "ended"       # đã kết thúc

    def __init__(self, size: int = 15):
        # ----- Task 1: Ma trận ô cờ -----
        self.size = size
        # grid[row][col] = None (trống) / "X" / "O"
        self.grid = [[self.EMPTY for _ in range(size)] for _ in range(size)]
 
        # ----- Task 2: Trạng thái ván đấu -----
        self.current_turn = self.PLAYER_X   # X luôn đi trước
        self.player_X = "Player 1"          # tên/id người chơi X (có thể gán lại)
        self.player_O = "Player 2"          # tên/id người chơi O (có thể gán lại)
        self.status = self.STATUS_PLAYING   # trạng thái ván đấu

    def get_cell(self, row: int, col: int):
        """Lấy trạng thái của 1 ô (None / 'X' / 'O')"""
        return self.grid[row][col]
 
    def set_cell(self, row: int, col: int, value):
        """Đặt trạng thái cho 1 ô (đánh cờ vào ô đó)"""
        self.grid[row][col] = value
 
    def is_in_bounds(self, row: int, col: int) -> bool:
        """Kiểm tra tọa độ có nằm trong bàn cờ không"""
        return 0 <= row < self.size and 0 <= col < self.size
 
    def is_empty(self, row: int, col: int) -> bool:
        """Kiểm tra ô có đang trống không"""
        return self.get_cell(row, col) == self.EMPTY

    def _get_all_rows(self):
        return self.grid

    def _get_all_cols(self):
        columns = []
        for y in range(self.size):
            col = []
            for x in range(self.size):
                col.append(self.grid[x][y])
            columns.append(col)
        return columns

    def _get_all_diagonals(self):
        diagonals = []
        for y in range(self.size):
            x = 0
            diagonal = []
            while x < self.size and y < self.size:
                diagonal.append(self.grid[x][y])
                x += 1
                y += 1
            diagonals.append(diagonal)

        for y in range(self.size):
            x = self.size - 1
            diagonal = []
            while x >= 0 and y < self.size:
                diagonal.append(self.grid[x][y])
                x -= 1
                y += 1
            diagonals.append(diagonal)

        for x in range(1, self.size):
            y = 0
            diagonal = []
            while x < self.size and y < self.size:
                diagonal.append(self.grid[x][y])
                x += 1
                y += 1
            diagonals.append(diagonal)

        for x in range(self.size - 1):
            y = 0
            diagonal = []
            while x >= 0 and y < self.size:
                diagonal.append(self.grid[x][y])
                x -= 1
                y += 1
            diagonals.append(diagonal)
        return diagonals

    def _get_winner(self):
        """
        X => 0
        Y => 1
        no player win => -1
        run out of all of cells => 2
        """

        def _check_consecutive(cons):
            for con in cons:
                count_X = 0
                count_O = 0
                for c in con:
                    if c == "X":
                        count_X += 1
                        count_O = 0
                    elif c == "O":
                        count_O += 1
                        count_X = 0
                    else:
                        count_X = 0
                        count_O = 0
                    if count_X == self.winning_condition:
                        return 0
                    if count_O == self.winning_condition:
                        return 1
            return -1

        rows = self._get_all_rows()
        cols = self._get_all_cols()
        diagonals = self._get_all_diagonals()

        winner = -1
        winner = _check_consecutive(rows)
        if winner != -1:
            return winner

        winner = _check_consecutive(cols)
        if winner != -1:
            return winner

        winner = _check_consecutive(diagonals)
        if winner != -1:
            return winner

        if self._is_terminate():
            if winner == -1:
                return 2
        return winner

    def _is_terminate(self):
        for x in range(self.size):
            for y in range(self.size):
                if self.grid[x][y] == ".":
                    return False
        return True


def _create_test_board(size=15, empty=True):
    if empty:
        return [["."] * size for _ in range(size)]
    return [[random.choice([".", "X", "O"]) for _ in range(size)] for _ in range(size)]


if __name__ == "__main__":
    caro = Caro(5, 5, winning_condition=5)
    caro.grid = _create_test_board(5, False)
    caro._visualize_grid()
    print(caro._get_winner())
