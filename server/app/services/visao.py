"""Integração da LLM de análise de fotos.

CONTRATO (não mudar a assinatura sem alinhar com o time):
    classificar(imagem: bytes) -> ClassificacaoFoto
"""

import base64
import json
import logging
import re
import time
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.problema import ClassificacaoFoto, Severidade, TipoProblema

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_TIMEOUT_SECONDS = 180

_TIPOS_VALIDOS: set[str] = {
    "asfalto",
    "alagamento",
    "iluminacao",
    "lixo",
    "arborizacao",
    "sinalizacao",
    "calcada",
    "esgoto",
    "outros",
    "nenhum",
}
_SEVERIDADES_VALIDAS: set[str] = {"baixa", "media", "alta", "critica"}

PROMPT_SISTEMA = """Você é um assistente técnico de infraestrutura municipal.
Analise a imagem fornecida e classifique o problema de infraestrutura pública.

REGRAS DE SEVERIDADE (baseadas em risco real para pedestres/veículos):
- CRITICA: Risco imediato de acidente, queda, atropelamento ou danos graves ao veículo.
  Exemplos: buraco grande (>30cm), poste caído, calçada levantada com desnível >10cm,
  lixo bloqueando totalmente a passada, buracos múltiplos impossibilitando trânsito.
- ALTA: Risco significativo, mas não imediato. Pode causar acidente se não atenção.
  Exemplos: buraco médio (15-30cm), luminária quebrada pendurada, lixo acumulado
  reduzindo visibilidade, calçada com rachaduras profundas, poças grandes em via movimentada.
- MEDIA: Problema visível que incomoda, mas não representa risco imediato.
  Exemplos: buraco pequeno (<15cm), lixo disperso sem bloquear passagem,
  rachaduras superficiais no asfalto, vegetação nas bordas da calçada.
- BAIXA: Problema estético ou de manutenção preventiva.
  Exemplos: pequenas rachaduras, desgaste superficial, manchas no pavimento.

REGRAS DE TIPO:
- ASFALTO: Problemas de pavimentação - buracos, rachaduras, deformações,
  desgaste, remendos, falta de pavimentação (rua de terra com buracos).
  IMPORTANTE: Poças de água em buracos de rua são problema de ASFALTO (drenagem),
  NÃO de alagamento. Alagamento é enchente generalizada que cobre a via toda.
- CALCADA: Problemas em passeios públicos - desnível, buracos, rachaduras,
  obstáculos, falta de acessibilidade. Quando há lixo NA calçada, o problema
  principal é a CALCADA (obstrução do passeio), não o lixo em si.
- LIXO: Acúmulo de resíduos sólidos que compromete a via ou calçada como um todo.
  Use quando o lixo é o problema DOMINANTE e visível (montes, sacos, entulho).
  Se o lixo está apenas sobre um buraco ou calçada quebrada, priorize o problema
  de infraestrutura (asfalto/calcada) sobre o lixo.
- ILUMINACAO: Postes, luminárias, fiação - quebrados, apagados, pendurados,
  fios expostos.
- ALAGAMENTO: APENAS para enchentes generalizadas que cobrem a via toda.
  NÃO use para poças em buracos (isso é asfalto).
- ARBORIZACAO: Árvores, vegetação - queda, galhos obstruindo, raízes levantando calçada.
- SINALIZACAO: Placas, semáforos, faixas de pedestre - apagados, quebrados, ilegíveis.
- ESGOTO: Vazamentos, bueiros entupidos, água servida exposta.
- OUTROS: Problemas que não se encaixam nas categorias acima.
- NENHUM: Se não houver problema visível de infraestrutura pública.

TIPOS VÁLIDOS: asfalto, alagamento, iluminacao, lixo, arborizacao, sinalizacao, calcada, esgoto, outros, nenhum

Retorne APENAS um objeto JSON válido com esta estrutura exata (sem markdown, sem explicações, sem raciocínio):
{
  "problema_detectado": true/false,
  "tipo_problema": "...",
  "subtipo": "...",
  "severidade": "...",
  "descricao": "...",
  "confianca": 0.0,
  "elementos_detectados": [],
  "recomendacao_acao": "..."
}"""


def _fallback(modelo: str, motivo: str) -> ClassificacaoFoto:
    logger.warning("Falha na classificação de visão: %s", motivo)
    return ClassificacaoFoto(
        tipo_problema="outros",
        severidade="baixa",
        resumo_llm="Classificação automática indisponível; revisar manualmente a imagem.",
        palavras_chave=["fallback", "visao", "revisao_manual"],
        modelo_utilizado=f"{modelo}:fallback",
        confianca=0.0,
    )


