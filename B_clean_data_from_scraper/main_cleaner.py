import os
import json
import sqlite3
import pdfplumber

conn = sqlite3.connect("../Nexus.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT,
    date TEXT,
    market TEXT,
    issuer_id TEXT,
    link TEXT,
    message TEXT,
    pdf_text TEXT
);
""")
conn.commit()

sql_insert = """
INSERT INTO notifications (company_name, date, market, issuer_id, link, message, pdf_text)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

JSON_DATA_PATH = "../A_scrape_oslo_bors_web_page/data"
DOWNLOWDED_DATA_PATH = "../A_scrape_oslo_bors_web_page/data_"

json_files = os.listdir(JSON_DATA_PATH)

data = []
for file_name in json_files:
    print(f"Starting to process {file_name}")

    file_path = os.path.join(JSON_DATA_PATH, file_name)
    
    with open(file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    primary_folder_name = json_data[0]["IssuerID"]

    for msg_data in json_data:
        message_folder_name = msg_data["link"][1:].replace("/", "_")

        message_folder_path = os.path.join(DOWNLOWDED_DATA_PATH, primary_folder_name, message_folder_name)

        if not os.path.isdir(message_folder_path):
            print("Missing folder:", message_folder_path)
            continue

        message_folder = os.listdir(message_folder_path)

        # skip if error in the file...
        if "error" in message_folder:
            continue

        with open(os.path.join(message_folder_path, "document_text.txt"), "r") as message:
            main_message = message.read().strip()

        all_text = ""
        for message_file in message_folder:
            if message_file.endswith(".pdf"):
                with pdfplumber.open(os.path.join(message_folder_path, message_file)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            all_text += page_text

        cursor.execute(sql_insert, (file_name, msg_data["date"], msg_data["market"], msg_data["IssuerID"], message_folder_name, main_message, all_text))
    
    conn.commit()
conn.close()