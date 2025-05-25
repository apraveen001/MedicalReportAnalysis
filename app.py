#!/usr/bin/env python3
"""
app.py

1. Prompts you to select a PDF.
2. Renders each page via PyMuPDF.
3. OCRs each page with your local Gemma3 vision model (via Ollama CLI).
4. Feeds the concatenated OCR text into the “generate” logic:
   • Explains the report in plain‐English bullet points.
   • Enters an interactive Q&A loop on the report.
"""

import os
import sys
import shutil
import subprocess
import tempfile
import textwrap
from tkinter import Tk, filedialog, messagebox

import fitz      # pip install pymupdf
import ollama    # pip install ollama

# ——————————————————————————————————————————————————————————————
# CONFIG
# ——————————————————————————————————————————————————————————————
OCR_MODEL = "gemma3:12b"  # vision-enabled Gemma3 model; pull with `ollama pull gemma3:12b`

# ——————————————————————————————————————————————————————————————
# Initialization / Model Setup
# ——————————————————————————————————————————————————————————————
def initialize_chatbot():
    """Ensure Ollama is running and the OCR model is available locally."""
    try:
        ollama.list()
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        print("Make sure Ollama is running (`ollama serve`).")
        sys.exit(1)

    try:
        ollama.show(OCR_MODEL)
    except ollama.ResponseError:
        print(f"Pulling model {OCR_MODEL} (this may take a minute)...")
        ollama.pull(OCR_MODEL)

# ——————————————————————————————————————————————————————————————
# OCR Logic
# ——————————————————————————————————————————————————————————————
def ocr_pdf(pdf_path: str) -> str:
    """
    Render each page of `pdf_path` to a PNG via PyMuPDF, then call:
        ollama run <OCR_MODEL> "Extract the text from this image: <path>"
    Collects and returns the concatenated OCR text.
    """
    doc = fitz.open(pdf_path)
    texts: list[str] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=300)
            img_path = os.path.join(tmpdir, f"page_{i}.png")
            pix.save(img_path)
            print(f"OCRing page {i}/{len(doc)} with {OCR_MODEL}…")
            prompt = f"Extract the text from this image: {img_path}"
            proc = subprocess.run(
                ["ollama", "run", OCR_MODEL, prompt],
                capture_output=True,
                text=True
            )
            if proc.returncode != 0:
                print(f"⚠️ OCR failed on {img_path}:\n{proc.stderr}")
                texts.append("")  
            else:
                out = proc.stdout.strip()
                if not out:
                    print(f"⚠️ Warning: page {i} returned blank.")
                texts.append(out)
    return "\n\n".join(texts)

# ——————————————————————————————————————————————————————————————
# “Generate” Logic (original generate.py, adapted)
# ——————————————————————————————————————————————————————————————
def explain_report(report_text: str) -> str:
    prompt = f"""
Here is a medical lab report:

{report_text}

Please explain this report in simple, non-medical terms that a normal person can understand.
Focus on:
1. The patient's overall health based on the results
2. Any values that are outside normal ranges and what that might mean
3. General advice based on the results
4. Whether they should consult a doctor about any specific results

Organize your response in clear sections with headings.
Use bullet points for easy reading.
Be reassuring but honest about any concerns.
"""
    resp = ollama.generate(
        model=OCR_MODEL,
        prompt=prompt,
        options={"temperature": 0.3}
    )
    return resp["response"]

def answer_question(report_text: str, question: str) -> str:
    prompt = f"""
Here is a medical lab report:

{report_text}

The user asks: {question}

Please answer this question in simple, non-medical terms that a normal person can understand.
If the question requires medical expertise beyond explaining the report, say "You should consult your doctor about this."
Be accurate but use simple language.
"""
    resp = ollama.generate(
        model=OCR_MODEL,
        prompt=prompt,
        options={"temperature": 0.3}
    )
    return resp["response"]

# ——————————————————————————————————————————————————————————————
# UI Helpers
# ——————————————————————————————————————————————————————————————
def prompt_open_pdf() -> str:
    root = Tk(); root.withdraw()
    path = filedialog.askopenfilename(
        title="Select PDF to OCR",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    root.destroy()
    if not path:
        print("No PDF selected. Exiting."); sys.exit(0)
    return path

# ——————————————————————————————————————————————————————————————
# Main Entrypoint
# ——————————————————————————————————————————————————————————————
def main():
    # 0) Ensure Ollama CLI is on PATH
    if shutil.which("ollama") is None:
        messagebox.showerror("Error", "Ollama CLI not found. Install from https://ollama.com/")
        sys.exit(1)

    # 1) Prompt for PDF
    pdf_path = prompt_open_pdf()

    # 2) Initialize Ollama + pull model if needed
    initialize_chatbot()

    # 3) OCR the PDF
    report_text = ocr_pdf(pdf_path)

    # 4) Generate easy-to-understand summary
    print("\nGenerating plain-language summary...\n")
    summary = explain_report(report_text)
    print(textwrap.fill(summary, width=80), "\n")

    # 5) Interactive Q&A
    print("You can now ask questions about your report (type 'quit' to exit).")
    while True:
        q = input("\nWhat would you like to know? ").strip()
        if q.lower() in ("quit", "exit", "q"):
            break
        if not q:
            continue
        print("\nThinking...\n")
        ans = answer_question(report_text, q)
        print(textwrap.fill(ans, width=80))

if __name__ == "__main__":
    main()
