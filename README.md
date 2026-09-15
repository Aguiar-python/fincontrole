# FinControle — Cartões de crédito e despesas mensais

Sistema web em Flask + PostgreSQL para controlar cartões de crédito (com parcelamento
e fatura por mês) e despesas mensais (fixas e variáveis).

## O que o sistema faz

**Cartões de crédito**
- Cadastro de vários cartões com limite, bandeira, cor, dia de fechamento e vencimento
- Compras parceladas em até 24x: o sistema cria uma linha por parcela e joga cada
  uma na fatura do mês certo automaticamente
- Respeita o dia de fechamento: compra feita depois do fechamento cai na fatura do mês seguinte
- Tela de fatura por cartão e por mês, com limite disponível

**Despesas**
- Lançamento por cartão, débito, Pix, dinheiro ou boleto
- Categorias personalizadas com cor
- Navegação mês a mês
- Excluir uma compra parcelada remove todas as parcelas de uma vez

**Despesas fixas**
- Cadastra uma vez (aluguel, assinaturas, escola) e o sistema lança sozinho todo mês
- Pode pausar e reativar sem perder o histórico

**Dashboard**
- Total do mês, total em cartões e total nas demais formas de pagamento
- Gastos por categoria em barras proporcionais
- Faturas de todos os cartões e últimos lançamentos

**Multiusuário**: cada pessoa vê apenas os próprios dados (login com senha criptografada).

---

## Rodar localmente

```bash
pip install -r requirements.txt
cp .env.exemplo .env     # edite com os dados do seu PostgreSQL
python app.py
```

Acesse `http://localhost:5000`, clique em "Criar conta" e comece a usar.
As tabelas e as 9 categorias padrão são criadas automaticamente.

---

## Usar com Supabase (banco grátis na nuvem)

O Supabase é PostgreSQL de verdade, então funciona sem alterar nada no código.
Basta configurar a variável `DATABASE_URL`.

### Passo a passo

1. Crie um projeto em supabase.com (plano Free)
2. No painel do projeto, clique em **Connect** no topo
3. Escolha **Session pooler** — não use "Direct connection"
4. Copie a string e configure:

```
DATABASE_URL=postgresql://postgres.SEU_REF:SUA_SENHA@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
DB_SSLMODE=require
SECRET_KEY=uma-string-bem-longa-e-aleatoria
```

Quando `DATABASE_URL` está definida, as variáveis `DB_HOST`, `DB_NAME` etc. são ignoradas.

### Por que Session pooler e não Direct connection

A conexão direta do Supabase (`db.xxxx.supabase.co`) resolve **só em IPv6**. A maioria
das VPS e plataformas de hospedagem não tem saída IPv6, e a conexão simplesmente falha
com "connection refused" ou "no route to host". O pooler (`pooler.supabase.com`) funciona
em IPv4 e resolve isso.

Use a **porta 5432** (session mode), não a 6543 (transaction mode). O transaction mode
reaproveita conexões de forma agressiva e quebra recursos de sessão que a aplicação usa.

Repare também que no pooler o usuário vem no formato `postgres.SEU_PROJECT_REF`, com ponto —
não é só `postgres`.

### Limites do plano Free (2026)

- 500 MB de banco e 500 MB de RAM — muito mais que suficiente aqui
- 2 projetos por organização
- **O projeto pausa após 7 dias sem uso.** O primeiro acesso depois disso demora
  de 10 a 30 segundos para religar. Para uso pessoal é só um incômodo; se você
  ficar semanas sem abrir, conte com essa espera.
- **Sem backup automático.** Como são seus dados financeiros, vale rodar um
  `pg_dump` periódico por conta própria.

---

## Deploy no EasyPanel (Hostinger)

1. **Banco**: Add Service → Postgres. Anote host interno, nome do banco, usuário e senha.
2. **App**: Add Service → App → Fonte: Upload → sobe o `fincontrole.zip`
3. **Construção**: selecione Dockerfile
4. **Ambiente**: configure as variáveis:

```
DB_HOST=projeto_fincontrole_db     # host interno gerado pelo EasyPanel
DB_PORT=5432
DB_NAME=fincontrole
DB_USER=postgres
DB_PASSWORD=sua_senha
SECRET_KEY=uma-string-bem-longa-e-aleatoria
```

5. **Domínios**: aponte para a porta `5000` e ative HTTPS
6. **Implantar**

O `.env` não vai no ZIP — em produção as variáveis vêm da aba Ambiente.

### Subir nova versão

Serviço → Fonte → upload do novo ZIP. O EasyPanel reconstrói sozinho.

---

## Estrutura

```
app.py           Ponto de entrada e registro dos blueprints
db.py            Conexão PostgreSQL e helpers de query
auth.py          Modelo de usuário e categorias padrão
helpers.py       Cálculo de fatura, parcelamento e geração de despesas fixas
schema.sql       DDL (CREATE TABLE IF NOT EXISTS)
modules/         Blueprints: auth, dashboard, cartoes, despesas, fixas, categorias
templates/       Telas Jinja2
static/          CSS e JS
```

---

## Detalhe técnico: como a fatura é calculada

Cada linha na tabela `despesas` carrega um campo `mes_fatura` (formato `YYYY-MM`).
Para compras no cartão:

- Compra **até** o dia de fechamento → entra na fatura do mês corrente
- Compra **depois** do fechamento → entra na fatura do mês seguinte
- Cada parcela seguinte vai empurrando um mês por vez
- Centavos de arredondamento são somados na última parcela, para o total bater exatamente

Nenhum registro é apagado fisicamente: tudo usa `D_E_L_E_T=1` para manter auditoria.
