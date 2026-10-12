"""
Hàm Heuristic ước lượng cho thuật toán A* trong Bloxorz.
"""

from typing import Tuple
from core.state import GameState, Orientation


def heuristic_bloxorz(state: GameState, goal_pos: Tuple[int, int]) -> float:
    """Hàm Heuristic h(n) ước lượng chi phí còn lại từ trạng thái n đến đích."""
    gr, gc = goal_pos

    if not state.is_split:
        cells = state.get_occupied_cells()
        min_dist = min(abs(r - gr) + abs(c - gc) for r, c in cells)

        if min_dist == 0:
            if state.orientation == Orientation.STANDING:
                return 0.0
            else:
                return 2.0
        else:
            return float((min_dist + 1) // 2)
    else:
        c0, c1 = state.cubes
        d0 = abs(c0[0] - gr) + abs(c0[1] - gc)
        d1 = abs(c1[0] - gr) + abs(c1[1] - gc)
        d_between = abs(c0[0] - c1[0]) + abs(c0[1] - c1[1])
        return float((d0 + d1 + d_between + 3) // 4)

