import os
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from twilio.rest import Client
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Initiera OpenAI-klient
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initiera Twilio-klient
twilio_client = Client(
    os.getenv("TWILIO_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Variabler
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")
TO_NUMBER = os.getenv("TO_NUMBER")
FROM_NUMBER = os.getenv("FROM_NUMBER")

class CallRequest(BaseModel):
    customer_input: str
    company_name: str
    service: str

@app.get("/")
def root():
    return {"message": "AI Call Agent is running. Use the /chat endpoint to post messages."}

@app.post("/chat")
async def chat(req: CallRequest):
    prompt = f"""
Du är en AI-assistent som heter Sanna och jobbar för {req.company_name}. Du ringer villaägare för att höra om de funderar på {req.service}._
