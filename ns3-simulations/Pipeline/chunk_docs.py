from pathlib import Path

IN = Path("dataset/rag_docs")
OUT = Path("dataset/rag_chunks")
OUT.mkdir(exist_ok=True)

for file in IN.iterdir():
    text = file.read_text()
    parts = text.split("\n\n")

    for i, p in enumerate(parts):
        (OUT / f"{file.stem}_{i}.txt").write_text(p)
