"""
Giao diện người dùng đồ hoạ Pygame cho Bloxorz Solver.
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import glob
import time
from typing import Optional, List, Tuple, Dict
import pygame

from core.state import Direction, GameState, Orientation
from core.board import BloxorzBoard
from solvers import solve_bfs, solve_ids, solve_ucs, solve_astar, SearchResult
from gui.renderer import draw_iso_tile, draw_block, draw_rolling_block
from gui.animator import PlaybackAnimator, MoveAnimation

WINDOW_WIDTH = 1240
WINDOW_HEIGHT = 800
FPS = 60

COLOR_BG = (11, 17, 30)
COLOR_HEADER_BG = (17, 24, 39)
COLOR_PANEL_BG = (16, 23, 38)
COLOR_PANEL_BORDER = (30, 41, 59)

COLOR_CARD_BG = (23, 32, 51)
COLOR_CARD_HOVER = (30, 44, 68)
COLOR_CARD_ACTIVE = (20, 45, 75)
COLOR_CARD_BORDER = (39, 53, 78)
COLOR_CYAN_GLOW = (56, 189, 248)

COLOR_TEXT_WHITE = (241, 245, 249)
COLOR_TEXT_MUTED = (148, 163, 184)
COLOR_TEXT_DIM = (100, 116, 139)
COLOR_GOLD = (245, 158, 11)


class CardButton:
    """Nút bấm dạng Card có hiệu ứng hover/active."""
    def __init__(self, rect, text, icon=""):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.icon = icon
        self.is_hovered = False
        self.is_active = False

    def draw(self, surface, font, font_icon=None):
        if self.is_active:
            bg_col = COLOR_CARD_ACTIVE
            border_col = COLOR_CYAN_GLOW
            txt_col = COLOR_CYAN_GLOW
        elif self.is_hovered:
            bg_col = COLOR_CARD_HOVER
            border_col = (71, 85, 105)
            txt_col = COLOR_TEXT_WHITE
        else:
            bg_col = COLOR_CARD_BG
            border_col = COLOR_CARD_BORDER
            txt_col = COLOR_TEXT_WHITE

        pygame.draw.rect(surface, bg_col, self.rect, border_radius=8)
        pygame.draw.rect(surface, border_col, self.rect, width=1, border_radius=8)

        full_txt = f"{self.icon} {self.text}" if self.icon else self.text
        lbl = font.render(full_txt, True, txt_col)
        surface.blit(lbl, (self.rect.x + 16, self.rect.centery - lbl.get_height() // 2))

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class ActionButton:
    """Nút bấm hành động bo góc."""
    def __init__(self, rect, text, bg_color=(23, 32, 51), hover_color=(30, 44, 68), text_color=(241, 245, 249), border_color=(39, 53, 78)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_color = border_color
        self.is_hovered = False

    def draw(self, surface, font):
        col = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, col, self.rect, border_radius=6)
        pygame.draw.rect(surface, self.border_color, self.rect, width=1, border_radius=6)
        txt = font.render(self.text, True, self.text_color)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class BloxorzGUI:
    """Điều khiển giao diện chính của ứng dụng Bloxorz."""
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.is_fullscreen = False
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Project 1: Bloxorz Solver [24C01][Hcmus]")
        self.clock = pygame.time.Clock()

        self.font_title = self._get_font(18, bold=True)
        self.font_card = self._get_font(14, bold=True)
        self.font_bold = self._get_font(13, bold=True)
        self.font_normal = self._get_font(13, bold=False)
        self.font_small = self._get_font(11, bold=False)
        self.font_popup_title = self._get_font(22, bold=True)
        self.font_popup_body = self._get_font(14, bold=False)

        # Nút bấm trên Pop-up Thắng / Thua
        self.btn_popup_restart = ActionButton(
            (0, 0, 160, 40), "Thử lại ngay (R)",
            bg_color=(69, 10, 10), hover_color=(127, 29, 29),
            text_color=(254, 202, 202), border_color=(239, 68, 68)
        )
        self.btn_popup_next = ActionButton(
            (0, 0, 160, 40), "Màn tiếp theo (N)",
            bg_color=(20, 83, 45), hover_color=(22, 101, 52),
            text_color=(220, 252, 231), border_color=(74, 222, 128)
        )

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.level_files = sorted(glob.glob(os.path.join(base_dir, "levels", "*", "stage_*.json")))
        if not self.level_files:
            self.level_files = sorted(glob.glob(os.path.join(base_dir, "stages", "stage_*.json")))

        self.current_stage_idx = 0
        self.active_algo = None

        self.board: BloxorzBoard = None
        self.state: GameState = None
        self.game_over = False
        self.is_won = False
        self.move_count = 0
        self.history: list[GameState] = []

        self.search_result: SearchResult = None
        self.animator = PlaybackAnimator()
        self.manual_anim: Optional[MoveAnimation] = None

        self.hud_msg = ""
        self.hud_msg_timer = 0.0

        self.load_stage(self.current_stage_idx)
        self._init_ui_elements()

    def show_hud_message(self, text: str, duration: float = 2.5):
        self.hud_msg = text
        self.hud_msg_timer = time.time() + duration

    def _get_font(self, size: int, bold: bool = False):
        for fn in ["Segoe UI", "Arial", "Calibri", "Tahoma"]:
            try:
                f = pygame.font.SysFont(fn, size, bold=bold)
                if f:
                    return f
            except Exception:
                continue
        return pygame.font.Font(None, size)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        self._init_ui_elements()

    def _init_ui_elements(self):
        screen_w, screen_h = self.screen.get_size()

        self.rect_capsule = pygame.Rect(screen_w // 2 - 180, 16, 170, 36)
        self.btn_prev = ActionButton((self.rect_capsule.x + 6, self.rect_capsule.y + 4, 28, 28), "<", bg_color=(17, 24, 39), border_color=(30, 41, 59))
        self.btn_next = ActionButton((self.rect_capsule.right - 34, self.rect_capsule.y + 4, 28, 28), ">", bg_color=(17, 24, 39), border_color=(30, 41, 59))

        panel_w = 340
        p_x = screen_w - panel_w - 20
        y = 70

        card_h = 42
        self.btn_bfs = CardButton((p_x, y, panel_w, card_h), "BFS Solver", icon="[::]")
        y += 48
        self.btn_dfs = CardButton((p_x, y, panel_w, card_h), "DFS (IDS) Solver", icon="[|]")
        y += 48
        self.btn_ucs = CardButton((p_x, y, panel_w, card_h), "UCS Solver", icon="[-]")
        y += 48
        self.btn_astar = CardButton((p_x, y, panel_w, card_h), "A* Solver", icon="[*]")

        y = 415
        self.btn_show_anim = ActionButton(
            (p_x, y, panel_w, 38),
            "▶  SHOW ANIMATION",
            bg_color=(20, 35, 60),
            hover_color=(30, 55, 95),
            text_color=(56, 189, 248),
            border_color=(56, 189, 248)
        )

        y += 44
        half_w = (panel_w - 10) // 2
        self.btn_step_prev = ActionButton((p_x, y, half_w, 30), "<< Bước trước", bg_color=(23, 32, 51))
        self.btn_step_next = ActionButton((p_x + half_w + 10, y, half_w, 30), "Bước sau >>", bg_color=(23, 32, 51))

        y += 36
        self.btn_speed = ActionButton((p_x, y, half_w, 30), f"Tốc độ: {self.animator.speed}x", bg_color=(23, 32, 51))
        fs_lbl = "Thu nhỏ (F11)" if self.is_fullscreen else "Toàn màn (F11)"
        self.btn_fs = ActionButton((p_x + half_w + 10, y, half_w, 30), fs_lbl, bg_color=(23, 32, 51))

        y += 36
        self.btn_restart = ActionButton((p_x, y, panel_w, 30), "Chơi lại màn này (R)", bg_color=(35, 25, 30), hover_color=(55, 35, 45), text_color=(252, 165, 165), border_color=(127, 29, 29))

    #hàm cần code lại
    def load_stage(self, idx: int):
        """Nạp màn chơi theo chỉ mục."""
        if not self.level_files:
            return
        self.current_stage_idx = idx % len(self.level_files)
        filepath = self.level_files[self.current_stage_idx]
        self.board = BloxorzBoard.load_from_file(filepath)
        self.state = self.board.get_initial_state()
        self.game_over = False
        self.is_won = False
        self.move_count = 0
        self.history = [self.state]
        self.search_result = None
        self.active_algo = None
        self.animator.reset()
        self.manual_anim = None

    def restart_stage(self):
        """Khởi động lại màn chơi hiện tại."""
        self.state = self.board.get_initial_state()
        self.game_over = False
        self.is_won = False
        self.move_count = 0
        self.history = [self.state]
        self.animator.reset()
        self.manual_anim = None

    #hàm cần code lại
    def handle_manual_move(self, move_dir: Direction):
        """Xử lý di chuyển thủ công từ phím bấm với animation lăn."""
        if self.game_over or self.is_won:
            return
        self.animator.is_playing = False

        if self.manual_anim is not None and not self.manual_anim.is_finished:
            self.state = self.manual_anim.to_state
            self.manual_anim = None
            if self.board.is_goal_state(self.state):
                self.is_won = True
                return

        successors = self.board.get_successors(self.state)
        matched_state = None

        if not self.state.is_split:
            for act, next_st, cost in successors:
                if act.startswith(move_dir.value):
                    matched_state = next_st
                    break
        else:
            cube_idx = self.state.active_cube
            prefix = f"Cube{cube_idx + 1}_{move_dir.value}"
            for act, next_st, cost in successors:
                if act.startswith(prefix):
                    matched_state = next_st
                    break

        if matched_state is not None:
            self.manual_anim = MoveAnimation(self.state, matched_state, move_dir.value, duration=0.13)
        else:
            self.game_over = True


    def run_solver(self, algo_name: str):
        """Chạy thuật toán tìm kiếm và chuẩn bị lời giải."""
        self.restart_stage()
        self.active_algo = algo_name
        print(f"\n[SOLVER] Đang thực thi: {algo_name}...")

        if algo_name == "BFS":
            res = solve_bfs(self.board)
        elif algo_name == "DFS":
            res = solve_ids(self.board, max_limit=35)
        elif algo_name == "UCS":
            res = solve_ucs(self.board, use_weighted_cost=True)
        elif algo_name == "A*":
            res = solve_astar(self.board, use_weighted_cost=True)
        else:
            return

        self.search_result = res
        print(f"  -> {res.summary()}")

        if res.solved and len(res.states_path) > 1:
            self.animator.is_playing = True
            self.animator.current_step = 0

    def draw_header(self):
        """Vẽ thanh Header trên cùng: Capsule [ < LEVEL X / 10 > ], Tên màn, Pill Badge tư thế."""
        screen_w, screen_h = self.screen.get_size()

        # 1. Hộp capsule điều hướng Level
        pygame.draw.rect(self.screen, COLOR_HEADER_BG, self.rect_capsule, border_radius=18)
        pygame.draw.rect(self.screen, (30, 41, 59), self.rect_capsule, width=1, border_radius=18)

        self.btn_prev.draw(self.screen, self.font_bold)
        self.btn_next.draw(self.screen, self.font_bold)

        # Chữ LEVEL X / 10 ở giữa capsule
        txt_lvl = self.font_small.render("LEVEL ", True, COLOR_TEXT_DIM)
        cur_num = f"{self.current_stage_idx + 1:02d}" if (self.current_stage_idx + 1) >= 10 else f"{self.current_stage_idx + 1}"
        txt_num = self.font_bold.render(cur_num, True, COLOR_CYAN_GLOW)
        txt_total = self.font_small.render(f" / {len(self.level_files)}", True, COLOR_TEXT_DIM)

        mid_w = txt_lvl.get_width() + txt_num.get_width() + txt_total.get_width()
        cur_x = self.rect_capsule.centerx - mid_w // 2
        cy = self.rect_capsule.centery - txt_lvl.get_height() // 2

        self.screen.blit(txt_lvl, (cur_x, cy))
        cur_x += txt_lvl.get_width()
        self.screen.blit(txt_num, (cur_x, cy - 1))
        cur_x += txt_num.get_width()
        self.screen.blit(txt_total, (cur_x, cy))

        # 2. Tên màn chơi cạnh capsule
        lvl_name_text = f"Level {self.current_stage_idx + 1} — {self.board.name}"
        lbl_name = self.font_normal.render(lvl_name_text, True, COLOR_TEXT_MUTED)
        self.screen.blit(lbl_name, (self.rect_capsule.right + 20, self.rect_capsule.centery - lbl_name.get_height() // 2))

        # 3. Badge tư thế góc trên-phải (Pill badge)
        if not self.state.is_split:
            ori = self.state.orientation
            if ori == Orientation.STANDING:
                badge_text = "▲ Standing"
            elif ori == Orientation.HORIZONTAL:
                badge_text = "▬ Horizontal"
            else:
                badge_text = "❚ Vertical"
            badge_border = COLOR_CYAN_GLOW
            badge_bg = (12, 74, 110)
            badge_txt_col = (186, 230, 253)
        else:
            badge_text = f"◆ Split (Cube {self.state.active_cube + 1})"
            badge_border = (168, 85, 247)
            badge_bg = (88, 28, 135)
            badge_txt_col = (233, 213, 255)

        txt_badge = self.font_bold.render(badge_text, True, badge_txt_col)
        badge_w = txt_badge.get_width() + 24
        badge_rect = pygame.Rect(screen_w - 360, 18, badge_w, 32)
        pygame.draw.rect(self.screen, badge_bg, badge_rect, border_radius=16)
        pygame.draw.rect(self.screen, badge_border, badge_rect, width=1, border_radius=16)
        self.screen.blit(txt_badge, txt_badge.get_rect(center=badge_rect.center))

    #hàm cần code lại
    def draw_board(self):
        """Vẽ toàn bộ bàn cờ tự động căn giữa ở phần còn lại của màn hình."""
        screen_w, screen_h = self.screen.get_size()
        center_x = (screen_w - 360) / 2.0 - 20
        center_y = screen_h / 2.0 + 35

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                draw_iso_tile(
                    self.screen, r, c,
                    self.board.grid[r][c],
                    self.board,
                    self.state.bridge_states,
                    self.font_bold,
                    center_x, center_y
                )

        # Vẽ khối: ưu tiên diễn hoạt lăn 3D nếu đang có animation
        curr_anim = self.manual_anim or self.animator.active_animation
        if curr_anim is not None and not curr_anim.is_finished:
            draw_rolling_block(
                self.screen,
                curr_anim.from_state,
                curr_anim.to_state,
                curr_anim.move_dir,
                curr_anim.progress,
                self.board,
                center_x, center_y
            )
        else:
            draw_block(self.screen, self.state, self.board, center_x, center_y)

        # Hiển thị HUD thông báo tinh chỉnh khối realtime
        if self.hud_msg and time.time() < self.hud_msg_timer:
            msg_surf = self.font_bold.render(self.hud_msg, True, (56, 189, 248))
            pad_x, pad_y = 16, 8
            msg_w, msg_h = msg_surf.get_width() + pad_x * 2, msg_surf.get_height() + pad_y * 2
            msg_rect = pygame.Rect(center_x - msg_w // 2, screen_h - 55, msg_w, msg_h)
            pygame.draw.rect(self.screen, (15, 23, 42), msg_rect, border_radius=8)
            pygame.draw.rect(self.screen, (56, 189, 248), msg_rect, width=1, border_radius=8)
            self.screen.blit(msg_surf, msg_surf.get_rect(center=msg_rect.center))

    def draw_sidebar(self):
        """Vẽ thanh Sidebar bên phải với Solver Cards, SEARCH METRICS và Animation controls."""
        screen_w, screen_h = self.screen.get_size()
        panel_w = 340
        p_x = screen_w - panel_w - 20

        # Cập nhật trạng thái active của các nút Solver
        self.btn_bfs.is_active = (self.active_algo == "BFS")
        self.btn_dfs.is_active = (self.active_algo == "DFS")
        self.btn_ucs.is_active = (self.active_algo == "UCS")
        self.btn_astar.is_active = (self.active_algo == "A*")

        self.btn_bfs.draw(self.screen, self.font_card)
        self.btn_dfs.draw(self.screen, self.font_card)
        self.btn_ucs.draw(self.screen, self.font_card)
        self.btn_astar.draw(self.screen, self.font_card)

        # Tiêu đề | SEARCH METRICS
        stat_y = 265
        pygame.draw.line(self.screen, (56, 189, 248), (p_x, stat_y + 2), (p_x, stat_y + 16), 3)
        lbl_metrics = self.font_bold.render("  SEARCH METRICS", True, COLOR_TEXT_WHITE)
        self.screen.blit(lbl_metrics, (p_x + 4, stat_y))

        # Bảng số liệu chi tiết
        stat_y += 30
        metrics = [
            ("SEARCH TIME:", f"{self.search_result.search_time * 1000:.2f} ms" if self.search_result else "-- ms"),
            ("NODES EXPANDED:", f"{self.search_result.expanded_nodes}" if self.search_result else "--"),
            ("MEMORY USAGE (PEAK):", f"{self.search_result.peak_memory_kb:.1f} KB" if self.search_result else "-- KB"),
            ("SOLUTION LENGTH:", f"{self.search_result.solution_length} moves" if self.search_result else "-- moves"),
        ]

        for label, val in metrics:
            lbl_surf = self.font_normal.render(label, True, COLOR_TEXT_DIM)
            val_surf = self.font_bold.render(val, True, COLOR_TEXT_WHITE)
            self.screen.blit(lbl_surf, (p_x, stat_y))
            self.screen.blit(val_surf, (p_x + panel_w - val_surf.get_width(), stat_y))
            stat_y += 24

        # Cập nhật nút Show / Pause Animation
        if self.animator.is_playing:
            self.btn_show_anim.text = "❚❚  PAUSE ANIMATION"
            self.btn_show_anim.text_color = COLOR_GOLD
            self.btn_show_anim.border_color = COLOR_GOLD
        else:
            self.btn_show_anim.text = "▶  SHOW ANIMATION"
            self.btn_show_anim.text_color = (56, 189, 248)
            self.btn_show_anim.border_color = (56, 189, 248)

        self.btn_show_anim.draw(self.screen, self.font_bold)
        self.btn_step_prev.draw(self.screen, self.font_small)
        self.btn_step_next.draw(self.screen, self.font_small)
        self.btn_speed.draw(self.screen, self.font_small)
        self.btn_fs.draw(self.screen, self.font_small)
        self.btn_restart.draw(self.screen, self.font_small)

        # Hướng dẫn phím bấm
        guide_y = self.btn_restart.rect.bottom + 10
        guide_txt = self.font_small.render("Phím: WASD/Mũi tên | [ / ]: Chỉnh khối | F11: Toàn màn", True, COLOR_TEXT_DIM)
        self.screen.blit(guide_txt, (p_x, guide_y))

        # Banner trạng thái Thắng / Thua
        if self.is_won:
            b_rect = pygame.Rect(p_x, guide_y + 18, panel_w, 30)
            pygame.draw.rect(self.screen, (20, 83, 45), b_rect, border_radius=6)
            pygame.draw.rect(self.screen, (74, 222, 128), b_rect, width=1, border_radius=6)
            txt = self.font_bold.render("CHIẾN THẮNG! KHỐI ĐÃ VÀO ĐÍCH!", True, (74, 222, 128))
            self.screen.blit(txt, txt.get_rect(center=b_rect.center))
        elif self.game_over:
            b_rect = pygame.Rect(p_x, guide_y + 18, panel_w, 30)
            pygame.draw.rect(self.screen, (127, 29, 29), b_rect, border_radius=6)
            pygame.draw.rect(self.screen, (248, 113, 113), b_rect, width=1, border_radius=6)
            txt = self.font_bold.render("THẤT BẠI! KHỐI RƠI HOẶC VỠ SÀN!", True, (248, 113, 113))
            self.screen.blit(txt, txt.get_rect(center=b_rect.center))

    def draw_popup_result(self):
        """Vẽ pop-up thông báo Thắng / Thua nổi bật ở giữa màn hình game."""
        if not (self.is_won or self.game_over):
            return

        screen_w, screen_h = self.screen.get_size()
        center_x = (screen_w - 360) // 2
        center_y = screen_h // 2

        # 1. Lớp phủ mờ (dim backdrop) làm nổi bật pop-up
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((5, 10, 22, 160))
        self.screen.blit(overlay, (0, 0))

        # 2. Khung hộp thoại Pop-up
        popup_w = 440
        popup_h = 230
        popup_rect = pygame.Rect(center_x - popup_w // 2, center_y - popup_h // 2, popup_w, popup_h)

        if self.is_won:
            bg_color = (15, 23, 42)
            border_color = (34, 197, 94)      # Xanh lục Neon
            title_text = "CHIẾN THẮNG!"
            title_color = (74, 222, 128)
            desc_text = "Khối đã đứng thẳng vào ô đích an toàn!"
            info_text = f"Số bước di chuyển: {self.move_count} bước"
        else:
            bg_color = (24, 15, 22)
            border_color = (239, 68, 68)     # Đỏ Neon
            title_text = "THẤT BẠI!"
            title_color = (248, 113, 113)
            desc_text = "Khối đã rơi ra ngoài hoặc làm vỡ ô cam!"
            info_text = f"Đã thực hiện: {self.move_count} bước trước khi rơi"

        # Đổ bóng
        shadow_rect = popup_rect.copy()
        shadow_rect.y += 6
        pygame.draw.rect(self.screen, (0, 0, 0, 180), shadow_rect, border_radius=16)

        # Vẽ Card pop-up
        pygame.draw.rect(self.screen, bg_color, popup_rect, border_radius=16)
        pygame.draw.rect(self.screen, border_color, popup_rect, width=2, border_radius=16)

        # Tiêu đề
        lbl_title = self.font_popup_title.render(title_text, True, title_color)
        self.screen.blit(lbl_title, lbl_title.get_rect(center=(popup_rect.centerx, popup_rect.y + 40)))

        # Dòng miêu tả
        lbl_desc = self.font_popup_body.render(desc_text, True, COLOR_TEXT_WHITE)
        self.screen.blit(lbl_desc, lbl_desc.get_rect(center=(popup_rect.centerx, popup_rect.y + 82)))

        # Thông tin bước đi
        lbl_info = self.font_normal.render(info_text, True, COLOR_TEXT_MUTED)
        self.screen.blit(lbl_info, lbl_info.get_rect(center=(popup_rect.centerx, popup_rect.y + 112)))

        # Nút bấm trong pop-up
        btn_y = popup_rect.y + 152
        btn_w = 160
        btn_h = 40

        if self.is_won:
            self.btn_popup_restart.rect = pygame.Rect(popup_rect.centerx - btn_w - 10, btn_y, btn_w, btn_h)
            self.btn_popup_restart.text = "Chơi lại (R)"
            self.btn_popup_restart.bg_color = (23, 32, 51)
            self.btn_popup_restart.hover_color = (35, 48, 75)
            self.btn_popup_restart.text_color = COLOR_TEXT_WHITE
            self.btn_popup_restart.border_color = (71, 85, 105)

            self.btn_popup_next.rect = pygame.Rect(popup_rect.centerx + 10, btn_y, btn_w, btn_h)
            self.btn_popup_next.text = "Màn tiếp theo (N)"
            self.btn_popup_next.bg_color = (20, 83, 45)
            self.btn_popup_next.hover_color = (22, 101, 52)
            self.btn_popup_next.text_color = (220, 252, 231)
            self.btn_popup_next.border_color = (74, 222, 128)

            self.btn_popup_restart.draw(self.screen, self.font_bold)
            self.btn_popup_next.draw(self.screen, self.font_bold)
        else:
            self.btn_popup_restart.rect = pygame.Rect(popup_rect.centerx - btn_w // 2, btn_y, btn_w, btn_h)
            self.btn_popup_restart.text = "Thử lại ngay (R)"
            self.btn_popup_restart.bg_color = (69, 10, 10)
            self.btn_popup_restart.hover_color = (127, 29, 29)
            self.btn_popup_restart.text_color = (254, 202, 202)
            self.btn_popup_restart.border_color = (239, 68, 68)

            self.btn_popup_restart.draw(self.screen, self.font_bold)

    #hàm cần code lại
    def run(self):
        """Vòng lặp sự kiện chính của game."""

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    if not self.is_fullscreen:
                        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                        self._init_ui_elements()
                elif event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_F11, pygame.K_f]:
                        self.toggle_fullscreen()
                    elif (self.is_won or self.game_over) and event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        if self.is_won:
                            self.load_stage(self.current_stage_idx + 1)
                        else:
                            self.restart_stage()
                    elif event.key in [pygame.K_UP, pygame.K_w]:
                        self.handle_manual_move(Direction.UP)
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        self.handle_manual_move(Direction.DOWN)
                    elif event.key in [pygame.K_LEFT, pygame.K_a]:
                        self.handle_manual_move(Direction.LEFT)
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        self.handle_manual_move(Direction.RIGHT)
                    elif event.key == pygame.K_SPACE:
                        if self.state.is_split:
                            self.state = self.state.clone_with_active_cube(1 - self.state.active_cube)
                    elif event.key == pygame.K_r:
                        self.restart_stage()
                    elif event.key == pygame.K_n:
                        self.load_stage(self.current_stage_idx + 1)
                    elif event.key == pygame.K_p:
                        self.load_stage(self.current_stage_idx - 1)
                    elif event.key in [pygame.K_LEFTBRACKET, pygame.K_MINUS]:
                        # Giảm chiều cao khối nằm (-2px)
                        import gui.renderer as r_mod
                        r_mod.BLOCK_H_LYING = max(20, r_mod.BLOCK_H_LYING - 2)
                        r_mod.BLOCK_H = r_mod.BLOCK_H_LYING
                        self.show_hud_message(f"Chiều cao nằm: {r_mod.BLOCK_H_LYING}px | Đứng: {r_mod.BLOCK_H_STANDING}px")
                        print(f"[Đồ họa] BLOCK_H_LYING = {r_mod.BLOCK_H_LYING}px, BLOCK_H_STANDING = {r_mod.BLOCK_H_STANDING}px")
                    elif event.key in [pygame.K_RIGHTBRACKET, pygame.K_EQUALS, pygame.K_PLUS]:
                        # Tăng chiều cao khối nằm (+2px)
                        import gui.renderer as r_mod
                        r_mod.BLOCK_H_LYING = min(80, r_mod.BLOCK_H_LYING + 2)
                        r_mod.BLOCK_H = r_mod.BLOCK_H_LYING
                        self.show_hud_message(f"Chiều cao nằm: {r_mod.BLOCK_H_LYING}px | Đứng: {r_mod.BLOCK_H_STANDING}px")
                        print(f"[Đồ họa] BLOCK_H_LYING = {r_mod.BLOCK_H_LYING}px, BLOCK_H_STANDING = {r_mod.BLOCK_H_STANDING}px")
                    elif event.key == pygame.K_0:
                        # Khôi phục mặc định 48px / 96px
                        import gui.renderer as r_mod
                        r_mod.BLOCK_H_LYING = 48
                        r_mod.BLOCK_H_STANDING = 96
                        r_mod.BLOCK_H = 48
                        self.show_hud_message(f"Khôi phục mặc định: Nằm 48px | Đứng 96px")
                        print(f"[Đồ họa] Khôi phục mặc định BLOCK_H_LYING = 48px, BLOCK_H_STANDING = 96px")

                # Sự kiện nút trên Pop-up Thắng / Thua
                if self.is_won or self.game_over:
                    if self.btn_popup_restart.handle_event(event):
                        self.restart_stage()
                    elif self.is_won and self.btn_popup_next.handle_event(event):
                        self.load_stage(self.current_stage_idx + 1)

                # Nút điều hướng màn chơi
                if self.btn_prev.handle_event(event):
                    self.load_stage(self.current_stage_idx - 1)
                elif self.btn_next.handle_event(event):
                    self.load_stage(self.current_stage_idx + 1)

                # 4 Nút Solver Cards
                elif self.btn_bfs.handle_event(event):
                    self.run_solver("BFS")
                elif self.btn_dfs.handle_event(event):
                    self.run_solver("DFS")
                elif self.btn_ucs.handle_event(event):
                    self.run_solver("UCS")
                elif self.btn_astar.handle_event(event):
                    self.run_solver("A*")

                # Nút điều khiển Animation / Replay
                elif self.btn_show_anim.handle_event(event):
                    if self.search_result and self.search_result.solved:
                        self.animator.toggle_play()
                elif self.btn_step_prev.handle_event(event):
                    if self.search_result and self.search_result.solved:
                        self.manual_anim = None
                        step = self.animator.step_backward()
                        self.state = self.search_result.states_path[step]
                        self.move_count = step
                        self.is_won = self.board.is_goal_state(self.state)
                elif self.btn_step_next.handle_event(event):
                    if self.search_result and self.search_result.solved:
                        self.manual_anim = None
                        step = self.animator.step_forward(len(self.search_result.states_path))
                        self.state = self.search_result.states_path[step]
                        self.move_count = step
                        self.is_won = self.board.is_goal_state(self.state)
                elif self.btn_speed.handle_event(event):
                    spd = self.animator.cycle_speed()
                    self.btn_speed.text = f"Tốc độ: {spd}x"
                elif self.btn_fs.handle_event(event):
                    self.toggle_fullscreen()
                elif self.btn_restart.handle_event(event):
                    self.restart_stage()

            # Cập nhật hoạt ảnh di chuyển thủ công (nếu có)
            if self.manual_anim is not None:
                self.manual_anim.update()
                if self.manual_anim.is_finished:
                    self.state = self.manual_anim.to_state
                    self.move_count += 1
                    self.history.append(self.state)
                    if self.board.is_goal_state(self.state):
                        self.is_won = True
                    self.manual_anim = None

            # Tự động phát lại lời giải (Replay)
            if self.search_result and self.search_result.solved:
                actions_list = getattr(self.search_result, "actions", None) or getattr(self.search_result, "actions_path", None)
                next_st, anim = self.animator.update(self.search_result.states_path, actions_list)
                if next_st is not None:
                    self.state = next_st
                    self.move_count = self.animator.current_step
                    if self.board.is_goal_state(self.state):
                        self.is_won = True

            # Dựng hình
            self.screen.fill(COLOR_BG)
            self.draw_header()
            self.draw_board()
            self.draw_sidebar()
            self.draw_popup_result()

            pygame.display.flip()
            self.clock.tick(FPS)


        pygame.quit()


if __name__ == "__main__":
    app = BloxorzGUI()
    app.run()
