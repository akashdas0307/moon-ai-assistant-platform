from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from typing import List, Literal, Optional, Union
from pydantic import BaseModel
from backend.services.file_service import FileService
from backend.models.file_models import FileNode, FileContent, DeleteResult

router = APIRouter()

class CreateItemRequest(BaseModel):
    path: str
    type: Literal["file", "folder"]
    content: Optional[str] = ""

def get_file_service():
    return FileService()

@router.get("", response_model=List[FileNode])
async def list_files(
    path: str = Query("/", description="Path to list files from"),
    service: FileService = Depends(get_file_service)
):
    """List files and folders in a directory"""
    try:
        return service.list_directory(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=FileNode)
async def create_item(
    request: CreateItemRequest,
    service: FileService = Depends(get_file_service)
):
    """Create a new file or folder"""
    try:
        if request.type == "file":
            return service.create_file(request.path, request.content or "")
        else:
            return service.create_folder(request.path)
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content")
async def get_file_content(
    path: str = Query(..., description="Path to the file"),
    service: FileService = Depends(get_file_service)
):
    """Read file contents"""
    try:
        # Check if it is an image
        full_path = service.get_absolute_path(path)
        if full_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']:
            return FileResponse(full_path)

        return service.read_file(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IsADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        # Could be size limit or encoding error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("", response_model=DeleteResult)
async def delete_item(
    path: str = Query(..., description="Path to delete"),
    service: FileService = Depends(get_file_service)
):
    """Delete a file or folder"""
    try:
        result = service.delete_item(path)
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
