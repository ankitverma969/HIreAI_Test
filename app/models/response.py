from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")

class BaseAPIResponse(BaseModel):
    """Common fields for all API Responses."""
    success: bool = Field(description="Indicates if the operation completed without exceptions")
    message: Optional[str] = Field(default=None, description="Optional informational message")


class SuccessResponse(BaseAPIResponse, Generic[T]):
    """Standard success API Response containing typing data payload."""
    success: bool = True
    data: T = Field(description="Response data content payload")


class ErrorResponse(BaseAPIResponse):
    """Standard API response structure returned when errors occur."""
    success: bool = False
    error_code: str = Field(description="Standardized error category string")
    detail: Optional[Any] = Field(default=None, description="Detailed contextual error explanation")
