// DOM Elements
const fileInput = document.getElementById('file-input');
const uploadForm = document.getElementById('upload-form');
const startBtn = document.getElementById('start-btn');
const clearBtn = document.getElementById('clear-btn');
const pdfStatus = document.getElementById('pdf-status');
const modelStatus = document.getElementById('model-status');
const processingStatus = document.getElementById('processing-status');
const summaryContent = document.getElementById('summary-content');
const chatMessages = document.getElementById('chat-messages');
const questionInput = document.getElementById('question-input');
const sendBtn = document.getElementById('send-btn');
const processingModal = document.getElementById('processing-modal');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const progressLog = document.getElementById('progress-log');
const copySummaryBtn = document.getElementById('copy-summary-btn');
const printSummaryBtn = document.getElementById('print-summary-btn');

// Application State
let appState = {
    pdfSelected: false,
    pdfName: '',
    modelReady: false,
    processing: false,
    analysisComplete: false,
    reportText: '',
    summary: ''
};

// Default questions to suggest
const defaultQuestions = [
    "What does my cholesterol mean?",
    "Is my vitamin D level dangerous?",
    "Do I need to worry about my results?",
    "What should I do next?",
    "What is normal cholesterol?"
];

// Initialize the application
function init() {
    attachEventListeners();
    checkModelStatus();
}

// Check if the model is ready
function checkModelStatus() {
    fetch('/check_model')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                appState.modelReady = true;
                modelStatus.textContent = "Ready";
                modelStatus.classList.add('normal');
            } else {
                modelStatus.textContent = "Not ready";
                modelStatus.classList.add('abnormal');
            }
        })
        .catch(error => {
            console.error('Error checking model status:', error);
            modelStatus.textContent = "Error checking";
            modelStatus.classList.add('abnormal');
        });
}

// Attach event listeners to UI elements
function attachEventListeners() {
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Start analysis button
    startBtn.addEventListener('click', startAnalysis);
    
    // Clear results button
    clearBtn.addEventListener('click', clearResults);
    
    // Send question button
    sendBtn.addEventListener('click', sendQuestion);
    
    // Question input enter key
    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendQuestion();
        }
    });
    
    // Copy and print summary buttons
    copySummaryBtn.addEventListener('click', copySummary);
    printSummaryBtn.addEventListener('click', printSummary);
}

// Handle file selection
function handleFileSelect(event) {
    const file = event.target.files[0];
    
    if (file) {
        if (file.type !== 'application/pdf') {
            alert('Please select a PDF file.');
            fileInput.value = '';
            return;
        }
        
        appState.pdfSelected = true;
        appState.pdfName = file.name;
        
        // Update UI
        pdfStatus.textContent = file.name;
        startBtn.disabled = false;
        
        // Create file preview if it doesn't exist
        if (!document.querySelector('.file-preview')) {
            const fileUploadContainer = document.querySelector('.file-upload-container');
            const filePreview = document.createElement('div');
            filePreview.className = 'file-preview';
            filePreview.innerHTML = `
                <i class="fas fa-file-pdf"></i>
                <span class="file-preview-name">${file.name}</span>
                <button class="file-remove" title="Remove file">
                    <i class="fas fa-times"></i>
                </button>
            `;
            fileUploadContainer.appendChild(filePreview);
            
            // Add event listener to remove button
            const removeBtn = filePreview.querySelector('.file-remove');
            removeBtn.addEventListener('click', () => {
                fileInput.value = '';
                fileUploadContainer.removeChild(filePreview);
                pdfStatus.textContent = 'No PDF selected';
                startBtn.disabled = true;
                appState.pdfSelected = false;
                appState.pdfName = '';
            });
        } else {
            // Update existing preview
            document.querySelector('.file-preview-name').textContent = file.name;
        }
    }
}

// Upload the PDF file
function uploadPDF() {
    return new Promise((resolve, reject) => {
        if (!appState.pdfSelected) {
            reject('No PDF selected');
            return;
        }
        
        const formData = new FormData(uploadForm);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                resolve(data);
            } else {
                reject(data.message);
            }
        })
        .catch(error => {
            reject('Error uploading file: ' + error);
        });
    });
}

