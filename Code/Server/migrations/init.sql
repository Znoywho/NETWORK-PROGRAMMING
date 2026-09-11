
--  Module 3: Database & Queue Writer  (Nguyen Dinh Duy Khuong)
--
--  File nay duoc PostgreSQL tu dong chay lan dau khoi tao container
--  (mount vao /docker-entrypoint-initdb.d/ trong docker-compose.yml)
-- ============================================================


-- ------------------------------------------------------------
--  Bang 1: users
--  Luu tai khoan nguoi choi. id chinh la playerId trong message JSON.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(32)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    last_login_at   TIMESTAMPTZ,

    CONSTRAINT chk_users_username_len CHECK (char_length(username) >= 3)
);

COMMENT ON TABLE  users               IS 'Tai khoan nguoi choi';
COMMENT ON COLUMN users.id            IS 'Tuong ung playerId trong message-schema.json';
COMMENT ON COLUMN users.password_hash IS 'Chi luu hash (bcrypt/argon2), KHONG bao gio luu mat khau goc';


-- ------------------------------------------------------------
--  Bang 2: matches
--  Moi ban ghi la mot van dau. id lay tu room_id cua RoomManager.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS matches (
    id              VARCHAR(16)  PRIMARY KEY,
    player_x_id     UUID         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    player_o_id     UUID         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status          VARCHAR(16)  NOT NULL DEFAULT 'waiting',
    result          VARCHAR(16),
    winner_id       UUID                  REFERENCES users(id) ON DELETE SET NULL,
    board_rows      SMALLINT     NOT NULL DEFAULT 15,
    board_cols      SMALLINT     NOT NULL DEFAULT 15,
    win_condition   SMALLINT     NOT NULL DEFAULT 5,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,

    -- Hai nguoi choi phai khac nhau
    CONSTRAINT chk_matches_diff_players
        CHECK (player_x_id <> player_o_id),

    -- Trang thai khop voi RoomStatus ben module 4
    CONSTRAINT chk_matches_status
        CHECK (status IN ('waiting', 'playing', 'finished', 'aborted')),

    -- Ket qua khop voi message game_result
    CONSTRAINT chk_matches_result
        CHECK (result IS NULL OR result IN ('x_win', 'o_win', 'draw', 'aborted')),

    -- Van da ket thuc thi bat buoc phai co ket qua va thoi diem ket thuc
    CONSTRAINT chk_matches_finished_has_result
        CHECK (status <> 'finished' OR (result IS NOT NULL AND ended_at IS NOT NULL)),

    -- Hoa hoac huy thi khong duoc co nguoi thang
    CONSTRAINT chk_matches_winner_consistency
        CHECK (result IS NULL OR result IN ('draw', 'aborted') OR winner_id IS NOT NULL),

    CONSTRAINT chk_matches_time_order
        CHECK (ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at)
);

COMMENT ON TABLE  matches           IS 'Lich su cac van dau';
COMMENT ON COLUMN matches.id        IS 'Tuong ung matchId trong message JSON, lay tu room_id (uuid4 cat 8 ky tu)';
COMMENT ON COLUMN matches.result    IS 'x_win / o_win / draw / aborted. Client tu suy ra win|lose tu goc nhin cua minh';


-- ------------------------------------------------------------
--  Bang 3: moves
--  Luu tung nuoc di theo thu tu, dung de phat lai van dau va reconnect.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS moves (
    id          BIGSERIAL    PRIMARY KEY,
    match_id    VARCHAR(16)  NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id   UUID         NOT NULL REFERENCES users(id)   ON DELETE RESTRICT,
    row_idx     SMALLINT     NOT NULL,
    col_idx     SMALLINT     NOT NULL,
    move_index  INTEGER      NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT chk_moves_coord_non_negative
        CHECK (row_idx >= 0 AND col_idx >= 0),

    CONSTRAINT chk_moves_index_positive
        CHECK (move_index >= 1),

    -- Khong the co hai nuoc cung so thu tu trong mot van
    CONSTRAINT uq_moves_match_order
        UNIQUE (match_id, move_index),

    -- Khong the danh hai lan vao cung mot o. Chot o tang database,
    -- de phong truong hop Game Engine bi bo qua hoac co race condition.
    CONSTRAINT uq_moves_match_cell
        UNIQUE (match_id, row_idx, col_idx)
);

COMMENT ON TABLE  moves            IS 'Tung nuoc di trong van dau, sap xep theo move_index';
COMMENT ON COLUMN moves.row_idx    IS 'Dat ten row_idx vi ROW la tu khoa cua SQL, khong dung lam ten cot duoc';
COMMENT ON COLUMN moves.move_index IS 'Bat dau tu 1. So le = luot X, so chan = luot O';


-- ------------------------------------------------------------
--  Index
--  UNIQUE o tren da tu tao index cho (match_id, move_index)
--  va (match_id, row_idx, col_idx) nen khong khai bao lai.
-- ------------------------------------------------------------

-- Loc cac van dang dien ra de hien thi danh sach cho khan gia chon
CREATE INDEX IF NOT EXISTS idx_matches_status
    ON matches (status)
    WHERE status IN ('waiting', 'playing');

-- Tra lich su dau cua mot nguoi choi, moi nhat truoc
CREATE INDEX IF NOT EXISTS idx_matches_player_x
    ON matches (player_x_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_matches_player_o
    ON matches (player_o_id, created_at DESC);


-- ------------------------------------------------------------
--  Kiem tra nhanh sau khi chay
--    \dt
--    \d+ matches
-- ------------------------------------------------------------
