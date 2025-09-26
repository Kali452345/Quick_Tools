import logging
import os
import uuid
from logging import exception
from flask import Flask, render_template, request, abort, send_file
from pdf2docx import Converter
from pypdf import PdfWriter, PdfReader
import subprocess
import qrcode
import io
import base64
from PIL import Image


import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)