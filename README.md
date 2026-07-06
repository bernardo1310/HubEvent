# HubEvent

Plataforma web de gerenciamento de eventos com venda de ingressos e
**autenticação biométrica facial**, construída com **Flask** e integrada de
forma real aos serviços da **AWS** (Amazon S3, Amazon Rekognition, Amazon
DynamoDB e AWS Lambda) através do SDK oficial **boto3**.

Projeto acadêmico com arquitetura em camadas, código comentado e organizado,
pensado para facilitar a explicação da arquitetura e do fluxo biométrico em
apresentações.

---

## 1. Descrição do projeto

O HubEvent permite que usuários:

- criem uma conta (nome, e-mail e senha com hash seguro);
- naveguem e pesquisem eventos disponíveis;
- comprem ingressos;
- cadastrem sua biometria facial (selfie) vinculada ao ingresso comprado;
- validem sua entrada no evento através de reconhecimento facial.

E que administradores:

- acompanhem estatísticas gerais (usuários, eventos, ingressos, validações);
- cadastrem, editem e excluam eventos;
- visualizem usuários, biometrias e ingressos vendidos.

---

## 2. Arquitetura da solução

A aplicação segue uma arquitetura em camadas rígida, na qual **nenhuma rota
Flask acessa o boto3 diretamente** — toda integração com a AWS está
concentrada na pasta `services/`.

### Diagrama de funcionamento

```
 Usuário
   │
   ▼
 Flask (app.py)
   │
   ▼
 Routes (routes/)          <- validação de formulário, autenticação, fluxo HTTP
   │
   ▼
 Services (services/)      <- única camada que conhece a AWS
   │
   ▼
 boto3
   │
   ├──► Amazon S3            (selfies e imagens de eventos)
   ├──► Amazon Rekognition    (DetectFaces / IndexFaces / SearchFacesByImage)
   ├──► Amazon DynamoDB       (Usuarios / Eventos / Ingressos)
   └──► AWS Lambda            (processamento assíncrono + logs no CloudWatch)
```

### Fluxo de cadastro biométrico

```
Usuário → seleciona selfie → upload S3 (usuarios/) → Rekognition.IndexFaces
        → FaceId → atualiza tabela Usuarios → atualiza tabela Ingressos
        → status "Biometria cadastrada"
```

### Fluxo de validação de entrada

```
Usuário → nova selfie → upload S3 (validacao/) → Rekognition.SearchFacesByImage
        → similarity >= 95% ? → "Entrada autorizada" : "Entrada negada"
```

---

## 3. Tecnologias utilizadas

**Backend:** Python 3, Flask, boto3, Flask-Login, Flask-WTF, Werkzeug
Security, python-dotenv.

**Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript (Fetch API / File API).

**AWS:** Amazon S3, Amazon Rekognition, Amazon DynamoDB, AWS Lambda,
Amazon CloudWatch (logs).

---

## 4. Estrutura de pastas

```
HubEvent/
├── app.py                     # Application factory, registro dos blueprints
├── config.py                  # Configuração centralizada (lê o .env)
├── requirements.txt
├── .env.example
├── routes/                    # Camada HTTP (Blueprints) - nunca chama boto3
│   ├── auth.py                 # cadastro, login, logout
│   ├── eventos.py               # página inicial, listagem, detalhes
│   ├── ingressos.py             # compra e listagem de ingressos
│   ├── biometria.py             # cadastro biométrico e validação de entrada
│   └── admin.py                  # painel administrativo
├── services/                  # Única camada que conhece o boto3
│   ├── aws.py                   # sessão boto3 + clientes/resources
│   ├── s3_service.py            # upload/URL pré-assinada/exclusão no S3
│   ├── rekognition_service.py    # DetectFaces / IndexFaces / SearchFacesByImage
│   ├── dynamodb_service.py       # CRUD nas tabelas Usuarios/Eventos/Ingressos
│   └── lambda_service.py         # invocação assíncrona de funções Lambda
├── models/
│   └── user.py                  # Usuario (UserMixin do Flask-Login)
├── utils/
│   ├── forms.py                  # formulários Flask-WTF
│   └── decorators.py             # @admin_required
├── static/
│   ├── css/style.css              # estilo customizado (sem temas prontos)
│   └── js/main.js                  # pré-visualização de selfie/imagem
├── templates/                 # base.html + páginas (Bootstrap 5)
└── lambda_examples/
    └── hubevent_confirma_compra.py  # exemplo de função Lambda de referência
```

