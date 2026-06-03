# Fatia 1.5 — HMAC do autor: proteção do vínculo cidadão↔reporte no banco

**Data:** 2026-06-03
**Status:** spec aprovado, aguardando plan
**Pré-requisito:** Fatia 1 ("Minha Pauta") mergeada — esta fatia ajusta código criado lá.

## 1. Contexto e propósito

Após a Fatia 1, `problemas.autor_id` ainda guarda o UUID do `users.id` em texto plano. A Fatia 1 ocultou esse campo da API pública (`GET /problemas`, `GET /problemas/{id}` pra não-autores) e habilitou RLS — mas o dado em repouso continua exposto a quem tem acesso ao DB (operadores do banco, leak, ataque interno).

Esta fatia substitui `problemas.autor_id` por `problemas.autor_hmac`, um HMAC-SHA256 determinístico calculado com chave secreta do backend. Dump SQL da tabela `problemas` (mesmo cruzando com `users`) deixa de ser suficiente pra identificar quem reportou o quê — só com a chave HMAC, que mora exclusivamente no env do app.

## 2. Modelo de ameaça

### O que esta fatia resolve

- **Dump da tabela `problemas` isolado** → bytea opacos em `autor_hmac`, impossível ligar a usuário.
- **Dump COMPLETO do DB (problemas + users)** → ainda impossível ligar sem a chave, porque HMAC é one-way.
- **Operador do DB com SELECT** → vê hashes, não consegue desfazer.
- **Vazamento de backup do DB** → idem.

### O que NÃO resolve (aceito como fora do escopo)

- **Servidor totalmente comprometido (DB + env do backend)** → atacante tem a chave, pode recalcular HMAC de qualquer UUID conhecido pra confirmar autoria. Aceito porque equivale a comprometimento total já modelado para o `supabase_jwt_secret`.
- **Linkabilidade entre reportes do mesmo autor** → HMAC determinístico significa que o mesmo user gera o mesmo hash em todos os reportes. Atacante consegue agrupar reportes do mesmo autor sem identificar quem ele é. Resolver isso exige salt por reporte e mapeamento separado — fora do escopo desta fatia.
- **Ataque de força bruta com lista de UUIDs conhecidos** → se atacante já tem a chave E sabe o conjunto de UUIDs do `users`, ele calcula HMAC de cada e descobre o vínculo. Vide ponto 1: cenário de comprometimento total.

## 3. Abordagem técnica

**HMAC-SHA256 determinístico** com chave em env do backend.

- Nova coluna `problemas.autor_hmac` (bytea, 32 bytes).
- Calculado como `HMAC_SHA256(str(user.id).encode(), AUTOR_HMAC_KEY)`.
- `AUTOR_HMAC_KEY` mora em `server/.env` (padrão idêntico ao `supabase_jwt_secret` já estabelecido).
- **Remove** `problemas.autor_id` (a coluna em texto plano). HMAC substitui completamente.
- Determinístico → mesmo user gera mesmo hash → `WHERE autor_hmac = HMAC(:user_id, :chave)` funciona normalmente.

**Por que HMAC e não pseudonimização ou cifragem simétrica?**

| Opção | Por que descartada |
|---|---|
| Pseudonimização (UUID secundário em `users`) | Não protege contra dump completo do DB — atacante junta as duas tabelas e desfaz. |
| Cifragem simétrica (pgcrypto `PGP_SYM_ENCRYPT`) | Não é determinística — quebra `WHERE autor = ?`. Exigiria HMAC paralelo (= solução híbrida, mais complexa que HMAC puro). |
| HMAC determinístico | ✅ Protege contra dump completo, mantém `WHERE` eficiente, sem complexidade extra. |

## 4. Mudanças no backend

### Migration nova — `0010_hmac_autor.py`

Operações:
1. `ALTER TABLE problemas ADD COLUMN autor_hmac bytea` — nullable inicialmente.
2. `CREATE INDEX ix_problemas_autor_hmac ON problemas(autor_hmac)` — pra eficiência de `WHERE autor_hmac = ?`.
3. `ALTER TABLE problemas DROP CONSTRAINT problemas_autor_id_fkey`.
4. `ALTER TABLE problemas DROP COLUMN autor_id`.

