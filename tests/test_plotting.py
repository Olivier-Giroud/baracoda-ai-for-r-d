from ai_for_rd.plotting import TEXT_WIDTH_IN, figure, save


def test_figure_width_matches_text_width():
    fig, _ = figure(width_frac=0.5)
    assert fig.get_size_inches()[0] == TEXT_WIDTH_IN * 0.5


def test_save_writes_pdf(tmp_path):
    fig, ax = figure()
    ax.plot([0, 1], [0, 1])
    out = save(fig, tmp_path / "sub" / "fig.pdf")
    assert out.read_bytes().startswith(b"%PDF")
