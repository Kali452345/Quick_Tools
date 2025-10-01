import logging
import os
import uuid
import shutil
from rembg import remove
from logging import exception
from flask import Flask, render_template, request, abort, send_file, jsonify
from pdf2docx import Converter
from pypdf import PdfWriter, PdfReader
import subprocess
import qrcode
import io
import base64
from PIL import Image
import google.generativeai as genai
import json


import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure Gemini API (you'll need to set your API key)
# You can get a free API key from https://makersuite.google.com/app/apikey
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Check for .env file first
env_file = '.env'
if os.path.exists(env_file):
    try:
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    GEMINI_API_KEY = line.split('=', 1)[1].strip()
                    os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
                    break
    except:
        pass

# If no API key found, prompt user to enter it
if not GEMINI_API_KEY or len(GEMINI_API_KEY) < 10:
    print("\n" + "="*50)
    print("🤖 GEMINI AI SETUP REQUIRED")
    print("="*50)
    print("To use the AI LaTeX generation feature:")
    print("1. Go to: https://makersuite.google.com/app/apikey")
    print("2. Sign in with your Google account")
    print("3. Click 'Create API Key'")
    print("4. Copy the API key and paste it below")
    print("\nNote: You can skip this and use LaTeX editor without AI")
    print("-"*50)

    try:
        user_input = input("Enter your Gemini API key (or press Enter to skip): ").strip()

        if user_input and len(user_input) > 10:
            GEMINI_API_KEY = user_input
            # Save it as environment variable for future use
            os.environ['GEMINI_API_KEY'] = user_input
            
            # Save to .env file for persistence
            try:
                with open('.env', 'w') as f:
                    f.write(f'GEMINI_API_KEY={user_input}\n')
                print("✅ API key saved to .env file! It will be remembered for future sessions.")
            except:
                print("✅ API key set for this session.")
                
            # Also try to save to Windows environment
            try:
                import subprocess
                subprocess.run(['setx', 'GEMINI_API_KEY', user_input], capture_output=True, check=False)
            except:
                pass
        else:
            print("⚠️  Skipping AI setup. LaTeX editor will work without AI generation.")
    except (EOFError, KeyboardInterrupt):
        print("⚠️  Skipping AI setup (non-interactive mode). LaTeX editor will work without AI generation.")
    print("="*50 + "\n")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Step 3: Create a Flask route for '/' that accepts GET and POST
@app.route('/', methods=['GET', 'POST'])
def home():
    qrcode_img = None  # Step 7: Default to no QR code image
    # Step 4: Check if the request method is POST
    if request.method == 'POST':
        # Step 5: Get the form data from the request
        data = request.form.get('data')
        if data:
            # Step 6: Generate the QR code using the received data
            qr = qrcode.make(data)
            buf = io.BytesIO()
            qr.save(buf, format='PNG')
            img_bytes = buf.getvalue()
            # Encode the image to base64 so it can be embedded in HTML
            qrcode_img = 'data:image/png;base64,' + base64.b64encode(img_bytes).decode('utf-8')
    # Step 8: Render the result (QR code image) in your template
    return render_template('index.html', qrcode_img=qrcode_img, active_page='qr-gen')
@app.route('/pdftoword', methods=['GET', 'POST'])  # Allow both GET (show form) and POST (handle upload)
def pdftoword():
    if request.method == 'GET':
        # If the user visits the page, just show the upload form
        return render_template('pdftoword.html', active_page='pdftoword')

    # If the request is POST (form submitted with file)
    if 'pdfupload' not in request.files:
        # If no file was uploaded, abort with error
        abort(400, "No file uploaded")
    pdf_file = request.files['pdfupload']  # Get the uploaded file
    filename = pdf_file.filename or 'upload.pdf'  # Use the original filename or a default
    safe_name = secure_filename(filename)  # Sanitize the filename for safety
    safe_name = f"{uuid.uuid4().hex}_{safe_name}"  # Add a unique prefix to avoid name clashes

    with tempfile.TemporaryDirectory() as tmpdir:  # Create a temporary directory for processing
        pdf_path = os.path.join(tmpdir, safe_name)  # Full path for the uploaded PDF
        pdf_file.save(pdf_path)  # Save the uploaded PDF to the temp directory

        docx_name = os.path.splitext(safe_name)[0] + '.docx'  # Create a DOCX filename
        docx_path = os.path.join(tmpdir, docx_name)  # Full path for the output DOCX

        try:
            # Create the Converter object
            cv = Converter(pdf_path)
            cv.convert(docx_path)
            cv.close()
            # Read the resulting DOCX file into memory
            with open(docx_path, 'rb') as f:
                docx_bytes = f.read()
        except Exception:
            logging.exception("PDF->DOCX conversion failed")
            abort(500, "Conversion failed")

        # Send the DOCX file to the user as a download
        return send_file(
            io.BytesIO(docx_bytes),  # Serve from memory
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=docx_name
        )


@app.route('/wordtopdf', methods=['GET', 'POST'])
def wordtopdf():
    if request.method == 'GET':
        return render_template('wordtopdf.html', active_page='wordtopdf')

    if 'docxupload' not in request.files:
        abort(400, "No file uploaded")

    docx_file = request.files['docxupload']
    filename = docx_file.filename or 'upload.docx'
    safe_name = secure_filename(filename)
    safe_name = f"{uuid.uuid4().hex}_{safe_name}"

    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = os.path.join(tmpdir, safe_name)
        docx_file.save(docx_path)

        pdf_name = os.path.splitext(safe_name)[0] + '.pdf'
        pdf_path = os.path.join(tmpdir, pdf_name)

        try:
            # Call LibreOffice to convert DOCX → PDF
            subprocess.run(
                [
                    "libreoffice", "--headless", "--convert-to", "pdf",
                    "--outdir", tmpdir, docx_path
                ],
                check=True
            )

            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()

        except Exception:
            logging.exception("DOCX->PDF conversion failed")
            abort(500, "Conversion failed")

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=pdf_name
        )
