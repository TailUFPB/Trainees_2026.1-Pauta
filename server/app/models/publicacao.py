from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Publicacao(Base):
    """Post livre da timeline social. Texto até 1000 chars, imagem opcional.

    Autor segue o mesmo esquema de problemas (cifra reversível + lookup HMAC).
    Quando `anonimo=True`, ambos `autor_cifrado` e `autor_lookup` ficam NULL.
    """

    __tablename__ = "publicacoes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    autor_cifrado: Mapped[bytes | None] = mapped_column(LargeBinary)
    autor_lookup: Mapped[bytes | None] = mapped_column(LargeBinary)
    anonimo: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    conteudo: Mapped[str] = mapped_column(String(1000), nullable=False)
    imagem_url: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
