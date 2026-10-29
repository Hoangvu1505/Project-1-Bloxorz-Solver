"""
Bộ dựng hình đồ hoạ Isometric 2.5D cho Bloxorz.
"""

import math
from typing import Tuple, List, Optional
import pygame
from core.state import Orientation, GameState
from core.special_tiles import TileType, SwitchType

# Thông số kích thước khối và sàn
TILE_W = 40
TILE_H = 24
TILE_DEPTH = 14

BLOCK_H_LYING = 40 #nằm 
BLOCK_H_STANDING = 80 #đứng
BLOCK_H = BLOCK_H_LYING

# Bảng màu sàn - Xám sáng (Light Gray)
COLOR_FLOOR_TOP = (195, 195, 198)
COLOR_FLOOR_LEFT = (160, 162, 168)
COLOR_FLOOR_RIGHT = (132, 134, 140)
COLOR_FLOOR_BORDER = (160, 162, 168)
COLOR_SIDE_BORDER = (100, 103, 112)

# Bảng màu ô đặc biệt
COLOR_FRAGILE_TOP = (234, 88, 12)
COLOR_FRAGILE_LEFT = (194, 65, 12)
COLOR_FRAGILE_RIGHT = (154, 52, 18)
COLOR_FRAGILE_MARK = (124, 45, 18)

COLOR_BRIDGE_OPEN_TOP = (14, 165, 233)
COLOR_BRIDGE_OPEN_LEFT = (2, 132, 199)
COLOR_BRIDGE_OPEN_RIGHT = (3, 105, 161)
COLOR_BRIDGE_CLOSED_TOP = (22, 29, 42)
COLOR_BRIDGE_CLOSED_BORDER = (40, 52, 72)

COLOR_GOAL_TOP = (217, 119, 6)
COLOR_GOAL_LEFT = (180, 83, 9)
COLOR_GOAL_RIGHT = (146, 64, 14)
COLOR_GOAL_DIAMOND = (254, 240, 138)

# Bảng màu khối Bloxorz
COLOR_BLOCK_TOP = (56, 189, 248)
COLOR_BLOCK_TOP_BEVEL = (186, 230, 253)
COLOR_BLOCK_LEFT = (2, 132, 199)
COLOR_BLOCK_RIGHT = (3, 105, 161)
COLOR_BLOCK_BORDER = (12, 74, 110)

COLOR_BLOCK_ACTIVE_TOP = (168, 85, 247)
COLOR_BLOCK_ACTIVE_BEVEL = (233, 213, 255)
COLOR_BLOCK_ACTIVE_LEFT = (126, 34, 206)
COLOR_BLOCK_ACTIVE_RIGHT = (88, 28, 135)


#hàm cần code lại
def grid_to_iso(r: float, c: float, rows: int, cols: int, center_x: float, center_y: float) -> tuple[float, float]:
    """Chuyển toạ độ lưới (r, c) sang toạ độ Isometric trên màn hình."""
    center_r = rows / 2.0
    center_c = cols / 2.0

    rel_r = r - center_r
    rel_c = c - center_c

    iso_x = center_x + (rel_c - rel_r) * TILE_W
    iso_y = center_y + (rel_c + rel_r) * TILE_H
    return iso_x, iso_y


