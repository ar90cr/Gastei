from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Numeric,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    text,
    inspect,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
import os


# ============================================================
# CONFIGURAÇÃO DO BANCO
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    BASE = os.getenv("GASTEI_DATA_DIR", "/content/gastei")
    os.makedirs(BASE, exist_ok=True)
    DATABASE_URL = "sqlite:///" + os.path.join(BASE, "gastei.db")

# Render/PostgreSQL pode fornecer DATABASE_URL com postgres://.
# SQLAlchemy moderno utiliza postgresql://.

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1,
    )

engine_kwargs = {}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {
        "check_same_thread": False
    }

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


# ============================================================
# MIXIN
# ============================================================

class TimestampMixin:
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ============================================================
# MODELOS
# ============================================================

class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False,
    )

    institution = Column(String)

    account_type = Column(
        String,
        nullable=False,
        default="CHECKING",
    )

    initial_balance = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False,
    )

    category_type = Column(
        String,
        nullable=False,
    )

    parent_id = Column(
        Integer,
        ForeignKey("categories.id"),
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class Income(TimestampMixin, Base):
    __tablename__ = "income"

    id = Column(Integer, primary_key=True)

    account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
    )

    description = Column(String)

    amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    date = Column(
        Date,
        nullable=False,
    )

    income_type = Column(
        String,
        nullable=False,
        default="VARIABLE",
    )

    notes = Column(String)


class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)

    account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
    )

    description = Column(String)

    amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    date = Column(
        Date,
        nullable=False,
    )

    notes = Column(String)


class Transfer(TimestampMixin, Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True)

    source_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
    )

    destination_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
    )

    amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    date = Column(
        Date,
        nullable=False,
    )

    description = Column(String)

    __table_args__ = (
        CheckConstraint(
            "source_account_id <> destination_account_id",
            name="ck_transfer_accounts",
        ),
    )


class RewardProgram(TimestampMixin, Base):
    __tablename__ = "reward_programs"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False,
        unique=True,
    )

    reward_type = Column(
        String,
        nullable=False,
    )

    unit_name = Column(String)

    estimated_unit_value = Column(
        Numeric(15, 6),
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class CreditCard(TimestampMixin, Base):
    __tablename__ = "credit_cards"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False,
    )

    institution = Column(String)

    brand = Column(String)

    credit_limit = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
    )

    closing_day = Column(
        Integer,
        nullable=False,
    )

    due_day = Column(
        Integer,
        nullable=False,
    )

    annual_fee = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
    )

    reward_program_id = Column(
        Integer,
        ForeignKey("reward_programs.id"),
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class CreditCardPurchase(TimestampMixin, Base):
    __tablename__ = "credit_card_purchases"

    id = Column(Integer, primary_key=True)

    credit_card_id = Column(
        Integer,
        ForeignKey("credit_cards.id"),
        nullable=False,
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
    )

    description = Column(String)

    purchase_date = Column(
        Date,
        nullable=False,
    )

    total_amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    installment_count = Column(
        Integer,
        nullable=False,
        default=1,
    )

    is_installment = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    notes = Column(String)


class CreditCardInvoice(TimestampMixin, Base):
    __tablename__ = "credit_card_invoices"

    id = Column(Integer, primary_key=True)

    credit_card_id = Column(
        Integer,
        ForeignKey("credit_cards.id"),
        nullable=False,
    )

    reference_year = Column(
        Integer,
        nullable=False,
    )

    reference_month = Column(
        Integer,
        nullable=False,
    )

    closing_date = Column(
        Date,
        nullable=False,
    )

    due_date = Column(
        Date,
        nullable=False,
    )

    total_amount = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
    )

    status = Column(
        String,
        nullable=False,
        default="OPEN",
    )

    paid_at = Column(DateTime)

    payment_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
    )

    __table_args__ = (
        UniqueConstraint(
            "credit_card_id",
            "reference_year",
            "reference_month",
            name="uq_invoice_period",
        ),
    )


