from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx

# Importar nossas funções do banco e serviços
from app.database import (
    init_database,
    criar_cliente,
    buscar_cliente,
    listar_clientes,
    atualizar_cliente,
    deletar_cliente,
    contar_clientes,
    obter_estatisticas
)
from app.services import buscar_endereco_por_cep

# Criar aplicação FastAPI
app = FastAPI(
    title="API Principal - Cadastro de Clientes",
    description="Sistema completo de cadastro com validação, enriquecimento de endereço e persistência",
    version="1.0.0"
)


# ========== MODELOS PYDANTIC ==========

class ClienteCreate(BaseModel):
    """Modelo para criação de cliente"""
    nome: str
    cep: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Maria Silva",
                "cep": "01310-100"
            }
        }


class ClienteUpdate(BaseModel):
    """Modelo para atualização de cliente"""
    nome: Optional[str] = None
    cep: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Maria Silva Oliveira",
                "cep": "20040-020"
            }
        }


# ========== EVENTOS DE INICIALIZAÇÃO ==========

@app.on_event("startup")
def startup_event():
    """Inicializa banco de dados ao subir a aplicação"""
    init_database()
    print("✅ Banco de dados inicializado!")
    print("📡 API Principal rodando!")


# ========== ROTAS BÁSICAS ==========

@app.get("/")
def root():
    """Rota raiz - informações da API"""
    return {
        "message": "API Principal - Cadastro de Clientes",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "features": [
            "Validação de dados com API Secundária",
            "Enriquecimento de endereço com ViaCEP",
            "Persistência em SQLite",
            "CRUD completo"
        ]
    }


@app.get("/health")
def health_check():
    """Health check da API"""
    return {
        "status": "healthy",
        "database": "connected",
        "total_clientes": contar_clientes()
    }


# ========== ROTAS CRUD (OBRIGATÓRIAS) ==========

@app.post("/clientes", status_code=201)
async def criar_novo_cliente(cliente: ClienteCreate):
    """
    Cria um novo cliente no sistema.
    
    **Fluxo completo:**
    1. Valida CEP na API Secundária
    2. Normaliza nome na API Secundária
    3. Busca endereço completo no ViaCEP
    4. Salva no banco SQLite
    
    **Returns:**
    - Cliente criado com todos os dados (incluindo endereço completo)
    """
    
    # PASSO 1: Validar CEP na API Secundária
    print(f"\n🔄 Criando cliente: {cliente.nome}")
    print(f"1️⃣  Validando CEP na API Secundária...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://localhost:8001/validar-cep",
                json={"cep": cliente.cep}
            )
            validacao = resp.json()
            
            if not validacao.get("valido"):
                raise HTTPException(
                    status_code=400,
                    detail=f"CEP inválido: {validacao.get('mensagem')}"
                )
            
            print(f"   ✅ CEP válido: {validacao['cep_formatado']}")
    
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="API Secundária indisponível. Certifique-se de que está rodando na porta 8001."
        )
    
    # PASSO 2: Normalizar nome na API Secundária
    print(f"2️⃣  Normalizando nome na API Secundária...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://localhost:8001/normalizar-nome",
                json={"nome": cliente.nome}
            )
            normalizacao = resp.json()
            nome_normalizado = normalizacao['nome_normalizado']
            
            print(f"   ✅ Nome normalizado: {nome_normalizado}")
    
    except httpx.RequestError:
        # Se API Secundária falhar, usar nome original
        nome_normalizado = cliente.nome.strip()
        print(f"   ⚠️  API Secundária indisponível, usando nome original")
    
    # PASSO 3: Buscar endereço no ViaCEP
    print(f"3️⃣  Buscando endereço no ViaCEP...")
    
    dados_endereco = await buscar_endereco_por_cep(cliente.cep)
    
    if not dados_endereco:
        raise HTTPException(
            status_code=404,
            detail=f"CEP {cliente.cep} não encontrado no ViaCEP"
        )
    
    # PASSO 4: Salvar no banco SQLite
    print(f"4️⃣  Salvando no banco de dados...")
    
    dados_cliente = {
        'nome': nome_normalizado,
        'cep': dados_endereco['cep'],
        'logradouro': dados_endereco.get('logradouro'),
        'complemento': dados_endereco.get('complemento'),
        'bairro': dados_endereco.get('bairro'),
        'localidade': dados_endereco.get('localidade'),
        'uf': dados_endereco.get('uf')
    }
    
    cliente_id = criar_cliente(dados_cliente)
    
    print(f"✅ Cliente criado com ID: {cliente_id}\n")
    
    # Retornar cliente completo
    return {
        "id": cliente_id,
        "message": "Cliente criado com sucesso",
        **dados_cliente
    }


