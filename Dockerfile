# Use an official Python image (slim = smaller size)
FROM python:3.11-slim

# Install LibreOffice (for DOCX → PDF conversion)
RUN apt-get update && apt-get install -y libreoffice && apt-get clean

# Set working directory inside container
WORKDIR /app

# Copy dependency list and install
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose port for Render
EXPOSE 10000

# Run the app with Gunicorn
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:10000"]
