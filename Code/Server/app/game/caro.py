import random


class Caro:

    def __init__(self, rows: int, cols: int, winning_condition: int = 5, XO: str = "X"):
        """
        rows: nb of rows
        cols: nb of cols
        winning_condition: save the length of X/O
        XO: current character
        """
        self.originXO = XO
        self.rows = rows
        self.cols = cols
        self.grid = [["." for _ in range(self.cols)] for _ in range(self.rows)]
        self.winning_condition = winning_condition
        self.XO = XO
        self.last_move = []
        self.hard_ai = 7
        self.turn = 1
        self.ai_turn = 2
        self.is_use_ai = False

    def _get_possible_moves(self):
        possible_moves = []
        for x in range(self.rows):
            for y in range(self.rows):
                if self.grid[x][y] == ".":
                    possible_moves.append((x, y))

        return possible_moves

    def reset(self):
        self.grid = [["." for _ in range(self.cols)] for _ in range(self.rows)]
        self.last_move = []
        self.turn = 1
        self.XO = self.originXO

    def _visualize_grid(self):
        for i in range(self.rows):
            print(self.grid[i])

    def _make_move(self, X: int, Y: int):
        if self.grid[X][Y] != ".":
            return

        self.grid[X][Y] = self.XO
        move = (X, Y)
        self.last_move.append(move)

        if self.XO == "X":
            self.XO = "O"
        else:
            self.XO = "X"

        if self.turn == 1:
            self.turn = 2
        else:
            self.turn = 1

    def _get_all_cols(self):
        columns = []
        for y in range(self.cols):
            col = []
            for x in range(self.rows):
                col.append(self.grid[x][y])
            columns.append(col)
        return columns

    def _get_all_diagonals(self):
        diagonals = []
        for y in range(self.rows):
            x = 0
            diagonal = []
            while x < self.cols and y < self.rows:
                diagonal.append(self.grid[x][y])
                x += 1
                y += 1
            diagonals.append(diagonal)

        for y in range(self.rows):
            x = self.cols - 1
            diagonal = []
            while x >= 0 and y < self.rows:
                diagonal.append(self.grid[x][y])
                x -= 1
                y += 1
            diagonals.append(diagonal)

        for x in range(1, self.cols):
            y = 0
            diagonal = []
            while x < self.cols and y < self.rows:
                diagonal.append(self.grid[x][y])
                x += 1
                y += 1
            diagonals.append(diagonal)

        for x in range(self.cols - 1):
            y = 0
            diagonal = []
            while x >= 0 and y < self.rows:
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
        for x in range(self.rows):
            for y in range(self.cols):
                if self.grid[x][y] == ".":
                    return False
        return True


def _create_test_board(rows=15, cols=15, empty=True):
    if empty:
        return [["."] * cols for _ in range(rows)]
    return [[random.choice([".", "X", "O"]) for _ in range(cols)] for _ in range(rows)]


if __name__ == "__main__":
    caro = Caro(5, 5, winning_condition=5)
    caro.grid = _create_test_board(rows=5, cols=5, empty=False)
    caro._visualize_grid()
    print(caro._get_winner())
