# LOOK SMART AI

A simple OCR and chatbot integration tool that detects questions from screenshots and generates AI responses using Cohere.

## Features
- OCR-powered text detection (Tesseract & EasyOCR support).
- AI response generation using Cohere API.
- Standalone executable for easy deployment.

## Requirements
- Python 3.7+
- Tesseract-OCR installed and added to `PATH`.

## How to Use
Launch the application.
Click "Process Chat" to capture the screen and analyze questions.
The AI response will be displayed and optionally typed into the selected text box.

## Setup Instructions For Users (Windows)
[Download the Executable](https://github.com/yaseel/AQR/raw/main/dist/gui_app.exe)

Run the Executable:
Simply double-click the .exe file to launch the application.
No need to install Python or Tesseract.

## Setup Instructions For Developers
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd <project-directory>

2. Set up a virtual environment:
python -m venv env
source env/bin/activate  # On Linux/Mac
env\Scripts\activate     # On Windows

3. Install dependencies:
pip install -r requirements.txt

4. Install Tesseract-OCR:
Download Tesseract.
Add the installation path to the PATH environment variable.

5. Run the script:
python gui_app.py

6. Generate a standalone executable:
pyinstaller --onefile --noconsole --add-data "C:/Program Files/Tesseract-OCR/tesseract.exe;." gui_app.py

