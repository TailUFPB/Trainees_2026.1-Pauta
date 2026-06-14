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

# configurações
# nome do modelo -> BERT em português
# coluna com o texto das propostas -> proposta ementa
# coluna com nome dos vereadores -> vereador
# tamanho do batch -> 32 por padrão
MODEL_NAME = "neuralmind/bert-base-portuguese-cased" 
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

# agregar_por_vereador -> agrega os embeddings das propostas de cada vereador pela média
# retorna uma matriz com os embeddings agregados e um dataframe com os metadados
#
# IMPORTANTE: após calcular a média dos embeddings de cada vereador, é necessário:
#   1. subtrair o centroide do corpus (direção média compartilhada por todos)
#   2. re-normalizar os vetores para norma unitária (L2)
# sem isso, todos os vetores ficam extremamente próximos (~0.90 de similaridade cosseno)
# porque compartilham a mesma componente dominante ("texto legislativo genérico")
def agregar_por_vereador(df: pd.DataFrame, embeddings: np.ndarray) -> tuple[np.ndarray, pd.DataFrame]:
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

    # subtrai o centroide do corpus para remover a componente compartilhada
    # isso destaca as diferenças temáticas individuais de cada vereador
    centroide = matriz.mean(axis=0)
    matriz = matriz - centroide

    # re-normaliza cada vetor para norma unitária (L2)
    # necessário porque: (a) a média de vetores normalizados perde a norma unitária
    #                     (b) a subtração do centroide altera as normas
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    normas = np.maximum(normas, 1e-10)  # evita divisão por zero
    matriz = matriz / normas

    metadata = pd.DataFrame(vereadores)
    print(f"[agregação] Matriz final: {matriz.shape}  (vereadores × dimensão)")
    return matriz, metadata

# salvar -> salva a matriz de embeddings e o arquivo de metadados
# metadados pois serão usados em conjunto com os embeddings para recuperar as informações originais
def salvar(matriz: np.ndarray, metadata: pd.DataFrame) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(OUTPUT_PATH, matriz)
    metadata.to_csv(META_PATH, index=False)
    print(f"[salvo] Embeddings → {OUTPUT_PATH}")
    print(f"[salvo] Metadados  → {META_PATH}")

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
    matriz, metadata = agregar_por_vereador(df, embeddings)

    # salva resultados
    salvar(matriz, metadata)

    print("\nEmbeddings gerados com êxito!")