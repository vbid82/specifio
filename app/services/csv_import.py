import csv
import json
import os
import uuid
from io import StringIO
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.models.manufacturer import Manufacturer
from app.models.product import Product
from app.models.product_certification import ProductCertification
from app.models.product_image import ProductImage
from app.schemas.csv_import import (
    CSVDryRunResponse,
    CSVCommitResponse,
    CSVValidationError,
    CSVValidationWarning,
)

CANONICAL_CATEGORIES = frozenset([
    "wallcovering", "surface_panel", "acoustic_panel", "ceiling_tile",
    "ceiling_system", "textile", "mural", "decorative_paint",
    "liquid_metal", "bespoke_finish", "decorative_mesh", "composite_surface"
])

CANONICAL_COMMERCIAL_GRADES = frozenset([
    "type_i", "type_ii", "type_iii", "contract_grade",
    "residential_grade", "marine_grade", "exterior_grade"
])

CANONICAL_CERTIFICATION_CODES = frozenset([
    "EUROCLASS_A1", "EUROCLASS_A2", "EUROCLASS_B", "EUROCLASS_C",
    "EUROCLASS_D", "EUROCLASS_E", "EUROCLASS_F", "EUROCLASS_B_S1",
    "EUROCLASS_B_S2_D0", "FSC", "PEFC", "OEKO_TEX", "GREENGUARD",
    "GREENGUARD_GOLD", "CRADLE_TO_CRADLE", "EPD", "CE_MARK", "IMO"
])

CANONICAL_FIRE_CLASSES = frozenset(["A1", "A2", "B", "C", "D", "E", "F"])
CANONICAL_SMOKE_CLASSES = frozenset(["s1", "s2", "s3"])
CANONICAL_DROPLET_CLASSES = frozenset(["d0", "d1", "d2"])
CANONICAL_PRICE_VISIBILITY = frozenset(["public", "on_request", "trade_only", "registered"])
CANONICAL_WEIGHT_UNITS = frozenset(["gsm", "kg_m2", "kg", "g"])
CANONICAL_SAMPLE_TYPES = frozenset(["physical", "digital", "both"])

IMPORT_TEMP_DIR = Path("/tmp/specifio-csv-imports")


def parse_boolean(value: Optional[str]) -> Optional[bool]:
    if value is None or value == "":
        return None
    v = str(value).strip().lower()
    if v in ("true", "yes", "1"):
        return True
    if v in ("false", "no", "0"):
        return False
    return None


def parse_numeric(value: Optional[str]) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).strip())
    except:
        return None


