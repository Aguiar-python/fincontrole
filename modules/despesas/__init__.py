from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

import db
from helpers import (
    FORMAS_PAGAMENTO,
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
    categoria_id = request.args.get("categoria_id") or ""
    forma_pagamento = request.args.get("forma_pagamento") or ""
    data_inicio = request.args.get("data_inicio") or ""
    data_fim = request.args.get("data_fim") or ""

    usa_periodo_customizado = bool(data_inicio and data_fim)

    garantir_despesas_fixas_do_mes(current_user.conta_id, mes)

    condicoes = ["d.conta_id=%s", "d.D_E_L_E_T=0"]
    params = [current_user.conta_id]

    if usa_periodo_customizado:
        condicoes.append("d.data_compra BETWEEN %s AND %s")
        params += [data_inicio, data_fim]
    else:
        condicoes.append("d.mes_fatura=%s")
        params.append(mes)

    if categoria_id:
        condicoes.append("d.categoria_id=%s")
        params.append(categoria_id)
    if forma_pagamento:
        condicoes.append("d.forma_pagamento=%s")
        params.append(forma_pagamento)

    where_sql = " AND ".join(condicoes)
    lancamentos = db.query(
        f"""SELECT d.*, c.nome AS categoria_nome, c.cor AS categoria_cor,
                   ct.nome AS cartao_nome
            FROM despesas d
            LEFT JOIN categorias c ON c.id=d.categoria_id
            LEFT JOIN cartoes ct ON ct.id=d.cartao_id
            WHERE {where_sql}
            ORDER BY d.data_compra DESC, d.id DESC""",
        tuple(params),
    )
    categorias = db.query(
        "SELECT * FROM categorias WHERE conta_id=%s AND D_E_L_E_T=0 ORDER BY nome",
        (current_user.conta_id,),
    )
    cartoes = db.query(
        "SELECT * FROM cartoes WHERE conta_id=%s AND D_E_L_E_T=0 ORDER BY nome",
        (current_user.conta_id,),
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
        categoria_id=categoria_id,
        forma_pagamento=forma_pagamento,
        data_inicio=data_inicio,
        data_fim=data_fim,
        usa_periodo_customizado=usa_periodo_customizado,
        formas_pagamento=FORMAS_PAGAMENTO,
    )


@bp.route("/salvar", methods=["POST"])
@login_required
def salvar():
    d = request.form
    try:
        criar_despesa_avulsa(
            conta_id=current_user.conta_id,
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
        "SELECT * FROM despesas WHERE id=%s AND conta_id=%s",
        (despesa_id, current_user.conta_id),
    )
    if despesa and despesa["grupo_parcelamento"]:
        db.execute(
            """UPDATE despesas SET D_E_L_E_T=1
               WHERE grupo_parcelamento=%s AND conta_id=%s""",
            (despesa["grupo_parcelamento"], current_user.conta_id),
        )
        flash("Compra parcelada removida (todas as parcelas).", "success")
    else:
        db.execute(
            "UPDATE despesas SET D_E_L_E_T=1 WHERE id=%s AND conta_id=%s",
            (despesa_id, current_user.conta_id),
        )
        flash("Despesa removida.", "success")

    mes_ref = request.args.get("mes", mes_atual())
    return redirect(url_for("despesas.index", mes=mes_ref))