#hàm cần code lại
def draw_iso_tile(
    surface,
    r: int,
    c: int,
    tile_type: int,
    board,
    bridge_states,
    font_bold,
    center_x: float,
    center_y: float,
    show_goal: bool = True,
):
    """Vẽ ô sàn isometric 3D."""

    if tile_type == TileType.VOID:
        return
    if tile_type == TileType.GOAL and not show_goal:
        return

    cx, cy = grid_to_iso(r, c, board.rows, board.cols, center_x, center_y)

    # Cầu đang đóng: vẽ ô âm chìm tối đen kèm mã cầu
    if tile_type == TileType.BRIDGE:
        b_id = board.tile_to_bridge_id.get((r, c))
        is_open = board.is_bridge_open(b_id, bridge_states) if b_id is not None else False
        if not is_open:
            pts = [(cx, cy - TILE_H), (cx + TILE_W, cy), (cx, cy + TILE_H), (cx - TILE_W, cy)]
            pygame.draw.polygon(surface, COLOR_BRIDGE_CLOSED_TOP, pts)
            pygame.draw.polygon(surface, COLOR_BRIDGE_CLOSED_BORDER, pts, width=1)
            b_label = f"B{b_id + 1}" if b_id is not None else "B"
            txt = font_bold.render(b_label, True, (71, 85, 105))
            surface.blit(txt, txt.get_rect(center=(cx, cy)))
            return

    # Xác định màu sắc theo loại ô
    if tile_type == TileType.FLOOR:
        col_top, col_left, col_right = COLOR_FLOOR_TOP, COLOR_FLOOR_LEFT, COLOR_FLOOR_RIGHT
    elif tile_type == TileType.FRAGILE:
        col_top, col_left, col_right = COLOR_FRAGILE_TOP, COLOR_FRAGILE_LEFT, COLOR_FRAGILE_RIGHT
    elif tile_type == TileType.BRIDGE:
        col_top, col_left, col_right = COLOR_BRIDGE_OPEN_TOP, COLOR_BRIDGE_OPEN_LEFT, COLOR_BRIDGE_OPEN_RIGHT
    elif tile_type == TileType.GOAL:
        col_top, col_left, col_right = COLOR_GOAL_TOP, COLOR_GOAL_LEFT, COLOR_GOAL_RIGHT
    else:
        col_top, col_left, col_right = COLOR_FLOOR_TOP, COLOR_FLOOR_LEFT, COLOR_FLOOR_RIGHT

    top_pts = [(cx, cy - TILE_H), (cx + TILE_W, cy), (cx, cy + TILE_H), (cx - TILE_W, cy)]
    left_pts = [(cx - TILE_W, cy), (cx, cy + TILE_H), (cx, cy + TILE_H + TILE_DEPTH), (cx - TILE_W, cy + TILE_DEPTH)]
    right_pts = [(cx, cy + TILE_H), (cx + TILE_W, cy), (cx + TILE_W, cy + TILE_DEPTH), (cx, cy + TILE_H + TILE_DEPTH)]

    # 1. Vẽ mặt bên
    pygame.draw.polygon(surface, col_left, left_pts)
    pygame.draw.polygon(surface, col_right, right_pts)
    pygame.draw.polygon(surface, COLOR_SIDE_BORDER, left_pts, width=1)
    pygame.draw.polygon(surface, COLOR_SIDE_BORDER, right_pts, width=1)

    # 2. Vẽ mặt trên
    pygame.draw.polygon(surface, col_top, top_pts)
    pygame.draw.polygon(surface, COLOR_FLOOR_BORDER, top_pts, width=1)

    # Nếu là ô Goal: vẽ bệ vàng kim với kim cương phát sáng
    if tile_type == TileType.GOAL:
        d_sz = 10
        diamond_pts = [
            (cx, cy - d_sz),
            (cx + d_sz * 1.5, cy),
            (cx, cy + d_sz),
            (cx - d_sz * 1.5, cy)
        ]
        pygame.draw.polygon(surface, COLOR_GOAL_DIAMOND, diamond_pts)
        pygame.draw.polygon(surface, (255, 255, 255), diamond_pts, width=1)

    # Nếu là ô Fragile: hoa văn gạch chia ô
    if tile_type == TileType.FRAGILE:
        pygame.draw.line(surface, COLOR_FRAGILE_MARK, (cx - 10, cy - 5), (cx + 12, cy + 6), 2)
        pygame.draw.line(surface, COLOR_FRAGILE_MARK, (cx + 5, cy - 8), (cx - 7, cy + 9), 2)

    # Nếu ô có công tắc: vẽ huy hiệu tròn với ký tự S / H / P
    if (r, c) in board.switches:
        sw = board.switches[(r, c)]
        if sw.switch_type == SwitchType.SOFT:
            # Huy hiệu S tròn vàng
            pygame.draw.circle(surface, (251, 191, 36), (int(cx), int(cy)), 9)
            pygame.draw.circle(surface, (180, 130, 20), (int(cx), int(cy)), 9, width=1)
            lbl = font_bold.render("S", True, (15, 23, 42))
            surface.blit(lbl, lbl.get_rect(center=(cx, cy)))
        elif sw.switch_type == SwitchType.HEAVY:
            # Huy hiệu H hình thoi đỏ
            h_pts = [(cx, cy - 8), (cx + 10, cy), (cx, cy + 8), (cx - 10, cy)]
            pygame.draw.polygon(surface, (239, 68, 68), h_pts)
            pygame.draw.polygon(surface, (185, 28, 28), h_pts, width=1)
            lbl = font_bold.render("H", True, (255, 255, 255))
            surface.blit(lbl, lbl.get_rect(center=(cx, cy)))
        elif sw.switch_type == SwitchType.SPLIT:
            # Huy hiệu P tròn tím
            pygame.draw.circle(surface, (168, 85, 247), (int(cx), int(cy)), 9)
            pygame.draw.circle(surface, (126, 34, 206), (int(cx), int(cy)), 9, width=1)
            lbl = font_bold.render("P", True, (255, 255, 255))
            surface.blit(lbl, lbl.get_rect(center=(cx, cy)))


