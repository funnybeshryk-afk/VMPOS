from sqlalchemy import inspect, text

from app.database.database import engine


def apply_migrations():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    migrations = {
        "sales": {
            "payment_method": (
                "VARCHAR(20) NOT NULL DEFAULT 'cash'"
            ),
            "paid_amount": (
                "FLOAT NOT NULL DEFAULT 0"
            ),
            "change_amount": (
                "FLOAT NOT NULL DEFAULT 0"
            ),
            "status": (
                "VARCHAR(20) NOT NULL DEFAULT 'completed'"
            ),
            "cash_amount": (
                "FLOAT NOT NULL DEFAULT 0"
            ),
            "card_amount": (
                "FLOAT NOT NULL DEFAULT 0"
            ),
        },
        "stock_receipts": {
            "supplier_id": "INTEGER",
            "supplier_name": "VARCHAR(255)",
        },
        "customers": {
            "debt_amount": (
                "FLOAT NOT NULL DEFAULT 0"
            ),
            "debt_date": "DATE",
        },
        "shifts": {
            "cashier_user_id": "INTEGER",
        },
    }

    with engine.begin() as connection:
        for table_name, new_columns in migrations.items():
            if table_name not in table_names:
                continue

            existing_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }

            newly_added_columns = set()

            for column_name, column_definition in new_columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} "
                            f"{column_definition}"
                        )
                    )
                    newly_added_columns.add(column_name)

            # cash_amount/card_amount birinchi marta qo'shilganda eski
            # savdolarda ikkalasi ham 0 bo'lib qoladi — hisobotlarda
            # eski kunlar naqd/karta jamidan yo'qolib qoladi. Eski
            # yozuvlarni payment_method asosida qayta tiklaymiz: bu
            # ustunlar paydo bo'lishidan oldin "mixed" umuman
            # saqlanmagan (eski xato tufayli har doim "cash" yoki
            # "card" bo'lib yozilgan), shuning uchun bu tiklash aniq.
            if (
                table_name == "sales"
                and "cash_amount" in newly_added_columns
            ):
                connection.execute(
                    text(
                        "UPDATE sales SET "
                        "cash_amount = CASE "
                        "WHEN payment_method = 'card' THEN 0 "
                        "ELSE total_amount END, "
                        "card_amount = CASE "
                        "WHEN payment_method = 'card' THEN total_amount "
                        "ELSE 0 END"
                    )
                )