**Backfill:** como não há produção ainda e o DB local é descartável (`make db-reset`), a migration não tenta backfillar. Reportes pré-existentes em DBs com legado ficam com `autor_hmac NULL` — caso futuro precise, escrevemos um script CLI separado que lê `AUTOR_HMAC_KEY` do env e popula. Fora do escopo aqui.

**Downgrade:** recria `autor_id` vazio (`SET NULL` por padrão) e a FK. **NÃO recupera o vínculo original** — HMAC é one-way, dados originais ficam perdidos. Docstring da migration documenta explicitamente.

### Helper novo — `server/app/core/hmac_autor.py`

```python
"""HMAC-SHA256 determinístico do user.id para pseudonimizar autoria de reportes.

A chave (AUTOR_HMAC_KEY) mora em env e é estável ao longo da vida do projeto.
Rotação exige re-HMAC de toda a tabela problemas — não fazer sem plano.
"""
import hashlib
import hmac as _hmac
from uuid import UUID

from app.core.config import get_settings


def autor_hmac(user_id: UUID, *, chave: bytes | None = None) -> bytes:
    if chave is None:
        chave = get_settings().autor_hmac_key.encode()
    return _hmac.new(chave, str(user_id).encode(), hashlib.sha256).digest()
```

(Arquivo dedicado em vez de adicionar em `core/auth.py` porque tem responsabilidade própria — fácil de testar e mover se virar lib.)

### Settings — `server/app/core/config.py`

Adicionar `autor_hmac_key: str` no `Settings` (obrigatório, sem default → força configuração explícita). Pydantic valida a presença no startup.

### `.env.example` — `server/.env.example`

Adicionar linha:

```
# Chave secreta para HMAC do autor em problemas (32+ bytes aleatórios)
# Gere com: python -c "import secrets; print(secrets.token_urlsafe(32))"
# Mudar essa chave invalida o vínculo dos reportes existentes — não rotacionar sem plano.
AUTOR_HMAC_KEY=
```

### Modelo `Problema` — `server/app/models/problema.py`

- **Remover** `autor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))`.
- **Adicionar** `autor_hmac: Mapped[bytes | None] = mapped_column(LargeBinary)`.
- Importar `LargeBinary` de `sqlalchemy`.

### Schemas Pydantic — `server/app/schemas/problema.py`

- `ProblemaOut`: remover campo `autor_id`. **Não** adicionar `autor_hmac` (não expor hash na API).
- `ProblemaPublicoOut`: já não tem `autor_id`, sem mudança.

### Endpoints — `server/app/routers/problemas.py` + `routers/usuarios.py`

| Handler | Mudança |
|---|---|
| `POST /problemas` (`criar_problema`) | `problema.autor_hmac = autor_hmac(user.id)` em vez de `autor_id = user.id`. |
| `GET /problemas/{id}` (`obter_problema`) | **Simplificado**: passa a retornar SEMPRE `ProblemaPublicoOut` — sem branching autor-vs-público. Remove `Depends(get_current_user_optional)` desse handler. O autor consome o endpoint dedicado abaixo. |
| `GET /usuarios/me/problemas/{problema_id}` (**novo**, em `usuarios.py`) | Sempre `ProblemaOut` se autor; 404 se não for. Detalhe interno da área logada. Detalhes na seção 7. |
| `PATCH /problemas/{id}/status` (`atualizar_status`) | `if problema.autor_hmac != autor_hmac(user.id): raise 403` |
| `GET /usuarios/me/problemas` (`listar_meus_problemas` em `usuarios.py`) | `WHERE autor_hmac = autor_hmac(user.id)` |
| `GET /problemas` (`listar_problemas`) | Sem mudança — já não retorna `autor_id`. |

### Helper `_to_out` e `_to_problema_out`

Esses helpers em `routers/problemas.py` e `routers/usuarios.py` constroem `ProblemaOut`. Como `ProblemaOut` perde `autor_id`, remover essa linha de ambos.

### Evento `problema.criado` no outbox

Em `POST /problemas`, o payload publicado em `eventos_outbox` é:

```python
{
    "problema_id": str(problema.id),
    "tipo": classificacao.tipo_problema,
    "severidade": classificacao.severidade,
    "confianca": classificacao.confianca,
    "lat": lat,
    "lng": lng,
}
```

Não contém `autor_id` — sem mudança. Bom precedente que os eventos já não vazam autoria.

