const API_URL = "https://snappdf-backend.onrender.com/";
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const dropArea = document.getElementById("dropArea");
const fileInput = document.getElementById("fileInput");
const browseBtn = document.getElementById("browseBtn");
const previewContainer = document.getElementById("previewContainer");
const convertBtn = document.getElementById("convertBtn");
const compressionSelect = document.getElementById("compression");
const statusText = document.getElementById("statusText");
const loadingIndicator = document.getElementById("loadingIndicator");
const fileCount = document.getElementById("fileCount");
const downloadPanel = document.getElementById("downloadPanel");
const toast = document.getElementById("toast");

let imageList = [];
let sortable = null;

function showToast(message) {
    toast.textContent = message;
    toast.classList.remove("hidden");
    toast.classList.add("visible");

    window.clearTimeout(showToast.timeoutId);
    showToast.timeoutId = window.setTimeout(() => {
        toast.classList.remove("visible");
        toast.classList.add("hidden");
    }, 3200);
}

function setLoading(loading) {
    loadingIndicator.classList.toggle("hidden", !loading);
    convertBtn.disabled = loading || imageList.length === 0;
    convertBtn.textContent = loading ? "Generating PDF..." : "Convert to PDF";
}

function showStatus(message) {
    statusText.textContent = message;
}

function updateStatus() {
    const count = imageList.length;
    fileCount.textContent = `${count} image${count === 1 ? "" : "s"}`;
    showStatus(
        count
            ? "Drag images to reorder them or click Convert to export your PDF."
            : "No images added yet. Start by dropping images or selecting files."
    );
    convertBtn.disabled = count === 0;
    hideDownloadPanel();
}

function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 ** 2).toFixed(2)} MB`;
}

function buildFileKey(file) {
    return `${file.name}-${file.size}-${file.lastModified}`;
}

function isDuplicate(file) {
    const key = buildFileKey(file);
    return imageList.some((item) => item.key === key);
}

function addFiles(files) {
    const accepted = [];

    Array.from(files).forEach((file) => {
        if (!ALLOWED_TYPES.includes(file.type)) {
            showToast("Only JPG, PNG, and WEBP images are supported.");
            return;
        }

        if (isDuplicate(file)) {
            showToast(`${file.name} has already been added.`);
            return;
        }

        imageList.push({ file, key: buildFileKey(file) });
        accepted.push(file.name);
    });

    if (accepted.length) {
        renderPreview();
        showToast(`${accepted.length} image${accepted.length > 1 ? "s" : ""} added.`);
    }
}

function renderPreview() {
    previewContainer.innerHTML = "";

    if (!imageList.length) {
        previewContainer.innerHTML = `
            <div class="empty-state">
                <strong>No preview cards yet</strong>
                Add images to see thumbnails and reorder pages before export.
            </div>
        `;
        updateStatus();
        return;
    }

    imageList.forEach((item, index) => {
        const reader = new FileReader();
        const card = document.createElement("article");
        card.className = "preview-card";
        card.dataset.index = index;

        const imageElement = document.createElement("img");
        card.appendChild(imageElement);

        const body = document.createElement("div");
        body.className = "card-body";
        body.innerHTML = `
            <h3>${item.file.name}</h3>
            <p class="meta">${formatBytes(item.file.size)}</p>
            <div class="card-actions">
                <button type="button" class="small-btn remove-btn">Remove</button>
            </div>
        `;

        reader.onload = (event) => {
            imageElement.src = event.target.result;
        };
        reader.readAsDataURL(item.file);

        body.querySelector(".remove-btn").addEventListener("click", () => {
            imageList.splice(index, 1);
            renderPreview();
        });

        card.appendChild(body);
        previewContainer.appendChild(card);
    });

    enableSorting();
    updateStatus();
}

function enableSorting() {
    if (sortable) {
        sortable.destroy();
    }

    sortable = new Sortable(previewContainer, {
        animation: 180,
        ghostClass: "sortable-ghost",
        dragClass: "sortable-drag",
        filter: ".remove-btn",
        preventOnFilter: false,
        onEnd(event) {
            const [moved] = imageList.splice(event.oldIndex, 1);
            imageList.splice(event.newIndex, 0, moved);
            renderPreview();
        },
    });
}

function showDownloadPanel(downloadUrl) {
    downloadPanel.innerHTML = `
        <p><strong>Your PDF is ready.</strong> The download should begin automatically. If it does not, click the button below.</p>
        <div class="download-actions">
            <a href="${downloadUrl}" download="SnapPDF.pdf" class="button primary">Download PDF</a>
        </div>
    `;
    downloadPanel.classList.remove("hidden");
}

function hideDownloadPanel() {
    downloadPanel.classList.add("hidden");
    downloadPanel.innerHTML = "";
}

function resetAppState() {
    imageList = [];
    fileInput.value = "";
    renderPreview();
}

async function handleConversion() {
    if (!imageList.length) {
        showToast("Please add at least one image before converting.");
        return;
    }

    setLoading(true);
    showStatus("Generating your PDF. Please wait...");
    hideDownloadPanel();

    const formData = new FormData();
    imageList.forEach((item) => formData.append("images", item.file));
    formData.append("compression", compressionSelect.value);

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const errorPayload = await response.json().catch(() => null);
            throw new Error(errorPayload?.error || "Server failed to generate the PDF.");
        }

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = downloadUrl;
        link.download = "SnapPDF.pdf";
        document.body.appendChild(link);

        showStatus("PDF generated successfully. Download should begin now.");
        showToast("PDF generation complete. Your browser is downloading the file.");

        link.click();
        link.remove();
        resetAppState();
        showDownloadPanel(downloadUrl);

        window.setTimeout(() => {
            URL.revokeObjectURL(downloadUrl);
        }, 60000);
    } catch (error) {
        showToast(error.message || "Unable to convert images at this time.");
        showStatus("Something went wrong. Please try again with valid image files.");
        console.error(error);
    } finally {
        setLoading(false);
    }
}

function setDragState(active) {
    dropArea.classList.toggle("active", active);
}

fileInput.addEventListener("change", (event) => {
    if (event.target.files.length) {
        addFiles(event.target.files);
    }
    fileInput.value = "";
});

browseBtn.addEventListener("click", () => fileInput.click());

dropArea.addEventListener("dragover", (event) => {
    event.preventDefault();
    setDragState(true);
});

dropArea.addEventListener("dragleave", () => {
    setDragState(false);
});

dropArea.addEventListener("drop", (event) => {
    event.preventDefault();
    setDragState(false);
    if (event.dataTransfer.files.length) {
        addFiles(event.dataTransfer.files);
    }
});

convertBtn.addEventListener("click", handleConversion);

renderPreview();
