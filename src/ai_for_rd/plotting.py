"""Helpers for producing figures that match the paper's typography."""

from pathlib import Path

import matplotlib.pyplot as plt

# Width of the text column in paper/main.tex (article class, 1in margins), in inches.
TEXT_WIDTH_IN = 6.5

PAPER_RC = {
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 9,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,  # embed TrueType fonts; arXiv rejects Type 3 fonts in some cases
}


def figure(width_frac: float = 1.0, aspect: float = 0.62):
    """Create a figure sized as a fraction of the text width.

    Draw at the final printed size so fonts in the PDF match the paper body.
    """
    plt.rcParams.update(PAPER_RC)
    width = TEXT_WIDTH_IN * width_frac
    return plt.subplots(figsize=(width, width * aspect))


def save(fig, path: str | Path) -> Path:
    """Save a figure as vector PDF, creating the parent directory if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path
