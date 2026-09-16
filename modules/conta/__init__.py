from flask import Blueprint, render_template
from flask_login import current_user, login_required

import db

bp = Blueprint("conta", __name__)


@bp.route("/")
@login_required
def index():
    conta = db.query_one(
        "SELECT * FROM contas WHERE id=%s", (current_user.conta_id,)
    )
    membros = db.query(
        """SELECT nome, email FROM usuarios
           WHERE conta_id=%s AND D_E_L_E_T=0 ORDER BY nome""",
        (current_user.conta_id,),
    )
    return render_template("conta/index.html", conta=conta, membros=membros)
