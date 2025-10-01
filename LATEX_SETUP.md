# LaTeX Setup Instructions for Windows

## Option 1: MiKTeX (Recommended - Lightweight)
1. Download MiKTeX from: https://miktex.org/download
2. Run the installer as Administrator
3. Choose "Install MiKTeX for all users" 
4. During installation, set "Install missing packages" to "Yes"
5. After installation, add to PATH (usually automatic)

## Option 2: TeX Live (Full Distribution)
1. Download TeX Live from: https://tug.org/texlive/acquire-netinst.html
2. Run install-tl-windows.exe as Administrator
3. This is a larger download (~4GB) but includes everything

## Option 3: Portable LaTeX (No Installation Required)
If you can't install software, you can use online LaTeX services:
- Your app will show compilation errors but still generate LaTeX code
- Users can copy the code to Overleaf.com to compile

## Verification
After installing, open Command Prompt and type:
```
pdflatex --version
```

If successful, you should see version information.

## What This Enables
- Real-time LaTeX compilation in your web app
- PDF generation from LaTeX code  
- Error detection and helpful suggestions
- Full LaTeX document creation with AI assistance
