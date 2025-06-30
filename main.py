import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
from twilio.rest import Client
import openai
import requests

app = FastAPI()

# Miljövariabler
openai.api_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_from_number = os.getenv("TWILIO_FROM_NUMBER")
voice_id = os.getenv("VOICE_ID")
elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")

client = Client(twilio_sid, twilio_token)

class CallRequest(BaseModel):
    customer_input: str
    company_name: str
    service: str

@app.get("/")
async def root():
    return {"message": "AI Call Agent is running. Use the /chat endpoint to post messages."}

@app.post("/chat")
async def chat(req: CallRequest):
    prompt = f"""
Du är en AI-assistent som heter Sanna och jobbar för {req.company_name}.
Du ringer villaägare för att höra om de funderar på {req.service}.
Efter presentationen inled gärna med att fråga om kunden känner till företaget du ringer ifrån.
Invänta svar. Skriv som man pratar, inte som man skriver.

Upprepa inte kundens namn i varje mening.

Du ska låta som en trevlig människa – tydlig, varm och avslappnad.
För inte sälja, inte för stel. Ställ en enkel inledande fråga. Följ upp naturligt beroende på vad kunden säger.

Syftet är att ta reda på om kunden har ett intresse och försöka få till ett möte med en kollega.

Huvudmålet är att få kunden att förstå att det är kostnadsfritt och att kunden själv kommer kontakta oss.

Vi skickar inte ut information utan syftet är att få till ett möte.

Vid inbokad möte, föreslå en eftermiddag eller förmiddag, fråga vad som passar kunden bäst.
Skriv avslutningen naturligt.

Meddela att kunden kommer få en bokningsbekräftelse på sms efter samtalet.

Kund: {req.customer_input}
Sanna:
"""

    # Skicka till OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    ai_response = response.choices[0].message.content.strip()

    # ElevenLabs röstgenerering
    audio_response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": elevenlabs_key,
            "Content-Type": "application/json"
        },
        json={
            "text": ai_response,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
    )

    audio_path = "/tmp/voice.mp3"
    with open(audio_path, "wb") as f:
        f.write(audio_response.content)

    # Ringa samtal via Twilio (detta triggar ett voice call)
    call = client.calls.create(
        twiml=f'<Response><Play>https://{os.getenv("RAILWAY_STATIC_URL")}/voice.mp3</Play></Response>',
        to=os.getenv("TO_NUMBER"),
        from_=twilio_from_number
    )

    return {"message": "Samtal initierat", "response": ai_response}
