"""Generate every figure used in paper/ (run via `make figures`)."""

from pathlib import Path

import numpy as np

from ai_for_rd.plotting import figure, save

FIGURES_DIR = Path(__file__).resolve().parent.parent / "paper" / "figures"


def example_figure() -> Path:
    """Placeholder figure: replace with a real result."""
    x = np.linspace(0, 10, 200)
    fig, ax = figure(width_frac=0.7)
    ax.plot(x, np.sin(x), label="baseline")
    ax.plot(x, np.sin(x) * np.exp(-x / 8), label="proposed")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Score")
    ax.legend(frameon=False)
    return save(fig, FIGURES_DIR / "example.pdf")


def main() -> None:
    for make in (example_figure,):
        print(f"wrote {make()}")


if __name__ == "__main__":
    main()
