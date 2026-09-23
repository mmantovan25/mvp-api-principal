# API Principal - Sistema de Cadastro de Clientes

Sistema web de cadastro de clientes com arquitetura de microsserviços, integrando validação, enriquecimento de dados via API externa e persistência em banco de dados.

## Descrição

Esta é a API principal do sistema, responsável por orquestrar o fluxo completo de cadastro de clientes. Integra-se com uma API secundária para validação e normalização de dados, consome a API externa ViaCEP para enriquecimento de endereços, e persiste as informações em banco de dados SQLite.

## Arquitetura

arquitetura.jpg

O sistema segue o padrão de microsserviços com três componentes principais:

1. **API Principal (FastAPI)** - Orquestra o fluxo completo
2. **API Secundária** - Valida e normaliza dados
3. **ViaCEP (API Externa)** - Enriquece dados de endereço

##  Funcionalidades

-  CRUD completo de clientes (Create, Read, Update, Delete)
-  Validação automática de CEP via API Secundária
-  Normalização de nomes via API Secundária
-  Enriquecimento de endereço via ViaCEP
-  Persistência em banco de dados SQLite
-  Listagem com filtros (por UF) e paginação
-  Estatísticas de cadastros por estado

## 🛠️ Tecnologias Utilizadas

- **Python 3.11**
- **FastAPI 0.115.6** - Framework web moderno e rápido
- **Uvicorn 0.34.0** - Servidor ASGI
- **Pydantic 2.10.5** - Validação de dados
- **httpx 0.28.1** - Cliente HTTP assíncrono
- **SQLite3** - Banco de dados embutido

## API Externa Utilizada

### ViaCEP

**URL Base:** `https://viacep.com.br/`

**Descrição:** API pública e gratuita para consulta de endereços brasileiros por CEP.

**Licença:** Uso gratuito, sem necessidade de cadastro ou chave de API

**Rota Utilizada:**

GET https://viacep.com.br/ws/{cep}/json/

**Exemplo de Request:**
GET https://viacep.com.br/ws/01310100/json/

Exemplo de Response:

{
  "cep": "01310-100",
  "logradouro": "Avenida Paulista",
  "complemento": "lado ímpar",
  "bairro": "Bela Vista",
  "localidade": "São Paulo",
  "uf": "SP",
  "ibge": "3550308",
  "gia": "1004",
  "ddd": "11",
  "siafi": "7107"
}

Tratamento de Erros:

CEP inexistente: retorna {"erro": true}

A aplicação valida e retorna erro 404 ao usuário

Documentação Oficial: https://viacep.com.br/

## Instalação

Pré-requisitos
Python 3.11 ou superior
pip (gerenciador de pacotes Python)
API Secundária rodando em http://localhost:8001

1: Clone o repositório

git clone https://github.com/mmantovan25/mvp-api-principal
cd mvp-api-principal

2: Instale as dependências

pip install -r requirements.txt

3: O banco de dados será criado automaticamente

O arquivo clientes.db será gerado na primeira execução.

## Executando a aplicação

# Modo desenvolvimento (com reload automático)

uvicorn app.main:app --reload --port 8000

# Modo produção

uvicorn app.main:app --host 0.0.0.0 --port 8000

A API estará disponível em: http://localhost:8000

## Documentação Interativa

Acesse a documentação Swagger em: http://localhost:8000/docs

# Endpoints

CRUD de Clientes

Método
Endpoint
Descrição

POST
/clientes
Cria um novo cliente

GET
/clientes/{id}
Busca cliente por ID

GET
/clientes
Lista clientes (com filtros)

PUT
/clientes/{id}
Atualiza cliente existente

DELETE
/clientes/{id}
Deleta um cliente

Endpoints Adicionais

Método
Endpoint
Descrição

GET
/estatisticas
Estatísticas de cadastros por UF

## Exemplos de Uso

Criar Cliente

Request:

POST http://localhost:8000/clientes
Content-Type: application/json

{
  "nome": "maria silva",
  "cep": "01310100",
  "email": "maria@email.com"
}

Fluxo Interno:

API Principal chama API Secundária para validar CEP

API Principal chama API Secundária para normalizar nome

API Principal chama ViaCEP para buscar endereço

API Principal salva tudo no SQLite

Response:

{
  "id": 1,
  "nome": "Maria Silva",
  "cep": "01310-100",
  "email": "maria@email.com",
  "logradouro": "Avenida Paulista",
  "complemento": "lado ímpar",
  "bairro": "Bela Vista",
  "cidade": "São Paulo",
  "uf": "SP"
}

Buscar Cliente por ID

