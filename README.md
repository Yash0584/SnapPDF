# SnapPDF

SnapPDF is a production-style, privacy-focused image-to-PDF converter built with a lightweight vanilla JavaScript frontend and a Flask backend.

## Project Overview

SnapPDF lets users:

- Upload multiple images at once
- Drag and drop files into the uploader
- Preview image thumbnails
- Remove images before conversion
- Reorder pages using drag sorting
- Choose compression quality
- Generate a PDF and download it automatically
- Process uploads temporarily with no permanent server storage

## Core Privacy Guarantee

- Uploaded images are only stored temporarily during processing.
- Generated PDFs are created in memory or temporary storage.
- No permanent `uploads` or `outputs` folders are used.
- All temporary user files are removed immediately after the response is sent.

## Features

- Multiple image upload
- Unlimited uploads and preview cards
- Drag & drop upload experience
- Sortable image cards via SortableJS
- Compression options: High, Medium, Small
- Auto-triggered PDF download as `SnapPDF.pdf`
- Responsive dark SaaS-style UI
- Loading spinner and clear status updates
- Error handling for unsupported files and conversion failures
- Browser-friendly frontend flow
- Render-ready backend architecture
- Vercel-ready frontend deployment

## Folder Structure

```
SnapPDF/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── utils/
│       ├── __init__.py
│       └── pdf_generator.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── README.md
└── .gitignore
```

## Setup Guide

### Backend

1. Open a terminal in `backend/`
2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the backend:

```bash
python app.py
```

The backend will run at `http://127.0.0.1:5000`.

### Frontend

1. Open `frontend/index.html` in a web browser, or host the `frontend/` folder with a static server.
2. Ensure the backend is running on `http://127.0.0.1:5000`.

> For production, update `API_URL` in `frontend/script.js` to match your deployed backend URL.

## API Explanation

### `POST /convert`

This endpoint accepts image uploads and returns a PDF download directly.

#### Request

- `Content-Type`: `multipart/form-data`
- Fields:
  - `images`: one or more image files
  - `compression`: `high`, `medium`, or `low`

#### Response

- Success: `200 OK` with the PDF file download
- Error: JSON object with `error` message

## Deployment Instructions

### Backend on Render

1. Create a new Render Web Service.
2. Set the root directory to `backend/`.
3. Use this start command:

```bash
gunicorn app:app
```

4. Choose Python 3.11 or later.

### Frontend on Vercel

1. Deploy the `frontend/` folder as a static site.
2. Configure the frontend to point to the deployed backend URL in `frontend/script.js`.

## Validation Notes

- The backend uses `tempfile.TemporaryDirectory()` to process uploads safely.
- Image files are validated for JPG, PNG, and WEBP only.
- PDF files are generated in memory and returned immediately.
- No permanent file storage is created by the backend.

## Running Locally

1. Start the backend server.
2. Open `frontend/index.html` or serve the frontend from a static host.
3. Add images, rearrange them, choose compression, and click "Convert to PDF."

Enjoy the privacy-first SnapPDF experience.
"}