#hàm cần code lại
def draw_block(surface, state: GameState, board, center_x: float, center_y: float):
    """Vẽ khối Bloxorz 3D lên bề mặt isometric."""
    if not state.is_split:
        r, c = state.pos
        ori = state.orientation

        if ori == Orientation.STANDING:
            cx, cy = grid_to_iso(r, c, board.rows, board.cols, center_x, center_y)
            tot_h = BLOCK_H_STANDING

            top_y = cy - tot_h
            top_pts = [(cx, top_y - TILE_H), (cx + TILE_W, top_y), (cx, top_y + TILE_H), (cx - TILE_W, top_y)]
            left_pts = [(cx - TILE_W, top_y), (cx, top_y + TILE_H), (cx, cy + TILE_H), (cx - TILE_W, cy)]
            right_pts = [(cx, top_y + TILE_H), (cx + TILE_W, top_y), (cx + TILE_W, cy), (cx, cy + TILE_H)]

            pygame.draw.polygon(surface, COLOR_BLOCK_LEFT, left_pts)
            pygame.draw.polygon(surface, COLOR_BLOCK_RIGHT, right_pts)
            pygame.draw.polygon(surface, COLOR_BLOCK_BORDER, left_pts, width=1)
            pygame.draw.polygon(surface, COLOR_BLOCK_BORDER, right_pts, width=1)

            pygame.draw.polygon(surface, COLOR_BLOCK_TOP, top_pts)
            pygame.draw.polygon(surface, COLOR_BLOCK_TOP_BEVEL, top_pts, width=2)

        elif ori == Orientation.HORIZONTAL:
            cx0, cy0 = grid_to_iso(r, c, board.rows, board.cols, center_x, center_y)
            cx1, cy1 = grid_to_iso(r, c + 1, board.rows, board.cols, center_x, center_y)
            tot_h = BLOCK_H_LYING

            base_n = (cx0, cy0 - TILE_H)
            base_e = (cx1 + TILE_W, cy1)
            base_s = (cx1, cy1 + TILE_H)
            base_w = (cx0 - TILE_W, cy0)

            top_n = (base_n[0], base_n[1] - tot_h)
            top_e = (base_e[0], base_e[1] - tot_h)
            top_s = (base_s[0], base_s[1] - tot_h)
            top_w = (base_w[0], base_w[1] - tot_h)

            left_pts = [top_w, top_s, base_s, base_w]
            right_pts = [top_s, top_e, base_e, base_s]
            top_pts = [top_n, top_e, top_s, top_w]

            pygame.draw.polygon(surface, COLOR_BLOCK_LEFT, left_pts)
            pygame.draw.polygon(surface, COLOR_BLOCK_RIGHT, right_pts)
            pygame.draw.polygon(surface, COLOR_BLOCK_BORDER, left_pts, width=1)
            pygame.draw.polygon(surface, COLOR_BLOCK_BORDER, right_pts, width=1)

            pygame.draw.polygon(surface, COLOR_BLOCK_TOP, top_pts)
            pygame.draw.polygon(surface, COLOR_BLOCK_TOP_BEVEL, top_pts, width=2)

        elif ori == Orientation.VERTICAL:
            cx0, cy0 = grid_to_iso(r, c, board.rows, board.cols, center_x, center_y)
            cx1, cy1 = grid_to_iso(r + 1, c, board.rows, board.cols, center_x, center_y)
            tot_h = BLOCK_H_LYING

            base_n = (cx0, cy0 - TILE_H)
            base_e = (cx0 + TILE_W, cy0)
            base_s = (cx1, cy1 + TILE_H)
            base_w = (cx1 - TILE_W, cy1)

            top_n = (base_n[0], base_n[1] - tot_h)
            top_e = (base_e[0], base_e[1] - tot_h)
            top_s = (base_s[0], base_s[1] - tot_h)
            top_w = (base_w[0], base_w[1] - tot_h)

            left_pts = [top_w, top_s, base_s, base_w]
            right_pts = [top_s, top_e, base_e, base_s]
            top_pts = [top_n, top_e, top_s, top_w]

            pygame.draw.polygon(surface, COLOR_BLOCK_LEFT, left_pts)
            pygame.draw.polygon(surface, COLOR_BLOCK_RIGHT, right_pts)
            pygame.draw.polygon(surface, COLOR_BLOCK_BORDER, left_pts, width=1)
            pygame.draw.polygon(surface, COLOR_BLOCK_BORDER, right_pts, width=1)

            pygame.draw.polygon(surface, COLOR_BLOCK_TOP, top_pts)
            pygame.draw.polygon(surface, COLOR_BLOCK_TOP_BEVEL, top_pts, width=2)

    else:
        c0, c1 = state.cubes
        cubes_to_draw = [(0, c0), (1, c1)]
        cubes_to_draw.sort(key=lambda item: item[1][0] + item[1][1])

        for idx, (cr, cc) in cubes_to_draw:
            cx, cy = grid_to_iso(cr, cc, board.rows, board.cols, center_x, center_y)
            tot_h = BLOCK_H
            is_active = (idx == state.active_cube)

            top_y = cy - tot_h
            top_pts = [(cx, top_y - TILE_H), (cx + TILE_W, top_y), (cx, top_y + TILE_H), (cx - TILE_W, top_y)]
            left_pts = [(cx - TILE_W, top_y), (cx, top_y + TILE_H), (cx, cy + TILE_H), (cx - TILE_W, cy)]
            right_pts = [(cx, top_y + TILE_H), (cx + TILE_W, top_y), (cx + TILE_W, cy), (cx, cy + TILE_H)]

            if is_active:
                c_top = COLOR_BLOCK_ACTIVE_TOP
                c_bev = COLOR_BLOCK_ACTIVE_BEVEL
                c_left = COLOR_BLOCK_ACTIVE_LEFT
                c_right = COLOR_BLOCK_ACTIVE_RIGHT
            else:
                c_top = COLOR_BLOCK_TOP
                c_bev = COLOR_BLOCK_TOP_BEVEL
                c_left = COLOR_BLOCK_LEFT
                c_right = COLOR_BLOCK_RIGHT

            pygame.draw.polygon(surface, c_left, left_pts)
            pygame.draw.polygon(surface, c_right, right_pts)
            pygame.draw.polygon(surface, (15, 23, 42), left_pts, width=1)
            pygame.draw.polygon(surface, (15, 23, 42), right_pts, width=1)

            pygame.draw.polygon(surface, c_top, top_pts)
            pygame.draw.polygon(surface, c_bev, top_pts, width=2)

            if is_active:
                arrow_pts = [
                    (cx, top_y - TILE_H - 14),
                    (cx - 6, top_y - TILE_H - 24),
                    (cx + 6, top_y - TILE_H - 24)
                ]
                pygame.draw.polygon(surface, (234, 179, 8), arrow_pts)


