// static/js/main.js
// Funções JavaScript gerais do HubEvent (pré-visualização de imagens via Fetch API/File API)

document.addEventListener("DOMContentLoaded", function () {
    // Pré-visualização de selfie antes do upload (cadastro biométrico / validação)
    const inputSelfie = document.querySelector("input[type='file'][name='selfie']");
    const preview = document.getElementById("selfie-preview");

    if (inputSelfie && preview) {
        inputSelfie.addEventListener("change", function () {
            const arquivo = inputSelfie.files[0];
            if (arquivo) {
                preview.src = URL.createObjectURL(arquivo);
                preview.classList.remove("d-none");
            }
        });
    }

    // Pré-visualização de imagem de evento no formulário administrativo
    const inputImagemEvento = document.querySelector("input[type='file'][name='imagem']");
    const previewEvento = document.getElementById("imagem-preview");

    if (inputImagemEvento && previewEvento) {
        inputImagemEvento.addEventListener("change", function () {
            const arquivo = inputImagemEvento.files[0];
            if (arquivo) {
                previewEvento.src = URL.createObjectURL(arquivo);
                previewEvento.classList.remove("d-none");
            }
        });
    }
});
