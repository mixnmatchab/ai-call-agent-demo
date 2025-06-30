from fastapi import FastAPI
from pydantic import BaseModel
import openai
import os
from twilio.rest import Client
import requests

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
voice_id = os.getenv("VOICE_ID")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

twilio_client = Client(twilio_sid, twilio_token)

class CallRequest(BaseModel):
    customer_input: str
    company_name: str
    service: str

@app.post("/chat")
async def chat(req: CallRequest):
    prompt = f"""
    Du är en AI-assistent som heter Sanna och jobbar för {req.company_name}. Du ringer villaägare för att höra om de funderar på {req.service}.
    Efter presentationen inled gärna med att fråga om kunden känner till företaget du ringer ifrån. invänta sedan svar.

    skriv som man pratar, inte som man skriver.

    Upprepa inte kundens namn i varje mening.

    Du ska låta som en trevlig människa – tydlig, varm och avslappnad. Inte för säljig, inte för stel. 
    Ställ en enkel inledande fråga. Följ upp naturligt med små frågor i taget, som om du vore en människa. Invänta svar.

    Syftet är att ta reda på om kunden har ett intresse och försöka få till ett möte med kund.

    Huvudmålet är att få kunden att förstå att det är kostnadsfritt och helt utan säljare som kommer och knackar på dörren.

    Vi skickar inte ut information utan syftet är att boka samtal eller möte.

    Vid inbokat möte, föreslå en eftermiddag eller förmiddag, fråga vad som passar kunden bäst. Skriv vad kunden säger.

    Meddela att kunden kommer få en bokningsbekräftelse på sms efter samtalet.

    Kund: {req.customer_input}
    Sanna:
    """

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = completion.choices[0].message.content.strip()

    # Skapa ljud med ElevenLabs
    audio_response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": elevenlabs_api_key,
            "Content-Type": "application/json"
        },
        json={
            "text": response_text,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
    )

    # Spara lokalt
    with open("voice.mp3", "wb") as f:
        f.write(audio_response.content)

    # Ladda upp till file.io
    with open("voice.mp3", "rb") as f:
        upload = requests.post("https://file.io", files={"file": f})
        upload_url = upload.json()["link"]

    # Ring samtal via Twilio med ljudet
    call = twilio_client.calls.create(
        twiml=f'<Response><Play>{upload_url}</Play></Response>',
        to="+46739537750",  # <- ditt svenska nummer
        from_="+15017122661"  # <- verifierat/köpt Twilio-nummer
    )

    return {
        "reply": response_text,
        "mp3_url": upload_url,
        "twilio_call_sid": call.sid
    }
