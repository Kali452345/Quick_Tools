import os
import uuid
import logging
from flask import Flask, render_template, request, abort, send_file
from pdf2docx import Converter
import subprocess
import qrcode
import io
import base64


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
    return render_template('index.html', qrcode_img=qrcode_img)
@app.route('/pdftoword', methods=['GET', 'POST'])  # Allow both GET (show form) and POST (handle upload)
def pdftoword():
    if request.method == 'GET':
        # If the user visits the page, just show the upload form
        return render_template('pdftoword.html')

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
        return render_template('wordtopdf.html')

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


if __name__ == '__main__':
    app.run(debug=True)