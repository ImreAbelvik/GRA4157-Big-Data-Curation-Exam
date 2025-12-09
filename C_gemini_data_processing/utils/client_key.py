import os
from dotenv import load_dotenv

load_dotenv()
lst_gemini_keys = [
    os.getenv("GOOGLE_API_I"),
    os.getenv("GOOGLE_API_II"),
    os.getenv("GOOGLE_API_III"),
    os.getenv("GOOGLE_API_IV")
]

def switch_client_key():
    lst_gemini_keys.append(lst_gemini_keys.pop(0))
    return lst_gemini_keys[0]