def generate_slug(name: str, db_slugs: set = None) -> str:
    if db_slugs is None:
        db_slugs = set()

    slug = name.lower()
    slug = slug.replace(" ", "-").replace("_", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    slug = "-".join(filter(None, slug.split("-")))

    if not slug:
        slug = "product"

    if slug not in db_slugs:
        return slug

    counter = 2
    while f"{slug}-{counter}" in db_slugs:
        counter += 1
    return f"{slug}-{counter}"


async def validate_products_csv(file_content: bytes, db: AsyncSession) -> CSVDryRunResponse:
    IMPORT_TEMP_DIR.mkdir(exist_ok=True)
    import_id = str(uuid.uuid4())
    import_dir = IMPORT_TEMP_DIR / import_id
    import_dir.mkdir(exist_ok=True)

    errors: List[CSVValidationError] = []
    warnings: List[CSVValidationWarning] = []
    valid_rows: List[Dict[str, Any]] = []
    preview: List[Dict[str, Any]] = []

    # Decode with BOM handling
    try:
        text = file_content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = file_content.decode("utf-8")

    if not text.strip():
        return CSVDryRunResponse(
            import_id=import_id,
            file_type="products",
            total_rows=0,
            valid_rows=0,
            errors=[CSVValidationError(row=0, column="", value=None, error="CSV file is empty")],
        )

    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        return CSVDryRunResponse(
            import_id=import_id,
            file_type="products",
            total_rows=0,
            valid_rows=0,
            errors=[CSVValidationError(row=0, column="", value=None, error="CSV file is empty")],
        )

    required_columns = {"manufacturer_slug", "sku", "name", "category"}
    missing_cols = required_columns - set(reader.fieldnames)
    if missing_cols:
        errors.append(CSVValidationError(
            row=0,
            column=",".join(missing_cols),
            value=None,
            error=f"Missing required columns: {', '.join(missing_cols)}"
        ))

    # Preload manufacturers and slugs
    mfg_stmt = select(Manufacturer.id, Manufacturer.slug)
    mfg_result = await db.execute(mfg_stmt)
    mfg_map = {slug: id for id, slug in mfg_result.all()}

    prod_stmt = select(func.count(Product.id)).where(Product.is_active == True)
    total_prod = (await db.execute(prod_stmt)).scalar() or 0

    slug_stmt = select(Product.slug)
    slug_result = await db.execute(slug_stmt)
    db_slugs = set(slug_result.scalars().all())

    sku_by_mfg: Dict[UUID, set] = {}
    for mfg_id in mfg_map.values():
        sku_stmt = select(Product.sku).where(Product.manufacturer_id == mfg_id)
        sku_result = await db.execute(sku_stmt)
        sku_by_mfg[mfg_id] = set(sku_result.scalars().all())

    csv_skus_by_mfg: Dict[UUID, set] = {}
    row_num = 1
    total_rows = 0

    for row in reader:
        total_rows += 1
        row_num = total_rows + 1
        row_errors = []
        row_warnings = []

        manufacturer_slug = (row.get("manufacturer_slug") or "").strip()
        sku = (row.get("sku") or "").strip()
        name = (row.get("name") or "").strip()
        category = (row.get("category") or "").strip()

        if not manufacturer_slug:
            row_errors.append(("manufacturer_slug", None, "Required field is empty"))
        elif manufacturer_slug not in mfg_map:
            row_errors.append(("manufacturer_slug", manufacturer_slug, f"Manufacturer '{manufacturer_slug}' not found"))
        else:
            mfg_id = mfg_map[manufacturer_slug]
            if mfg_id not in csv_skus_by_mfg:
                csv_skus_by_mfg[mfg_id] = set()

        if not sku:
            row_errors.append(("sku", None, "Required field is empty"))
        elif manufacturer_slug in mfg_map:
            mfg_id = mfg_map[manufacturer_slug]
            if sku in sku_by_mfg[mfg_id]:
                row_errors.append(("sku", sku, f"SKU already exists for this manufacturer"))
            elif sku in csv_skus_by_mfg.get(mfg_id, set()):
                row_errors.append(("sku", sku, f"Duplicate SKU within this CSV"))
            else:
                csv_skus_by_mfg[mfg_id].add(sku)

        if not name:
            row_errors.append(("name", None, "Required field is empty"))

        if not category:
            row_errors.append(("category", None, "Required field is empty"))
        elif category not in CANONICAL_CATEGORIES:
            row_errors.append(("category", category, f"Unknown category. Valid: {', '.join(sorted(CANONICAL_CATEGORIES))}"))

        fire_class_eu = (row.get("fire_class_eu") or "").strip()
        if fire_class_eu and fire_class_eu not in CANONICAL_FIRE_CLASSES:
            row_errors.append(("fire_class_eu", fire_class_eu, f"Invalid fire class. Valid: {', '.join(sorted(CANONICAL_FIRE_CLASSES))}"))

        fire_smoke_class_eu = (row.get("fire_smoke_class_eu") or "").strip()
        if fire_smoke_class_eu and fire_smoke_class_eu not in CANONICAL_SMOKE_CLASSES:
            row_errors.append(("fire_smoke_class_eu", fire_smoke_class_eu, f"Invalid smoke class. Valid: {', '.join(sorted(CANONICAL_SMOKE_CLASSES))}"))

        fire_droplet_class_eu = (row.get("fire_droplet_class_eu") or "").strip()
        if fire_droplet_class_eu and fire_droplet_class_eu not in CANONICAL_DROPLET_CLASSES:
            row_errors.append(("fire_droplet_class_eu", fire_droplet_class_eu, f"Invalid droplet class. Valid: {', '.join(sorted(CANONICAL_DROPLET_CLASSES))}"))

        commercial_grade = (row.get("commercial_grade") or "").strip()
        if commercial_grade:
            grades = [g.strip() for g in commercial_grade.split("|") if g.strip()]
            for grade in grades:
                if grade not in CANONICAL_COMMERCIAL_GRADES:
                    row_errors.append(("commercial_grade", commercial_grade, f"Invalid grade '{grade}'. Valid: {', '.join(sorted(CANONICAL_COMMERCIAL_GRADES))}"))

        for field in ["width_mm", "height_mm", "thickness_mm", "weight_value", "repeat_width_mm", "repeat_height_mm", "nrc_value"]:
            value = (row.get(field) or "").strip()
            if value and parse_numeric(value) is None:
                row_errors.append((field, value, f"Expected numeric value"))

        for field in ["custom_colorway", "sample_available", "is_bespoke", "is_active"]:
            value = (row.get(field) or "").strip()
            if value and parse_boolean(value) is None:
                row_errors.append((field, value, f"Expected boolean (true/false/yes/no/1/0)"))

        price_visibility = (row.get("price_visibility") or "").strip()
        if price_visibility and price_visibility not in CANONICAL_PRICE_VISIBILITY:
            row_errors.append(("price_visibility", price_visibility, f"Invalid visibility. Valid: {', '.join(sorted(CANONICAL_PRICE_VISIBILITY))}"))

        weight_unit = (row.get("weight_unit") or "").strip()
        if weight_unit and weight_unit not in CANONICAL_WEIGHT_UNITS:
            row_errors.append(("weight_unit", weight_unit, f"Invalid unit. Valid: {', '.join(sorted(CANONICAL_WEIGHT_UNITS))}"))

        sample_type = (row.get("sample_type") or "").strip()
        if sample_type and sample_type not in CANONICAL_SAMPLE_TYPES:
            row_errors.append(("sample_type", sample_type, f"Invalid type. Valid: {', '.join(sorted(CANONICAL_SAMPLE_TYPES))}"))

        # Warnings for common empty optional fields
        if not (row.get("slug") or "").strip() and name:
            row_warnings.append(("slug", None, "Will be auto-generated from name"))
        if not (row.get("description") or "").strip():
            row_warnings.append(("description", None, "Empty optional field"))

        for error in row_errors:
            errors.append(CSVValidationError(row=row_num, column=error[0], value=error[1], error=error[2]))

        for warning in row_warnings:
            warnings.append(CSVValidationWarning(row=row_num, column=warning[0], value=warning[1], warning=warning[2]))

        if not row_errors:
            slug = (row.get("slug") or "").strip()
            if not slug:
                slug = generate_slug(name, db_slugs)
                db_slugs.add(slug)

            row_data = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items() if v}
            row_data["slug"] = slug
            valid_rows.append(row_data)
            if len(preview) < 5:
                preview.append(row_data)

    (import_dir / "products.json").write_text(json.dumps(valid_rows, indent=2, default=str))

    return CSVDryRunResponse(
        import_id=import_id,
        file_type="products",
        total_rows=total_rows,
        valid_rows=len(valid_rows),
        errors=errors,
        warnings=warnings,
        preview=preview,
    )


