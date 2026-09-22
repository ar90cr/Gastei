
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from decimal import Decimal
from datetime import date
import os

BASE = os.getenv("GASTEI_DATA_DIR", "/content/gastei")
os.makedirs(BASE, exist_ok=True)

DB = os.path.join(BASE, "gastei.db")

engine = create_engine(
    "sqlite:///" + DB,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ============================================================
# BANCO
# ============================================================

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    institution = Column(String)
    account_type = Column(String, default="CHECKING")
    initial_balance = Column(Numeric(15, 2), default=0)
    is_active = Column(Boolean, default=True)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category_type = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)


class Income(Base):
    __tablename__ = "income"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, nullable=False)
    category_id = Column(Integer, nullable=False)
    description = Column(String)
    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(Date, nullable=False)
    income_type = Column(String, default="VARIABLE")
    notes = Column(String)


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, nullable=False)
    category_id = Column(Integer, nullable=False)
    description = Column(String)
    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(Date, nullable=False)
    notes = Column(String)


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    investment_type = Column(String)
    current_value = Column(Numeric(15, 2), default=0)
    quantity = Column(Numeric(20, 8), default=0)
    is_active = Column(Boolean, default=True)


Base.metadata.create_all(engine)

# ============================================================
# DADOS INICIAIS
# ============================================================

db = SessionLocal()

if db.query(Account).count() == 0:
    db.add(
        Account(
            name="Conta principal",
            institution="",
            account_type="CHECKING",
            initial_balance=0
        )
    )

if db.query(Category).count() == 0:
    categorias = [
        ("Salário", "INCOME"),
        ("Extra", "INCOME"),
        ("Alimentação", "EXPENSE"),
        ("Moradia", "EXPENSE"),
        ("Transporte", "EXPENSE"),
        ("Lazer", "EXPENSE"),
        ("Saúde", "EXPENSE"),
        ("Educação", "EXPENSE"),
        ("Outros", "EXPENSE")
    ]

    for nome, tipo in categorias:
        db.add(
            Category(
                name=nome,
                category_type=tipo
            )
        )

db.commit()
db.close()

# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(title="Gastei")


def dinheiro(valor):
    valor = Decimal(str(valor or 0))
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X")
    texto = texto.replace(".", ",")
    texto = texto.replace("X", ".")
    return "R$ " + texto


@app.get("/", response_class=HTMLResponse)
def dashboard():

    db = SessionLocal()

    contas = (
        db.query(Account)
        .filter(Account.is_active == True)
        .all()
    )

    receitas = db.query(Income).all()
    despesas = db.query(Expense).all()

    investimentos = (
        db.query(Investment)
        .filter(Investment.is_active == True)
        .all()
    )

    categorias_despesa = (
        db.query(Category)
        .filter(Category.category_type == "EXPENSE")
        .all()
    )

    saldo_inicial = sum(
        [Decimal(str(x.initial_balance or 0)) for x in contas],
        Decimal("0")
    )

    total_receitas = sum(
        [Decimal(str(x.amount or 0)) for x in receitas],
        Decimal("0")
    )

    total_despesas = sum(
        [Decimal(str(x.amount or 0)) for x in despesas],
        Decimal("0")
    )

    total_investimentos = sum(
        [Decimal(str(x.current_value or 0)) for x in investimentos],
        Decimal("0")
    )

    disponivel = (
        saldo_inicial
        + total_receitas
        - total_despesas
    )

    patrimonio = disponivel + total_investimentos

    receitas_recentes = sorted(
        receitas,
        key=lambda x: x.date,
        reverse=True
    )[:5]

    despesas_recentes = sorted(
        despesas,
        key=lambda x: x.date,
        reverse=True
    )[:5]

    contas_html = ""

    for conta in contas:
        contas_html += (
            "<option value='"
            + str(conta.id)
            + "'>"
            + conta.name
            + "</option>"
        )

    categorias_html = ""

    for categoria in categorias_despesa:
        categorias_html += (
            "<option value='"
            + str(categoria.id)
            + "'>"
            + categoria.name
            + "</option>"
        )

    receitas_html = ""

    for item in receitas_recentes:
        receitas_html += (
            "<div class='item'>"
            "<div>"
            "<strong>"
            + (item.description or "Receita")
            + "</strong>"
            "<small>"
            + item.date.strftime("%d/%m/%Y")
            + "</small>"
            "</div>"
            "<span class='green'>+ "
            + dinheiro(item.amount)
            + "</span>"
            "</div>"
        )

    if not receitas_html:
        receitas_html = "<p class='muted'>Nenhuma receita registrada.</p>"

    despesas_html = ""

    for item in despesas_recentes:
        despesas_html += (
            "<div class='item'>"
            "<div>"
            "<strong>"
            + (item.description or "Despesa")
            + "</strong>"
            "<small>"
            + item.date.strftime("%d/%m/%Y")
            + "</small>"
            "</div>"
            "<span class='red'>- "
            + dinheiro(item.amount)
            + "</span>"
            "</div>"
        )

    if not despesas_html:
        despesas_html = "<p class='muted'>Nenhuma despesa registrada.</p>"

    db.close()

    html = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<meta name="theme-color" content="#FFD400">

<title>Gastei</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #0b0b0b;
    color: #ffffff;
    font-family: Arial, Helvetica, sans-serif;
}

.container {
    width: 100%;
    max-width: 900px;
    margin: auto;
    padding: 16px;
}

.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 22px;
}

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 27px;
    font-weight: 800;
}

.sun {
    font-size: 32px;
}

.subtitle {
    color: #999999;
    font-size: 13px;
    margin-top: 4px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}

.card {
    background: #191919;
    border: 1px solid #303030;
    border-radius: 16px;
    padding: 18px;
}

