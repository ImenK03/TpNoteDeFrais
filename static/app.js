const fileInput = document.querySelector("#file-input");
const previewWrapper = document.querySelector("#preview-wrapper");
const previewImage = document.querySelector("#preview-image");
const resultContainer = document.querySelector("#result-container");

function resetPage() {
    if (fileInput) {
        fileInput.value = "";
    }

    if (previewImage) {
        previewImage.removeAttribute("src");
    }

    if (previewWrapper) {
        previewWrapper.classList.add("hidden");
    }

    if (resultContainer) {
        resultContainer.innerHTML = "";
    }
}

if (fileInput) {
    fileInput.addEventListener("change", () => {
        const file = fileInput.files?.[0];

        if (!file) {
            resetPage();
            return;
        }

        if (!file.type.startsWith("image/")) {
            resultContainer.innerHTML = `
                <div class="alert alert-error">
                    <strong>Erreur</strong><br>
                    Le fichier choisi n'est pas une image.
                </div>
            `;

            return;
        }

        const reader = new FileReader();

        reader.onload = (event) => {
            previewImage.src = event.target.result;
            previewWrapper.classList.remove("hidden");
        };

        reader.readAsDataURL(file);
    });
}

document.body.addEventListener("htmx:responseError", (event) => {
    const xhr = event.detail.xhr;
    const target = event.detail.target || resultContainer;

    if (target) {
        target.innerHTML = xhr.responseText || `
            <div class="alert alert-error">
                <strong>Erreur</strong><br>
                Une erreur est survenue pendant la requête.
            </div>
        `;
    }
});

document.body.addEventListener("htmx:afterSwap", () => {
    const inlineResetButton = document.querySelector("#reset-button-inline");

    if (inlineResetButton) {
        inlineResetButton.addEventListener("click", resetPage);
    }
});