async def validate_certifications_csv(file_content: bytes, db: AsyncSession) -> CSVDryRunResponse:
    IMPORT_TEMP_DIR.mkdir(exist_ok=True)
    import_id = str(uuid.uuid4())
    import_dir = IMPORT_TEMP_DIR / import_id
    import_dir.mkdir(exist_ok=True)

    errors: List[CSVValidationError] = []
    warnings: List[CSVValidationWarning] = []
    valid_rows: List[Dict[str, Any]] = []
    preview: List[Dict[str, Any]] = []

    try:
        text = file_content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = file_content.decode("utf-8")

    if not text.strip():
        return CSVDryRunResponse(
            import_id=import_id,
            file_type="certifications",
            total_rows=0,
            valid_rows=0,
            errors=[CSVValidationError(row=0, column="", value=None, error="CSV file is empty")],
        )

    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        return CSVDryRunResponse(
            import_id=import_id,
            file_type="certifications",
            total_rows=0,
            valid_rows=0,
            errors=[CSVValidationError(row=0, column="", value=None, error="CSV file is empty")],
        )

    required_columns = {"product_sku", "certification_code"}
    missing_cols = required_columns - set(reader.fieldnames)
    if missing_cols:
        errors.append(CSVValidationError(
            row=0,
            column=",".join(missing_cols),
            value=None,
            error=f"Missing required columns: {', '.join(missing_cols)}"
        ))

    prod_stmt = select(Product.id, Product.sku, Product.manufacturer_id)
    prod_result = await db.execute(prod_stmt)
    sku_to_id = {(sku, mfg_id): id for id, sku, mfg_id in prod_result.all()}

    row_num = 1
    total_rows = 0

    for row in reader:
        total_rows += 1
        row_num = total_rows + 1
        row_errors = []

        product_sku = (row.get("product_sku") or "").strip()
        cert_code = (row.get("certification_code") or "").strip()

        if not product_sku:
            row_errors.append(("product_sku", None, "Required field is empty"))
        else:
            found = False
            for (sku, _), _ in sku_to_id.items():
                if sku == product_sku:
                    found = True
                    break
            if not found:
                row_errors.append(("product_sku", product_sku, f"Product SKU not found"))

        if not cert_code:
            row_errors.append(("certification_code", None, "Required field is empty"))
        elif cert_code not in CANONICAL_CERTIFICATION_CODES:
            row_errors.append(("certification_code", cert_code, f"Unknown code. Valid: {', '.join(sorted(CANONICAL_CERTIFICATION_CODES))}"))

        valid_until = (row.get("valid_until") or "").strip()
        if valid_until:
            try:
                from datetime import datetime
                datetime.strptime(valid_until, "%Y-%m-%d")
            except:
                row_errors.append(("valid_until", valid_until, "Expected ISO date (YYYY-MM-DD)"))

        for error in row_errors:
            errors.append(CSVValidationError(row=row_num, column=error[0], value=error[1], error=error[2]))

        if not row_errors:
            row_data = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items() if v}
            valid_rows.append(row_data)
            if len(preview) < 5:
                preview.append(row_data)

    (import_dir / "certifications.json").write_text(json.dumps(valid_rows, indent=2, default=str))

    return CSVDryRunResponse(
        import_id=import_id,
        file_type="certifications",
        total_rows=total_rows,
        valid_rows=len(valid_rows),
        errors=errors,
        warnings=warnings,
        preview=preview,
    )


