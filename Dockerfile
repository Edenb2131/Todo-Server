# Use a specific Python version
FROM --platform=linux/amd64 python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Expose port 8080
EXPOSE 3000

# Specify the command to run on container start
ENTRYPOINT ["python", "todoapp.py"]

# Health check
HEALTHCHECK --interval=5s --timeout=3s \
  CMD curl -f http://localhost:3000/ || exit 1
