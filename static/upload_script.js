document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("file-upload");
    const fileNamesDisplay = document.getElementById("file-names");
    const previewContainer = document.getElementById("image-preview");
    const errorMessage = document.getElementById("error-message");
    const uploadBtn = document.getElementById("upload-btn");

    fileInput.addEventListener("change", function (event) {
        let files = event.target.files;
        let validFiles = [];
        let errorText = "";

        previewContainer.innerHTML = ""; // Clear previous previews

        if (files.length > 6) {
            errorText = "⚠️ You can only upload up to 6 images!";
        } else {
            for (let file of files) {
                if (file.size > 2 * 1024 * 1024) {
                    errorText = "⚠️ Each image must be under 2MB!";
                    break;
                }
                validFiles.push(file);
            }
        }

        if (errorText) {
            fileInput.value = ""; // Reset file input
            fileNamesDisplay.textContent = "No files chosen";
            errorMessage.textContent = errorText;
            errorMessage.style.display = "block";
            uploadBtn.disabled = true;
        } else {
            errorMessage.style.display = "none";
            uploadBtn.disabled = false;

            fileNamesDisplay.textContent = validFiles.length > 0 ? [...validFiles].map(f => f.name).join(", ") : "No files chosen";

            for (let file of validFiles) {
                let reader = new FileReader();
                reader.onload = function (e) {
                    let img = document.createElement("img");
                    img.src = e.target.result;
                    img.classList.add("preview-image"); // Apply styling
                    previewContainer.appendChild(img);
                };
                reader.readAsDataURL(file);
            }
        }
    });
});
