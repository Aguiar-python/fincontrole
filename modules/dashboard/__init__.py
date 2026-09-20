from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

import db
from helpers import garantir_despesas_fixas_do_mes, mes_add, mes_atual, mes_label

bp = Blueprint("dashboard", __name__)

# Regime de caixa: quanto efetivamente saiu do bolso naquele mês (parcelas
# de cartão contam na fatura em que caem). Regime de competência: quanto
# você se comprometeu a gastar naquele mês (uma compra parcelada conta
# inteira no mês da compra).
CAMPO_MES_POR_REGIME = {
    "caixa": "mes_fatura",
    "competencia": "mes_competencia",
}


@bp.route("/")
@login_required
def index():
    mes = request.args.get("mes", mes_atual())
    regime = request.args.get("regime", "caixa")
    if regime not in CAMPO_MES_POR_REGIME:
        regime = "caixa"
    campo_mes = CAMPO_MES_POR_REGIME[regime]

    garantir_despesas_fixas_do_mes(current_user.conta_id, mes)

    total_despesas = db.query_one(
        f"""SELECT COALESCE(SUM(valor),0) AS total FROM despesas
            WHERE conta_id=%s AND {campo_mes}=%s AND D_E_L_E_T=0""",
        (current_user.conta_id, mes),
    )["total"]

    total_receitas = db.query_one(
        """SELECT COALESCE(SUM(valor_liquido),0) AS total FROM receitas
           WHERE conta_id=%s AND mes_referencia=%s AND D_E_L_E_T=0""",
        (current_user.conta_id, mes),
    )["total"]

    saldo = float(total_receitas) - float(total_despesas)

    por_categoria = db.query(
        f"""SELECT c.nome, c.cor, COALESCE(SUM(d.valor),0) AS total
            FROM categorias c
            LEFT JOIN despesas d ON d.categoria_id=c.id AND d.{campo_mes}=%s
                                     AND d.D_E_L_E_T=0 AND d.conta_id=%s
            WHERE c.conta_id=%s AND c.D_E_L_E_T=0
            GROUP BY c.id, c.nome, c.cor
            HAVING COALESCE(SUM(d.valor),0) > 0
            ORDER BY total DESC""",
        (mes, current_user.conta_id, current_user.conta_id),
    )

    faturas_cartoes = db.query(
        """SELECT ct.id, ct.nome, ct.cor, ct.limite, ct.dia_vencimento,
                  COALESCE(SUM(d.valor),0) AS total_fatura
           FROM cartoes ct
           LEFT JOIN despesas d ON d.cartao_id=ct.id AND d.mes_fatura=%s
                                    AND d.D_E_L_E_T=0
           WHERE ct.conta_id=%s AND ct.D_E_L_E_T=0
           GROUP BY ct.id, ct.nome, ct.cor, ct.limite, ct.dia_vencimento
           ORDER BY ct.nome""",
        (mes, current_user.conta_id),
    )

    ultimos_lancamentos = db.query(
        f"""SELECT d.*, c.nome AS categoria_nome, c.cor AS categoria_cor,
                   ct.nome AS cartao_nome
            FROM despesas d
            LEFT JOIN categorias c ON c.id=d.categoria_id
            LEFT JOIN cartoes ct ON ct.id=d.cartao_id
            WHERE d.conta_id=%s AND d.{campo_mes}=%s AND d.D_E_L_E_T=0
            ORDER BY d.data_compra DESC, d.id DESC
            LIMIT 8""",
        (current_user.conta_id, mes),
    )

    return render_template(
        "dashboard/index.html",
        mes=mes,
        mes_label=mes_label(mes),
        mes_anterior=mes_add(mes, -1),
        mes_seguinte=mes_add(mes, 1),
        regime=regime,
        total_despesas=total_despesas,
        total_receitas=total_receitas,
        saldo=saldo,
        por_categoria=por_categoria,
        faturas_cartoes=faturas_cartoes,
        ultimos_lancamentos=ultimos_lancamentos,
    )
