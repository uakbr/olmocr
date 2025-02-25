#!/usr/bin/env python3
"""
Creates a simple HTML viewer to display the original PDF images alongside extracted text.
"""

import os
import json
import argparse
import base64
from pathlib import Path
# Import our text formatting utilities
from text_formatter import process_page_text


# Define the HTML template with triple quotes
HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>PDF Viewer - {pdf_name}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --primary-color: #4285f4;
            --secondary-color: #e8f0fe;
            --dark-color: #333;
            --light-color: #f5f5f5;
            --success-color: #34a853;
            --text-color: #202124;
            --border-radius: 8px;
            --box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            --transition: all 0.3s ease;
        }}
        
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--light-color);
            color: var(--text-color);
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background-color: var(--primary-color);
            color: white;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            position: relative;
        }}
        
        .navbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .navbar h1 {{
            margin: 0;
            font-size: 1.8rem;
        }}
        
        .document-info {{
            margin-top: 10px;
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 10px 20px;
            background-color: white;
            color: var(--primary-color);
            border: none;
            border-radius: var(--border-radius);
            cursor: pointer;
            font-weight: 500;
            text-decoration: none;
            transition: var(--transition);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .btn i {{
            margin-right: 8px;
        }}
        
        .copy-all-btn {{
            margin-left: 10px;
        }}
        
        .copy-page-btn {{
            font-size: 0.9rem;
            padding: 6px 12px;
            margin-top: 10px;
        }}

        .format-toggle {{
            margin-right: 10px;
        }}
        
        .toast {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background-color: var(--success-color);
            color: white;
            padding: 12px 24px;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            opacity: 0;
            transition: opacity 0.3s ease-in-out;
            z-index: 1000;
        }}
        
        .toast.show {{
            opacity: 1;
        }}
        
        .metadata {{
            background-color: var(--secondary-color);
            padding: 20px;
            border-radius: var(--border-radius);
            margin-bottom: 30px;
            box-shadow: var(--box-shadow);
        }}
        
        .page-container {{
            display: flex;
            flex-direction: row;
            margin-bottom: 50px;
            background-color: white;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            overflow: hidden;
        }}
        
        @media (max-width: 768px) {{
            .page-container {{
                flex-direction: column;
            }}
        }}
        
        .page-image {{
            flex: 1;
            padding: 20px;
            min-width: 0;
            border-right: 1px solid #eee;
        }}
        
        @media (max-width: 768px) {{
            .page-image {{
                border-right: none;
                border-bottom: 1px solid #eee;
            }}
        }}
        
        .page-text {{
            flex: 1;
            padding: 20px;
            background-color: #fafafa;
            position: relative;
            min-width: 0;
        }}
        
        .page-image img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        
        .page-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        
        h2 {{
            margin: 0;
            font-size: 1.4rem;
            color: var(--primary-color);
        }}
        
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            line-height: 1.5;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border: 1px solid #eee;
            margin: 0;
        }}

        .markdown-content {{
            font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            font-size: 14px;
            line-height: 1.6;
            padding: 10px;
        }}

        .markdown-content h1 {{
            font-size: 1.8rem;
            margin-top: 0;
            color: var(--primary-color);
        }}

        .markdown-content h2 {{
            font-size: 1.4rem;
            margin-top: 1.5rem;
            color: var(--primary-color);
        }}

        .markdown-content p {{
            margin: 0.8rem 0;
        }}

        .markdown-content ul, .markdown-content ol {{
            padding-left: 2rem;
        }}

        .page-raw, .page-formatted {{
            display: none;
        }}

        .active {{
            display: block;
        }}
        
        .page-navigation {{
            display: flex;
            justify-content: center;
            margin: 30px 0;
        }}
        
        .page-navigation button {{
            margin: 0 5px;
        }}
        
        .back-to-top {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background-color: var(--primary-color);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            box-shadow: var(--box-shadow);
            opacity: 0;
            transition: var(--transition);
            z-index: 999;
        }}
        
        .back-to-top.visible {{
            opacity: 1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="navbar">
                <h1>PDF Viewer</h1>
                <div>
                    <button id="toggleFormat" class="btn format-toggle">
                        <i class="fas fa-magic"></i> Toggle Formatting
                    </button>
                    <button id="copyAllText" class="btn copy-all-btn">
                        <i class="fas fa-copy"></i> Copy All Text
                    </button>
                </div>
            </div>
            <div class="document-info">Document: {pdf_name}</div>
        </div>
        
        <div class="metadata">
            <h2>Metadata</h2>
            <pre>{metadata}</pre>
        </div>
        
        {page_content}
    </div>
    
    <div id="toast" class="toast">Text copied to clipboard!</div>
    
    <div id="backToTop" class="back-to-top">
        <i class="fas fa-arrow-up"></i>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            // Format toggle functionality
            const toggleFormatBtn = document.getElementById('toggleFormat');
            const rawElements = document.querySelectorAll('.page-raw');
            const formattedElements = document.querySelectorAll('.page-formatted');
            let isFormatted = true; // Default to formatted view
            
            function updateFormatToggle() {{
                if (isFormatted) {{
                    rawElements.forEach(el => el.classList.remove('active'));
                    formattedElements.forEach(el => el.classList.add('active'));
                    toggleFormatBtn.innerHTML = '<i class="fas fa-font"></i> Show Raw Text';
                }} else {{
                    rawElements.forEach(el => el.classList.add('active'));
                    formattedElements.forEach(el => el.classList.remove('active'));
                    toggleFormatBtn.innerHTML = '<i class="fas fa-magic"></i> Show Formatted Text';
                }}
            }}
            
            // Initialize format view
            updateFormatToggle();
            
            // Toggle format on button click
            toggleFormatBtn.addEventListener('click', function() {{
                isFormatted = !isFormatted;
                updateFormatToggle();
            }});
            
            // Get all the text content from all pages
            function getAllText() {{
                let allText = '';
                const activeElements = document.querySelectorAll('.active');
                activeElements.forEach(container => {{
                    if (container.tagName === 'PRE') {{
                        allText += container.textContent + '\\n\\n';
                    }} else {{
                        allText += container.innerText + '\\n\\n';
                    }}
                }});
                return allText.trim();
            }}
            
            // Copy text to clipboard
            function copyToClipboard(text) {{
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                
                // Show toast notification
                const toast = document.getElementById('toast');
                toast.classList.add('show');
                setTimeout(() => {{
                    toast.classList.remove('show');
                }}, 2000);
            }}
            
            // Add event listener to the copy all button
            const copyAllButton = document.getElementById('copyAllText');
            copyAllButton.addEventListener('click', function() {{
                const allText = getAllText();
                copyToClipboard(allText);
            }});
            
            // Add event listeners to copy page buttons
            const copyPageButtons = document.querySelectorAll('.copy-page-btn');
            copyPageButtons.forEach(button => {{
                button.addEventListener('click', function() {{
                    const pageContainer = this.closest('.page-text');
                    const activeContent = pageContainer.querySelector('.active');
                    let pageText = '';
                    
                    if (activeContent.tagName === 'PRE') {{
                        pageText = activeContent.textContent;
                    }} else {{
                        pageText = activeContent.innerText;
                    }}
                    
                    copyToClipboard(pageText);
                }});
            }});
            
            // Back to top button
            const backToTopButton = document.getElementById('backToTop');
            
            window.addEventListener('scroll', function() {{
                if (window.pageYOffset > 300) {{
                    backToTopButton.classList.add('visible');
                }} else {{
                    backToTopButton.classList.remove('visible');
                }}
            }});
            
            backToTopButton.addEventListener('click', function() {{
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }});
        }});
    </script>
