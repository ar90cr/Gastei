from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import (
    create_engine, Column, Integer, String, Numeric, Date, DateTime, Boolean,
    ForeignKey, CheckConstraint, UniqueConstraint, Index, text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from decimal import Decimal
from datetime import date, datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    BASE = os.getenv("GASTEI_DATA_DIR", "/content/gastei")
    os.makedirs(BASE, exist_ok=True)
    DATABASE_URL = "sqlite:///" + os.path.join(BASE, "gastei.db")

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    institution = Column(String)
    account_type = Column(String, nullable=False, default="CHECKING")
    initial_balance = Column(Numeric(15, 2), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)


class Category(TimestampMixin, Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category_type = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"))
    is_active = Column(Boolean, nullable=False, default=True)


class Income(TimestampMixin, Base):
    __tablename__ = "income"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    description = Column(String)
    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(Date, nullable=False)
    income_type = Column(String, nullable=False, default="VARIABLE")
    notes = Column(String)


class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    description = Column(String)
    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(Date, nullable=False)
    notes = Column(String)


class Transfer(TimestampMixin, Base):
    __tablename__ = "transfers"
    id = Column(Integer, primary_key=True)
    source_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    destination_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String)
    __table_args__ = (CheckConstraint("source_account_id <> destination_account_id", name="ck_transfer_accounts"),)


class CreditCard(TimestampMixin, Base):
    __tablename__ = "credit_cards"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    institution = Column(String)
    brand = Column(String)
    credit_limit = Column(Numeric(15, 2), nullable=False, default=0)
    closing_day = Column(Integer, nullable=False)
    due_day = Column(Integer, nullable=False)
    annual_fee = Column(Numeric(15, 2), nullable=False, default=0)
    reward_program_id = Column(Integer, ForeignKey("reward_programs.id"))
    is_active = Column(Boolean, nullable=False, default=True)


class CreditCardPurchase(TimestampMixin, Base):
    __tablename__ = "credit_card_purchases"
    id = Column(Integer, primary_key=True)
    credit_card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    description = Column(String)
    purchase_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    installment_count = Column(Integer, nullable=False, default=1)
    is_installment = Column(Boolean, nullable=False, default=False)
    notes = Column(String)


class CreditCardInvoice(TimestampMixin, Base):
    __tablename__ = "credit_card_invoices"
    id = Column(Integer, primary_key=True)
    credit_card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=False)
    reference_year = Column(Integer, nullable=False)
    reference_month = Column(Integer, nullable=False)
    closing_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    status = Column(String, nullable=False, default="OPEN")
    paid_at = Column(DateTime)
    payment_account_id = Column(Integer, ForeignKey("accounts.id"))
    __table_args__ = (UniqueConstraint("credit_card_id", "reference_year", "reference_month", name="uq_invoice_period"),)


class Installment(TimestampMixin, Base):
    __tablename__ = "installments"
    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey("credit_card_purchases.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("credit_card_invoices.id"))
    installment_number = Column(Integer, nullable=False)
    total_installments = Column(Integer, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="OPEN")
    paid_at = Column(DateTime)
    __table_args__ = (
        UniqueConstraint("purchase_id", "installment_number", name="uq_installment_number"),
        CheckConstraint("installment_number >= 1 AND installment_number <= total_installments", name="ck_installment_number"),
    )


class RecurringExpense(TimestampMixin, Base):
    __tablename__ = "recurring_expenses"
    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    frequency = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    payment_method = Column(String, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    card_id = Column(Integer, ForeignKey("credit_cards.id"))
    is_active = Column(Boolean, nullable=False, default=True)


class RecurringIncome(TimestampMixin, Base):
    __tablename__ = "recurring_income"
    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    frequency = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class RewardProgram(TimestampMixin, Base):
    __tablename__ = "reward_programs"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    reward_type = Column(String, nullable=False)
    unit_name = Column(String)
    estimated_unit_value = Column(Numeric(15, 6))
    is_active = Column(Boolean, nullable=False, default=True)


class CardRewardRule(TimestampMixin, Base):
    __tablename__ = "card_reward_rules"
    id = Column(Integer, primary_key=True)
    credit_card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=False)
    reward_program_id = Column(Integer, ForeignKey("reward_programs.id"), nullable=False)
    points_per_unit = Column(Numeric(20, 8), nullable=False)
    reference_currency = Column(String, nullable=False, default="BRL")
    currency_conversion_mode = Column(String, nullable=False, default="NONE")
    fixed_exchange_rate = Column(Numeric(15, 6))
    earning_mode = Column(String, nullable=False, default="PURCHASE")
    is_active = Column(Boolean, nullable=False, default=True)


class RewardTransaction(TimestampMixin, Base):
    __tablename__ = "reward_transactions"
    id = Column(Integer, primary_key=True)
    reward_program_id = Column(Integer, ForeignKey("reward_programs.id"), nullable=False)
    credit_card_id = Column(Integer, ForeignKey("credit_cards.id"))
    purchase_id = Column(Integer, ForeignKey("credit_card_purchases.id"))
    amount_spent = Column(Numeric(15, 2), nullable=False)
    reference_currency = Column(String, nullable=False, default="BRL")
    exchange_rate = Column(Numeric(15, 6))
    points_earned = Column(Numeric(20, 8), nullable=False)
    transaction_date = Column(Date, nullable=False)
    notes = Column(String)


class InvestmentInstitution(TimestampMixin, Base):
    __tablename__ = "investment_institutions"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)


