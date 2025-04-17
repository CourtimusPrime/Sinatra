# Uses a lightweight version of Python for the base image
FROM python:3.13-slim

# Set the working directory in the /app. Everything runs from this directory.
WORKDIR /app

# Copy dependency files first (so Docker can cache them)
COPY requirements.txt .

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade setuptools && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000
 
# Run the app with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]