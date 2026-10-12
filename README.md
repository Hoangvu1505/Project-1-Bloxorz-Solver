# HƯỚNG DẪN MÃ NGUỒN (SOURCE CODE) - BLOXORZ SOLVER

## 1. Cài đặt thư viện phụ thuộc
Đảm bảo bạn đã kích hoạt môi trường ảo `.venv`:
```bash
pip install -r requirements.txt
```

## 2. Cấu trúc Mô-đun trong Source/
```
Source/
├── README.md                        # Hướng dẫn cài đặt và chạy chương trình
├── requirements.txt                 # Danh sách thư viện cần cài đặt
├── main.py                          # File khởi chạy chính của chương trình
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
├── gui/                             # Giao diện đồ họa
│   ├── __init__.py
│   ├── app.py                       # Cửa sổ chính, menu và vòng lặp game
│   ├── renderer.py                  # Vẽ bàn cờ, khối hộp và hiệu ứng
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
File `main.py` chuyên biệt cho việc chạy và trải nghiệm game:
```bash
python main.py
```
**Phím tắt điều khiển trong Game:**
- **Mũi tên / W A S D**: Lăn khối Bloxorz.
- **Phím Space**: Chuyển đổi giữa 2 khối lập phương khi tách (Split).
- **Phím R**: Chơi lại màn hiện tại.
- **Phím N / P**: Chuyển nhanh sang màn Tiếp theo / Trước đó.
- **Phím F11 / F** (hoặc nhấn nút *"Toàn màn"*): Bật / Tắt chế độ Toàn màn hình (Fullscreen).

## 4. Chạy Thực nghiệm Đo đạc (Benchmark & Xuất Biểu đồ)
Chạy trực tiếp file benchmark riêng:
```bash
python benchmark/run_benchmark.py
```
Kết quả đo đạc sẽ tự động xuất ra thư mục `benchmark/results/`:
- Bảng Markdown: `benchmark/results/benchmark_results.md`
- Bảng CSV: `benchmark/results/benchmark_results.csv`
- 5 Biểu đồ PNG phân giải cao (Search Time, Peak Memory, Expanded Nodes, Solution Length, Dashboard).

Để vẽ lại biểu đồ từ dữ liệu CSV đã lưu:
```bash
python benchmark/plot_charts.py
```
