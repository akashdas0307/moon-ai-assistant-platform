import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config.settings import settings

client = TestClient(app)

@pytest.fixture
def test_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "WORKSPACE_DIR", tmp_path)
    return tmp_path

def test_list_files(test_workspace):
    (test_workspace / "test.txt").touch()
    response = client.get("/api/v1/files")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test.txt"

def test_create_file(test_workspace):
    response = client.post("/api/v1/files", json={
        "path": "/new.txt",
        "type": "file",
        "content": "hello"
    })
    assert response.status_code == 200
    assert (test_workspace / "new.txt").exists()
    assert (test_workspace / "new.txt").read_text(encoding="utf-8") == "hello"

def test_create_folder(test_workspace):
    response = client.post("/api/v1/files", json={
        "path": "/new_folder",
        "type": "folder"
    })
    assert response.status_code == 200
    assert (test_workspace / "new_folder").is_dir()

def test_get_content(test_workspace):
    (test_workspace / "read.txt").write_text("content", encoding="utf-8")
    response = client.get("/api/v1/files/content?path=/read.txt")
    assert response.status_code == 200
    assert response.json()["content"] == "content"

def test_delete_file(test_workspace):
    (test_workspace / "del.txt").touch()
    response = client.delete("/api/v1/files?path=/del.txt")
    assert response.status_code == 200
    assert not (test_workspace / "del.txt").exists()

def test_path_traversal_list(test_workspace):
    response = client.get("/api/v1/files?path=../")
    assert response.status_code == 403

def test_create_invalid_extension(test_workspace):
    response = client.post("/api/v1/files", json={
        "path": "/bad.exe",
        "type": "file"
    })
    assert response.status_code == 400
    assert "extension not allowed" in response.json()["detail"]

def test_get_nonexistent_file(test_workspace):
    response = client.get("/api/v1/files/content?path=/ghost.txt")
    assert response.status_code == 404
