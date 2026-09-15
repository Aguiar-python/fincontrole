from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

import db
from helpers import (
    criar_despesa_avulsa,
    garantir_despesas_fixas_do_mes,
    mes_add,
    mes_atual,
    mes_label,
)

bp = Blueprint("despesas", __name__)


@bp.route("/")
@login_required
def index():
    mes = request.args.get("mes", mes_atual())
    garantir_despesas_fixas_do_mes(current_user.id, mes)

    lancamentos = db.query(
        """SELECT d.*, c.nome AS categoria_nome, c.cor AS categoria_cor,
                  ct.nome AS cartao_nome
           FROM despesas d
           LEFT JOIN categorias c ON c.id=d.categoria_id
           LEFT JOIN cartoes ct ON ct.id=d.cartao_id
           WHERE d.usuario_id=%s AND d.mes_fatura=%s AND d.D_E_L_E_T=0
           ORDER BY d.data_compra DESC, d.id DESC""",
        (current_user.id, mes),
    )
    categorias = db.query(
        "SELECT * FROM categorias WHERE usuario_id=%s AND D_E_L_E_T=0 ORDER BY nome",
        (current_user.id,),
    )
    cartoes = db.query(
        "SELECT * FROM cartoes WHERE usuario_id=%s AND D_E_L_E_T=0 ORDER BY nome",
        (current_user.id,),
    )
    total = sum(float(item["valor"]) for item in lancamentos)

    return render_template(
        "despesas/index.html",
        lancamentos=lancamentos,
        categorias=categorias,
        cartoes=cartoes,
        total=total,
        mes=mes,
        mes_label=mes_label(mes),
        mes_anterior=mes_add(mes, -1),
        mes_seguinte=mes_add(mes, 1),
    )


@bp.route("/salvar", methods=["POST"])
@login_required
def salvar():
    d = request.form
    try:
        criar_despesa_avulsa(
            usuario_id=current_user.id,
            descricao=d.get("descricao", "").strip(),
            valor=float(d.get("valor", "0").replace(",", ".")),
            data_compra=d.get("data_compra"),
            categoria_id=d.get("categoria_id") or None,
            forma_pagamento=d.get("forma_pagamento", "debito"),
            cartao_id=d.get("cartao_id") or None,
            total_parcelas=d.get("total_parcelas") or 1,
        )
        flash("Despesa lançada com sucesso.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Não foi possível salvar a despesa. Confira os dados informados.", "danger")

    mes_ref = (d.get("data_compra") or "")[:7] or mes_atual()
    return redirect(url_for("despesas.index", mes=mes_ref))


@bp.route("/excluir/<int:despesa_id>")
@login_required
def excluir(despesa_id):
    despesa = db.query_one(
        "SELECT * FROM despesas WHERE id=%s AND usuario_id=%s", (despesa_id, current_user.id)
    )
    if despesa and despesa["grupo_parcelamento"]:
        db.execute(
            """UPDATE despesas SET D_E_L_E_T=1
               WHERE grupo_parcelamento=%s AND usuario_id=%s""",
            (despesa["grupo_parcelamento"], current_user.id),
        )
        flash("Compra parcelada removida (todas as parcelas).", "success")
    else:
        db.execute(
            "UPDATE despesas SET D_E_L_E_T=1 WHERE id=%s AND usuario_id=%s",
            (despesa_id, current_user.id),
        )
        flash("Despesa removida.", "success")

    mes_ref = request.args.get("mes", mes_atual())
    return redirect(url_for("despesas.index", mes=mes_ref))