// Start the analysis process
function startAnalysis() {
    if (appState.processing || !appState.pdfSelected) return;
    
    appState.processing = true;
    processingStatus.textContent = "Processing...";
    startBtn.disabled = true;
    
    // Show processing modal
    processingModal.classList.add('show');
    progressBar.style.width = '10%';
    progressText.textContent = "Uploading PDF...";
    progressLog.innerHTML = '<p>Starting analysis process...</p>';
    
    // Upload the PDF
    uploadPDF()
        .then(data => {
            progressBar.style.width = '30%';
            progressText.textContent = "PDF uploaded, starting analysis...";
            progressLog.innerHTML += '<p>PDF uploaded successfully.</p>';
            
            // Start the analysis
            return fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
        })
        .then(response => {
            // Check if response is ok before parsing JSON
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Analysis response:", data); // Debug log
            
            if (data.success) {
                // Update progress log with all progress updates
                if (data.progress && data.progress.length > 0) {
                    data.progress.forEach(update => {
                        progressLog.innerHTML += `<p>${update}</p>`;
                        progressLog.scrollTop = progressLog.scrollHeight;
                    });
                }
                
                progressBar.style.width = '100%';
                progressText.textContent = "Analysis complete!";
                
                // Wait a moment before closing the modal
                setTimeout(() => {
                    processingModal.classList.remove('show');
                    completeAnalysis(data.summary);
                }, 1000);
            } else {
                throw new Error(data.message || "Unknown error during analysis");
            }
        })
        .catch(error => {
            console.error('Error during analysis:', error);
            progressText.textContent = "Error during analysis";
            progressLog.innerHTML += `<p class="error">Error: ${error.message || error}</p>`;
            
            // Enable the start button again
            startBtn.disabled = false;
            appState.processing = false;
            
            // Wait for user to close the modal
            setTimeout(() => {
                processingModal.classList.remove('show');
            }, 3000);
        });
}

// Complete the analysis and update UI
function completeAnalysis(summary) {
    appState.processing = false;
    appState.analysisComplete = true;
    appState.summary = summary || "No summary was generated. Please try again with a different PDF.";
    
    // Update UI
    processingStatus.textContent = "Analysis complete";
    clearBtn.disabled = false;
    questionInput.disabled = false;
    sendBtn.disabled = false;
    copySummaryBtn.disabled = false;
    printSummaryBtn.disabled = false;
    
    // Display summary - ensure it's not empty
    if (summary && summary.trim()) {
        summaryContent.innerHTML = summary;
    } else {
        summaryContent.innerHTML = `
            <div class="error-message">
                <h3>No Summary Generated</h3>
                <p>The analysis did not produce a summary. This could be due to:</p>
                <ul>
                    <li>The PDF containing no extractable text</li>
                    <li>The PDF being password protected</li>
                    <li>A temporary issue with the AI model</li>
                </ul>
                <p>Please try again with a different PDF file.</p>
            </div>
        `;
    }
    
    // Add system message to chat
    addMessage("Analysis complete! You can now ask questions about your medical report.", "system");
    
    // Add suggested questions
    addSuggestedQuestions();
}

