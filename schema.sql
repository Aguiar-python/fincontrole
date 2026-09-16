-- =========================================================
-- Controle Financeiro: Cartões de Crédito + Despesas Mensais
-- =========================================================

-- Uma "conta" é o espaço compartilhado (ex.: um casal usando o mesmo painel).
-- Cada usuário pertence a uma conta, e todos os dados (cartões, despesas etc.)
-- são visíveis para todos os usuários da mesma conta.
CREATE TABLE IF NOT EXISTS contas (
    id                SERIAL PRIMARY KEY,
    nome              VARCHAR(200) NOT NULL,
    codigo_convite    VARCHAR(10) NOT NULL UNIQUE,
    D_E_L_E_T         SMALLINT DEFAULT 0,
    datestamp_insert  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usuarios (
    id                SERIAL PRIMARY KEY,
    conta_id          INTEGER REFERENCES contas(id),
    nome              VARCHAR(200) NOT NULL,
    email             VARCHAR(200) NOT NULL UNIQUE,
    senha_hash        VARCHAR(300) NOT NULL,
    ativo             SMALLINT DEFAULT 1,
    D_E_L_E_T         SMALLINT DEFAULT 0,
    datestamp_insert  TIMESTAMP DEFAULT NOW(),
    datestamp_update  TIMESTAMP
);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS conta_id INTEGER REFERENCES contas(id);

CREATE TABLE IF NOT EXISTS cartoes (
    id                SERIAL PRIMARY KEY,
    conta_id          INTEGER REFERENCES contas(id),
    usuario_id        INTEGER NOT NULL REFERENCES usuarios(id),
    nome              VARCHAR(100) NOT NULL,
    bandeira          VARCHAR(50),
    limite            NUMERIC(12,2) DEFAULT 0,
    dia_fechamento    INTEGER NOT NULL CHECK (dia_fechamento BETWEEN 1 AND 28),
    dia_vencimento    INTEGER NOT NULL CHECK (dia_vencimento BETWEEN 1 AND 28),
    cor               VARCHAR(20) DEFAULT '#6366f1',
    D_E_L_E_T         SMALLINT DEFAULT 0,
    datestamp_insert  TIMESTAMP DEFAULT NOW(),
    datestamp_update  TIMESTAMP
);
ALTER TABLE cartoes ADD COLUMN IF NOT EXISTS conta_id INTEGER REFERENCES contas(id);

CREATE TABLE IF NOT EXISTS categorias (
    id                SERIAL PRIMARY KEY,
    conta_id          INTEGER REFERENCES contas(id),
    usuario_id        INTEGER NOT NULL REFERENCES usuarios(id),
    nome              VARCHAR(100) NOT NULL,
    cor               VARCHAR(20) DEFAULT '#64748b',
    icone             VARCHAR(50) DEFAULT 'tag',
    D_E_L_E_T         SMALLINT DEFAULT 0,
    datestamp_insert  TIMESTAMP DEFAULT NOW()
);
ALTER TABLE categorias ADD COLUMN IF NOT EXISTS conta_id INTEGER REFERENCES contas(id);

-- Modelos de despesas fixas (assinaturas, aluguel, etc.) que se repetem todo mês
CREATE TABLE IF NOT EXISTS despesas_fixas (
    id                SERIAL PRIMARY KEY,
    conta_id          INTEGER REFERENCES contas(id),
    usuario_id        INTEGER NOT NULL REFERENCES usuarios(id),
    descricao         VARCHAR(200) NOT NULL,
    valor             NUMERIC(12,2) NOT NULL,
    dia_vencimento    INTEGER NOT NULL CHECK (dia_vencimento BETWEEN 1 AND 28),
    categoria_id      INTEGER REFERENCES categorias(id),
    forma_pagamento   VARCHAR(30) NOT NULL DEFAULT 'debito',
    cartao_id         INTEGER REFERENCES cartoes(id),
    ativa             SMALLINT DEFAULT 1,
    D_E_L_E_T         SMALLINT DEFAULT 0,
    datestamp_insert  TIMESTAMP DEFAULT NOW(),
    datestamp_update  TIMESTAMP
);
ALTER TABLE despesas_fixas ADD COLUMN IF NOT EXISTS conta_id INTEGER REFERENCES contas(id);

-- Lançamentos reais (compras avulsas, parcelas de cartão e instâncias geradas das despesas fixas)
CREATE TABLE IF NOT EXISTS despesas (
    id                  SERIAL PRIMARY KEY,
    conta_id            INTEGER REFERENCES contas(id),
    usuario_id          INTEGER NOT NULL REFERENCES usuarios(id),
    descricao           VARCHAR(200) NOT NULL,
    valor               NUMERIC(12,2) NOT NULL,
    data_compra         DATE NOT NULL,
    categoria_id        INTEGER REFERENCES categorias(id),
    forma_pagamento     VARCHAR(30) NOT NULL DEFAULT 'debito', -- cartao, debito, pix, dinheiro, boleto
    cartao_id           INTEGER REFERENCES cartoes(id),
    parcela_atual       INTEGER DEFAULT 1,
    total_parcelas      INTEGER DEFAULT 1,
    grupo_parcelamento  VARCHAR(40),
    mes_fatura          VARCHAR(7) NOT NULL, -- 'YYYY-MM'
    origem_fixa_id      INTEGER REFERENCES despesas_fixas(id),
    D_E_L_E_T           SMALLINT DEFAULT 0,
    datestamp_insert    TIMESTAMP DEFAULT NOW(),
    datestamp_update    TIMESTAMP
);
ALTER TABLE despesas ADD COLUMN IF NOT EXISTS conta_id INTEGER REFERENCES contas(id);

CREATE INDEX IF NOT EXISTS idx_despesas_conta_mes ON despesas (conta_id, mes_fatura) WHERE D_E_L_E_T = 0;
CREATE INDEX IF NOT EXISTS idx_despesas_cartao_mes ON despesas (cartao_id, mes_fatura) WHERE D_E_L_E_T = 0;
CREATE INDEX IF NOT EXISTS idx_fixas_conta ON despesas_fixas (conta_id) WHERE D_E_L_E_T = 0;
CREATE INDEX IF NOT EXISTS idx_cartoes_conta ON cartoes (conta_id) WHERE D_E_L_E_T = 0;
CREATE INDEX IF NOT EXISTS idx_categorias_conta ON categorias (conta_id) WHERE D_E_L_E_T = 0;
