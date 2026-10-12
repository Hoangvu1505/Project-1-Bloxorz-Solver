"""
Thuật toán tìm kiếm A* Search.
"""

import time
import tracemalloc
import heapq
from typing import Dict, Tuple, Optional, List, Callable

from core.board import BloxorzBoard
from core.state import GameState
from solvers.base_solver import SearchResult, reconstruct_path
from solvers.heuristics import heuristic_bloxorz


def solve_astar(
    board: BloxorzBoard,
    heuristic_func: Optional[Callable[[GameState, Tuple[int, int]], float]] = None,
    use_weighted_cost: bool = True
) -> SearchResult:
    """Thuật toán A* Search."""
    if heuristic_func is None:
        heuristic_func = heuristic_bloxorz

    tracemalloc.start()
    start_time = time.perf_counter()

    initial_state = board.get_initial_state()
    h_init = heuristic_func(initial_state, board.goal_pos)

    # Priority queue lưu tuple: (f_score, h_score, counter, state)
    counter = 0
    pq: List[Tuple[float, float, int, GameState]] = [(h_init, h_init, counter, initial_state)]
    g_score: Dict[GameState, float] = {initial_state: 0.0}
    parent_map: Dict[GameState, Tuple[Optional[GameState], Optional[str], float]] = {
        initial_state: (None, None, 0.0)
    }

    expanded_nodes = 0
    solved = False
    goal_state = None

    while pq:
        curr_f, curr_h, _, curr_state = heapq.heappop(pq)
        curr_g = g_score.get(curr_state, float('inf'))

        if curr_g + curr_h > curr_f + 1e-6:
            continue

        expanded_nodes += 1

        if board.is_goal_state(curr_state):
            solved = True
            goal_state = curr_state
            break

        for action, next_state, step_cost in board.get_successors(curr_state):
            cost_to_add = step_cost if use_weighted_cost else 1.0
            tentative_g = curr_g + cost_to_add

            if tentative_g < g_score.get(next_state, float('inf')):
                g_score[next_state] = tentative_g
                h_val = heuristic_func(next_state, board.goal_pos)
                f_val = tentative_g + h_val
                parent_map[next_state] = (curr_state, action, cost_to_add)
                counter += 1
                heapq.heappush(pq, (f_val, h_val, counter, next_state))

    search_time = time.perf_counter() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if solved and goal_state:
        actions, states, total_cost = reconstruct_path(parent_map, goal_state)
        return SearchResult(
            algorithm="A*",
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
            algorithm="A*",
            solved=False,
            actions=[],
            states_path=[],
            expanded_nodes=expanded_nodes,
            solution_length=0,
            total_cost=0.0,
            search_time=search_time,
            peak_memory_kb=peak_mem / 1024.0
        )

