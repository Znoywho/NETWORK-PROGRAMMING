import sys
import unittest
from pathlib import Path

# Tro vao thu muc Server chu khong phai Server/app: neu them app/ vao sys.path
# thi package app/queue/ se che mat module `queue` cua stdlib.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.game.caro import Caro


class ValidateMoveTurnTest(unittest.TestCase):
    """current_turn phai doi luot sau moi nuoc di.

    Bug cu: _make_move doi self.XO va self.turn nhung quen current_turn, nen
    validate_move so voi luot luc khoi tao mai mai -> O khong bao gio danh duoc.
    """

    def setUp(self):
        self.board = Caro(9, 9, winning_condition=5)

    def test_x_di_truoc_o_phai_doi(self):
        self.assertTrue(self.board.validate_move(3, 3, "X"))
        self.assertFalse(self.board.validate_move(3, 3, "O"))

    def test_doi_luot_sau_moi_nuoc(self):
        self.board._make_move(3, 3)
        self.assertTrue(self.board.validate_move(3, 4, "O"))
        self.assertFalse(self.board.validate_move(3, 4, "X"))

        self.board._make_move(3, 4)
        self.assertTrue(self.board.validate_move(4, 4, "X"))
        self.assertFalse(self.board.validate_move(4, 4, "O"))

    def test_current_turn_bam_sat_xo_qua_nhieu_nuoc(self):
        for i in range(20):
            row, col = divmod(i, 9)
            self.board._make_move(row, col)
            self.assertEqual(
                self.board.XO,
                self.board.current_turn,
                msg=f"lech nhau sau nuoc thu {i + 1}",
            )

    def test_o_da_co_quan_khong_an_mat_luot(self):
        self.board._make_move(3, 3)
        luot_truoc = self.board.current_turn

        self.board._make_move(3, 3)  # o da bi chiem -> _make_move thoat som

        self.assertEqual(luot_truoc, self.board.current_turn)
        self.assertEqual("X", self.board.grid[3][3])

    def test_ban_co_khoi_tao_voi_o_di_truoc(self):
        board = Caro(9, 9, winning_condition=5, XO="O")
        self.assertTrue(board.validate_move(3, 3, "O"))
        self.assertFalse(board.validate_move(3, 3, "X"))

    def test_reset_tra_luot_ve_ban_dau(self):
        self.board._make_move(3, 3)
        self.assertEqual("O", self.board.current_turn)

        self.board.reset()

        self.assertEqual("X", self.board.current_turn)
        self.assertEqual("playing", self.board.status)
        self.assertTrue(self.board.validate_move(3, 3, "X"))


class ValidateMoveRulesTest(unittest.TestCase):
    """Ba dieu kien con lai cua validate_move: trong bien, o trong, van chua xong."""

    def setUp(self):
        self.board = Caro(9, 9, winning_condition=5)

    def test_tu_choi_nuoc_ngoai_ban_co(self):
        for row, col in ((-1, 0), (0, -1), (9, 0), (0, 9)):
            with self.subTest(row=row, col=col):
                self.assertFalse(self.board.validate_move(row, col, "X"))

    def test_tu_choi_o_da_co_quan(self):
        self.board._make_move(3, 3)
        self.assertFalse(self.board.validate_move(3, 3, "O"))

    def test_van_da_xong_thi_tu_choi_moi_nuoc(self):
        self.assertTrue(self.board.validate_move(3, 3, "X"))

        self.board.status = "finished"

        # Dung luot, dung bien, o van trong -- nhung van da ket thuc.
        self.assertFalse(self.board.validate_move(3, 3, "X"))


if __name__ == "__main__":
    unittest.main()
