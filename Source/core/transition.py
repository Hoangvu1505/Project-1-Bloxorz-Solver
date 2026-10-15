"""
Quy tắc chuyển đổi trạng thái khi lăn khối Bloxorz.
"""

from typing import Tuple, Optional
from core.state import Orientation, Direction, DIR_DELTAS



def roll_solid_block(
    ori: Orientation,
    pos: Tuple[int, int],
    move: Direction
) -> Tuple[Orientation, Tuple[int, int]]:
    """Tính toán định hướng và toạ độ mới của khối 1x1x2 khi lăn theo hướng move."""
    r, c = pos

    if ori == Orientation.STANDING:
        if move == Direction.UP:
            return Orientation.VERTICAL, (r - 2, c)
        elif move == Direction.DOWN:
            return Orientation.VERTICAL, (r + 1, c)
        elif move == Direction.LEFT:
            return Orientation.HORIZONTAL, (r, c - 2)
        elif move == Direction.RIGHT:
            return Orientation.HORIZONTAL, (r, c + 1)

    elif ori == Orientation.HORIZONTAL:
        if move == Direction.UP:
            return Orientation.HORIZONTAL, (r - 1, c)
        elif move == Direction.DOWN:
            return Orientation.HORIZONTAL, (r + 1, c)
        elif move == Direction.LEFT:
            return Orientation.STANDING, (r, c - 1)
        elif move == Direction.RIGHT:
            return Orientation.STANDING, (r, c + 2)

    elif ori == Orientation.VERTICAL:
        if move == Direction.UP:
            return Orientation.STANDING, (r - 1, c)
        elif move == Direction.DOWN:
            return Orientation.STANDING, (r + 2, c)
        elif move == Direction.LEFT:
            return Orientation.VERTICAL, (r, c - 1)
        elif move == Direction.RIGHT:
            return Orientation.VERTICAL, (r, c + 1)

    raise ValueError(f"Không hợp lệ: orientation={ori}, direction={move}")



def roll_split_cube(
    cube_pos: Tuple[int, int],
    move: Direction
) -> Tuple[int, int]:
    """Di chuyển một khối lập phương 1x1x1 theo hướng chỉ định."""
    dr, dc = DIR_DELTAS[move]
    return cube_pos[0] + dr, cube_pos[1] + dc



def check_cube_merge(
    cube1: Tuple[int, int],
    cube2: Tuple[int, int]
) -> Tuple[bool, Optional[Orientation], Optional[Tuple[int, int]]]:
    """Kiểm tra điều kiện sáp nhập hai khối 1x1x1 lại thành khối 1x1x2."""
    r1, c1 = cube1
    r2, c2 = cube2

    # Kề nhau theo phương ngang
    if r1 == r2 and abs(c1 - c2) == 1:
        return True, Orientation.HORIZONTAL, (r1, min(c1, c2))

    # Kề nhau theo phương dọc
    if c1 == c2 and abs(r1 - r2) == 1:
        return True, Orientation.VERTICAL, (min(r1, r2), c1)

    return False, None, None

