"""Image validation and normalisation. Handles corrupt, truncated and tiny images."""
from __future__ import annotations

import base64
import io
from dataclasses import dataclass

from fastapi import UploadFile
from PIL import Image, ImageFile, UnidentifiedImageError

from .config import get_settings
from .errors import AppError

ImageFile.LOAD_TRUNCATED_IMAGES = False  # truncated files must fail loudly
ALLOWED = {"image/jpeg", "image/png", "image/webp"}
MAX_SIDE = 1568
MIN_SIDE = 160


@dataclass
class PreparedImage:
    filename: str
    media_type: str
    data: bytes
    width: int
    height: int

    @property
    def b64(self) -> str:
        return base64.b64encode(self.data).decode()


async def prepare_images(files: list[UploadFile] | None) -> tuple[list[PreparedImage], list[str]]:
    settings = get_settings()
    files = [f for f in (files or []) if f and f.filename]
    if len(files) > settings.max_images_per_request:
        raise AppError("too_many_images", f"Upload at most {settings.max_images_per_request} images per request.", 422)

    prepared: list[PreparedImage] = []
    warnings: list[str] = []
    limit = settings.max_image_mb * 1024 * 1024

    for f in files:
        if f.content_type not in ALLOWED:
            raise AppError("unsupported_image", f"{f.filename}: use a JPEG, PNG or WebP image.", 415)
        raw = await f.read()
        if not raw:
            raise AppError("empty_image", f"{f.filename} is empty.", 422)
        if len(raw) > limit:
            raise AppError("image_too_large", f"{f.filename} exceeds {settings.max_image_mb} MB.", 413)
        try:
            img = Image.open(io.BytesIO(raw))
            img.load()  # forces a full decode so incomplete files are caught here
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
            raise AppError(
                "corrupt_image",
                f"{f.filename} is corrupt or incomplete and could not be read. Re-export or re-upload the image.",
                422,
            ) from exc

        if min(img.size) < MIN_SIDE:
            warnings.append(f"{f.filename} is very small ({img.size[0]}x{img.size[1]}). Results may be unreliable.")

        img = img.convert("RGB")
        if max(img.size) > MAX_SIDE:
            img.thumbnail((MAX_SIDE, MAX_SIDE))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88)
        prepared.append(PreparedImage(f.filename, "image/jpeg", buf.getvalue(), img.size[0], img.size[1]))

    return prepared, warnings
