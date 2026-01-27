"""
Admin endpoints for logs management.
Requires admin role for access.
"""

import os
from typing import Annotated
from fastapi import APIRouter, Query, HTTPException
from src.core.auth import AdminUser
from src.core.config import settings
from src.core.logs import logger

router = APIRouter(prefix="/admin/logs", tags=["admin"])


@router.get("/application")
def get_application_logs(
    admin_email: AdminUser,
    limit: int = Query(100, ge=1, le=1000),
    level: str | None = None
) -> dict:
    """
    Lê últimas N linhas do api.log local.

    Args:
        admin_email: Email do admin (verificado por dependency)
        limit: Número de linhas a retornar
        level: Filtrar por nível de log (INFO, WARNING, ERROR, etc.)

    Returns:
        dict: Contém logs, source e total
    """
    logger.info(f"Admin {admin_email} requesting application logs (limit={limit}, level={level})")

    log_file = "api.log"

    if not os.path.exists(log_file):
        return {
            "logs": [],
            "source": "local",
            "total": 0,
            "message": "Log file not found"
        }

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Filtrar por level se especificado
        if level:
            level_upper = level.upper()
            lines = [l for l in lines if f"[{level_upper}]" in l]

        # Pegar últimas N linhas
        result_lines = lines[-limit:] if len(lines) > limit else lines

        return {
            "logs": result_lines,
            "source": "local",
            "total": len(result_lines),
            "total_available": len(lines)
        }

    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read log file: {str(e)}"
        )


@router.get("/betterstack")
async def get_betterstack_logs(
    admin_email: AdminUser,
    limit: int = Query(100, ge=50, le=1000),
    query: str | None = None
) -> dict:
    """
    Busca logs do BetterStack via API.

    Args:
        admin_email: Email do admin (verificado por dependency)
        limit: Número de logs a retornar
        query: Query string para filtrar logs (opcional)

    Returns:
        dict: Resposta da API do BetterStack

    Raises:
        HTTPException: 503 se BetterStack não configurado
        HTTPException: 500 se erro na API do BetterStack
    """
    logger.info(f"Admin {admin_email} requesting BetterStack logs (limit={limit})")

    if not settings.BETTERSTACK_API_TOKEN or not settings.BETTERSTACK_SOURCE_ID:
        raise HTTPException(
            status_code=503,
            detail="BetterStack integration not configured. Set BETTERSTACK_API_TOKEN and BETTERSTACK_SOURCE_ID."
        )

    try:
        import httpx

        url = "https://telemetry.betterstack.com/api/v2/query/live-tail"
        headers = {"Authorization": f"Bearer {settings.BETTERSTACK_API_TOKEN}"}
        params = {
            "sources": settings.BETTERSTACK_SOURCE_ID,
            "limit": limit,
            "order": "newest_first"
        }

        if query:
            params["query"] = query

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"BetterStack API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"BetterStack API error: {e.response.text}"
        )
    except httpx.RequestError as e:
        logger.error(f"BetterStack request error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to BetterStack: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching BetterStack logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
