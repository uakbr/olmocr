#!/usr/bin/env python3
"""
Creates a simple HTML viewer to display the original PDF images alongside extracted text.
"""

import os
import json
import argparse
import base64
from pathlib import Path


# Define the HTML template with triple quotes
HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>PDF Viewer - {pdf_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #333;
            color: white;
            padding: 10px 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .page-container {{
            display: flex;
            margin-bottom: 40px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        .page-image {{
            flex: 1;
            padding-right: 20px;
            min-width: 0;
        }}
        .page-text {{
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background-color: #f9f9f9;
            border-radius: 5px;
            min-width: 0;
        }}
        .page-image img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
        }}
        h1, h2 {{
            margin-top: 0;
        }}
        .metadata {{
            background-color: #e9f7fe;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: monospace;
            font-size: 14px;
            line-height: 1.4;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PDF Viewer</h1>
        <p>Document: {pdf_name}</p>
    </div>
    
    <div class="metadata">
        <h2>Metadata</h2>
        <pre>{metadata}</pre>
    </div>
    
    {page_content}
</body>
</html>'''

# Define the page template with triple quotes
PAGE_TEMPLATE = '''
<div class="page-container">
    <div class="page-image">
        <h2>Page {page_num} - Image</h2>
        <img src="{image_path}" alt="Page {page_num}">
    </div>
    <div class="page-text">
        <h2>Page {page_num} - Extracted Text</h2>
        <pre>{page_text}</pre>
    </div>
</div>'''


def create_viewer(json_path, output_html_path=None):
    """Create an HTML viewer from the extracted PDF content"""
    # Load the JSON content
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Extract information
    pdf_name = data.get('filename', 'Unknown')
    metadata = json.dumps(data.get('metadata', {}), indent=2)
    pages = data.get('pages', [])
    
    # Get the base directory for image paths
    base_dir = os.path.dirname(json_path)
    pdf_base_name = os.path.splitext(pdf_name)[0]
    image_dir = os.path.join(base_dir, f"{pdf_base_name}_images")
    
    # Generate HTML for each page
    page_content = ""
    for page in pages:
        page_num = page.get('page_num', 0)
        page_text = page.get('text', '')
        
        # Find the corresponding image file
        image_pattern = f"page_{page_num-1:04d}.png"
        image_path = os.path.join(image_dir, image_pattern)
        
        # Make the image path relative to the HTML file
        if output_html_path:
            html_dir = os.path.dirname(output_html_path)
            image_path = os.path.relpath(image_path, html_dir)
        
        # Generate HTML for this page
        page_content += PAGE_TEMPLATE.format(
            page_num=page_num,
            image_path=image_path,
            page_text=page_text
        )
    
    # Generate the complete HTML
    html_content = HTML_TEMPLATE.format(
        pdf_name=pdf_name,
        metadata=metadata,
        page_content=page_content
    )
    
    # Determine the output path if not provided
    if not output_html_path:
        output_html_path = os.path.join(base_dir, f"{pdf_base_name}_viewer.html")
    
    # Write the HTML file
    with open(output_html_path, 'w') as f:
        f.write(html_content)
    
    print(f"HTML viewer created at: {output_html_path}")
    return output_html_path


def main():
    parser = argparse.ArgumentParser(description="Create HTML viewer for PDF extraction results")
    parser.add_argument("json_path", help="Path to the JSON file containing extracted PDF content")
    parser.add_argument("--output", help="Path to save the HTML viewer (optional)")
    
    args = parser.parse_args()
    
    create_viewer(args.json_path, args.output)


if __name__ == "__main__":
    main() 