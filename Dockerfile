
# Use the official Python runtime image
FROM python:3.11-slim

# Create a specific user and the app directory
RUN useradd -m -r python && \
    mkdir /app && \
    chown -R python /app

# Set the working directory inside the container
WORKDIR /app/checklistapp

# Set environment variables 
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1 

# Upgrade pip
RUN pip install --upgrade pip 

# Copy the Django project  and install dependencies
COPY --chown=python:python ./requirements.txt  /app/requirements.txt

# run this command to install all dependencies 
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the Django project to the container
COPY --chown=python:python ./checklistapp/ /app/checklistapp/

# create folder for staticfile that is writable
RUN mkdir -p /app/checklistapp/staticfiles
RUN chown python:python /app/checklistapp/staticfiles
RUN chmod 744 /app/checklistapp/staticfiles

USER python

# Expose the Django port
EXPOSE 8000

# Run Django’s development server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "checklistapp.wsgi:application"]