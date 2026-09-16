import pygame

WIDTH, HEIGHT = 1200, 720
SIDEBAR_W = 300
FPS = 30

COL_BG = (50, 94, 106)
COL_PANEL = (32, 35, 44)
COL_PANEL_ALT = (38, 42, 52)
COL_BORDER = (55, 59, 70)
COL_TEXT = (230, 230, 235)
COL_TEXT_DIM = (150, 154, 165)
COL_ACCENT = (86, 156, 255)
COL_GREEN = (95, 200, 130)
COL_YELLOW = (230, 190, 90)
COL_RED = (230, 100, 100)
COL_SELECTED = (52, 58, 74)
COL_GRID = (70, 74, 86)
COL_X = (240, 120, 120)
COL_O = (110, 170, 240)

STATUS_COLOR = {
    "idle": COL_TEXT_DIM,
    "playing": COL_GREEN,
    "spectating": COL_YELLOW,
    "waiting": COL_YELLOW,
    "finished": COL_TEXT_DIM,
}



# ----------------------------------------------------------------------------
# Đọc dữ liệu an toàn từ manager (dùng chung lock của chính manager đó)
# ----------------------------------------------------------------------------
def _snapshot_players(player_manager) -> list:
    with player_manager._lock:
        return list(player_manager._players.values())


def _snapshot_rooms(room_manager) -> list:
    with room_manager._lock:
        return list(room_manager._rooms.values())


def _enum_val(x):
    """Room.status / Player.status có thể là Enum hoặc string, chuẩn hoá về string."""
    return getattr(x, "value", x)


# ----------------------------------------------------------------------------
# UI helpers
# ----------------------------------------------------------------------------
class Button:
    """Vùng bấm được, lưu callback để gọi khi click."""

    def __init__(self, rect, on_click, data=None):
        self.rect = pygame.Rect(rect)
        self.on_click = on_click
        self.data = data

    def hit(self, pos):
        return self.rect.collidepoint(pos)


def draw_text(surf, font, text, pos, color=COL_TEXT, max_w=None):
    if max_w is not None:
        while font.size(text)[0] > max_w and len(text) > 1:
            text = text[:-1]
        if font.size(text)[0] > max_w:
            text = text[: max(0, len(text) - 3)] + "..."
    img = font.render(text, True, color)
    surf.blit(img, pos)
    return img.get_width()
