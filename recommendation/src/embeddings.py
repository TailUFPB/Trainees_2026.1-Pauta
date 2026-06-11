# GERAÇÃO DE EMBEDDINGS

# imports necessários

import os
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
DATA_PATH = BASE_DIR / "data" / "df_nlp_final.csv"
MODELS_DIR = BASE_DIR / "models"
OUTPUT_PATH = MODELS_DIR / "embeddings.npy"
META_PATH = MODELS_DIR / "embeddings_meta.csv"

# configurações
# nome do modelo -> BERT em português
# coluna com o texto das propostas -> proposta ementa
# coluna com nome dos vereadores -> vereador
# tamanho do batch -> 32 por padrão
MODEL_NAME = "neuralmind/bert-base-portuguese-cased" 
EMENTA_COL = "proposta_ementa" 
VEREADOR_COL = "vereador"
BATCH_SIZE = 32

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