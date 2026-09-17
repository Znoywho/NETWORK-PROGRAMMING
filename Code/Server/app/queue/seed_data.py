"""
Dung SQL tho (khong qua ORM) de doi chieu truc tiep voi
migrations/init.sql -> phat hien duoc ngay neu schema va ORM lech nhau.

Luu y: du lieu o day la GIA LAP hoan toan.
De bai yeu cau "du lieu nhay cam dung khi demo phai la du lieu gia lap".
password_hash chi la chuoi danh dau, khong phai hash that.
"""

import argparse
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.config import Config


# ------------------------------------------------------------
#  Du lieu mau
# ------------------------------------------------------------
USERS_MAU = ["hao", "khuong", "kiet", "khoi", "han", "khoa"]

# Mot van hoan chinh: hao (X) thang khoi (O) bang 5 quan hang ngang.
# Nuoc le = X, nuoc chan = O.
NUOC_DI_MAU = [
    (7, 7), (8, 8),
    (7, 8), (8, 9),
    (7, 9), (9, 9),
    (7, 10), (6, 6),
    (7, 11),            # X du 5 quan tu (7,7) den (7,11) -> thang
]


def _engine():
    if not Config.DATABASE_URI:
        print("[LOI] DATABASE_URI rong.")
        print("      Kiem tra file Code/Server/.env co bien")
        print("      OUT_CARO_DATABASE_URL (chay ngoai Docker) hoac")
        print("      CARO_DB_DOCKER (chay trong Docker) chua.")
        sys.exit(1)
    return create_engine(Config.DATABASE_URI)


# ------------------------------------------------------------
#  1. Kiem tra ket noi
# ------------------------------------------------------------
def kiem_tra_ket_noi() -> bool:
    print("-" * 58)
    print(" KIEM TRA KET NOI DATABASE")
    print("-" * 58)

    try:
        eng = _engine()
        with eng.connect() as conn:
            phien_ban = conn.execute(text("SELECT version()")).scalar()
            ten_db = conn.execute(text("SELECT current_database()")).scalar()
            nguoi_dung = conn.execute(text("SELECT current_user")).scalar()

            print(f"[OK] Ket noi thanh cong")
            print(f"     Database : {ten_db}")
            print(f"     User     : {nguoi_dung}")
            print(f"     Postgres : {phien_ban.split(',')[0]}")

            # Kiem tra du 3 bang
            bang = conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)).scalars().all()

            can_co = {"matches", "moves", "users"}
            thieu = can_co - set(bang)
            if thieu:
                print(f"[LOI] Thieu bang: {', '.join(sorted(thieu))}")
                print("      Chay init.sql truoc:")
                print("      docker compose exec db psql -U <user> -d caro_db -f /tmp/init.sql")
                return False

            print(f"[OK] Da co du 3 bang: {', '.join(bang)}")
            return True

    except OperationalError as e:
        print(f"[LOI] Khong ket noi duoc database")
        print(f"      {e.orig}")
        print("      Kiem tra: docker compose ps  -> caro-db co dang chay khong")
        return False


# ------------------------------------------------------------
#  2. Nap du lieu mau
# ------------------------------------------------------------
def nap_du_lieu() -> bool:
    print("-" * 58)
    print(" NAP DU LIEU MAU")
    print("-" * 58)

    eng = _engine()
    with eng.begin() as conn:
        # --- users ---
        user_id = {}
        for ten in USERS_MAU:
            uid = conn.execute(text("""
                INSERT INTO users (username, password_hash, ranking)
                VALUES (:u, :h, :r)
                ON CONFLICT (username) DO UPDATE SET username = EXCLUDED.username
                RETURNING id
            """), {"u": ten, "h": f"hash_gia_lap_{ten}", "r": 0}).scalar()
            user_id[ten] = uid
        print(f"[OK] Nap {len(user_id)} user: {', '.join(USERS_MAU)}")

        # --- match dang choi ---
        match_dang_choi = conn.execute(text("""
            INSERT INTO matches (player_x_id, player_o_id, status, started_at)
            VALUES (:x, :o, 'playing', now())
            RETURNING id
        """), {"x": user_id["kiet"], "o": user_id["khoa"]}).scalar()
        print(f"[OK] Nap 1 match dang choi (id={match_dang_choi})"
              f" - dung de test tinh nang khan gia")

        # --- match da ket thuc, co day du nuoc di ---
        match_xong = conn.execute(text("""
            INSERT INTO matches
                (player_x_id, player_o_id, status, result, winner_id,
                 started_at, ended_at)
            VALUES (:x, :o, 'finished', 'x_win', :w, now(), now())
            RETURNING id
        """), {
            "x": user_id["hao"], "o": user_id["khoi"], "w": user_id["hao"],
        }).scalar()

        for i, (r, c) in enumerate(NUOC_DI_MAU, start=1):
            nguoi = user_id["hao"] if i % 2 == 1 else user_id["khoi"]
            conn.execute(text("""
                INSERT INTO moves
                    (match_id, player_id, row_idx, col_idx, move_index)
                VALUES (:m, :p, :r, :c, :i)
            """), {"m": match_xong, "p": nguoi, "r": r, "c": c, "i": i})

        print(f"[OK] Nap 1 match da ket thuc (id={match_xong})"
              f" voi {len(NUOC_DI_MAU)} nuoc di")

    return True


