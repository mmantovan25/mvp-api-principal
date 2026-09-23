import httpx
import re
from fastapi import HTTPException


async def buscar_endereco_por_cep(cep: str) -> dict:
    """
    Busca endereço completo no ViaCEP.
   
    Args:
        cep: CEP com ou sem formatação
       
    Returns:
        dict com dados do endereço ou None se não encontrado
    """
    # Remove caracteres não numéricos
    cep_limpo = re.sub(r'\D', '', cep)
   
    # Valida se tem 8 dígitos
    if len(cep_limpo) != 8:
        raise HTTPException(
            status_code=400,
            detail="CEP deve ter 8 dígitos"
        )
   
    # Chama ViaCEP
    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
   
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.get(url)
            response.raise_for_status()
            dados = response.json()
           
            # ViaCEP retorna {"erro": true} quando CEP não existe
            if "erro" in dados and dados["erro"]:
                raise HTTPException(
                    status_code=404,
                    detail="CEP não encontrado"
                )
           
            return dados
           
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar ViaCEP: {str(e)}"
        )


def validar_formato_cep(cep: str) -> bool:
    """Valida se CEP tem formato válido (8 dígitos)"""
    cep_limpo = re.sub(r'\D', '', cep)
    return len(cep_limpo) == 8


def formatar_cep(cep: str) -> str:
    """Formata CEP no padrão XXXXX-XXX"""
    cep_limpo = re.sub(r'\D', '', cep)
    if len(cep_limpo) == 8:
        return f"{cep_limpo[:5]}-{cep_limpo[5:]}"
    return cep