async def validate_images_csv(file_content: bytes, db: AsyncSession) -> CSVDryRunResponse:
    IMPORT_TEMP_DIR.mkdir(exist_ok=True)
    import_id = str(uuid.uuid4())
    import_dir = IMPORT_TEMP_DIR / import_id
    import_dir.mkdir(exist_ok=True)

    errors: List[CSVValidationError] = []
    warnings: List[CSVValidationWarning] = []
    valid_rows: List[Dict[str, Any]] = []
    preview: List[Dict[str, Any]] = []

    try:
        text = file_content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = file_content.decode("utf-8")

    if not text.strip():
        return CSVDryRunResponse(
            import_id=import_id,
            file_type="images",
            total_rows=0,
            valid_rows=0,
            errors=[CSVValidationError(row=0, column="", value=None, error="CSV file is empty")],
        )

    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        return CSVDryRunResponse(
            import_id=import_id,
            file_type="images",
            total_rows=0,
            valid_rows=0,
            errors=[CSVValidationError(row=0, column="", value=None, error="CSV file is empty")],
        )

    required_columns = {"product_sku", "url"}
    missing_cols = required_columns - set(reader.fieldnames)
    if missing_cols:
        errors.append(CSVValidationError(
            row=0,
            column=",".join(missing_cols),
            value=None,
            error=f"Missing required columns: {', '.join(missing_cols)}"
        ))

    prod_stmt = select(Product.id, Product.sku)
    prod_result = await db.execute(prod_stmt)
    sku_to_id = {sku: id for id, sku in prod_result.all()}

    row_num = 1
    total_rows = 0

    for row in reader:
        total_rows += 1
        row_num = total_rows + 1
        row_errors = []

        product_sku = (row.get("product_sku") or "").strip()
        url = (row.get("url") or "").strip()

        if not product_sku:
            row_errors.append(("product_sku", None, "Required field is empty"))
        elif product_sku not in sku_to_id:
            row_errors.append(("product_sku", product_sku, f"Product SKU not found"))

        if not url:
            row_errors.append(("url", None, "Required field is empty"))
        elif not (url.startswith("http://") or url.startswith("https://")):
            row_errors.append(("url", url, "URL must start with http:// or https://"))

        sort_order = (row.get("sort_order") or "0").strip()
        if sort_order and not sort_order.isdigit():
            row_errors.append(("sort_order", sort_order, "Expected integer"))

        is_primary = (row.get("is_primary") or "false").strip()
        if is_primary and parse_boolean(is_primary) is None:
            row_errors.append(("is_primary", is_primary, "Expected boolean (true/false/yes/no/1/0)"))

        for error in row_errors:
            errors.append(CSVValidationError(row=row_num, column=error[0], value=error[1], error=error[2]))

        if not row_errors:
            row_data = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items() if v}
            row_data["sort_order"] = int(sort_order) if sort_order else 0
            row_data["is_primary"] = parse_boolean(is_primary) or False
            valid_rows.append(row_data)
            if len(preview) < 5:
                preview.append(row_data)

    (import_dir / "images.json").write_text(json.dumps(valid_rows, indent=2, default=str))

    return CSVDryRunResponse(
        import_id=import_id,
        file_type="images",
        total_rows=total_rows,
        valid_rows=len(valid_rows),
        errors=errors,
        warnings=warnings,
        preview=preview,
    )


