"""
Thuật toán tìm kiếm theo chiều sâu (Depth-First Search - DFS).
"""

import time
import tracemalloc
from typing import Dict, Tuple, Optional, List, Set

from core.board import BloxorzBoard
from core.state import GameState
from solvers.base_solver import SearchResult, reconstruct_path


def solve_dfs(board: BloxorzBoard) -> SearchResult:
    """
    Thuật toán DFS.
    
    Đầu vào:
        board (BloxorzBoard): Bàn cờ Bloxorz cần giải quyết.
        
    Đầu ra:
        SearchResult: Đối tượng chứa đường đi tìm kiếm, thời gian, bộ nhớ đỉnh và số node đã duyệt.
    """
    # 1. Bắt đầu theo dõi tài nguyên hệ thống (RAM và thời gian)
    tracemalloc.start()
    start_time = time.perf_counter()

    initial_state = board.get_initial_state()

    # 2. Khởi tạo cấu trúc dữ liệu tìm kiếm
    # Ngăn xếp (Stack) lưu trữ tuple: (trạng thái hiện tại, trạng thái cha, hành động, chi phí bước)
    stack: List[Tuple[GameState, Optional[GameState], Optional[str], float]] = [
        (initial_state, None, None, 0.0)
    ]
    
    # Tập các trạng thái đã được lấy ra khỏi stack và mở rộng (Explored / Visited Set)
    visited: Set[GameState] = set()
    
    # Bảng băm lưu vết cha để tái tạo đường đi: {state: (parent_state, action, step_cost)}
    parent_map: Dict[GameState, Tuple[Optional[GameState], Optional[str], float]] = {}
    
    expanded_nodes = 0
    solved = False
    goal_state = None

    # 3. Vòng lặp duyệt DFS
    while stack:
        curr_state, parent_state, action, step_cost = stack.pop()

        # Bỏ qua nếu trạng thái này đã được mở rộng trước đó
        if curr_state in visited:
            continue

        # Đánh dấu trạng thái đã thăm và ghi nhận mối quan hệ cha - con vào parent_map
        visited.add(curr_state)
        parent_map[curr_state] = (parent_state, action, step_cost)
        expanded_nodes += 1

        # Kiểm tra điều kiện đích (Goal Test khi node được lấy ra mở rộng)
        if board.is_goal_state(curr_state):
            solved = True
            goal_state = curr_state
            break

        # Sinh các trạng thái kế tiếp và đẩy vào stack
        # Sử dụng reversed(...) để giữ thứ tự duyệt tự nhiên (UP -> DOWN -> LEFT -> RIGHT)
        for act, next_st, cost in reversed(board.get_successors(curr_state)):
            if next_st not in visited:
                stack.append((next_st, curr_state, act, cost))

    # 4. Thu thập chỉ số hiệu năng
    search_time = time.perf_counter() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 5. Đóng gói kết quả tìm kiếm
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


