from flask_login import UserMixin

import db


class Usuario(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
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


def criar_categorias_padrao(usuario_id):
    for nome, cor, icone in CATEGORIAS_PADRAO:
        db.execute(
            "INSERT INTO categorias (usuario_id, nome, cor, icone) VALUES (%s,%s,%s,%s)",
            (usuario_id, nome, cor, icone),
        )
