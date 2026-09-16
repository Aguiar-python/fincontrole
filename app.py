import os

from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_login import LoginManager

import db
from auth import Usuario
from helpers import FORMAS_PAGAMENTO, mes_atual, mes_label

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-nao-use-em-producao")

login_mgr = LoginManager(app)
login_mgr.login_view = "auth.login"
login_mgr.login_message = "Faça login para continuar."
login_mgr.login_message_category = "warning"


@login_mgr.user_loader
def load_user(user_id):
    return Usuario.buscar_por_id(user_id)


with app.app_context():
    try:
        db.init_db()
        from migracao import migrar_usuarios_sem_conta
        migrar_usuarios_sem_conta()
    except Exception as e:
        print(f"[DB] Erro ao inicializar o banco: {e}")


# Blueprints
from modules.auth import bp as bp_auth, init_bcrypt
from modules.dashboard import bp as bp_dashboard
from modules.cartoes import bp as bp_cartoes
from modules.despesas import bp as bp_despesas
from modules.categorias import bp as bp_categorias
from modules.fixas import bp as bp_fixas
from modules.conta import bp as bp_conta

init_bcrypt(app)
app.register_blueprint(bp_auth, url_prefix="/auth")
app.register_blueprint(bp_dashboard, url_prefix="/")
app.register_blueprint(bp_cartoes, url_prefix="/cartoes")
app.register_blueprint(bp_despesas, url_prefix="/despesas")
app.register_blueprint(bp_categorias, url_prefix="/categorias")
app.register_blueprint(bp_fixas, url_prefix="/fixas")
app.register_blueprint(bp_conta, url_prefix="/conta")


@app.context_processor
def injetar_globais():
    return {"FORMAS_PAGAMENTO": FORMAS_PAGAMENTO, "mes_atual_global": mes_atual()}


@app.route("/")
def raiz():
    return redirect(url_for("dashboard.index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
