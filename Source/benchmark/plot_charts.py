"""
Tự động vẽ các biểu đồ so sánh hiệu năng bằng Matplotlib.
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt
import numpy as np


def plot_benchmark_charts(results: dict, stage_names: list, algo_keys: list, output_dir: str):
    """Vẽ và lưu các biểu đồ so sánh hiệu năng vào thư mục output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    labels = [f"Màn {i+1}" for i in range(len(stage_names))]
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#2BA84A']  # Xanh dương, Tím sen, Cam, Xanh lục
    x = np.arange(len(labels))
    width = 0.2

    # 1. Biểu đồ Thời gian tìm kiếm (ms)
    plt.figure(figsize=(12, 6))
    for i, algo in enumerate(algo_keys):
        times = [results[s][algo].search_time * 1000 for s in stage_names]
        plt.bar(x + (i - 1.5) * width, times, width, label=algo, color=colors[i])
    plt.xlabel('Màn chơi (Stages)', fontsize=12, fontweight='bold')
    plt.ylabel('Thời gian tìm kiếm (ms)', fontsize=12, fontweight='bold')
    plt.title('So sánh Thời gian Tìm kiếm giữa các Thuật toán (Search Time)', fontsize=14, fontweight='bold')
    plt.xticks(x, labels, fontsize=9, rotation=45, ha='right')
    plt.legend(fontsize=11)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_search_time.png"), dpi=300)
    plt.close()

    # 2. Biểu đồ Bộ nhớ tiêu thụ đỉnh (KB)
    plt.figure(figsize=(12, 6))
    for i, algo in enumerate(algo_keys):
        mems = [results[s][algo].peak_memory_kb for s in stage_names]
        plt.bar(x + (i - 1.5) * width, mems, width, label=algo, color=colors[i])
    plt.xlabel('Màn chơi (Stages)', fontsize=12, fontweight='bold')
    plt.ylabel('Bộ nhớ tiêu thụ đỉnh (KB)', fontsize=12, fontweight='bold')
    plt.title('So sánh Bộ nhớ Tiêu thụ Đỉnh (Peak Memory Usage)', fontsize=14, fontweight='bold')
    plt.xticks(x, labels, fontsize=9, rotation=45, ha='right')
    plt.legend(fontsize=11)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_peak_memory.png"), dpi=300)
    plt.close()

    # 3. Biểu đồ Số nút mở rộng (Expanded Nodes)
    plt.figure(figsize=(12, 6))
    for i, algo in enumerate(algo_keys):
        nodes = [results[s][algo].expanded_nodes for s in stage_names]
        plt.bar(x + (i - 1.5) * width, nodes, width, label=algo, color=colors[i])
    plt.xlabel('Màn chơi (Stages)', fontsize=12, fontweight='bold')
    plt.ylabel('Số lượng Node mở rộng', fontsize=12, fontweight='bold')
    plt.title('So sánh Số lượng Node đã Mở rộng (Expanded Nodes)', fontsize=14, fontweight='bold')
    plt.xticks(x, labels, fontsize=9, rotation=45, ha='right')
    plt.legend(fontsize=11)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_expanded_nodes.png"), dpi=300)
    plt.close()

    # 4. Biểu đồ Chiều dài lời giải (Solution Length)
    plt.figure(figsize=(12, 6))
    for i, algo in enumerate(algo_keys):
        steps = [results[s][algo].solution_length for s in stage_names]
        plt.bar(x + (i - 1.5) * width, steps, width, label=algo, color=colors[i])
    plt.xlabel('Màn chơi (Stages)', fontsize=12, fontweight='bold')
    plt.ylabel('Số bước đi (Moves)', fontsize=12, fontweight='bold')
    plt.title('So sánh Chiều dài Lời giải (Solution Length)', fontsize=14, fontweight='bold')
    plt.xticks(x, labels, fontsize=9, rotation=45, ha='right')
    plt.legend(fontsize=11)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_solution_length.png"), dpi=300)
    plt.close()

    # 5. Biểu đồ Tổng hợp 4 trong 1 (Dashboard Summary)
    fig, axs = plt.subplots(2, 2, figsize=(16, 11))

    # 5.1 Thời gian
    for i, algo in enumerate(algo_keys):
        times = [results[s][algo].search_time * 1000 for s in stage_names]
        axs[0, 0].bar(x + (i - 1.5) * width, times, width, label=algo, color=colors[i])
    axs[0, 0].set_title('Thời gian Tìm kiếm (ms)', fontsize=12, fontweight='bold')

    # 5.2 Bộ nhớ
    for i, algo in enumerate(algo_keys):
        mems = [results[s][algo].peak_memory_kb for s in stage_names]
        axs[0, 1].bar(x + (i - 1.5) * width, mems, width, label=algo, color=colors[i])
    axs[0, 1].set_title('Bộ nhớ Tiêu thụ Đỉnh (KB)', fontsize=12, fontweight='bold')

    # 5.3 Nút mở rộng
    for i, algo in enumerate(algo_keys):
        nodes = [results[s][algo].expanded_nodes for s in stage_names]
        axs[1, 0].bar(x + (i - 1.5) * width, nodes, width, label=algo, color=colors[i])
    axs[1, 0].set_title('Số Node đã Mở rộng', fontsize=12, fontweight='bold')

    # 5.4 Số bước giải
    for i, algo in enumerate(algo_keys):
        steps = [results[s][algo].solution_length for s in stage_names]
        axs[1, 1].bar(x + (i - 1.5) * width, steps, width, label=algo, color=colors[i])
    axs[1, 1].set_title('Chiều dài Lời giải (Bước đi)', fontsize=12, fontweight='bold')

    for ax in axs.flat:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
        ax.legend(fontsize=9)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.suptitle('TỔNG HỢP SO SÁNH HIỆU NĂNG 4 THUẬT TOÁN TÌM KIẾM (BLOXORZ)', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_overall_comparison.png"), dpi=300)
    plt.close()

    print(f"[OK] Đã vẽ và lưu 5 biểu đồ vào: {output_dir}")


if __name__ == "__main__":
    import csv
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    res_dir = os.path.join(curr_dir, "results")
    csv_file = os.path.join(res_dir, "benchmark_results.csv")

    if not os.path.exists(csv_file):
        print(f"[LỖI] Không tìm thấy file {csv_file}. Vui lòng chạy run_benchmark.py trước!")
        exit(1)

    class DummyResult:
        def __init__(self, search_time, peak_memory_kb, expanded_nodes, solution_length):
            self.search_time = search_time
            self.peak_memory_kb = peak_memory_kb
            self.expanded_nodes = expanded_nodes
            self.solution_length = solution_length

    results = {}
    stage_names = []
    algo_keys = ["BFS", "DFS", "UCS", "A*"]

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            s_name = row["Stage"]
            algo = row["Algorithm"]
            if s_name not in results:
                results[s_name] = {}
                stage_names.append(s_name)

            t_val = row.get("SearchTime_ms", "0")
            m_val = row.get("PeakMemory_KB", "0")
            n_val = row.get("ExpandedNodes", "0")
            s_val = row.get("SolutionLength", "0")

            search_time = float(t_val) / 1000.0 if t_val not in ("N/A", "") else 0.0
            peak_memory_kb = float(m_val) if m_val not in ("N/A", "") else 0.0
            expanded_nodes = int(n_val) if n_val not in ("N/A", "") and n_val.isdigit() else 0
            solution_length = int(s_val) if s_val not in ("N/A", "") and s_val.isdigit() else 0

            results[s_name][algo] = DummyResult(
                search_time=search_time,
                peak_memory_kb=peak_memory_kb,
                expanded_nodes=expanded_nodes,
                solution_length=solution_length
            )

    plot_benchmark_charts(results, stage_names, algo_keys, res_dir)
