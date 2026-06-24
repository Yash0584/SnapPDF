import gc
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional

import img2pdf
from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)

QUALITY_MAP = {
    "high": {"quality": 95, "resize_if_width_above": 4000},
    "medium": {"quality": 80, "resize_if_width_above": 3000},
    "small": {"quality": 60, "resize_if_width_above": 1600},
}

CHUNK_SIZE = 25


def _get_quality_settings(compression: str) -> dict:
    normalized = (compression or "medium").lower().strip()
    if normalized in {"low", "small"}:
        return QUALITY_MAP["small"]
    return QUALITY_MAP.get(normalized, QUALITY_MAP["medium"])


def _prepare_image_for_pdf(image_path: str, output_path: Path, compression: str) -> None:
    settings = _get_quality_settings(compression)
    resample_filter = getattr(Image, "Resampling", Image).LANCZOS

    try:
        with Image.open(image_path) as source_image:
            image = ImageOps.exif_transpose(source_image)
            image = image.convert("RGB")

            if image.width > settings["resize_if_width_above"]:
                image.thumbnail(
                    (settings["resize_if_width_above"], settings["resize_if_width_above"] * 10),
                    resample_filter,
                )

            image.save(
                output_path,
                format="JPEG",
                quality=settings["quality"],
                optimize=True,
                progressive=True,
            )
            image.close()
            del image
    except (FileNotFoundError, UnidentifiedImageError, OSError, ValueError) as exc:
        logger.exception("Failed to prepare image %s", image_path)
        raise ValueError(f"Failed to process image '{Path(image_path).name}': {exc}") from exc


def create_pdf(
    image_paths: Iterable[str],
    output_file,
    compression: str = "medium",
    temp_dir: Optional[Path] = None,
) -> None:
    """Create a multi-page PDF from temporary image files using chunked processing and low-memory temp files."""
    image_paths = [str(path) for path in image_paths]

    if not image_paths:
        raise ValueError("No valid images were provided for PDF generation.")

    temp_root = Path(temp_dir) if temp_dir else Path(tempfile.mkdtemp(prefix="snappdf_processed_"))
    processed_dir = temp_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    prepared_image_paths: List[str] = []
    total_images = len(image_paths)
    total_chunks = max(1, (total_images + CHUNK_SIZE - 1) // CHUNK_SIZE)

    try:
        for chunk_index in range(1, total_chunks + 1):
            start = (chunk_index - 1) * CHUNK_SIZE
            end = min(start + CHUNK_SIZE, total_images)
            chunk_paths = image_paths[start:end]
            logger.info("Starting chunk %d/%d with %d images", chunk_index, total_chunks, len(chunk_paths))

            for offset, image_path in enumerate(chunk_paths, start=1):
                index = start + offset
                output_path = processed_dir / f"page_{index:03d}.jpg"
                logger.info("Processing image %d/%d in chunk %d/%d", index, total_images, chunk_index, total_chunks)
                _prepare_image_for_pdf(image_path, output_path, compression)
                prepared_image_paths.append(str(output_path))

            logger.info("Memory released after chunk %d/%d", chunk_index, total_chunks)
            gc.collect()

        if not prepared_image_paths:
            raise ValueError("No valid images were provided for PDF generation.")

        logger.info("Final PDF generation started")
        pdf_bytes = img2pdf.convert(prepared_image_paths)
        output_file.write(pdf_bytes)
        output_file.seek(0)
        logger.info("Final PDF generation completed")
    except Exception:
        logger.exception("PDF generation pipeline failed")
        raise
    finally:
        if temp_dir is None:
            shutil.rmtree(temp_root, ignore_errors=True)
