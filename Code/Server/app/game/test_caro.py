import unittest

from caro import Caro


class TestCaroWin(unittest.TestCase):
    """Test các trường hợp thắng: ngang / dọc / chéo"""

    def setUp(self):
        # Bàn 5x5, cần 3 quân liên tiếp để thắng -> dễ dựng test case
        self.game = Caro(rows=5, cols=5, winning_condition=3)

    def test_win_horizontal(self):
        # X thắng theo hàng ngang: (2,0) (2,1) (2,2)
        self.game.set_cell(2, 0, "X")
        self.game.set_cell(2, 1, "X")
        self.game.set_cell(2, 2, "X")
        self.assertEqual(self.game._get_winner(), 0)  # 0 = X thắng

    def test_win_vertical(self):
        # O thắng theo cột dọc: (0,3) (1,3) (2,3)
        self.game.set_cell(0, 3, "O")
        self.game.set_cell(1, 3, "O")
        self.game.set_cell(2, 3, "O")
        self.assertEqual(self.game._get_winner(), 1)  # 1 = O thắng

    def test_win_diagonal_main(self):
        # X thắng theo đường chéo chính: (0,0) (1,1) (2,2)
        self.game.set_cell(0, 0, "X")
        self.game.set_cell(1, 1, "X")
        self.game.set_cell(2, 2, "X")
        self.assertEqual(self.game._get_winner(), 0)

    def test_win_diagonal_anti(self):
        # O thắng theo đường chéo phụ: (0,2) (1,1) (2,0)
        self.game.set_cell(0, 2, "O")
        self.game.set_cell(1, 1, "O")
        self.game.set_cell(2, 0, "O")
        self.assertEqual(self.game._get_winner(), 1)

    def test_no_winner_yet(self):
        # Chưa đủ quân liên tiếp -> chưa ai thắng
        self.game.set_cell(0, 0, "X")
        self.game.set_cell(0, 1, "X")
        self.assertEqual(self.game._get_winner(), -1)


class TestCaroInvalidMove(unittest.TestCase):
    """Test các trường hợp nước đi không hợp lệ"""

    def setUp(self):
        self.game = Caro(rows=5, cols=5, winning_condition=3, XO="X")

    def test_valid_move(self):
        # Đúng lượt X, ô trống, trong bàn cờ -> hợp lệ
        self.assertTrue(self.game.validate_move(0, 0, "X"))

    def test_invalid_move_wrong_turn(self):
        # Chưa tới lượt O
        self.assertFalse(self.game.validate_move(0, 0, "O"))

    def test_invalid_move_out_of_bounds_negative(self):
        self.assertFalse(self.game.validate_move(-1, 0, "X"))

    def test_invalid_move_out_of_bounds_too_large(self):
        self.assertFalse(self.game.validate_move(5, 5, "X"))  # bàn 5x5 -> index hợp lệ 0..4

    def test_invalid_move_occupied_cell(self):
        self.game.set_cell(2, 2, "X")
        self.assertFalse(self.game.validate_move(2, 2, "O"))

    def test_invalid_move_when_game_finished(self):
        self.game.status = "finished"
        self.assertFalse(self.game.validate_move(0, 0, "X"))


class TestCaroDraw(unittest.TestCase):
    """Test trường hợp hoà cờ (bàn đầy, không ai đủ điều kiện thắng)"""

    def test_draw_when_board_full_no_winner(self):
        game = Caro(rows=3, cols=3, winning_condition=3)
        # Bố trí sao cho bàn đầy nhưng không ai có 3 quân liên tiếp
        board = [
            ["X", "O", "X"],
            ["X", "O", "O"],
            ["O", "X", "X"],
        ]
        for r in range(3):
            for c in range(3):
                game.set_cell(r, c, board[r][c])

        self.assertEqual(game._get_winner(), 2)  # 2 = hoà


class TestCaroGameResult(unittest.TestCase):
    """Test bonus: message game_result sinh ra đúng khi ván đấu kết thúc"""

    def test_game_result_win_message(self):
        game = Caro(rows=5, cols=5, winning_condition=3)
        game.set_cell(0, 0, "X")
        game.set_cell(0, 1, "X")
        game.set_cell(0, 2, "X")

        result = game.get_game_result()
        self.assertIsNotNone(result)
        self.assertEqual(result["result"], "win")
        self.assertEqual(result["winner"], "X")
        self.assertEqual(game.status, "finished")

    def test_game_result_none_when_not_finished(self):
        game = Caro(rows=5, cols=5, winning_condition=3)
        game.set_cell(0, 0, "X")
        result = game.get_game_result()
        self.assertIsNone(result)
        self.assertEqual(game.status, "playing")


if __name__ == "__main__":
    unittest.main()
