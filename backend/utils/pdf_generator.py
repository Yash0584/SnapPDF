from PIL import Image

QUALITY_MAP = {
    "high": 95,
    "medium": 75,
    "low": 45,
}

MAX_WIDTH = 1600


def create_pdf(image_paths, output_file, compression="medium"):
    """Create a multi-page PDF from temporary image files and write the result into a file-like object."""
    quality = QUALITY_MAP.get(compression, 75)
    images = []

    for image_path in image_paths:
        with Image.open(image_path) as source_image:
            image = source_image.convert("RGB")
            if image.width > MAX_WIDTH:
                image.thumbnail((MAX_WIDTH, MAX_WIDTH * 10), Image.LANCZOS)
            images.append(image.copy())
            image.close()

    if not images:
        raise ValueError("No valid images were provided for PDF generation.")

    first_image, rest_images = images[0], images[1:]
    first_image.save(
        output_file,
        format="PDF",
        save_all=True,
        append_images=rest_images,
        quality=quality,
        optimize=True,
    )

    try:
        output_file.seek(0)
    except Exception:
        pass
