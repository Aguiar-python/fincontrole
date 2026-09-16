import os
import ssl
from contextlib import contextmanager
from urllib.parse import unquote, urlparse

import pg8000.dbapi as pg8000
from dotenv import load_dotenv

load_dotenv()


def _config_da_conexao():
    """
    Aceita duas formas de configuração:

    1) DATABASE_URL (recomendado para Supabase/Neon/Render)
       Ex.: postgresql://postgres.xxxx:SENHA@aws-0-sa-east-1.pooler.supabase.com:5432/postgres

    2) Variáveis separadas DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD
       (usado quando o Postgres roda no próprio EasyPanel)
    """
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        p = urlparse(database_url)
        return {
            "host": p.hostname,
            "port": p.port or 5432,
            "database": (p.path or "/postgres").strip("/") or "postgres",
            "user": unquote(p.username or ""),
            "password": unquote(p.password or ""),
        }

    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }


def get_conn():
    cfg = _config_da_conexao()
    sslmode = os.getenv("DB_SSLMODE", "disable")

    ssl_context = None
    if sslmode != "disable":
        ssl_context = ssl.create_default_context()
        # Sem isso, alguns provedores (Supabase incluso) usam certificados
        # que o Python não valida por padrão nessa forma de conexão.
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    return pg8000.connect(
        host=cfg["host"],
        port=cfg["port"],
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
        ssl_context=ssl_context,
    )


@contextmanager
def db():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _linhas_para_dicts(cur):
    if cur.description is None:
        return []
    colunas = [d[0] for d in cur.description]
    return [dict(zip(colunas, linha)) for linha in cur.fetchall()]


def _linha_para_dict(cur, linha):
    if linha is None or cur.description is None:
        return None
    colunas = [d[0] for d in cur.description]
    return dict(zip(colunas, linha))


def query(sql, params=None):
    """Retorna lista de dicts."""
    with db() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        return _linhas_para_dicts(cur)


def query_one(sql, params=None):
    """Retorna dict ou None."""
    with db() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        return _linha_para_dict(cur, cur.fetchone())


def execute(sql, params=None):
    """Executa e retorna a primeira linha (útil para RETURNING id)."""
    with db() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        try:
            return _linha_para_dict(cur, cur.fetchone())
        except Exception:
            return None


def executemany_insert(sql, seq_params):
    """Executa o mesmo INSERT várias vezes (usado no parcelamento de cartão)."""
    with db() as conn:
        cur = conn.cursor()
        for params in seq_params:
            cur.execute(sql, params)


def _executar_arquivo_sql(conn, caminho):
    """
    pg8000 executa um comando por vez, então separamos o arquivo .sql
    em instruções individuais (separadas por ';') antes de rodar.
    """
    with open(caminho, encoding="utf-8") as f:
        conteudo = f.read()
    cur = conn.cursor()
    for comando in _dividir_comandos_sql(conteudo):
        cur.execute(comando)


def _dividir_comandos_sql(conteudo):
    """
    Divide um arquivo .sql em comandos individuais, separando por ';'.
    Ignora ';' que apareça dentro de comentários (--) ou de strings
    entre aspas simples, para não quebrar um comando no meio por engano.
    """
    comandos = []
    buffer = []
    em_comentario = False
    em_string = False
    i = 0
    n = len(conteudo)

    while i < n:
        ch = conteudo[i]

        if em_comentario:
            buffer.append(ch)
            if ch == "\n":
                em_comentario = False
            i += 1
            continue

        if em_string:
            buffer.append(ch)
            if ch == "'":
                em_string = False
            i += 1
            continue

        if conteudo[i:i + 2] == "--":
            em_comentario = True
            buffer.append("--")
            i += 2
            continue

        if ch == "'":
            em_string = True
            buffer.append(ch)
            i += 1
            continue

        if ch == ";":
            comandos.append("".join(buffer))
            buffer = []
            i += 1
            continue

        buffer.append(ch)
        i += 1

    if "".join(buffer).strip():
        comandos.append("".join(buffer))

    return [c.strip() for c in comandos if c.strip()]


def init_db():
    """Executa schema.sql e seed.sql na inicialização do app."""
    base = os.path.dirname(os.path.abspath(__file__))
    with db() as conn:
        _executar_arquivo_sql(conn, os.path.join(base, "schema.sql"))
    try:
        with db() as conn:
            _executar_arquivo_sql(conn, os.path.join(base, "seed.sql"))
    except Exception as e:
        print(f"[DB] Seed ignorado: {e}")
