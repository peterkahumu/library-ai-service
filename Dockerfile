FROM python:3.11-slim

WORKDIR /app

# Ensure Python output is sent straight to terminal (e.g. your container log)
# without being first buffered and that you can see the output of your application
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN useradd appuser && chown -R appuser /app
USER appuser

COPY --chown=appuser:appuser . .

# Expose port and run uvicorn
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
