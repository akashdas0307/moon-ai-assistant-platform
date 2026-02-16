import os
import shutil
from pathlib import Path
from typing import List
from datetime import datetime
from backend.config.settings import settings
from backend.models.file_models import FileNode, FileContent, DeleteResult

class FileService:
    def __init__(self):
        self.workspace_root = settings.WORKSPACE_DIR

    def _safe_join(self, path: str) -> Path:
        """
        Safely join paths and prevent traversal attacks.
        Returns an absolute path.
        """
        # Remove leading slashes to prevent absolute path overriding
        clean_path = path.lstrip("/")

        # Resolve the full path
        full_path = (self.workspace_root / clean_path).resolve()

        # Verify it's still within workspace_root
        if not str(full_path).startswith(str(self.workspace_root.resolve())):
            raise ValueError("Access denied: path traversal detected")

        return full_path

    def _get_relative_path(self, full_path: Path) -> str:
        """Convert absolute path to workspace-relative path"""
        try:
            rel = full_path.relative_to(self.workspace_root)
            return "/" + str(rel) if str(rel) != "." else "/"
        except ValueError:
            # Fallback if path is not relative to workspace (should not happen if logic is correct)
            return str(full_path)

    def list_directory(self, path: str) -> List[FileNode]:
        """List files and folders in a directory"""
        full_path = self._safe_join(path)

        if not full_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not full_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")

        nodes = []
        for item in full_path.iterdir():
            if item.name == ".gitkeep":
                continue

            stat = item.stat()
            modified = datetime.fromtimestamp(stat.st_mtime)

            is_file = item.is_file()
            node_type = "file" if is_file else "folder"
            size = stat.st_size if is_file else None
            extension = item.suffix if is_file else None

            nodes.append(FileNode(
                name=item.name,
                path=self._get_relative_path(item),
                type=node_type,
                size=size,
                modified=modified,
                extension=extension
            ))

        # Sort by type (folder first) then name
        nodes.sort(key=lambda x: (x.type != "folder", x.name.lower()))
        return nodes

    def create_file(self, path: str, content: str = "") -> FileNode:
        """Create a new file with optional content"""
        full_path = self._safe_join(path)

        if full_path.exists():
            raise FileExistsError(f"File already exists: {path}")

        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Check allowed extensions
        if full_path.suffix not in settings.ALLOWED_EXTENSIONS:
             raise ValueError(f"File extension not allowed: {full_path.suffix}")

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        stat = full_path.stat()
        return FileNode(
            name=full_path.name,
            path=self._get_relative_path(full_path),
            type="file",
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime),
            extension=full_path.suffix
        )

    def create_folder(self, path: str) -> FileNode:
        """Create a new folder"""
        full_path = self._safe_join(path)

        if full_path.exists():
            raise FileExistsError(f"Item already exists: {path}")

        full_path.mkdir(parents=True, exist_ok=True)

        stat = full_path.stat()
        return FileNode(
            name=full_path.name,
            path=self._get_relative_path(full_path),
            type="folder",
            size=None,
            modified=datetime.fromtimestamp(stat.st_mtime),
            extension=None
        )

    def read_file(self, path: str) -> FileContent:
        """Read file contents"""
        full_path = self._safe_join(path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not full_path.is_file():
            raise IsADirectoryError(f"Path is a directory: {path}")

        # Check file size
        stat = full_path.stat()
        if stat.st_size > settings.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {stat.st_size} bytes (limit: {settings.MAX_FILE_SIZE})")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            raise ValueError("File is not a valid UTF-8 text file")

        return FileContent(
            path=self._get_relative_path(full_path),
            content=content,
            size=len(content.encode("utf-8"))
        )

    def delete_item(self, path: str) -> DeleteResult:
        """Delete a file or folder"""
        full_path = self._safe_join(path)

        if not full_path.exists():
            raise FileNotFoundError(f"Item not found: {path}")

        # Prevent deleting the workspace root
        if full_path == self.workspace_root:
            raise ValueError("Cannot delete workspace root")

        try:
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)

            return DeleteResult(
                success=True,
                path=path,
                message="Item deleted successfully"
            )
        except Exception as e:
            return DeleteResult(
                success=False,
                path=path,
                message=str(e)
            )

    def get_file_info(self, path: str) -> FileNode:
        """Get info about a file or folder"""
        full_path = self._safe_join(path)

        if not full_path.exists():
            raise FileNotFoundError(f"Item not found: {path}")

        stat = full_path.stat()
        is_file = full_path.is_file()

        return FileNode(
            name=full_path.name,
            path=self._get_relative_path(full_path),
            type="file" if is_file else "folder",
            size=stat.st_size if is_file else None,
            modified=datetime.fromtimestamp(stat.st_mtime),
            extension=full_path.suffix if is_file else None
        )