async def commit_import(import_id: str, db: AsyncSession) -> CSVCommitResponse:
    import_dir = IMPORT_TEMP_DIR / import_id

    if not import_dir.exists():
        raise ValueError(f"Import session not found or expired: {import_id}")

    products_file = import_dir / "products.json"
    certifications_file = import_dir / "certifications.json"
    images_file = import_dir / "images.json"

    if products_file.exists():
        return await _commit_products(products_file, db, import_dir)
    elif certifications_file.exists():
        return await _commit_certifications(certifications_file, db, import_dir)
    elif images_file.exists():
        return await _commit_images(images_file, db, import_dir)
    else:
        raise ValueError(f"No valid CSV data found in import session: {import_id}")


async def _commit_products(file_path: Path, db: AsyncSession, import_dir: Path) -> CSVCommitResponse:
    data = json.loads(file_path.read_text())
    errors: List[CSVValidationError] = []
    rows_inserted = 0
    rows_skipped = 0

    mfg_stmt = select(Manufacturer.id, Manufacturer.slug)
    mfg_result = await db.execute(mfg_stmt)
    mfg_map = {slug: id for id, slug in mfg_result.all()}

    for row_idx, row_data in enumerate(data, start=2):
        try:
            mfg_slug = row_data.get("manufacturer_slug", "")
            mfg_id = mfg_map.get(mfg_slug)
            if not mfg_id:
                errors.append(CSVValidationError(row=row_idx, column="manufacturer_slug", value=mfg_slug, error="Manufacturer not found"))
                rows_skipped += 1
                continue

            product = Product(
                id=uuid.uuid4(),
                manufacturer_id=mfg_id,
                sku=row_data.get("sku", ""),
                name=row_data.get("name", ""),
                slug=row_data.get("slug", ""),
                category=row_data.get("category", ""),
                subcategory=row_data.get("subcategory"),
                short_description=row_data.get("description", ""),
                long_description=row_data.get("description"),
                primary_material=row_data.get("material_composition", ""),
                secondary_material=row_data.get("finish"),
                finish_type=row_data.get("finish"),
                colorway_count=int(row_data["colorway_count"]) if row_data.get("colorway_count") else None,
                custom_colorway=parse_boolean(row_data.get("custom_colorway", "false")) or False,
                width_mm=parse_numeric(row_data.get("width_mm")),
                height_mm=parse_numeric(row_data.get("height_mm")),
                thickness_mm=parse_numeric(row_data.get("thickness_mm")),
                weight_value=parse_numeric(row_data.get("weight_value")),
                weight_unit=row_data.get("weight_unit"),
                repeat_width_mm=parse_numeric(row_data.get("repeat_width_mm")),
                repeat_height_mm=parse_numeric(row_data.get("repeat_vertical_mm")),
                fire_class_eu=row_data.get("fire_class_eu"),
                fire_smoke_class_eu=row_data.get("fire_smoke_class_eu"),
                fire_droplet_class_eu=row_data.get("fire_droplet_class_eu"),
                nrc_value=parse_numeric(row_data.get("acoustic_nrc")),
                acoustic_class=row_data.get("acoustic_class"),
                commercial_grade=[g.strip() for g in (row_data.get("commercial_grade", "")).split("|") if g.strip()],
                voc_class=row_data.get("voc_class"),
                recycled_content_pct=int(row_data["recycled_content_pct"]) if row_data.get("recycled_content_pct") else None,
                suitable_environments=row_data.get("collection"),
                price_visibility=row_data.get("price_visibility", "on_request"),
                indicative_price_eur=parse_numeric(row_data.get("price_per_unit")),
                price_unit=row_data.get("price_unit"),
                moq=int(row_data["min_order_qty"]) if row_data.get("min_order_qty") else 1,
                moq_unit=row_data.get("min_order_unit"),
                lead_time_weeks_min=int(row_data["lead_time_weeks"]) if row_data.get("lead_time_weeks") else 0,
                sample_available=parse_boolean(row_data.get("sample_available", "false")) or False,
                sample_type=row_data.get("sample_type"),
                made_to_order=parse_boolean(row_data.get("is_bespoke", "false")) or False,
                is_active=parse_boolean(row_data.get("is_active", "true")) if row_data.get("is_active") else True,
            )

            db.add(product)
            rows_inserted += 1
        except IntegrityError as e:
            await db.rollback()
            sku = row_data.get("sku", "")
            errors.append(CSVValidationError(row=row_idx, column="sku", value=sku, error=f"Constraint violation: {str(e)}"))
            rows_skipped += 1
        except Exception as e:
            await db.rollback()
            errors.append(CSVValidationError(row=row_idx, column="", value=None, error=f"Error: {str(e)}"))
            rows_skipped += 1

    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        errors.append(CSVValidationError(row=0, column="", value=None, error=f"Commit failed: {str(e)}"))

    import_dir_to_delete = import_dir
    import_dir_to_delete = str(import_dir_to_delete)
    import os
    import shutil
    try:
        shutil.rmtree(import_dir_to_delete)
    except:
        pass

    return CSVCommitResponse(
        file_type="products",
        rows_inserted=rows_inserted,
        rows_skipped=rows_skipped,
        errors=errors,
    )


