from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class FileNode(BaseModel):
    name: str
    path: str  # Relative to workspace root
    type: Literal["file", "folder"]
    size: Optional[int] = None  # Bytes (null for folders)
    modified: datetime
    extension: Optional[str] = None  # For files (e.g., ".py", ".md")

class FileContent(BaseModel):
    path: str
    content: str
    encoding: str = "utf-8"
    size: int

class DeleteResult(BaseModel):
    success: bool
    path: str
    message: str
