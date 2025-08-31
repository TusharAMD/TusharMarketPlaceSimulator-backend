import os
from dotenv import load_dotenv
load_dotenv()
from mistralai import Mistral
from pydantic import BaseModel, ValidationError
import json

class Seller:
    def __init__(self, seller_name):
        self.name = seller_name
        self.dialog_list = []
        self.description = ""
        self.items_available_with_price = {}

class SellerResponse(BaseModel):
    seller_response: str
    purchase_successful: bool
    item_purchased: str
    deal_price: int

seller_names = [
    "bread_seller_1",
    "meat_seller_1",
    "vegetable_seller_1",
    "vegetable_seller_2",
    "fish_seller_1",
    "small_vegetable_seller_1"
]


def build_seller_context(seller: Seller):
    items = "\n".join([f"- {item}: {price} coins" for item, price in seller.items_available_with_price.items()])
    dialog_history = "\n".join([f'{d[0]}: {d[1]}' for d in seller.dialog_list])

    context = f"""
You are {seller.name}.
{seller.description}

You would return purchase_successful bool as true only when item is purchased. And only  when purchase_successful is true item_purchased will be populated and deal_price will be populated.
Else purchase_successful will be false and item_purchased will be empty string and deal_price will be None.



Items you sell (with prices):
{items if items else "No items available."}

Dialog so far:
{dialog_history if dialog_history else "No previous dialog."}

Important: Always respond ONLY in strict JSON format like this:
Do not include anything outside JSON.
    """
    return context


sellers = {name: Seller(name) for name in seller_names}
sellers["bread_seller_1"].description = "You are a bread seller. You will not entertain any other questions apart from trading breads. Keep the responses short like within 10-15 words. If anything else is asked just say I am bread seller I have no idea about it."
sellers["bread_seller_1"].items_available_with_price = {"White Bread":10,"Brown Bread":15,"Sour Dough":30,}

print(dir(sellers["bread_seller_1"]))

print(build_seller_context(sellers["bread_seller_1"]))



API_KEY = os.getenv("MISTRAL_API_KEY")

client = Mistral(api_key=API_KEY)

def get_seller_response(seller: Seller, player_input: str):
    context = build_seller_context(seller)
    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": player_input}
    ]

    response = client.chat.parse(
        model="mistral-tiny", 
        messages=messages,
        temperature=0.3,
        response_format=SellerResponse,
    )

    raw_reply = response.choices[0].message.content
    try:
        seller_reply_json = json.loads(raw_reply)
        validated = SellerResponse(**seller_reply_json)
    except (json.JSONDecodeError, ValidationError):
        print("Failed")
        validated = SellerResponse(seller_response=raw_reply)
    
    seller.dialog_list.append(("Player", player_input))
    seller.dialog_list.append((seller.name, validated.seller_response))
    return validated


while True:
    print("====")
    player_input = input()
    reply = get_seller_response(sellers["bread_seller_1"], player_input)
    print(reply)


'''
{{
  "seller_response": "<your reply here>",
  "purchase_successful": "<Boolean>",
  "item_purchased": "<ItemName>",
  "deal_price": "<Price>"
}}
'''