async def _commit_certifications(file_path: Path, db: AsyncSession, import_dir: Path) -> CSVCommitResponse:
    data = json.loads(file_path.read_text())
    errors: List[CSVValidationError] = []
    rows_inserted = 0
    rows_skipped = 0

    prod_stmt = select(Product.id, Product.sku)
    prod_result = await db.execute(prod_stmt)
    sku_to_id = {sku: id for id, sku in prod_result.all()}

    for row_idx, row_data in enumerate(data, start=2):
        try:
            product_sku = row_data.get("product_sku", "")
            product_id = sku_to_id.get(product_sku)
            if not product_id:
                errors.append(CSVValidationError(row=row_idx, column="product_sku", value=product_sku, error="Product not found"))
                rows_skipped += 1
                continue

            from datetime import datetime
            valid_until = None
            if row_data.get("valid_until"):
                valid_until = datetime.strptime(row_data["valid_until"], "%Y-%m-%d").date()

            cert = ProductCertification(
                id=uuid.uuid4(),
                product_id=product_id,
                certification_code=row_data.get("certification_code", ""),
                certification_name=row_data.get("certification_body"),
                issued_by=row_data.get("certification_body"),
                certificate_number=row_data.get("certificate_number"),
                valid_until=valid_until,
                document_url=row_data.get("document_url"),
            )

            db.add(cert)
            rows_inserted += 1
        except IntegrityError as e:
            await db.rollback()
            errors.append(CSVValidationError(row=row_idx, column="", value=None, error=f"Constraint violation: {str(e)}"))
            rows_skipped += 1
        except Exception as e:
            await db.rollback()
            errors.append(CSVValidationError(row=row_idx, column="", value=None, error=f"Error: {str(e)}"))
            rows_skipped += 1

    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        errors.append(CSVValidationError(row=0, column="", value=None, error=f"Commit failed: {str(e)}"))

    import shutil
    try:
        shutil.rmtree(str(import_dir))
    except:
        pass

    return CSVCommitResponse(
        file_type="certifications",
        rows_inserted=rows_inserted,
        rows_skipped=rows_skipped,
        errors=errors,
    )


