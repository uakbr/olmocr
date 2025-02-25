#!/usr/bin/env python3
"""
A simple script to extract content from PDFs using olmocr components
without requiring GPU acceleration.
"""

import os
import sys
import json
import base64
import io
import subprocess
from pathlib import Path
import argparse
from typing import List, Dict, Any, Optional

# Import needed components from olmocr
from olmocr.data.renderpdf import render_pdf_to_base64png
from olmocr.check import check_poppler_version
import pypdf
from PIL import Image


def render_and_save_pdf_page(pdf_path: str, page_num: int, output_dir: str, target_longest_dim: int = 2000) -> str:
    """Render a PDF page to PNG and save it to disk"""
    # Render the page to base64 PNG
    base64_png = render_pdf_to_base64png(pdf_path, page_num, target_longest_dim)
    
    # Decode base64 to binary
    png_data = base64.b64decode(base64_png)
    
    # Create output path
    output_path = os.path.join(output_dir, f"page_{page_num-1:04d}.png")
    
    # Save the PNG to disk
    with open(output_path, "wb") as f:
        f.write(png_data)
    
    return output_path


def process_pdf(pdf_path: str, output_dir: str) -> None:
    """Process a PDF file and extract its content"""
    # Ensure poppler is installed
    check_poppler_version()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract filename for output
    pdf_filename = os.path.basename(pdf_path)
    base_name = os.path.splitext(pdf_filename)[0]
    
    print(f"Processing PDF: {pdf_path}")
    
    # Read PDF and extract metadata
    with open(pdf_path, "rb") as f:
        pdf_reader = pypdf.PdfReader(f)
        num_pages = len(pdf_reader.pages)  # Use pages property
        metadata = {
            "filename": pdf_filename,
            "num_pages": num_pages,
            "metadata": {k: str(v) for k, v in pdf_reader.metadata.items()} if pdf_reader.metadata else {}
        }
        
        # Extract text from each page
        pages_text = []
        for i in range(num_pages):
            page = pdf_reader.pages[i]
            text = page.extract_text()
            pages_text.append({
                "page_num": i + 1,
                "text": text
            })
        
        metadata["pages"] = pages_text
    
    # Save metadata and text content
    with open(os.path.join(output_dir, f"{base_name}_text.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Render PDF pages as images
    print(f"Rendering {num_pages} pages from PDF...")
    render_output_dir = os.path.join(output_dir, f"{base_name}_images")
    os.makedirs(render_output_dir, exist_ok=True)
    
    # Set a reasonable size for rendering images
    target_longest_dim = 2000
    
    try:
        # Render each page as an image
        rendered_pages = []
        for page_num in range(1, num_pages + 1):
            output_path = render_and_save_pdf_page(
                pdf_path=pdf_path,
                page_num=page_num,
                output_dir=render_output_dir,
                target_longest_dim=target_longest_dim
            )
            rendered_pages.append(output_path)
            print(f"Rendered page {page_num}/{num_pages}")
        
        print(f"Successfully rendered {len(rendered_pages)} pages to {render_output_dir}")
    except Exception as e:
        print(f"Error rendering PDF: {e}")
    
    print(f"PDF processing complete. Results saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Extract content from PDFs using olmocr components")
    parser.add_argument("pdf_path", help="Path to the PDF file to process")
    parser.add_argument("--output_dir", default="./pdf_output", help="Directory to save extracted content")
    
    args = parser.parse_args()
    
    # Process the PDF
    process_pdf(args.pdf_path, args.output_dir)


if __name__ == "__main__":
    main() 