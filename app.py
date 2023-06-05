from collections import defaultdict
import csv
from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

# create the extension
db = SQLAlchemy()
# create the app
app = Flask(__name__)
# configure the SQLite database  relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kasheesh.db"
# initialize the app with the extension
db.init_app(app)

PURCHASE = 'PurchaseActivity'
RETURN = 'ReturnActivity'


class Purchase(db.Model):

    __tablename__ = 'purchases'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, index=True, nullable=False)
    merchant_type_code = db.Column(db.Integer, index=True, nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)

    @property
    def iso_date_str(self):
        return self.datetime.isoformat()


class Return(db.Model):

    __tablename__ = 'returns'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, index=True, nullable=False)
    merchant_type_code = db.Column(db.Integer, index=True, nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)

    @property
    def iso_date_str(self):
        return self.datetime.isoformat()


@app.cli.command('seed')
def seed_db():
    with open("combined_transactions.csv") as f:
        print("SEEDING")
        reader = csv.DictReader(f)
        for row in reader:
            dt = row['datetime'].replace('T', ' ')
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S.%f')
            if row['transaction_type'] == PURCHASE:
                db.session.add(
                        Purchase(user_id=row['user_id'],
                                 merchant_type_code=row['merchant_type_code'],
                                 amount_cents=row['amount_cents'],
                                 datetime=dt))
            elif row['transaction_type'] == RETURN:
                return_rec = Return(user_id=row['user_id'],
                                    merchant_type_code=row['merchant_type_code'],
                                    amount_cents=int(row['amount_cents']) * -1,
                                    datetime=dt)
                db.session.add(return_rec)
            else:
                print(f"Unknown Transaction Type: {row['transaction_type']}")
        db.session.commit()

with app.app_context():
    db.create_all()


def transactions_by_user(user_id):
    purchases = Purchase.query.filter(Purchase.user_id==user_id).all()
    returns = Return.query.filter(Return.user_id==user_id).all()
    return [{
            "type": PURCHASE if isinstance(t, Purchase) else RETURN,
            "user_id": t.user_id, 
            "merchant_type_code": t.merchant_type_code,
            "amount_in_dollars": int(t.amount_cents // 100),
            "datetime": t.iso_date_str}
            for t in purchases + returns]


def merchant_type_net_purchases(merchant_type_code):
    purchases = (Purchase.query.with_entities(func.DATE(Purchase.datetime), func.sum(Purchase.amount_cents))
                         .filter(Purchase.merchant_type_code==merchant_type_code)
                         .group_by(func.DATE(Purchase.datetime))
                         .all())
    returns = (Return.query.with_entities(func.DATE(Return.datetime), func.sum(Return.amount_cents))
                     .filter(Return.merchant_type_code==merchant_type_code)
                     .group_by(func.DATE(Return.datetime))
                     .all())
    transactions = purchases + returns
    transactions_dict = defaultdict(int)
    for date, amt in transactions:
        transactions_dict[date] += amt

    return [{"merchant_type_code": merchant_type_code, "net_amount_in_dollars": int(amt // 100), "date": date}
            for date, amt in transactions_dict.items()]


@app.route("/users/<int:id>/transactions")
def user_transactions(id):
    return transactions_by_user(id)


@app.route("/merchant-type-codes/<int:id>/net-purchases")
def net_purchases(id):
    return merchant_type_net_purchases(id)
