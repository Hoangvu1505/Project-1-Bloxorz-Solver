# HƯỚNG DẪN MÃ NGUỒN (SOURCE CODE) - BLOXORZ SOLVER - NHÓM 3 - LỚP CQ2024/23

## Giới thiệu thành viên nhóm

| STT | Họ và tên | MSSV | Vai trò / Phụ trách |
|:---:|:---|:---:|:---|
| 1 | Lương Nguyễn Hoàng Vũ | 24120493 | Trưởng nhóm |
| 2 | Huỳnh Chí Thoại | 24120457 | Thành viên |
| 3 | Trần Minh Tiến | 24120465 | Thành viên |
| 4 | Đỗ Trung Kiên | 24120341 | Thành viên |
| 5 | Lê Phạm Đăng Khiêm | 24120350 | Thành viên |

## 1. Cài đặt thư viện phụ thuộc
- **Yêu cầu môi trường:** Python >= 3.11 (khuyên dùng Python 3.11 hoặc 3.12)
- Đảm bảo đã kích hoạt môi trường ảo `.venv` tại thư mục dự án:
```bash
pip install -r requirements.txt
```

## 2. Cấu trúc Dự án
```
Source/
├── README.md                        # Hướng dẫn cài đặt, chạy chương trình và báo cáo
├── requirements.txt                 # Danh sách thư viện cần cài đặt
├── main.py                          # File khởi chạy chính của trò chơi
│
├── core/                            # Logic trò chơi
│   ├── __init__.py
│   ├── state.py                     # Cấu trúc trạng thái (vị trí, tư thế, cầu)
│   ├── board.py                     # Quản lý bản đồ, va chạm, kiểm tra thắng/thua
│   ├── transition.py                # Quy tắc chuyển trạng thái khi lăn khối
│   └── special_tiles.py             # Xử lý ô cam, cầu, công tắc và tách khối
│
├── solvers/                         # Các thuật toán tìm kiếm
│   ├── __init__.py
│   ├── base_solver.py               # Khung chung đo thời gian, bộ nhớ, số node
│   ├── bfs.py                       # Thuật toán BFS
│   ├── dfs.py                       # Thuật toán DFS / IDS
│   ├── ucs.py                       # Thuật toán UCS (hàm chi phí non-uniform)
│   ├── astar.py                     # Thuật toán A*
│   └── heuristics.py                # Các hàm heuristic cho A*
│
├── gui/                             # Giao diện đồ họa Pygame
│   ├── __init__.py
│   ├── app.py                       # Cửa sổ chính, menu và vòng lặp game
│   ├── renderer.py                  # Vẽ bàn cờ 2.5D, khối hộp và hiệu ứng
│   └── animator.py                  # Tự động diễn hoạt lại đường đi (Replay)
│
├── levels/                          # Dữ liệu các màn chơi (JSON)
│   ├── group1_basic/                # Màn chơi phẳng cơ bản
│   ├── group2_fragile/              # Màn chơi có ô cam dễ vỡ
│   ├── group3_switches/             # Màn chơi có công tắc và cầu
│   └── group4_complex/              # Màn chơi kết hợp (có tách khối)
│
└── benchmark/                       # Đo đạc thực nghiệm
    ├── run_benchmark.py             # Script chạy đo đạc tự động các thuật toán
    ├── plot_charts.py               # Script vẽ biểu đồ so sánh kết quả
    └── results/                     # Thư mục lưu bảng số liệu (CSV) và ảnh biểu đồ
```

## 3. Khởi chạy Giao diện Game (GUI Pygame)
Khởi chạy game từ thư mục `Source/`:
```bash
python main.py
```
*(Hoặc chạy từ thư mục gốc `Project1/`: `python Source/main.py`)*

**Phím tắt điều khiển trong Game:**
- **Mũi tên / W A S D**: Lăn khối Bloxorz.
- **Phím Space**: Chuyển đổi giữa 2 khối lập phương khi tách (Split).
- **Phím R**: Chơi lại màn hiện tại.
- **Phím N / P**: Chuyển nhanh sang màn Tiếp theo / Trước đó.
- **Phím F11 / F** (hoặc nhấn nút *"Toàn màn"*): Bật / Tắt chế độ Toàn màn hình (Fullscreen).
- **Phím ESC**: Quay lại Menu chính hoặc màn hình trước.

## 4. Chạy Thực nghiệm Đo đạc (Benchmark & Xuất Biểu đồ)
Chạy đo đạc tự động toàn bộ 24 màn chơi:
```bash
python benchmark/run_benchmark.py
```
*(Hoặc chạy từ thư mục gốc `Project1/`: `python Source/benchmark/run_benchmark.py`)*

Kết quả đo đạc sẽ tự động xuất ra thư mục `benchmark/results/`:
- Bảng Markdown: `benchmark/results/benchmark_results.md`
- Bảng CSV: `benchmark/results/benchmark_results.csv`
- Bảng số liệu: `benchmark/results/metrics.csv`
- 5 Biểu đồ PNG phân giải cao (Search Time, Peak Memory, Expanded Nodes, Solution Length, Dashboard).

Để vẽ lại biểu đồ từ dữ liệu CSV đã lưu:
```bash
python benchmark/plot_charts.py
```
*(Hoặc chạy từ thư mục gốc `Project1/`: `python Source/benchmark/plot_charts.py`)*

## 5. Chuẩn Interface Problem (Dùng chung cho tất cả Solvers)
Mọi thuật toán tìm kiếm (`BFS`, `DFS/IDS`, `UCS`, `A*`) đều kế thừa và tương tác đồng nhất qua interface của `BloxorzBoard` và `SearchResult`:
- **Initial State**: `board.get_initial_state() -> GameState`
- **Actions & Results**: `board.get_successors(state) -> List[Tuple[action: str, next_state: GameState, step_cost: float]]`
- **Goal Test**: `board.is_goal_state(state) -> bool` (khối đứng thẳng tại ô Goal)
- **Path Cost**: `step_cost` (1.0 cho sàn thường, 2.0 cho ô cam Fragile, 0.8 khi bật switch, 1.2 khi split cube)
- **Truy vết đường đi**: `reconstruct_path(parent_map, goal_state) -> (actions, states, total_cost)`
- **Kết quả trả về**: Data class `SearchResult` chứa 4 chỉ số hiệu năng: `search_time`, `peak_memory_kb`, `expanded_nodes`, `solution_length`.