# python


@app.route('/pdfmerge', methods=['GET', 'POST'])
def pdfmerge():
    if request.method == 'GET':
        return render_template('pdfmerge.html', active_page='pdfmerge')

    # Match the input name in `templates/pdfmerge.html`
    files = [f for f in request.files.getlist('files[]') if f and f.filename]
    if len(files) < 2:
        abort(400, "Upload at least two PDF files")

    # Optional: basic extension/mimetype checks
    for f in files:
        name = (f.filename or "").lower()
        if not name.endswith(".pdf"):
            abort(400, "Only .pdf files are allowed")

    writer = PdfWriter()

    try:
        # Save and read in a single temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            saved_paths = []
            for f in files:
                safe_name = secure_filename(f.filename or "upload.pdf")
                safe_name = f"{uuid.uuid4().hex}_{safe_name}"
                pdf_path = os.path.join(tmpdir, safe_name)
                f.save(pdf_path)
                saved_paths.append(pdf_path)

            # Read pages and add to writer
            for pdf_path in saved_paths:
                with open(pdf_path, "rb") as fh:
                    reader = PdfReader(fh)
                    for page in reader.pages:
                        writer.add_page(page)

            # Write merged PDF to memory
            out_buf = io.BytesIO()
            writer.write(out_buf)
            out_buf.seek(0)

    except Exception:
        logging.exception("PDF merge failed")
        abort(500, "Merge failed")

    return send_file(
        out_buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="merged.pdf",
    )
@app.route('/pdfcompress', methods=['GET', 'POST'])
def pdfcompress():
    if request.method == 'GET':
        return render_template('pdfcompress.html', active_page='pdfcompress')
    if 'pdfcompress' not in request.files:
        abort(400, "No file uploaded")

    pdf_file = request.files['pdfcompress']
    filename = pdf_file.filename or 'upload.pdf'
    safe_name = secure_filename(filename)
    safe_name = f"{uuid.uuid4().hex}_{safe_name}"

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, safe_name)
        pdf_file.save(pdf_path)

        writer = PdfWriter(clone_from=pdf_path)
        for page in writer.pages:
            page.compress_content_streams(level=9)

        out_buf = io.BytesIO()
        writer.write(out_buf)
        out_buf.seek(0)

    return send_file(
        out_buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"compressed_{filename}",
    )
