"""
Shared utilities for data import.
"""
from fastapi import UploadFile, HTTPException
from src.core.logs import logger

async def read_csv_file(file: UploadFile) -> str:
    """
    Validates and reads a CSV file from an UploadFile.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser um CSV.")

    try:
        content = await file.read()
        return content.decode("utf-8")
    except Exception as e:
        logger.error("Error reading uploaded CSV file: %s", e)
        raise HTTPException(status_code=400, detail="Falha ao ler o arquivo CSV.") from e