</body>
</html>'''

# Define the page template with triple quotes
PAGE_TEMPLATE = '''
<div class="page-container">
    <div class="page-image">
        <div class="page-header">
            <h2>Page {page_num} - Image</h2>
        </div>
        <img src="{image_path}" alt="Page {page_num}">
    </div>
    <div class="page-text">
        <div class="page-header">
            <h2>Page {page_num} - Extracted Text</h2>
            <button class="btn copy-page-btn">
                <i class="fas fa-copy"></i> Copy
            </button>
        </div>
        <pre class="page-raw">{raw_text}</pre>
        <div class="page-formatted markdown-content active">{formatted_text}</div>
    </div>
</div>'''


def create_viewer(json_path, output_html_path=None, use_markdown=True):
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
    image_dir = f"{pdf_base_name}_images"  # Make this relative, not absolute
    
    # Generate HTML for each page
    page_content = ""
    for page in pages:
        page_num = page.get('page_num', 0)
        raw_text = page.get('text', '')
        
        # Apply text formatting to the raw text
        formatted_text = process_page_text(raw_text, use_markdown=use_markdown)
        
        # Find the corresponding image file
        image_pattern = f"page_{page_num-1:04d}.png"
        image_path = os.path.join(image_dir, image_pattern)
        
        # Generate HTML for this page
        page_content += PAGE_TEMPLATE.format(
            page_num=page_num,
            image_path=image_path,
            raw_text=raw_text,
            formatted_text=formatted_text
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
    parser.add_argument("--no-markdown", action="store_true", help="Disable markdown formatting")
    
    args = parser.parse_args()
    
    create_viewer(args.json_path, args.output, use_markdown=not args.no_markdown)


if __name__ == "__main__":
    main() 