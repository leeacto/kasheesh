# Getting Started
1. Requirements:
* Python v3.8
2. Run `python3 -m venv .venv` to create virtual environment
3. Run `. .venv/bin/activate` to activate environment
4. Run `pip install -r requirements.txt` to install packages
5. Run `flask run` to run local server at http://127.0.0.1:5000
6. Run `flask seed` to seed database

# API
1. `/users/:id/transactions` returns all Payments and Returns for a given User ID in whole USD
2. `/merchant-type-codes/:id/net-purchases` returns daily net purchases (Payments less Returns) for a given Merchant Type Code
  a. Days without activity are omitted
  b. Days where Net Purchases equal $0 means that the delta was under $1


# Development Notes
* SQLite was chosen as the local database. The reason is that it is already part of Python 3, so it's easy to use. If production would like something more robust like PostgreSql or MySQL, configuration will need to be done.
* Data is loaded via the `seed_db` method. This method employs a CSV reader and checks the `transaction_type` field to determine which table the record should be inserted into. In order to simplify aggregation, `amount_cents` values for the `returns` table are entered as negative. Thus, summing between the tables will not require conversion.
* The two tables, `purchases` and `returns` were created based on the instructions. This data looks so similar, that I would likely have created a single `transactions` table. This type of table would scale more easily by typically needing a single query or omit queries that use `UNION` which can be expensive at scale.
* Business logic for endpoints have been moved to helper methods. I often separate this work to increase testability and allow for potential reuse of code.
* In order to return this challenge in a timely manner, tests have been skipped. If I were to write them, I would unit test the helper methods which make use of the ORM. I would have positive and negative tests to ensure that calculations and filtering are correct.
