from fastapi import FastAPI, File, UploadFile, Form
import shutil
from pydantic import BaseModel
import speech_recognition as sr
import sellers
from mistralai import Mistral
from io import BytesIO
import edge_tts
import base64
import os
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel, ValidationError
import json
from typing import Optional


app = FastAPI()
API_KEY = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=API_KEY)

class DialogDetail(BaseModel):
    character_name: str
    player_dialog: str
    

async def generate_tts_audio(text, voice):
    audio_data = BytesIO()
    communicate = edge_tts.Communicate(text, voice)

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.write(chunk["data"])

    return audio_data.getvalue()

def build_seller_context(seller):
    items = "\n".join([f"- {item}: {price} coins" for item, price in seller.items_available_with_price.items()])
    dialog_history = "\n".join([f'{d[0]}: {d[1]}' for d in seller.dialog_list])

    context = f"""
You are {seller.name}.
{seller.description}

You would return purchase_successful bool as true only when item is purchased. And only  when purchase_successful is true item_purchased will be populated and deal_price will be populated.
Else purchase_successful will be false and item_purchased will be empty string and deal_price will be null.
Include prices and items in seller_response variable.
If Dialog so far is empty then first introduce yourself with seller name.

Items you sell (with prices):
{items if items else "No items available."}

Dialog so far:
{dialog_history if dialog_history else "No previous dialog."}

Important: Always respond ONLY in strict JSON format like this:
{{
  "seller_response": "<your reply here>",
  "purchase_successful": "<Boolean>",
  "item_purchased": "<ItemName>",
  "deal_price": "<Price>"
}}
Keep valid json only
Do not include anything outside JSON.
    """
    return context

class SellerResponse(BaseModel):
    seller_response: str
    purchase_successful: bool
    item_purchased: Optional[str]
    deal_price: Optional[int]
        
def get_seller_response(seller, player_input: str):
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
    print(raw_reply)
    print(json.loads(raw_reply))
    try:
        seller_reply_json = json.loads(raw_reply)
        validated = SellerResponse(**seller_reply_json)
    except (json.JSONDecodeError, ValidationError):
        print("Failed")
        validated = SellerResponse(seller_response=raw_reply)
    
    if validated.purchase_successful:
        seller.dialog_list = []
    else:
        seller.dialog_list.append(("Player", player_input))
        seller.dialog_list.append((seller.name, validated.seller_response))
    return validated
    
async def process_dialog(recognised_text, character_name):
    seller_obj = sellers.sellers[character_name]
    
    seller_response = get_seller_response(seller_obj, recognised_text)
    tts_audio = await generate_tts_audio(seller_response.seller_response,sellers.sellers[character_name].voice)
    audio_base64 = base64.b64encode(tts_audio).decode("utf-8")
    
    return audio_base64,seller_response
    
    
@app.post("/upload")
async def upload_audio(file: UploadFile = File(...), character_name:str = Form(...)):
    
    recognizer = sr.Recognizer()
    
    file.file.seek(0)
    
    with sr.AudioFile(file.file) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            text = "Could not understand audio"
        except sr.RequestError:
            text = "API unavailable"

    audio_base64, seller_response = await process_dialog(text, character_name)
    
    
    #tts_audio = await generate_tts_audio("Hello my name is Tushar")
    
    #audio_base64 = base64.b64encode(tts_audio).decode("utf-8")
    #audio_base64=""
    
    return {"text": text, 
    "character_name":character_name, 
    "audio_base64": audio_base64,
    "purchase_successful": seller_response.purchase_successful,
    "item_purchased": seller_response.item_purchased,
    "deal_price": seller_response.deal_price
    }