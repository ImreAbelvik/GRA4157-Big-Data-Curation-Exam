import sqlite3
import pandas as pd
import time

from utils.prompt import build_prompt
from utils.gemini_functions import get_response_gemini
from utils.client_key import switch_client_key


conn = sqlite3.connect("../Nexus.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS insider_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insider_role TEXT NOT NULL,
    shares_held_before INTEGER NOT NULL,
    shares_acquired_or_sold INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    price_per_share REAL NOT NULL,
    total_shares_after_transaction INTEGER NOT NULL,
    salary_related INTEGER NOT NULL,
    regulatory_context TEXT NOT NULL,
    notification_id INTEGER NOT NULL,
    FOREIGN KEY (notification_id) REFERENCES notifications(id)
);
""")


sql_insert = """
INSERT INTO insider_transactions (
    insider_role,
    shares_held_before,
    shares_acquired_or_sold,
    transaction_type,
    price_per_share,
    total_shares_after_transaction,
    salary_related,
    regulatory_context,
    notification_id
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

df = pd.read_sql_query("SELECT * FROM notifications", conn)


error_count = 0

# I want to use iterrows because I want it to run slowly.
# The API limits my requests, so it's better to process them one by one.
for index, row in df.iterrows():
    if error_count >= 100:
        break

    cursor.execute(
    "SELECT 1 FROM insider_transactions WHERE notification_id = ? LIMIT 1;",
    (row["id"],)
    )
    exists = cursor.fetchone()

    if exists:
        print(f"Skipping notification_id {row['id']} (already processed)")
        continue


    client_key = switch_client_key()
    prompt = build_prompt(row["message"], row["pdf_text"])
    response = get_response_gemini(client_key=client_key, prompt=prompt)

    if response:
        for transaction in response:
            data = (
                transaction.insider_role,
                transaction.shares_held_before,
                transaction.shares_acquired_or_sold,
                transaction.transaction_type,
                transaction.price_per_share,
                transaction.total_shares_after_transaction,
                1 if transaction.salary_related else 0,
                transaction.regulatory_context,
                row["id"]
            )

            cursor.execute(sql_insert, data)
    else:
        time.sleep(100)
        error_count += 1
        with open("logs/logs.txt", "a") as f:
            f.write(f"Error with: {row['id']}\n")

    conn.commit()
    time.sleep(2.5)

conn.close()