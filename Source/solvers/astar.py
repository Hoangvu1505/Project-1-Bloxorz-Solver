"""
Thuật toán tìm kiếm A* (A* Search).
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
    """
    Thuật toán A*.

    Đầu vào:
        board (BloxorzBoard): Bàn cờ Bloxorz cần giải quyết.
        heuristic_func: Hàm heuristic h(state, goal_pos). Mặc định dùng heuristic_bloxorz.
        use_weighted_cost (bool):
            - True: Sử dụng chi phí theo luật (ô cam tốn nhiều chi phí hơn, ô công tắc giảm chi phí...).
            - False: Xem mỗi bước đi có chi phí bằng 1.0.

    Đầu ra:
        SearchResult: Đối tượng chứa đường đi tìm kiếm, thời gian, bộ nhớ đỉnh và số node đã duyệt.
    """
    if heuristic_func is None:
        heuristic_func = heuristic_bloxorz

    # 1. Bắt đầu theo dõi tài nguyên hệ thống (RAM và thời gian)
    tracemalloc.start()
    start_time = time.perf_counter()

    initial_state = board.get_initial_state()
    h_init = heuristic_func(initial_state, board.goal_pos)

    # 2. Khởi tạo cấu trúc dữ liệu tìm kiếm
    # Hàng đợi ưu tiên (Priority Queue - Min Heap) lưu trữ tuple: (f_score, g_cost, counter, state)
    # f_score = g_cost + h_val là tiêu chí ưu tiên chính.
    # Biến `counter` đóng vai trò tie-breaker (phá vỡ thế hòa khi f và g bằng nhau),
    # tránh so sánh trực tiếp hai đối tượng GameState.
    counter = 0
    pq: List[Tuple[float, float, int, GameState]] = [(h_init, 0.0, counter, initial_state)]

    # Bảng lưu chi phí g(n) tốt nhất từng tìm thấy tới mỗi trạng thái: {state: min_g_cost}
    g_score: Dict[GameState, float] = {initial_state: 0.0}

    # Bảng băm lưu vết cha để tái tạo đường đi: {state: (parent_state, action, step_cost)}
    parent_map: Dict[GameState, Tuple[Optional[GameState], Optional[str], float]] = {
        initial_state: (None, None, 0.0)
    }

    expanded_nodes = 0
    solved = False
    goal_state = None

    # 3. Vòng lặp duyệt A*
    while pq:
        curr_f, curr_g, _, curr_state = heapq.heappop(pq)

        # Kỹ thuật Lazy Deletion:
        # Nếu chi phí g của node lấy ra lớn hơn chi phí tốt nhất đã biết tới curr_state,
        # nghĩa là node này đã bị thay thế bởi một đường đi rẻ hơn trước đó -> Bỏ qua.
        if curr_g > g_score.get(curr_state, float('inf')):
            continue

        expanded_nodes += 1

        # Kiểm tra điều kiện đích (Bắt buộc kiểm tra tại thời điểm lấy ra khỏi priority queue)
        if board.is_goal_state(curr_state):
            solved = True
            goal_state = curr_state
            break

        # Mở rộng các trạng thái kế tiếp từ curr_state
        for action, next_state, step_cost in board.get_successors(curr_state):
            cost_to_add = step_cost if use_weighted_cost else 1.0
            tentative_g = curr_g + cost_to_add

            # Nếu tìm thấy một đường đi mới tới next_state với chi phí g(n) thấp hơn
            if tentative_g < g_score.get(next_state, float('inf')):
                g_score[next_state] = tentative_g
                h_val = heuristic_func(next_state, board.goal_pos)
                f_val = tentative_g + h_val
                parent_map[next_state] = (curr_state, action, cost_to_add)
                counter += 1
                heapq.heappush(pq, (f_val, tentative_g, counter, next_state))

    # 4. Thu thập chỉ số hiệu năng
    search_time = time.perf_counter() - start_time
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 5. Đóng gói kết quả tìm kiếm
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