def _draw_single_static_cube(surface, cr: int, cc: int, board, center_x: float, center_y: float, is_active: bool = False):
    """Vẽ 1 viên lập phương 1x1x1 tĩnh khi tách khối."""
    cx, cy = grid_to_iso(cr, cc, board.rows, board.cols, center_x, center_y)
    tot_h = BLOCK_H
    top_y = cy - tot_h
    top_pts = [(cx, top_y - TILE_H), (cx + TILE_W, top_y), (cx, top_y + TILE_H), (cx - TILE_W, top_y)]
    left_pts = [(cx - TILE_W, top_y), (cx, top_y + TILE_H), (cx, cy + TILE_H), (cx - TILE_W, cy)]
    right_pts = [(cx, top_y + TILE_H), (cx + TILE_W, top_y), (cx + TILE_W, cy), (cx, cy + TILE_H)]

    if is_active:
        c_top = COLOR_BLOCK_ACTIVE_TOP
        c_bev = COLOR_BLOCK_ACTIVE_BEVEL
        c_left = COLOR_BLOCK_ACTIVE_LEFT
        c_right = COLOR_BLOCK_ACTIVE_RIGHT
    else:
        c_top = COLOR_BLOCK_TOP
        c_bev = COLOR_BLOCK_TOP_BEVEL
        c_left = COLOR_BLOCK_LEFT
        c_right = COLOR_BLOCK_RIGHT

    pygame.draw.polygon(surface, c_left, left_pts)
    pygame.draw.polygon(surface, c_right, right_pts)
    pygame.draw.polygon(surface, (15, 23, 42), left_pts, width=1)
    pygame.draw.polygon(surface, (15, 23, 42), right_pts, width=1)
    pygame.draw.polygon(surface, c_top, top_pts)
    pygame.draw.polygon(surface, c_bev, top_pts, width=2)