@app.route('/pdfprotect', methods=['GET', 'POST'])
def pdfprotect():
    if request.method == 'GET':
        return render_template('pdfprotect.html', active_page='pdfprotect')

    # Handle Set Password form
    if 'pdfprotect' in request.files:
        pdf_file = request.files['pdfprotect']
        password = request.form.get('password')
        if not pdf_file or not password:
            abort(400, "PDF file and password are required")
        filename = pdf_file.filename or 'upload.pdf'
        safe_name = secure_filename(filename)
        safe_name = f"{uuid.uuid4().hex}_{safe_name}"
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path = os.path.join(tmpdir, safe_name)
                pdf_file.save(pdf_path)
                reader = PdfReader(pdf_path)
                writer = PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)
                writer.encrypt(password)
                out_buf = io.BytesIO()
                writer.write(out_buf)
                out_buf.seek(0)
        except Exception:
            logging.exception("Protection failed")
            abort(500, "Protection failed")
        return send_file(
            out_buf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"protected_{filename}"
        )
    # If no file was uploaded, return an error
    return "No file uploaded.", 400



@app.route('/pdfunprotect', methods=['POST'])
def pdfunprotect():
    if 'pdfunprotect' not in request.files:
        return "No file uploaded.", 400
    pdf_file = request.files['pdfunprotect']
    password = request.form.get('password')

    if not pdf_file.filename.endswith('.pdf'):
        return "Invalid file type. Please upload a PDF.", 400

    try:
        pdf_stream = io.BytesIO(pdf_file.read())
        reader = PdfReader(pdf_stream)

        if reader.is_encrypted:
            if not password:
                return "PDF is encrypted. Please provide the password.", 400
            if reader.decrypt(password) == 0:
                return "Wrong password.", 401

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)

        return send_file(
            output_stream,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='decrypted_pdf.pdf'
        )

    except Exception as e:
        return f"Error processing PDF: {e}", 500

@app.route('/imageconvert', methods=['GET', 'POST'])
def imageconvert():
    if request.method == 'GET':
        return render_template('imageconvert.html', active_page='imageconvert')
    if 'image' not in request.files:
        abort(400, "No file uploaded")
    file = request.files['image']

    if file.filename == '':
        return "No selected file", 400

    if file:
        try:
            # Open the image using Pillow
            img = Image.open(file.stream)

            # Perform conversion (e.g., to JPEG)
            output_format = request.form.get('format', 'JPEG').upper()

            # Create an in-memory byte stream for the output image
            img_io = io.BytesIO()
            img.save(img_io, format=output_format)
            img_io.seek(0)  # Rewind the stream to the beginning

            # Send the converted image as a file
            return send_file(img_io, mimetype=f'image/{output_format.lower()}', as_attachment=True,
                             download_name=f'converted_image.{output_format.lower()}')

        except Exception as e:
            return f"Error processing image: {e}", 500


@app.route('/codeeditor', methods=['GET', 'POST'])
def codeeditor():
    if request.method == 'GET':
        return render_template('codeeditor.html', active_page='codeeditor')

    # Handle code saving/processing if needed
    code_content = request.form.get('code', '')
    language = request.form.get('language', 'javascript')

    # You can add code processing logic here if needed
    return {"status": "success", "message": "Code saved"}, 200

