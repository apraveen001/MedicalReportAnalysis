#!/usr/bin/env python3
"""
pdf_to_txt.py

Usage:
    python pdf_to_txt.py path/to/input.pdf

This script will:
  1. Convert each page of the input PDF to an image
  2. Send each image through the Gemma OCR model
  3. Concatenate all OCR’d text
  4. Save the result (overwriting) into text.txt in the current directory
"""

import os
import argparse
from pdf2image import convert_from_path
from gemma import GemmaClient   # replace with your actual Gemma SDK import

def ocr_with_gemma(image):
    """
    Send a PIL image to Gemma OCR and return the recognized text.
    Requires GEMMA_API_KEY in environment.
    """
    client = GemmaClient(api_key=os.getenv("GEMMA_API_KEY"))
    result = client.ocr(image)
    return result.text

def main():
    parser = argparse.ArgumentParser(
        description="OCR a PDF using Gemma and save output to text.txt"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to OCR"
    )
    parser.add_argument(
        "--dpi", "-d",
        type=int,
        default=300,
        help="Resolution for PDF→image conversion (default: 300)"
    )
    args = parser.parse_args()

    # verify API key
    if not os.getenv("GEMMA_API_KEY"):
        raise RuntimeError("Please set the GEMMA_API_KEY environment variable.")

    # convert PDF pages to images
    pages = convert_from_path(args.pdf_path, dpi=args.dpi)

    # OCR each page and accumulate text
    full_text = []
    for i, page in enumerate(pages, start=1):
        print(f"OCRing page {i}/{len(pages)}...")
        page_text = ocr_with_gemma(page)
        full_text.append(page_text)

    # write all OCR’d text to text.txt (in the current branch)
    output_path = "text.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(full_text))

    print(f"✅ OCR complete. Output saved to {output_path}")

if __name__ == "__main__":
    main()