@app.get("/clientes/{cliente_id}")
def obter_cliente(cliente_id: int):
    """
    Busca um cliente específico por ID.
    
    **Args:**
    - cliente_id: ID do cliente
    
    **Returns:**
    - Dados completos do cliente
    """
    print(f"\n🔍 Buscando cliente ID: {cliente_id}")
    
    cliente = buscar_cliente(cliente_id)
    
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com ID {cliente_id} não encontrado"
        )
    
    print(f"✅ Cliente encontrado: {cliente['nome']}\n")
    return cliente


@app.put("/clientes/{cliente_id}")
async def atualizar_dados_cliente(cliente_id: int, dados: ClienteUpdate):
    """
    Atualiza dados de um cliente existente.
    
    **Regras:**
    - Se alterar nome: normaliza na API Secundária
    - Se alterar CEP: valida e busca novo endereço no ViaCEP
    
    **Args:**
    - cliente_id: ID do cliente a atualizar
    - dados: Campos a atualizar (nome e/ou cep)
    
    **Returns:**
    - Cliente atualizado com todos os dados
    """
    print(f"\n🔄 Atualizando cliente ID: {cliente_id}")
    
    # Verificar se cliente existe
    cliente_existente = buscar_cliente(cliente_id)
    if not cliente_existente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com ID {cliente_id} não encontrado"
        )
    
    dados_atualizacao = {}
    
    # Se atualizar nome, normalizar
    if dados.nome:
        print(f"1️⃣  Normalizando novo nome...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "http://localhost:8001/normalizar-nome",
                    json={"nome": dados.nome}
                )
                normalizacao = resp.json()
                dados_atualizacao['nome'] = normalizacao['nome_normalizado']
                print(f"   ✅ Nome normalizado: {dados_atualizacao['nome']}")
        except:
            dados_atualizacao['nome'] = dados.nome.strip()
    
    # Se atualizar CEP, buscar novo endereço
    if dados.cep:
        print(f"2️⃣  Buscando novo endereço...")
        
        dados_endereco = await buscar_endereco_por_cep(dados.cep)
        
        if not dados_endereco:
            raise HTTPException(
                status_code=404,
                detail=f"CEP {dados.cep} não encontrado no ViaCEP"
            )
        
        dados_atualizacao.update({
            'cep': dados_endereco['cep'],
            'logradouro': dados_endereco.get('logradouro'),
            'complemento': dados_endereco.get('complemento'),
            'bairro': dados_endereco.get('bairro'),
            'localidade': dados_endereco.get('localidade'),
            'uf': dados_endereco.get('uf')
        })
        print(f"   ✅ Novo endereço: {dados_endereco['logradouro']}")
    
    # Atualizar no banco
    print(f"3️⃣  Atualizando no banco...")
    atualizar_cliente(cliente_id, dados_atualizacao)
    
    # Buscar cliente atualizado
    cliente_atualizado = buscar_cliente(cliente_id)
    
    print(f"✅ Cliente atualizado com sucesso!\n")
    
    return {
        "message": "Cliente atualizado com sucesso",
        "cliente": cliente_atualizado
    }


@app.delete("/clientes/{cliente_id}")
def deletar_cliente_por_id(cliente_id: int):
    """
    Deleta um cliente do sistema.
    
    **Args:**
    - cliente_id: ID do cliente a ser deletado
    
    **Returns:**
    - Mensagem de confirmação
    """
    print(f"\n🗑️  Deletando cliente ID: {cliente_id}")
    
    sucesso = deletar_cliente(cliente_id)
    
    if not sucesso:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com ID {cliente_id} não encontrado"
        )
    
    print(f"✅ Cliente deletado com sucesso!\n")
    
    return {
        "message": f"Cliente {cliente_id} deletado com sucesso"
    }


# ========== ROTAS EXTRAS (CRIATIVIDADE +1,0 PT) ==========

@app.get("/clientes")
def listar_todos_clientes(
    uf: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Lista clientes com filtros opcionais.
    
    **Filtros:**
    - uf: Filtrar por estado (ex: SP, RJ)
    - skip: Paginação - quantos pular (offset)
    - limit: Paginação - máximo de resultados
    
    **Returns:**
    - Lista de clientes com metadados de paginação
    """
    clientes = listar_clientes(uf=uf, skip=skip, limit=limit)
    
    return {
        "total": len(clientes),
        "skip": skip,
        "limit": limit,
        "filtro_uf": uf,
        "clientes": clientes
    }


@app.get("/estatisticas")
def obter_estatisticas_gerais():
    """
    Retorna estatísticas gerais do sistema.
    
    **Returns:**
    - Total de clientes cadastrados
    - Distribuição de clientes por UF
    """
    stats = obter_estatisticas()
    
    return {
        "message": "Estatísticas do sistema",
        **stats
    }