@app.route('/runcode', methods=['POST'])
def runcode():
    code = request.json.get('code', '')
    language = request.json.get('language', 'javascript')

    if language == 'python':
        try:
            # Create a temporary file and execute it
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10  # 10 second timeout
            )

            os.unlink(temp_file)  # Clean up

            if result.returncode == 0:
                return {'output': result.stdout, 'error': None}
            else:
                return {'output': result.stdout, 'error': result.stderr}

        except subprocess.TimeoutExpired:
            return {'output': '', 'error': 'Code execution timed out (10 seconds)'}
        except Exception as e:
            return {'output': '', 'error': str(e)}

    elif language == 'javascript':
        try:
            # Use Node.js for JavaScript execution
            result = subprocess.run(
                ['node', '-e', code],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return {'output': result.stdout, 'error': None}
            else:
                return {'output': result.stdout, 'error': result.stderr}

        except subprocess.TimeoutExpired:
            return {'output': '', 'error': 'Code execution timed out'}
        except Exception as e:
            return {'output': '', 'error': f'JavaScript execution failed: {str(e)}'}

    return {'output': '', 'error': f'Execution not supported for {language}'}


@app.route('/imagecompress', methods=['GET', 'POST'])
def imagecompress():
    if request.method == 'GET':
        return render_template('imagecompress.html', active_page='imagecompress')

    if 'image' not in request.files:
        abort(400, "No file uploaded")

    file = request.files['image']
    if file.filename == '':
        return "No selected file", 400

    quality = int(request.form.get('quality', 85))  # Default quality 85%

    try:
        # Open the image using Pillow
        img = Image.open(file.stream)

        # Convert to RGB if necessary (for JPEG compression)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Create an in-memory byte stream for the compressed image
        img_io = io.BytesIO()

        # Compress the image
        img.save(img_io, format='JPEG', quality=quality, optimize=True)
        img_io.seek(0)

        # Generate filename
        original_name = file.filename.rsplit('.', 1)[0]
        compressed_filename = f"compressed_{original_name}.jpg"

        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=compressed_filename
        )

    except Exception as e:
        return f"Error compressing image: {e}", 500

@app.route('/imageremovebg', methods=['GET', 'POST'])
def imageremovebg():
    if request.method == 'GET':
        return render_template('imageremovebg.html', active_page='imageremovebg')
    if 'image' not in request.files:
        return {'success': False, 'error': 'No file uploaded'}, 400
    file = request.files['image']
    if file.filename == '':
        return {'success': False, 'error': 'No selected file'}, 400
    try:
        import uuid, tempfile, os
        input_bytes = file.read()
        output_bytes = remove(input_bytes)
        # Save to a temp file with a unique id
        file_id = str(uuid.uuid4())
        temp_dir = tempfile.gettempdir()
        out_path = os.path.join(temp_dir, f'removebg_{file_id}.png')
        with open(out_path, 'wb') as f:
            f.write(output_bytes)
        return {'success': True, 'file_id': file_id}
    except Exception as e:
        return {'success': False, 'error': f'Error removing background: {e}'}, 500

@app.route('/download-removed-bg/<file_id>')
def download_removed_bg(file_id):
    import os, tempfile
    temp_dir = tempfile.gettempdir()
    out_path = os.path.join(temp_dir, f'removebg_{file_id}.png')
    if not os.path.exists(out_path):
        return 'File not found', 404
    return send_file(out_path, mimetype='image/png', as_attachment=True, download_name='no_bg.png')

