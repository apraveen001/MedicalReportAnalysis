#!/usr/bin/env python3
"""
pdf_to_txt.py

1. Prompts you to pick a PDF.
2. Renders each page via PyMuPDF.
3. Calls Ollama’s Gemma3 Vision model with an inline prompt to OCR each page.
4. Aggregates and saves the output to a .txt file.
"""

import os
import sys
import shutil
import subprocess
import tempfile
from tkinter import Tk, filedialog, messagebox
import fitz  # PyMuPDF

DEFAULT_MODEL = "gemma3:12b"

def ocr_page_with_ollama(image_path: str, model: str) -> str:
    """
    Run Ollama CLI; the prompt must be the last positional argument.
    """
    prompt = f"Extract the text from this image: {image_path}"
    proc = subprocess.run(
        ["ollama", "run", model, prompt],
        capture_output=True,
        text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"OCR failed on {image_path}:\n{proc.stderr}")
    return proc.stdout.strip()

def prompt_open_pdf() -> str:
    root = Tk(); root.withdraw()
    path = filedialog.askopenfilename(
        title="Select PDF to OCR",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    root.destroy()
    if not path:
        print("No PDF selected—exiting."); sys.exit(0)
    return path

def prompt_save_txt(default: str) -> str:
    root = Tk(); root.withdraw()
    path = filedialog.asksaveasfilename(
        title="Save OCR output as",
        defaultextension=".txt",
        initialfile=default,
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    root.destroy()
    if not path:
        print("No output file chosen—exiting."); sys.exit(0)
    return path

def main():
    # 1) Check Ollama CLI
    if shutil.which("ollama") is None:
        messagebox.showerror("Error", "Ollama CLI not found. Install from https://ollama.com/")
        sys.exit(1)

    # 2) Pick PDF & output path
    pdf_path = prompt_open_pdf()
    out_txt = prompt_save_txt("text.txt")

    # 3) Confirm or override model
    model = DEFAULT_MODEL
    ans = input(f"Use Ollama model [{DEFAULT_MODEL}]? (y/n): ").strip().lower()
    if ans == "n":
        custom = input("Enter model (e.g. gemma3:12b): ").strip()
        if custom:
            model = custom

    # 4) Open PDF & render pages
    doc = fitz.open(pdf_path)
    print(f"PDF has {len(doc)} pages. Rendering at 300 dpi…")
    ocr_texts = []

    with tempfile.TemporaryDirectory() as tmp:
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=300)
            img = os.path.join(tmp, f"page_{i}.png")
            pix.save(img)
            print(f"OCRing page {i}/{len(doc)}…")
            text = ocr_page_with_ollama(img, model)
            if not text:
                print(f"⚠️  Warning: page {i} returned blank.")
            ocr_texts.append(text)

    # 5) Write to text file
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n\n".join(ocr_texts))

    print(f"\n✅ Done! OCR output saved to: {out_txt}")

if __name__ == "__main__":
    main()
