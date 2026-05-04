import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID, uuid4
from typing import Optional

from app.config import get_settings
from app.database import get_db
from app.models.project import Project
from app.models.project_product import ProjectProduct
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.specifier import Specifier
from app.dependencies import get_current_specifier, require_specifier
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectProductAdd,
    ProjectProductUpdate,
    ProjectProductOut,
    ProjectOut,
    ProjectDetailOut,
    ProjectListResponse,
    ShareLinkResponse,
)
from app.services.events import emit_event

router = APIRouter(prefix="/projects", tags=["projects"])
settings = get_settings()


async def get_project_or_404(
    db: AsyncSession,
    project_id: UUID,
    specifier: Specifier,
) -> Project:
    project = await db.get(Project, project_id)
    if not project or project.specifier_id != specifier.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def build_project_product_out(
    project_product: ProjectProduct,
    db: AsyncSession,
) -> ProjectProductOut:
    product = project_product.product
    manufacturer_name = product.manufacturer.name if product.manufacturer else ""

    primary_image = next((img for img in product.images if img.is_primary), None)
    primary_image_url = primary_image.url if primary_image else None

    return ProjectProductOut(
        id=project_product.id,
        product_id=project_product.product_id,
        product_name=product.name,
        product_slug=product.slug,
        product_category=product.category,
        manufacturer_name=manufacturer_name,
        primary_image_url=primary_image_url,
        notes=project_product.notes,
        sort_order=project_product.sort_order,
        added_at=project_product.added_at,
    )


async def build_project_out(
    project: Project,
    product_count: int,
    db: AsyncSession,
) -> ProjectOut:
    share_url = None
    if project.is_shared and project.share_token:
        share_url = f"{settings.frontend_base_url}/shared/{project.share_token}"

    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        client_name=project.client_name,
        project_type=project.project_type,
        status=project.status,
        is_shared=project.is_shared,
        share_url=share_url,
        product_count=product_count,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    project = Project(
        id=uuid4(),
        specifier_id=specifier.id,
        name=body.name,
        description=body.description,
        client_name=body.client_name,
        project_type=body.project_type,
        status="active",
    )
    db.add(project)
    await db.flush()

    await emit_event(
        db,
        "project.created",
        specifier_id=specifier.id,
        project_id=project.id,
        properties={"name": project.name},
    )
    await db.commit()

    return await build_project_out(project, 0, db)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Project)
        .where(Project.specifier_id == specifier.id)
        .order_by(Project.updated_at.desc())
    )

    result = await db.execute(stmt)
    projects = result.scalars().all()

    items = []
    for project in projects:
        product_count_result = await db.execute(
            select(func.count(ProjectProduct.id)).where(ProjectProduct.project_id == project.id)
        )
        product_count = product_count_result.scalar() or 0

        items.append(await build_project_out(project, product_count, db))

    return ProjectListResponse(items=items, total=len(items))


@router.get("/{project_id}", response_model=ProjectDetailOut)
async def get_project(
    project_id: UUID,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.project_products).selectinload(ProjectProduct.product).selectinload(Product.manufacturer),
            selectinload(Project.project_products).selectinload(ProjectProduct.product).selectinload(Product.images),
        )
    )

    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project or project.specifier_id != specifier.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    product_count = len(project.project_products)
    project_out = await build_project_out(project, product_count, db)

    products = []
    for pp in project.project_products:
        products.append(await build_project_product_out(pp, db))

    return ProjectDetailOut(
        **project_out.dict(),
        products=products,
    )


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id, specifier)

    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    if body.client_name is not None:
        project.client_name = body.client_name
    if body.project_type is not None:
        project.project_type = body.project_type

    status_changed_to_archived = False
    if body.status is not None:
        if body.status not in ("active", "archived", "completed"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
        if body.status != project.status:
            project.status = body.status
            status_changed_to_archived = body.status == "archived"

    await db.flush()

    event_type = "project.archived" if status_changed_to_archived else "project.updated"
    await emit_event(db, event_type, specifier_id=specifier.id, project_id=project.id)

    await db.commit()

    product_count_result = await db.execute(
        select(func.count(ProjectProduct.id)).where(ProjectProduct.project_id == project.id)
    )
    product_count = product_count_result.scalar() or 0

    return await build_project_out(project, product_count, db)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id, specifier)

    await emit_event(
        db,
        "project.deleted",
        specifier_id=specifier.id,
        project_id=project.id,
        properties={"name": project.name},
    )

    await db.delete(project)
    await db.commit()