#hàm cần code lại
def draw_falling_block(
    surface,
    from_state: GameState,
    to_state: GameState,
    move_dir: str,
    board,
    center_x: float,
    center_y: float,
    roll_progress: float,
    fall_progress: float,
):
    """Vẽ khối lăn tới vị trí lỗi rồi rơi dần xuống dưới bàn cờ."""
    if fall_progress <= 0.0:
        draw_rolling_block(
            surface,
            from_state,
            to_state,
            move_dir,
            roll_progress,
            board,
            center_x,
            center_y,
        )
        return

    falling_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    draw_block(falling_surface, to_state, board, center_x, center_y)
    bounds = falling_surface.get_bounding_rect()
    if bounds.width == 0 or bounds.height == 0:
        return

    block_image = falling_surface.subsurface(bounds).copy()
    scale = 1.0 - 0.55 * min(1.0, max(0.0, fall_progress))
    scaled_size = (
        max(1, int(block_image.get_width() * scale)),
        max(1, int(block_image.get_height() * scale)),
    )
    block_image = pygame.transform.smoothscale(block_image, scaled_size)
    block_image.set_alpha(int(255 * (1.0 - fall_progress)))

    # The block sinks into the void instead of teleporting downward.
    center_x_pos = bounds.centerx
    center_y_pos = bounds.centery + int(TILE_H * 2.2 * fall_progress)
    target_rect = block_image.get_rect(
        center=(center_x_pos, center_y_pos)
    )
    surface.blit(block_image, target_rect)


