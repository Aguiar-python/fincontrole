from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_bcrypt import Bcrypt
from flask_login import current_user, login_required, login_user, logout_user

import db
from auth import (
    Usuario,
    buscar_conta_por_codigo,
    criar_categorias_padrao,
    criar_conta,
)

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
        modo = request.form.get("modo", "criar")  # "criar" ou "entrar"
        codigo_convite = request.form.get("codigo_convite", "").strip().upper()

        conta = None
        if modo == "entrar":
            conta = buscar_conta_por_codigo(codigo_convite)

        if not nome or not email or not senha:
            flash("Preencha todos os campos.", "danger")
        elif senha != confirmar:
            flash("As senhas não conferem.", "danger")
        elif len(senha) < 6:
            flash("A senha precisa ter pelo menos 6 caracteres.", "danger")
        elif Usuario.buscar_por_email(email):
            flash("Já existe uma conta com este e-mail.", "danger")
        elif modo == "entrar" and not conta:
            flash("Código de convite inválido. Confira com quem te enviou.", "danger")
        else:
            criar_categorias = False
            if modo == "entrar":
                conta_id = conta["id"]
            else:
                conta_id, codigo_gerado = criar_conta(f"Conta de {nome}")
                criar_categorias = True

            senha_hash = bcrypt.generate_password_hash(senha).decode("utf-8")
            novo = db.execute(
                """INSERT INTO usuarios (conta_id, nome, email, senha_hash)
                   VALUES (%s,%s,%s,%s) RETURNING id""",
                (conta_id, nome, email, senha_hash),
            )
            if criar_categorias:
                criar_categorias_padrao(conta_id, novo["id"])

            if modo == "entrar":
                flash(
                    f"Conta criada! Você entrou na mesma conta de {conta['nome']}. "
                    "Faça login para continuar.",
                    "success",
                )
                return redirect(url_for("auth.login"))
            else:
                return redirect(url_for("auth.conta_criada", codigo=codigo_gerado))

    return render_template("auth/registro.html")


@bp.route("/conta-criada/<codigo>")
def conta_criada(codigo):
    return render_template("auth/conta_criada.html", codigo=codigo)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
