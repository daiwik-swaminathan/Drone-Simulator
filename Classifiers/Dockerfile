# Use an official Python image as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the contents of the Classifiers directory into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose any necessary ports (optional)
EXPOSE 5000

# Make print lines show up
ENV PYTHONUNBUFFERED=1

# Command to run your script
CMD ["python", "image_classifier.py"]

