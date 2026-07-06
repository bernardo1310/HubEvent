# lambda_examples/hubevent_confirma_compra.py
"""
Exemplo de função AWS Lambda referenciada por services/lambda_service.py
(AWS_LAMBDA_CONFIRMA_COMPRA no .env).

Esta função NÃO faz parte do runtime do Flask: ela deve ser publicada
separadamente na AWS (Console ou IaC) com o nome configurado em
AWS_LAMBDA_CONFIRMA_COMPRA. Este arquivo é apenas um exemplo de referência
para fins acadêmicos.

Responsabilidade: processar de forma assíncrona a confirmação de compra de
um ingresso, registrando um log estruturado no CloudWatch. Em uma evolução
do projeto, esta função poderia também disparar um e-mail de confirmação
ou gravar um registro de auditoria em outra tabela do DynamoDB.
"""

import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Payload esperado (enviado por services/lambda_service.py):
    {
        "evento": "confirmacao_compra",
        "idIngresso": "...",
        "idUsuario": "...",
        "idEvento": "..."
    }
    """
    logger.info("Evento recebido: %s", json.dumps(event))

    id_ingresso = event.get("idIngresso")
    id_usuario = event.get("idUsuario")
    id_evento = event.get("idEvento")

    # Este log é enviado automaticamente ao CloudWatch Logs pelo runtime do Lambda.
    logger.info(
        "Compra confirmada -> ingresso=%s usuario=%s evento=%s",
        id_ingresso, id_usuario, id_evento,
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"mensagem": "Confirmação de compra processada com sucesso."}),
    }