class Installment(TimestampMixin, Base):
    __tablename__ = "installments"

    id = Column(Integer, primary_key=True)

    purchase_id = Column(
        Integer,
        ForeignKey("credit_card_purchases.id"),
        nullable=False,
    )

    invoice_id = Column(
        Integer,
        ForeignKey("credit_card_invoices.id"),
    )

    installment_number = Column(
        Integer,
        nullable=False,
    )

    total_installments = Column(
        Integer,
        nullable=False,
    )

    amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    due_date = Column(
        Date,
        nullable=False,
    )

    status = Column(
        String,
        nullable=False,
        default="OPEN",
    )

    paid_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint(
            "purchase_id",
            "installment_number",
            name="uq_installment_number",
        ),
        CheckConstraint(
            "installment_number >= 1 "
            "AND installment_number <= total_installments",
            name="ck_installment_number",
        ),
    )


class RecurringExpense(TimestampMixin, Base):
    __tablename__ = "recurring_expenses"

    id = Column(Integer, primary_key=True)

    description = Column(
        String,
        nullable=False,
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
    )

    amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    frequency = Column(
        String,
        nullable=False,
    )

    start_date = Column(
        Date,
        nullable=False,
    )

    end_date = Column(Date)

    payment_method = Column(
        String,
        nullable=False,
    )

    account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
    )

    card_id = Column(
        Integer,
        ForeignKey("credit_cards.id"),
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class RecurringIncome(TimestampMixin, Base):
    __tablename__ = "recurring_income"

    id = Column(Integer, primary_key=True)

    description = Column(
        String,
        nullable=False,
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
    )

    amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    frequency = Column(
        String,
        nullable=False,
    )

    start_date = Column(
        Date,
        nullable=False,
    )

    end_date = Column(Date)

    account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class CardRewardRule(TimestampMixin, Base):
    __tablename__ = "card_reward_rules"

    id = Column(Integer, primary_key=True)

    credit_card_id = Column(
        Integer,
        ForeignKey("credit_cards.id"),
        nullable=False,
    )

    reward_program_id = Column(
        Integer,
        ForeignKey("reward_programs.id"),
        nullable=False,
    )

    points_per_unit = Column(
        Numeric(20, 8),
        nullable=False,
    )

    reference_currency = Column(
        String,
        nullable=False,
        default="BRL",
    )

    currency_conversion_mode = Column(
        String,
        nullable=False,
        default="NONE",
    )

    fixed_exchange_rate = Column(
        Numeric(15, 6),
    )

    earning_mode = Column(
        String,
        nullable=False,
        default="PURCHASE",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class RewardTransaction(TimestampMixin, Base):
    __tablename__ = "reward_transactions"

    id = Column(Integer, primary_key=True)

    reward_program_id = Column(
        Integer,
        ForeignKey("reward_programs.id"),
        nullable=False,
    )

    credit_card_id = Column(
        Integer,
        ForeignKey("credit_cards.id"),
    )

    purchase_id = Column(
        Integer,
        ForeignKey("credit_card_purchases.id"),
    )

    amount_spent = Column(
        Numeric(15, 2),
        nullable=False,
    )

    reference_currency = Column(
        String,
        nullable=False,
        default="BRL",
    )

    exchange_rate = Column(
        Numeric(15, 6),
    )

    points_earned = Column(
        Numeric(20, 8),
        nullable=False,
    )

    transaction_date = Column(
        Date,
        nullable=False,
    )

    notes = Column(String)


class InvestmentInstitution(TimestampMixin, Base):
    __tablename__ = "investment_institutions"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False,
        unique=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class Investment(TimestampMixin, Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True)

    institution_id = Column(
        Integer,
        ForeignKey("investment_institutions.id"),
    )

    name = Column(
        String,
        nullable=False,
    )

    investment_type = Column(String)

    ticker = Column(String)

    currency = Column(
        String,
        nullable=False,
        default="BRL",
    )

    current_value = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
    )

    quantity = Column(
        Numeric(20, 8),
        nullable=False,
        default=0,
    )

    average_price = Column(
        Numeric(20, 8),
    )

    interest_rate = Column(
        Numeric(15, 6),
    )

    start_date = Column(Date)

    maturity_date = Column(Date)

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class InvestmentTransaction(TimestampMixin, Base):
    __tablename__ = "investment_transactions"

    id = Column(Integer, primary_key=True)

    investment_id = Column(
        Integer,
        ForeignKey("investments.id"),
        nullable=False,
    )

    transaction_type = Column(
        String,
        nullable=False,
    )

    amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    quantity = Column(
        Numeric(20, 8),
    )

    unit_price = Column(
        Numeric(20, 8),
    )

    date = Column(
        Date,
        nullable=False,
    )

    notes = Column(String)


class CryptoAsset(TimestampMixin, Base):
    __tablename__ = "crypto_assets"

    id = Column(Integer, primary_key=True)

    symbol = Column(
        String,
        nullable=False,
        unique=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    is_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class CryptoPrice(Base):
    __tablename__ = "crypto_prices"

    id = Column(Integer, primary_key=True)

    crypto_asset_id = Column(
        Integer,
        ForeignKey("crypto_assets.id"),
        nullable=False,
    )

    price = Column(
        Numeric(20, 8),
        nullable=False,
    )

    currency = Column(
        String,
        nullable=False,
        default="BRL",
    )

    source = Column(
        String,
        nullable=False,
    )

    timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True)

    brand = Column(
        String,
        nullable=False,
    )

    model = Column(
        String,
        nullable=False,
    )

    version = Column(String)

    year = Column(Integer)

    license_plate = Column(
        String,
        unique=True,
    )

    current_mileage = Column(
        Numeric(15, 2),
    )

    fuel_type = Column(String)

    average_consumption = Column(
        Numeric(15, 4),
    )

    tank_capacity = Column(
        Numeric(15, 2),
    )

    fuel_price = Column(
        Numeric(15, 4),
    )

    insurance_cost = Column(
        Numeric(15, 2),
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class VehicleMaintenance(TimestampMixin, Base):
    __tablename__ = "vehicle_maintenance"

    id = Column(Integer, primary_key=True)

    vehicle_id = Column(
        Integer,
        ForeignKey("vehicles.id"),
        nullable=False,
    )

    date = Column(
        Date,
        nullable=False,
    )

    mileage = Column(
        Numeric(15, 2),
    )

    component = Column(String)

    service = Column(String)

    amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    workshop = Column(String)

    notes = Column(String)


class VehicleTrip(TimestampMixin, Base):
    __tablename__ = "vehicle_trips"

    id = Column(Integer, primary_key=True)

    vehicle_id = Column(
        Integer,
        ForeignKey("vehicles.id"),
        nullable=False,
    )

    origin = Column(String)

    destination = Column(String)

    date = Column(
        Date,
        nullable=False,
    )

    distance_km = Column(
        Numeric(15, 2),
    )

    fuel_used = Column(
        Numeric(15, 4),
    )

    fuel_cost = Column(
        Numeric(15, 2),
    )

    toll_cost = Column(
        Numeric(15, 2),
    )

    total_cost = Column(
        Numeric(15, 2),
    )

    notes = Column(String)


class FuelPrice(TimestampMixin, Base):
    __tablename__ = "fuel_prices"

    id = Column(Integer, primary_key=True)

    fuel_type = Column(
        String,
        nullable=False,
    )

    price_per_liter = Column(
        Numeric(15, 4),
        nullable=False,
    )

    date = Column(
        Date,
        nullable=False,
    )

    source = Column(String)


class FinancialGoal(TimestampMixin, Base):
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False,
    )

    target_amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    current_amount = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
    )

    start_date = Column(Date)

    target_date = Column(Date)

    category = Column(String)

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )


