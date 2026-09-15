from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

import db
from helpers import garantir_despesas_fixas_do_mes, mes_add, mes_atual, mes_label

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    mes = request.args.get("mes", mes_atual())
    garantir_despesas_fixas_do_mes(current_user.id, mes)

    total_mes = db.query_one(
        """SELECT COALESCE(SUM(valor),0) AS total FROM despesas
           WHERE usuario_id=%s AND mes_fatura=%s AND D_E_L_E_T=0""",
        (current_user.id, mes),
    )["total"]

    por_categoria = db.query(
        """SELECT c.nome, c.cor, COALESCE(SUM(d.valor),0) AS total
           FROM categorias c
           LEFT JOIN despesas d ON d.categoria_id=c.id AND d.mes_fatura=%s
                                    AND d.D_E_L_E_T=0 AND d.usuario_id=%s
           WHERE c.usuario_id=%s AND c.D_E_L_E_T=0
           GROUP BY c.id, c.nome, c.cor
           HAVING COALESCE(SUM(d.valor),0) > 0
           ORDER BY total DESC""",
        (mes, current_user.id, current_user.id),
    )

    por_forma = db.query(
        """SELECT forma_pagamento, COALESCE(SUM(valor),0) AS total
           FROM despesas
           WHERE usuario_id=%s AND mes_fatura=%s AND D_E_L_E_T=0
           GROUP BY forma_pagamento
           ORDER BY total DESC""",
        (current_user.id, mes),
    )

    faturas_cartoes = db.query(
        """SELECT ct.id, ct.nome, ct.cor, ct.limite, ct.dia_vencimento,
                  COALESCE(SUM(d.valor),0) AS total_fatura
           FROM cartoes ct
           LEFT JOIN despesas d ON d.cartao_id=ct.id AND d.mes_fatura=%s
                                    AND d.D_E_L_E_T=0
           WHERE ct.usuario_id=%s AND ct.D_E_L_E_T=0
           GROUP BY ct.id, ct.nome, ct.cor, ct.limite, ct.dia_vencimento
           ORDER BY ct.nome""",
        (mes, current_user.id),
    )

    ultimos_lancamentos = db.query(
        """SELECT d.*, c.nome AS categoria_nome, c.cor AS categoria_cor,
                  ct.nome AS cartao_nome
           FROM despesas d
           LEFT JOIN categorias c ON c.id=d.categoria_id
           LEFT JOIN cartoes ct ON ct.id=d.cartao_id
           WHERE d.usuario_id=%s AND d.mes_fatura=%s AND d.D_E_L_E_T=0
           ORDER BY d.data_compra DESC, d.id DESC
           LIMIT 8""",
        (current_user.id, mes),
    )

    return render_template(
        "dashboard/index.html",
        mes=mes,
        mes_label=mes_label(mes),
        mes_anterior=mes_add(mes, -1),
        mes_seguinte=mes_add(mes, 1),
        total_mes=total_mes,
        por_categoria=por_categoria,
        por_forma=por_forma,
        faturas_cartoes=faturas_cartoes,
        ultimos_lancamentos=ultimos_lancamentos,
    )
