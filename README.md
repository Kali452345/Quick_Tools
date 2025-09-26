I'll update your README.md with all the current features and proper setup instructions, removing the group information as requested.

```markdown
# Quick Tools Project

This is **Quick Tools**, a comprehensive web-based application that provides various utility tools including QR code generation, PDF tools, image tools, and a code editor with execution capabilities.

---

## Project Overview

**Purpose:**
The aim of this project is to provide an easy-to-use collection of web tools for everyday tasks. Users can generate QR codes, convert and manipulate PDF files, compress and convert images, and write/execute code directly in the browser.

**Main Features:**

### QR Code Generator
- Generate QR codes from text or URLs
- Real-time QR code generation
- Downloadable QR code images

### PDF Tools
- **PDF to Word:** Convert PDF files to Word documents (.docx)
- **Word to PDF:** Convert Word documents to PDF files
- **PDF Merge:** Combine multiple PDF files into one
- **PDF Compress:** Reduce PDF file sizes
- **PDF Protect:** Add or remove password protection from PDFs

### Image Tools
- **Image Converter:** Convert between various image formats (JPEG, PNG, GIF, BMP, TIFF, WEBP, ICO, ICNS, PPM, TGA)
- **Image Compressor:** Compress images with adjustable quality settings (10-100%)

### Code Editor
- Monaco Editor with syntax highlighting
- Support for multiple programming languages
- **Code Execution:** Run Python and JavaScript code directly in the browser
- Save and load code files
- Mobile-friendly responsive design

---

## Requirements

**System Requirements:**
- Python 3.7 or higher
- Node.js (for JavaScript code execution)
- LibreOffice (for Word to PDF conversion)

**Python Dependencies:**
All dependencies are listed in `requirements.txt` and include:
- Flask
- pdf2docx
- pypdf
- qrcode
- Pillow (PIL)
- Other supporting libraries

---

## Setup Instructions

### Option 1: Manual Python Setup (Recommended)

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Kali452345/Quick_Tools.git
   cd Quick_Tools
   ```

2. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install System Dependencies:**

   **For Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install libreoffice nodejs npm
   ```

   **For Windows:**
   - Download and install LibreOffice from https://www.libreoffice.org/
   - Download and install Node.js from https://nodejs.org/
   - Make sure both are added to your system PATH

   **For macOS:**
   ```bash
   brew install libreoffice node
   ```

4. **Run the Application:**
   ```bash
   python main.py
   ```

5. **Access the Application:**
   - Open your browser and go to `http://localhost:5000`

### Option 2: Docker Setup (Linux)

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Kali452345/Quick_Tools.git
   cd Quick_Tools
   ```

2. **Build and Run with Docker:**
   ```bash
   docker build -t quick-tools .
   docker run -p 5000:5000 quick-tools
   ```

3. **Access the Application:**
   - Open your browser and go to `http://localhost:5000`

---

## Usage Guide

### QR Code Generator
1. Navigate to the home page
2. Enter the text or URL you want to encode
3. Click "Generate QR Code"
4. Right-click on the generated QR code to save it

### PDF Tools
1. **PDF to Word:** Upload a PDF file and download the converted Word document
2. **Word to PDF:** Upload a Word document and download the converted PDF
3. **PDF Merge:** Select multiple PDF files to combine into one
4. **PDF Compress:** Upload a PDF to reduce its file size
5. **PDF Protect:** Add password protection or remove existing passwords from PDFs

### Image Tools
1. **Image Converter:** Upload an image and select the desired output format
2. **Image Compressor:** Upload an image, adjust quality (10-100%), and download the compressed version

### Code Editor
1. **Writing Code:** Use the Monaco editor with syntax highlighting
2. **Language Selection:** Choose from JavaScript, Python, HTML, CSS, and more
3. **Running Code:** Click "Run Code" to execute Python or JavaScript
4. **Saving Code:** Click "Save Code" to download your code as a file

---

## Features

- **Responsive Design:** Works on desktop and mobile devices
- **No Registration Required:** All tools are available without user accounts
- **Privacy Focused:** Files are processed temporarily and not stored permanently
- **Multiple Format Support:** Wide range of file formats supported
- **Real-time Processing:** Immediate results for most operations
- **Error Handling:** Clear error messages and progress indicators

---

## Technical Details

- **Frontend:** HTML5, CSS3, JavaScript, Monaco Editor
- **Backend:** Flask (Python)
- **File Processing:** Pillow (Images), pypdf (PDFs), pdf2docx (Conversions)
- **Code Execution:** Subprocess with timeout protection
- **Security:** Input validation, temporary file handling, execution timeouts

---

## Live Demo

Visit the live application at: `https://qrcode-project-9sxj.onrender.com`

---

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

---

> **Repository:** [Quick_Tools](https://github.com/Kali452345/Quick_Tools)
```

This updated README provides:
- Complete feature overview of all current tools
- Clear setup instructions for different operating systems
- Detailed usage guide for each feature
- System requirements including Node.js and LibreOffice
- Proper technical documentation
- Updated repository link to the new Quick_Tools repo
- Removed all group information as requested

The README now accurately reflects all the functionality in your Quick Tools project.