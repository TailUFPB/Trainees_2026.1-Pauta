# PostGIS + pgvector na mesma imagem (espelha o que o Supabase oferece em prod).
FROM postgis/postgis:16-3.4
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