## 5. Testes

### Novos — `server/tests/test_autor_hmac.py`

```python
"""HMAC determinístico do user_id pra pseudonimizar autoria."""

import uuid

from app.core.hmac_autor import autor_hmac


def test_hmac_deterministico_mesmo_user_mesma_chave():
    uid = uuid.uuid4()
    chave = b"test-key-32-bytes-minimum-aqui--"
    h1 = autor_hmac(uid, chave=chave)
    h2 = autor_hmac(uid, chave=chave)
    assert h1 == h2
    assert len(h1) == 32  # SHA256


def test_hmac_users_diferentes_geram_hashes_diferentes():
    chave = b"test-key-32-bytes-minimum-aqui--"
    h1 = autor_hmac(uuid.uuid4(), chave=chave)
    h2 = autor_hmac(uuid.uuid4(), chave=chave)
    assert h1 != h2


def test_hmac_muda_quando_chave_muda():
    uid = uuid.uuid4()
    h1 = autor_hmac(uid, chave=b"chave-original-32-bytes-minimum.")
    h2 = autor_hmac(uid, chave=b"chave-rotacionada-32-bytes-min..")
    assert h1 != h2
```

### Ajustados

- **`server/tests/test_problemas.py`**
  - `test_fluxo_criar_problema`: remover assert de `autor_id`; adicionar verificação no banco que `problema.autor_hmac` foi populado (não precisa assertar valor exato).
  - `test_atualizar_status_emite_evento`: continua funcionando — mesmo user cria e atualiza.
  - `test_get_problema_autor_recebe_campos_completos`: o teste verifica `body["autor_id"] is not None` — **remover esse assert**, porque o response não tem mais autor_id. Manter o assert que checa `descricao` (que continua presente pra autor).

- **`server/tests/test_meus_problemas.py`**
  - `test_lista_apenas_do_autor`: continua passando porque o backend traduz user → HMAC internamente. Remover qualquer assert direto de `autor_id`.
  - `test_lista_apenas_do_autor`: o assert `p["autor_id"] is not None` precisa virar `"autor_id" not in p` (campo removido do schema).

- **`server/tests/test_users_table.py`** ou novo **`test_problemas_table.py`**: smoke da migration confirmando que `problemas` não tem mais `autor_id` e tem `autor_hmac`:

```python
def test_problemas_sem_autor_id_e_com_autor_hmac():
    from sqlalchemy import inspect
    from app.db.session import engine

    insp = inspect(engine)
    colunas = {c["name"] for c in insp.get_columns("problemas")}
    assert "autor_id" not in colunas
    assert "autor_hmac" in colunas
```

### Verificação manual de modelo de ameaça (não automatizada, documentada)

Após rodar testes:
```bash
docker exec pauta-db-1 pg_dump -U pauta -d pauta -t problemas --data-only --inserts
```
Conferir que o output **não contém** UUIDs reconhecíveis de usuários — só `\x` bytea em `autor_hmac`.

## 6. Critérios de sucesso

1. Migration 0010 aplica e tabela `problemas` não tem mais `autor_id` — só `autor_hmac` (bytea).
2. `POST /problemas` cria reporte com `autor_hmac` preenchido; nenhuma referência a `autor_id` no código.
3. `GET /usuarios/me/problemas` continua retornando só os reportes do autor (existing test verifica).
4. `PATCH /problemas/{id}/status` mantém 403 pra não-autores (existing test verifica).
5. Dump bruto da tabela `problemas` não contém UUIDs de usuários — só bytea em `autor_hmac` (verificação manual).
6. Todos os 59 testes existentes + os ~5 novos da Fatia 1.5 passam.
7. `make ci` verde.
8. `AUTOR_HMAC_KEY` é obrigatória em `server/.env` — startup falha sem ela (Pydantic valida).
9. `ProblemaOut` não tem mais campo `autor_id`; tipo `Problema` no front atualizado.

## 7. Frontend — impacto

O tipo `Problema` no front (`client/src/lib/api/types.ts`) tem campo `autor_id: string | null`. Como o backend deixa de retornar isso, **remover** do tipo.

Consumidores no front que usavam `autor_id`:
- `client/src/app/conta/reportes/[id]/page.tsx` — fazia `if (!("autor_id" in resp)) notFound()` pra detectar se o user é autor. Como **agora a resposta nunca tem `autor_id`**, essa detecção quebra.

