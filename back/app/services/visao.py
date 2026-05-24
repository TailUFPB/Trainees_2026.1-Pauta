"""Seam da LLM de análise de fotos.

CONTRATO (não mudar a assinatura sem alinhar com o time):
    classificar(imagem: bytes) -> ClassificacaoFoto

A implementação abaixo é um STUB determinístico que devolve uma classificação
plausível, permitindo que todo o fluxo de POST /problemas funcione end-to-end sem a
LLM real. O colega responsável pela visão substitui o corpo de `classificar` por uma
chamada ao MLLM (ex.: Gemini 2.5 Flash) com o prompt de sistema fixo, mantendo o
retorno no formato `ClassificacaoFoto`.
"""

import hashlib

from app.schemas.problema import ClassificacaoFoto

# Ciclo determinístico de tipos para o stub (baseado no hash da imagem), só para
# gerar variedade nos dados de desenvolvimento.
_TIPOS_STUB = [
    "buraco",
    "alagamento",
    "iluminacao",
    "entulho",
    "calcada_irregular",
]
_SEVERIDADES_STUB = ["baixa", "media", "alta", "critica"]


def classificar(imagem: bytes) -> ClassificacaoFoto:
    """STUB: classifica a imagem de forma determinística pelo hash do conteúdo.

    Substituir pela chamada real ao MLLM. Manter o retorno em ClassificacaoFoto.
    """
    h = hashlib.sha256(imagem).digest()
    tipo = _TIPOS_STUB[h[0] % len(_TIPOS_STUB)]
    severidade = _SEVERIDADES_STUB[h[1] % len(_SEVERIDADES_STUB)]
    # Confiança entre 0.50 e 0.99 — exercita também o caminho de precisa_revisao (<0.6).
    confianca = round(0.50 + (h[2] / 255) * 0.49, 2)

    return ClassificacaoFoto(
        tipo_problema=tipo,
        severidade=severidade,
        resumo_llm=f"[STUB] Problema do tipo {tipo} com severidade {severidade}.",
        palavras_chave=[tipo, severidade, "stub"],
        modelo_utilizado="stub-visao-0.1",
        confianca=confianca,
    )
