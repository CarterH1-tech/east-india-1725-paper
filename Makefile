.PHONY: all pdf clean install check

all: pdf

pdf: paper.pdf

paper.pdf: paper.md build.py
	python3 build.py paper.md paper.pdf

# Fallback for Windows Python launcher
pdf-win: paper.pdf

install:
	python3 -m pip install -r requirements.txt

check:
	python3 build.py paper.md paper.pdf

clean:
	rm -f paper.pdf
