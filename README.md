# Quick Tools Project

This is the **Quick Tools**, a web-based application designed to generate QR codes, convert pdf to word and word to pdf. The project leverages HTML for the frontend, Python for backend logic, and includes Docker support for containerized deployment.

---

## Project Overview

**Purpose:**  
The aim of this project is to provide an easy-to-use tool for generating QR codes And pdf to word . Users can input their desired data or upload desired pdf for conversion and receive a QR code image as output or pdf or word file.

**Main Features:**
- Web-based interface for inputting data
- Real-time QR code generation
- Downloadable QR code images
- Additional pdftoword and wordtopdf converter
- Dockerfile in linux branch for easy deployment

---

## Setup Instructions
LINUX(Master Branch):

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Kali452345/qrcode_project.git
   cd qrcode_project
   ```

2. **(Optional for building on linux web servers) Run with Docker:**
   ```bash
   docker build -t qrcode_project .
   docker run -p 8000:8000 qrcode_project
   ```

3. **Manual Python Setup:**
   - Ensure you have Python 3 installed.
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Run the application:
     ```bash
     python main.py
     ```
   - Open your browser at `http://localhost:8000` (or specified port).

---
Windows (Windows-Version)
1. **Clone the Repository: Or Download as zip **
   ```bash
   git clone https://github.com/Kali452345/qrcode_project.git
   cd qrcode_project
   ```
2. **Manual Python Setup:**
   - Ensure you have Python 3 installed.
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Run the application:
     ```bash
     python main.py
     ```
   - Open your browser at `http://localhost:8000` (or specified port).

---


## Usage
1. **Using Qr-Gen**

- Enter the text or URL you want to encode.
- Click the "Generate" button.
- Download or use the generated QR code image.
  
2. **Using pdf to word**
-  Click on Upload
-  Choose pdf file
-  Click on Submit and Download
  
3. **Using pdf to word**
-  Click on Upload
-  Choose docx file
-  Click on Submit and Download
---

## Project Details

- **Frontend:** HTML
- **Backend:** Python
- **Containerization:** Dockerfile included

---
## Link to Website
 `https://qrcode-project-9sxj.onrender.com` 

## Group/Project Slots

| Slot            | Value                |
|-----------------|---------------------|
| Group Name      |      High Devs      |
| Group Member 1  |    Prince Ayaata    |
| Group member 2  |     Aidoo Irene     |
| Group Member 3  |   Dominic Gyimah    |
| Group Member 4  |   Marvin Habadah    |
| Group Member 5  |Noi Caleb Nii Majeoyi|



---

> **Repository:** [qrcode_project](https://github.com/Kali452345/qrcode_project)