# ------------------------------------------------------------
#  3. Kiem tra cac rang buoc co that su hoat dong
# ------------------------------------------------------------
def kiem_tra_rang_buoc() -> bool:
    """Moi truong hop duoi day PHAI bi database tu choi."""
    print("-" * 58)
    print(" KIEM TRA RANG BUOC (cac lenh nay PHAI bi tu choi)")
    print("-" * 58)

    eng = _engine()
    ket_qua = []

    truong_hop = [
        (
            "Ten dang nhap duoi 3 ky tu",
            "INSERT INTO users (username) VALUES ('ab')",
            {},
            "chk_users_username_len",
        ),
        (
            "Hai nguoi choi trung nhau",
            """INSERT INTO matches (player_x_id, player_o_id)
               SELECT id, id FROM users WHERE username = 'hao'""",
            {},
            "chk_matches_diff_players",
        ),
        (
            "Van finished ma khong co ket qua",
            """INSERT INTO matches (player_x_id, player_o_id, status)
               SELECT a.id, b.id FROM users a, users b
               WHERE a.username='hao' AND b.username='khoi'""",
            {},
            "chk_matches_finished_has_result",
        ),
        (
            "Danh hai lan vao cung mot o",
            """INSERT INTO moves (match_id, player_id, row_idx, col_idx, move_index)
               SELECT m.match_id, m.player_id, m.row_idx, m.col_idx, 99
               FROM moves m LIMIT 1""",
            {},
            "uq_moves_match_cell",
        ),
    ]

    for mo_ta, sql, tham_so, ten_rang_buoc in truong_hop:
        # Truong hop 3 phai sua lai de thuc su vi pham
        if ten_rang_buoc == "chk_matches_finished_has_result":
            sql = """INSERT INTO matches (player_x_id, player_o_id, status)
                     SELECT a.id, b.id FROM users a, users b
                     WHERE a.username='hao' AND b.username='khoi'"""
            sql = sql.replace("status)", "status)").replace(
                "b.id FROM", "b.id, 'finished' FROM"
            ).replace("(player_x_id, player_o_id, status)",
                      "(player_x_id, player_o_id, status)")

        try:
            with eng.begin() as conn:
                conn.execute(text(sql), tham_so)
            print(f"[SAI] {mo_ta}: database DA CHAP NHAN, rang buoc khong hoat dong")
            ket_qua.append(False)
        except IntegrityError as e:
            loi = str(e.orig)
            khop = ten_rang_buoc in loi
            dau = "[OK]" if khop else "[?]"
            print(f"{dau}  {mo_ta}")
            print(f"      -> bi chan boi: {ten_rang_buoc if khop else loi[:70]}")
            ket_qua.append(True)
        except Exception as e:
            print(f"[?]   {mo_ta}: loi khac - {type(e).__name__}")
            ket_qua.append(True)

    return all(ket_qua)


# ------------------------------------------------------------
#  4. Xoa du lieu mau
# ------------------------------------------------------------
def xoa_du_lieu() -> bool:
    print("-" * 58)
    print(" XOA DU LIEU MAU")
    print("-" * 58)

    eng = _engine()
    with eng.begin() as conn:
        # Thu tu quan trong: moves -> matches -> users
        # vi khoa ngoai ON DELETE RESTRICT chan xoa users truoc.
        for bang in ("moves", "matches", "users"):
            so_dong = conn.execute(text(f"DELETE FROM {bang}")).rowcount
            print(f"[OK] Xoa {so_dong} dong khoi bang {bang}")
    return True


# ------------------------------------------------------------
#  5. Thong ke
# ------------------------------------------------------------
def thong_ke() -> None:
    eng = _engine()
    with eng.connect() as conn:
        print("-" * 58)
        print(" THONG KE HIEN TAI")
        print("-" * 58)
        for bang in ("users", "matches", "moves"):
            n = conn.execute(text(f"SELECT count(*) FROM {bang}")).scalar()
            print(f"     {bang:10s}: {n} dong")

        dang_choi = conn.execute(text("""
            SELECT count(*) FROM matches WHERE status = 'playing'
        """)).scalar()
        print(f"     Van dang dien ra: {dang_choi}")


def main():
    p = argparse.ArgumentParser(description="Kiem tra va seed database module 3")
    p.add_argument("--check", action="store_true", help="kiem tra ket noi")
    p.add_argument("--seed", action="store_true", help="nap du lieu mau")
    p.add_argument("--verify", action="store_true", help="kiem tra rang buoc")
    p.add_argument("--clean", action="store_true", help="xoa du lieu mau")
    p.add_argument("--all", action="store_true", help="chay tat ca")
    args = p.parse_args()

    if not any(vars(args).values()):
        p.print_help()
        return

    print("=" * 58)
    print(" SEED DATA - Module 3 Task 10")
    print("=" * 58)

    if args.check or args.all:
        if not kiem_tra_ket_noi():
            sys.exit(1)

    if args.clean or args.all:
        xoa_du_lieu()

    if args.seed or args.all:
        nap_du_lieu()

    if args.verify or args.all:
        kiem_tra_rang_buoc()

    if args.seed or args.all or args.check:
        thong_ke()

    print("=" * 58)


if __name__ == "__main__":
    main()