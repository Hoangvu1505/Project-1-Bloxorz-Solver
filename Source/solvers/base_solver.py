"""
Định nghĩa SearchResult và hàm truy vết đường đi reconstruct_path.
"""

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from core.state import GameState


@dataclass
class SearchResult:
    """Kết quả thực thi của một thuật toán tìm kiếm."""
    algorithm: str
    solved: bool
    actions: List[str]
    states_path: List[GameState]
    expanded_nodes: int
    solution_length: int
    total_cost: float
    search_time: float
    peak_memory_kb: float

    def summary(self) -> str:
        status = "THÀNH CÔNG" if self.solved else "THẤT BẠI"
        return (
            f"[{self.algorithm}] {status} | "
            f"Thời gian: {self.search_time * 1000:.2f} ms | "
            f"Bộ nhớ: {self.peak_memory_kb:.2f} KB | "
            f"Nút mở rộng: {self.expanded_nodes} | "
            f"Độ dài lời giải: {self.solution_length} bước | "
            f"Tổng chi phí: {self.total_cost:.2f}"
        )


def reconstruct_path(parent_map, goal_state):
    if goal_state not in parent_map:
        raise KeyError("goal_state không có trong parent_map")

    actions, states = [], []
    total_cost = 0.0
    curr = goal_state

    while curr is not None:
        states.append(curr)
        parent, act, cost = parent_map[curr]
        if act is not None:
            actions.append(act)
            total_cost += cost
        curr = parent

    actions.reverse()
    states.reverse()
    return actions, states, total_cost

