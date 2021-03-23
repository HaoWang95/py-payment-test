from .connection import metadata, engine, Base
import sqlalchemy

Users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("first", sqlalchemy.String),
    sqlalchemy.Column("last", sqlalchemy.String),
    sqlalchemy.Column("email", sqlalchemy.String),
    sqlalchemy.Column("password", sqlalchemy.String)
)

PaymentAccount = sqlalchemy.Table(
    "payment_accounts",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key = True),
    sqlalchemy.Column("user", sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("account_number", sqlalchemy.String),
    sqlalchemy.Column("deposit", sqlalchemy.Float),
    sqlalchemy.Column("account_status", sqlalchemy.Boolean)
)


PaymentRecord = sqlalchemy.Table(
    "payment_records",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key = True),
    sqlalchemy.Column("sender", sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("receiver", sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("sender_account", sqlalchemy.ForeignKey("payment_accounts.id")),
    sqlalchemy.Column("receiver_account", sqlalchemy.ForeignKey("payment_accounts.id")),
    sqlalchemy.Column("amount", sqlalchemy.Float),
    sqlalchemy.Column("transactionFee", sqlalchemy.Float),
    sqlalchemy.Column("is_deleted", sqlalchemy.String),
    sqlalchemy.Column("create_time", sqlalchemy.Date),
)

metadata.create_all(engine)


class UserModel(Base):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, unique = True)
    email = sqlalchemy.Column(sqlalchemy.String)
    first = sqlalchemy.Column(sqlalchemy.String)
    last = sqlalchemy.Column(sqlalchemy.String)
    password = sqlalchemy.Column(sqlalchemy.String)


class AccountModel(Base):
    __tablename__ = 'payment_accounts'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    userid = sqlalchemy.Column(sqlalchemy.ForeignKey("users.id"))
    account = sqlalchemy.Column(sqlalchemy.String)
    deposit = sqlalchemy.Column(sqlalchemy.Integer)
    account_status = sqlalchemy.Column(sqlalchemy.Boolean)


class PaymentRecordModel(Base):
    __tablename__ = 'payment_records'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    sender = sqlalchemy.Column(sqlalchemy.ForeignKey("users.id"))
    receiver = sqlalchemy.Column(sqlalchemy.ForeignKey("users.id"))
    sender_account = sqlalchemy.Column(sqlalchemy.ForeignKey("payment_accounts.id"))
    receiver_account = sqlalchemy.Column(sqlalchemy.ForeignKey("payment_accounts.id"))
    amount = sqlalchemy.Column(sqlalchemy.Float)
    transactionFee = sqlalchemy.Column(sqlalchemy.Float)
    status = sqlalchemy.Column(sqlalchemy.String)
    create_time = sqlalchemy.Column(sqlalchemy.Date)
