# services/aws.py
"""
Módulo central de acesso à AWS.

Este é o ÚNICO ponto do projeto onde uma sessão boto3 é criada.
Todos os demais serviços (s3_service, rekognition_service, dynamodb_service,
lambda_service) importam os clientes/resources definidos aqui, garantindo que
nenhuma rota Flask precise conhecer detalhes de autenticação da AWS.

Fluxo de arquitetura obrigatório do projeto:
    Usuário -> Flask -> Routes -> Services -> boto3 -> AWS
"""

import logging
import boto3
from config import Config

# Configuração básica de logging para toda a aplicação.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hubevent.aws")


def _build_session() -> boto3.session.Session:
    """
    Cria a sessão boto3 utilizando as credenciais definidas no .env.

    Se as variáveis de ambiente não estiverem preenchidas, o boto3 tentará
    utilizar automaticamente outras fontes de credenciais (ex.: perfil
    configurado em ~/.aws/credentials, variáveis de ambiente do sistema,
    ou role da instância EC2), conforme a cadeia padrão de resolução de
    credenciais da AWS.
    """
    session_kwargs = {"region_name": Config.AWS_DEFAULT_REGION}

    if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
        session_kwargs["aws_access_key_id"] = Config.AWS_ACCESS_KEY_ID
        session_kwargs["aws_secret_access_key"] = Config.AWS_SECRET_ACCESS_KEY
        if Config.AWS_SESSION_TOKEN:
            session_kwargs["aws_session_token"] = Config.AWS_SESSION_TOKEN

    logger.info("Inicializando sessão boto3 na região %s", Config.AWS_DEFAULT_REGION)
    return boto3.session.Session(**session_kwargs)


# Sessão única, reaproveitada por todos os serviços (padrão singleton simples).
_session = _build_session()

# --- Clientes / Resources reutilizáveis ---
s3_client = _session.client("s3")
rekognition_client = _session.client("rekognition")
dynamodb_resource = _session.resource("dynamodb")
lambda_client = _session.client("lambda")


class AWSServiceError(Exception):
    """
    Exceção customizada para erros de integração com a AWS.

    Utilizada pelos services para encapsular exceções do boto3 (ClientError,
    BotoCoreError, etc.) em uma exceção única e mais amigável para as rotas
    Flask tratarem e exibirem mensagens adequadas ao usuário final.
    """
    pass
