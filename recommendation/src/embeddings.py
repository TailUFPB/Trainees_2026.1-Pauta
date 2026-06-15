# GERAÇÃO DE EMBEDDINGS

# imports necessários

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from pathlib import Path

# datapath
# adiciona os paths dos arquivos no sistema em formato compatível com linux, mac e windows
# base dir é a raiz do projeto
# data_path é o path do arquivo csv com as propostas
# models_dir é o path onde serão salvos os embeddings
# output_path é o path onde serão salvos os embeddings
# meta_path é o path onde serão salvos os metadados
BASE_DIR = Path(__file__).resolve().parent.parent # recommendation/
DATA_PATH = BASE_DIR / "data" / "df_nlp_filtrado.csv"  
MODELS_DIR = BASE_DIR / "models"
OUTPUT_PATH = MODELS_DIR / "embeddings.npy"
META_PATH = MODELS_DIR / "embeddings_meta.csv"
CENTROID_PATH = MODELS_DIR / "centroid.npy"
PROPOSAL_OUTPUT_PATH = MODELS_DIR / "proposal_embeddings.npy"
PROPOSAL_META_PATH = MODELS_DIR / "proposal_embeddings_meta.csv"

# configurações
# nome do modelo -> BERT em português
# coluna com o texto das propostas -> proposta ementa
# coluna com nome dos vereadores -> vereador
# tamanho do batch -> 32 por padrão
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  # SBERT 768d: treinado p/ similaridade semântica (cosseno reflete significado)
EMENTA_COL = "proposta_ementa_filtrada" 
VEREADOR_COL = "vereador"
BATCH_SIZE = 32

# padrões de ementas genéricas (boilerplate institucional)
# essas ementas não revelam preferência temática individual e distorcem os embeddings
PADROES_GENERICOS = [
    r"^sem_proposta_ementa$",
    r"^emenda\s.*(lei\s+de\s+diretrizes|impositiva|orçament)",
    r"^estima\s+a\s+receita\s+e\s+fixa\s+a\s+despesa",
    r"^dispõe\s+sobre\s+denominação\s+de\s+(rua|predio)",
]

# definindo funções

# carregar dados -> carrega o csv e valida as colunas obrigatórias com base na sua presença
def carregar_dados(caminho: Path) -> pd.DataFrame:
    """Carrega e valida o dataset principal"""
    if not caminho.exists():
        raise FileNotFoundError(f"Dataset não encontrado em: {caminho}\n" "Execute o pipeline de pré-processamento antes de rodar este script.")
    # lê o csv e checa se as colunas obrigatórias existem
    df = pd.read_csv(caminho)
    
    for col in [EMENTA_COL, VEREADOR_COL]:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente no dataset: '{col}'")

    # remove linhas sem ementa
    df = df.dropna(subset=[EMENTA_COL]).reset_index(drop=True)
    print(f"[dados] {len(df)} propostas carregadas de {len(df[VEREADOR_COL].unique())} vereadores.")
    return df


