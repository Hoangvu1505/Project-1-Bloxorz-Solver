"""
Pygame graphical user interface for the Bloxorz Solver.
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import glob
import re
import time
from typing import Optional, List, Tuple, Dict
import pygame

from core.state import Direction, GameState, Orientation
from core.board import BloxorzBoard
from solvers import solve_bfs, solve_dfs, solve_ucs, solve_astar, SearchResult
from gui.renderer import (
    draw_iso_tile,
    draw_block,
    draw_rolling_block,
    draw_falling_block,
    COLOR_FLOOR_TOP,
    COLOR_FLOOR_BORDER,
    COLOR_GOAL_TOP,
    COLOR_GOAL_DIAMOND,
    COLOR_FRAGILE_TOP,
    COLOR_FRAGILE_MARK,
    COLOR_BRIDGE_OPEN_TOP,
    COLOR_BLOCK_LEFT,
    COLOR_BLOCK_TOP,
    COLOR_BLOCK_TOP_BEVEL,
)
from gui.animator import PlaybackAnimator, MoveAnimation, FallingAnimation
from core.transition import roll_solid_block, roll_split_cube

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
    """Card button with hover and active states."""
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
            border_col = (51, 65, 85)
            txt_col = (255, 255, 255)

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
    """Rounded action button."""
    def __init__(self, rect, text, bg_color=(28, 40, 65), hover_color=(38, 56, 92), text_color=(255, 255, 255), border_color=(51, 65, 85)):
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
    """Main Bloxorz application controller."""
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
        self.font_menu_title = self._get_font(54, bold=True)
        self.font_menu_subtitle = self._get_font(18, bold=False)
        self.font_menu_button = self._get_font(16, bold=True)
        self.font_menu_hint = self._get_font(12, bold=False)

        self.start_screen = True
        self.level_select_screen = False
        self.level_page = 0
        self.levels_per_page = 6
        self.settings_screen = False
        self.guide_screen = False
        self.guide_page = 0
        self.guide_page_count = 5
        self.game_modes = ["ALGORITHM TEST", "PLAYER"]
        self.game_mode_index = 0

        # Victory and game-over popup buttons
        self.btn_popup_restart = ActionButton(
            (0, 0, 160, 40), "Retry (R)",
            bg_color=(69, 10, 10), hover_color=(127, 29, 29),
            text_color=(254, 202, 202), border_color=(239, 68, 68)
        )
        self.btn_popup_next = ActionButton(
            (0, 0, 160, 40), "Next level (N)",
            bg_color=(20, 83, 45), hover_color=(22, 101, 52),
            text_color=(220, 252, 231), border_color=(74, 222, 128)
        )

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        guide_image_path = os.path.join(base_dir, "gui", "assets", "bloxorz_guide.png")
        self.guide_image = pygame.image.load(guide_image_path).convert_alpha()

        self.level_files = self._find_level_files(base_dir)
        if not self.level_files:
            self.level_files = self._find_level_files(base_dir, "stages")

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
        self.falling_anim: Optional[FallingAnimation] = None

        self.hud_msg = ""
        self.hud_msg_timer = 0.0
        self.goal_reveal_started_at = 0.0
        self.goal_reveal_duration = 1.8

        self.load_stage(self.current_stage_idx)
        self._init_ui_elements()
        self._init_start_screen()
        self._init_level_select_screen()
        self._init_settings_screen()
        self._init_guide_screen()

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

    @staticmethod
    def _find_level_files(base_dir: str, folder_name: str = "levels") -> list[str]:
        """Find all levels and sort them by the number in their filename."""
        pattern = os.path.join(base_dir, folder_name, "*", "stage_*.json")
        files = glob.glob(pattern)

        def level_number(filepath: str) -> tuple[float, str]:
            filename = os.path.basename(filepath)
            match = re.search(r"stage_(\d+)", filename, re.IGNORECASE)
            number = int(match.group(1)) if match else float("inf")
            return number, filepath.lower()

        return sorted(files, key=level_number)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        self._init_ui_elements()
        self._init_start_screen()
        self._init_level_select_screen()
        self._init_settings_screen()
        self._init_guide_screen()

    def _init_ui_elements(self):
        screen_w, screen_h = self.screen.get_size()

        self.rect_capsule = pygame.Rect(screen_w // 2 - 180, 16, 170, 36)
        self.btn_prev = ActionButton((self.rect_capsule.x + 6, self.rect_capsule.y + 4, 28, 28), "<", bg_color=(17, 24, 39), border_color=(30, 41, 59))
        self.btn_next = ActionButton((self.rect_capsule.right - 34, self.rect_capsule.y + 4, 28, 28), ">", bg_color=(17, 24, 39), border_color=(30, 41, 59))

        panel_w = 340
        p_x = screen_w - panel_w - 20
        y = 70

        card_h = 42
        self.btn_bfs = CardButton((p_x, y, panel_w, card_h), "BFS Solver")
        y += 48
        self.btn_dfs = CardButton((p_x, y, panel_w, card_h), "DFS Solver")
        y += 48
        self.btn_ucs = CardButton((p_x, y, panel_w, card_h), "UCS Solver")
        y += 48
        self.btn_astar = CardButton((p_x, y, panel_w, card_h), "A* Solver")

        y = 415
        self.btn_show_anim = ActionButton(
            (p_x, y, panel_w, 38),
            "SHOW ANIMATION",
            bg_color=(20, 35, 60),
            hover_color=(30, 55, 95),
            text_color=(56, 189, 248),
            border_color=(56, 189, 248)
        )

        y += 44
        half_w = (panel_w - 10) // 2
        self.btn_step_prev = ActionButton(
            (p_x, y, half_w, 30),
            "<< Previous step",
            bg_color=(28, 40, 65),
            hover_color=(38, 56, 92),
            text_color=(255, 255, 255),
            border_color=(51, 65, 85),
        )
        self.btn_step_next = ActionButton(
            (p_x + half_w + 10, y, half_w, 30),
            "Next step >>",
            bg_color=(28, 40, 65),
            hover_color=(38, 56, 92),
            text_color=(255, 255, 255),
            border_color=(51, 65, 85),
        )

        y += 36
        self.btn_speed = ActionButton(
            (p_x, y, half_w, 30),
            f"Speed: {self.animator.speed}x",
            bg_color=(28, 40, 65),
            hover_color=(38, 56, 92),
            text_color=(255, 255, 255),
            border_color=(51, 65, 85),
        )
        fs_lbl = "Windowed (F11)" if self.is_fullscreen else "Fullscreen (F11)"
        self.btn_fs = ActionButton(
            (p_x + half_w + 10, y, half_w, 30),
            fs_lbl,
            bg_color=(28, 40, 65),
            hover_color=(38, 56, 92),
            text_color=(255, 255, 255),
            border_color=(51, 65, 85),
        )

        y += 36
        self.btn_restart = ActionButton(
            (p_x, y, panel_w, 30),
            "Restart level (R)",
            bg_color=(55, 25, 35),
            hover_color=(80, 35, 50),
            text_color=(254, 226, 226),
            border_color=(220, 38, 38),
        )

        y += 36
        self.btn_main_menu = ActionButton(
            (p_x, y, half_w, 30),
            "MAIN MENU",
            bg_color=(28, 40, 65),
            hover_color=(38, 56, 92),
            text_color=(255, 255, 255),
            border_color=(71, 85, 105),
        )
        self.btn_exit_game = ActionButton(
            (p_x + half_w + 10, y, half_w, 30),
            "EXIT",
            bg_color=(55, 25, 35),
            hover_color=(80, 35, 50),
            text_color=(254, 226, 226),
            border_color=(220, 38, 38),
        )

    def _init_start_screen(self):
        """Initialize the start-screen buttons."""
        screen_w, screen_h = self.screen.get_size()
        button_w, button_h = 300, 48
        button_x = screen_w // 2 - button_w // 2
        button_y = screen_h // 2 - 20
        button_gap = 14

        self.menu_buttons = [
            ActionButton(
                (button_x, button_y, button_w, button_h),
                "PLAY NOW",
                bg_color=(14, 74, 110),
                hover_color=(18, 105, 150),
                text_color=(224, 242, 254),
                border_color=COLOR_CYAN_GLOW,
            ),
            ActionButton(
                (button_x, button_y + (button_h + button_gap), button_w, button_h),
                "SELECT LEVEL",
                bg_color=COLOR_CARD_BG,
                hover_color=COLOR_CARD_HOVER,
                text_color=COLOR_TEXT_WHITE,
                border_color=COLOR_CARD_BORDER,
            ),
            ActionButton(
                (button_x, button_y + 2 * (button_h + button_gap), button_w, button_h),
                "GUIDE",
                bg_color=COLOR_CARD_BG,
                hover_color=COLOR_CARD_HOVER,
                text_color=COLOR_TEXT_WHITE,
                border_color=COLOR_CARD_BORDER,
            ),
            ActionButton(
                (button_x, button_y + 3 * (button_h + button_gap), button_w, button_h),
                "SETTINGS",
                bg_color=COLOR_CARD_BG,
                hover_color=COLOR_CARD_HOVER,
                text_color=COLOR_TEXT_WHITE,
                border_color=COLOR_CARD_BORDER,
            ),
            ActionButton(
                (button_x, button_y + 4 * (button_h + button_gap), button_w, button_h),
                "EXIT",
                bg_color=(35, 25, 30),
                hover_color=(69, 35, 45),
                text_color=(252, 165, 165),
                border_color=(127, 29, 29),
            ),
        ]

    def _init_level_select_screen(self):
        """Initialize six level buttons in a three-column, two-row layout."""
        screen_w, screen_h = self.screen.get_size()
        gap_x, gap_y = 18, 18
        start_y = 158
        button_size = min(
            (screen_w - 80 - 2 * gap_x) // 3,
            (screen_h - start_y - 140 - gap_y) // 2,
        )
        button_size = max(120, button_size)
        button_w = button_h = button_size
        column_count, row_count = 3, 2
        total_w = button_w * column_count + gap_x * (column_count - 1)
        start_x = (screen_w - total_w) // 2
        self.level_button_font = self._get_font(
            max(12, min(16, button_size // 14)),
            bold=True,
        )

        self.level_buttons = []
        page_count = max(
            1,
            (len(self.level_files) + self.levels_per_page - 1)
            // self.levels_per_page,
        )
        self.level_page = min(self.level_page, page_count - 1)
        first_level = self.level_page * self.levels_per_page
        page_files = self.level_files[first_level:first_level + self.levels_per_page]

        for page_index, filepath in enumerate(page_files):
            try:
                board = BloxorzBoard.load_from_file(filepath)
                level_name = board.name
            except (OSError, KeyError, TypeError, ValueError):
                level_name = f"Level {first_level + page_index + 1}"

            level_name = self._wrap_level_name(
                level_name,
                self.level_button_font,
                button_w - 28,
            )
            column = page_index % column_count
            row = page_index // column_count
            self.level_buttons.append(
                ActionButton(
                    (
                        start_x + column * (button_w + gap_x),
                        start_y + row * (button_h + gap_y),
                        button_w,
                        button_h,
                    ),
                    level_name,
                    bg_color=COLOR_CARD_BG,
                    hover_color=COLOR_CARD_HOVER,
                    text_color=COLOR_TEXT_WHITE,
                    border_color=COLOR_CARD_BORDER,
                )
            )

        nav_y = start_y + row_count * button_h + (row_count - 1) * gap_y + 20
        self.btn_level_prev = ActionButton(
            (start_x, nav_y, 120, 38),
            "< PREVIOUS",
            bg_color=COLOR_CARD_BG,
            hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_TEXT_WHITE,
            border_color=COLOR_CARD_BORDER,
        )
        self.btn_level_next = ActionButton(
            (start_x + total_w - 120, nav_y, 120, 38),
            "NEXT >",
            bg_color=COLOR_CARD_BG,
            hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_TEXT_WHITE,
            border_color=COLOR_CARD_BORDER,
        )
        self.btn_level_back = ActionButton(
            (screen_w // 2 - 120, nav_y + 54, 240, 42),
            "BACK",
            bg_color=COLOR_CARD_BG,
            hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_TEXT_WHITE,
            border_color=COLOR_CARD_BORDER,
        )
        self.level_page_count = page_count

    @staticmethod
    def _wrap_level_name(name: str, font, max_width: int) -> str:
        """Wrap a level name into at most three lines for its square card."""
        words = name.split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and font.size(candidate)[0] > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return "\n".join(lines[:3])

    def _init_settings_screen(self):
        """Initialize the settings buttons."""
        screen_w, screen_h = self.screen.get_size()
        button_w, button_h = 360, 52
        button_x = screen_w // 2 - button_w // 2
        button_y = screen_h // 2 - 56

        fullscreen_text = (
            "WINDOWED"
            if self.is_fullscreen
            else "FULLSCREEN"
        )
        self.btn_settings_fullscreen = ActionButton(
            (button_x, button_y, button_w, button_h),
            fullscreen_text,
            bg_color=COLOR_CARD_BG,
            hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_TEXT_WHITE,
            border_color=COLOR_CARD_BORDER,
        )
        self.btn_settings_mode = ActionButton(
            (button_x, button_y + button_h + 16, button_w, button_h),
            f"MODE: {self.game_modes[self.game_mode_index]}",
            bg_color=COLOR_CARD_BG,
            hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_TEXT_WHITE,
            border_color=COLOR_CARD_BORDER,
        )
        self.btn_settings_back = ActionButton(
            (button_x, button_y + 2 * (button_h + 16), button_w, button_h),
            "BACK TO MAIN MENU",
            bg_color=COLOR_CARD_BG,
            hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_TEXT_WHITE,
            border_color=COLOR_CARD_BORDER,
        )

    def _init_guide_screen(self):
        """Initialize guide navigation buttons."""
        screen_w, screen_h = self.screen.get_size()
        self.btn_guide_back = ActionButton(
            (screen_w // 2 - 120, screen_h - 58, 240, 42),
            "BACK TO MAIN MENU",
            bg_color=COLOR_CARD_BG,
            hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_TEXT_WHITE,
            border_color=COLOR_CARD_BORDER,
        )
        self.btn_guide_prev = ActionButton(
            (40, screen_h - 58, 120, 42),
            "< PREVIOUS",
            bg_color=COLOR_CARD_BG,
            hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_TEXT_WHITE,
            border_color=COLOR_CARD_BORDER,
        )
        self.btn_guide_next = ActionButton(
            (screen_w - 160, screen_h - 58, 120, 42),
            "NEXT >",
            bg_color=COLOR_CARD_BG,
            hover_color=COLOR_CARD_HOVER,
            text_color=COLOR_TEXT_WHITE,
            border_color=COLOR_CARD_BORDER,
        )

    def draw_start_screen(self):
        """Draw the start screen."""
        screen_w, screen_h = self.screen.get_size()
        center_x = screen_w // 2

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((8, 13, 25, 125))
        self.screen.blit(overlay, (0, 0))

        # Geometric pattern inspired by the board and Bloxorz block.
        grid_color = (20, 46, 70)
        for offset in range(-screen_h, screen_w, 64):
            pygame.draw.line(
                self.screen,
                grid_color,
                (offset, screen_h),
                (offset + screen_h, 0),
                1,
            )
            pygame.draw.line(
                self.screen,
                grid_color,
                (offset, 0),
                (offset + screen_h, screen_h),
                1,
            )

        title = self.font_menu_title.render("BLOXORZ", True, COLOR_CYAN_GLOW)
        title_rect = title.get_rect(center=(center_x, 150))
        self.screen.blit(title, title_rect)

        subtitle = self.font_menu_subtitle.render(
            "SOLVER", True, COLOR_TEXT_WHITE
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(center_x, 195)))

        pygame.draw.line(
            self.screen,
            COLOR_CYAN_GLOW,
            (center_x - 94, 222),
            (center_x + 94, 222),
            2,
        )

        for button in self.menu_buttons:
            button.draw(self.screen, self.font_menu_button)

        hint = self.font_menu_hint.render(
            "Project 1 • Bloxorz Solver", True, COLOR_TEXT_DIM
        )
        self.screen.blit(hint, hint.get_rect(center=(center_x, screen_h - 32)))

    def draw_level_select_screen(self):
        """Draw the level-selection screen."""
        screen_w, screen_h = self.screen.get_size()
        center_x = screen_w // 2

        title = self.font_menu_title.render("SELECT LEVEL", True, COLOR_CYAN_GLOW)
        self.screen.blit(title, title.get_rect(center=(center_x, 82)))

        subtitle = self.font_menu_subtitle.render(
            f"Choose a level to begin  |  Page {self.level_page + 1}/{self.level_page_count}",
            True,
            COLOR_TEXT_DIM,
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(center_x, 124)))

        for button in self.level_buttons:
            self._draw_multiline_button(button, self.level_button_font)
        if self.level_page > 0:
            self.btn_level_prev.draw(self.screen, self.font_menu_button)
        if self.level_page < self.level_page_count - 1:
            self.btn_level_next.draw(self.screen, self.font_menu_button)
        self.btn_level_back.draw(self.screen, self.font_menu_button)

    def _draw_multiline_button(self, button: ActionButton, font) -> None:
        """Draw a button with a centered multiline level name."""
        col = button.hover_color if button.is_hovered else button.bg_color
        pygame.draw.rect(self.screen, col, button.rect, border_radius=8)
        pygame.draw.rect(
            self.screen,
            button.border_color,
            button.rect,
            width=1,
            border_radius=8,
        )
        lines = button.text.splitlines()
        line_height = font.get_linesize()
        first_y = button.rect.centery - (len(lines) * line_height) // 2
        for line_index, line in enumerate(lines):
            text_surface = font.render(line, True, button.text_color)
            text_rect = text_surface.get_rect(
                center=(button.rect.centerx, first_y + line_index * line_height)
            )
            self.screen.blit(text_surface, text_rect)

    def draw_settings_screen(self):
        """Draw the settings screen."""
        screen_w = self.screen.get_width()
        center_x = screen_w // 2

        title = self.font_menu_title.render("SETTINGS", True, COLOR_CYAN_GLOW)
        self.screen.blit(title, title.get_rect(center=(center_x, 180)))

        subtitle = self.font_menu_subtitle.render(
            "Customize display and game mode", True, COLOR_TEXT_DIM
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(center_x, 225)))

        self.btn_settings_fullscreen.draw(self.screen, self.font_menu_button)
        self.btn_settings_mode.draw(self.screen, self.font_menu_button)
        self.btn_settings_back.draw(self.screen, self.font_menu_button)

    def draw_guide_screen(self):
        """Draw the multi-page guide with visual illustrations."""
        screen_w, screen_h = self.screen.get_size()
        center_x = screen_w // 2

        title = self.font_menu_title.render("GUIDE", True, COLOR_CYAN_GLOW)
        self.screen.blit(title, title.get_rect(center=(center_x, 68)))

        subtitle = self.font_menu_subtitle.render(
            f"Page {self.guide_page + 1}/{self.guide_page_count}",
            True,
            COLOR_TEXT_DIM,
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(center_x, 112)))

        pages = [
            (
                "RULES AND CONTROLS",
                [
                    ("GOAL", "Move the block onto the goal while standing upright."),
                    ("MOVEMENT", "Use W A S D or the arrow keys to roll the block."),
                    ("ORIENTATION", "The block can stand upright or lie horizontally or vertically."),
                    ("RULE", "If the block falls off the platform or onto an invalid tile, you lose."),
                ],
            ),
            (
                "GOAL TILE",
                [
                    ("FUNCTION", "The yellow tile marks the destination for the block."),
                    ("MECHANIC", "The block must stand upright and cover the goal to win."),
                ],
            ),
            (
                "FRAGILE TILE",
                [
                    ("FUNCTION", "The orange tile is weak and can break."),
                    ("MECHANIC", "Do not stand upright on it; roll across it using the block's long side."),
                ],
            ),
            (
                "BRIDGE",
                [
                    ("FUNCTION", "Bridges are blue tiles that connect paths or extend the platform."),
                    ("MECHANIC", "A closed bridge creates a gap; linked switches open or close it."),
                ],
            ),
            (
                "SWITCHES",
                [
                    ("SOFT / S", "Activates when the block lies on the switch, usually toggling a bridge."),
                    ("HEAVY / H", "Activates only when the block stands upright on the switch."),
                    ("SPLIT / P", "Splits the block into two cubes; press Space to switch the active cube."),
                ],
            ),
        ]
        page_title, sections = pages[self.guide_page]
        page_heading = self.font_bold.render(page_title, True, COLOR_CYAN_GLOW)
        self.screen.blit(page_heading, page_heading.get_rect(center=(center_x, 145)))

        if self.guide_page == 0:
            image_rect = pygame.Rect(42, 175, min(470, screen_w // 2 - 70), 360)
            self._draw_guide_image(image_rect)
            card_w = min(500, screen_w - image_rect.right - 50)
            card_x = image_rect.right + 20
            card_h = 62
            y = 205
        else:
            self._draw_special_tile_illustration(
                self.guide_page,
                center_x - 250,
                300,
            )
            card_w = min(500, screen_w - 390)
            card_x = center_x - 20
            card_h = 82
            y = 205

        for heading, description in sections:
            card_rect = pygame.Rect(card_x, y, card_w, card_h)
            pygame.draw.rect(self.screen, COLOR_CARD_BG, card_rect, border_radius=8)
            pygame.draw.rect(
                self.screen, COLOR_CARD_BORDER, card_rect, width=1, border_radius=8
            )
            heading_surface = self.font_bold.render(heading, True, COLOR_CYAN_GLOW)
            self.screen.blit(heading_surface, (card_x + 18, y + 14))
            description_surface = self.font_small.render(
                description, True, COLOR_TEXT_WHITE
            )
            self.screen.blit(
                description_surface,
                (card_x + 18, y + (48 if card_h > 70 else 36)),
            )
            y += card_h + 8

        if self.guide_page > 0:
            self.btn_guide_prev.draw(self.screen, self.font_menu_button)
        if self.guide_page < self.guide_page_count - 1:
            self.btn_guide_next.draw(self.screen, self.font_menu_button)
        self.btn_guide_back.draw(self.screen, self.font_menu_button)

    def _draw_guide_image(self, target_rect: pygame.Rect) -> None:
        """Draw the board and Bloxorz block illustration on the first page."""
        image = pygame.transform.smoothscale(self.guide_image, target_rect.size)
        self.screen.blit(image, target_rect)

    def _draw_special_tile_illustration(
        self,
        page: int,
        center_x: int,
        center_y: int,
    ) -> None:
        """Draw the special-tile illustration for the current page."""
        tile_w, tile_h = 88, 44
        top = [(center_x, center_y - tile_h), (center_x + tile_w, center_y),
               (center_x, center_y + tile_h), (center_x - tile_w, center_y)]
        if page == 1:
            color = COLOR_GOAL_TOP
        elif page == 2:
            color = COLOR_FRAGILE_TOP
        elif page == 3:
            color = COLOR_BRIDGE_OPEN_TOP
        else:
            color = COLOR_FLOOR_TOP
        pygame.draw.polygon(self.screen, color, top)
        pygame.draw.polygon(self.screen, COLOR_FLOOR_BORDER, top, width=2)

        if page == 1:
            pygame.draw.polygon(
                self.screen,
                COLOR_GOAL_DIAMOND,
                [(center_x, center_y - 18), (center_x + 26, center_y),
                 (center_x, center_y + 18), (center_x - 26, center_y)],
            )
            label = "GOAL"
        elif page == 2:
            pygame.draw.line(self.screen, COLOR_FRAGILE_MARK,
                             (center_x - 32, center_y - 15),
                             (center_x + 34, center_y + 15), 5)
            pygame.draw.line(self.screen, COLOR_FRAGILE_MARK,
                             (center_x + 20, center_y - 25),
                             (center_x - 22, center_y + 24), 5)
            label = "FRAGILE"
        elif page == 3:
            label = "BRIDGE"
        else:
            for offset, text, color in [
                (-42, "S", (251, 191, 36)),
                (0, "H", (239, 68, 68)),
                (42, "P", (168, 85, 247)),
            ]:
                pygame.draw.circle(
                    self.screen, color,
                    (center_x + offset, center_y), 15,
                )
                glyph = self.font_bold.render(text, True, COLOR_TEXT_WHITE)
                self.screen.blit(glyph, glyph.get_rect(
                    center=(center_x + offset, center_y)
                ))
            label = "SWITCHES"
        label_surface = self.font_menu_subtitle.render(label, True, COLOR_TEXT_WHITE)
        self.screen.blit(
            label_surface,
            label_surface.get_rect(center=(center_x, center_y + 90)),
        )

    def load_stage(self, idx: int):
        """Load a level by index."""
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
        self.falling_anim = None
        self.goal_reveal_started_at = time.time()

    def restart_stage(self):
        """Restart the current level."""
        self.state = self.board.get_initial_state()
        self.game_over = False
        self.is_won = False
        self.move_count = 0
        self.history = [self.state]
        self.animator.reset()
        self.manual_anim = None
        self.falling_anim = None
        self.goal_reveal_started_at = time.time()

    def return_to_main_menu(self):
        """Return to the main menu from a level."""
        self.start_screen = True
        self.level_select_screen = False
        self.animator.reset()
        self.manual_anim = None
        self.falling_anim = None

    def handle_manual_move(self, move_dir: Direction):
        """Handle a keyboard move with rolling animation."""
        if self.game_over or self.is_won or self.falling_anim is not None:
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
            failed_state = self._get_failed_move_state(move_dir)
            self.falling_anim = FallingAnimation(
                self.state,
                failed_state,
                move_dir.value,
            )

    def _get_failed_move_state(self, move_dir: Direction) -> GameState:
        """Create the visual state after rolling off the board."""
        if not self.state.is_split:
            orientation, pos = roll_solid_block(
                self.state.orientation,
                self.state.pos,
                move_dir,
            )
            return GameState(
                is_split=False,
                orientation=orientation,
                pos=pos,
                cubes=None,
                active_cube=0,
                bridge_states=self.state.bridge_states,
            )

        cube_index = self.state.active_cube
        cubes = list(self.state.cubes)
        cubes[cube_index] = roll_split_cube(cubes[cube_index], move_dir)
        return GameState(
            is_split=True,
            orientation=None,
            pos=None,
            cubes=tuple(cubes),
            active_cube=cube_index,
            bridge_states=self.state.bridge_states,
        )


    def run_solver(self, algo_name: str):
        """Run a search algorithm and prepare its solution."""
        self.restart_stage()
        self.active_algo = algo_name
        print(f"\n[SOLVER] Running: {algo_name}...")

        if algo_name == "BFS":
            res = solve_bfs(self.board)
        elif algo_name == "DFS":
            res = solve_dfs(self.board)
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
        """Draw the top header with level navigation and level name."""
        screen_w, screen_h = self.screen.get_size()

        # 1. Level navigation capsule
        pygame.draw.rect(self.screen, COLOR_HEADER_BG, self.rect_capsule, border_radius=18)
        pygame.draw.rect(self.screen, (30, 41, 59), self.rect_capsule, width=1, border_radius=18)

        self.btn_prev.draw(self.screen, self.font_bold)
        self.btn_next.draw(self.screen, self.font_bold)

        # LEVEL X / total in the center of the capsule
        txt_lvl = self.font_small.render("LEVEL ", True, (160, 185, 215))
        cur_num = f"{self.current_stage_idx + 1:02d}" if (self.current_stage_idx + 1) >= 10 else f"{self.current_stage_idx + 1}"
        txt_num = self.font_bold.render(cur_num, True, COLOR_CYAN_GLOW)
        txt_total = self.font_small.render(f" / {len(self.level_files)}", True, (160, 185, 215))

        mid_w = txt_lvl.get_width() + txt_num.get_width() + txt_total.get_width()
        cur_x = self.rect_capsule.centerx - mid_w // 2
        cy = self.rect_capsule.centery - txt_lvl.get_height() // 2

        self.screen.blit(txt_lvl, (cur_x, cy))
        cur_x += txt_lvl.get_width()
        self.screen.blit(txt_num, (cur_x, cy - 1))
        cur_x += txt_num.get_width()
        self.screen.blit(txt_total, (cur_x, cy))

        # 2. Level name beside the capsule
        lvl_name_text = f"Level {self.current_stage_idx + 1} — {self.board.name}"
        lbl_name = self.font_normal.render(lvl_name_text, True, COLOR_TEXT_MUTED)
        self.screen.blit(lbl_name, (self.rect_capsule.right + 20, self.rect_capsule.centery - lbl_name.get_height() // 2))

    def draw_board(self):
        """Draw the board centered in the available game area."""
        screen_w, screen_h = self.screen.get_size()
        center_x = (screen_w - 360) / 2.0+30
        center_y = screen_h / 2.0 + 35
        reveal_elapsed = time.time() - self.goal_reveal_started_at
        show_goal = (
            reveal_elapsed >= self.goal_reveal_duration
            or int(reveal_elapsed / 0.18) % 2 == 0
        )

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                draw_iso_tile(
                    self.screen, r, c,
                    self.board.grid[r][c],
                    self.board,
                    self.state.bridge_states,
                    self.font_bold,
                    center_x,
                    center_y,
                    show_goal,
                )

        # Draw the block, prioritizing the 3D rolling animation when active.
        curr_anim = self.manual_anim or self.animator.active_animation
        if self.falling_anim is not None and not self.falling_anim.is_finished:
            draw_falling_block(
                self.screen,
                self.falling_anim.from_state,
                self.falling_anim.to_state,
                self.falling_anim.move_dir,
                self.board,
                center_x,
                center_y,
                self.falling_anim.roll_progress,
                self.falling_anim.fall_progress,
            )
        elif curr_anim is not None and not curr_anim.is_finished:
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

        # Display real-time block-tuning messages.
        if self.hud_msg and time.time() < self.hud_msg_timer:
            msg_surf = self.font_bold.render(self.hud_msg, True, (56, 189, 248))
            pad_x, pad_y = 16, 8
            msg_w, msg_h = msg_surf.get_width() + pad_x * 2, msg_surf.get_height() + pad_y * 2
            msg_rect = pygame.Rect(center_x - msg_w // 2, screen_h - 55, msg_w, msg_h)
            pygame.draw.rect(self.screen, (15, 23, 42), msg_rect, border_radius=8)
            pygame.draw.rect(self.screen, (56, 189, 248), msg_rect, width=1, border_radius=8)
            self.screen.blit(msg_surf, msg_surf.get_rect(center=msg_rect.center))

    def draw_sidebar(self):
        """Draw the sidebar with orientation, solver, metrics, and animation controls."""
        screen_w, screen_h = self.screen.get_size()
        panel_w = 340
        p_x = screen_w - panel_w - 20

        # 1. Orientation badge in the upper-right corner
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
            badge_txt_col = (224, 242, 254)
        else:
            badge_text = f"◆ Split (Cube {self.state.active_cube + 1})"
            badge_border = (168, 85, 247)
            badge_bg = (88, 28, 135)
            badge_txt_col = (243, 232, 255)

        txt_badge = self.font_bold.render(badge_text, True, badge_txt_col)
        badge_w = txt_badge.get_width() + 24
        badge_rect = pygame.Rect(p_x, 18, badge_w, 32)
        pygame.draw.rect(self.screen, badge_bg, badge_rect, border_radius=16)
        pygame.draw.rect(self.screen, badge_border, badge_rect, width=1, border_radius=16)
        self.screen.blit(txt_badge, txt_badge.get_rect(center=badge_rect.center))

        if self.game_mode_index == 0:
            # Update solver button active states.
            self.btn_bfs.is_active = (self.active_algo == "BFS")
            self.btn_dfs.is_active = (self.active_algo == "DFS")
            self.btn_ucs.is_active = (self.active_algo == "UCS")
            self.btn_astar.is_active = (self.active_algo == "A*")

            self.btn_bfs.draw(self.screen, self.font_card)
            self.btn_dfs.draw(self.screen, self.font_card)
            self.btn_ucs.draw(self.screen, self.font_card)
            self.btn_astar.draw(self.screen, self.font_card)

            # Title | SEARCH METRICS
            stat_y = 265
            pygame.draw.line(self.screen, (56, 189, 248), (p_x, stat_y + 2), (p_x, stat_y + 16), 3)
            lbl_metrics = self.font_bold.render("  SEARCH METRICS", True, (255, 255, 255))
            self.screen.blit(lbl_metrics, (p_x + 4, stat_y))

            # Detailed metrics
            stat_y += 30
            metrics = [
                ("SEARCH TIME:", f"{self.search_result.search_time * 1000:.2f} ms" if self.search_result else "-- ms"),
                ("NODES EXPANDED:", f"{self.search_result.expanded_nodes}" if self.search_result else "--"),
                ("MEMORY USAGE (PEAK):", f"{self.search_result.peak_memory_kb:.1f} KB" if self.search_result else "-- KB"),
                ("SOLUTION LENGTH:", f"{self.search_result.solution_length} moves" if self.search_result else "-- moves"),
            ]

            for label, val in metrics:
                lbl_surf = self.font_bold.render(label, True, (203, 213, 225))
                val_surf = self.font_bold.render(val, True, (255, 255, 255))
                self.screen.blit(lbl_surf, (p_x, stat_y))
                self.screen.blit(val_surf, (p_x + panel_w - val_surf.get_width(), stat_y))
                stat_y += 24

            # Update the show/pause animation button.
            if self.animator.is_playing:
                self.btn_show_anim.text = "PAUSE ANIMATION"
                self.btn_show_anim.text_color = COLOR_GOLD
                self.btn_show_anim.border_color = COLOR_GOLD
            else:
                self.btn_show_anim.text = "SHOW ANIMATION"
                self.btn_show_anim.text_color = (56, 189, 248)
                self.btn_show_anim.border_color = (56, 189, 248)

            self.btn_show_anim.draw(self.screen, self.font_bold)
            self.btn_step_prev.draw(self.screen, self.font_bold)
            self.btn_step_next.draw(self.screen, self.font_bold)
            self.btn_speed.draw(self.screen, self.font_bold)
        self.btn_fs.draw(self.screen, self.font_bold)
        self.btn_restart.draw(self.screen, self.font_bold)
        self.btn_main_menu.draw(self.screen, self.font_bold)
        self.btn_exit_game.draw(self.screen, self.font_bold)

        # Keyboard help
        guide_y = self.btn_exit_game.rect.bottom + 10
        guide_txt = self.font_normal.render("Keys: WASD/Arrows | [ / ]: Adjust block | F11: Fullscreen", True, (160, 185, 215))
        self.screen.blit(guide_txt, (p_x, guide_y))

        # Victory / game-over status banner
        if self.is_won:
            b_rect = pygame.Rect(p_x, guide_y + 22, panel_w, 32)
            pygame.draw.rect(self.screen, (20, 83, 45), b_rect, border_radius=6)
            pygame.draw.rect(self.screen, (74, 222, 128), b_rect, width=1, border_radius=6)
            txt = self.font_bold.render("VICTORY! BLOCK REACHED THE GOAL!", True, (220, 252, 231))
            self.screen.blit(txt, txt.get_rect(center=b_rect.center))
        elif self.game_over:
            b_rect = pygame.Rect(p_x, guide_y + 22, panel_w, 32)
            pygame.draw.rect(self.screen, (127, 29, 29), b_rect, border_radius=6)
            pygame.draw.rect(self.screen, (248, 113, 113), b_rect, width=1, border_radius=6)
            txt = self.font_bold.render("GAME OVER! THE BLOCK FELL OR BROKE THE FLOOR!", True, (254, 226, 226))
            self.screen.blit(txt, txt.get_rect(center=b_rect.center))

    def draw_popup_result(self):
        """Draw a prominent victory or game-over popup."""
        if not (self.is_won or self.game_over):
            return

        screen_w, screen_h = self.screen.get_size()
        center_x = (screen_w - 360) // 2
        center_y = screen_h // 2

        # 1. Dim the board area without covering the sidebar.
        board_area_w = max(0, screen_w - 360)
        overlay = pygame.Surface((board_area_w, screen_h), pygame.SRCALPHA)
        overlay.fill((5, 10, 22, 160))
        self.screen.blit(overlay, (0, 0))

        # 2. Popup frame
        popup_w = 440
        popup_h = 230
        popup_rect = pygame.Rect(center_x - popup_w // 2, center_y - popup_h // 2, popup_w, popup_h)

        if self.is_won:
            bg_color = (15, 23, 42)
            border_color = (34, 197, 94)
            title_text = "VICTORY!"
            title_color = (74, 222, 128)
            desc_text = "The block is upright on the goal!"
            info_text = f"Moves: {self.move_count}"
        else:
            bg_color = (24, 15, 22)
            border_color = (239, 68, 68)
            title_text = "GAME OVER!"
            title_color = (248, 113, 113)
            desc_text = "The block fell off the platform or broke a fragile tile!"
            info_text = f"Moves before falling: {self.move_count}"

        # Shadow
        shadow_rect = popup_rect.copy()
        shadow_rect.y += 6
        pygame.draw.rect(self.screen, (0, 0, 0, 180), shadow_rect, border_radius=16)

        # Popup card
        pygame.draw.rect(self.screen, bg_color, popup_rect, border_radius=16)
        pygame.draw.rect(self.screen, border_color, popup_rect, width=2, border_radius=16)

        # Title
        lbl_title = self.font_popup_title.render(title_text, True, title_color)
        self.screen.blit(lbl_title, lbl_title.get_rect(center=(popup_rect.centerx, popup_rect.y + 40)))

        # Description
        lbl_desc = self.font_popup_body.render(desc_text, True, COLOR_TEXT_WHITE)
        self.screen.blit(lbl_desc, lbl_desc.get_rect(center=(popup_rect.centerx, popup_rect.y + 82)))

        # Move information
        lbl_info = self.font_normal.render(info_text, True, COLOR_TEXT_MUTED)
        self.screen.blit(lbl_info, lbl_info.get_rect(center=(popup_rect.centerx, popup_rect.y + 112)))

        # Popup buttons
        btn_y = popup_rect.y + 152
        btn_w = 160
        btn_h = 40

        if self.is_won:
            self.btn_popup_restart.rect = pygame.Rect(popup_rect.centerx - btn_w - 10, btn_y, btn_w, btn_h)
            self.btn_popup_restart.text = "Restart (R)"
            self.btn_popup_restart.bg_color = (23, 32, 51)
            self.btn_popup_restart.hover_color = (35, 48, 75)
            self.btn_popup_restart.text_color = COLOR_TEXT_WHITE
            self.btn_popup_restart.border_color = (71, 85, 105)

            self.btn_popup_next.rect = pygame.Rect(popup_rect.centerx + 10, btn_y, btn_w, btn_h)
            self.btn_popup_next.text = "Next level (N)"
            self.btn_popup_next.bg_color = (20, 83, 45)
            self.btn_popup_next.hover_color = (22, 101, 52)
            self.btn_popup_next.text_color = (220, 252, 231)
            self.btn_popup_next.border_color = (74, 222, 128)

            self.btn_popup_restart.draw(self.screen, self.font_bold)
            self.btn_popup_next.draw(self.screen, self.font_bold)
        else:
            self.btn_popup_restart.rect = pygame.Rect(popup_rect.centerx - btn_w // 2, btn_y, btn_w, btn_h)
            self.btn_popup_restart.text = "Retry (R)"
            self.btn_popup_restart.bg_color = (69, 10, 10)
            self.btn_popup_restart.hover_color = (127, 29, 29)
            self.btn_popup_restart.text_color = (254, 202, 202)
            self.btn_popup_restart.border_color = (239, 68, 68)

            self.btn_popup_restart.draw(self.screen, self.font_bold)

    def run(self):
        """Run the main game event loop."""

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    if not self.is_fullscreen:
                        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                        self._init_ui_elements()
                        self._init_start_screen()
                        self._init_level_select_screen()
                        self._init_settings_screen()
                elif self.start_screen:
                    for button_index, button in enumerate(self.menu_buttons):
                        if button.handle_event(event):
                            if button_index == 0:
                                self.load_stage(0)
                                self.start_screen = False
                            elif button_index == 1:
                                self.start_screen = False
                                self.level_select_screen = True
                            elif button_index == 2:
                                self.start_screen = False
                                self.guide_screen = True
                            elif button_index == 3:
                                self.start_screen = False
                                self.settings_screen = True
                            elif button_index == 4:
                                running = False
                            break
                elif self.level_select_screen:
                    if self.btn_level_back.handle_event(event):
                        self.level_select_screen = False
                        self.start_screen = True
                    elif self.level_page > 0 and self.btn_level_prev.handle_event(event):
                        if self.level_page > 0:
                            self.level_page -= 1
                            self._init_level_select_screen()
                    elif self.level_page < self.level_page_count - 1 and self.btn_level_next.handle_event(event):
                        if self.level_page < self.level_page_count - 1:
                            self.level_page += 1
                            self._init_level_select_screen()
                    else:
                        for page_index, button in enumerate(self.level_buttons):
                            if button.handle_event(event):
                                level_index = (
                                    self.level_page * self.levels_per_page
                                    + page_index
                                )
                                self.load_stage(level_index)
                                self.level_select_screen = False
                                break
                elif self.guide_screen:
                    if self.guide_page > 0 and self.btn_guide_prev.handle_event(event):
                        self.guide_page = max(0, self.guide_page - 1)
                    elif self.guide_page < self.guide_page_count - 1 and self.btn_guide_next.handle_event(event):
                        self.guide_page = min(
                            self.guide_page_count - 1,
                            self.guide_page + 1,
                        )
                    elif self.btn_guide_back.handle_event(event):
                        self.guide_screen = False
                        self.start_screen = True
                elif self.settings_screen:
                    if self.btn_settings_fullscreen.handle_event(event):
                        self.toggle_fullscreen()
                    elif self.btn_settings_mode.handle_event(event):
                        self.game_mode_index = (
                            (self.game_mode_index + 1)
                            % len(self.game_modes)
                        )
                        self.btn_settings_mode.text = (
                            f"MODE: {self.game_modes[self.game_mode_index]}"
                        )
                    elif self.btn_settings_back.handle_event(event):
                        self.settings_screen = False
                        self.start_screen = True
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
                        # Decrease lying-block height (-2px).
                        import gui.renderer as r_mod
                        r_mod.BLOCK_H_LYING = max(20, r_mod.BLOCK_H_LYING - 2)
                        r_mod.BLOCK_H = r_mod.BLOCK_H_LYING
                        self.show_hud_message(f"Lying height: {r_mod.BLOCK_H_LYING}px | Standing: {r_mod.BLOCK_H_STANDING}px")
                        print(f"[Graphics] BLOCK_H_LYING = {r_mod.BLOCK_H_LYING}px, BLOCK_H_STANDING = {r_mod.BLOCK_H_STANDING}px")
                    elif event.key in [pygame.K_RIGHTBRACKET, pygame.K_EQUALS, pygame.K_PLUS]:
                        # Increase lying-block height (+2px).
                        import gui.renderer as r_mod
                        r_mod.BLOCK_H_LYING = min(80, r_mod.BLOCK_H_LYING + 2)
                        r_mod.BLOCK_H = r_mod.BLOCK_H_LYING
                        self.show_hud_message(f"Lying height: {r_mod.BLOCK_H_LYING}px | Standing: {r_mod.BLOCK_H_STANDING}px")
                        print(f"[Graphics] BLOCK_H_LYING = {r_mod.BLOCK_H_LYING}px, BLOCK_H_STANDING = {r_mod.BLOCK_H_STANDING}px")
                    elif event.key == pygame.K_0:
                        # Restore defaults: 48px / 96px.
                        import gui.renderer as r_mod
                        r_mod.BLOCK_H_LYING = 48
                        r_mod.BLOCK_H_STANDING = 96
                        r_mod.BLOCK_H = 48
                        self.show_hud_message("Defaults restored: Lying 48px | Standing 96px")
                        print("[Graphics] Defaults restored: BLOCK_H_LYING = 48px, BLOCK_H_STANDING = 96px")

                # Victory and game-over popup button events
                if self.is_won or self.game_over:
                    if self.btn_popup_restart.handle_event(event):
                        self.restart_stage()
                    elif self.is_won and self.btn_popup_next.handle_event(event):
                        self.load_stage(self.current_stage_idx + 1)

                # Level navigation buttons
                if self.btn_prev.handle_event(event):
                    self.load_stage(self.current_stage_idx - 1)
                elif self.btn_next.handle_event(event):
                    self.load_stage(self.current_stage_idx + 1)

                # Solver buttons are available only in algorithm-test mode.
                if self.game_mode_index == 0 and self.btn_bfs.handle_event(event):
                    self.run_solver("BFS")
                elif self.game_mode_index == 0 and self.btn_dfs.handle_event(event):
                    self.run_solver("DFS")
                elif self.game_mode_index == 0 and self.btn_ucs.handle_event(event):
                    self.run_solver("UCS")
                elif self.game_mode_index == 0 and self.btn_astar.handle_event(event):
                    self.run_solver("A*")

                # Animation and replay controls
                elif self.game_mode_index == 0 and self.btn_show_anim.handle_event(event):
                    if self.search_result and self.search_result.solved:
                        self.animator.toggle_play()
                elif self.game_mode_index == 0 and self.btn_step_prev.handle_event(event):
                    if self.search_result and self.search_result.solved:
                        self.manual_anim = None
                        step = self.animator.step_backward()
                        self.state = self.search_result.states_path[step]
                        self.move_count = step
                        self.is_won = self.board.is_goal_state(self.state)
                elif self.game_mode_index == 0 and self.btn_step_next.handle_event(event):
                    if self.search_result and self.search_result.solved:
                        self.manual_anim = None
                        step = self.animator.step_forward(len(self.search_result.states_path))
                        self.state = self.search_result.states_path[step]
                        self.move_count = step
                        self.is_won = self.board.is_goal_state(self.state)
                elif self.game_mode_index == 0 and self.btn_speed.handle_event(event):
                    spd = self.animator.cycle_speed()
                    self.btn_speed.text = f"Speed: {spd}x"
                elif self.btn_fs.handle_event(event):
                    self.toggle_fullscreen()
                elif self.btn_restart.handle_event(event):
                    self.restart_stage()
                elif self.btn_main_menu.handle_event(event):
                    self.return_to_main_menu()
                elif self.btn_exit_game.handle_event(event):
                    running = False

            if self.start_screen:
                self.screen.fill(COLOR_BG)
                self.draw_start_screen()
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            if self.level_select_screen:
                self.screen.fill(COLOR_BG)
                self.draw_level_select_screen()
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            if self.settings_screen:
                self.screen.fill(COLOR_BG)
                self.draw_settings_screen()
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            if self.guide_screen:
                self.screen.fill(COLOR_BG)
                self.draw_guide_screen()
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            # Update manual movement animation, if any.
            if self.manual_anim is not None:
                self.manual_anim.update()
                if self.manual_anim.is_finished:
                    self.state = self.manual_anim.to_state
                    self.move_count += 1
                    self.history.append(self.state)
                    if self.board.is_goal_state(self.state):
                        self.is_won = True
                    self.manual_anim = None

            if self.falling_anim is not None:
                self.falling_anim.update()
                if self.falling_anim.is_finished:
                    self.falling_anim = None
                    self.game_over = True

            # Automatically replay the solution.
            if self.game_mode_index == 0 and self.search_result and self.search_result.solved:
                actions_list = getattr(self.search_result, "actions", None) or getattr(self.search_result, "actions_path", None)
                next_st, anim = self.animator.update(self.search_result.states_path, actions_list)
                if next_st is not None:
                    self.state = next_st
                    self.move_count = self.animator.current_step
                    if self.board.is_goal_state(self.state):
                        self.is_won = True

            # Render the current frame.
            self.screen.fill(COLOR_BG)
            self.draw_header()
            self.draw_board()
            self.draw_popup_result()
            self.draw_sidebar()

            pygame.display.flip()
            self.clock.tick(FPS)


        pygame.quit()


if __name__ == "__main__":
    app = BloxorzGUI()
    app.run()
