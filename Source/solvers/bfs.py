"""
Thuật toán tìm kiếm theo chiều rộng (Breadth-First Search - BFS).
"""

import time
import tracemalloc
from collections import deque
from typing import Dict, Tuple, Optional, List, Set

from core.board import BloxorzBoard
from core.state import GameState
from solvers.base_solver import SearchResult, reconstruct_path


def solve_bfs(board: BloxorzBoard) -> SearchResult:
    """
    Thuật toán BFS.

    Đầu vào:
        board (BloxorzBoard): Bàn cờ Bloxorz cần giải quyết.

    Đầu ra:
        SearchResult: Đối tượng chứa đường đi tìm kiếm, thời gian, bộ nhớ đỉnh và số node đã duyệt.
    """
    # 1. Bắt đầu theo dõi tài nguyên hệ thống (RAM và thời gian)
    tracemalloc.start()
    start_time = time.perf_counter()

    initial_state = board.get_initial_state()

    # Kiểm tra nhanh nếu trạng thái bắt đầu đã là đích
    if board.is_goal_state(initial_state):
        _, peak_mem = tracemalloc.get_traced_memory()
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

    # 2. Khởi tạo cấu trúc dữ liệu tìm kiếm
    # Hàng đợi (Queue - FIFO) lưu trữ các trạng thái chờ mở rộng
    queue: deque[GameState] = deque([initial_state])

    # Tập các trạng thái đã ghé thăm (Visited Set) để tránh lặp chu kỳ
    visited: Set[GameState] = {initial_state}

    # Bảng băm lưu vết cha để tái tạo đường đi: {state: (parent_state, action, step_cost)}
    parent_map: Dict[GameState, Tuple[Optional[GameState], Optional[str], float]] = {
        initial_state: (None, None, 0.0)
    }

    expanded_nodes = 0
    solved = False
    goal_state: Optional[GameState] = None

    # 3. Vòng lặp duyệt BFS
    while queue:
        curr_state = queue.popleft()
        expanded_nodes += 1

        # Mở rộng các trạng thái kế tiếp từ curr_state
        for action, next_state, cost in board.get_successors(curr_state):
            if next_state not in visited:
                visited.add(next_state)
                parent_map[next_state] = (curr_state, action, cost)

                # Kiểm tra đích sớm ngay khi sinh node (Goal Test chuẩn BFS theo giáo trình AIMA)
                if board.is_goal_state(next_state):
                    solved = True
                    goal_state = next_state
                    break

                queue.append(next_state)

        if solved:
            break

    # 4. Thu thập chỉ số hiệu năng
    search_time = time.perf_counter() - start_time
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 5. Đóng gói kết quả tìm kiếm
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