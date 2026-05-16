from src.reports.metrics import calculate_metrics


def test_empty_metrics():
    metrics = calculate_metrics([])
    assert metrics["total_trades"] == 0
    assert metrics["win_rate"] == 0.0

