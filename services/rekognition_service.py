# services/rekognition_service.py
"""
Serviço responsável pela integração com o Amazon Rekognition.

Collection já existente e utilizada por toda a aplicação: ticketbio-faces
Esta collection NUNCA deve ser recriada pela aplicação.

Operações utilizadas:
    - DetectFaces          -> valida se a imagem enviada realmente contém um rosto
    - IndexFaces            -> cadastra o rosto do usuário na collection (biometria)
    - SearchFacesByImage    -> compara uma nova selfie com os rostos indexados
                               (validação de entrada no evento)
"""

import logging
from botocore.exceptions import ClientError, BotoCoreError

from config import Config
from services.aws import rekognition_client, AWSServiceError

logger = logging.getLogger("hubevent.rekognition")


def detectar_rosto(image_bytes: bytes) -> bool:
    """
    Verifica se a imagem enviada contém pelo menos um rosto detectável.

    Utilizado como validação antes de indexar ou buscar rostos, evitando
    chamadas desnecessárias (e custos) para imagens sem rosto.
    """
    try:
        response = rekognition_client.detect_faces(
            Image={"Bytes": image_bytes},
            Attributes=["DEFAULT"],
        )
        return len(response.get("FaceDetails", [])) > 0
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao detectar rosto na imagem")
        raise AWSServiceError(f"Falha ao detectar rosto: {exc}") from exc


def cadastrar_rosto(image_bytes: bytes, id_usuario: str) -> str:
    """
    Indexa o rosto do usuário na collection ticketbio-faces (cadastro biométrico).

    Args:
        image_bytes: conteúdo binário da selfie do usuário.
        id_usuario: identificador do usuário, usado como ExternalImageId,
                    permitindo relacionar o FaceId retornado ao usuário no DynamoDB.

    Returns:
        FaceId gerado pelo Rekognition para este rosto.
    """
    try:
        response = rekognition_client.index_faces(
            CollectionId=Config.AWS_REKOGNITION_COLLECTION,
            Image={"Bytes": image_bytes},
            ExternalImageId=id_usuario,
            DetectionAttributes=["DEFAULT"],
            QualityFilter="AUTO",
            MaxFaces=1,
        )

        registros = response.get("FaceRecords", [])
        if not registros:
            raise AWSServiceError(
                "Nenhum rosto foi identificado com qualidade suficiente para cadastro biométrico."
            )

        face_id = registros[0]["Face"]["FaceId"]
        logger.info("Rosto indexado com sucesso para usuário %s (FaceId=%s)", id_usuario, face_id)
        return face_id
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao indexar rosto no Rekognition")
        raise AWSServiceError(f"Falha ao cadastrar biometria facial: {exc}") from exc


def buscar_rosto_similar(image_bytes: bytes, threshold: float = None):
    """
    Compara a selfie enviada na entrada do evento com os rostos já indexados
    na collection, retornando o melhor match encontrado (se houver).

    Args:
        image_bytes: selfie tirada no momento da validação de entrada.
        threshold: percentual mínimo de similaridade (padrão: valor do config).

    Returns:
        dict com "face_id", "external_image_id" (id_usuario) e "similarity",
        ou None caso nenhum rosto atenda ao threshold mínimo.
    """
    threshold = threshold or Config.REKOGNITION_SIMILARITY_THRESHOLD

    try:
        response = rekognition_client.search_faces_by_image(
            CollectionId=Config.AWS_REKOGNITION_COLLECTION,
            Image={"Bytes": image_bytes},
            MaxFaces=1,
            FaceMatchThreshold=threshold,
        )

        matches = response.get("FaceMatches", [])
        if not matches:
            logger.info("Nenhum rosto correspondente encontrado (threshold=%s%%)", threshold)
            return None

        melhor_match = matches[0]
        resultado = {
            "face_id": melhor_match["Face"]["FaceId"],
            "external_image_id": melhor_match["Face"].get("ExternalImageId"),
            "similarity": melhor_match["Similarity"],
        }
        logger.info(
            "Rosto correspondente encontrado: usuario=%s similarity=%.2f%%",
            resultado["external_image_id"], resultado["similarity"],
        )
        return resultado
    except rekognition_client.exceptions.InvalidParameterException:
        # Lançada pelo Rekognition quando nenhum rosto é encontrado na imagem enviada.
        logger.info("Nenhum rosto detectado na imagem de validação enviada")
        return None
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Erro ao buscar rosto similar no Rekognition")
        raise AWSServiceError(f"Falha ao validar biometria facial: {exc}") from exc
