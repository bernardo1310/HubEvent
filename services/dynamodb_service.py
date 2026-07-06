# services/dynamodb_service.py
"""
Serviço responsável por toda a comunicação com o Amazon DynamoDB.

Tabelas já existentes e utilizadas pela aplicação:
    - Usuarios   (partition key: idUsuario)
    - Eventos    (partition key: idEvento)
    - Ingressos  (partition key: idIngresso)

Este módulo concentra todas as operações de CRUD, para que as rotas Flask
jamais precisem conhecer a API do boto3 / DynamoDB diretamente.
"""

import logging
import uuid
from datetime import datetime, timezone

from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError, BotoCoreError

from config import Config
from services.aws import dynamodb_resource, AWSServiceError

logger = logging.getLogger("hubevent.dynamodb")

tabela_usuarios = dynamodb_resource.Table(Config.DYNAMODB_TABLE_USERS)
tabela_eventos = dynamodb_resource.Table(Config.DYNAMODB_TABLE_EVENTS)
tabela_ingressos = dynamodb_resource.Table(Config.DYNAMODB_TABLE_TICKETS)


def _agora() -> str:
    """Retorna o timestamp atual em formato ISO 8601 (UTC)."""
    return datetime.now(timezone.utc).isoformat()


def _novo_id() -> str:
    """Gera um identificador único (UUID4) para uso como partition key."""
    return uuid.uuid4().hex


# ==========================================================
# USUÁRIOS
# ==========================================================

def criar_usuario(nome: str, email: str, senha_hash: str) -> dict:
    """Cria um novo usuário na tabela Usuarios."""
    item = {
        "idUsuario": _novo_id(),
        "nome": nome,
        "email": email.lower().strip(),
        "senhaHash": senha_hash,
        "faceId": None,
        "biometriaCadastrada": False,
        "isAdmin": False,
        "criadoEm": _agora(),
    }
    try:
        tabela_usuarios.put_item(Item=item)
        logger.info("Usuário criado: %s", item["idUsuario"])
        return item
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao criar usuário no DynamoDB")
        raise AWSServiceError(f"Falha ao criar usuário: {exc}") from exc


def buscar_usuario_por_id(id_usuario: str) -> dict | None:
    try:
        response = tabela_usuarios.get_item(Key={"idUsuario": id_usuario})
        return response.get("Item")
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao buscar usuário por id")
        raise AWSServiceError(f"Falha ao buscar usuário: {exc}") from exc


def buscar_usuario_por_email(email: str) -> dict | None:
    """
    Busca um usuário pelo e-mail.

    Como a partition key da tabela é idUsuario (não o e-mail), utilizamos
    um Scan com filtro. Em um cenário de produção real, o ideal seria criar
    um Global Secondary Index (GSI) por email — aqui mantemos a tabela como
    já foi provisionada no ambiente acadêmico, sem alterar seu schema.
    """
    try:
        response = tabela_usuarios.scan(
            FilterExpression=Attr("email").eq(email.lower().strip())
        )
        itens = response.get("Items", [])
        return itens[0] if itens else None
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao buscar usuário por email")
        raise AWSServiceError(f"Falha ao buscar usuário por email: {exc}") from exc


def listar_usuarios() -> list:
    try:
        response = tabela_usuarios.scan()
        return response.get("Items", [])
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao listar usuários")
        raise AWSServiceError(f"Falha ao listar usuários: {exc}") from exc


def atualizar_biometria_usuario(id_usuario: str, face_id: str) -> None:
    """Atualiza o usuário após o cadastro biométrico bem-sucedido (IndexFaces)."""
    try:
        tabela_usuarios.update_item(
            Key={"idUsuario": id_usuario},
            UpdateExpression="SET faceId = :f, biometriaCadastrada = :b",
            ExpressionAttributeValues={":f": face_id, ":b": True},
        )
        logger.info("Biometria atualizada para usuário %s", id_usuario)
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao atualizar biometria do usuário")
        raise AWSServiceError(f"Falha ao atualizar biometria: {exc}") from exc


# ==========================================================
# EVENTOS
# ==========================================================

def criar_evento(dados: dict) -> dict:
    item = {
        "idEvento": _novo_id(),
        "nome": dados["nome"],
        "descricao": dados["descricao"],
        "local": dados["local"],
        "data": dados["data"],
        "horario": dados["horario"],
        "valor": dados["valor"],
        "imagemKey": dados.get("imagemKey"),
        "criadoEm": _agora(),
    }
    try:
        tabela_eventos.put_item(Item=item)
        logger.info("Evento criado: %s", item["idEvento"])
        return item
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao criar evento")
        raise AWSServiceError(f"Falha ao criar evento: {exc}") from exc


def listar_eventos() -> list:
    try:
        response = tabela_eventos.scan()
        return response.get("Items", [])
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao listar eventos")
        raise AWSServiceError(f"Falha ao listar eventos: {exc}") from exc


