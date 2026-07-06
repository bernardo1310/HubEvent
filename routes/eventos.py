# routes/eventos.py
"""
Rotas públicas relacionadas a eventos: página inicial, listagem e detalhes.
"""

from flask import Blueprint, render_template, request
from services import dynamodb_service as db
from services import s3_service
from services.aws import AWSServiceError

eventos_bp = Blueprint("eventos", __name__)


def _anexar_url_imagem(evento: dict) -> dict:
    """Gera a URL temporária (presigned) da imagem do evento armazenada no S3."""
    if evento.get("imagemKey"):
        try:
            evento["imagemUrl"] = s3_service.gerar_url_temporaria(evento["imagemKey"])
        except AWSServiceError:
            evento["imagemUrl"] = None
    else:
        evento["imagemUrl"] = None
    return evento


@eventos_bp.route("/")
def index():
    """Página inicial: banner, pesquisa e cards de eventos disponíveis."""
    termo_busca = request.args.get("busca", "").strip().lower()

    try:
        eventos = db.listar_eventos()
    except AWSServiceError as exc:
        eventos = []
        return render_template("index.html", eventos=eventos, erro=str(exc), busca=termo_busca)

    if termo_busca:
        eventos = [e for e in eventos if termo_busca in e.get("nome", "").lower()]

    eventos = [_anexar_url_imagem(e) for e in eventos]
    eventos.sort(key=lambda e: e.get("data", ""))

    return render_template("index.html", eventos=eventos, busca=termo_busca)


@eventos_bp.route("/eventos")
def listar():
    """Listagem completa de eventos disponíveis (página dedicada)."""
    try:
        eventos = db.listar_eventos()
        eventos = [_anexar_url_imagem(e) for e in eventos]
        eventos.sort(key=lambda e: e.get("data", ""))
    except AWSServiceError as exc:
        eventos = []
        return render_template("eventos.html", eventos=eventos, erro=str(exc))

    return render_template("eventos.html", eventos=eventos)


@eventos_bp.route("/eventos/<id_evento>")
def detalhe(id_evento):
    """Página de detalhes de um evento específico, com botão de compra."""
    try:
        evento = db.buscar_evento_por_id(id_evento)
        if evento:
            evento = _anexar_url_imagem(evento)
    except AWSServiceError as exc:
        return render_template("evento.html", evento=None, erro=str(exc))

    return render_template("evento.html", evento=evento)
