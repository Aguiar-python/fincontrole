from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

import db

bp = Blueprint("fixas", __name__)


@bp.route("/")
@login_required
def index():
    fixas = db.query(
        """SELECT f.*, c.nome AS categoria_nome, c.cor AS categoria_cor,
                  ct.nome AS cartao_nome
           FROM despesas_fixas f
           LEFT JOIN categorias c ON c.id=f.categoria_id
           LEFT JOIN cartoes ct ON ct.id=f.cartao_id
           WHERE f.usuario_id=%s AND f.D_E_L_E_T=0
           ORDER BY f.dia_vencimento""",
        (current_user.id,),
    )
    categorias = db.query(
        "SELECT * FROM categorias WHERE usuario_id=%s AND D_E_L_E_T=0 ORDER BY nome",
        (current_user.id,),
    )
    cartoes = db.query(
        "SELECT * FROM cartoes WHERE usuario_id=%s AND D_E_L_E_T=0 ORDER BY nome",
        (current_user.id,),
    )
    total_mensal = sum(float(f["valor"]) for f in fixas if f["ativa"])

    return render_template(
        "fixas/index.html",
        fixas=fixas,
        categorias=categorias,
        cartoes=cartoes,
        total_mensal=total_mensal,
    )


@bp.route("/salvar", methods=["POST"])
@login_required
def salvar():
    d = request.form
    fixa_id = d.get("id")
    descricao = d.get("descricao", "").strip()
    try:
        valor = float(d.get("valor", "0").replace(",", "."))
        dia_vencimento = int(d.get("dia_vencimento"))
    except (TypeError, ValueError):
        flash("Valor ou dia de vencimento inválidos.", "danger")
        return redirect(url_for("fixas.index"))

    categoria_id = d.get("categoria_id") or None
    forma_pagamento = d.get("forma_pagamento", "debito")
    cartao_id = d.get("cartao_id") or None

    if not descricao:
        flash("Informe a descrição da despesa fixa.", "danger")
        return redirect(url_for("fixas.index"))

    if fixa_id:
        db.execute(
            """UPDATE despesas_fixas SET descricao=%s, valor=%s, dia_vencimento=%s,
               categoria_id=%s, forma_pagamento=%s, cartao_id=%s, datestamp_update=NOW()
               WHERE id=%s AND usuario_id=%s""",
            (descricao, valor, dia_vencimento, categoria_id, forma_pagamento,
             cartao_id, fixa_id, current_user.id),
        )
        flash("Despesa fixa atualizada.", "success")
    else:
        db.execute(
            """INSERT INTO despesas_fixas
               (usuario_id, descricao, valor, dia_vencimento, categoria_id,
                forma_pagamento, cartao_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (current_user.id, descricao, valor, dia_vencimento, categoria_id,
             forma_pagamento, cartao_id),
        )
        flash("Despesa fixa criada. Ela será lançada automaticamente todo mês.", "success")
    return redirect(url_for("fixas.index"))


@bp.route("/alternar/<int:fixa_id>")
@login_required
def alternar(fixa_id):
    fixa = db.query_one(
        "SELECT ativa FROM despesas_fixas WHERE id=%s AND usuario_id=%s",
        (fixa_id, current_user.id),
    )
    if fixa:
        nova_situacao = 0 if fixa["ativa"] else 1
        db.execute(
            "UPDATE despesas_fixas SET ativa=%s WHERE id=%s AND usuario_id=%s",
            (nova_situacao, fixa_id, current_user.id),
        )
    return redirect(url_for("fixas.index"))


@bp.route("/excluir/<int:fixa_id>")
@login_required
def excluir(fixa_id):
    db.execute(
        "UPDATE despesas_fixas SET D_E_L_E_T=1 WHERE id=%s AND usuario_id=%s",
        (fixa_id, current_user.id),
    )
    flash("Despesa fixa removida.", "success")
    return redirect(url_for("fixas.index"))
