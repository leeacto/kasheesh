from IPython import embed
import csv
from datetime import datetime
import json

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

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

    def __json__(self):
        return json.dumps({
            "type": PURCHASE,
            "user_id": self.user_id, 
            "merchant_type_code": self.merchant_type_code,
            "amount_in_dollars": self.amount_cents % 100,
            "datetime": str(self.datetime)})

class Return(db.Model):

    __tablename__ = 'returns'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, index=True, nullable=False)
    merchant_type_code = db.Column(db.Integer, index=True, nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)

    def __json__(self):
        return json.dumps({
            "type": RETURN,
            "user_id": self.user_id, 
            "merchant_type_code": self.merchant_type_code,
            "amount_in_dollars": self.amount_cents % 100,
            "datetime": str(self.datetime)})


with app.app_context():
    db.create_all()
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
                                 amount_cents=row['amount_cents'],
                                 datetime=dt))
            else:
                print(f"Unknown Transaction Type: {row['transaction_type']}")
        db.session.commit()


@app.route("/users/<int:id>/transactions")
def user_transactions(id):
    pq = Purchase.query.filter(Purchase.user_id==id).all()
    rq = Return.query.filter(Return.user_id==id).all()
    return [{
            "type": PURCHASE if isinstance(t, Purchase) else RETURN,
            "user_id": t.user_id, 
            "merchant_type_code": t.merchant_type_code,
            "amount_in_dollars": t.amount_cents // 100,
            "datetime": t.datetime.isoformat()}
            for t in pq + rq]
