# Medical Report Analyzer

A modern web application that uses AI to analyze medical reports, extract key information, and provide simplified explanations in plain language.

![Medical Report Analyzer](https://img.shields.io/badge/Medical-Report%20Analyzer-4CAF50)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-lightgrey)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Overview

Medical Report Analyzer is a tool designed to help patients understand their medical reports without needing advanced medical knowledge. The application uses OCR (Optical Character Recognition) to extract text from PDF medical reports and leverages large language models to:

1. Provide a plain-language summary of the report
2. Highlight abnormal values and explain what they might mean
3. Offer general health advice based on the results
4. Allow users to ask specific questions about their report

This project aims to bridge the gap between complex medical terminology and patient understanding, making healthcare information more accessible to everyone.

## Features

- **PDF Upload**: Securely upload medical report PDFs
- **OCR Processing**: Extract text from image-based PDFs
- **AI Analysis**: Get simplified explanations of medical terminology and results
- **Interactive Q&A**: Ask specific questions about your report
- **Clean UI**: Modern, responsive interface with a soothing color scheme
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.9 or higher
- Ollama (for running local LLMs)
- The Gemma3:12b model (will be downloaded automatically if not present)
- Flask and other Python dependencies (listed in requirements.txt)

## Installation & Setup

### Method 1: Local Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/MedicalReportAnalyzer.git
   cd MedicalReportAnalyzer
   ```

2. **Set up a virtual environment (recommended)**

   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install Ollama**

   Download and install Ollama from [https://ollama.com/](https://ollama.com/)

5. **Start the Ollama service**

   ```bash
   ollama serve
   ```

6. **Run the application**

   ```bash
   python app.py
   ```

7. **Access the web interface**

   Open your browser and navigate to: [http://localhost:5000](http://localhost:5000)

### Method 2: Docker Setup

1. **Download the Docker image**

   Download the Docker image file (.tar) from [Google Drive](https://drive.google.com/file/d/1KRV7K49kV0vIlNOBhQBc4kqatJY51dv3/view?usp=sharing)

2. **Load the Docker image**

   ```bash
   docker load -i medical_report_analyzer.tar
   ```

3. **Run the Docker container**

   ```bash
   docker run -p 5000:5000 -p 11434:11434 --name medical-analyzer medical-report-analyzer:latest
   ```

4. **Access the web interface**

   Open your browser and navigate to: [http://localhost:5000](http://localhost:5000)

## Usage

1. **Upload a medical report**
   - Click the "Choose PDF File" button
   - Select a medical report PDF from your computer
   - The file name will appear once selected

2. **Analyze the report**
   - Click the "Start Analysis" button
   - A progress modal will show the OCR and analysis progress
   - Wait for the analysis to complete

3. **Review the summary**
   - The summary will appear in the main panel
   - Normal values will be highlighted in green
   - Abnormal values will be highlighted in red
   - General health advice will be provided

4. **Ask questions**
   - Use the chat interface at the bottom of the page
   - Type your question and press Enter or click the send button
   - The AI will respond with information specific to your report
   - You can also click on suggested questions for common inquiries

5. **Save or print the results**
   - Use the copy button to copy the summary to your clipboard
   - Use the print button to print the summary or save it as a PDF

## Troubleshooting

- **"Error connecting to Ollama"**: Make sure Ollama is installed and running with `ollama serve`
- **"Model not ready"**: The first run may take time as it downloads the Gemma3:12b model
- **Blank or error in summary**: Try a different PDF or check if the PDF contains actual text content
- **Docker container exits immediately**: Check Docker logs for errors, ensure ports 5000 and 11434 are available

## Privacy & Security

- All processing happens locally on your machine
- Medical reports are not sent to external servers
- Uploaded PDFs are stored temporarily in the 'uploads' directory
- Session data is cleared when you close the browser

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyMuPDF for PDF processing
- Ollama for local LLM inference
- Flask for the web framework
- Font Awesome for the icons
