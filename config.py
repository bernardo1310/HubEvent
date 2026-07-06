# config.py
"""
Configuração centralizada da aplicação HubEvent.

Todas as variáveis sensíveis (credenciais AWS, nomes de tabelas, bucket, etc.)
são carregadas a partir do arquivo .env através da biblioteca python-dotenv.

Nenhuma credencial real deve ser gravada neste arquivo ou em qualquer outro
arquivo versionado do projeto. Utilize sempre o arquivo .env (não versionado)
com base no modelo .env.example.
"""

import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env, se existir.
load_dotenv()


class Config:
    """Configurações gerais da aplicação Flask."""

    # --- Flask ---
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "chave-secreta-desenvolvimento-trocar-em-producao")
    DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"

    # --- AWS - Credenciais e região ---
    # As credenciais são lidas pelo boto3 automaticamente a partir das
    # variáveis de ambiente abaixo (ou de um perfil configurado localmente).
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")  # opcional, usado com credenciais temporárias
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    # --- Amazon S3 ---
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "ticketbio-bernardo")
    S3_PREFIX_USUARIOS = "usuarios/"
    S3_PREFIX_EVENTOS = "eventos/"
    S3_PREFIX_VALIDACAO = "validacao/"

    # --- Amazon Rekognition ---
    AWS_REKOGNITION_COLLECTION = os.getenv("AWS_REKOGNITION_COLLECTION", "ticketbio-faces")
    # Percentual mínimo de similaridade exigido para autorizar a entrada no evento.
    REKOGNITION_SIMILARITY_THRESHOLD = float(os.getenv("REKOGNITION_SIMILARITY_THRESHOLD", "95"))

    # --- Amazon DynamoDB ---
    DYNAMODB_TABLE_USERS = os.getenv("DYNAMODB_TABLE_USERS", "Usuarios")
    DYNAMODB_TABLE_EVENTS = os.getenv("DYNAMODB_TABLE_EVENTS", "Eventos")
    DYNAMODB_TABLE_TICKETS = os.getenv("DYNAMODB_TABLE_TICKETS", "Ingressos")

    # --- AWS Lambda ---
    # Nome da função Lambda utilizada para processamento assíncrono
    # (ex.: confirmação de compra, geração de logs em CloudWatch).
    AWS_LAMBDA_CONFIRMA_COMPRA = os.getenv("AWS_LAMBDA_CONFIRMA_COMPRA", "hubevent-confirma-compra")

    # --- Upload ---
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB - limite de tamanho de upload de selfies
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
