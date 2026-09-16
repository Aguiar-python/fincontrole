import uuid
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

import db

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

FORMAS_PAGAMENTO = {
    "cartao": "Cartão de crédito",
    "debito": "Cartão de débito",
    "pix": "Pix",
    "dinheiro": "Dinheiro",
    "boleto": "Boleto",
}


def mes_str(d: date) -> str:
    return d.strftime("%Y-%m")


def mes_add(mes: str, n: int) -> str:
    ano, mm = map(int, mes.split("-"))
    d = date(ano, mm, 1) + relativedelta(months=n)
    return mes_str(d)


def mes_label(mes: str) -> str:
    ano, mm = map(int, mes.split("-"))
    return f"{MESES_PT[mm - 1]} de {ano}"


def mes_atual() -> str:
    return mes_str(date.today())


def calcular_mes_fatura_inicial(data_compra: date, dia_fechamento: int) -> str:
    """
    Se a compra ocorreu depois do fechamento do cartão, ela cai na fatura
    do mês seguinte. Caso contrário, cai na fatura do mês corrente.
    """
    base = mes_str(data_compra)
    if data_compra.day > dia_fechamento:
        return mes_add(base, 1)
    return base


def criar_despesa_avulsa(conta_id, usuario_id, descricao, valor, data_compra,
                          categoria_id, forma_pagamento, cartao_id=None,
                          total_parcelas=1):
    """
    Cria uma despesa visível para toda a conta (todos os usuários dela).
    usuario_id registra apenas quem lançou, pra auditoria.
    Se for no cartão e parcelada, gera uma linha por parcela, cada uma com
    o mes_fatura correto (indo empurrando fatura a fatura).
    """
    if isinstance(data_compra, str):
        data_compra = datetime.strptime(data_compra, "%Y-%m-%d").date()

    total_parcelas = max(1, int(total_parcelas or 1))

    if forma_pagamento == "cartao" and cartao_id:
        cartao = db.query_one(
            "SELECT * FROM cartoes WHERE id=%s AND conta_id=%s AND D_E_L_E_T=0",
            (cartao_id, conta_id),
        )
        if not cartao:
            raise ValueError("Cartão não encontrado.")
        mes_base = calcular_mes_fatura_inicial(data_compra, cartao["dia_fechamento"])
        valor_parcela = round(float(valor) / total_parcelas, 2)
        grupo = str(uuid.uuid4())[:8] if total_parcelas > 1 else None

        # ajusta a última parcela para não perder centavos no arredondamento
        soma_parcial = round(valor_parcela * (total_parcelas - 1), 2)
        valor_ultima = round(float(valor) - soma_parcial, 2)

        for i in range(1, total_parcelas + 1):
            valor_atual = valor_ultima if i == total_parcelas else valor_parcela
            mes_fatura = mes_add(mes_base, i - 1)
            db.execute(
                """INSERT INTO despesas
                   (conta_id, usuario_id, descricao, valor, data_compra, categoria_id,
                    forma_pagamento, cartao_id, parcela_atual, total_parcelas,
                    grupo_parcelamento, mes_fatura)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (conta_id, usuario_id, descricao, valor_atual, data_compra, categoria_id,
                 forma_pagamento, cartao_id, i, total_parcelas, grupo, mes_fatura),
            )
    else:
        mes_fatura = mes_str(data_compra)
        db.execute(
            """INSERT INTO despesas
               (conta_id, usuario_id, descricao, valor, data_compra, categoria_id,
                forma_pagamento, cartao_id, parcela_atual, total_parcelas, mes_fatura)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,1,%s)""",
            (conta_id, usuario_id, descricao, valor, data_compra, categoria_id,
             forma_pagamento, cartao_id, mes_fatura),
        )


def garantir_despesas_fixas_do_mes(conta_id, mes):
    """
    Para cada despesa fixa ativa da conta, garante que exista uma instância
    lançada em `despesas` para o mês informado. Chamado sempre que alguém
    visualiza o dashboard ou a lista de despesas de um mês.
    """
    fixas = db.query(
        "SELECT * FROM despesas_fixas WHERE conta_id=%s AND ativa=1 AND D_E_L_E_T=0",
        (conta_id,),
    )
    ano, mm = map(int, mes.split("-"))
    for fixa in fixas:
        ja_existe = db.query_one(
            """SELECT id FROM despesas
               WHERE origem_fixa_id=%s AND mes_fatura=%s AND D_E_L_E_T=0""",
            (fixa["id"], mes),
        )
        if ja_existe:
            continue
        dia = min(fixa["dia_vencimento"], 28)
        data_lancamento = date(ano, mm, dia)
        db.execute(
            """INSERT INTO despesas
               (conta_id, usuario_id, descricao, valor, data_compra, categoria_id,
                forma_pagamento, cartao_id, parcela_atual, total_parcelas,
                mes_fatura, origem_fixa_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,1,%s,%s)""",
            (conta_id, fixa["usuario_id"], fixa["descricao"], fixa["valor"], data_lancamento,
             fixa["categoria_id"], fixa["forma_pagamento"], fixa["cartao_id"],
             mes, fixa["id"]),
        )