class ApplicationSetting(Base):
    __tablename__ = "application_settings"

    id = Column(Integer, primary_key=True)

    key = Column(
        String,
        nullable=False,
        unique=True,
    )

    value = Column(String)

    value_type = Column(
        String,
        nullable=False,
        default="STRING",
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ============================================================
# ÍNDICES
# ============================================================

Index(
    "ix_income_date",
    Income.date,
)

Index(
    "ix_income_account_id",
    Income.account_id,
)

Index(
    "ix_expenses_date",
    Expense.date,
)

Index(
    "ix_expenses_category_id",
    Expense.category_id,
)

Index(
    "ix_transfers_date",
    Transfer.date,
)

Index(
    "ix_cc_purchases_date",
    CreditCardPurchase.purchase_date,
)

Index(
    "ix_installments_due_date",
    Installment.due_date,
)

Index(
    "ix_invoices_due_date",
    CreditCardInvoice.due_date,
)

Index(
    "ix_investment_transactions_date",
    InvestmentTransaction.date,
)

Index(
    "ix_vehicle_maintenance_date",
    VehicleMaintenance.date,
)

Index(
    "ix_vehicle_trips_date",
    VehicleTrip.date,
)

Index(
    "ix_reward_transactions_date",
    RewardTransaction.transaction_date,
)

Index(
    "ix_crypto_prices_timestamp",
    CryptoPrice.timestamp,
)


# ============================================================
# MIGRAÇÃO COMPATÍVEL DO MVP
# ============================================================

def migrate_legacy_schema():
    """
    Migração compatível com o MVP existente.

    Não apaga dados.
    Não recria tabelas existentes.
    Adiciona somente colunas ausentes.
    Preenche timestamps antigos.
    Cria a instituição padrão "Não informado".
    Vincula investimentos antigos a essa instituição.
    """

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
            "average_price": "NUMERIC(20,8)",
            "interest_rate": "NUMERIC(15,6)",
            "start_date": "DATE",
            "maturity_date": "DATE",
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP",
        },
    }

    with engine.begin() as conn:

        # ----------------------------------------------------
        # 1. ADICIONA COLUNAS AUSENTES
        # ----------------------------------------------------

        for table_name, columns in legacy_columns.items():

            inspector = inspect(conn)

            if not inspector.has_table(table_name):
                continue

            existing_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }

            for column_name, sql_type in columns.items():

                if column_name in existing_columns:
                    continue

                conn.execute(
                    text(
                        f'ALTER TABLE "{table_name}" '
                        f'ADD COLUMN "{column_name}" {sql_type}'
                    )
                )

            # ====================================================
    # 2. INSTITUIÇÃO PADRÃO
    # ====================================================

    inspector = inspect(conn)

    if inspector.has_table("investment_institutions"):

        institution_columns = {
            column["name"]
            for column in inspector.get_columns(
                "investment_institutions"
            )
        }

        # Preenche timestamps existentes que estejam NULL
        if "created_at" in institution_columns:
            conn.execute(
                text(
                    """
                    UPDATE investment_institutions
                    SET created_at = CURRENT_TIMESTAMP
                    WHERE created_at IS NULL
                    """
                )
            )

        if "updated_at" in institution_columns:
            conn.execute(
                text(
                    """
                    UPDATE investment_institutions
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE updated_at IS NULL
                    """
                )
            )

        # Cria a instituição padrão somente se ela ainda não existir
        conn.execute(
            text(
                """
                INSERT INTO investment_institutions
                    (
                        name,
                        is_active,
                        created_at,
                        updated_at
                    )
                SELECT
                    :name,
                    TRUE,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM investment_institutions
                    WHERE name = :name
                )
                """
            ),
            {
                "name": "Não informado"
            },
        )

        # ----------------------------------------------------
        # 3. VINCULA INVESTIMENTOS ANTIGOS
        # ----------------------------------------------------

        inspector = inspect(conn)

        if (
            inspector.has_table("investment_institutions")
            and inspector.has_table("investments")
        ):

            investment_columns = {
                column["name"]
                for column in inspector.get_columns(
                    "investments"
                )
            }

            if "institution_id" in investment_columns:

                conn.execute(
                    text(
                        """
                        UPDATE investments
                        SET institution_id = (
                            SELECT id
                            FROM investment_institutions
                            WHERE name = :name
                            ORDER BY id
                            LIMIT 1
                        )
                        WHERE institution_id IS NULL
                        """
                    ),
                    {
                        "name": "Não informado"
                    },
                )

        # ----------------------------------------------------
        # 4. PREENCHE TIMESTAMPS ANTIGOS
        # ----------------------------------------------------

        for table_name in (
            "accounts",
            "categories",
            "income",
            "expenses",
            "investments",
        ):

            inspector = inspect(conn)

            if not inspector.has_table(table_name):
                continue

            columns = {
                column["name"]
                for column in inspector.get_columns(
                    table_name
                )
            }

            if "created_at" in columns:

                conn.execute(
                    text(
                        f'''
                        UPDATE "{table_name}"
                        SET created_at = CURRENT_TIMESTAMP
                        WHERE created_at IS NULL
                        '''
                    )
                )

            if "updated_at" in columns:

                conn.execute(
                    text(
                        f'''
                        UPDATE "{table_name}"
                        SET updated_at = CURRENT_TIMESTAMP
                        WHERE updated_at IS NULL
                        '''
                    )
                )