---

## 5. Infraestrutura AWS já existente utilizada

| Serviço      | Recurso                | Uso                                             |
|--------------|-------------------------|--------------------------------------------------|
| S3           | `ticketbio-bernardo`    | selfies de usuários, fotos de eventos, validação |
| Rekognition  | `ticketbio-faces`       | IndexFaces / SearchFacesByImage / DetectFaces    |
| DynamoDB     | `Usuarios`              | partition key `idUsuario`                        |
| DynamoDB     | `Eventos`               | partition key `idEvento`                         |
| DynamoDB     | `Ingressos`             | partition key `idIngresso`                       |

Nenhum desses recursos é criado pela aplicação — todos já devem existir na
conta AWS utilizada.

---

## 6. Configuração do `.env`

Copie o modelo e preencha com credenciais reais (nunca versionadas):

```bash
cp .env.example .env
```

```env
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=
AWS_DEFAULT_REGION=us-east-1

AWS_BUCKET_NAME=ticketbio-bernardo
AWS_REKOGNITION_COLLECTION=ticketbio-faces

DYNAMODB_TABLE_USERS=Usuarios
DYNAMODB_TABLE_EVENTS=Eventos
DYNAMODB_TABLE_TICKETS=Ingressos
```

> Em ambientes como AWS Academy/Educate, as credenciais costumam ser
> temporárias (Access Key + Secret Key + Session Token) e expiram
> periodicamente — atualize o `.env` quando necessário.

---

## 7. Instalação

```bash
git clone <repositorio>
cd HubEvent

python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env          # e preencha com suas credenciais
```

---

## 8. Execução

```bash
python app.py
```

A aplicação sobe por padrão em `http://localhost:5000`.

---

## 9. Integração com Amazon S3

Implementada em `services/s3_service.py`. Todo upload usa
`s3_client.upload_fileobj`, e a exibição de imagens no frontend usa
**URLs pré-assinadas** (`generate_presigned_url`), evitando tornar o bucket
público. A estrutura lógica de pastas (`usuarios/`, `eventos/`,
`validacao/`) é respeitada em todas as chaves geradas.

## 10. Integração com Amazon Rekognition

Implementada em `services/rekognition_service.py`, utilizando exclusivamente
a collection `ticketbio-faces` já existente:

- `detect_faces` — valida se há um rosto detectável antes de prosseguir;
- `index_faces` — cadastro biométrico (retorna o `FaceId`);
- `search_faces_by_image` — validação de entrada (compara com o threshold
  de similaridade configurado, padrão 95%).

## 11. Integração com Amazon DynamoDB

Implementada em `services/dynamodb_service.py`, cobrindo todo o CRUD das
tabelas `Usuarios`, `Eventos` e `Ingressos`, incluindo a máquina de estados
do ingresso: `Aguardando biometria` → `Biometria cadastrada` →
`Entrada autorizada` / `Entrada negada`.

## 12. Integração com AWS Lambda

Implementada em `services/lambda_service.py`, através de invocação
assíncrona (`InvocationType="Event"`) da função configurada em
`AWS_LAMBDA_CONFIRMA_COMPRA`. Um exemplo de implementação da função está em
`lambda_examples/hubevent_confirma_compra.py`; seus logs são enviados
automaticamente ao **Amazon CloudWatch**.

---

## 13. Ordem de desenvolvimento sugerida

1. Estrutura inicial do projeto
2. Configuração do Flask
3. Configuração do boto3 (`services/aws.py`)
4. Integração com DynamoDB
5. Sistema de autenticação
6. Painel administrativo
7. Cadastro de eventos
8. Compra de ingressos
9. Upload de imagens para o S3
10. Cadastro biométrico com Rekognition
11. Validação facial
12. Integração com Lambda
13. Testes
14. Documentação

---

## 14. Observações finais

- Nenhuma credencial é gravada no código-fonte; tudo vem do `.env`.
- Todas as chamadas à AWS passam obrigatoriamente por `services/`.
- O projeto não cria novos buckets, tabelas ou collections — utiliza somente
  a infraestrutura já provisionada.
# HubEvent
