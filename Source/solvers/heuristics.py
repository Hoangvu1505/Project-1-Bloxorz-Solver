"""
Hàm Heuristic ước lượng khoảng cách cho thuật toán A* trong Bloxorz.
"""

from typing import Tuple
from core.state import GameState, Orientation


def heuristic_bloxorz(state: GameState, goal_pos: Tuple[int, int]) -> float:
    """
    Hàm Heuristic h(n) ước lượng chi phí/số bước còn lại từ trạng thái hiện tại đến đích.

    Đầu vào:
        state (GameState): Trạng thái hiện tại của khối Bloxorz.
        goal_pos (Tuple[int, int]): Toạ độ (hàng, cột) của ô đích.

    Đầu ra:
        float: Giá trị ước lượng chi phí còn lại h(n).
    """
    gr, gc = goal_pos

    # Trường hợp 1: Khối đặc nguyên bản (không bị tách)
    if not state.is_split:
        cells = state.get_occupied_cells()
        # Tìm khoảng cách Manhattan nhỏ nhất từ các ô khối đang chiếm đến ô đích
        min_dist = min(abs(r - gr) + abs(c - gc) for r, c in cells)

        if min_dist == 0:
            if state.orientation == Orientation.STANDING:
                return 0.0
            else:
                return 2.0
        else:
            return float((min_dist + 1) // 2)

    # Trường hợp 2: Khối đang bị tách thành 2 viên 1x1x1
    else:
        c0, c1 = state.cubes
        d0 = abs(c0[0] - gr) + abs(c0[1] - gc)
        d1 = abs(c1[0] - gr) + abs(c1[1] - gc)
        d_between = abs(c0[0] - c1[0]) + abs(c0[1] - c1[1])
        return float((d0 + d1 + d_between + 3) // 4)


