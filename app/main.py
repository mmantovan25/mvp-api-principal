from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.database import (
    atualizar_cliente,
    buscar_cliente,
    contar_clientes,
    criar_cliente,
    deletar_cliente,
    init_database,
    listar_clientes,
    obter_estatisticas,
)
from app.services import buscar_endereco_por_cep

API_SECUNDARIA_URL = "http://localhost:8000"

app = FastAPI(
    title="API Principal - Cadastro de Clientes",
    description="Sistema completo de cadastro com validação, enriquecimento de endereço e persistência",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ClienteCreate(BaseModel):
    nome: str
    cep: str
    email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Maria Silva",
                "cep": "01310-100",
                "email": "maria@email.com",
            }
        }


class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    cep: Optional[str] = None
    email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Maria Silva Oliveira",
                "cep": "20040-020",
                "email": "maria.nova@email.com",
            }
        }


@app.on_event("startup")
def startup_event():
    """Inicializa o banco ao subir a aplicação."""
    init_database()
    print("✅ Banco de dados inicializado!")
    print("📡 API Principal rodando!")


@app.get("/")
def root():
    """Rota raiz com informações da API."""
    return {
        "message": "API Principal - Cadastro de Clientes",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "features": [
            "Validação de dados com API Secundária",
            "Enriquecimento de endereço com ViaCEP",
            "Persistência em SQLite",
            "CRUD completo",
        ],
    }


@app.get("/health")
def health_check():
    """Health check da API."""
    return {
        "status": "healthy",
        "database": "connected",
        "total_clientes": contar_clientes(),
    }


async def _chamar_api_secundaria(path: str, payload: dict):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{API_SECUNDARIA_URL}{path}", json=payload)
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail") or "Erro na API Secundária",
                )
            return response.json()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"API Secundária indisponível: {exc}",
        ) from exc


@app.post("/clientes", status_code=201)
async def criar_novo_cliente(cliente: ClienteCreate):
    """Cria um cliente validando CEP e normalizando o nome."""
    validacao = await _chamar_api_secundaria("/validar-cep", {"cep": cliente.cep})
    if not validacao.get("valido"):
        raise HTTPException(
            status_code=400,
            detail=f"CEP inválido: {validacao.get('mensagem')}",
        )

    try:
        normalizacao = await _chamar_api_secundaria("/normalizar-nome", {"nome": cliente.nome})
        nome_normalizado = normalizacao["nome_normalizado"]
    except HTTPException:
        nome_normalizado = cliente.nome.strip()

    dados_endereco = await buscar_endereco_por_cep(cliente.cep)
    if not dados_endereco:
        raise HTTPException(
            status_code=404,
            detail=f"CEP {cliente.cep} não encontrado no ViaCEP",
        )

    dados_cliente = {
        "nome": nome_normalizado,
        "cep": dados_endereco.get("cep") or cliente.cep,
        "email": cliente.email,
        "logradouro": dados_endereco.get("logradouro"),
        "complemento": dados_endereco.get("complemento"),
        "bairro": dados_endereco.get("bairro"),
        "localidade": dados_endereco.get("localidade"),
        "uf": dados_endereco.get("uf"),
    }

    cliente_id = criar_cliente(dados_cliente)

    return {
        "id": cliente_id,
        "message": "Cliente criado com sucesso",
        "cliente": {**dados_cliente, "id": cliente_id},
    }


@app.get("/clientes/{cliente_id}")
def obter_cliente(cliente_id: int):
    """Busca um cliente pelo ID."""
    cliente = buscar_cliente(cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com ID {cliente_id} não encontrado",
        )
    return cliente


@app.put("/clientes/{cliente_id}")
async def atualizar_dados_cliente(cliente_id: int, dados: ClienteUpdate):
    """Atualiza dados do cliente, validando nome e CEP quando necessário."""
    cliente_existente = buscar_cliente(cliente_id)
    if not cliente_existente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com ID {cliente_id} não encontrado",
        )

    dados_atualizacao = {}

    if dados.nome:
        try:
            normalizacao = await _chamar_api_secundaria("/normalizar-nome", {"nome": dados.nome})
            dados_atualizacao["nome"] = normalizacao["nome_normalizado"]
        except HTTPException:
            dados_atualizacao["nome"] = dados.nome.strip()

    if dados.email is not None:
        dados_atualizacao["email"] = dados.email

    if dados.cep:
        validacao = await _chamar_api_secundaria("/validar-cep", {"cep": dados.cep})
        if not validacao.get("valido"):
            raise HTTPException(
                status_code=400,
                detail=f"CEP inválido: {validacao.get('mensagem')}",
            )

        dados_endereco = await buscar_endereco_por_cep(dados.cep)
        if not dados_endereco:
            raise HTTPException(
                status_code=404,
                detail=f"CEP {dados.cep} não encontrado no ViaCEP",
            )

        dados_atualizacao.update({
            "cep": dados_endereco.get("cep") or dados.cep,
            "logradouro": dados_endereco.get("logradouro"),
            "complemento": dados_endereco.get("complemento"),
            "bairro": dados_endereco.get("bairro"),
            "localidade": dados_endereco.get("localidade"),
            "uf": dados_endereco.get("uf"),
        })

    if not dados_atualizacao:
        return {
            "message": "Nenhum campo foi informado para atualização",
            "cliente": cliente_existente,
        }

    atualizar_cliente(cliente_id, dados_atualizacao)
    cliente_atualizado = buscar_cliente(cliente_id)

    return {
        "message": "Cliente atualizado com sucesso",
        "cliente": cliente_atualizado,
    }


@app.delete("/clientes/{cliente_id}")
def deletar_cliente_por_id(cliente_id: int):
    """Deleta um cliente pelo ID."""
    sucesso = deletar_cliente(cliente_id)
    if not sucesso:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com ID {cliente_id} não encontrado",
        )

    return {
        "message": f"Cliente {cliente_id} deletado com sucesso",
    }


@app.get("/clientes")
def listar_todos_clientes(
    uf: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    """Lista clientes com filtros opcionais."""
    clientes = listar_clientes(uf=uf, skip=skip, limit=limit)
    return {
        "total": len(clientes),
        "skip": skip,
        "limit": limit,
        "filtro_uf": uf,
        "clientes": clientes,
    }


@app.get("/estatisticas")
def obter_estatisticas_gerais():
    """Retorna estatísticas do sistema."""
    stats = obter_estatisticas()
    return {
        "message": "Estatísticas do sistema",
        **stats,
    }
