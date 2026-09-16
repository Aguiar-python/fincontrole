import db
from auth import criar_conta


def migrar_usuarios_sem_conta():
    """
    Roda toda vez que o app inicia. Para cada usuário que ainda não tem
    conta_id preenchido (bancos criados antes do recurso de conta
    compartilhada), cria uma conta pessoal pra ele e reatribui os dados
    que ele já tinha cadastrado (cartões, categorias, despesas fixas,
    despesas). É seguro rodar repetidas vezes: usuários que já têm
    conta_id são ignorados.
    """
    usuarios_sem_conta = db.query(
        "SELECT id, nome FROM usuarios WHERE conta_id IS NULL AND D_E_L_E_T=0"
    )

    for usuario in usuarios_sem_conta:
        conta_id, _codigo = criar_conta(f"Conta de {usuario['nome']}")

        db.execute(
            "UPDATE usuarios SET conta_id=%s WHERE id=%s",
            (conta_id, usuario["id"]),
        )
        for tabela in ("cartoes", "categorias", "despesas_fixas", "despesas"):
            db.execute(
                f"""UPDATE {tabela} SET conta_id=%s
                    WHERE usuario_id=%s AND conta_id IS NULL""",
                (conta_id, usuario["id"]),
            )