def _extrair_texto_resposta(resultado: dict[str, Any]) -> str:
    if "result" in resultado and isinstance(resultado["result"], dict):
        choices = resultado["result"].get("choices", [])
    else:
        choices = resultado.get("choices", [])
    if not choices or not isinstance(choices, list):
        raise ValueError("Resposta sem choices.")
    primeiro = choices[0]
    if not isinstance(primeiro, dict):
        raise ValueError("Choice inválido.")
    message = primeiro.get("message", {})
    if not isinstance(message, dict):
        raise ValueError("Message inválida.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Conteúdo textual ausente.")
    return content


def _extrair_json_bruto(texto: str) -> str:
    texto = texto.strip()
    if "```json" in texto:
        texto = texto.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in texto:
        texto = texto.split("```", 2)[1].strip()
    inicio = texto.find("{")
    fim = texto.rfind("}")
    if inicio != -1 and fim != -1 and fim > inicio:
        return texto[inicio : fim + 1]
    return texto


def _limpar_json(texto: str) -> dict[str, Any]:
    json_str = _extrair_json_bruto(texto)
    tentativas = (
        json_str,
        json_str.replace("\\n", " ").replace("\\t", " ").replace("\n", " "),
    )
    for candidato in tentativas:
        try:
            parsed = json.loads(candidato)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*\}", tentativas[-1], re.DOTALL)
    if match:
        parsed = json.loads(match.group(0))
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("Não foi possível extrair JSON válido.")


def _texto(dados: dict[str, Any], chave: str, padrao: str = "") -> str:
    valor = dados.get(chave)
    if valor is None:
        return padrao
    return str(valor).lower().strip()


def _normalizar_confianca(valor: Any) -> float:
    try:
        confianca = float(valor)
    except (TypeError, ValueError):
        return 0.0
    if confianca > 1:
        confianca = confianca / 100
    return max(0.0, min(1.0, confianca))


def _palavras_chave(dados: dict[str, Any], tipo: str, severidade: str) -> list[str]:
    elementos = dados.get("elementos_detectados", [])
    palavras = [tipo, severidade]
    if isinstance(elementos, list):
        palavras.extend(str(item).lower().strip() for item in elementos if str(item).strip())
    subtipo = _texto(dados, "subtipo")
    if subtipo:
        palavras.append(subtipo)
    return list(dict.fromkeys(palavras))[:8]


def _montar_classificacao(dados: dict[str, Any], modelo: str) -> ClassificacaoFoto:
    tipo = _texto(dados, "tipo_problema", "outros")
    if tipo not in _TIPOS_VALIDOS:
        tipo = "outros"

    severidade = _texto(dados, "severidade", "baixa")
    if severidade not in _SEVERIDADES_VALIDAS:
        severidade = "baixa"

    if dados.get("problema_detectado") is False:
        tipo = "nenhum"
        severidade = "baixa"

    descricao = str(dados.get("descricao") or "").strip()
    if not descricao:
        descricao = "Problema de infraestrutura pública identificado na imagem."

    return ClassificacaoFoto(
        tipo_problema=cast(TipoProblema, tipo),
        severidade=cast(Severidade, severidade),
        resumo_llm=descricao[:500],
        palavras_chave=_palavras_chave(dados, tipo, severidade),
        modelo_utilizado=modelo,
        confianca=_normalizar_confianca(dados.get("confianca", 0.0)),
    )


def _chamar_cloudflare(imagem: bytes, modelo: str, account_id: str, api_token: str) -> str:
    imagem_b64 = base64.b64encode(imagem).decode("ascii")
    payload = {
        "model": modelo,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{PROMPT_SISTEMA}\n\nClassifique esta imagem."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{imagem_b64}"},
                    },
                ],
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.2,
        "top_p": 0.95,
        "stream": False,
    }
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    for tentativa in range(_MAX_RETRIES):
        request = Request(url, data=data, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
                resultado = json.loads(response.read().decode("utf-8"))
            return _extrair_texto_resposta(resultado)
        except HTTPError as exc:
            if exc.code == 429 and tentativa < _MAX_RETRIES - 1:
                time.sleep(5 * (2**tentativa))
                continue
            raise
        except URLError:
            if tentativa < _MAX_RETRIES - 1:
                time.sleep(5 * (2**tentativa))
                continue
            raise
    raise RuntimeError("Max retries atingido.")


def classificar(imagem: bytes) -> ClassificacaoFoto:
    """Classifica a imagem com Gemma 4 via Cloudflare Workers AI."""
    settings = get_settings()
    modelo = settings.cloudflare_ai_model
    if not settings.cloudflare_account_id or not settings.cloudflare_api_token:
        return _fallback(modelo, "Cloudflare Workers AI não configurado.")

    try:
        texto = _chamar_cloudflare(
            imagem,
            modelo,
            settings.cloudflare_account_id,
            settings.cloudflare_api_token,
        )
        return _montar_classificacao(_limpar_json(texto), modelo)
    except (
        HTTPError,
        URLError,
        TimeoutError,
        ValueError,
        json.JSONDecodeError,
        ValidationError,
    ) as exc:
        return _fallback(modelo, str(exc))
