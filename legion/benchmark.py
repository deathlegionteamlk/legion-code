import time
import statistics
from datetime import datetime


class Benchmark:
    def __init__(self):
        self.results = {}

    def measure_latency(self, func, args=None, kwargs=None, iterations: int = 10, warmup: int = 3) -> dict:
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        for _ in range(warmup):
            func(*args, **kwargs)
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        name = getattr(func, "__name__", str(func))
        result = {
            "name": name,
            "iterations": iterations,
            "warmup": warmup,
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "total": sum(times),
            "ops_per_sec": iterations / sum(times) if sum(times) > 0 else 0,
        }
        self.results[name] = result
        return result

    def measure_throughput(self, func, data_items: list, batch_size: int = 1) -> dict:
        times = []
        total_items = len(data_items)
        start = time.perf_counter()
        for i in range(0, total_items, batch_size):
            batch = data_items[i:i+batch_size]
            func(batch)
        elapsed = time.perf_counter() - start
        name = getattr(func, "__name__", str(func))
        result = {
            "name": name,
            "total_items": total_items,
            "batch_size": batch_size,
            "elapsed": elapsed,
            "items_per_sec": total_items / elapsed if elapsed > 0 else 0,
            "batches_per_sec": (total_items / batch_size) / elapsed if elapsed > 0 else 0,
        }
        self.results[f"{name}_throughput"] = result
        return result

    def compare_models(self, funcs: list, args=None, kwargs=None, iterations: int = 5) -> list:
        results = []
        for func in funcs:
            r = self.measure_latency(func, args, kwargs, iterations=iterations, warmup=2)
            results.append(r)
        results.sort(key=lambda x: x["mean"])
        return results

    def generate_report(self) -> str:
        lines = [f"# Benchmark Report", f"Generated: {datetime.now().isoformat()}", ""]
        for name, result in sorted(self.results.items()):
            lines.append(f"## {name}")
            for key, value in result.items():
                if key != "name":
                    lines.append(f"- **{key}**: {value}")
            lines.append("")
        return "\n".join(lines)

    def clear(self):
        self.results.clear()