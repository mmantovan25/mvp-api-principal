"""
Script de teste para validar funções do database.py
Execute: python test_database.py
"""

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

print("=" * 60)
print("🧪 TESTANDO FUNÇÕES DO BANCO DE DADOS")
print("=" * 60)

# 1. Inicializar banco
print("\n1️⃣  Inicializando banco de dados...")
init_database()

# 2. Criar cliente 1
print("\n2️⃣  Criando cliente 1...")
cliente1_id = criar_cliente({
    'nome': 'Maria Silva',
    'cep': '01310-100',
    'logradouro': 'Avenida Paulista',
    'bairro': 'Bela Vista',
    'localidade': 'São Paulo',
    'uf': 'SP'
})
print(f"✅ Cliente criado com ID: {cliente1_id}")

# 3. Criar cliente 2
print("\n3️⃣  Criando cliente 2...")
cliente2_id = criar_cliente({
    'nome': 'João Santos',
    'cep': '20040-020',
    'logradouro': 'Avenida Rio Branco',
    'bairro': 'Centro',
    'localidade': 'Rio de Janeiro',
    'uf': 'RJ'
})
print(f"✅ Cliente criado com ID: {cliente2_id}")

# 4. Buscar cliente por ID
print("\n4️⃣  Buscando cliente 1...")
cliente = buscar_cliente(cliente1_id)
print(f"✅ Cliente encontrado: {cliente['nome']} - {cliente['localidade']}/{cliente['uf']}")

# 5. Listar todos os clientes
print("\n5️⃣  Listando todos os clientes...")
todos = listar_clientes()
print(f"✅ Total de clientes: {len(todos)}")
for c in todos:
    print(f"   - ID {c['id']}: {c['nome']} ({c['localidade']}/{c['uf']})")

# 6. Filtrar por UF
print("\n6️⃣  Filtrando clientes de SP...")
clientes_sp = listar_clientes(uf='SP')
print(f"✅ Clientes em SP: {len(clientes_sp)}")
for c in clientes_sp:
    print(f"   - {c['nome']}")

# 7. Atualizar cliente
print("\n7️⃣  Atualizando cliente 1...")
sucesso = atualizar_cliente(cliente1_id, {
    'nome': 'Maria Silva Oliveira',
    'complemento': 'Sala 1001'
})
if sucesso:
    cliente_atualizado = buscar_cliente(cliente1_id)
    print(f"✅ Cliente atualizado: {cliente_atualizado['nome']}")

# 8. Contar clientes
print("\n8️⃣  Contando clientes...")
total = contar_clientes()
print(f"✅ Total de clientes no banco: {total}")

# 9. Estatísticas
print("\n9️⃣  Obtendo estatísticas...")
stats = obter_estatisticas()
print(f"✅ Total: {stats['total_clientes']}")
print(f"✅ Distribuição por UF:")
for item in stats['distribuicao_por_uf']:
    print(f"   - {item['uf']}: {item['quantidade']} cliente(s)")

# 10. Deletar cliente
print("\n🔟 Deletando cliente 2...")
sucesso = deletar_cliente(cliente2_id)
if sucesso:
    print(f"✅ Cliente {cliente2_id} deletado com sucesso!")
    print(f"✅ Total restante: {contar_clientes()}")

print("\n" + "=" * 60)
print("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
print("=" * 60)