@app.route('/latexeditor', methods=['GET', 'POST'])
def latexeditor():
    if request.method == 'GET':
        return render_template('latexeditor.html', active_page='latexeditor')

    # Handle LaTeX compilation
    latex_code = request.form.get('latex_code', '')

    if not latex_code.strip():
        return jsonify({'success': False, 'error': 'No LaTeX code provided'})

    try:
        # Compile LaTeX to PDF
        pdf_path = compile_latex_to_pdf(latex_code)
        
        if pdf_path and os.path.exists(pdf_path):
            # Read the PDF and return it
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()

            # Clean up temporary files
            os.unlink(pdf_path)

            return send_file(
                io.BytesIO(pdf_data),
                mimetype='application/pdf',
                as_attachment=True,
                download_name='latex_document.pdf'
            )
        else:
            return jsonify({'success': False, 'error': 'LaTeX compilation failed'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/compile-latex', methods=['POST'])
def compile_latex():
    """Compile LaTeX code and return compilation results"""
    try:
        data = request.get_json()
        latex_code = data.get('latex_code', '')

        if not latex_code.strip():
            return jsonify({'success': False, 'error': 'No LaTeX code provided'})

        # Compile LaTeX and get results
        result = compile_latex_with_output(latex_code)

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def find_pdflatex():
    """Find pdflatex executable in common MiKTeX installation paths"""
    # Common MiKTeX installation paths
    possible_paths = [
        r"C:\Users\{}\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe".format(os.environ.get('USERNAME', '')),
        r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
        r"C:\Program Files (x86)\MiKTeX\miktex\bin\x64\pdflatex.exe",
        r"C:\MiKTeX\miktex\bin\x64\pdflatex.exe",
        # Also check common TeX Live paths
        r"C:\texlive\2023\bin\win32\pdflatex.exe",
        r"C:\texlive\2024\bin\win32\pdflatex.exe",
        "pdflatex"  # Try system PATH as fallback
    ]

    for path in possible_paths:
        try:
            # Test if pdflatex works at this path
            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return path
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue

    return None

def setup_miktex():
    """Setup MiKTeX without update checking - just refresh databases"""
    pdflatex_path = find_pdflatex()
    if not pdflatex_path:
        return False

    try:
        # Get MiKTeX directory
        miktex_dir = os.path.dirname(pdflatex_path)
        
        # Only refresh file name database if needed, skip update checks entirely
        initexmf_path = os.path.join(miktex_dir, 'initexmf.exe')
        if os.path.exists(initexmf_path):
            try:
                # Only refresh the filename database, don't check for updates
                subprocess.run([initexmf_path, '--update-fndb', '--quiet'],
                             capture_output=True, text=True, timeout=15)
            except:
                pass  # Continue even if this fails

        return True  # Always return True to avoid blocking compilation

    except Exception:
        return True  # Don't fail compilation if setup fails

def compile_latex_to_pdf(latex_code):
    """Compile LaTeX code to PDF and return the PDF file path"""
    pdflatex_path = find_pdflatex()
    if not pdflatex_path:
        return None

    try:
        # Use a temporary directory in a path without spaces to avoid MiKTeX issues
        import string
        import random
        
        # Create temp directory in C:\Temp to avoid username spaces
        temp_base = r"C:\Temp"
        os.makedirs(temp_base, exist_ok=True)
        
        # Generate random directory name
        temp_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        tmpdir = os.path.join(temp_base, f"latex_{temp_name}")
        os.makedirs(tmpdir, exist_ok=True)
        
        try:
            # Create LaTeX file
            tex_file = os.path.join(tmpdir, 'document.tex')
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_code)

            # Set environment variables to disable MiKTeX problematic features
            env = os.environ.copy()
            env['MIKTEX_AUTOINSTALL'] = '0'  # Disable auto package installation
            env['MIKTEX_ENABLE_INSTALLER'] = '0'  # Disable installer prompts
            
            # First attempt: Try with nonstopmode
            try:
                result = subprocess.run(
                    [pdflatex_path, '-interaction=nonstopmode', '-output-directory', tmpdir, tex_file],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env
                )

                pdf_file = os.path.join(tmpdir, 'document.pdf')
                if os.path.exists(pdf_file):
                    # Copy to a permanent location (avoid spaces in path)
                    output_dir = r"C:\Temp"
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(output_dir, f'latex_output_{uuid.uuid4().hex}.pdf')
                    shutil.copy2(pdf_file, output_path)
                    return output_path

            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            # Second attempt: Try with batchmode (completely non-interactive)
            try:
                result = subprocess.run(
                    [pdflatex_path, '-interaction=batchmode', '-output-directory', tmpdir, tex_file],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env
                )

                pdf_file = os.path.join(tmpdir, 'document.pdf')
                if os.path.exists(pdf_file):
                    # Copy to a permanent location (avoid spaces in path)
                    output_dir = r"C:\Temp"
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(output_dir, f'latex_output_{uuid.uuid4().hex}.pdf')
                    shutil.copy2(pdf_file, output_path)
                    return output_path

            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            return None
        
        finally:
            # Clean up temporary directory
            try:
                if os.path.exists(tmpdir):
                    shutil.rmtree(tmpdir)
            except:
                pass  # Ignore cleanup errors

    except Exception:
        return None

def compile_latex_with_output(latex_code):
    """Compile LaTeX and return detailed results including errors"""
    pdflatex_path = find_pdflatex()

    if not pdflatex_path:
        return {
            'success': False,
            'error': 'LaTeX compiler not found',
            'details': '''MiKTeX is installed but pdflatex is not accessible. Please try:
1. Restart your application 
2. Or manually add MiKTeX to your system PATH
3. MiKTeX should be installed at: C:\\Users\\{}\\AppData\\Local\\Programs\\MiKTeX\\miktex\\bin\\x64\\
            
You can still use the LaTeX editor for code generation and templates.'''.format(os.environ.get('USERNAME', 'YourUsername')),
            'install_help': True
        }

    # Skip all MiKTeX update checking to avoid problems

    try:
        # Use a temporary directory in a path without spaces to avoid MiKTeX issues
        import string
        import random
        
        # Create temp directory in C:\Temp to avoid username spaces
        temp_base = r"C:\Temp"
        os.makedirs(temp_base, exist_ok=True)
        
        # Generate random directory name
        temp_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        tmpdir = os.path.join(temp_base, f"latex_{temp_name}")
        os.makedirs(tmpdir, exist_ok=True)
        
        try:
            # Create LaTeX file
            tex_file = os.path.join(tmpdir, 'document.tex')
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_code)

            # Set environment variables to disable MiKTeX problematic features
            env = os.environ.copy()
            env['MIKTEX_AUTOINSTALL'] = '0'  # Disable auto package installation
            env['MIKTEX_ENABLE_INSTALLER'] = '0'  # Disable installer prompts
            
            # Add MiKTeX to PATH if not already there
            miktex_dir = os.path.dirname(pdflatex_path)
            if miktex_dir not in env.get('PATH', ''):
                env['PATH'] = miktex_dir + ';' + env.get('PATH', '')

            pdf_file = os.path.join(tmpdir, 'document.pdf')
            log_file = os.path.join(tmpdir, 'document.log')

            # First attempt: Try with nonstopmode
            try:
                result = subprocess.run(
                    [pdflatex_path,
                     '-interaction=nonstopmode',
                     '-output-directory', tmpdir,
                     tex_file],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env
                )

                # Read log file for errors/warnings
                log_content = ""
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()

                # Check if compilation succeeded (PDF file exists)
                if os.path.exists(pdf_file):
                    # Check if it's just the MiKTeX update warning
                    if 'major issue: So far, you have not checked for MiKTeX updates' in (result.stderr or ''):
                        return {
                            'success': True,
                            'message': f'LaTeX compiled successfully! (MiKTeX update warning ignored)',
                            'log': extract_important_log_info(log_content) + '\n\nNote: MiKTeX shows an update warning but compilation succeeded.',
                            'has_pdf': True
                        }
                    else:
                        return {
                            'success': True,
                            'message': f'LaTeX compiled successfully!',
                            'log': extract_important_log_info(log_content),
                            'has_pdf': True
                        }

            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': 'LaTeX compilation timed out (30 seconds)',
                    'details': 'The compilation process took too long. Try simplifying your document.'
                }

            # Second attempt: Try with batchmode (completely non-interactive)
            try:
                result2 = subprocess.run(
                    [pdflatex_path,
                     '-interaction=batchmode',
                     '-output-directory', tmpdir,
                     tex_file],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env
                )

                # Re-read log file
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()

                if os.path.exists(pdf_file):
                    return {
                        'success': True,
                        'message': f'LaTeX compiled successfully (batch mode)!',
                        'log': extract_important_log_info(log_content) + '\n\nNote: MiKTeX update warning ignored - compilation succeeded.',
                        'has_pdf': True
                    }

            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': 'LaTeX compilation timed out (30 seconds)',
                    'details': 'The compilation process took too long. Try simplifying your document.'
                }

            # Final check: if PDF exists despite errors, consider it successful
            if os.path.exists(pdf_file):
                return {
                    'success': True,
                    'message': 'LaTeX compiled successfully (despite warnings)!',
                    'log': extract_important_log_info(log_content) + '\n\nNote: Some warnings occurred but PDF was generated successfully.',
                    'has_pdf': True
                }
            
            # If we get here, both attempts failed and no PDF was created
            errors = extract_errors_from_log(log_content) if log_content else None
            
            # Try to get more detailed error information
            error_details = []
            if hasattr(result, 'stderr') and result.stderr:
                error_details.append(f"Error output: {result.stderr}")
            if hasattr(result, 'stdout') and result.stdout:
                error_details.append(f"Standard output: {result.stdout}")
            if log_content:
                error_details.append(f"Log content: {log_content[-1000:]}")
            
            detailed_error = "\n\n".join(error_details) if error_details else "No detailed error information available"
            
            return {
                'success': False,
                'error': 'LaTeX compilation failed',
                'details': errors or detailed_error,
                'log': log_content[-2000:] if log_content else detailed_error
            }
        
        finally:
            # Clean up temporary directory
            try:
                if os.path.exists(tmpdir):
                    shutil.rmtree(tmpdir)
            except:
                pass  # Ignore cleanup errors

    except Exception as e:
        return {
            'success': False,
            'error': f'Compilation error: {str(e)}'
        }

