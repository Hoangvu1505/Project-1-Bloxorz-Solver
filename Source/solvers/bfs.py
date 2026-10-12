"""
Thuật toán tìm kiếm Breadth-First Search (BFS).
"""

import time
import tracemalloc
from collections import deque
from typing import Dict, Tuple, Optional

from core.board import BloxorzBoard
from core.state import GameState
from solvers.base_solver import SearchResult, reconstruct_path


#hàm cần code lại
def solve_bfs(board: BloxorzBoard) -> SearchResult:
    """Thuật toán tìm kiếm theo chiều rộng (BFS)."""
    tracemalloc.start()
    start_time = time.perf_counter()

    initial_state = board.get_initial_state()
    if board.is_goal_state(initial_state):
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return SearchResult(
            algorithm="BFS",
            solved=True,
            actions=[],
            states_path=[initial_state],
            expanded_nodes=0,
            solution_length=0,
            total_cost=0.0,
            search_time=time.perf_counter() - start_time,
            peak_memory_kb=peak_mem / 1024.0
        )

    queue: deque[GameState] = deque([initial_state])
    parent_map: Dict[GameState, Tuple[Optional[GameState], Optional[str], float]] = {
        initial_state: (None, None, 0.0)
    }
    visited = {initial_state}
    expanded_nodes = 0
    solved = False
    goal_state = None

    while queue:
        curr_state = queue.popleft()
        expanded_nodes += 1

        if board.is_goal_state(curr_state):
            solved = True
            goal_state = curr_state
            break

        for action, next_state, cost in board.get_successors(curr_state):
            if next_state not in visited:
                visited.add(next_state)
                parent_map[next_state] = (curr_state, action, cost)
                if board.is_goal_state(next_state):
                    expanded_nodes += 1
                    solved = True
                    goal_state = next_state
                    break
                queue.append(next_state)

        if solved:
            break

    search_time = time.perf_counter() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if solved and goal_state:
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
    else:
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

