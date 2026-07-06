# routes/auth.py
"""
Rotas de autenticação: cadastro, login e logout.

Importante: nenhuma rota aqui acessa boto3 diretamente. Toda persistência
de usuários é feita através de services/dynamodb_service.py.
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from utils.forms import CadastroForm, LoginForm
from models.user import Usuario
from services import dynamodb_service as db
from services.aws import AWSServiceError

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    """
    Cadastro de novo usuário.

    Nesta etapa NÃO existe biometria: apenas nome, e-mail e senha.
    A senha é armazenada com hash seguro (Werkzeug Security), nunca em texto puro.
    """
    if current_user.is_authenticated:
        return redirect(url_for("eventos.index"))

    form = CadastroForm()
    if form.validate_on_submit():
        try:
            if db.buscar_usuario_por_email(form.email.data):
                flash("Já existe uma conta cadastrada com este e-mail.", "warning")
                return render_template("cadastro.html", form=form)

            senha_hash = generate_password_hash(form.senha.data)
            db.criar_usuario(form.nome.data, form.email.data, senha_hash)

            flash("Cadastro realizado com sucesso! Faça login para continuar.", "success")
            return redirect(url_for("auth.login"))
        except AWSServiceError as exc:
            flash(f"Erro ao criar conta: {exc}", "danger")

    return render_template("cadastro.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Autenticação do usuário via e-mail e senha."""
    if current_user.is_authenticated:
        return redirect(url_for("eventos.index"))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            dados_usuario = db.buscar_usuario_por_email(form.email.data)

            if dados_usuario and check_password_hash(dados_usuario["senhaHash"], form.senha.data):
                usuario = Usuario(dados_usuario)
                login_user(usuario)
                flash(f"Bem-vindo(a), {usuario.nome}!", "success")

                proxima = url_for("admin.dashboard") if usuario.is_admin else url_for("eventos.index")
                return redirect(proxima)

            flash("E-mail ou senha inválidos.", "danger")
        except AWSServiceError as exc:
            flash(f"Erro ao autenticar: {exc}", "danger")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("eventos.index"))
