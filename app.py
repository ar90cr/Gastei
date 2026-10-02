from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
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
        "investment_institutions": {
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP",
        },
    }

    with engine.begin() as conn:

        # -------------------------------------------------
        # 1. Adiciona colunas que estejam faltando
        # -------------------------------------------------

        for table_name, columns in legacy_columns.items():

            inspector = inspect(conn)

            if not inspector.has_table(table_name):
                continue

            existing_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }

            for column_name, column_type in columns.items():

                if column_name in existing_columns:
                    continue

                conn.execute(
                    text(
                        f"""
                        ALTER TABLE {table_name}
                        ADD COLUMN {column_name} {column_type}
                        """
                    )
                )

        # -------------------------------------------------
        # 2. Atualiza o inspector depois das alterações
        # -------------------------------------------------

        inspector = inspect(conn)

        # -------------------------------------------------
        # 3. Instituição padrão
        # -------------------------------------------------

        if inspector.has_table("investment_institutions"):

            institution_columns = {
                column["name"]
                for column in inspector.get_columns(
                    "investment_institutions"
                )
            }

            # Corrige registros antigos que tenham
            # created_at ou updated_at nulos.
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

            # Cria a instituição padrão somente se não existir.
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

        # -------------------------------------------------
        # 4. Descobre o ID da instituição padrão
        # -------------------------------------------------

        default_institution_id = None

        if inspector.has_table("investment_institutions"):

            result = conn.execute(
                text(
                    """
                    SELECT id
                    FROM investment_institutions
                    WHERE name = :name
                    LIMIT 1
                    """
                ),
                {
                    "name": "Não informado"
                },
            )

            row = result.fetchone()

            if row:
                default_institution_id = row[0]

        # -------------------------------------------------
        # 5. Vincula investimentos antigos
        # -------------------------------------------------

        if (
            default_institution_id is not None
            and inspector.has_table("investments")
        ):
            investment_columns = {
                column["name"]
                for column in inspector.get_columns("investments")
            }

            if "institution_id" in investment_columns:

                conn.execute(
                    text(
                        """
                        UPDATE investments
                        SET institution_id = :institution_id
                        WHERE institution_id IS NULL
                        """
                    ),
                    {
                        "institution_id": default_institution_id
                    },
                )

        # -------------------------------------------------
        # 6. Preenche timestamps das tabelas antigas
        # -------------------------------------------------

        timestamp_tables = (
            "accounts",
            "categories",
            "income",
            "expenses",
            "investments",
            "investment_institutions",
        )

        for table_name in timestamp_tables:

            if not inspector.has_table(table_name):
                continue

            table_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }

            if "created_at" in table_columns:

                conn.execute(
                    text(
                        f"""
                        UPDATE {table_name}
                        SET created_at = CURRENT_TIMESTAMP
                        WHERE created_at IS NULL
                        """
                    )
                )

            if "updated_at" in table_columns:

                conn.execute(
                    text(
                        f"""
                        UPDATE {table_name}
                        SET updated_at = CURRENT_TIMESTAMP
                        WHERE updated_at IS NULL
                        """
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
            <a href="/">Dashboard</a>
            <a href="/transfers">Transferências</a>
            <a href="/cards">Cartões</a>
            <a href="/investments">Investimentos</a>
            <a href="/goals">Metas</a>
            <a href="/rewards">Recompensas</a>
            <a href="/vehicles">Automóveis</a>
            <a href="/health">Saúde</a>
            <a href="/settings">Configurações</a>
            <a href="/export.json">Exportar</a>
        </div>

    </div>
    <script>if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');</script>
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
# PWA
# ============================================================

@app.get("/manifest.json")
def manifest():
    return JSONResponse({
        "name": "Gastei",
        "short_name": "Gastei",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0b0b0b",
        "theme_color": "#FFD400",
        "description": "Controle financeiro pessoal",
        "icons": [],
    })


@app.get("/sw.js")
def service_worker():
    js = """
const CACHE = 'gastei-v1';
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(['/','/manifest.json'])));
});
self.addEventListener('fetch', event => {
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
"""
    return Response(js, media_type="application/javascript")


def page_shell(title, body):
    return f"""<!DOCTYPE html>
<html lang='pt-BR'><head>
<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<meta name='theme-color' content='#FFD400'><link rel='manifest' href='/manifest.json'>
<title>{title} — Gastei</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#0b0b0b;color:#fff;font-family:Arial,sans-serif}}
.container{{max-width:960px;margin:auto;padding:16px}}a{{color:#FFD400;text-decoration:none}}
.header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}}
.logo{{font-size:25px;font-weight:800}}.sun{{font-size:29px}}.muted{{color:#888}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}.full{{grid-column:1/-1}}
.card{{background:#191919;border:1px solid #303030;border-radius:16px;padding:16px}}
label{{display:block;color:#aaa;font-size:13px;margin:4px 0}}input,select,button{{width:100%;padding:13px;border-radius:10px;border:1px solid #333;background:#242424;color:#fff;font-size:15px}}
button{{background:#FFD400;color:#000;border:0;font-weight:800;cursor:pointer}}form{{display:grid;gap:9px}}
.item{{display:flex;justify-content:space-between;gap:12px;padding:12px 0;border-bottom:1px solid #303030}}.item:last-child{{border-bottom:0}}
.nav{{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}}.nav a{{background:#191919;border:1px solid #303030;border-radius:10px;padding:10px 12px;color:#ddd;font-size:13px}}
.good{{color:#38d17a}}.bad{{color:#ff5c5c}}.yellow{{color:#FFD400}}
@media(max-width:650px){{.grid{{grid-template-columns:1fr}}.full{{grid-column:auto}}}}
</style></head><body><div class='container'>
<div class='header'><div class='logo'><span class='sun'>🌻</span> Gastei</div><a href='/'>Dashboard</a></div>
<div class='nav'><a href='/'>Início</a><a href='/transfers'>Transferências</a><a href='/cards'>Cartões</a><a href='/investments'>Investimentos</a><a href='/goals'>Metas</a><a href='/rewards'>Recompensas</a><a href='/vehicles'>Automóveis</a><a href='/health'>Saúde</a><a href='/settings'>Configurações</a><a href='/export.json'>Exportar</a></div>
{body}
</div><script>if('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');</script></body></html>"""


def get_accounts(db):
    return db.query(Account).filter(Account.is_active == True).order_by(Account.name).all()


def get_categories(db, kind):
    return db.query(Category).filter(Category.category_type == kind, Category.is_active == True).order_by(Category.name).all()


@app.get('/transfers', response_class=HTMLResponse)
def transfers_page():
    db=SessionLocal()
    try:
        accounts=get_accounts(db)
        transfers=db.query(Transfer).order_by(Transfer.date.desc(), Transfer.id.desc()).limit(30).all()
        opts=''.join(f"<option value='{a.id}'>{a.name}</option>" for a in accounts)
        items=''.join(f"<div class='item'><span>{t.description or 'Transferência'}<br><small class='muted'>{t.date.strftime('%d/%m/%Y')}</small></span><span>{dinheiro(t.amount)}</span></div>" for t in transfers) or "<p class='muted'>Nenhuma transferência registrada.</p>"
        body=f"""<h1>Transferências</h1><div class='grid'><div class='card'><h2>Nova transferência</h2><form method='post' action='/transfers'>
<label>Origem</label><select name='source_account_id' required>{opts}</select><label>Destino</label><select name='destination_account_id' required>{opts}</select>
<label>Valor</label><input name='amount' inputmode='decimal' placeholder='0,00' required><label>Descrição</label><input name='description' placeholder='Ex.: reserva mensal'>
<button>Registrar transferência</button></form></div><div class='card'><h2>Histórico</h2>{items}</div></div>"""
        return HTMLResponse(page_shell('Transferências',body))
    finally: db.close()


@app.post('/transfers')
def create_transfer(source_account_id:int=Form(...), destination_account_id:int=Form(...), amount:str=Form(...), description:str=Form('')):
    if source_account_id == destination_account_id: raise HTTPException(400,'As contas de origem e destino devem ser diferentes.')
    valor=converter_decimal(amount)
    if valor <= 0: raise HTTPException(400,'O valor deve ser maior que zero.')
    db=SessionLocal()
    try:
        ids={a.id for a in get_accounts(db)}
        if source_account_id not in ids or destination_account_id not in ids: raise HTTPException(400,'Conta inválida.')
        db.add(Transfer(source_account_id=source_account_id,destination_account_id=destination_account_id,amount=valor,date=date.today(),description=description.strip() or None))
        db.commit()
    except Exception:
        db.rollback(); raise
    finally: db.close()
    return RedirectResponse('/transfers',303)


@app.get('/cards', response_class=HTMLResponse)
def cards_page():
    db=SessionLocal()
    try:
        cards=db.query(CreditCard).filter(CreditCard.is_active==True).order_by(CreditCard.name).all()
        cats=get_categories(db,'EXPENSE')
        cardopts=''.join(f"<option value='{c.id}'>{c.name}</option>" for c in cards)
        catopts=''.join(f"<option value='{c.id}'>{c.name}</option>" for c in cats)
        carditems=''.join(f"<div class='item'><span><b>{c.name}</b><br><small class='muted'>{c.institution or ''} · limite {dinheiro(c.credit_limit)}</small></span><span>fecha {c.closing_day} · vence {c.due_day}</span></div>" for c in cards) or "<p class='muted'>Nenhum cartão cadastrado.</p>"
        body=f"""<h1>Cartões</h1><div class='grid'><div class='card'><h2>Novo cartão</h2><form method='post' action='/cards'><input name='name' placeholder='Nome do cartão' required><input name='institution' placeholder='Instituição'><input name='brand' placeholder='Bandeira'><input name='credit_limit' inputmode='decimal' placeholder='Limite'><input name='closing_day' type='number' min='1' max='31' placeholder='Dia de fechamento' required><input name='due_day' type='number' min='1' max='31' placeholder='Dia de vencimento' required><button>Cadastrar cartão</button></form></div>
<div class='card'><h2>Cartões</h2>{carditems}</div><div class='card full'><h2>Nova compra</h2><form method='post' action='/cards/purchase'><select name='credit_card_id' required>{cardopts}</select><select name='category_id' required>{catopts}</select><input name='description' placeholder='Descrição' required><input name='total_amount' inputmode='decimal' placeholder='Valor total' required><input name='installment_count' type='number' min='1' max='120' value='1' required><button>Registrar compra</button></form></div></div>"""
        return HTMLResponse(page_shell('Cartões',body))
    finally: db.close()


@app.post('/cards')
def create_card(name:str=Form(...), institution:str=Form(''), brand:str=Form(''), credit_limit:str=Form('0'), closing_day:int=Form(...), due_day:int=Form(...)):
    if not 1<=closing_day<=31 or not 1<=due_day<=31: raise HTTPException(400,'Dias devem estar entre 1 e 31.')
    db=SessionLocal()
    try:
        db.add(CreditCard(name=name.strip(),institution=institution.strip() or None,brand=brand.strip() or None,credit_limit=converter_decimal(credit_limit),closing_day=closing_day,due_day=due_day))
        db.commit()
    except Exception: db.rollback(); raise
    finally: db.close()
    return RedirectResponse('/cards',303)


def add_months(d, months):
    y=d.year+(d.month-1+months)//12; m=(d.month-1+months)%12+1
    import calendar
    return date(y,m,min(d.day,calendar.monthrange(y,m)[1]))


@app.post('/cards/purchase')
def create_purchase(credit_card_id:int=Form(...), category_id:int=Form(...), description:str=Form(...), total_amount:str=Form(...), installment_count:int=Form(1)):
    valor=converter_decimal(total_amount)
    if valor<=0 or installment_count<1 or installment_count>120: raise HTTPException(400,'Compra ou número de parcelas inválido.')
    db=SessionLocal()
    try:
        card=db.query(CreditCard).filter(CreditCard.id==credit_card_id,CreditCard.is_active==True).first()
        cat=db.query(Category).filter(Category.id==category_id,Category.category_type=='EXPENSE',Category.is_active==True).first()
        if not card or not cat: raise HTTPException(400,'Cartão ou categoria inválidos.')
        purchase=CreditCardPurchase(credit_card_id=credit_card_id,category_id=category_id,description=description.strip(),purchase_date=date.today(),total_amount=valor,installment_count=installment_count,is_installment=installment_count>1)
        db.add(purchase); db.flush()
        base=(valor/Decimal(installment_count)).quantize(Decimal('0.01'))
        remainder=valor-base*installment_count
        for n in range(1,installment_count+1):
            amount=base+(remainder if n==installment_count else Decimal('0'))
            due=add_months(date.today(),n-1)
            db.add(Installment(purchase_id=purchase.id,installment_number=n,total_installments=installment_count,amount=amount,due_date=due,status='OPEN'))
        db.commit()
    except Exception: db.rollback(); raise
    finally: db.close()
    return RedirectResponse('/cards',303)


@app.get('/investments', response_class=HTMLResponse)
def investments_page():
    db=SessionLocal()
    try:
        insts=db.query(InvestmentInstitution).filter(InvestmentInstitution.is_active==True).order_by(InvestmentInstitution.name).all()
        investments=db.query(Investment).filter(Investment.is_active==True).order_by(Investment.name).all()
        opts=''.join(f"<option value='{i.id}'>{i.name}</option>" for i in insts)
        items=''.join(f"<div class='item'><span><b>{i.name}</b><br><small class='muted'>{i.investment_type or ''} · {i.ticker or ''}</small></span><span class='yellow'>{dinheiro(i.current_value)}</span></div>" for i in investments) or "<p class='muted'>Nenhum investimento cadastrado.</p>"
        body=f"""<h1>Investimentos</h1><div class='grid'><div class='card'><h2>Novo investimento</h2><form method='post' action='/investments'><input name='name' placeholder='Nome' required><input name='investment_type' placeholder='Tipo'><input name='ticker' placeholder='Ticker'><select name='institution_id'>{opts}</select><input name='current_value' inputmode='decimal' placeholder='Valor atual' required><input name='quantity' inputmode='decimal' placeholder='Quantidade'><input name='average_price' inputmode='decimal' placeholder='Preço médio'><button>Cadastrar investimento</button></form></div><div class='card'><h2>Carteira</h2>{items}</div></div>"""
        return HTMLResponse(page_shell('Investimentos',body))
    finally: db.close()


@app.post('/investments')
def create_investment(name:str=Form(...), investment_type:str=Form(''), ticker:str=Form(''), institution_id:int=Form(...), current_value:str=Form('0'), quantity:str=Form('0'), average_price:str=Form('0')):
    cv=converter_decimal(current_value); q=converter_decimal(quantity); ap=converter_decimal(average_price)
    if cv<0 or q<0: raise HTTPException(400,'Valores inválidos.')
    db=SessionLocal()
    try:
        if not db.query(InvestmentInstitution).filter(InvestmentInstitution.id==institution_id,InvestmentInstitution.is_active==True).first(): raise HTTPException(400,'Instituição inválida.')
        db.add(Investment(name=name.strip(),investment_type=investment_type.strip() or None,ticker=ticker.strip() or None,institution_id=institution_id,current_value=cv,quantity=q,average_price=ap,currency='BRL'))
        db.commit()
    except Exception: db.rollback(); raise
    finally: db.close()
    return RedirectResponse('/investments',303)


@app.get('/goals', response_class=HTMLResponse)
def goals_page():
    db=SessionLocal()
    try:
        goals=db.query(FinancialGoal).filter(FinancialGoal.is_active==True).order_by(FinancialGoal.target_date.asc().nullslast()).all()
        items=''.join(f"<div class='item'><span><b>{g.name}</b><br><small class='muted'>{dinheiro(g.current_amount)} de {dinheiro(g.target_amount)}</small></span><span>{(Decimal(str(g.current_amount or 0))/Decimal(str(g.target_amount or 1))*100).quantize(Decimal('0.1'))}%</span></div>" for g in goals) or "<p class='muted'>Nenhuma meta cadastrada.</p>"
        body=f"""<h1>Metas financeiras</h1><div class='grid'><div class='card'><h2>Nova meta</h2><form method='post' action='/goals'><input name='name' placeholder='Ex.: Reserva de emergência' required><input name='target_amount' inputmode='decimal' placeholder='Valor alvo' required><input name='current_amount' inputmode='decimal' placeholder='Valor atual' value='0'><input name='target_date' type='date'><input name='category' placeholder='Categoria'><button>Criar meta</button></form></div><div class='card'><h2>Progresso</h2>{items}</div></div>"""
        return HTMLResponse(page_shell('Metas',body))
    finally: db.close()


@app.post('/goals')
def create_goal(name:str=Form(...), target_amount:str=Form(...), current_amount:str=Form('0'), target_date:str=Form(''), category:str=Form('')):
    target=converter_decimal(target_amount); current=converter_decimal(current_amount)
    if target<=0 or current<0: raise HTTPException(400,'Valores da meta inválidos.')
    td=date.fromisoformat(target_date) if target_date else None
    db=SessionLocal()
    try:
        db.add(FinancialGoal(name=name.strip(),target_amount=target,current_amount=current,target_date=td,category=category.strip() or None))
        db.commit()
    except Exception: db.rollback(); raise
    finally: db.close()
    return RedirectResponse('/goals',303)


@app.get('/health', response_class=HTMLResponse)
def health_page():
    db=SessionLocal()
    try:
        accounts=get_accounts(db)
        incomes=db.query(Income).all(); expenses=db.query(Expense).all(); investments=db.query(Investment).filter(Investment.is_active==True).all()
        inc=sum((Decimal(str(x.amount or 0)) for x in incomes),Decimal('0')); exp=sum((Decimal(str(x.amount or 0)) for x in expenses),Decimal('0'))
        inv=sum((Decimal(str(x.current_value or 0)) for x in investments),Decimal('0'))
        fixed=db.query(RecurringExpense).filter(RecurringExpense.is_active==True).all()
        fixed_month=sum((Decimal(str(x.amount or 0)) for x in fixed),Decimal('0'))
        savings=((inc-exp)/inc*Decimal('100')) if inc else None
        score=Decimal('0')
        if accounts: score+=Decimal('20')
        if inc and exp<=inc: score+=Decimal('20')
        if inv>0: score+=Decimal('20')
        if fixed_month<=inc*Decimal('0.5') if inc else False: score+=Decimal('20')
        if savings is not None and savings>=Decimal('10'): score+=Decimal('20')
        score=score.quantize(Decimal('0.1'))
        savings_txt=f'{savings.quantize(Decimal("0.1"))}%' if savings is not None else 'N/D'
        body=f"""<h1>Saúde financeira</h1><div class='grid'><div class='card'><div class='muted'>Indicador atual</div><div style='font-size:42px' class='yellow'>{score}</div><p class='muted'>Indicador determinístico inicial. N/D é usado quando não há dados suficientes.</p></div><div class='card'><div class='muted'>Taxa de poupança</div><div style='font-size:30px'>{savings_txt}</div><p class='muted'>Receitas: {dinheiro(inc)} · Despesas: {dinheiro(exp)}</p></div><div class='card'><div class='muted'>Investimentos</div><div style='font-size:30px'>{dinheiro(inv)}</div></div><div class='card'><div class='muted'>Despesas recorrentes</div><div style='font-size:30px'>{dinheiro(fixed_month)}</div></div></div>"""
        return HTMLResponse(page_shell('Saúde financeira',body))
    finally: db.close()


@app.get('/export.json')
def export_json():
    db=SessionLocal()
    try:
        def rows(model, fields):
            return [{f: (getattr(x,f).isoformat() if isinstance(getattr(x,f),(date,datetime)) else str(getattr(x,f)) if isinstance(getattr(x,f),Decimal) else getattr(x,f)) for f in fields} for x in db.query(model).all()]
        data={
            'exported_at':datetime.utcnow().isoformat()+'Z',
            'accounts':rows(Account,['id','name','institution','account_type','initial_balance','is_active']),
            'categories':rows(Category,['id','name','category_type','parent_id','is_active']),
            'income':rows(Income,['id','account_id','category_id','description','amount','date','income_type','notes']),
            'expenses':rows(Expense,['id','account_id','category_id','description','amount','date','notes']),
            'transfers':rows(Transfer,['id','source_account_id','destination_account_id','amount','date','description']),
            'credit_cards':rows(CreditCard,['id','name','institution','brand','credit_limit','closing_day','due_day','annual_fee','reward_program_id','is_active']),
            'investments':rows(Investment,['id','institution_id','name','investment_type','ticker','currency','current_value','quantity','average_price','interest_rate','start_date','maturity_date','is_active']),
            'goals':rows(FinancialGoal,['id','name','target_amount','current_amount','start_date','target_date','category','is_active']),
        }
        return JSONResponse(data,headers={'Content-Disposition':'attachment; filename="gastei-export.json"'})
    finally: db.close()


# ============================================================
# RECOMPENSAS
# ============================================================

@app.get('/rewards', response_class=HTMLResponse)
def rewards_page():
    db=SessionLocal()
    try:
        programs=db.query(RewardProgram).filter(RewardProgram.is_active==True).order_by(RewardProgram.name).all()
        cards=db.query(CreditCard).filter(CreditCard.is_active==True).order_by(CreditCard.name).all()
        cardopts=''.join(f"<option value='{c.id}'>{c.name}</option>" for c in cards)
        items=''.join(f"<div class='item'><span><b>{p.name}</b><br><small class='muted'>{p.reward_type} · {p.unit_name or 'unidades'}</small></span><span>{dinheiro(p.estimated_unit_value or 0)}/un.</span></div>" for p in programs) or "<p class='muted'>Nenhum programa cadastrado.</p>"
        body=f"""<h1>Recompensas</h1><div class='grid'><div class='card'><h2>Novo programa</h2><form method='post' action='/rewards'><input name='name' placeholder='Ex.: Pontos do cartão' required><input name='reward_type' placeholder='Tipo' value='POINTS' required><input name='unit_name' placeholder='Unidade' value='pontos'><input name='estimated_unit_value' inputmode='decimal' placeholder='Valor estimado por unidade' value='0'><button>Cadastrar programa</button></form></div><div class='card'><h2>Programas</h2>{items}</div><div class='card full'><h2>Regra de cartão</h2><form method='post' action='/rewards/rule'><select name='credit_card_id' required>{cardopts}</select><select name='reward_program_id' required>{''.join(f"<option value='{p.id}'>{p.name}</option>" for p in programs)}</select><input name='points_per_unit' inputmode='decimal' placeholder='Pontos por R$ 1,00' required><button>Salvar regra</button></form></div></div>"""
        return HTMLResponse(page_shell('Recompensas',body))
    finally: db.close()


@app.post('/rewards')
def create_reward(name:str=Form(...), reward_type:str=Form('POINTS'), unit_name:str=Form('pontos'), estimated_unit_value:str=Form('0')):
    db=SessionLocal()
    try:
        db.add(RewardProgram(name=name.strip(),reward_type=reward_type.strip() or 'POINTS',unit_name=unit_name.strip() or None,estimated_unit_value=converter_decimal(estimated_unit_value)))
        db.commit()
    except Exception: db.rollback(); raise
    finally: db.close()
    return RedirectResponse('/rewards',303)


@app.post('/rewards/rule')
def create_reward_rule(credit_card_id:int=Form(...), reward_program_id:int=Form(...), points_per_unit:str=Form(...)):
    points=converter_decimal(points_per_unit)
    if points<0: raise HTTPException(400,'A pontuação não pode ser negativa.')
    db=SessionLocal()
    try:
        if not db.query(CreditCard).filter(CreditCard.id==credit_card_id,CreditCard.is_active==True).first(): raise HTTPException(400,'Cartão inválido.')
        if not db.query(RewardProgram).filter(RewardProgram.id==reward_program_id,RewardProgram.is_active==True).first(): raise HTTPException(400,'Programa inválido.')
        db.add(CardRewardRule(credit_card_id=credit_card_id,reward_program_id=reward_program_id,points_per_unit=points))
        db.commit()
    except Exception: db.rollback(); raise
    finally: db.close()
    return RedirectResponse('/rewards',303)


# ============================================================
# AUTOMÓVEIS
# ============================================================

@app.get('/vehicles', response_class=HTMLResponse)
def vehicles_page():
    db=SessionLocal()
    try:
        vehicles=db.query(Vehicle).filter(Vehicle.is_active==True).order_by(Vehicle.brand,Vehicle.model).all()
        opts=''.join(f"<option value='{v.id}'>{v.brand} {v.model}</option>" for v in vehicles)
        items=''.join(f"<div class='item'><span><b>{v.brand} {v.model}</b><br><small class='muted'>{v.year or ''} · {v.license_plate or ''} · {v.fuel_type or ''}</small></span><span>{v.current_mileage or 0} km</span></div>" for v in vehicles) or "<p class='muted'>Nenhum veículo cadastrado.</p>"
        body=f"""<h1>Automóveis</h1><div class='grid'><div class='card'><h2>Novo veículo</h2><form method='post' action='/vehicles'><input name='brand' placeholder='Marca' required><input name='model' placeholder='Modelo' required><input name='version' placeholder='Versão'><input name='year' type='number' placeholder='Ano'><input name='license_plate' placeholder='Placa'><input name='current_mileage' inputmode='decimal' placeholder='Quilometragem'><input name='fuel_type' placeholder='Combustível'><input name='average_consumption' inputmode='decimal' placeholder='Consumo médio'><button>Cadastrar veículo</button></form></div><div class='card'><h2>Veículos</h2>{items}</div><div class='card full'><h2>Manutenção</h2><form method='post' action='/vehicles/maintenance'><select name='vehicle_id' required>{opts}</select><input name='component' placeholder='Componente'><input name='service' placeholder='Serviço' required><input name='amount' inputmode='decimal' placeholder='Valor' required><input name='mileage' inputmode='decimal' placeholder='Quilometragem'><button>Registrar manutenção</button></form></div></div>"""
        return HTMLResponse(page_shell('Automóveis',body))
    finally: db.close()


@app.post('/vehicles')
def create_vehicle(brand:str=Form(...), model:str=Form(...), version:str=Form(''), year:int|None=Form(None), license_plate:str=Form(''), current_mileage:str=Form('0'), fuel_type:str=Form(''), average_consumption:str=Form('0')):
    db=SessionLocal()
    try:
        db.add(Vehicle(brand=brand.strip(),model=model.strip(),version=version.strip() or None,year=year,license_plate=license_plate.strip().upper() or None,current_mileage=converter_decimal(current_mileage),fuel_type=fuel_type.strip() or None,average_consumption=converter_decimal(average_consumption)))
        db.commit()
    except Exception: db.rollback(); raise
    finally: db.close()
    return RedirectResponse('/vehicles',303)


@app.post('/vehicles/maintenance')
def create_maintenance(vehicle_id:int=Form(...), component:str=Form(''), service:str=Form(...), amount:str=Form(...), mileage:str=Form('0')):
    valor=converter_decimal(amount)
    if valor<0: raise HTTPException(400,'Valor inválido.')
    db=SessionLocal()
    try:
        if not db.query(Vehicle).filter(Vehicle.id==vehicle_id,Vehicle.is_active==True).first(): raise HTTPException(400,'Veículo inválido.')
        db.add(VehicleMaintenance(vehicle_id=vehicle_id,date=date.today(),mileage=converter_decimal(mileage),component=component.strip() or None,service=service.strip(),amount=valor))
        db.commit()
    except Exception: db.rollback(); raise
    finally: db.close()
    return RedirectResponse('/vehicles',303)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

@app.get('/settings', response_class=HTMLResponse)
def settings_page():
    body="""<h1>Configurações</h1><div class='grid'><div class='card'><h2>Dados</h2><p class='muted'>O banco PostgreSQL do Render continua sendo a fonte principal. Use Exportar para gerar uma cópia legível em JSON.</p><a href='/export.json'><button>Exportar dados</button></a></div><div class='card'><h2>Privacidade</h2><p class='muted'>O Gastei não solicita credenciais bancárias. Dados financeiros ficam no banco configurado pelo aplicativo.</p></div></div>"""
    return HTMLResponse(page_shell('Configurações',body))


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
