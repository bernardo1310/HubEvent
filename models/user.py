# models/user.py
"""
Modelo de usuário utilizado pelo Flask-Login.

Este objeto NÃO acessa a AWS diretamente: ele apenas encapsula o dicionário
retornado pela camada services/dynamodb_service.py em um objeto compatível
com a interface UserMixin exigida pelo Flask-Login.
"""

from flask_login import UserMixin


class Usuario(UserMixin):
    """Representa um usuário autenticado na sessão do Flask-Login."""

    def __init__(self, dados: dict):
        self.id_usuario = dados["idUsuario"]
        self.nome = dados.get("nome")
        self.email = dados.get("email")
        self.senha_hash = dados.get("senhaHash")
        self.face_id = dados.get("faceId")
        self.biometria_cadastrada = dados.get("biometriaCadastrada", False)
        self.is_admin = dados.get("isAdmin", False)

    def get_id(self):
        # Flask-Login exige que get_id() retorne uma string (usada na sessão).
        return self.id_usuario

    @property
    def is_active(self):
        return True
