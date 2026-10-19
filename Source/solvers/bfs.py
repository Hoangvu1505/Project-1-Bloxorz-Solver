"""
Thuật toán tìm kiếm Breadth-First Search (BFS).
"""

import time
import tracemalloc
from collections import deque
from typing import Dict, Tuple, Optional, Hashable

from core.board import BloxorzBoard
from core.state import GameState
from solvers.base_solver import SearchResult, reconstruct_path


def _state_key(state: GameState) -> Hashable:
    """Khoá nhận dạng trạng thái để loại trùng trong `visited`.

    GameState.__eq__/__hash__ có tính `active_cube` (cube vừa di chuyển), nhưng
    get_successors luôn sinh nước đi cho cả hai khối nên nó không ảnh hưởng tương lai.
    Bỏ nó đi để cùng một cấu hình không bị tính thành 2 trạng thái khác nhau.
    (`cubes` đã được GameState sắp xếp sẵn nên không cần sort lại.)
    """
    return (state.is_split, state.orientation, state.pos, state.cubes, state.bridge_states)


def solve_bfs(board: BloxorzBoard) -> SearchResult:
    """Tìm kiếm theo chiều rộng (BFS).

    BFS cho lời giải ít bước nhất. Vì chi phí mỗi bước không đồng đều
    (gạch yếu, công tắc, tách/gộp), đó chưa chắc là lời giải tổng chi phí nhỏ nhất.
    """
    tracemalloc.start()
    start_time = time.perf_counter()

    initial_state = board.get_initial_state()

    parent_map: Dict[GameState, Tuple[Optional[GameState], Optional[str], float]] = {
        initial_state: (None, None, 0.0)
    }
    visited = {_state_key(initial_state)}
    queue: deque = deque([initial_state])
    expanded_nodes = 0

    goal_state: Optional[GameState] = (
        initial_state if board.is_goal_state(initial_state) else None
    )

    while queue and goal_state is None:
        curr_state = queue.popleft()
        expanded_nodes += 1

        for action, next_state, cost in board.get_successors(curr_state):
            key = _state_key(next_state)
            if key in visited:
                continue
            visited.add(key)
            parent_map[next_state] = (curr_state, action, cost)

            # Goal-test lúc sinh nút: BFS nên dừng sớm, tiết kiệm một tầng mở rộng.
            if board.is_goal_state(next_state):
                expanded_nodes += 1
                goal_state = next_state
                break
            queue.append(next_state)

    search_time = time.perf_counter() - start_time
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if goal_state is None:
        return SearchResult(
            algorithm="BFS",
            solved=False,
            actions=[],
            states_path=[],
            expanded_nodes=expanded_nodes,
            solution_length=0,
            total_cost=0.0,
            search_time=search_time,
            peak_memory_kb=peak_mem / 1024.0
        )

    actions, states, total_cost = reconstruct_path(parent_map, goal_state)
    return SearchResult(
        algorithm="BFS",
        solved=True,
        actions=actions,
        states_path=states,
        expanded_nodes=expanded_nodes,
        solution_length=len(actions),
        total_cost=total_cost,
        search_time=search_time,
        peak_memory_kb=peak_mem / 1024.0
    )