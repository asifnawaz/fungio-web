from mycelium.bench import benchmark, format_rows


def test_benchmark_runs_and_finds_families():
    rows = benchmark(n=2000, queries=20, kinds=["numpy"])
    assert rows[0]["right_family"] == 1.0
    assert "numpy" in format_rows(rows, 2000)
