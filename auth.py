import secrets
import string

from flask_login import UserMixin

import db


class Usuario(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.conta_id = row["conta_id"]
        self.nome = row["nome"]
        self.email = row["email"]
        self.senha_hash = row["senha_hash"]

    @staticmethod
    def buscar_por_id(user_id):
        row = db.query_one(
            "SELECT * FROM usuarios WHERE id=%s AND D_E_L_E_T=0 AND ativo=1",
            (user_id,),
        )
        return Usuario(row) if row else None

    @staticmethod
    def buscar_por_email(email):
        row = db.query_one(
            "SELECT * FROM usuarios WHERE email=%s AND D_E_L_E_T=0 AND ativo=1",
            (email,),
        )
        return Usuario(row) if row else None


CATEGORIAS_PADRAO = [
    ("Alimentação", "#f97316", "utensils"),
    ("Transporte", "#3b82f6", "car"),
    ("Moradia", "#8b5cf6", "home"),
    ("Saúde", "#ef4444", "heart-pulse"),
    ("Educação", "#06b6d4", "book"),
    ("Lazer", "#ec4899", "gamepad-2"),
    ("Compras", "#eab308", "shopping-bag"),
    ("Assinaturas", "#6366f1", "repeat"),
    ("Outros", "#64748b", "tag"),
]

# Caracteres usados no código de convite: sem 0/O/1/I pra evitar confusão
_ALFABETO_CONVITE = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def gerar_codigo_convite():
    return "".join(secrets.choice(_ALFABETO_CONVITE) for _ in range(6))


def criar_conta(nome_conta):
    """Cria uma nova conta compartilhada e retorna (id, codigo_convite)."""
    for _ in range(5):
        codigo = gerar_codigo_convite()
        ja_existe = db.query_one(
            "SELECT id FROM contas WHERE codigo_convite=%s", (codigo,)
        )
        if not ja_existe:
            nova = db.execute(
                "INSERT INTO contas (nome, codigo_convite) VALUES (%s,%s) RETURNING id",
                (nome_conta, codigo),
            )
            return nova["id"], codigo
    raise RuntimeError("Não foi possível gerar um código de convite único.")


def buscar_conta_por_codigo(codigo):
    return db.query_one(
        "SELECT * FROM contas WHERE codigo_convite=%s AND D_E_L_E_T=0",
        ((codigo or "").strip().upper(),),
    )


def criar_categorias_padrao(conta_id, usuario_id):
    for nome, cor, icone in CATEGORIAS_PADRAO:
        db.execute(
            """INSERT INTO categorias (conta_id, usuario_id, nome, cor, icone)
               VALUES (%s,%s,%s,%s,%s)""",
            (conta_id, usuario_id, nome, cor, icone),
        )
