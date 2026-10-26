import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app.config import get_settings
    get_settings.cache_clear()
    from app.main import app
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def make_image(fmt="PNG", size=(640, 480)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (120, 130, 140)).save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture()
def png():
    return make_image()