# limpar dados -> remove placeholders, ementas genéricas e duplicatas intra-vereador
def limpar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Remove placeholders, ementas genéricas e duplicatas intra-vereador.

    Filtro 1: remove linhas com placeholder 'sem_proposta_ementa'
    Filtro 2: remove ementas genéricas (boilerplate institucional) via regex
    Filtro 3: deduplica ementas dentro de cada vereador (mantém 1 cópia)
    """
    n_original = len(df)

    # Filtro 1: remove placeholder
    mask_placeholder = df[EMENTA_COL] == "sem_proposta_ementa"
    n_placeholder = mask_placeholder.sum()
    df = pd.DataFrame(df[~mask_placeholder])
    print(f"[limpeza] Filtro 1 — removidas {n_placeholder} linhas com 'sem_proposta_ementa'")

    # Filtro 2: remove ementas genéricas por regex
    regex_combinado = "|".join(PADROES_GENERICOS)
    mask_generico = df[EMENTA_COL].str.contains(
        regex_combinado, case=False, na=False, regex=True
    )
    n_generico = mask_generico.sum()
    df = pd.DataFrame(df[~mask_generico])
    print(f"[limpeza] Filtro 2 — removidas {n_generico} ementas genéricas")

    # Filtro 3: deduplica por vereador
    n_antes_dedup = len(df)
    df = df.drop_duplicates(subset=[VEREADOR_COL, "municipio", EMENTA_COL])
    n_dedup = n_antes_dedup - len(df)
    print(f"[limpeza] Filtro 3 — removidas {n_dedup} duplicatas intra-vereador")

    df = df.reset_index(drop=True)

    # vereadores que ficaram sem propostas serão excluídos automaticamente na agregação
    n_vereadores = df[VEREADOR_COL].nunique()
    print(f"[limpeza] Resultado: {n_original} → {len(df)} propostas "
          f"({n_original - len(df)} removidas), {n_vereadores} vereadores restantes")
    return df

# gerar embeddings -> gera embeddings das propostas
def gerar_embeddings(textos: list[str], modelo: SentenceTransformer) -> np.ndarray:
    """Gera embeddings para uma lista de textos usando o modelo BERT"""

    # informa via terminal qual o número de propostas será usado para gerar os embeddings
    print(f"[embeddings] Gerando embeddings para {len(textos)} textos")

    # gera embeddings com os seguintes parâmetros
    # textos -> texto a ser codificado
    # batch_size -> tamanho do lote de textos
    # show_progress_bar -> mostra barra de progresso
    # convert_to_numpy -> converte para numpy array
    # normalize_embeddings -> normaliza os embeddings (l2-norm) permitindo o cálculo de similaridade de cosseno via produto escalar
    embeddings = modelo.encode(textos, batch_size=BATCH_SIZE, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True,)
    return embeddings

# projetar_no_espaco -> FONTE ÚNICA DE VERDADE do espaço vetorial dos perfis
#
# Subtrai o centróide do corpus (direção média compartilhada por todos os perfis) e
# re-normaliza para norma L2 unitária. TANTO os perfis dos vereadores (agregar_por_vereador)
# QUANTO a query do cidadão (recommend.embed_query / backend gerar_embedding) DEVEM passar
# exatamente por esta mesma transformação. Se a query for projetada de forma diferente,
# ela cai num espaço distinto dos perfis e o ranking de cosseno vira ruído — sem erro
# explícito. Manter esta função como o único lugar onde a projeção acontece elimina esse
# drift por construção.
#
# Aceita um vetor (D,) OU uma matriz (N, D); retorna no mesmo formato.
def projetar_no_espaco(vetores: np.ndarray, centroide: np.ndarray) -> np.ndarray:
    """Projeta vetores BERT no espaço centrado dos perfis (subtrai centróide + L2)."""
    v = np.asarray(vetores, dtype=np.float32)
    unidim = v.ndim == 1
    if unidim:
        v = v[None, :]
    # subtrai o centroide do corpus para remover a componente compartilhada
    # (destaca as diferenças temáticas individuais de cada vereador)
    v = v - centroide
    # re-normaliza cada vetor para norma unitária (L2); necessário porque a subtração
    # do centróide altera as normas (e a média de vetores normalizados já as perde)
    normas = np.linalg.norm(v, axis=1, keepdims=True)
    normas = np.maximum(normas, 1e-10)  # evita divisão por zero
    v = v / normas
    return v[0] if unidim else v

# agregar_por_vereador -> agrega os embeddings das propostas de cada vereador pela média
# retorna uma matriz com os embeddings agregados e um dataframe com os metadados
#
# IMPORTANTE: após calcular a média dos embeddings de cada vereador, é necessário:
#   1. subtrair o centroide do corpus (direção média compartilhada por todos)
#   2. re-normalizar os vetores para norma unitária (L2)
# sem isso, todos os vetores ficam extremamente próximos (~0.90 de similaridade cosseno)
# porque compartilham a mesma componente dominante ("texto legislativo genérico")
def agregar_por_vereador(df: pd.DataFrame, embeddings: np.ndarray) -> tuple[np.ndarray, pd.DataFrame, np.ndarray]:
    df = df.copy()
    df["_emb_idx"] = range(len(df))

    vereadores = []
    vetores = []

    grupos = df.groupby([VEREADOR_COL, "municipio"])

    for (nome, municipio), grupo in grupos:
        idxs = grupo["_emb_idx"].values
        vetor_medio = embeddings[idxs].mean(axis=0)
        vetores.append(vetor_medio)
        vereadores.append({"nome": nome, "municipio": municipio})

    matriz = np.array(vetores, dtype=np.float32)

    # centróide do corpus: média dos vetores-perfil ANTES da subtração/normalização.
    # PRECISA ser persistido (salvar) — sem ele é impossível projetar a query do cidadão
    # no mesmo espaço dos perfis. Não é recuperável de embeddings.npy (já normalizado).
    centroide = matriz.mean(axis=0).astype(np.float32)

    # projeta os perfis no espaço centrado — MESMA transformação aplicada à query
    matriz = projetar_no_espaco(matriz, centroide)

    metadata = pd.DataFrame(vereadores)
    print(f"[agregação] Matriz final: {matriz.shape}  (vereadores × dimensão)")
    return matriz, metadata, centroide

# salvar -> salva a matriz de embeddings e o arquivo de metadados
# metadados pois serão usados em conjunto com os embeddings para recuperar as informações originais
def preparar_evidencias(
    df: pd.DataFrame,
    modelo: SentenceTransformer,
    centroide: np.ndarray,
) -> tuple[np.ndarray, pd.DataFrame]:
    """Embeddings PROJETADOS dos resumos das propostas + metadados (evidências).

    As evidências são embeddadas a partir do RESUMO em linguagem natural (o mesmo texto
    exibido ao cidadão), e não da ementa em juridiquês — assim a similaridade casa com a
    query, que também é linguagem natural. Os vetores passam pela MESMA projeção dos perfis
    (projetar_no_espaco) para viverem no mesmo espaço da query.
    """
    metadata = df[
        [
            VEREADOR_COL,
            "municipio",
            "proposta_tipo",
            "proposta_numero",
            "proposta_ano",
            "resumo_proposta",
            "proposta_ementa",
        ]
    ].copy()
    metadata["resumo"] = (
        metadata["resumo_proposta"]
        .fillna(metadata["proposta_ementa"])
        .fillna("")
        .str.strip()
    )
    metadata = metadata.rename(
        columns={
            VEREADOR_COL: "nome",
            "proposta_tipo": "tipo",
            "proposta_numero": "numero",
            "proposta_ano": "ano",
        }
    )[["nome", "municipio", "tipo", "numero", "ano", "resumo"]].reset_index(drop=True)

    bruto = gerar_embeddings(metadata["resumo"].tolist(), modelo)
    vetores = projetar_no_espaco(bruto, centroide)
    return vetores.astype(np.float32), metadata


def salvar(
    matriz: np.ndarray,
    metadata: pd.DataFrame,
    centroide: np.ndarray,
    proposal_embeddings: np.ndarray,
    proposal_metadata: pd.DataFrame,
) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(OUTPUT_PATH, matriz)
    np.save(CENTROID_PATH, centroide)
    np.save(PROPOSAL_OUTPUT_PATH, proposal_embeddings)
    metadata.to_csv(META_PATH, index=False)
    proposal_metadata.to_csv(PROPOSAL_META_PATH, index=False)
    print(f"[salvo] Embeddings → {OUTPUT_PATH}")
    print(f"[salvo] Centróide  → {CENTROID_PATH}  (shape {centroide.shape})")
    print(f"[salvo] Metadados  → {META_PATH}")
    print(
        f"[salvo] Evidências → {PROPOSAL_OUTPUT_PATH} "
        f"(shape {proposal_embeddings.shape})"
    )
    print(f"[salvo] Metadados de evidências → {PROPOSAL_META_PATH}")

# pipeline principal
if __name__ == "__main__":
    # carrega dados
    df = carregar_dados(DATA_PATH)

    # limpa dados (remove placeholders, genéricas e duplicatas)
    df = limpar_dados(df)

    # carrega modelo BERT em português
    print(f"[modelo] Carregando '{MODEL_NAME}'...")
    modelo = SentenceTransformer(MODEL_NAME)

    # gera embeddings das ementas
    embeddings = gerar_embeddings(df[EMENTA_COL].tolist(), modelo)

    # agrega por vereador (média dos embeddings das propostas)
    matriz, metadata, centroide = agregar_por_vereador(df, embeddings)
    proposal_embeddings, proposal_metadata = preparar_evidencias(
        df,
        modelo,
        centroide,
    )

    # salva resultados (inclui o centróide do corpus, necessário p/ embeddar a query)
    salvar(
        matriz,
        metadata,
        centroide,
        proposal_embeddings,
        proposal_metadata,
    )

    print("\nEmbeddings gerados com êxito!")
