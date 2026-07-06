# services/lambda_service.py
"""
Serviço responsável por invocar funções AWS Lambda.

O Flask permanece como backend principal da aplicação. O Lambda é utilizado
apenas em pontos específicos e não críticos ao fluxo síncrono principal:
    - processamento assíncrono após a compra do ingresso;
    - geração de logs estruturados (registrados automaticamente no CloudWatch);
    - confirmação da compra (envio de "recibo"/registro de evento de negócio);
    - ponto de extensão para futuras integrações (ex.: envio de e-mail, notificações).

Importante: a invocação é feita de forma assíncrona (InvocationType="Event"),
para não bloquear a resposta ao usuário enquanto o Lambda processa a tarefa.
"""

import json
import logging
from botocore.exceptions import ClientError, BotoCoreError

from config import Config
from services.aws import lambda_client, AWSServiceError

logger = logging.getLogger("hubevent.lambda")


def invocar_confirmacao_compra(id_ingresso: str, id_usuario: str, id_evento: str) -> bool:
    """
    Invoca a função Lambda responsável por processar a confirmação de compra.

    A invocação é assíncrona (fire-and-forget): a aplicação Flask não espera
    o resultado do processamento para responder ao usuário, apenas registra
    se a invocação foi aceita com sucesso pela AWS.

    Retorna True se a invocação foi aceita, False caso a função Lambda ainda
    não esteja configurada no ambiente (para não travar o fluxo principal
    da compra em ambiente acadêmico onde o Lambda pode não existir).
    """
    payload = {
        "evento": "confirmacao_compra",
        "idIngresso": id_ingresso,
        "idUsuario": id_usuario,
        "idEvento": id_evento,
    }

    try:
        response = lambda_client.invoke(
            FunctionName=Config.AWS_LAMBDA_CONFIRMA_COMPRA,
            InvocationType="Event",  # assíncrono - não bloqueia a resposta ao usuário
            Payload=json.dumps(payload).encode("utf-8"),
        )
        aceito = response.get("StatusCode") == 202
        if aceito:
            logger.info("Lambda de confirmação de compra invocada com sucesso: %s", payload)
        return aceito
    except lambda_client.exceptions.ResourceNotFoundException:
        # A função Lambda ainda não foi criada no ambiente da AWS Academy/conta utilizada.
        # Não deve interromper o fluxo de compra: apenas registra o aviso em log.
        logger.warning(
            "Função Lambda '%s' não encontrada. Pulando processamento assíncrono.",
            Config.AWS_LAMBDA_CONFIRMA_COMPRA,
        )
        return False
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao invocar função Lambda de confirmação de compra")
        raise AWSServiceError(f"Falha ao invocar Lambda: {exc}") from exc
