# services/s3_service.py
"""
Serviço responsável por toda a comunicação com o Amazon S3.

Bucket utilizado: ticketbio-bernardo
Estrutura lógica de pastas dentro do bucket:
    usuarios/    -> selfies de cadastro biométrico dos usuários
    eventos/     -> imagens/fotos dos eventos
    validacao/   -> selfies tiradas no momento da validação de entrada

Nenhuma rota Flask deve chamar boto3 diretamente: todo upload/download
de objetos do S3 passa obrigatoriamente por este módulo.
"""

import io
import logging
import uuid
from botocore.exceptions import ClientError, BotoCoreError

from config import Config
from services.aws import s3_client, AWSServiceError

logger = logging.getLogger("hubevent.s3")


def _upload_bytes(file_bytes: bytes, key: str, content_type: str = "image/jpeg") -> str:
    """
    Realiza o upload de um objeto binário (imagem) para o S3.

    Args:
        file_bytes: conteúdo binário do arquivo.
        key: caminho completo (chave) do objeto dentro do bucket.
        content_type: tipo MIME do arquivo.

    Returns:
        A chave (key) do objeto salvo no S3.
    """
    try:
        s3_client.upload_fileobj(
            io.BytesIO(file_bytes),
            Config.AWS_BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        logger.info("Upload realizado com sucesso: s3://%s/%s", Config.AWS_BUCKET_NAME, key)
        return key
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao enviar arquivo para o S3")
        raise AWSServiceError(f"Falha ao enviar arquivo para o S3: {exc}") from exc


def upload_selfie_usuario(id_usuario: str, file_bytes: bytes, extensao: str = "jpg") -> str:
    """Faz upload da selfie de cadastro biométrico do usuário (pasta usuarios/)."""
    key = f"{Config.S3_PREFIX_USUARIOS}{id_usuario}/{uuid.uuid4().hex}.{extensao}"
    return _upload_bytes(file_bytes, key)


def upload_selfie_validacao(id_usuario: str, file_bytes: bytes, extensao: str = "jpg") -> str:
    """Faz upload da selfie tirada na entrada do evento (pasta validacao/)."""
    key = f"{Config.S3_PREFIX_VALIDACAO}{id_usuario}/{uuid.uuid4().hex}.{extensao}"
    return _upload_bytes(file_bytes, key)


def upload_imagem_evento(id_evento: str, file_bytes: bytes, extensao: str = "jpg") -> str:
    """Faz upload da imagem de um evento (pasta eventos/)."""
    key = f"{Config.S3_PREFIX_EVENTOS}{id_evento}/{uuid.uuid4().hex}.{extensao}"
    return _upload_bytes(file_bytes, key)


def gerar_url_temporaria(key: str, expires_in: int = 3600) -> str:
    """
    Gera uma URL pré-assinada (presigned URL) para exibir uma imagem privada
    do S3 no navegador do usuário sem tornar o bucket público.
    """
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": Config.AWS_BUCKET_NAME, "Key": key},
            ExpiresIn=expires_in,
        )
        return url
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao gerar URL pré-assinada")
        raise AWSServiceError(f"Falha ao gerar URL do S3: {exc}") from exc


def excluir_objeto(key: str) -> None:
    """Remove um objeto do bucket (ex.: ao excluir um evento ou usuário)."""
    try:
        s3_client.delete_object(Bucket=Config.AWS_BUCKET_NAME, Key=key)
        logger.info("Objeto removido do S3: %s", key)
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao excluir objeto do S3")
        raise AWSServiceError(f"Falha ao excluir objeto do S3: {exc}") from exc
