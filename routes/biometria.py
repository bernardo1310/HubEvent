# routes/biometria.py
"""
Rotas de biometria facial: cadastro biométrico e validação de entrada no evento.

Fluxo de cadastro biométrico:
    Usuário -> seleciona selfie -> upload S3 -> Rekognition (IndexFaces)
    -> FaceId -> atualiza tabela Usuarios -> atualiza tabela Ingressos
    -> status "Biometria cadastrada"

Fluxo de validação de entrada:
    Usuário -> nova selfie -> upload S3 -> Rekognition (SearchFacesByImage)
    -> similarity >= threshold (padrão 95%) -> "Entrada autorizada"
    caso contrário -> "Entrada negada"
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from utils.forms import BiometriaForm
from services import s3_service, rekognition_service, dynamodb_service as db
from services.aws import AWSServiceError

biometria_bp = Blueprint("biometria", __name__)


@biometria_bp.route("/biometria/cadastro/<id_ingresso>", methods=["GET", "POST"])
@login_required
def cadastro(id_ingresso):
    """Cadastro biométrico vinculado a um ingresso recém-comprado."""
    form = BiometriaForm()

    try:
        ingresso = db.buscar_ingresso_por_id(id_ingresso)
    except AWSServiceError as exc:
        flash(f"Erro ao carregar ingresso: {exc}", "danger")
        return redirect(url_for("ingressos.meus_ingressos"))

    if not ingresso or ingresso.get("idUsuario") != current_user.id_usuario:
        flash("Ingresso não encontrado.", "warning")
        return redirect(url_for("ingressos.meus_ingressos"))

    if form.validate_on_submit():
        try:
            selfie_bytes = form.selfie.data.read()

            # 1) Valida se existe realmente um rosto na imagem antes de prosseguir.
            if not rekognition_service.detectar_rosto(selfie_bytes):
                flash("Não foi possível identificar um rosto na imagem enviada. Tente novamente.", "warning")
                return render_template("biometria.html", form=form, ingresso=ingresso)

            # 2) Upload da selfie para o S3 (pasta usuarios/).
            s3_service.upload_selfie_usuario(current_user.id_usuario, selfie_bytes)

            # 3) Indexa o rosto na collection do Rekognition (IndexFaces).
            face_id = rekognition_service.cadastrar_rosto(selfie_bytes, current_user.id_usuario)

            # 4) Atualiza a tabela Usuarios com o FaceId retornado.
            db.atualizar_biometria_usuario(current_user.id_usuario, face_id)

            # 5) Atualiza o ingresso para o status "Biometria cadastrada".
            db.atualizar_status_ingresso(id_ingresso, db.STATUS_BIOMETRIA_CADASTRADA, face_id=face_id)

            flash("Biometria cadastrada com sucesso!", "success")
            return redirect(url_for("ingressos.meus_ingressos"))
        except AWSServiceError as exc:
            flash(f"Erro no cadastro biométrico: {exc}", "danger")

    return render_template("biometria.html", form=form, ingresso=ingresso)


@biometria_bp.route("/validacao", methods=["GET", "POST"])
@login_required
def validacao():
    """
    Validação facial na entrada do evento.

    Pode ser utilizada tanto pelo próprio participante quanto por um
    operador no local do evento (ex.: um tablet na portaria), desde que
    autenticado no sistema.
    """
    form = BiometriaForm()
    resultado = None

    if form.validate_on_submit():
        try:
            selfie_bytes = form.selfie.data.read()

            # 1) Upload da selfie de validação (pasta validacao/).
            s3_service.upload_selfie_validacao(current_user.id_usuario, selfie_bytes)

            # 2) Busca por rosto correspondente na collection (SearchFacesByImage).
            match = rekognition_service.buscar_rosto_similar(selfie_bytes)

            if match:
                id_usuario_encontrado = match["external_image_id"]

                # Localiza o ingresso do usuário identificado que esteja pronto para validação.
                ingressos = db.listar_ingressos_do_usuario(id_usuario_encontrado)
                ingresso_valido = next(
                    (i for i in ingressos if i.get("status") == db.STATUS_BIOMETRIA_CADASTRADA), None
                )

                if ingresso_valido:
                    db.atualizar_status_ingresso(
                        ingresso_valido["idIngresso"], db.STATUS_ENTRADA_AUTORIZADA
                    )
                    usuario = db.buscar_usuario_por_id(id_usuario_encontrado)
                    resultado = {
                        "autorizado": True,
                        "similarity": match["similarity"],
                        "nome_usuario": usuario.get("nome") if usuario else "Participante",
                    }
                else:
                    resultado = {
                        "autorizado": False,
                        "similarity": match["similarity"],
                        "motivo": "Nenhum ingresso válido encontrado para este rosto.",
                    }
            else:
                resultado = {
                    "autorizado": False,
                    "similarity": 0,
                    "motivo": "Rosto não reconhecido na base biométrica.",
                }

        except AWSServiceError as exc:
            flash(f"Erro na validação facial: {exc}", "danger")

    return render_template("validacao.html", form=form, resultado=resultado)
