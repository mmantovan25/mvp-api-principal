import sqlite3
from typing import Optional, List, Dict
from datetime import datetime

# Nome do arquivo do banco de dados
DATABASE_NAME = "clientes.db"


def get_connection():
    """
    Cria e retorna uma conexão com o banco SQLite.
    Row_factory permite acessar colunas por nome (como dicionário).
    """
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """
    Inicializa o banco de dados e cria a tabela 'clientes' se não existir.
    
    Campos:
    - id: Chave primária auto-incremento
    - nome: Nome completo do cliente
    - cep: CEP no formato XXXXX-XXX
    - logradouro: Rua/Avenida (vem do ViaCEP)
    - complemento: Complemento do endereço
    - bairro: Bairro
    - localidade: Cidade
    - uf: Estado (sigla)
    - created_at: Data/hora de criação (automático)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cep TEXT NOT NULL,
            logradouro TEXT,
            complemento TEXT,
            bairro TEXT,
            localidade TEXT,
            uf TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Banco de dados inicializado com sucesso!")


def criar_cliente(dados: dict) -> int:
    """
    Insere um novo cliente no banco.
    
    Args:
        dados: Dicionário com os campos do cliente
               (nome, cep, logradouro, complemento, bairro, localidade, uf)
    
    Returns:
        ID do cliente criado
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO clientes (nome, cep, logradouro, complemento, bairro, localidade, uf)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados['nome'],
        dados['cep'],
        dados.get('logradouro'),
        dados.get('complemento'),
        dados.get('bairro'),
        dados.get('localidade'),
        dados.get('uf')
    ))
    
    cliente_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return cliente_id


def buscar_cliente(cliente_id: int) -> Optional[Dict]:
    """
    Busca um cliente específico por ID.
    
    Args:
        cliente_id: ID do cliente
    
    Returns:
        Dicionário com dados do cliente ou None se não encontrado
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def listar_clientes(uf: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict]:
    """
    Lista clientes com filtros opcionais.
    
    Args:
        uf: Filtrar por estado (ex: 'SP', 'RJ')
        skip: Quantidade de registros a pular (paginação)
        limit: Quantidade máxima de registros a retornar
    
    Returns:
        Lista de dicionários com dados dos clientes
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Monta query dinamicamente conforme filtros
    query = 'SELECT * FROM clientes'
    params = []
    
    if uf:
        query += ' WHERE uf = ?'
        params.append(uf.upper())
    
    query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
    params.extend([limit, skip])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def atualizar_cliente(cliente_id: int, dados: dict) -> bool:
    """
    Atualiza dados de um cliente existente.
    
    Args:
        cliente_id: ID do cliente a ser atualizado
        dados: Dicionário com campos a atualizar (apenas os fornecidos)
    
    Returns:
        True se atualizou, False se cliente não existe
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verifica se cliente existe
    cursor.execute('SELECT id FROM clientes WHERE id = ?', (cliente_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    # Monta query de UPDATE dinâmica com apenas os campos fornecidos
    campos_update = []
    valores = []
    
    campos_permitidos = ['nome', 'cep', 'logradouro', 'complemento', 'bairro', 'localidade', 'uf']
    
    for campo in campos_permitidos:
        if campo in dados and dados[campo] is not None:
            campos_update.append(f'{campo} = ?')
            valores.append(dados[campo])
    
    # Se não há nada para atualizar, retorna True (não é erro)
    if not campos_update:
        conn.close()
        return True
    
    # Adiciona o ID no final dos valores
    valores.append(cliente_id)
    
    query = f"UPDATE clientes SET {', '.join(campos_update)} WHERE id = ?"
    
    cursor.execute(query, valores)
    conn.commit()
    conn.close()
    
    return True


def deletar_cliente(cliente_id: int) -> bool:
    """
    Deleta um cliente do banco.
    
    Args:
        cliente_id: ID do cliente a ser deletado
    
    Returns:
        True se deletou, False se cliente não existe
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
    linhas_afetadas = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return linhas_afetadas > 0


def contar_clientes() -> int:
    """
    Retorna o total de clientes cadastrados.
    
    Returns:
        Quantidade total de clientes
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM clientes')
    resultado = cursor.fetchone()
    conn.close()
    
    return resultado['total']


def obter_estatisticas() -> Dict:
    """
    Retorna estatísticas gerais do banco.
    
    Returns:
        Dicionário com total de clientes e distribuição por UF
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total de clientes
    cursor.execute('SELECT COUNT(*) as total FROM clientes')
    total = cursor.fetchone()['total']
    
    # Distribuição por UF
    cursor.execute('''
        SELECT uf, COUNT(*) as quantidade
        FROM clientes
        GROUP BY uf
        ORDER BY quantidade DESC
    ''')
    por_uf = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_clientes": total,
        "distribuicao_por_uf": por_uf
    }
