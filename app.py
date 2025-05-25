#!/usr/bin/env python3
"""
app.py - Flask web server for Medical Report Analyzer

This Flask application provides a web interface for the Medical Report Analyzer.
It handles PDF uploads, processes them using the original app.py logic,
and displays the results on the web page.
"""

import os
import sys
import shutil
import subprocess
import tempfile
import textwrap
import uuid
import io
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename

import fitz      # pip install pymupdf
import ollama    # pip install ollama

# ——————————————————————————————————————————————————————————————
# CONFIG
# ——————————————————————————————————————————————————————————————
OCR_MODEL = "gemma3:12b"  # vision-enabled Gemma3 model; pull with `ollama pull gemma3:12b`
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.secret_key = os.urandom(24)

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
        return False, f"Error connecting to Ollama: {e}. Make sure Ollama is running."

    try:
        ollama.show(OCR_MODEL)
        return True, "Model ready"
    except ollama.ResponseError:
        try:
            print(f"Pulling model {OCR_MODEL} (this may take a minute)...")
            ollama.pull(OCR_MODEL)
            return True, f"Model {OCR_MODEL} pulled successfully"
        except Exception as e:
            return False, f"Error pulling model {OCR_MODEL}: {e}"

# ——————————————————————————————————————————————————————————————
# OCR Logic
# ——————————————————————————————————————————————————————————————
def ocr_pdf(pdf_path: str) -> tuple[str, list]:
    """
    Render each page of `pdf_path` to a PNG via PyMuPDF, then call:
        ollama run <OCR_MODEL> "Extract the text from this image: <path>"
    Collects and returns the concatenated OCR text and progress updates.
    """
    progress_updates = []
    
    try:
        doc = fitz.open(pdf_path)
        texts = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, page in enumerate(doc, start=1):
                progress_updates.append(f"Rendering page {i}/{len(doc)}...")
                
                pix = page.get_pixmap(dpi=300)
                img_path = os.path.join(tmpdir, f"page_{i}.png")
                pix.save(img_path)
                
                progress_updates.append(f"OCRing page {i}/{len(doc)} with {OCR_MODEL}...")
                
                # Use direct ollama API instead of subprocess for better cross-platform compatibility
                try:
                    # First try using the ollama Python API
                    with open(img_path, 'rb') as img_file:
                        response = ollama.generate(
                            model=OCR_MODEL,
                            prompt=f"Extract the text from this image:",
                            images=[img_file.read()],
                            options={"temperature": 0.0}
                        )
                        out = response.get('response', '').strip()
                        if not out:
                            progress_updates.append(f"Warning: page {i} returned blank.")
                        texts.append(out)
                except Exception as e:
                    # Fall back to subprocess with explicit UTF-8 encoding and error handling
                    progress_updates.append(f"Using fallback method for OCR on page {i}...")
                    prompt = f"Extract the text from this image: {img_path}"
                    
                    try:
                        # Use explicit UTF-8 encoding with error replacement for cross-platform compatibility
                        proc = subprocess.run(
                            ["ollama", "run", OCR_MODEL, prompt],
                            capture_output=True,
                            encoding='utf-8',  # Explicitly use UTF-8
                            errors='replace',  # Replace invalid chars instead of failing
                            check=False  # Don't raise exception on non-zero return code
                        )
                        
                        if proc.returncode != 0:
                            error_msg = f"OCR failed on page {i}: {proc.stderr}"
                            progress_updates.append(error_msg)
                            texts.append("")
                        else:
                            out = proc.stdout.strip()
                            if not out:
                                progress_updates.append(f"Warning: page {i} returned blank.")
                            texts.append(out)
                    except Exception as sub_e:
                        error_msg = f"Subprocess error on page {i}: {str(sub_e)}"
                        progress_updates.append(error_msg)
                        texts.append("")
        
        result_text = "\n\n".join(texts)
        # Add a fallback if no text was extracted
        if not result_text.strip():
            result_text = "No text could be extracted from the PDF. Please try a different file or check if the PDF contains actual text content."
            progress_updates.append("Warning: No text was extracted from any page.")
        
        return result_text, progress_updates
    except Exception as e:
        error_message = f"Error processing PDF: {str(e)}"
        print(error_message)  # Log the error
        return "Error processing PDF. Please try again with a different file.", [error_message]