# ============================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================

def initialize_database():

    # Cria tabelas novas sem apagar as existentes.
    Base.metadata.create_all(engine)

    # Executa migração compatível.
    migrate_legacy_schema()

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # CONTA PADRÃO
        # ----------------------------------------------------

        if db.query(Account).count() == 0:

            db.add(
                Account(
                    name="Conta principal",
                    institution="",
                    account_type="CHECKING",
                    initial_balance=Decimal("0.00"),
                )
            )

        # ----------------------------------------------------
        # CATEGORIAS PADRÃO
        # ----------------------------------------------------

        categorias = [
            ("Salário", "INCOME"),
            ("Extra", "INCOME"),
            ("Alimentação", "EXPENSE"),
            ("Moradia", "EXPENSE"),
            ("Transporte", "EXPENSE"),
            ("Lazer", "EXPENSE"),
            ("Saúde", "EXPENSE"),
            ("Educação", "EXPENSE"),
            ("Outros", "EXPENSE"),
        ]

        for nome, tipo in categorias:

            existente = (
                db.query(Category)
                .filter(
                    Category.name == nome,
                    Category.category_type == tipo,
                )
                .first()
            )

            if not existente:

                db.add(
                    Category(
                        name=nome,
                        category_type=tipo,
                    )
                )

        # ----------------------------------------------------
        # CRIPTOMOEDAS PADRÃO
        # ----------------------------------------------------

        cryptos = [
            ("BTC", "Bitcoin"),
            ("ETH", "Ethereum"),
            ("SOL", "Solana"),
        ]

        for symbol, name in cryptos:

            existente = (
                db.query(CryptoAsset)
                .filter(
                    CryptoAsset.symbol == symbol
                )
                .first()
            )

            if not existente:

                db.add(
                    CryptoAsset(
                        symbol=symbol,
                        name=name,
                    )
                )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


