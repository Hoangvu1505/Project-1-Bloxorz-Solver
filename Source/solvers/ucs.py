"""
Thuật toán tìm kiếm Uniform-Cost Search (UCS).
"""

import time
import tracemalloc
import heapq
from typing import Dict, Tuple, Optional, List

from core.board import BloxorzBoard
from core.state import GameState
from solvers.base_solver import SearchResult, reconstruct_path


#hàm cần code lại
def solve_ucs(board: BloxorzBoard, use_weighted_cost: bool = True) -> SearchResult:
    """Thuật toán Uniform-Cost Search (UCS)."""
    tracemalloc.start()
    start_time = time.perf_counter()

    initial_state = board.get_initial_state()

    # Priority queue lưu tuple: (g_cost, counter, state)
    counter = 0
    pq: List[Tuple[float, int, GameState]] = [(0.0, counter, initial_state)]
    best_cost: Dict[GameState, float] = {initial_state: 0.0}
    parent_map: Dict[GameState, Tuple[Optional[GameState], Optional[str], float]] = {
        initial_state: (None, None, 0.0)
    }

    expanded_nodes = 0
    solved = False
    goal_state = None

    while pq:
        curr_g, _, curr_state = heapq.heappop(pq)

        if curr_g > best_cost.get(curr_state, float('inf')):
            continue

        expanded_nodes += 1

        if board.is_goal_state(curr_state):
            solved = True
            goal_state = curr_state
            break

        for action, next_state, step_cost in board.get_successors(curr_state):
            cost_to_add = step_cost if use_weighted_cost else 1.0
            new_g = curr_g + cost_to_add

            if new_g < best_cost.get(next_state, float('inf')):
                best_cost[next_state] = new_g
                parent_map[next_state] = (curr_state, action, cost_to_add)
                counter += 1
                heapq.heappush(pq, (new_g, counter, next_state))

    search_time = time.perf_counter() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if solved and goal_state:
        actions, states, total_cost = reconstruct_path(parent_map, goal_state)
        return SearchResult(
            algorithm="UCS",
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
            algorithm="UCS",
            solved=False,
            actions=[],
            states_path=[],
            expanded_nodes=expanded_nodes,
            solution_length=0,
            total_cost=0.0,
            search_time=search_time,
            peak_memory_kb=peak_mem / 1024.0
        )

