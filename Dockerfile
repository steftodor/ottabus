# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn
RUN pip install gunicorn

# Copy the entire project into the container
COPY . .

# Create a data directory
RUN mkdir -p /app/data

# Expose the port the app runs on
EXPOSE 9991

# Run the application with Gunicorn
CMD ["gunicorn", "--workers", "8", "--bind", "0.0.0.0:9991","--threads", "4", "app:app"]