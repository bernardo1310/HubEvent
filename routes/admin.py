# routes/admin.py
"""
Rotas do painel administrativo: dashboard, gestão de eventos, usuários e ingressos.

Todas as rotas deste blueprint exigem que o usuário esteja autenticado E
marcado como administrador (isAdmin=True na tabela Usuarios), através do
decorator utils.decorators.admin_required.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from utils.decorators import admin_required
from utils.forms import EventoForm
from services import dynamodb_service as db
from services import s3_service
from services.aws import AWSServiceError

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    """Dashboard administrativo: totais de usuários, eventos, ingressos e validações."""
    try:
        usuarios = db.listar_usuarios()
        eventos = db.listar_eventos()
        ingressos = db.listar_todos_ingressos()
    except AWSServiceError as exc:
        flash(f"Erro ao carregar dashboard: {exc}", "danger")
        usuarios, eventos, ingressos = [], [], []

    total_validacoes = sum(
        1 for i in ingressos
        if i.get("status") in (db.STATUS_ENTRADA_AUTORIZADA, db.STATUS_ENTRADA_NEGADA)
    )

    estatisticas = {
        "total_usuarios": len(usuarios),
        "total_eventos": len(eventos),
        "total_ingressos": len(ingressos),
        "total_validacoes": total_validacoes,
    }

    return render_template("admin.html", secao="dashboard", estatisticas=estatisticas)


@admin_bp.route("/eventos")
@login_required
@admin_required
def eventos():
    """Lista todos os eventos para gestão (editar/excluir)."""
    try:
        lista_eventos = db.listar_eventos()
    except AWSServiceError as exc:
        flash(f"Erro ao carregar eventos: {exc}", "danger")
        lista_eventos = []

    return render_template("admin.html", secao="eventos", eventos=lista_eventos)


@admin_bp.route("/eventos/novo", methods=["GET", "POST"])
@login_required
@admin_required
def novo_evento():
    """Cadastro de um novo evento, com upload opcional de imagem para o S3."""
    form = EventoForm()

    if form.validate_on_submit():
        try:
            imagem_key = None
            # A chave da imagem só é conhecida após a criação do evento (usa idEvento no path),
            # então criamos o evento primeiro e, se houver imagem, fazemos o upload em seguida.
            dados = {
                "nome": form.nome.data,
                "descricao": form.descricao.data,
                "local": form.local.data,
                "data": form.data.data.isoformat(),
                "horario": form.horario.data.strftime("%H:%M"),
                "valor": str(form.valor.data),
            }
            evento = db.criar_evento(dados)

            if form.imagem.data:
                extensao = form.imagem.data.filename.rsplit(".", 1)[-1].lower()
                imagem_key = s3_service.upload_imagem_evento(
                    evento["idEvento"], form.imagem.data.read(), extensao
                )
                db.atualizar_evento(evento["idEvento"], {"imagemKey": imagem_key})

            flash("Evento cadastrado com sucesso!", "success")
            return redirect(url_for("admin.eventos"))
        except AWSServiceError as exc:
            flash(f"Erro ao cadastrar evento: {exc}", "danger")

    return render_template("admin.html", secao="novo_evento", form=form)


@admin_bp.route("/eventos/<id_evento>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar_evento(id_evento):
    """Edição de um evento existente."""
    try:
        evento = db.buscar_evento_por_id(id_evento)
    except AWSServiceError as exc:
        flash(f"Erro ao carregar evento: {exc}", "danger")
        return redirect(url_for("admin.eventos"))

    if not evento:
        flash("Evento não encontrado.", "warning")
        return redirect(url_for("admin.eventos"))

    form = EventoForm(data=evento) if request.method == "GET" else EventoForm()

    if form.validate_on_submit():
        try:
            dados = {
                "nome": form.nome.data,
                "descricao": form.descricao.data,
                "local": form.local.data,
                "data": form.data.data.isoformat(),
                "horario": form.horario.data.strftime("%H:%M"),
                "valor": str(form.valor.data),
            }

            if form.imagem.data:
                extensao = form.imagem.data.filename.rsplit(".", 1)[-1].lower()
                imagem_key = s3_service.upload_imagem_evento(id_evento, form.imagem.data.read(), extensao)
                dados["imagemKey"] = imagem_key

            db.atualizar_evento(id_evento, dados)
            flash("Evento atualizado com sucesso!", "success")
            return redirect(url_for("admin.eventos"))
        except AWSServiceError as exc:
            flash(f"Erro ao atualizar evento: {exc}", "danger")

    return render_template("admin.html", secao="editar_evento", form=form, evento=evento)


@admin_bp.route("/eventos/<id_evento>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir_evento(id_evento):
    """Exclusão de um evento."""
    try:
        evento = db.buscar_evento_por_id(id_evento)
        if evento and evento.get("imagemKey"):
            s3_service.excluir_objeto(evento["imagemKey"])
        db.excluir_evento(id_evento)
        flash("Evento excluído com sucesso.", "success")
    except AWSServiceError as exc:
        flash(f"Erro ao excluir evento: {exc}", "danger")

    return redirect(url_for("admin.eventos"))


@admin_bp.route("/usuarios")
@login_required
@admin_required
def usuarios():
    """Visualização de usuários cadastrados, com status de biometria e ingressos."""
    try:
        lista_usuarios = db.listar_usuarios()
        for usuario in lista_usuarios:
            usuario["ingressos"] = db.listar_ingressos_do_usuario(usuario["idUsuario"])
    except AWSServiceError as exc:
        flash(f"Erro ao carregar usuários: {exc}", "danger")
        lista_usuarios = []

    return render_template("admin.html", secao="usuarios", usuarios=lista_usuarios)


@admin_bp.route("/ingressos")
@login_required
@admin_required
def ingressos():
    """Visualização de todos os ingressos: comprador, evento, data, status e biometria."""
    try:
        lista_ingressos = db.listar_todos_ingressos()
        for ingresso in lista_ingressos:
            ingresso["usuario"] = db.buscar_usuario_por_id(ingresso["idUsuario"])
            ingresso["evento"] = db.buscar_evento_por_id(ingresso["idEvento"])
        lista_ingressos.sort(key=lambda i: i.get("comprEm", ""), reverse=True)
    except AWSServiceError as exc:
        flash(f"Erro ao carregar ingressos: {exc}", "danger")
        lista_ingressos = []

    return render_template("admin.html", secao="ingressos", ingressos=lista_ingressos)
