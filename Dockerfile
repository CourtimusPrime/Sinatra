# Use an official Python image
FROM python:3.11.7-slim

# Set the working directory in the container
WORKDIR /app

# Copy dependency files first (so Docker can cache them)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000
 
# Run the app with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]