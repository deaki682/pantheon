from delphi.selector import select_top


def test_select_top_default():
    ranked = [{"symbol": f"S{i}", "momentum": 0.5 - i * 0.01} for i in range(20)]
    out = select_top(ranked)
    assert len(out) == 10
    assert out[0]["symbol"] == "S0"


def test_select_top_custom_n():
    ranked = [{"symbol": f"S{i}", "momentum": 0.5 - i * 0.01} for i in range(20)]
    out = select_top(ranked, top_n=5)
    assert len(out) == 5
