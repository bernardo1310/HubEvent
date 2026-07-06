# app.py
"""
HubEvent - Ponto de entrada da aplicação Flask.

Responsabilidades deste arquivo:
    - criar e configurar a aplicação Flask (app factory);
    - inicializar o Flask-Login;
    - registrar os Blueprints (routes/);
    - definir handlers de erro básicos.

Este arquivo NÃO contém lógica de negócio nem chamadas diretas ao boto3:
essa responsabilidade é sempre delegada às camadas routes/ e services/.
"""

from flask import Flask, render_template
from flask_login import LoginManager

from config import Config
from models.user import Usuario
from services import dynamodb_service as db
from services.aws import AWSServiceError

from routes.auth import auth_bp
from routes.eventos import eventos_bp
from routes.ingressos import ingressos_bp
from routes.biometria import biometria_bp
from routes.admin import admin_bp


def create_app() -> Flask:
    """Application factory: cria e configura a instância do Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # --- Flask-Login ---
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para acessar esta página."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def carregar_usuario(id_usuario):
        """Recarrega o usuário a partir do DynamoDB a cada requisição autenticada."""
        try:
            dados = db.buscar_usuario_por_id(id_usuario)
            return Usuario(dados) if dados else None
        except AWSServiceError:
            return None

    # --- Registro dos Blueprints (routes/) ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(eventos_bp)
    app.register_blueprint(ingressos_bp)
    app.register_blueprint(biometria_bp)
    app.register_blueprint(admin_bp)

    # --- Handlers de erro ---
    @app.errorhandler(403)
    def acesso_negado(_error):
        return render_template("erro.html", codigo=403, mensagem="Acesso negado."), 403

    @app.errorhandler(404)
    def pagina_nao_encontrada(_error):
        return render_template("erro.html", codigo=404, mensagem="Página não encontrada."), 404

    @app.errorhandler(500)
    def erro_interno(_error):
        return render_template("erro.html", codigo=500, mensagem="Erro interno do servidor."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
