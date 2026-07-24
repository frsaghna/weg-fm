#!/usr/bin/env /usr/bin/python3
"""
Spike 1c: `fd` Traversal Responsiveness Benchmark.
Measures search latency over $HOME for different query patterns & depth options.
"""

import os
import sys
import time
import subprocess

def run_fd_query(query, search_path, extra_args=None):
    if extra_args is None:
        extra_args = []
    
    cmd = ["fd", "--hidden", "--exclude", ".git", "--exclude", "node_modules", "--exclude", ".cache"] + extra_args + [query, search_path]
    start = time.perf_counter()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    elapsed = (time.perf_counter() - start) * 1000 # ms

    lines = [l for l in res.stdout.splitlines() if l.strip()]
    return elapsed, len(lines), lines[:5]

def main():
    home = os.path.expanduser("~")
    print(f"=== Spike 1c: `fd` Search Traversal Benchmark on {home} ===")
    
    test_queries = ["proj", "config", "test", "doc", "main"]

    for q in test_queries:
        print(f"\n--- Query: '>{q}' ---")
        
        # 1. Standard depth-first default fd
        t_default, count_def, samples_def = run_fd_query(q, home)
        print(f"[Default fd]            Latency: {t_default:6.2f} ms | Results count: {count_def}")
        if samples_def:
            print("  Top samples:", samples_def[:2])

        # 2. Shallow depth tier (--max-depth 3)
        t_d3, count_d3, samples_d3 = run_fd_query(q, home, ["--max-depth", "3"])
        print(f"[Depth 3 Tier]          Latency: {t_d3:6.2f} ms | Results count: {count_d3}")

        # 3. Mid depth tier (--max-depth 5)
        t_d5, count_d5, samples_d5 = run_fd_query(q, home, ["--max-depth", "5"])
        print(f"[Depth 5 Tier]          Latency: {t_d5:6.2f} ms | Results count: {count_d5}")

    print("\nBenchmark finished.")

if __name__ == "__main__":
    main()