**Solução adotada:** endpoint dedicado `GET /usuarios/me/problemas/{problema_id}` no backend. Retorna `ProblemaOut` se autor, 404 se não. O front passa a chamar esse endpoint no detalhe da área logada.

Trade-offs considerados e descartados:
- Backend retornar `sou_autor: bool` no `ProblemaOut` — polui o schema com campo só pra UI.
- Detectar autoria pela presença de campos privados (`descricao`) — heurística frágil, quebra se o schema mudar.
- Manter `GET /problemas/{id}` com branching autor-vs-público — força o front a duvidar do tipo retornado. Pior contrato.

A escolha por endpoint dedicado também permite **simplificar `GET /problemas/{id}`**: ele passa a ser **puramente público** (sempre `ProblemaPublicoOut`), sem dependência de autenticação. Contrato fica previsível em ambos os lados.

Implementação:
```python
@router.get("/me/problemas/{problema_id}", response_model=ProblemaOut)
def obter_meu_problema(
    problema_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProblemaOut:
    row = db.execute(
        select(Problema, ST_Y(Problema.localizacao), ST_X(Problema.localizacao)).where(
            Problema.id == problema_id, Problema.autor_hmac == autor_hmac(user.id)
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reporte não encontrado.")
    p, lat, lng = row
    return _to_problema_out(p, lat, lng)
```

E o front:
- `client/src/lib/api/serverClient.ts::problemaPorIdComoAutor` → fetch para `/usuarios/me/problemas/{id}` em vez de `/problemas/{id}`.
- `client/src/app/conta/reportes/[id]/page.tsx` → remove a checagem heurística (`if (!("autor_id" in resp)) notFound()`) — agora o backend faz a checagem e retorna 404 direto.

## 8. Fora do escopo (roadmap)

- **Rotação de chave HMAC.** Quando precisar, vira fatia própria — exige re-HMAC de toda a tabela, dois deploys, e fallback de leitura dupla.
- **Cifragem at-rest da tabela `users`** ou outros campos PII restantes. Continua planejado pra Fatia 4 "Privacidade & Compliance".
- **Esconder linkabilidade** entre reportes do mesmo autor (HMAC determinístico expõe que dois reportes vieram do mesmo user). Resolver exige salt por reporte + mapeamento separado — fatia futura se virar requisito.
- **Endpoints administrativos** que precisem de "quem fez este reporte?". Pra isso, backend roda `autor_hmac(suspeito_user_id)` e compara — consulta-por-comparação. Não é fatia: é capacidade que já está implícita no design.
- **Backfill em produção** (caso um dia exista DB com reportes pré-HMAC). Quando precisar, script CLI separado lê `AUTOR_HMAC_KEY` e popula. Hoje irrelevante.

## 9. Riscos

| Risco | Mitigação |
|---|---|
| `AUTOR_HMAC_KEY` ausente no `.env` | Pydantic settings exige no startup → erro claro. `.env.example` documenta. |
| Chave muda acidentalmente entre deploys | "Meus Reportes" vira vazio pra todos — sintoma óbvio. Documentar no README que a chave é permanente. |
| Atacante com acesso a DB + env recalcula HMACs | Aceito (modelo equivalente ao do `supabase_jwt_secret`). |
| Dev tentar acessar `problema.autor_id` em código antigo | Atributo não existe mais → erro de Python imediato. Linter pega. |
| `routers/problemas.py:_to_out` esquecido com `autor_id` | Coberto pelos testes — `test_fluxo_criar_problema` falha se response tem `autor_id`. |
| Front quebrar porque o tipo `Problema` tinha `autor_id` | Atualização do tipo `Problema` força typecheck a apontar todos os usos. |

## 10. Resumo da fatia

**Tamanho estimado:** ~6-8 commits, 1 migration, 1 helper novo, ~10 arquivos tocados.

**Dependência:** Fatia 1 mergeada (que cria `GET /usuarios/me/problemas` e o `apiServer.problemaPorIdComoAutor`).

**Não bloqueia:** Fatias 2, 3, 4. Pode ir em paralelo se quiser, mas é melhor fechar antes de Fatia 2 pra não criar mais código que dependa de `autor_id`.