def extract_errors_from_log(log_content):
    """Extract important error messages from LaTeX log"""
    if not log_content:
        return None

    errors = []
    lines = log_content.split('\n')

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('!') or 'Error:' in line or 'error:' in line.lower():
            # Found an error, collect context
            error_block = [line]
            # Get next few lines for context
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip():
                    error_block.append(lines[j].strip())
                else:
                    break
            errors.append('\n'.join(error_block))

    return '\n\n'.join(errors) if errors else None

def extract_important_log_info(log_content):
    """Extract warnings and important info from LaTeX log"""
    if not log_content:
        return "Compilation completed."

    warnings = []
    lines = log_content.split('\n')

    for line in lines:
        line = line.strip()
        if 'Warning:' in line or 'warning:' in line.lower():
            warnings.append(line)

    if warnings:
        return "Warnings:\n" + '\n'.join(warnings[:5])  # Max 5 warnings
    else:
        return "Compilation completed successfully."

@app.route('/generate-latex', methods=['POST'])
def generate_latex():
    """Generate LaTeX code using Gemini AI"""
    if not GEMINI_API_KEY:
        return jsonify({'error': 'Gemini API key not configured'}), 500

    try:
        data = request.get_json()
        prompt = data.get('prompt', '')

        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400

        # Initialize Gemini model - using the current available model name
        model = genai.GenerativeModel('models/gemini-2.5-flash')

        # Create a detailed prompt for LaTeX generation
        full_prompt = f"""Generate clean, well-formatted LaTeX code for the following request: {prompt}

Please provide only the LaTeX code without any markdown formatting or explanations. 
The code should be ready to compile and should include necessary packages if needed.
Focus on mathematical expressions, documents, tables, or whatever is requested.

Request: {prompt}"""

        # Generate response
        response = model.generate_content(full_prompt)
        latex_code = response.text.strip()

        # Clean up the response (remove markdown if present)
        if latex_code.startswith('```latex'):
            latex_code = latex_code[8:]
        if latex_code.startswith('```'):
            latex_code = latex_code[3:]
        if latex_code.endswith('```'):
            latex_code = latex_code[:-3]

        return jsonify({'latex_code': latex_code.strip()})

    except Exception as e:
        return jsonify({'error': f'Failed to generate LaTeX: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
