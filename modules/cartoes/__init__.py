from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

import db
from helpers import mes_add, mes_atual, mes_label

bp = Blueprint("cartoes", __name__)


@bp.route("/")
@login_required
def index():
    mes = mes_atual()
    cartoes = db.query(
        """SELECT ct.*, COALESCE(SUM(d.valor),0) AS fatura_atual
           FROM cartoes ct
           LEFT JOIN despesas d ON d.cartao_id=ct.id AND d.mes_fatura=%s AND d.D_E_L_E_T=0
           WHERE ct.conta_id=%s AND ct.D_E_L_E_T=0
           GROUP BY ct.id
           ORDER BY ct.nome""",
        (mes, current_user.conta_id),
    )
    return render_template("cartoes/index.html", cartoes=cartoes)


@bp.route("/salvar", methods=["POST"])
@login_required
def salvar():
    d = request.form
    cartao_id = d.get("id")
    nome = d.get("nome", "").strip()
    bandeira = d.get("bandeira", "").strip()
    limite = d.get("limite") or 0
    dia_fechamento = d.get("dia_fechamento")
    dia_vencimento = d.get("dia_vencimento")
    cor = d.get("cor") or "#6366f1"

    if not nome or not dia_fechamento or not dia_vencimento:
        flash("Preencha nome, dia de fechamento e dia de vencimento.", "danger")
        return redirect(url_for("cartoes.index"))

    if cartao_id:
        db.execute(
            """UPDATE cartoes SET nome=%s, bandeira=%s, limite=%s, dia_fechamento=%s,
               dia_vencimento=%s, cor=%s, datestamp_update=NOW()
               WHERE id=%s AND conta_id=%s""",
            (nome, bandeira, limite, dia_fechamento, dia_vencimento, cor,
             cartao_id, current_user.conta_id),
        )
        flash("Cartão atualizado.", "success")
    else:
        db.execute(
            """INSERT INTO cartoes (conta_id, usuario_id, nome, bandeira, limite,
               dia_fechamento, dia_vencimento, cor)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (current_user.conta_id, current_user.id, nome, bandeira, limite,
             dia_fechamento, dia_vencimento, cor),
        )
        flash("Cartão cadastrado.", "success")
    return redirect(url_for("cartoes.index"))


@bp.route("/excluir/<int:cartao_id>")
@login_required
def excluir(cartao_id):
    db.execute(
        "UPDATE cartoes SET D_E_L_E_T=1 WHERE id=%s AND conta_id=%s",
        (cartao_id, current_user.conta_id),
    )
    flash("Cartão removido.", "success")
    return redirect(url_for("cartoes.index"))


@bp.route("/<int:cartao_id>/fatura")
@login_required
def fatura(cartao_id):
    mes = request.args.get("mes", mes_atual())
    cartao = db.query_one(
        "SELECT * FROM cartoes WHERE id=%s AND conta_id=%s AND D_E_L_E_T=0",
        (cartao_id, current_user.conta_id),
    )
    if not cartao:
        flash("Cartão não encontrado.", "danger")
        return redirect(url_for("cartoes.index"))

    itens = db.query(
        """SELECT d.*, c.nome AS categoria_nome, c.cor AS categoria_cor
           FROM despesas d
           LEFT JOIN categorias c ON c.id=d.categoria_id
           WHERE d.cartao_id=%s AND d.mes_fatura=%s AND d.D_E_L_E_T=0
           ORDER BY d.data_compra""",
        (cartao_id, mes),
    )
    total = sum(float(item["valor"]) for item in itens)

    return render_template(
        "cartoes/fatura.html",
        cartao=cartao,
        itens=itens,
        total=total,
        mes=mes,
        mes_label=mes_label(mes),
        mes_anterior=mes_add(mes, -1),
        mes_seguinte=mes_add(mes, 1),
    )