def draw_rolling_block(surface, from_state: GameState, to_state: GameState, move_dir: str, progress: float, board, center_x: float, center_y: float):
    """Vẽ animation khối Bloxorz đang lăn 3D giữa 2 trạng thái."""
    import math


    # Nếu là các hiệu ứng đặc biệt tách / gộp (SPLIT / MERGE)
    d_upper = str(move_dir).upper()
    if "SPLIT" in d_upper or "MERGE" in d_upper:
        st = to_state if progress >= 0.5 else from_state
        draw_block(surface, st, board, center_x, center_y)
        return

    # Xác định hình hộp ban đầu (r_min, r_max, c_min, c_max, z_min, z_max)
    if from_state.is_split:
        active_idx = from_state.active_cube
        inactive_idx = 1 - active_idx

        # Vẽ viên thụ động tĩnh
        inact_r, inact_c = from_state.cubes[inactive_idx]
        _draw_single_static_cube(surface, inact_r, inact_c, board, center_x, center_y, is_active=False)

        # Viên chủ động lăn
        act_r, act_c = from_state.cubes[active_idx]
        r_min, r_max = act_r - 0.5, act_r + 0.5
        c_min, c_max = act_c - 0.5, act_c + 0.5
        z_min, z_max = 0.0, 1.0
        is_active_cube = True
    else:
        r, c = from_state.pos
        ori = from_state.orientation
        is_active_cube = False

        if ori == Orientation.STANDING:
            r_min, r_max = r - 0.5, r + 0.5
            c_min, c_max = c - 0.5, c + 0.5
            z_min, z_max = 0.0, float(BLOCK_H_STANDING) / max(1.0, float(BLOCK_H_LYING))
        elif ori == Orientation.HORIZONTAL:
            r_min, r_max = r - 0.5, r + 0.5
            c_min, c_max = c - 0.5, c + 1.5
            z_min, z_max = 0.0, 1.0
        elif ori == Orientation.VERTICAL:
            r_min, r_max = r - 0.5, r + 1.5
            c_min, c_max = c - 0.5, c + 0.5
            z_min, z_max = 0.0, 1.0
        else:
            r_min, r_max = r - 0.5, r + 0.5
            c_min, c_max = c - 0.5, c + 0.5
            z_min, z_max = 0.0, float(BLOCK_H_STANDING) / max(1.0, float(BLOCK_H_LYING))

    # Xác định hướng lăn
    if "RIGHT" in d_upper:
        roll_type = "RIGHT"
    elif "LEFT" in d_upper:
        roll_type = "LEFT"
    elif "DOWN" in d_upper:
        roll_type = "DOWN"
    elif "UP" in d_upper:
        roll_type = "UP"
    else:
        roll_type = "RIGHT"

    alpha = max(0.0, min(1.0, progress)) * (math.pi / 2.0)
    cos_a = math.cos(alpha)
    sin_a = math.sin(alpha)

    # 1. Hàm quay toạ độ điểm (r, c, z) quanh cạnh đáy
    def rotate_point(pr, pc, pz):
        if roll_type == "RIGHT":
            p = c_max
            dc = pc - p
            new_c = p + dc * cos_a + pz * sin_a
            new_z = -dc * sin_a + pz * cos_a
            new_r = pr
        elif roll_type == "LEFT":
            p = c_min
            dc = pc - p
            new_c = p + dc * cos_a - pz * sin_a
            new_z = dc * sin_a + pz * cos_a
            new_r = pr
        elif roll_type == "DOWN":
            p = r_max
            dr = pr - p
            new_r = p + dr * cos_a + pz * sin_a
            new_z = -dr * sin_a + pz * cos_a
            new_c = pc
        elif roll_type == "UP":
            p = r_min
            dr = pr - p
            new_r = p + dr * cos_a - pz * sin_a
            new_z = dr * sin_a + pz * cos_a
            new_c = pc
        return new_r, new_c, new_z

    # 2. Hàm quay vector pháp tuyến mặt (Nr, Nc, Nz)
    def rotate_normal(nr, nc, nz):
        if roll_type == "RIGHT":
            new_c = nc * cos_a + nz * sin_a
            new_z = -nc * sin_a + nz * cos_a
            new_r = nr
        elif roll_type == "LEFT":
            new_c = nc * cos_a - nz * sin_a
            new_z = nc * sin_a + nz * cos_a
            new_r = nr
        elif roll_type == "DOWN":
            new_r = nr * cos_a + nz * sin_a
            new_z = -nr * sin_a + nz * cos_a
            new_c = nc
        elif roll_type == "UP":
            new_r = nr * cos_a - nz * sin_a
            new_z = nr * sin_a + nz * cos_a
            new_c = nc
        return new_r, new_c, new_z

    # 3. Chiếu điểm 3D lên màn hình 2D Isometric
    center_r = board.rows / 2.0
    center_c = board.cols / 2.0

    def project_3d(pr, pc, pz):
        rel_r = pr - center_r
        rel_c = pc - center_c
        sx = center_x + (rel_c - rel_r) * TILE_W
        sy = center_y + (rel_c + rel_r) * TILE_H - pz * BLOCK_H_LYING
        return (sx, sy)

    # 8 đỉnh của cuboid
    raw_verts = {
        (0,0,0): (r_min, c_min, z_min),
        (0,1,0): (r_min, c_max, z_min),
        (1,1,0): (r_max, c_max, z_min),
        (1,0,0): (r_max, c_min, z_min),
        (0,0,1): (r_min, c_min, z_max),
        (0,1,1): (r_min, c_max, z_max),
        (1,1,1): (r_max, c_max, z_max),
        (1,0,1): (r_max, c_min, z_max),
    }

    # Quay và chiếu các đỉnh
    proj_verts = {}
    rot_3d_verts = {}
    for k, pt in raw_verts.items():
        r_rot, c_rot, z_rot = rotate_point(*pt)
        rot_3d_verts[k] = (r_rot, c_rot, z_rot)
        proj_verts[k] = project_3d(r_rot, c_rot, z_rot)

    # 6 mặt của khối hộp (các đỉnh theo thứ tự viền ngoài)
    faces_def = [
        ("top", [(0,0,1), (0,1,1), (1,1,1), (1,0,1)], (0.0, 0.0, 1.0)),
        ("bottom", [(0,0,0), (1,0,0), (1,1,0), (0,1,0)], (0.0, 0.0, -1.0)),
        ("south_east", [(0,1,0), (1,1,0), (1,1,1), (0,1,1)], (0.0, 1.0, 0.0)),
        ("north_west", [(0,0,0), (0,0,1), (1,0,1), (1,0,0)], (0.0, -1.0, 0.0)),
        ("south_west", [(1,0,0), (1,0,1), (1,1,1), (1,1,0)], (1.0, 0.0, 0.0)),
        ("north_east", [(0,0,0), (0,1,0), (0,1,1), (0,0,1)], (-1.0, 0.0, 0.0)),
    ]

    visible_faces = []
    for f_name, v_keys, initial_norm in faces_def:
        pts_2d = [proj_verts[k] for k in v_keys]
        # Shoelace formula tính diện tích 2D có hướng (khử mặt khuất)
        area = 0.5 * sum(
            pts_2d[i][0] * pts_2d[(i + 1) % 4][1] - pts_2d[(i + 1) % 4][0] * pts_2d[i][1]
            for i in range(4)
        )
        if area > 1e-4:
            rot_norm = rotate_normal(*initial_norm)
            avg_r = sum(rot_3d_verts[k][0] for k in v_keys) / 4.0
            avg_c = sum(rot_3d_verts[k][1] for k in v_keys) / 4.0
            avg_z = sum(rot_3d_verts[k][2] for k in v_keys) / 4.0
            depth = (avg_r + avg_c) - 0.5 * avg_z
            visible_faces.append((depth, pts_2d, rot_norm, f_name))

    # Sắp xếp mặt theo chiều sâu từ xa đến gần
    visible_faces.sort(key=lambda item: item[0])

    for depth, pts_2d, rot_norm, f_name in visible_faces:
        nr, nc, nz = rot_norm

        # Phối màu Cyberpunk theo hướng chiếu sáng
        if not is_active_cube:
            if nz > 0.40:
                col_fill = COLOR_BLOCK_TOP
                col_border = COLOR_BLOCK_TOP_BEVEL
                bw = 2
            elif nr > nc:
                col_fill = COLOR_BLOCK_LEFT
                col_border = COLOR_BLOCK_BORDER
                bw = 1
            elif nc > nr:
                col_fill = COLOR_BLOCK_RIGHT
                col_border = COLOR_BLOCK_BORDER
                bw = 1
            else:
                col_fill = (12, 74, 110)
                col_border = (7, 43, 64)
                bw = 1
        else:
            if nz > 0.40:
                col_fill = COLOR_BLOCK_ACTIVE_TOP
                col_border = COLOR_BLOCK_ACTIVE_BEVEL
                bw = 2
            elif nr > nc:
                col_fill = COLOR_BLOCK_ACTIVE_LEFT
                col_border = (15, 23, 42)
                bw = 1
            elif nc > nr:
                col_fill = COLOR_BLOCK_ACTIVE_RIGHT
                col_border = (15, 23, 42)
                bw = 1
            else:
                col_fill = (59, 7, 100)
                col_border = (15, 23, 42)
                bw = 1

        pygame.draw.polygon(surface, col_fill, pts_2d)
        pygame.draw.polygon(surface, col_border, pts_2d, width=bw)
