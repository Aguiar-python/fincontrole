from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

import db
from helpers import mes_add, mes_atual, mes_label

bp = Blueprint("receitas", __name__)


def _num(form, campo):
    bruto = (form.get(campo, "") or "0").replace(",", ".").strip()
    return float(bruto) if bruto else 0.0


@bp.route("/")
@login_required
def index():
    mes = request.args.get("mes", mes_atual())

    receitas = db.query(
        """SELECT r.*, u.nome AS usuario_nome
           FROM receitas r
           LEFT JOIN usuarios u ON u.id = r.usuario_id
           WHERE r.conta_id=%s AND r.mes_referencia=%s AND r.D_E_L_E_T=0
           ORDER BY r.data_recebimento DESC, r.id DESC""",
        (current_user.conta_id, mes),
    )
    total_liquido = sum(float(r["valor_liquido"]) for r in receitas)
    total_bruto = sum(float(r["salario_bruto"]) for r in receitas)
    total_descontos = sum(
        float(r["inss"]) + float(r["irrf"]) + float(r["plano_saude"])
        + float(r["plano_odontologico"]) + float(r["vale_alimentacao"])
        + float(r["outros_descontos"])
        for r in receitas
    )

    return render_template(
        "receitas/index.html",
        receitas=receitas,
        total_liquido=total_liquido,
        total_bruto=total_bruto,
        total_descontos=total_descontos,
        mes=mes,
        mes_label=mes_label(mes),
        mes_anterior=mes_add(mes, -1),
        mes_seguinte=mes_add(mes, 1),
    )


@bp.route("/salvar", methods=["POST"])
@login_required
def salvar():
    d = request.form
    tipo = d.get("tipo", "salario")
    descricao = d.get("descricao", "").strip()
    data_recebimento = d.get("data_recebimento")

    if not descricao or not data_recebimento:
        flash("Preencha a descrição e a data de recebimento.", "danger")
        return redirect(url_for("receitas.index"))

    mes_referencia = data_recebimento[:7]

    if tipo == "salario":
        salario_bruto = _num(d, "salario_bruto")
        inss = _num(d, "inss")
        irrf = _num(d, "irrf")
        plano_saude = _num(d, "plano_saude")
        plano_odontologico = _num(d, "plano_odontologico")
        vale_alimentacao = _num(d, "vale_alimentacao")
        outros_descontos = _num(d, "outros_descontos")
        valor_liquido = round(
            salario_bruto - inss - irrf - plano_saude
            - plano_odontologico - vale_alimentacao - outros_descontos,
            2,
        )
        if valor_liquido < 0:
            flash("Os descontos somados são maiores que o salário bruto. Confira os valores.", "danger")
            return redirect(url_for("receitas.index"))
    else:
        salario_bruto = inss = irrf = plano_saude = 0.0
        plano_odontologico = vale_alimentacao = outros_descontos = 0.0
        valor_liquido = _num(d, "valor_liquido")

    db.execute(
        """INSERT INTO receitas
           (conta_id, usuario_id, tipo, descricao, data_recebimento, mes_referencia,
            salario_bruto, inss, irrf, plano_saude, plano_odontologico,
            vale_alimentacao, outros_descontos, valor_liquido)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (current_user.conta_id, current_user.id, tipo, descricao, data_recebimento,
         mes_referencia, salario_bruto, inss, irrf, plano_saude, plano_odontologico,
         vale_alimentacao, outros_descontos, valor_liquido),
    )
    flash("Receita lançada com sucesso.", "success")
    return redirect(url_for("receitas.index", mes=mes_referencia))


@bp.route("/excluir/<int:receita_id>")
@login_required
def excluir(receita_id):
    mes_ref = request.args.get("mes", mes_atual())
    db.execute(
        "UPDATE receitas SET D_E_L_E_T=1 WHERE id=%s AND conta_id=%s",
        (receita_id, current_user.conta_id),
    )
    flash("Receita removida.", "success")
    return redirect(url_for("receitas.index", mes=mes_ref))
