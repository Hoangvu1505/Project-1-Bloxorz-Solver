"""
Thuật toán tìm kiếm chi phí đồng nhất (Uniform-Cost Search - UCS).
"""

import time
import tracemalloc
import heapq
from typing import Dict, Tuple, Optional, List

from core.board import BloxorzBoard
from core.state import GameState
from solvers.base_solver import SearchResult, reconstruct_path


def solve_ucs(board: BloxorzBoard, use_weighted_cost: bool = True) -> SearchResult:
    """
    Thuật toán UCS.
    
    Đầu vào:
        board (BloxorzBoard): Bàn cờ Bloxorz cần giải quyết.
        use_weighted_cost (bool): 
            - True: Sử dụng chi phí theo luật (ô cam tốn nhiều chi phí hơn, ô công tắc giảm chi phí...).
            - False: Xem mỗi bước đi có chi phí bằng 1.0 (tương đương BFS tìm số bước ít nhất).
            
    Đầu ra:
        SearchResult: Đối tượng chứa đường đi tìm kiếm, thời gian, bộ nhớ đỉnh và số node đã duyệt.
    """
    # 1. Bắt đầu theo dõi tài nguyên hệ thống (RAM và thời gian)
    tracemalloc.start()
    start_time = time.perf_counter()

    initial_state = board.get_initial_state()

    # 2. Khởi tạo cấu trúc dữ liệu tìm kiếm
    # Hàng đợi ưu tiên (Priority Queue) lưu trữ tuple: (g_cost, counter, state)
    # Biến `counter` đóng vai trò tie-breaker (phá vỡ thế hòa khi g_cost bằng nhau),
    # tránh việc Python phải so sánh trực tiếp hai đối tượng GameState.
    counter = 0
    pq: List[Tuple[float, int, GameState]] = [(0.0, counter, initial_state)]
    
    # Bảng lưu chi phí đường đi tốt nhất (nhỏ nhất) từng tìm thấy tới mỗi trạng thái: {state: min_g_cost}
    best_cost: Dict[GameState, float] = {initial_state: 0.0}
    
    # Bảng băm lưu vết cha để tái tạo đường đi: {state: (parent_state, action, step_cost)}
    parent_map: Dict[GameState, Tuple[Optional[GameState], Optional[str], float]] = {
        initial_state: (None, None, 0.0)
    }

    expanded_nodes = 0
    solved = False
    goal_state = None

    # 3. Vòng lặp duyệt UCS
    while pq:
        # Lấy trạng thái có chi phí đường đi g(n) tích lũy nhỏ nhất hiện tại
        curr_g, _, curr_state = heapq.heappop(pq)

        # Kỹ thuật Lazy Deletion:
        # Nếu chi phí g của node này lớn hơn chi phí tốt nhất đã biết tới curr_state,
        # nghĩa là node này đã bị thay thế bởi một đường đi rẻ hơn trước đó -> Bỏ qua.
        if curr_g > best_cost.get(curr_state, float('inf')):
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
            new_g = curr_g + cost_to_add

            # Nếu tìm thấy một đường đi mới tới next_state với chi phí thấp hơn
            if new_g < best_cost.get(next_state, float('inf')):
                best_cost[next_state] = new_g
                parent_map[next_state] = (curr_state, action, cost_to_add)
                counter += 1
                heapq.heappush(pq, (new_g, counter, next_state))

    # 4. Thu thập chỉ số hiệu năng
    search_time = time.perf_counter() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 5. Đóng gói kết quả tìm kiếm
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


