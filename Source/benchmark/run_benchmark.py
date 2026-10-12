"""
Kịch bản tự động đo đạc hiệu năng các thuật toán tìm kiếm trên các màn chơi.
"""

import os
import sys
import glob

source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from core.board import BloxorzBoard
from solvers import solve_bfs, solve_ids, solve_ucs, solve_astar, SearchResult
from benchmark.plot_charts import plot_benchmark_charts


#hàm cần code lại
def run_all_benchmarks():
    """Chạy thực nghiệm tự động đo đạc thời gian, bộ nhớ và số node duyệt."""
    base_levels_dir = os.path.join(source_dir, "levels")
    stage_files = sorted(glob.glob(os.path.join(base_levels_dir, "*", "stage_*.json")))

    if not stage_files:
        stage_files = sorted(glob.glob(os.path.join(source_dir, "stages", "stage_*.json")))


    if not stage_files:
        print("[LỖI] Không tìm thấy file màn chơi nào!")
        return

    algorithms = [
        ("BFS", lambda b: solve_bfs(b)),
        ("DFS/IDS", lambda b: solve_ids(b, max_limit=30)),
        ("UCS", lambda b: solve_ucs(b, use_weighted_cost=True)),
        ("A*", lambda b: solve_astar(b, use_weighted_cost=True))
    ]

    results = {}
    stage_names = []

    print("=" * 105)
    print("CHẠY THỰC NGHIỆM ĐÁNH GIÁ 4 THUẬT TOÁN TÌM KIẾM TRÊN CÁC MÀN CHƠI (LEVELS)")
    print("=" * 105)

    for s_path in stage_files:
        board = BloxorzBoard.load_from_file(s_path)
        group_name = os.path.basename(os.path.dirname(s_path))
        display_name = f"{board.name} [{group_name}]"
        stage_names.append(board.name)
        results[board.name] = {}

        print(f"\n>>> ĐANG ĐÁNH GIÁ: {board.name} ({group_name} / {os.path.basename(s_path)})")
        print("-" * 105)
        print(f"{'Thuật toán':<12} | {'Trạng thái':<10} | {'Thời gian (ms)':<15} | {'Bộ nhớ (KB)':<13} | {'Nodes mở rộng':<15} | {'Số bước':<10}")
        print("-" * 105)

        for algo_name, solver_fn in algorithms:
            res: SearchResult = solver_fn(board)
            results[board.name][algo_name] = res
            status = "Thành công" if res.solved else "Thất bại"
            t_ms = f"{res.search_time * 1000:.2f}"
            m_kb = f"{res.peak_memory_kb:.2f}"
            print(f"{algo_name:<12} | {status:<10} | {t_ms:<15} | {m_kb:<13} | {res.expanded_nodes:<15} | {res.solution_length:<10}")

    print("=" * 105)
    print("HOÀN TẤT ĐO ĐẠC! TIẾN HÀNH XUẤT BẢNG SỐ LIỆU VÀ VẼ BIỂU ĐỒ...")
    print("=" * 105)

    # Thư mục lưu kết quả benchmark
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)

    md_path = os.path.join(results_dir, "benchmark_results.md")
    csv_path = os.path.join(results_dir, "benchmark_results.csv")

    with open(md_path, "w", encoding="utf-8") as f_md, open(csv_path, "w", encoding="utf-8") as f_csv:
        f_csv.write("Stage,Algorithm,Solved,SearchTime_ms,PeakMemory_KB,ExpandedNodes,SolutionLength\n")
        f_md.write("# BẢNG TỔNG HỢP KẾT QUẢ THỰC NGHIỆM THUẬT TOÁN (BLOXORZ SOLVER)\n\n")
        f_md.write("| Màn chơi | Thuật toán | Trạng thái | Thời gian (ms) | Bộ nhớ đỉnh (KB) | Số node mở rộng | Chiều dài lời giải (bước) |\n")
        f_md.write("|:---|:---|:---:|:---:|:---:|:---:|:---:|\n")

        for s_name in stage_names:
            for algo_name, _ in algorithms:
                res = results[s_name][algo_name]
                status = "Thành công" if res.solved else "Thất bại"
                t_ms = f"{res.search_time * 1000:.2f}"
                m_kb = f"{res.peak_memory_kb:.2f}"
                f_md.write(f"| {s_name} | {algo_name} | {status} | {t_ms} | {m_kb} | {res.expanded_nodes} | {res.solution_length} |\n")
                f_csv.write(f'"{s_name}","{algo_name}",{res.solved},{t_ms},{m_kb},{res.expanded_nodes},{res.solution_length}\n')

    print(f"[OK] Đã lưu bảng Markdown vào: {md_path}")
    print(f"[OK] Đã lưu bảng CSV vào: {csv_path}")

    # Vẽ 5 biểu đồ lưu vào thư mục results/
    algo_keys = [a[0] for a in algorithms]
    plot_benchmark_charts(results, stage_names, algo_keys, results_dir)


if __name__ == "__main__":
    run_all_benchmarks()
