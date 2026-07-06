# routes/ingressos.py
"""
Rotas relacionadas à compra e listagem de ingressos.

Fluxo de compra (conforme especificação do projeto):
    1. Usuário confirma a compra de um ingresso para um evento.
    2. Um registro de ingresso é criado no DynamoDB com status
       "Aguardando biometria".
    3. Uma função Lambda é invocada de forma assíncrona para processamento
       adicional (ex.: geração de log de confirmação da compra).
    4. O usuário é redirecionado automaticamente para o cadastro biométrico.
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from services import dynamodb_service as db
from services import lambda_service
from services.aws import AWSServiceError

ingressos_bp = Blueprint("ingressos", __name__)


@ingressos_bp.route("/eventos/<id_evento>/comprar", methods=["GET", "POST"])
@login_required
def comprar(id_evento):
    """Confirmação de compra de ingresso para um evento."""
    try:
        evento = db.buscar_evento_por_id(id_evento)
        if not evento:
            flash("Evento não encontrado.", "warning")
            return redirect(url_for("eventos.index"))

        # Página de confirmação (GET) exibida antes de efetivar a compra.
        return render_template("compra.html", evento=evento)
    except AWSServiceError as exc:
        flash(f"Erro ao carregar evento: {exc}", "danger")
        return redirect(url_for("eventos.index"))


@ingressos_bp.route("/eventos/<id_evento>/confirmar-compra", methods=["POST"])
@login_required
def confirmar_compra(id_evento):
    """Efetiva a compra: cria o ingresso no DynamoDB e aciona o Lambda."""
    try:
        evento = db.buscar_evento_por_id(id_evento)
        if not evento:
            flash("Evento não encontrado.", "warning")
            return redirect(url_for("eventos.index"))

        ingresso = db.criar_ingresso(current_user.id_usuario, id_evento)

        # Processamento assíncrono não bloqueante (confirmação/logs via Lambda + CloudWatch).
        lambda_service.invocar_confirmacao_compra(
            id_ingresso=ingresso["idIngresso"],
            id_usuario=current_user.id_usuario,
            id_evento=id_evento,
        )

        flash(
            "Ingresso reservado com sucesso! Agora finalize seu cadastro biométrico.",
            "success",
        )
        # Redirecionamento automático para o cadastro biométrico, conforme especificado.
        return redirect(url_for("biometria.cadastro", id_ingresso=ingresso["idIngresso"]))
    except AWSServiceError as exc:
        flash(f"Erro ao processar compra: {exc}", "danger")
        return redirect(url_for("eventos.detalhe", id_evento=id_evento))


@ingressos_bp.route("/meus-ingressos")
@login_required
def meus_ingressos():
    """Lista os ingressos do usuário autenticado, com status atual."""
    try:
        ingressos = db.listar_ingressos_do_usuario(current_user.id_usuario)

        # Anexa dados do evento a cada ingresso para exibição.
        for ingresso in ingressos:
            evento = db.buscar_evento_por_id(ingresso["idEvento"])
            ingresso["evento"] = evento

        ingressos.sort(key=lambda i: i.get("comprEm", ""), reverse=True)
    except AWSServiceError as exc:
        ingressos = []
        flash(f"Erro ao carregar ingressos: {exc}", "danger")

    return render_template("dashboard.html", ingressos=ingressos)
