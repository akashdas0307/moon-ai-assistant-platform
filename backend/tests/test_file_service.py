import pytest
from backend.services.file_service import FileService
from backend.config.settings import settings

@pytest.fixture
def test_workspace(tmp_path, monkeypatch):
    """Create a temporary workspace directory and patch settings."""
    monkeypatch.setattr(settings, "WORKSPACE_DIR", tmp_path)
    return tmp_path

def test_list_directory(test_workspace):
    # Setup files
    (test_workspace / "file1.txt").touch()
    (test_workspace / "folder1").mkdir()

    service = FileService()
    nodes = service.list_directory("/")

    assert len(nodes) == 2
    assert any(n.name == "file1.txt" and n.type == "file" for n in nodes)
    assert any(n.name == "folder1" and n.type == "folder" for n in nodes)

def test_create_file(test_workspace):
    service = FileService()
    node = service.create_file("/newfile.txt", "content")

    assert node.name == "newfile.txt"
    assert (test_workspace / "newfile.txt").exists()
    assert (test_workspace / "newfile.txt").read_text(encoding="utf-8") == "content"

def test_create_folder(test_workspace):
    service = FileService()
    node = service.create_folder("/newfolder")

    assert node.name == "newfolder"
    assert (test_workspace / "newfolder").is_dir()

def test_read_file(test_workspace):
    (test_workspace / "test.txt").write_text("hello world", encoding="utf-8")

    service = FileService()
    content = service.read_file("/test.txt")

    assert content.content == "hello world"
    assert content.path == "/test.txt"

def test_delete_file(test_workspace):
    (test_workspace / "del.txt").touch()

    service = FileService()
    result = service.delete_item("/del.txt")

    assert result.success
    assert not (test_workspace / "del.txt").exists()

def test_delete_folder(test_workspace):
    (test_workspace / "del_folder").mkdir()

    service = FileService()
    result = service.delete_item("/del_folder")

    assert result.success
    assert not (test_workspace / "del_folder").exists()

def test_path_traversal(test_workspace):
    service = FileService()

    with pytest.raises(ValueError, match="Access denied"):
        service.list_directory("../")

    with pytest.raises(ValueError, match="Access denied"):
        service.read_file("/../../etc/passwd")

def test_invalid_extension(test_workspace):
    service = FileService()

    with pytest.raises(ValueError, match="File extension not allowed"):
        service.create_file("/test.exe", "")

def test_create_nested_file(test_workspace):
    service = FileService()
    node = service.create_file("/nested/dir/test.txt", "content")

    assert node.name == "test.txt"
    assert (test_workspace / "nested/dir/test.txt").exists()

def test_delete_root(test_workspace):
    service = FileService()
    # Attempt to delete root
    # It should fail and return success=False or raise ValueError?
    # In my code: if full_path == workspace_root: raise ValueError("Cannot delete workspace root")
    # But delete_item catches Exception!
    # Wait, my code:
    # try: ... except Exception as e: return DeleteResult(success=False...)
    # But the check is BEFORE try/except?
    # No, I put it inside delete_item but before try block.
    # So it raises ValueError.
    # Who catches it? The API router.
    # The test calls service.delete_item directly. So it should raise ValueError.

    with pytest.raises(ValueError, match="Cannot delete workspace root"):
        service.delete_item("/")