initialize_database()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Gastei",
)


# ============================================================
# UTILITÁRIOS
# ============================================================

def dinheiro(valor):
    """
    Formata um valor como moeda brasileira.
    """

    try:
        valor = Decimal(str(valor or 0))

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        valor = Decimal("0")

    texto = (
        f"{valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return "R$ " + texto


def converter_decimal(valor):
    """
    Converte entrada monetária para Decimal.

    Aceita formatos como:
    1000
    1000.50
    1.000,50
    """

    if valor is None:
        raise ValueError("Valor não informado.")

    valor = str(valor).strip()

    if not valor:
        raise ValueError("Valor não informado.")

    # Trata formato brasileiro.
    if "," in valor:
        valor = valor.replace(".", "")
        valor = valor.replace(",", ".")

    try:
        numero = Decimal(valor)

    except (
        InvalidOperation,
        ValueError,
    ):
        raise ValueError(
            "Valor monetário inválido."
        )

    if numero <= 0:
        raise ValueError(
            "O valor deve ser maior que zero."
        )

    return numero.quantize(
        Decimal("0.01")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse,
)
def dashboard():

    db = SessionLocal()

    try:

        contas = (
            db.query(Account)
            .filter(
                Account.is_active == True
            )
            .order_by(Account.name)
            .all()
        )

        receitas = (
            db.query(Income)
            .order_by(Income.date.desc())
            .all()
        )

        despesas = (
            db.query(Expense)
            .order_by(Expense.date.desc())
            .all()
        )

        investimentos = (
            db.query(Investment)
            .filter(
                Investment.is_active == True
            )
            .all()
        )

        categorias_despesa = (
            db.query(Category)
            .filter(
                Category.category_type == "EXPENSE",
                Category.is_active == True,
            )
            .order_by(Category.name)
            .all()
        )

        # ----------------------------------------------------
        # CÁLCULOS
        # ----------------------------------------------------

        saldo_inicial = sum(
            (
                Decimal(
                    str(
                        x.initial_balance or 0
                    )
                )
                for x in contas
            ),
            Decimal("0"),
        )

        total_receitas = sum(
            (
                Decimal(
                    str(
                        x.amount or 0
                    )
                )
                for x in receitas
            ),
            Decimal("0"),
        )

        total_despesas = sum(
            (
                Decimal(
                    str(
                        x.amount or 0
                    )
                )
                for x in despesas
            ),
            Decimal("0"),
        )

        total_investimentos = sum(
            (
                Decimal(
                    str(
                        x.current_value or 0
                    )
                )
                for x in investimentos
            ),
            Decimal("0"),
        )

        disponivel = (
            saldo_inicial
            + total_receitas
            - total_despesas
        )

        patrimonio = (
            disponivel
            + total_investimentos
        )

        receitas_recentes = receitas[:5]
        despesas_recentes = despesas[:5]

        # ----------------------------------------------------
        # SELECTS
        # ----------------------------------------------------

        contas_html = "".join(
            f"<option value='{c.id}'>"
            f"{c.name}"
            f"</option>"
            for c in contas
        )

        categorias_html = "".join(
            f"<option value='{c.id}'>"
            f"{c.name}"
            f"</option>"
            for c in categorias_despesa
        )

        # ----------------------------------------------------
        # RECEITAS RECENTES
        # ----------------------------------------------------

        receitas_html = "".join(
            (
                "<div class='item'>"
                "<div>"
                "<strong>"
                f"{item.description or 'Receita'}"
                "</strong>"
                "<small>"
                f"{item.date.strftime('%d/%m/%Y')}"
                "</small>"
                "</div>"
                "<span class='green'>"
                f"+ {dinheiro(item.amount)}"
                "</span>"
                "</div>"
            )
            for item in receitas_recentes
        )

        if not receitas_html:

            receitas_html = (
                "<p class='muted'>"
                "Nenhuma receita registrada."
                "</p>"
            )

        # ----------------------------------------------------
        # DESPESAS RECENTES
        # ----------------------------------------------------

        despesas_html = "".join(
            (
                "<div class='item'>"
                "<div>"
                "<strong>"
                f"{item.description or 'Despesa'}"
                "</strong>"
                "<small>"
                f"{item.date.strftime('%d/%m/%Y')}"
                "</small>"
                "</div>"
                "<span class='red'>"
                f"- {dinheiro(item.amount)}"
                "</span>"
                "</div>"
            )
            for item in despesas_recentes
        )

        if not despesas_html:

            despesas_html = (
                "<p class='muted'>"
                "Nenhuma despesa registrada."
                "</p>"
            )

    finally:
        db.close()

    # ========================================================
    # HTML
    # ========================================================

    html = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <meta
        name="theme-color"
        content="#FFD400"
    >

    <title>Gastei</title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            background: #0b0b0b;
            color: #fff;
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
            color: #999;
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
            color: #999;
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
            color: #888;
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
            border: 1px solid #333;
            background: #242424;
            color: white;
            font-size: 15px;
        }

        button {
            background: #FFD400;
            color: #000;
            border: none;
            font-weight: 800;
            cursor: pointer;
        }

        button:hover {
            opacity: 0.9;
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
            color: #888;
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
            color: #aaa;
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

        <h2>
            Adicionar receita
        </h2>

        <div class="card">

            <form
                method="post"
                action="/income"
            >

                <input
                    name="description"
                    placeholder="Descrição"
                    required
                >

                <input
                    name="amount"
                    type="text"
                    inputmode="decimal"
                    placeholder="Valor"
                    required
                >

                <select
                    name="account_id"
                    required
                >
                    __CONTAS__
                </select>

                <button type="submit">
                    + Registrar receita
                </button>

            </form>

        </div>

        <h2>
            Adicionar despesa
        </h2>

        <div class="card">

            <form
                method="post"
                action="/expense"
            >

                <input
                    name="description"
                    placeholder="Descrição"
                    required
                >

                <input
                    name="amount"
                    type="text"
                    inputmode="decimal"
                    placeholder="Valor"
                    required
                >

                <select
                    name="account_id"
                    required
                >
                    __CONTAS__
                </select>

                <select
                    name="category_id"
                    required
                >
                    __CATEGORIAS__
                </select>

                <button type="submit">
                    - Registrar despesa
                </button>

            </form>

        </div>

        <h2>
            Últimas receitas
        </h2>

        <div class="card">
            __RECEITAS_RECENTES__
        </div>

        <h2>
            Últimas despesas
        </h2>

        <div class="card">
            __DESPESAS_RECENTES__
        </div>

        <div class="nav">

            <div>
                Dashboard
            </div>

            <div>
                Cartões
            </div>

            <div>
                Investimentos
            </div>

            <div>
                Recompensas
            </div>

            <div>
                Automóveis
            </div>

            <div>
                Configurações
            </div>

        </div>

    </div>

</body>

</html>
"""

    replacements = {
        "__PATRIMONIO__": dinheiro(patrimonio),
        "__DISPONIVEL__": dinheiro(disponivel),
        "__INVESTIMENTOS__": dinheiro(total_investimentos),
        "__RECEITAS__": dinheiro(total_receitas),
        "__DESPESAS__": dinheiro(total_despesas),
        "__CONTAS__": contas_html,
        "__CATEGORIAS__": categorias_html,
        "__RECEITAS_RECENTES__": receitas_html,
        "__DESPESAS_RECENTES__": despesas_html,
    }

    for key, value in replacements.items():
        html = html.replace(
            key,
            value,
        )

    return HTMLResponse(html)


# ============================================================
# ADICIONAR RECEITA
# ============================================================

@app.post("/income")
def adicionar_receita(
    description: str = Form(...),
    amount: str = Form(...),
    account_id: int = Form(...),
):

    description = description.strip()

    if not description:
        raise HTTPException(
            status_code=400,
            detail="A descrição é obrigatória.",
        )

    try:
        valor = converter_decimal(amount)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    db = SessionLocal()

    try:

        conta = (
            db.query(Account)
            .filter(
                Account.id == account_id,
                Account.is_active == True,
            )
            .first()
        )

        if not conta:
            raise HTTPException(
                status_code=400,
                detail="Conta inválida.",
            )

        categoria = (
            db.query(Category)
            .filter(
                Category.category_type == "INCOME",
                Category.is_active == True,
            )
            .order_by(Category.id)
            .first()
        )

        if not categoria:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Nenhuma categoria de receita "
                    "está cadastrada."
                ),
            )

        db.add(
            Income(
                account_id=account_id,
                category_id=categoria.id,
                description=description,
                amount=valor,
                date=date.today(),
                income_type="VARIABLE",
            )
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    return RedirectResponse(
        "/",
        status_code=303,
    )


# ============================================================
# ADICIONAR DESPESA
# ============================================================

@app.post("/expense")
def adicionar_despesa(
    description: str = Form(...),
    amount: str = Form(...),
    account_id: int = Form(...),
    category_id: int = Form(...),
):

    description = description.strip()

    if not description:
        raise HTTPException(
            status_code=400,
            detail="A descrição é obrigatória.",
        )

    try:
        valor = converter_decimal(amount)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    db = SessionLocal()

    try:

        conta = (
            db.query(Account)
            .filter(
                Account.id == account_id,
                Account.is_active == True,
            )
            .first()
        )

        if not conta:
            raise HTTPException(
                status_code=400,
                detail="Conta inválida.",
            )

        categoria = (
            db.query(Category)
            .filter(
                Category.id == category_id,
                Category.category_type == "EXPENSE",
                Category.is_active == True,
            )
            .first()
        )

        if not categoria:
            raise HTTPException(
                status_code=400,
                detail="Categoria de despesa inválida.",
            )

        db.add(
            Expense(
                account_id=account_id,
                category_id=category_id,
                description=description,
                amount=valor,
                date=date.today(),
            )
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    return RedirectResponse(
        "/",
        status_code=303,
    )
