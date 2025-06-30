
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from twilio.rest import Client
import openai
import requests

app = FastAPI()

# Miljövariabler
openai.api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
voice_id = os.getenv("VOICE_ID")
twilio_sid = os.getenv("TWILIO_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("FROM_NUMBER")
to_number = os.getenv("TO_NUMBER")

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
    Du är en AI-assistent som heter Sanna och jobbar för {req.company_name}. Du ringer villaägare för att höra om de funderar på {req.service}.
    Efter presentationen, inled gärna med att fråga om kunden känner till företaget du ringer ifrån. Invänta svar.
    Skriv som man pratar, inte som man skriver. Upprepa inte kundens namn i varje mening.

    Du ska låta som en trevlig människa – tydlig, varm och avslappnad. Inte för säljig, inte för stel.
    Ställ en enkel inledande fråga. Följ upp naturligt utifrån det kunden svarar. Håll tonen mjuk, varm men professionell.

    Syftet är att ta reda på om kunden har ett intresse och försöka få till ett möte med rådgivare.

    Huvudmålet är att få kunden att förstå att det är kostnadsfritt och att rådgivaren som kontaktar kunden gör en behovsanalys.

    Vi skickar inte ut information utan syftet är att boka ett första samtal med en rådgivare.

    Vid inbokat möte – föreslå en eftermiddag eller förmiddag, fråga vad som passar kunden bäst. Svara inte själv.

    Meddela att kunden kommer få en bokningsbekräftelse på sms efter samtalet.

    Kund: {req.customer_input}
    Sanna:
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        reply_text = response.choices[0].message["content"]

        audio_resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": elevenlabs_api_key,
                "Content-Type": "application/json"
            },
            json={
                "text": reply_text,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
            }
        )

        if audio_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to generate audio.")

        with open("speech.mp3", "wb") as f:
            f.write(audio_resp.content)

        client = Client(twilio_sid, twilio_token)

        call = client.calls.create(
            twiml=f"<Response><Play>https://{os.getenv('RAILWAY_STATIC_URL')}/speech.mp3</Play></Response>",
            from_=from_number,
            to=to_number
        )

        return {"status": "success", "call_sid": call.sid}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
