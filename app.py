#!/usr/bin/env python3
"""
A beautiful GUI for the olmocr PDF processing application.
"""

import os
import sys
import json
import time
import threading
import subprocess
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory

# Import our PDF processing functions
from extract_pdf import process_pdf
from create_viewer import create_viewer

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'olmocr-pdf-processor'  # for flash messages
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'pdf_output'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store processing jobs
processing_jobs = {}


def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_processing_status(job_id):
    """Get the status of a processing job"""
    if job_id in processing_jobs:
        return processing_jobs[job_id]
    return {'status': 'unknown', 'progress': 0, 'message': 'Unknown job'}


def process_pdf_async(pdf_path, job_id):
    """Process a PDF asynchronously and update job status"""
    try:
        # Update job status to processing
        processing_jobs[job_id]['status'] = 'processing'
        processing_jobs[job_id]['message'] = 'Starting PDF processing...'
        
        # Get filename for output paths
        pdf_filename = os.path.basename(pdf_path)
        base_name = os.path.splitext(pdf_filename)[0]
        
        # Process the PDF
        output_dir = app.config['OUTPUT_FOLDER']
        
        # Process PDF
        process_pdf(pdf_path, output_dir)
        
        # Create HTML viewer
        json_path = os.path.join(output_dir, f"{base_name}_text.json")
        html_path = create_viewer(json_path)
        
        # Update job status to completed
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['progress'] = 100
        processing_jobs[job_id]['message'] = 'PDF processing completed'
        processing_jobs[job_id]['html_path'] = os.path.basename(html_path)
        
    except Exception as e:
        # Update job status to failed
        processing_jobs[job_id]['status'] = 'failed'
        processing_jobs[job_id]['message'] = f'Error: {str(e)}'


@app.route('/')
def index():
    """Home page - display upload form and processed PDFs"""
    # Get list of processed PDFs
    processed_pdfs = []
    for filename in os.listdir(app.config['OUTPUT_FOLDER']):
        if filename.endswith('_viewer.html'):
            base_name = filename.replace('_viewer.html', '')
            processed_pdfs.append({
                'name': base_name,
                'html_path': filename,
                'date': time.ctime(os.path.getctime(os.path.join(app.config['OUTPUT_FOLDER'], filename)))
            })
    
    return render_template('index.html', processed_pdfs=processed_pdfs)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start processing"""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Create a job ID
        job_id = f"job_{int(time.time())}"
        
        # Initialize job status
        processing_jobs[job_id] = {
            'status': 'queued',
            'progress': 0,
            'message': 'Queued for processing',
            'filename': filename
        }
        
        # Start processing in background
        thread = threading.Thread(target=process_pdf_async, args=(filepath, job_id))
        thread.daemon = True
        thread.start()
        
        flash(f'File {filename} uploaded and queued for processing', 'success')
        return redirect(url_for('view_job', job_id=job_id))
    
    flash('Invalid file format. Only PDF files are allowed.', 'error')
    return redirect(url_for('index'))


@app.route('/job/<job_id>')
def view_job(job_id):
    """View job status page"""
    job_status = get_processing_status(job_id)
    return render_template('job.html', job_id=job_id, job_status=job_status)


@app.route('/job/<job_id>/status')
def job_status(job_id):
    """API endpoint to get job status"""
    return jsonify(get_processing_status(job_id))


@app.route('/view/<path:filename>')
def view_pdf(filename):
    """View a processed PDF or its resources"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


if __name__ == '__main__':
    # Run the app on all network interfaces (0.0.0.0) to allow external access
    # Using port 8080 instead of 5000 to avoid conflict with AirPlay Receiver
    app.run(host='0.0.0.0', port=8080, debug=True) 