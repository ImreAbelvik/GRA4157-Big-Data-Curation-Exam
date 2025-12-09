from google import genai
from pydantic import BaseModel
import json

class InsiderTransactions(BaseModel):
    insider_role: str
    shares_held_before: int
    shares_acquired_or_sold: int
    transaction_type: str
    price_per_share: float
    total_shares_after_transaction: int
    salary_related: bool
    regulatory_context: str

def get_response_gemini(client_key, prompt: str) -> list[InsiderTransactions] | None:
    client = genai.Client(api_key=client_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config={
                "temperature": 0.4,
                "response_mime_type": "application/json",
                "response_json_schema": {
                    "type": "array",
                    "items": InsiderTransactions.model_json_schema()
                },
            },
        )

        transactions = [InsiderTransactions.model_validate(item) 
                        for item in json.loads(response.text)]

        return transactions
    
    except Exception as e:
        print("Gemini returned invalid JSON or wrong schema:")
        return None
