from IPython import embed
from collections import defaultdict
import csv
from datetime import datetime
import json

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, Date

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
                db.session.add(
                        Return(user_id=row['user_id'],
                                 merchant_type_code=row['merchant_type_code'],
                                 amount_cents=row['amount_cents'] * -1,
                                 datetime=dt))
            else:
                print(f"Unknown Transaction Type: {row['transaction_type']}")
        db.session.commit()

with app.app_context():
    db.create_all()
    # seed_db()


@app.route("/users/<int:id>/transactions")
def user_transactions(id):
    pq = Purchase.query.filter(Purchase.user_id==id).all()
    rq = Return.query.filter(Return.user_id==id).all()
    return [{
            "type": PURCHASE if isinstance(t, Purchase) else RETURN,
            "user_id": t.user_id, 
            "merchant_type_code": t.merchant_type_code,
            "amount_in_dollars": t.amount_cents // 100,
            "datetime": t.iso_date_str}
            for t in pq + rq]


@app.route("/merchant-type-codes/<int:id>/net-purchases")
def net_purchases(id):
    # select sum(amount_cents), merchant_type_code, date(datetime) from purchases group by  merchant_type_code, date(datetime
    pq = Purchase.query.with_entities(func.DATE(Purchase.datetime), func.sum(Purchase.amount_cents)).filter(Purchase.merchant_type_code==id).group_by(func.DATE(Purchase.datetime)).all()
    rq = Return.query.with_entities(func.DATE(Return.datetime), func.sum(Return.amount_cents)).filter(Return.merchant_type_code==id).group_by(func.DATE(Return.datetime)).all()
    t = pq + rq
    d = defaultdict(int)
    for x in t:
        d[x[0]] += x[1]

    return [{"merchant_type_code": id, "net_amount_in_dollars": amt // 100, "date": date}
            for date, amt in d.items() if amt // 100 != 0]
