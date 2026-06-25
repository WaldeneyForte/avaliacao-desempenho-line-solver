from pypdf import PdfReader

pdf_path = "docs/LINE-python.pdf"
md_path = "docs/manual_line.md"

reader = PdfReader(pdf_path)

with open(md_path, "w", encoding="utf-8") as f:
    f.write("# Manual do LINE Solver em texto\n\n")
    f.write("Este arquivo foi extraído do PDF oficial do LINE Solver para facilitar a consulta pelo Codex.\n\n")

    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        f.write(f"\n\n## Página {i}\n\n")
        f.write(text)

print(f"Manual extraído para {md_path}")