.card.full {
    grid-column: 1 / -1;
}

.highlight {
    border-color: #FFD400;
}

.label {
    color: #999999;
    font-size: 13px;
    margin-bottom: 8px;
}

.value {
    font-size: 23px;
    font-weight: 800;
}

.yellow {
    color: #FFD400;
}

.green {
    color: #38d17a;
}

.red {
    color: #ff5c5c;
}

.muted {
    color: #888888;
}

h2 {
    font-size: 18px;
    margin-top: 28px;
}

form {
    display: grid;
    gap: 10px;
}

input,
select,
button {
    width: 100%;
    padding: 14px;
    border-radius: 10px;
    border: 1px solid #333333;
    background: #242424;
    color: white;
    font-size: 15px;
}

button {
    background: #FFD400;
    color: #000000;
    border: none;
    font-weight: 800;
}

.item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 13px 0;
    border-bottom: 1px solid #303030;
    gap: 10px;
}

.item:last-child {
    border-bottom: none;
}

.item strong {
    display: block;
}

.item small {
    display: block;
    color: #888888;
    margin-top: 4px;
}

.nav {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-top: 24px;
}

.nav div {
    background: #191919;
    border: 1px solid #303030;
    border-radius: 12px;
    padding: 13px 5px;
    text-align: center;
    color: #aaaaaa;
    font-size: 12px;
}

@media (max-width: 600px) {

    .container {
        padding: 13px;
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .card.full {
        grid-column: auto;
    }

    .value {
        font-size: 21px;
    }

}

</style>

</head>

<body>

<div class="container">

    <div class="header">

        <div>

            <div class="logo">
                <span class="sun">🌻</span>
                Gastei
            </div>

            <div class="subtitle">
                Controle financeiro pessoal
            </div>

        </div>

    </div>


    <div class="grid">

        <div class="card highlight">

            <div class="label">
                Patrimônio estimado
            </div>

            <div class="value yellow">
                __PATRIMONIO__
            </div>

        </div>


        <div class="card">

            <div class="label">
                Disponível
            </div>

            <div class="value">
                __DISPONIVEL__
            </div>

        </div>


        <div class="card">

            <div class="label">
                Investimentos
            </div>

            <div class="value">
                __INVESTIMENTOS__
            </div>

        </div>


        <div class="card">

            <div class="label">
                Receitas
            </div>

            <div class="value green">
                __RECEITAS__
            </div>

        </div>


        <div class="card">

            <div class="label">
                Despesas
            </div>

            <div class="value red">
                __DESPESAS__
            </div>

        </div>

    </div>


    <h2>Adicionar receita</h2>

    <div class="card">

        <form method="post" action="/income">

            <input
                name="description"
                placeholder="Descrição"
                required
            >

            <input
                name="amount"
                type="number"
                step="0.01"
                min="0.01"
                placeholder="Valor"
                required
            >

            <select name="account_id">
                __CONTAS__
            </select>

            <button type="submit">
                + Registrar receita
            </button>

        </form>

    </div>


    <h2>Adicionar despesa</h2>

    <div class="card">

        <form method="post" action="/expense">

            <input
                name="description"
                placeholder="Descrição"
                required
            >

            <input
                name="amount"
                type="number"
                step="0.01"
                min="0.01"
                placeholder="Valor"
                required
            >

            <select name="account_id">
                __CONTAS__
            </select>

            <select name="category_id">
                __CATEGORIAS__
            </select>

            <button type="submit">
                - Registrar despesa
            </button>

        </form>

    </div>


    <h2>Últimas receitas</h2>

    <div class="card">
        __RECEITAS_RECENTES__
    </div>


    <h2>Últimas despesas</h2>

    <div class="card">
        __DESPESAS_RECENTES__
    </div>


    <div class="nav">

        <div>Dashboard</div>
        <div>Cartões</div>
        <div>Investimentos</div>
        <div>Recompensas</div>
        <div>Automóveis</div>
        <div>Configurações</div>

    </div>

</div>

</body>
</html>
"""

    html = html.replace("__PATRIMONIO__", dinheiro(patrimonio))
    html = html.replace("__DISPONIVEL__", dinheiro(disponivel))
    html = html.replace("__INVESTIMENTOS__", dinheiro(total_investimentos))
    html = html.replace("__RECEITAS__", dinheiro(total_receitas))
    html = html.replace("__DESPESAS__", dinheiro(total_despesas))
    html = html.replace("__CONTAS__", contas_html)
    html = html.replace("__CATEGORIAS__", categorias_html)
    html = html.replace("__RECEITAS_RECENTES__", receitas_html)
    html = html.replace("__DESPESAS_RECENTES__", despesas_html)

    return HTMLResponse(html)


@app.post("/income")
def adicionar_receita(
    description: str = Form(...),
    amount: str = Form(...),
    account_id: int = Form(...)
):

    db = SessionLocal()

    categoria = (
        db.query(Category)
        .filter(Category.category_type == "INCOME")
        .first()
    )

    db.add(
        Income(
            account_id=account_id,
            category_id=categoria.id,
            description=description,
            amount=Decimal(amount),
            date=date.today(),
            income_type="VARIABLE"
        )
    )

    db.commit()
    db.close()

    return RedirectResponse("/", status_code=303)


@app.post("/expense")
def adicionar_despesa(
    description: str = Form(...),
    amount: str = Form(...),
    account_id: int = Form(...),
    category_id: int = Form(...)
):

    db = SessionLocal()

    db.add(
        Expense(
            account_id=account_id,
            category_id=category_id,
            description=description,
            amount=Decimal(amount),
            date=date.today()
        )
    )

    db.commit()
    db.close()

    return RedirectResponse("/", status_code=303)
