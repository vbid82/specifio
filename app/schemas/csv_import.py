from pydantic import BaseModel, Field
from typing import Optional, List


class CSVValidationError(BaseModel):
    row: int
    column: str
    value: Optional[str] = None
    error: str


class CSVValidationWarning(BaseModel):
    row: int
    column: str
    value: Optional[str] = None
    warning: str


class CSVDryRunResponse(BaseModel):
    import_id: str
    file_type: str
    total_rows: int
    valid_rows: int
    errors: List[CSVValidationError] = Field(default_factory=list)
    warnings: List[CSVValidationWarning] = Field(default_factory=list)
    preview: List[dict] = Field(default_factory=list)


class CSVCommitRequest(BaseModel):
    import_id: str


class CSVCommitResponse(BaseModel):
    file_type: str
    rows_inserted: int
    rows_skipped: int
    errors: List[CSVValidationError] = Field(default_factory=list)