def buscar_evento_por_id(id_evento: str) -> dict | None:
    try:
        response = tabela_eventos.get_item(Key={"idEvento": id_evento})
        return response.get("Item")
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao buscar evento")
        raise AWSServiceError(f"Falha ao buscar evento: {exc}") from exc


def atualizar_evento(id_evento: str, dados: dict) -> None:
    try:
        expressao = "SET " + ", ".join(f"#{k} = :{k}" for k in dados)
        nomes = {f"#{k}": k for k in dados}
        valores = {f":{k}": v for k, v in dados.items()}
        tabela_eventos.update_item(
            Key={"idEvento": id_evento},
            UpdateExpression=expressao,
            ExpressionAttributeNames=nomes,
            ExpressionAttributeValues=valores,
        )
        logger.info("Evento atualizado: %s", id_evento)
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao atualizar evento")
        raise AWSServiceError(f"Falha ao atualizar evento: {exc}") from exc


def excluir_evento(id_evento: str) -> None:
    try:
        tabela_eventos.delete_item(Key={"idEvento": id_evento})
        logger.info("Evento excluído: %s", id_evento)
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao excluir evento")
        raise AWSServiceError(f"Falha ao excluir evento: {exc}") from exc


# ==========================================================
# INGRESSOS
# ==========================================================

STATUS_AGUARDANDO_BIOMETRIA = "Aguardando biometria"
STATUS_BIOMETRIA_CADASTRADA = "Biometria cadastrada"
STATUS_ENTRADA_AUTORIZADA = "Entrada autorizada"
STATUS_ENTRADA_NEGADA = "Entrada negada"


def criar_ingresso(id_usuario: str, id_evento: str) -> dict:
    item = {
        "idIngresso": _novo_id(),
        "idUsuario": id_usuario,
        "idEvento": id_evento,
        "status": STATUS_AGUARDANDO_BIOMETRIA,
        "faceId": None,
        "comprEm": _agora(),
        "validadoEm": None,
    }
    try:
        tabela_ingressos.put_item(Item=item)
        logger.info("Ingresso criado: %s (usuario=%s, evento=%s)", item["idIngresso"], id_usuario, id_evento)
        return item
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao criar ingresso")
        raise AWSServiceError(f"Falha ao registrar ingresso: {exc}") from exc


def buscar_ingresso_por_id(id_ingresso: str) -> dict | None:
    try:
        response = tabela_ingressos.get_item(Key={"idIngresso": id_ingresso})
        return response.get("Item")
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao buscar ingresso")
        raise AWSServiceError(f"Falha ao buscar ingresso: {exc}") from exc


def listar_ingressos_do_usuario(id_usuario: str) -> list:
    try:
        response = tabela_ingressos.scan(FilterExpression=Attr("idUsuario").eq(id_usuario))
        return response.get("Items", [])
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao listar ingressos do usuário")
        raise AWSServiceError(f"Falha ao listar ingressos: {exc}") from exc


def listar_todos_ingressos() -> list:
    try:
        response = tabela_ingressos.scan()
        return response.get("Items", [])
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao listar ingressos")
        raise AWSServiceError(f"Falha ao listar ingressos: {exc}") from exc


def atualizar_status_ingresso(id_ingresso: str, status: str, face_id: str = None) -> None:
    """Atualiza o status do ingresso (ex.: após cadastro biométrico ou validação de entrada)."""
    try:
        expressao = "SET #s = :s"
        nomes = {"#s": "status"}
        valores = {":s": status}

        if face_id is not None:
            expressao += ", faceId = :f"
            valores[":f"] = face_id

        if status in (STATUS_ENTRADA_AUTORIZADA, STATUS_ENTRADA_NEGADA):
            expressao += ", validadoEm = :v"
            valores[":v"] = _agora()

        tabela_ingressos.update_item(
            Key={"idIngresso": id_ingresso},
            UpdateExpression=expressao,
            ExpressionAttributeNames=nomes,
            ExpressionAttributeValues=valores,
        )
        logger.info("Status do ingresso %s atualizado para: %s", id_ingresso, status)
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao atualizar status do ingresso")
        raise AWSServiceError(f"Falha ao atualizar status do ingresso: {exc}") from exc


def buscar_ingresso_pendente_por_usuario(id_usuario: str) -> dict | None:
    """Busca o ingresso mais recente do usuário que ainda aguarda cadastro biométrico."""
    ingressos = listar_ingressos_do_usuario(id_usuario)
    pendentes = [i for i in ingressos if i.get("status") == STATUS_AGUARDANDO_BIOMETRIA]
    if not pendentes:
        return None
    pendentes.sort(key=lambda i: i.get("comprEm", ""), reverse=True)
    return pendentes[0]