async def _commit_images(file_path: Path, db: AsyncSession, import_dir: Path) -> CSVCommitResponse:
    data = json.loads(file_path.read_text())
    errors: List[CSVValidationError] = []
    rows_inserted = 0
    rows_skipped = 0

    prod_stmt = select(Product.id, Product.sku)
    prod_result = await db.execute(prod_stmt)
    sku_to_id = {sku: id for id, sku in prod_result.all()}

    for row_idx, row_data in enumerate(data, start=2):
        try:
            product_sku = row_data.get("product_sku", "")
            product_id = sku_to_id.get(product_sku)
            if not product_id:
                errors.append(CSVValidationError(row=row_idx, column="product_sku", value=product_sku, error="Product not found"))
                rows_skipped += 1
                continue

            image = ProductImage(
                id=uuid.uuid4(),
                product_id=product_id,
                url=row_data.get("url", ""),
                alt_text=row_data.get("alt_text"),
                sort_order=row_data.get("sort_order", 0),
                is_primary=row_data.get("is_primary", False),
            )

            db.add(image)
            rows_inserted += 1
        except IntegrityError as e:
            await db.rollback()
            errors.append(CSVValidationError(row=row_idx, column="", value=None, error=f"Constraint violation: {str(e)}"))
            rows_skipped += 1
        except Exception as e:
            await db.rollback()
            errors.append(CSVValidationError(row=row_idx, column="", value=None, error=f"Error: {str(e)}"))
            rows_skipped += 1

    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        errors.append(CSVValidationError(row=0, column="", value=None, error=f"Commit failed: {str(e)}"))

    import shutil
    try:
        shutil.rmtree(str(import_dir))
    except:
        pass

    return CSVCommitResponse(
        file_type="images",
        rows_inserted=rows_inserted,
        rows_skipped=rows_skipped,
        errors=errors,
    )
