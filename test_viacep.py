"""
Script de teste para validar integração com ViaCEP
Execute: python test_viacep.py
"""

import asyncio
from app.services import buscar_endereco_por_cep, validar_formato_cep, formatar_cep

print("=" * 70)
print("🧪 TESTANDO INTEGRAÇÃO COM ViaCEP")
print("=" * 70)


async def executar_testes():
    """Função assíncrona para executar todos os testes"""
    
    # Teste 1: CEP válido (Av. Paulista, SP)
    print("\n1️⃣  Testando CEP válido: 01310-100 (Av. Paulista)")
    resultado = await buscar_endereco_por_cep("01310-100")
    if resultado:
        print(f"✅ Logradouro: {resultado['logradouro']}")
        print(f"✅ Bairro: {resultado['bairro']}")
        print(f"✅ Cidade: {resultado['localidade']}/{resultado['uf']}")
    else:
        print("❌ Falha ao buscar CEP")
    
    # Teste 2: CEP sem formatação
    print("\n2️⃣  Testando CEP sem máscara: 20040020 (Centro, RJ)")
    resultado = await buscar_endereco_por_cep("20040020")
    if resultado:
        print(f"✅ Logradouro: {resultado['logradouro']}")
        print(f"✅ Cidade: {resultado['localidade']}/{resultado['uf']}")
    else:
        print("❌ Falha ao buscar CEP")
    
    # Teste 3: CEP inválido (não existe)
    print("\n3️⃣  Testando CEP inexistente: 99999-999")
    resultado = await buscar_endereco_por_cep("99999999")
    if resultado:
        print(f"❌ Erro: CEP deveria ser inválido!")
    else:
        print("✅ CEP corretamente identificado como inexistente")
    
    # Teste 4: CEP com formato errado
    print("\n4️⃣  Testando CEP com formato inválido: 123")
    resultado = await buscar_endereco_por_cep("123")
    if resultado:
        print(f"❌ Erro: CEP deveria ser inválido!")
    else:
        print("✅ Formato inválido corretamente rejeitado")
    
    # Teste 5: Validar formato
    print("\n5️⃣  Testando validação de formato")
    print(f"   01310-100: {validar_formato_cep('01310-100')} ✅")
    print(f"   01310100: {validar_formato_cep('01310100')} ✅")
    print(f"   123: {validar_formato_cep('123')} ❌")
    print(f"   abcd-efgh: {validar_formato_cep('abcd-efgh')} ❌")
    
    # Teste 6: Formatar CEP
    print("\n6️⃣  Testando formatação de CEP")
    print(f"   01310100 → {formatar_cep('01310100')}")
    print(f"   20040020 → {formatar_cep('20040020')}")
    print(f"   123 → {formatar_cep('123')} (inválido)")
    
    print("\n" + "=" * 70)
    print("🎉 TESTES CONCLUÍDOS!")
    print("=" * 70)


# Executar testes
if __name__ == "__main__":
    asyncio.run(executar_testes())