# ——————————————————————————————————————————————————————————————
# "Generate" Logic (original generate.py, adapted)
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
    try:
        resp = ollama.generate(
            model=OCR_MODEL,
            prompt=prompt,
            options={"temperature": 0.3}
        )
        return resp["response"]
    except Exception as e:
        error_message = f"Error generating summary: {str(e)}"
        print(error_message)  # Log the error
        
        # Return a user-friendly message with sample data for demonstration
        return """
<h3>Summary Generation Error</h3>
<p>There was an error generating the summary. This could be due to connectivity issues with the AI model or problems with the extracted text.</p>

<h3>Sample Summary (for demonstration)</h3>
<p>Below is a sample of what the summary would look like with actual medical data:</p>

<h3>Overall Health Assessment</h3>
<p>Based on your lab results, your overall health appears to be <span class="normal">generally good</span> with a few areas that may need attention.</p>

<h3>Key Findings</h3>
<ul>
    <li>Your <span class="normal">blood glucose level is within normal range</span> at 92 mg/dL (normal range: 70-99 mg/dL), indicating good blood sugar control.</li>
    <li>Your <span class="abnormal">total cholesterol is slightly elevated</span> at 215 mg/dL (normal range: below 200 mg/dL), which may indicate a need for dietary changes.</li>
    <li>Your <span class="normal">kidney function tests (BUN and creatinine) are normal</span>, suggesting healthy kidney function.</li>
    <li>Your <span class="normal">liver function tests are within normal ranges</span>, indicating healthy liver function.</li>
    <li>Your <span class="abnormal">vitamin D level is slightly low</span> at 28 ng/mL (normal range: 30-100 ng/mL), which is common but may need supplementation.</li>
</ul>

<p>Note: This is sample data and not based on your actual report.</p>
"""

def answer_question(report_text: str, question: str) -> str:
    prompt = f"""
Here is a medical lab report:

{report_text}

The user asks: {question}

Please answer this question in simple, non-medical terms that a normal person can understand.
If the question requires medical expertise beyond explaining the report, say "You should consult your doctor about this."
Be accurate but use simple language.
"""
    try:
        resp = ollama.generate(
            model=OCR_MODEL,
            prompt=prompt,
            options={"temperature": 0.3}
        )
        return resp["response"]
    except Exception as e:
        error_message = f"Error answering question: {str(e)}"
        print(error_message)  # Log the error
        return "I'm sorry, I couldn't process your question due to a technical issue. Please try again later or ask a different question."

# ——————————————————————————————————————————————————————————————
# Helper Functions
# ——————————————————————————————————————————————————————————————
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ——————————————————————————————————————————————————————————————
# Flask Routes
# ——————————————————————————————————————————————————————————————
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_model', methods=['GET'])
def check_model():
    success, message = initialize_chatbot()
    return jsonify({'success': success, 'message': message})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    if file and allowed_file(file.filename):
        try:
            # Create a unique filename
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            file.save(filepath)
            
            # Store the filepath in session
            session['pdf_path'] = filepath
            session['pdf_name'] = file.filename
            
            return jsonify({
                'success': True, 
                'message': 'File uploaded successfully',
                'filename': file.filename
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error saving file: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'File type not allowed'})

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'pdf_path' not in session:
        return jsonify({'success': False, 'message': 'No PDF uploaded'})
    
    pdf_path = session['pdf_path']
    
    if not os.path.exists(pdf_path):
        return jsonify({'success': False, 'message': 'PDF file not found'})
    
    try:
        # Process the PDF
        report_text, progress_updates = ocr_pdf(pdf_path)
        
        if not report_text:
            return jsonify({
                'success': False, 
                'message': 'Failed to extract text from PDF',
                'progress': progress_updates
            })
        
        # Generate summary
        progress_updates.append("Generating summary...")
        summary = explain_report(report_text)
        
        # Store the report text in session for Q&A
        session['report_text'] = report_text
        
        return jsonify({
            'success': True,
            'message': 'Analysis complete',
            'summary': summary,
            'progress': progress_updates
        })
    except Exception as e:
        error_message = f"Error during analysis: {str(e)}"
        print(error_message)  # Log the error
        return jsonify({
            'success': False,
            'message': error_message,
            'progress': [error_message]
        })

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({'success': False, 'message': 'No question provided'})
        
        if 'report_text' not in session:
            return jsonify({'success': False, 'message': 'No report analyzed yet'})
        
        question = data['question']
        report_text = session['report_text']
        
        answer = answer_question(report_text, question)
        
        return jsonify({
            'success': True,
            'answer': answer
        })
    except Exception as e:
        error_message = f"Error processing question: {str(e)}"
        print(error_message)  # Log the error
        return jsonify({
            'success': False,
            'message': error_message
        })

# ——————————————————————————————————————————————————————————————
# Main Entrypoint
# ——————————————————————————————————————————————————————————————
if __name__ == '__main__':
    # Ensure uploads directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Check if Ollama CLI is on PATH
    if shutil.which("ollama") is None:
        print("Error: Ollama CLI not found. Install from https://ollama.com/")
        sys.exit(1)
    
    # Initialize the model (but don't exit if it fails)
    initialize_chatbot()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
