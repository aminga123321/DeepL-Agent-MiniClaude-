"""
性能压测脚本
"""

import time
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))
from rerank import retrieve


def benchmark_retrieval(queries: List[str], num_runs: int = 10):
    """
    压测检索性能
    """
    print("="*60)
    print("检索性能压测")
    print("="*60)
    
    latencies = []
    
    for i, query in enumerate(queries * num_runs):
        print(f"\r正在运行: {i+1}/{len(queries)*num_runs}", end="")
        
        start = time.time()
        try:
            retrieve(query, top_k=5)
            latency = (time.time() - start) * 1000
            latencies.append(latency)
        except Exception as e:
            print(f"\n错误: {e}")
    
    print("\n\n" + "="*60)
    print("压测结果")
    print("="*60)
    
    if latencies:
        import statistics
        print(f"总运行次数: {len(latencies)}")
        print(f"平均延迟: {statistics.mean(latencies):.2f} ms")
        print(f"中位数: {statistics.median(latencies):.2f} ms")
        print(f"最小延迟: {min(latencies):.2f} ms")
        print(f"最大延迟: {max(latencies):.2f} ms")
        
        if len(latencies) >= 2:
            print(f"标准差: {statistics.stdev(latencies):.2f} ms")
        
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        print(f"P95 延迟: {p95:.2f} ms")


def main():
    queries = [
        "什么是统一力位控制？",
        "机器人如何进行擦黑板任务？",
        "如何打开抽屉？",
        "力控制和位置控制的区别是什么？",
        "sim2real 是什么意思？",
    ]
    
    benchmark_retrieval(queries, num_runs=5)


if __name__ == "__main__":
    main()