class Investment(TimestampMixin, Base):
    __tablename__ = "investments"
    id = Column(Integer, primary_key=True)
    institution_id = Column(Integer, ForeignKey("investment_institutions.id"))
    name = Column(String, nullable=False)
    investment_type = Column(String)
    ticker = Column(String)
    currency = Column(String, nullable=False, default="BRL")
    current_value = Column(Numeric(15, 2), nullable=False, default=0)
    quantity = Column(Numeric(20, 8), nullable=False, default=0)
    average_price = Column(Numeric(20, 8))
    interest_rate = Column(Numeric(15, 6))
    start_date = Column(Date)
    maturity_date = Column(Date)
    is_active = Column(Boolean, nullable=False, default=True)


class InvestmentTransaction(TimestampMixin, Base):
    __tablename__ = "investment_transactions"
    id = Column(Integer, primary_key=True)
    investment_id = Column(Integer, ForeignKey("investments.id"), nullable=False)
    transaction_type = Column(String, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    quantity = Column(Numeric(20, 8))
    unit_price = Column(Numeric(20, 8))
    date = Column(Date, nullable=False)
    notes = Column(String)


class CryptoAsset(TimestampMixin, Base):
    __tablename__ = "crypto_assets"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    is_enabled = Column(Boolean, nullable=False, default=True)


class CryptoPrice(Base):
    __tablename__ = "crypto_prices"
    id = Column(Integer, primary_key=True)
    crypto_asset_id = Column(Integer, ForeignKey("crypto_assets.id"), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    currency = Column(String, nullable=False, default="BRL")
    source = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    version = Column(String)
    year = Column(Integer)
    license_plate = Column(String, unique=True)
    current_mileage = Column(Numeric(15, 2))
    fuel_type = Column(String)
    average_consumption = Column(Numeric(15, 4))
    tank_capacity = Column(Numeric(15, 2))
    fuel_price = Column(Numeric(15, 4))
    insurance_cost = Column(Numeric(15, 2))
    is_active = Column(Boolean, nullable=False, default=True)


class VehicleMaintenance(TimestampMixin, Base):
    __tablename__ = "vehicle_maintenance"
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    date = Column(Date, nullable=False)
    mileage = Column(Numeric(15, 2))
    component = Column(String)
    service = Column(String)
    amount = Column(Numeric(15, 2), nullable=False)
    workshop = Column(String)
    notes = Column(String)


class VehicleTrip(TimestampMixin, Base):
    __tablename__ = "vehicle_trips"
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    origin = Column(String)
    destination = Column(String)
    date = Column(Date, nullable=False)
    distance_km = Column(Numeric(15, 2))
    fuel_used = Column(Numeric(15, 4))
    fuel_cost = Column(Numeric(15, 2))
    toll_cost = Column(Numeric(15, 2))
    total_cost = Column(Numeric(15, 2))
    notes = Column(String)


class FuelPrice(TimestampMixin, Base):
    __tablename__ = "fuel_prices"
    id = Column(Integer, primary_key=True)
    fuel_type = Column(String, nullable=False)
    price_per_liter = Column(Numeric(15, 4), nullable=False)
    date = Column(Date, nullable=False)
    source = Column(String)


class FinancialGoal(TimestampMixin, Base):
    __tablename__ = "financial_goals"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    target_amount = Column(Numeric(15, 2), nullable=False)
    current_amount = Column(Numeric(15, 2), nullable=False, default=0)
    start_date = Column(Date)
    target_date = Column(Date)
    category = Column(String)
    is_active = Column(Boolean, nullable=False, default=True)


class ApplicationSetting(Base):
    __tablename__ = "application_settings"
    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(String)
    value_type = Column(String, nullable=False, default="STRING")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Useful indexes
Index("ix_income_date", Income.date)
Index("ix_income_account_id", Income.account_id)
Index("ix_expenses_date", Expense.date)
Index("ix_expenses_category_id", Expense.category_id)
Index("ix_transfers_date", Transfer.date)
Index("ix_cc_purchases_date", CreditCardPurchase.purchase_date)
Index("ix_installments_due_date", Installment.due_date)
Index("ix_invoices_due_date", CreditCardInvoice.due_date)
Index("ix_investment_transactions_date", InvestmentTransaction.date)
Index("ix_vehicle_maintenance_date", VehicleMaintenance.date)
Index("ix_vehicle_trips_date", VehicleTrip.date)
Index("ix_reward_transactions_date", RewardTransaction.transaction_date)
Index("ix_crypto_prices_timestamp", CryptoPrice.timestamp)

# Safe bootstrap for a fresh PostgreSQL database.
# Existing MVP tables are preserved. New tables are added without deleting data.
# ============================================================
# MIGRAÇÃO COMPATÍVEL DO MVP
# ============================================================
# O MVP inicial já criou algumas tabelas no PostgreSQL sem as
# colunas novas. create_all() não altera tabelas existentes.
# Esta etapa adiciona apenas colunas ausentes e preserva dados.

def migrate_legacy_schema():
    from sqlalchemy import inspect

    inspector = inspect(engine)
    dialect = engine.dialect.name

    legacy_columns = {
        "accounts": {
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP",
        },
        "categories": {
            "parent_id": "INTEGER",
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP",
        },
        "income": {
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP",
        },
        "expenses": {
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP",
        },
        "investments": {
            "institution_id": "INTEGER",
            "ticker": "VARCHAR",
            "currency": "VARCHAR",
            "average_price": "NUMERIC(15,2)",
            "interest_rate": "NUMERIC(15,6)",
            "start_date": "DATE",
            "maturity_date": "DATE",
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP",
        },
    }

    # No PostgreSQL, adicionamos somente colunas realmente ausentes.
    # As novas colunas ficam inicialmente NULL para não quebrar os
    # registros antigos.
    with engine.begin() as conn:
        for table_name, columns in legacy_columns.items():
            if not inspector.has_table(table_name):
                continue

            existing = {c["name"] for c in inspect(engine).get_columns(table_name)}

            for column_name, sql_type in columns.items():
                if column_name not in existing:
                    if dialect == "postgresql":
                        conn.execute(text(
                            f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {sql_type}'
                        ))
                    elif dialect == "sqlite":
                        conn.execute(text(
                            f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {sql_type}'
                        ))

        # Garante uma instituição para investimentos antigos, quando necessário.
        if inspector.has_table("investment_institutions") and inspector.has_table("investments"):
            result = conn.execute(text(
                "SELECT id FROM investment_institutions ORDER BY id LIMIT 1"
            )).first()

            if result is None:
                conn.execute(text(
                    "INSERT INTO investment_institutions (name, is_active) "
                    "VALUES ('Não informado', 1)"
                ))
                result = conn.execute(text(
                    "SELECT id FROM investment_institutions ORDER BY id LIMIT 1"
                )).first()

            if result is not None:
                conn.execute(text(
                    "UPDATE investments "
                    "SET institution_id = :institution_id "
                    "WHERE institution_id IS NULL"
                ), {"institution_id": result[0]})

        # Preenche timestamps dos registros antigos.
        for table_name in ("accounts", "categories", "income", "expenses", "investments"):
            if inspector.has_table(table_name):
                cols = {c["name"] for c in inspect(engine).get_columns(table_name)}
                if "created_at" in cols:
                    conn.execute(text(
                        f'UPDATE "{table_name}" SET created_at = CURRENT_TIMESTAMP '
                        'WHERE created_at IS NULL'
                    ))
                if "updated_at" in cols:
                    conn.execute(text(
                        f'UPDATE "{table_name}" SET updated_at = CURRENT_TIMESTAMP '
                        'WHERE updated_at IS NULL'
                    ))

# Cria as tabelas novas e depois adapta as tabelas antigas.
Base.metadata.create_all(engine)
migrate_legacy_schema()

db = SessionLocal()
try:
    if db.query(Account).count() == 0:
        db.add(Account(name="Conta principal", institution="", account_type="CHECKING", initial_balance=Decimal("0")))

    if db.query(Category).count() == 0:
        categorias = [
            ("Salário", "INCOME"), ("Extra", "INCOME"),
            ("Alimentação", "EXPENSE"), ("Moradia", "EXPENSE"),
            ("Transporte", "EXPENSE"), ("Lazer", "EXPENSE"),
            ("Saúde", "EXPENSE"), ("Educação", "EXPENSE"), ("Outros", "EXPENSE")
        ]
        for nome, tipo in categorias:
            db.add(Category(name=nome, category_type=tipo))

    for symbol, name in [("BTC", "Bitcoin"), ("ETH", "Ethereum"), ("SOL", "Solana")]:
        if not db.query(CryptoAsset).filter_by(symbol=symbol).first():
            db.add(CryptoAsset(symbol=symbol, name=name))

    db.commit()
finally:
    db.close()


app = FastAPI(title="Gastei")


def dinheiro(valor):
    valor = Decimal(str(valor or 0))
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + texto


@app.get("/", response_class=HTMLResponse)
def dashboard():
    db = SessionLocal()
    try:
        contas = db.query(Account).filter(Account.is_active == True).all()
        receitas = db.query(Income).all()
        despesas = db.query(Expense).all()
        investimentos = db.query(Investment).filter(Investment.is_active == True).all()
        categorias_despesa = db.query(Category).filter(Category.category_type == "EXPENSE").all()

        saldo_inicial = sum((Decimal(str(x.initial_balance or 0)) for x in contas), Decimal("0"))
        total_receitas = sum((Decimal(str(x.amount or 0)) for x in receitas), Decimal("0"))
        total_despesas = sum((Decimal(str(x.amount or 0)) for x in despesas), Decimal("0"))
        total_investimentos = sum((Decimal(str(x.current_value or 0)) for x in investimentos), Decimal("0"))

        disponivel = saldo_inicial + total_receitas - total_despesas
        patrimonio = disponivel + total_investimentos

        receitas_recentes = sorted(receitas, key=lambda x: x.date, reverse=True)[:5]
        despesas_recentes = sorted(despesas, key=lambda x: x.date, reverse=True)[:5]

        contas_html = "".join(f"<option value='{c.id}'>{c.name}</option>" for c in contas)
        categorias_html = "".join(f"<option value='{c.id}'>{c.name}</option>" for c in categorias_despesa)

        receitas_html = "".join(
            f"<div class='item'><div><strong>{item.description or 'Receita'}</strong><small>{item.date.strftime('%d/%m/%Y')}</small></div>"
            f"<span class='green'>+ {dinheiro(item.amount)}</span></div>" for item in receitas_recentes
        ) or "<p class='muted'>Nenhuma receita registrada.</p>"

        despesas_html = "".join(
            f"<div class='item'><div><strong>{item.description or 'Despesa'}</strong><small>{item.date.strftime('%d/%m/%Y')}</small></div>"
            f"<span class='red'>- {dinheiro(item.amount)}</span></div>" for item in despesas_recentes
        ) or "<p class='muted'>Nenhuma despesa registrada.</p>"
    finally:
        db.close()

    html = """
<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#FFD400"><title>Gastei</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0b0b0b;color:#fff;font-family:Arial,Helvetica,sans-serif}
.container{width:100%;max-width:900px;margin:auto;padding:16px}.header{display:flex;align-items:center;justify-content:space-between;margin-bottom:22px}
.logo{display:flex;align-items:center;gap:10px;font-size:27px;font-weight:800}.sun{font-size:32px}.subtitle{color:#999;font-size:13px;margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.card{background:#191919;border:1px solid #303030;border-radius:16px;padding:18px}
.card.full{grid-column:1/-1}.highlight{border-color:#FFD400}.label{color:#999;font-size:13px;margin-bottom:8px}
.value{font-size:23px;font-weight:800}.yellow{color:#FFD400}.green{color:#38d17a}.red{color:#ff5c5c}.muted{color:#888}
h2{font-size:18px;margin-top:28px}form{display:grid;gap:10px}input,select,button{width:100%;padding:14px;border-radius:10px;border:1px solid #333;background:#242424;color:white;font-size:15px}
button{background:#FFD400;color:#000;border:none;font-weight:800}.item{display:flex;justify-content:space-between;align-items:center;padding:13px 0;border-bottom:1px solid #303030;gap:10px}
.item:last-child{border-bottom:none}.item strong{display:block}.item small{display:block;color:#888;margin-top:4px}
.nav{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:24px}.nav div{background:#191919;border:1px solid #303030;border-radius:12px;padding:13px 5px;text-align:center;color:#aaa;font-size:12px}
@media(max-width:600px){.container{padding:13px}.grid{grid-template-columns:1fr}.card.full{grid-column:auto}.value{font-size:21px}}
</style></head><body><div class="container">
<div class="header"><div><div class="logo"><span class="sun">🌻</span>Gastei</div><div class="subtitle">Controle financeiro pessoal</div></div></div>
<div class="grid">
<div class="card highlight"><div class="label">Patrimônio estimado</div><div class="value yellow">__PATRIMONIO__</div></div>
<div class="card"><div class="label">Disponível</div><div class="value">__DISPONIVEL__</div></div>
<div class="card"><div class="label">Investimentos</div><div class="value">__INVESTIMENTOS__</div></div>
<div class="card"><div class="label">Receitas</div><div class="value green">__RECEITAS__</div></div>
<div class="card"><div class="label">Despesas</div><div class="value red">__DESPESAS__</div></div>
</div>
<h2>Adicionar receita</h2><div class="card"><form method="post" action="/income">
<input name="description" placeholder="Descrição" required><input name="amount" type="number" step="0.01" min="0.01" placeholder="Valor" required>
<select name="account_id">__CONTAS__</select><button type="submit">+ Registrar receita</button></form></div>
<h2>Adicionar despesa</h2><div class="card"><form method="post" action="/expense">
<input name="description" placeholder="Descrição" required><input name="amount" type="number" step="0.01" min="0.01" placeholder="Valor" required>
<select name="account_id">__CONTAS__</select><select name="category_id">__CATEGORIAS__</select><button type="submit">- Registrar despesa</button></form></div>
<h2>Últimas receitas</h2><div class="card">__RECEITAS_RECENTES__</div>
<h2>Últimas despesas</h2><div class="card">__DESPESAS_RECENTES__</div>
<div class="nav"><div>Dashboard</div><div>Cartões</div><div>Investimentos</div><div>Recompensas</div><div>Automóveis</div><div>Configurações</div></div>
</div></body></html>"""
    replacements = {
        "__PATRIMONIO__": dinheiro(patrimonio), "__DISPONIVEL__": dinheiro(disponivel),
        "__INVESTIMENTOS__": dinheiro(total_investimentos), "__RECEITAS__": dinheiro(total_receitas),
        "__DESPESAS__": dinheiro(total_despesas), "__CONTAS__": contas_html,
        "__CATEGORIAS__": categorias_html, "__RECEITAS_RECENTES__": receitas_html,
        "__DESPESAS_RECENTES__": despesas_html
    }
    for k, v in replacements.items():
        html = html.replace(k, v)
    return HTMLResponse(html)


@app.post("/income")
def adicionar_receita(description: str = Form(...), amount: str = Form(...), account_id: int = Form(...)):
    db = SessionLocal()
    try:
        categoria = db.query(Category).filter(Category.category_type == "INCOME").first()
        db.add(Income(account_id=account_id, category_id=categoria.id, description=description,
                      amount=Decimal(amount), date=date.today(), income_type="VARIABLE"))
        db.commit()
    finally:
        db.close()
    return RedirectResponse("/", status_code=303)


@app.post("/expense")
def adicionar_despesa(description: str = Form(...), amount: str = Form(...),
                       account_id: int = Form(...), category_id: int = Form(...)):
    db = SessionLocal()
    try:
        db.add(Expense(account_id=account_id, category_id=category_id, description=description,
                       amount=Decimal(amount), date=date.today()))
        db.commit()
    finally:
        db.close()
    return RedirectResponse("/", status_code=303)