Request:

GET http://localhost:8000/clientes/1

Response:

{
  "id": 1,
  "nome": "Maria Silva",
  "cep": "01310-100",
  "email": "maria@email.com",
  "logradouro": "Avenida Paulista",
  "complemento": "lado ímpar",
  "bairro": "Bela Vista",
  "cidade": "São Paulo",
  "uf": "SP"
}

Listar Clientes com Filtro

Request:

GET http://localhost:8000/clientes?uf=SP&skip=0&limit=10

Response:

{
  "clientes": [
    {
      "id": 1,
      "nome": "Maria Silva",
      "uf": "SP",
      ...
    }
  ],
  "total": 1,
  "filtro_uf": "SP"
}

Atualizar Cliente

Request:

PUT http://localhost:8000/clientes/1
Content-Type: application/json

{
  "nome": "Maria Silva Santos",
  "cep": "20040020",
  "email": "maria.santos@email.com"
}

Observação: Se o CEP for alterado, o endereço será atualizado automaticamente via ViaCEP.

Deletar Cliente

Request:

DELETE http://localhost:8000/clientes/1

Response:

{
  "mensagem": "Cliente deletado com sucesso"
}

Estatísticas

Request:

GET http://localhost:8000/estatisticas

Response:

{
  "total_clientes": 150,
  "clientes_por_uf": {
    "SP": 80,
    "RJ": 45,
    "MG": 25
  }
}

# Fluxo de Integração

Cadastro de Cliente (POST /clientes)

1. Cliente envia dados (nome, cep, email)
   ↓
2. API Principal → API Secundária
   - Valida formato do CEP
   - Normaliza o nome (Title Case)
   ↓
3. API Principal → ViaCEP
   - Busca endereço completo pelo CEP
   ↓
4. API Principal → SQLite
   - Salva cliente com todos os dados enriquecidos
   ↓
5. Retorna cliente completo para o usuário

Atualização de Cliente (PUT /clientes/{id})

1. Verifica se cliente existe
   ↓
2. Se CEP mudou:
   - Valida novo CEP na API Secundária
   - Busca novo endereço no ViaCEP
   ↓
3. Se nome mudou:
   - Normaliza na API Secundária
   ↓
4. Atualiza registro no SQLite
   ↓
5. Retorna cliente atualizado

## Estrutura do Banco de Dados

Tabela: clientes

Campo
Tipo
Descrição

id
INTEGER
Chave primária (autoincrement)

nome
TEXT
Nome completo (normalizado)

cep
TEXT
CEP formatado (XXXXX-XXX)

email
TEXT
Email do cliente (opcional)

logradouro
TEXT
Rua/Avenida (do ViaCEP)

complemento
TEXT
Complemento (do ViaCEP)

bairro
TEXT
Bairro (do ViaCEP)

cidade
TEXT
Cidade (do ViaCEP)

uf
TEXT
Estado (do ViaCEP)

## Docker

Construir a imagem

docker build -t mvp-api-principal .

Executar o container

docker run -d -p 8000:8000 mvp-api-principal

## Estrutura do Projeto

mvp-api-principal/
├── app/
│   ├── __init__.py
│   ├── main.py          # Rotas da API
│   ├── database.py      # Funções de banco de dados
│   └── services.py      # Integração com ViaCEP
├── arquitetura.jpg      # Diagrama da arquitetura
├── clientes.db          # Banco de dados SQLite (gerado automaticamente)
├── Dockerfile           # Configuração Docker
├── requirements.txt     # Dependências Python
├── test_database.py     # Testes do banco de dados
├── test_viacep.py       # Testes da integração com ViaCEP
└── README.md            # Este arquivo

## Testes

Testar funções do banco de dados

python test_database.py

Testar integração com ViaCEP

python test_viacep.py

## Dependências

O sistema depende de:

API Secundária rodando em http://localhost:8001

Repositório: https://github.com/mmantovan25/mvp-api-secundaria

Endpoints utilizados:
POST /validar-cep - Validação de formato

POST /normalizar-nome - Normalização de texto

ViaCEP (API pública externa)

URL: https://viacep.com.br/

Endpoint utilizado: GET /ws/{cep}/json/

## Tratamento de Erros

Situação
HTTP Status
Mensagem

CEP com formato inválido
400
"CEP deve ter 8 dígitos"

CEP não encontrado no ViaCEP
404
"CEP não encontrado"

Cliente não existe
404
"Cliente não encontrado"

Nome vazio ou inválido
422
Erro de validação Pydantic

API Secundária offline
500
"Erro ao comunicar com API Secundária"