@router.post("/{project_id}/products", response_model=ProjectProductOut, status_code=status.HTTP_201_CREATED)
async def add_product_to_project(
    project_id: UUID,
    body: ProjectProductAdd,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id, specifier)

    stmt = (
        select(Product)
        .where(Product.id == body.product_id)
        .options(selectinload(Product.manufacturer), selectinload(Product.images))
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    existing = await db.execute(
        select(ProjectProduct).where(
            (ProjectProduct.project_id == project_id) & (ProjectProduct.product_id == body.product_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already in project",
        )

    pp = ProjectProduct(
        id=uuid4(),
        project_id=project_id,
        product_id=body.product_id,
        notes=body.notes,
    )
    db.add(pp)
    await db.flush()

    await emit_event(
        db,
        "project_product.added",
        specifier_id=specifier.id,
        project_id=project_id,
        product_id=body.product_id,
        properties={
            "product_name": product.name,
            "manufacturer_name": product.manufacturer.name if product.manufacturer else "",
        },
    )
    await db.commit()

    pp.product = product
    return await build_project_product_out(pp, db)


@router.delete("/{project_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product_from_project(
    project_id: UUID,
    product_id: UUID,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id, specifier)

    pp = await db.execute(
        select(ProjectProduct).where(
            (ProjectProduct.project_id == project_id) & (ProjectProduct.product_id == product_id)
        )
    )
    pp_obj = pp.scalar_one_or_none()

    if not pp_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not in project")

    await emit_event(
        db,
        "project_product.removed",
        specifier_id=specifier.id,
        project_id=project_id,
        product_id=product_id,
    )

    await db.delete(pp_obj)
    await db.commit()


@router.put("/{project_id}/products/{product_id}", response_model=ProjectProductOut)
async def update_project_product(
    project_id: UUID,
    product_id: UUID,
    body: ProjectProductUpdate,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id, specifier)

    pp = await db.execute(
        select(ProjectProduct).where(
            (ProjectProduct.project_id == project_id) & (ProjectProduct.product_id == product_id)
        ).options(
            selectinload(ProjectProduct.product).selectinload(Product.manufacturer),
            selectinload(ProjectProduct.product).selectinload(Product.images),
        )
    )
    pp_obj = pp.scalar_one_or_none()

    if not pp_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not in project")

    if body.notes is not None:
        pp_obj.notes = body.notes
    if body.sort_order is not None:
        pp_obj.sort_order = body.sort_order

    await db.flush()
    await db.commit()

    return await build_project_product_out(pp_obj, db)


@router.post("/{project_id}/share", response_model=ShareLinkResponse)
async def share_project(
    project_id: UUID,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id, specifier)

    if project.is_shared and project.share_token:
        share_url = f"{settings.frontend_base_url}/shared/{project.share_token}"
        return ShareLinkResponse(share_url=share_url, share_token=project.share_token)

    share_token = secrets.token_urlsafe(32)
    project.is_shared = True
    project.share_token = share_token

    await db.flush()

    await emit_event(
        db,
        "project.shared",
        specifier_id=specifier.id,
        project_id=project.id,
        properties={"share_token": share_token},
    )
    await db.commit()

    share_url = f"{settings.frontend_base_url}/shared/{share_token}"
    return ShareLinkResponse(share_url=share_url, share_token=share_token)


@router.delete("/{project_id}/share", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_project(
    project_id: UUID,
    specifier: Specifier = Depends(require_specifier),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id, specifier)

    project.is_shared = False
    project.share_token = None

    await db.flush()

    await emit_event(
        db,
        "project.unshared",
        specifier_id=specifier.id,
        project_id=project.id,
    )
    await db.commit()


@router.get("/shared/{share_token}", response_model=ProjectDetailOut)
async def view_shared_project(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Project)
        .where((Project.share_token == share_token) & (Project.is_shared == True))
        .options(
            selectinload(Project.project_products).selectinload(ProjectProduct.product).selectinload(Product.manufacturer),
            selectinload(Project.project_products).selectinload(ProjectProduct.product).selectinload(Product.images),
        )
    )

    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared project not found")

    product_count = len(project.project_products)
    project_out = await build_project_out(project, product_count, db)

    products = []
    for pp in project.project_products:
        products.append(await build_project_product_out(pp, db))

    await emit_event(
        db,
        "project.viewed_shared",
        project_id=project.id,
        properties={"share_token": share_token},
    )
    await db.commit()

    return ProjectDetailOut(
        **project_out.dict(),
        products=products,
    )
