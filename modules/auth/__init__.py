from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_bcrypt import Bcrypt
from flask_login import current_user, login_required, login_user, logout_user

import db
from auth import Usuario, criar_categorias_padrao

bp = Blueprint("auth", __name__)
bcrypt = Bcrypt()


def init_bcrypt(app):
    bcrypt.init_app(app)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        usuario = Usuario.buscar_por_email(email)
        if usuario and bcrypt.check_password_hash(usuario.senha_hash, senha):
            login_user(usuario)
            return redirect(url_for("dashboard.index"))
        flash("E-mail ou senha inválidos.", "danger")

    return render_template("auth/login.html")


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar_senha", "")

        if not nome or not email or not senha:
            flash("Preencha todos os campos.", "danger")
        elif senha != confirmar:
            flash("As senhas não conferem.", "danger")
        elif len(senha) < 6:
            flash("A senha precisa ter pelo menos 6 caracteres.", "danger")
        elif Usuario.buscar_por_email(email):
            flash("Já existe uma conta com este e-mail.", "danger")
        else:
            senha_hash = bcrypt.generate_password_hash(senha).decode("utf-8")
            novo = db.execute(
                """INSERT INTO usuarios (nome, email, senha_hash)
                   VALUES (%s,%s,%s) RETURNING id""",
                (nome, email, senha_hash),
            )
            criar_categorias_padrao(novo["id"])
            flash("Conta criada com sucesso! Faça login para continuar.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/registro.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
