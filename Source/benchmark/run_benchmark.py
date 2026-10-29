"""Kịch bản tự động đo đạc hiệu năng các thuật toán tìm kiếm trên các màn chơi.

Chạy từ thư mục gốc dự án:
    python benchmark/run_benchmark.py

Kết quả đầu ra lưu tại benchmark/results/:
    - benchmark_results.md : Bảng kết quả định dạng Markdown.
    - benchmark_results.csv: Dữ liệu kết quả đo đạc.
    - metrics.csv          : Bảng số liệu phục vụ báo cáo DOCX.
    - 5 biểu đồ PNG        : Search Time, Peak Memory, Expanded Nodes, Solution Length, Dashboard.
"""

import os
import sys
import glob
from typing import Any, Callable, Dict, List, Tuple

source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from benchmark.plot_charts import plot_benchmark_charts
from core.board import BloxorzBoard
from solvers import SearchResult, solve_astar, solve_bfs, solve_dfs, solve_ucs


def discover_stage_files(base_levels_dir: str) -> List[str]:
    """Tìm kiếm danh sách đường dẫn các file JSON màn chơi theo thứ tự.

    Args:
        base_levels_dir: Thư mục gốc chứa các thư mục con nhóm màn chơi (levels/).

    Returns:
        Danh sách đường dẫn các file stage_*.json đã sắp xếp.
    """
    stage_files = sorted(glob.glob(os.path.join(base_levels_dir, "*", "stage_*.json")))
    if not stage_files:
        stage_files = sorted(glob.glob(os.path.join(source_dir, "stages", "stage_*.json")))
    return [f for f in stage_files if os.path.exists(f) and os.path.getsize(f) > 0]


def export_benchmark_results(
    results: Dict[str, Dict[str, SearchResult]],
    stage_names: List[str],
    algo_names: List[str],
    results_dir: str,
) -> Tuple[str, str, str]:
    """Xuất kết quả đo đạc ra file Markdown và CSV (cùng metrics.csv cho báo cáo).

    Args:
        results: Từ điển lưu kết quả SearchResult theo cấu trúc [stage_name][algo_name].
        stage_names: Danh sách tên màn chơi đã đánh giá.
        algo_names: Danh sách tên thuật toán đã chạy.
        results_dir: Thư mục lưu kết quả xuất ra.

    Returns:
        Tuple chứa đường dẫn tới 3 file: (benchmark_results.md, benchmark_results.csv, metrics.csv).
    """
    os.makedirs(results_dir, exist_ok=True)

    md_path = os.path.join(results_dir, "benchmark_results.md")
    csv_path = os.path.join(results_dir, "benchmark_results.csv")
    metrics_path = os.path.join(results_dir, "metrics.csv")

    # 1. Ghi bảng kết quả Markdown
    with open(md_path, "w", encoding="utf-8") as f_md:
        f_md.write("# BẢNG TỔNG HỢP KẾT QUẢ THỰC NGHIỆM THUẬT TOÁN (BLOXORZ SOLVER)\n\n")
        f_md.write("| Màn chơi | Thuật toán | Trạng thái | Thời gian (ms) | Bộ nhớ đỉnh (KB) | Số node mở rộng | Chiều dài lời giải (bước) |\n")
        f_md.write("|:---|:---|:---:|:---:|:---:|:---:|:---:|\n")

        for s_name in stage_names:
            for algo in algo_names:
                res = results[s_name][algo]
                status = "Thành công" if res.solved else "Thất bại"
                t_ms = f"{res.search_time * 1000:.2f}"
                m_kb = f"{res.peak_memory_kb:.2f}"
                # Phân biệt lần chạy thất bại: không dùng 0 thay cho số bước khi chưa giải được
                sol_len_str = str(res.solution_length) if res.solved else "N/A"
                f_md.write(f"| {s_name} | {algo} | {status} | {t_ms} | {m_kb} | {res.expanded_nodes} | {sol_len_str} |\n")

    # 2. Chuẩn bị dữ liệu CSV chuẩn cho benchmark_results.csv và metrics.csv
    csv_header = "Stage,Algorithm,Solved,SearchTime_ms,PeakMemory_KB,ExpandedNodes,SolutionLength\n"
    csv_lines = [csv_header]

    for s_name in stage_names:
        for algo in algo_names:
            res = results[s_name][algo]
            t_ms = f"{res.search_time * 1000:.2f}"
            m_kb = f"{res.peak_memory_kb:.2f}"
            sol_len_val = str(res.solution_length) if res.solved else "N/A"
            csv_lines.append(f'"{s_name}","{algo}",{res.solved},{t_ms},{m_kb},{res.expanded_nodes},{sol_len_val}\n')

    # Xuất benchmark_results.csv
    with open(csv_path, "w", encoding="utf-8") as f_csv:
        f_csv.writelines(csv_lines)

    # Xuất metrics.csv từ cùng dữ liệu đo thực tế, phục vụ số liệu báo cáo DOCX
    with open(metrics_path, "w", encoding="utf-8") as f_met:
        f_met.writelines(csv_lines)

    return md_path, csv_path, metrics_path


def run_all_benchmarks() -> None:
    """Điều phối toàn bộ quá trình chạy thực nghiệm, xuất dữ liệu và vẽ biểu đồ."""
    base_levels_dir = os.path.join(source_dir, "levels")
    stage_files = discover_stage_files(base_levels_dir)

    if not stage_files:
        print("[LỖI] Không tìm thấy file màn chơi nào!")
        return

    algorithms: List[Tuple[str, Callable[[BloxorzBoard], SearchResult]]] = [
        ("BFS", lambda b: solve_bfs(b)),
        ("DFS", lambda b: solve_dfs(b)),
        ("UCS", lambda b: solve_ucs(b, use_weighted_cost=True)),
        ("A*", lambda b: solve_astar(b, use_weighted_cost=True)),
    ]

    results: Dict[str, Dict[str, SearchResult]] = {}
    stage_names: List[str] = []

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
            sol_len_str = str(res.solution_length) if res.solved else "N/A"
            print(f"{algo_name:<12} | {status:<10} | {t_ms:<15} | {m_kb:<13} | {res.expanded_nodes:<15} | {sol_len_str:<10}")

    print("=" * 105)
    print("HOÀN TẤT ĐO ĐẠC! TIẾN HÀNH XUẤT BẢNG SỐ LIỆU VÀ VẼ BIỂU ĐỒ...")
    print("=" * 105)

    # Thư mục lưu kết quả benchmark
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    algo_keys = [a[0] for a in algorithms]

    md_path, csv_path, metrics_path = export_benchmark_results(results, stage_names, algo_keys, results_dir)
    print(f"[OK] Đã lưu bảng Markdown vào: {md_path}")
    print(f"[OK] Đã lưu bảng CSV vào: {csv_path}")
    print(f"[OK] Đã xuất file metrics cho báo cáo: {metrics_path}")

    # Gọi hàm vẽ biểu đồ có sẵn
    plot_benchmark_charts(results, stage_names, algo_keys, results_dir)


if __name__ == "__main__":
    run_all_benchmarks()
