from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

import db

bp = Blueprint("categorias", __name__)


@bp.route("/")
@login_required
def index():
    categorias = db.query(
        """SELECT c.*, COALESCE(SUM(d.valor),0) AS total_gasto
           FROM categorias c
           LEFT JOIN despesas d ON d.categoria_id=c.id AND d.D_E_L_E_T=0
           WHERE c.conta_id=%s AND c.D_E_L_E_T=0
           GROUP BY c.id
           ORDER BY c.nome""",
        (current_user.conta_id,),
    )
    return render_template("categorias/index.html", categorias=categorias)


@bp.route("/salvar", methods=["POST"])
@login_required
def salvar():
    d = request.form
    cat_id = d.get("id")
    nome = d.get("nome", "").strip()
    cor = d.get("cor") or "#64748b"

    if not nome:
        flash("Informe o nome da categoria.", "danger")
        return redirect(url_for("categorias.index"))

    if cat_id:
        db.execute(
            """UPDATE categorias SET nome=%s, cor=%s
               WHERE id=%s AND conta_id=%s""",
            (nome, cor, cat_id, current_user.conta_id),
        )
        flash("Categoria atualizada.", "success")
    else:
        db.execute(
            "INSERT INTO categorias (conta_id, usuario_id, nome, cor) VALUES (%s,%s,%s,%s)",
            (current_user.conta_id, current_user.id, nome, cor),
        )
        flash("Categoria criada.", "success")
    return redirect(url_for("categorias.index"))


@bp.route("/excluir/<int:cat_id>")
@login_required
def excluir(cat_id):
    db.execute(
        "UPDATE categorias SET D_E_L_E_T=1 WHERE id=%s AND conta_id=%s",
        (cat_id, current_user.conta_id),
    )
    flash("Categoria removida.", "success")
    return redirect(url_for("categorias.index"))
