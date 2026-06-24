import logging
import shutil
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional

import img2pdf
from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)

QUALITY_MAP = {
    "high": {"quality": 95, "max_width": None, "resize_if_width_above": None},
    "medium": {"quality": 80, "max_width": None, "resize_if_width_above": 3000},
    "small": {"quality": 60, "max_width": 1600, "resize_if_width_above": None},
}

MAX_IMAGES_PER_CONVERSION = 50
BATCH_SIZE = 20


def _get_quality_settings(compression: str) -> dict:
    normalized = (compression or "medium").lower().strip()
    if normalized == "low":
        return QUALITY_MAP["small"]
    return QUALITY_MAP.get(normalized, QUALITY_MAP["medium"])


def _prepare_image_for_pdf(image_path: str, output_path: Path, compression: str) -> None:
    settings = _get_quality_settings(compression)
    resample_filter = getattr(Image, "Resampling", Image).LANCZOS

    try:
        with Image.open(image_path) as source_image:
            image = ImageOps.exif_transpose(source_image)
            image = image.convert("RGB")

            if settings["resize_if_width_above"] is not None and image.width > settings["resize_if_width_above"]:
                image.thumbnail(
                    (settings["resize_if_width_above"], settings["resize_if_width_above"] * 10),
                    resample_filter,
                )
            elif settings["max_width"] is not None and image.width > settings["max_width"]:
                image.thumbnail((settings["max_width"], settings["max_width"] * 10), resample_filter)

            image.save(
                output_path,
                format="JPEG",
                quality=settings["quality"],
                optimize=True,
                progressive=True,
            )
            image.close()
    except (FileNotFoundError, UnidentifiedImageError, OSError, ValueError) as exc:
        logger.exception("Failed to prepare image %s", image_path)
        raise ValueError(f"Failed to process image '{Path(image_path).name}': {exc}") from exc


def create_pdf(
    image_paths: Iterable[str],
    output_file,
    compression: str = "medium",
    temp_dir: Optional[Path] = None,
) -> None:
    """Create a multi-page PDF from temporary image files without retaining all images in memory."""
    image_paths = [str(path) for path in image_paths]

    if not image_paths:
        raise ValueError("No valid images were provided for PDF generation.")

    if len(image_paths) > MAX_IMAGES_PER_CONVERSION:
        raise ValueError("Maximum 50 images allowed per conversion.")

    temp_root = Path(temp_dir) if temp_dir else Path(tempfile.mkdtemp(prefix="snappdf_processed_"))
    processed_dir = temp_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    prepared_image_paths: List[str] = []

    try:
        for batch_start in range(0, len(image_paths), BATCH_SIZE):
            batch_paths = image_paths[batch_start : batch_start + BATCH_SIZE]
            logger.info("Processing PDF batch %d with %d images", batch_start // BATCH_SIZE + 1, len(batch_paths))

            for offset, image_path in enumerate(batch_paths, start=1):
                index = batch_start + offset
                output_path = processed_dir / f"page_{index:03d}.jpg"
                logger.info("Preparing image %d/%d for PDF generation", index, len(image_paths))
                _prepare_image_for_pdf(image_path, output_path, compression)
                prepared_image_paths.append(str(output_path))

        if not prepared_image_paths:
            raise ValueError("No valid images were provided for PDF generation.")

        logger.info("Generating PDF from %d prepared images", len(prepared_image_paths))
        pdf_bytes = img2pdf.convert(prepared_image_paths)
        output_file.write(pdf_bytes)
        output_file.seek(0)
    except Exception:
        logger.exception("PDF generation pipeline failed")
        raise
    finally:
        if temp_dir is None:
            shutil.rmtree(temp_root, ignore_errors=True)
