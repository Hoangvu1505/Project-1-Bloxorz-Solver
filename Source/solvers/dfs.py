"""
Thuật toán tìm kiếm Depth-First Search (DFS) và Iterative Deepening Search (IDS).
"""

import time
import tracemalloc
from typing import Dict, Tuple, Optional, List

from core.board import BloxorzBoard
from core.state import GameState
from solvers.base_solver import SearchResult, reconstruct_path


#hàm cần code lại
def solve_dfs(board: BloxorzBoard, max_depth: int = 150) -> SearchResult:
    """Thuật toán tìm kiếm theo chiều sâu (DFS) có giới hạn độ sâu và tránh chu kỳ."""
    tracemalloc.start()
    start_time = time.perf_counter()

    initial_state = board.get_initial_state()
    stack: List[Tuple[GameState, int]] = [(initial_state, 0)]
    parent_map: Dict[GameState, Tuple[Optional[GameState], Optional[str], float]] = {
        initial_state: (None, None, 0.0)
    }
    visited_at_depth: Dict[GameState, int] = {initial_state: 0}
    expanded_nodes = 0
    solved = False
    goal_state = None

    while stack:
        curr_state, depth = stack.pop()
        expanded_nodes += 1

        if board.is_goal_state(curr_state):
            solved = True
            goal_state = curr_state
            break

        if depth >= max_depth:
            continue

        for action, next_state, cost in reversed(board.get_successors(curr_state)):
            if next_state not in visited_at_depth or depth + 1 < visited_at_depth[next_state]:
                visited_at_depth[next_state] = depth + 1
                parent_map[next_state] = (curr_state, action, cost)
                stack.append((next_state, depth + 1))

    search_time = time.perf_counter() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if solved and goal_state:
        actions, states, total_cost = reconstruct_path(parent_map, goal_state)
        return SearchResult(
            algorithm="DFS",
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
            algorithm="DFS",
            solved=False,
            actions=[],
            states_path=[],
            expanded_nodes=expanded_nodes,
            solution_length=0,
            total_cost=0.0,
            search_time=search_time,
            peak_memory_kb=peak_mem / 1024.0
        )


#hàm cần code lại
def solve_ids(board: BloxorzBoard, max_limit: int = 100) -> SearchResult:
    """Thuật toán tìm kiếm lặp sâu dần (Iterative Deepening Search - IDS)."""
    tracemalloc.start()
    start_time = time.perf_counter()

    initial_state = board.get_initial_state()
    total_expanded = 0

    for depth_limit in range(1, max_limit + 1):
        stack: List[Tuple[GameState, int]] = [(initial_state, 0)]
        parent_map: Dict[GameState, Tuple[Optional[GameState], Optional[str], float]] = {
            initial_state: (None, None, 0.0)
        }
        visited_at_depth: Dict[GameState, int] = {initial_state: 0}
        solved = False
        goal_state = None

        while stack:
            curr_state, depth = stack.pop()
            total_expanded += 1

            if board.is_goal_state(curr_state):
                solved = True
                goal_state = curr_state
                break

            if depth >= depth_limit:
                continue

            for action, next_state, cost in reversed(board.get_successors(curr_state)):
                if next_state not in visited_at_depth or depth + 1 < visited_at_depth[next_state]:
                    visited_at_depth[next_state] = depth + 1
                    parent_map[next_state] = (curr_state, action, cost)
                    stack.append((next_state, depth + 1))

        if solved and goal_state:
            search_time = time.perf_counter() - start_time
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            actions, states, total_cost = reconstruct_path(parent_map, goal_state)
            return SearchResult(
                algorithm="DFS/IDS",
                solved=True,
                actions=actions,
                states_path=states,
                expanded_nodes=total_expanded,
                solution_length=len(actions),
                total_cost=total_cost,
                search_time=search_time,
                peak_memory_kb=peak_mem / 1024.0
            )

    search_time = time.perf_counter() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return SearchResult(
        algorithm="DFS/IDS",
        solved=False,
        actions=[],
        states_path=[],
        expanded_nodes=total_expanded,
        solution_length=0,
        total_cost=0.0,
        search_time=search_time,
        peak_memory_kb=peak_mem / 1024.0
    )

