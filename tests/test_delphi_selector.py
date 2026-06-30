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


def test_select_top_with_vetoes():
    ranked = [{"symbol": f"S{i}", "momentum": 0.5 - i * 0.01} for i in range(20)]
    out = select_top(ranked, top_n=3, vetoes={"S0", "S2"})
    assert len(out) == 3
    assert out[0]["symbol"] == "S1"
    assert out[1]["symbol"] == "S3"
    assert out[2]["symbol"] == "S4"


def test_select_top_vetoes_backfills():
    ranked = [{"symbol": f"S{i}", "momentum": 0.5 - i * 0.01} for i in range(20)]
    out = select_top(ranked, top_n=10, vetoes={"S0", "S1"})
    assert len(out) == 10
    assert out[0]["symbol"] == "S2"
    assert out[-1]["symbol"] == "S11"


def test_select_top_empty_vetoes():
    ranked = [{"symbol": f"S{i}", "momentum": 0.5 - i * 0.01} for i in range(20)]
    out = select_top(ranked, vetoes=set())
    assert len(out) == 10
    assert out[0]["symbol"] == "S0"