// Add a message to the chat
function addMessage(text, type, time = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `${type}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `<p>${text}</p>`;
    
    messageDiv.appendChild(contentDiv);
    
    if (time) {
        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = time;
        messageDiv.appendChild(timeSpan);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add suggested questions to the chat
function addSuggestedQuestions() {
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.className = 'system-message';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    let suggestionsHTML = '<p>Here are some questions you might want to ask:</p><div class="suggested-questions">';
    
    defaultQuestions.forEach(question => {
        suggestionsHTML += `<button class="suggested-question">${question}</button>`;
    });
    
    suggestionsHTML += '</div>';
    contentDiv.innerHTML = suggestionsHTML;
    
    suggestionsDiv.appendChild(contentDiv);
    chatMessages.appendChild(suggestionsDiv);
    
    // Add event listeners to suggested questions
    document.querySelectorAll('.suggested-question').forEach(button => {
        button.addEventListener('click', () => {
            questionInput.value = button.textContent;
            sendQuestion();
        });
    });
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Send a question
function sendQuestion() {
    const question = questionInput.value.trim();
    if (!question || !appState.analysisComplete) return;
    
    // Add user message
    addMessage(question, 'user', getCurrentTime());
    
    // Clear input
    questionInput.value = '';
    
    // Disable input while waiting for response
    questionInput.disabled = true;
    sendBtn.disabled = true;
    
    // Send question to server
    fetch('/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: question })
    })
    .then(response => {
        // Check if response is ok before parsing JSON
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Add AI response
            addMessage(data.answer, 'ai', getCurrentTime());
        } else {
            // Add error message
            addMessage("Sorry, I couldn't process your question. " + data.message, 'ai', getCurrentTime());
        }
        
        // Re-enable input
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    })
    .catch(error => {
        console.error('Error sending question:', error);
        addMessage("Sorry, there was an error processing your question.", 'ai', getCurrentTime());
        
        // Re-enable input
        questionInput.disabled = false;
        sendBtn.disabled = false;
    });
}

// Clear all results
function clearResults() {
    // Reset app state
    appState.pdfSelected = false;
    appState.analysisComplete = false;
    appState.summary = '';
    
    // Reset UI
    pdfStatus.textContent = "No PDF selected";
    processingStatus.textContent = "Waiting to start";
    summaryContent.innerHTML = `
        <div class="placeholder-content">
            <i class="fas fa-file-medical"></i>
            <p>Your medical report summary will appear here after analysis</p>
        </div>
    `;
    chatMessages.innerHTML = `
        <div class="system-message">
            <div class="message-content">
                <p>Welcome to Medical Report Analyzer. After analyzing your report, you can ask questions about it here.</p>
            </div>
        </div>
    `;
    
    // Reset file input
    fileInput.value = '';
    const filePreview = document.querySelector('.file-preview');
    if (filePreview) {
        filePreview.parentNode.removeChild(filePreview);
    }
    
    // Reset buttons
    startBtn.disabled = true;
    clearBtn.disabled = true;
    questionInput.disabled = true;
    sendBtn.disabled = true;
    copySummaryBtn.disabled = false;
    printSummaryBtn.disabled = false;
    
    // Reset progress
    progressBar.style.width = '0%';
    progressText.textContent = "Initializing...";
    progressLog.innerHTML = '';
}

// Copy summary to clipboard
function copySummary() {
    if (!appState.analysisComplete) return;
    
    // Create a temporary element to hold the HTML content
    const tempElement = document.createElement('div');
    tempElement.innerHTML = summaryContent.innerHTML;
    
    // Convert to plain text (remove HTML tags)
    const plainText = tempElement.textContent || tempElement.innerText || '';
    
    // Use the clipboard API
    navigator.clipboard.writeText(plainText).then(() => {
        // Show a temporary notification
        const notification = document.createElement('div');
        notification.className = 'copy-notification';
        notification.textContent = 'Summary copied to clipboard!';
        document.body.appendChild(notification);
        
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 2000);
    });
}

// Print summary
function printSummary() {
    if (!appState.analysisComplete) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
        <head>
            <title>Medical Report Analysis</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: #388E3C;
                    border-bottom: 1px solid #E0E0E0;
                    padding-bottom: 10px;
                }
                h3 {
                    color: #388E3C;
                    margin-top: 20px;
                }
                .normal {
                    color: #4CAF50;
                    font-weight: bold;
                }
                .abnormal {
                    color: #F44336;
                    font-weight: bold;
                }
                .footer {
                    margin-top: 30px;
                    border-top: 1px solid #E0E0E0;
                    padding-top: 10px;
                    font-size: 0.8rem;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <h1>Medical Report Analysis</h1>
            <p>Generated on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}</p>
            <p>Report: ${appState.pdfName}</p>
            ${summaryContent.innerHTML}
            <div class="footer">
                <p>This analysis is generated by Medical Report Analyzer and is not a substitute for professional medical advice.</p>
            </div>
        </body>
        </html>
    `);
    
    printWindow.document.close();
    printWindow.focus();
    
    // Print after a short delay to ensure content is loaded
    setTimeout(() => {
        printWindow.print();
    }, 500);
}

// Get current time in HH:MM format
function getCurrentTime() {
    const now = new Date();
    return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
}

// Add CSS for error message
const style = document.createElement('style');
style.textContent = `
    .error-message {
        background-color: rgba(244, 67, 54, 0.1);
        border-left: 4px solid #F44336;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    
    .error-message h3 {
        color: #D32F2F;
        margin-top: 0;
    }
    
    .error-message ul {
        margin-bottom: 15px;
    }
    
    .error {
        color: #F44336;
    }
`;
document.head.appendChild(style);

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
