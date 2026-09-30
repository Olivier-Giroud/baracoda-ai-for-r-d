PYTHON ?= python3
PAPER_DIR := paper
BUILD_DIR := $(PAPER_DIR)/build
ARXIV_DIR := $(BUILD_DIR)/arxiv

.PHONY: figures paper arxiv test lint clean

figures:
	$(PYTHON) scripts/make_figures.py

paper: figures
	cd $(PAPER_DIR) && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex

# Package only what arXiv needs: sources, figures and the compiled .bbl.
arxiv: paper
	rm -rf $(ARXIV_DIR) && mkdir -p $(ARXIV_DIR)
	cp $(PAPER_DIR)/main.tex $(BUILD_DIR)/main.bbl $(ARXIV_DIR)/
	cp -r $(PAPER_DIR)/sections $(PAPER_DIR)/figures $(ARXIV_DIR)/
	rm -f $(ARXIV_DIR)/figures/.gitkeep
	tar -czf $(BUILD_DIR)/arxiv.tar.gz -C $(ARXIV_DIR) .
	@echo "arXiv package: $(BUILD_DIR)/arxiv.tar.gz"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src scripts tests

clean:
	rm -rf $(BUILD_DIR)
