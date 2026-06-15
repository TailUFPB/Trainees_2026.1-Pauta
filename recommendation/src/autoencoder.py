# AUTOENCODER 

# imports necessários:

# torch -> biblioteca padrão em pytorch para deep learning
# nn -> é o módulo de redes neurais do torch
# Dataset, DataLoader -> classes para criação de datasets e carregamento em lotes
# numpy -> manipulação de arrays numéricos
# pathlib -> paths multiplataforma

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path

# datapath
# base_dir -> raiz do projeto (recommendation/)
# embeddings_path -> caminho do arquivo .npy com os embeddings agregados por vereador
# model_path -> caminho onde o modelo treinado será salvo
BASE_DIR = Path(__file__).resolve().parent.parent
EMBEDDINGS_PATH = BASE_DIR / "models" / "embeddings.npy"
MODEL_PATH = BASE_DIR / "models" / "autoencoder.pt"

# configurações
# input_dim -> dimensão dos embeddings do BERT português (768)
# hidden_dim -> dimensão da primeira camada oculta
# latent_dim -> dimensão do espaço latente (representação comprimida do vereador)
# learning_rate -> taxa de aprendizado do otimizador
# epochs -> número de épocas de treinamento
# batch_size -> tamanho do lote para o DataLoader

INPUT_DIM  = 768
HIDDEN_DIM = 256
LATENT_DIM = 64
LEARNING_RATE = 1e-3
EPOCHS = 200
BATCH_SIZE = 16

# device: usa GPU se disponível, senão CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Dataset

# EmbeddingsDataset -> encapsula os embeddings como um Dataset do PyTorch
# necessário para usar com o DataLoader e iterar em lotes durante o treino
class EmbeddingsDataset(Dataset):
    def __init__(self, embeddings: np.ndarray):
        # converte o numpy array para tensor float32
        self.data = torch.tensor(embeddings, dtype=torch.float32)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]

# carregar_embeddings -> carrega o arquivo .npy e retorna um DataLoader
def carregar_embeddings(caminho: Path = EMBEDDINGS_PATH, batch_size: int = BATCH_SIZE) -> DataLoader:
    """Carrega embeddings do disco e retorna um DataLoader pronto para treino."""
    if not caminho.exists():
        raise FileNotFoundError(
            f"Embeddings não encontrados em: {caminho}\n"
            "Execute src/embeddings.py antes de treinar o autoencoder."
        )
    embeddings = np.load(caminho)
    print(f"[autoencoder] Embeddings carregados: {embeddings.shape}")
    dataset = EmbeddingsDataset(embeddings)
    # shuffle=True para embaralhar a cada época
    return DataLoader(dataset, batch_size=batch_size, shuffle=True)

# Arquitetura do Autoencoder

# autoencoder -> rede neural que comprime os embeddings (768 -> 256 -> 64)
# e reconstrói a partir do espaço latente (64 -> 256 -> 768)
# o objetivo é aprender uma representação compacta de cada vereador
class Autoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        # encoder -> comprime de INPUT_DIM para LATENT_DIM
        self.encoder = nn.Sequential(
            nn.Linear(INPUT_DIM, HIDDEN_DIM),
            nn.ReLU(),
            nn.Linear(HIDDEN_DIM, LATENT_DIM),
        )
        # decoder -> reconstrói de LATENT_DIM para INPUT_DIM
        self.decoder = nn.Sequential(
            nn.Linear(LATENT_DIM, HIDDEN_DIM),
            nn.ReLU(),
            nn.Linear(HIDDEN_DIM, INPUT_DIM),
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

    # encode -> retorna apenas a representação latente (sem reconstruir)
    # usado após o treino para obter os vetores comprimidos
    def encode(self, x):
        return self.encoder(x)

# Funções utilitárias

# extrair_latente -> dado um modelo treinado e os embeddings originais,
# retorna as representações no espaço latente como numpy array
@torch.no_grad()
def extrair_latente(model: Autoencoder, embeddings: np.ndarray) -> np.ndarray:
    """Extrai as representações latentes dos embeddings usando o encoder treinado."""
    model.eval()
    tensor = torch.tensor(embeddings, dtype=torch.float32).to(device)
    latente = model.encode(tensor)
    return latente.cpu().numpy()

# pipeline principal, apenas para testes rápidos
# o treinamento completo fica em train.py
if __name__ == "__main__":
    print(f"Dispositivo utilizado: {device}")
    model = Autoencoder().to(device)
    print(f"[autoencoder] Arquitetura:\n{model}")
    print(f"[autoencoder] Parâmetros treináveis: {sum(p.numel() for p in model.parameters()):,}")

    # testa carregamento dos embeddings se disponíveis
    if EMBEDDINGS_PATH.exists():
        loader = carregar_embeddings()
        batch = next(iter(loader))
        print(f"[autoencoder] Batch de teste: {batch.shape}")
        saida = model(batch.to(device))
        print(f"[autoencoder] Saída de teste:  {saida.shape}")
    else:
        print("[autoencoder] Embeddings não encontrados — execute embeddings.py primeiro.")
