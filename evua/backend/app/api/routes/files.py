"""
File upload routes
POST   /api/upload              — upload PHP files or a ZIP archive
GET    /api/uploads/{upload_id} — list files in an upload batch
DELETE /api/uploads/{upload_id} — remove an upload batch
"""
import os
import shutil
import uuid
import zipfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from ...core.dependencies import SettingsDep
from ...schemas.migration import UploadResponse

router = APIRouter(prefix="/api", tags=["files"])

# In-memory map: upload_id → list[saved file paths]
_uploads: dict[str, list[str]] = {}

_PHP_EXTS = {".php", ".phtml"}


def _extract_zip(zip_path: str, dest_dir: str) -> list[str]:
    """Extract all .php/.phtml files from a zip archive into dest_dir."""
    saved: list[str] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            _, ext = os.path.splitext(member.filename.lower())
            if ext not in _PHP_EXTS:
                continue
            # Flatten any directory prefix inside the zip to avoid path traversal
            safe_name = member.filename.replace("..", "").lstrip("/\\")
            out_path = os.path.join(dest_dir, safe_name)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with zf.open(member) as src, open(out_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            saved.append(out_path)
    return saved


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_files(
    files: list[UploadFile] = File(...),
    settings: SettingsDep = None,
):
    """
    Accept one or more PHP files (or a ZIP archive) and save them to a
    temporary directory.  ZIP files are extracted and only .php/.phtml
    entries are kept.
    Returns an ``upload_id`` and the list of saved paths.
    """
    upload_id = str(uuid.uuid4())
    upload_dir = os.path.join(settings.upload_dir, upload_id)
    os.makedirs(upload_dir, exist_ok=True)

    saved: list[str] = []
    for upload in files:
        if not upload.filename:
            continue
        dest = os.path.join(upload_dir, upload.filename)
        size = 0
        with open(dest, "wb") as fh:
            while chunk := await upload.read(65_536):
                size += len(chunk)
                if size > settings.max_upload_size_bytes:
                    fh.close()
                    os.remove(dest)
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"File '{upload.filename}' exceeds the "
                            f"{settings.max_upload_size_mb} MB upload limit"
                        ),
                    )
                fh.write(chunk)

        if upload.filename.lower().endswith(".zip"):
            # Extract PHP files from the archive then discard the zip itself
            extracted = _extract_zip(dest, upload_dir)
            os.remove(dest)
            saved.extend(extracted)
        else:
            saved.append(dest)

    _uploads[upload_id] = saved

    return UploadResponse(
        upload_id=upload_id,
        files=saved,
        message=f"Uploaded {len(saved)} file(s)",
    )


@router.get("/uploads/{upload_id}")
async def get_upload(upload_id: str):
    """Return the file paths for a given upload batch."""
    if upload_id not in _uploads:
        raise HTTPException(status_code=404, detail="Upload not found")
    return {"upload_id": upload_id, "files": _uploads[upload_id]}


@router.delete("/uploads/{upload_id}", status_code=204)
async def delete_upload(upload_id: str, settings: SettingsDep = None):
    """Delete all files associated with an upload batch."""
    if upload_id not in _uploads:
        raise HTTPException(status_code=404, detail="Upload not found")
    upload_dir = os.path.join(settings.upload_dir, upload_id)
    shutil.rmtree(upload_dir, ignore_errors=True)
    _uploads.pop(upload_id, None)
