from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import require_admin
from app.database import get_db
from app.models.specifier import Specifier
from app.schemas.csv_import import CSVDryRunResponse, CSVCommitRequest, CSVCommitResponse
from app.services.csv_import import (
    validate_products_csv,
    validate_certifications_csv,
    validate_images_csv,
    commit_import,
)

router = APIRouter(prefix="/admin/import", tags=["admin-import"])

MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/products/dry-run", response_model=CSVDryRunResponse)
async def dry_run_products(
    file: UploadFile = File(...),
    _: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 10MB limit")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 10MB limit")

    try:
        return await validate_products_csv(content, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"CSV parsing error: {str(e)}")


@router.post("/certifications/dry-run", response_model=CSVDryRunResponse)
async def dry_run_certifications(
    file: UploadFile = File(...),
    _: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 10MB limit")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 10MB limit")

    try:
        return await validate_certifications_csv(content, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"CSV parsing error: {str(e)}")


@router.post("/images/dry-run", response_model=CSVDryRunResponse)
async def dry_run_images(
    file: UploadFile = File(...),
    _: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 10MB limit")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 10MB limit")

    try:
        return await validate_images_csv(content, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"CSV parsing error: {str(e)}")


@router.post("/commit", response_model=CSVCommitResponse)
async def commit(
    request: CSVCommitRequest,
    _: Specifier = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await commit_import(request.import_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Commit error: {str(e)}")
