import os
import openai
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
destination_number = os.getenv("DESTINATION_PHONE_NUMBER")

client = Client(twilio_sid, twilio_token)

class ChatRequest(BaseModel):
    customer_input: str
    company_name: str
    service: str

@app.get("/")
def read_root():
    return {"message": "AI Call Agent is running. Use the /chat endpoint to post messages."}

@app.post("/chat")
async def chat(request: ChatRequest):
    prompt = f"""
    Du är en AI-assistent som heter Sanna och jobbar för {request.company_name}. Du ringer villaägare för att höra om de funderar på {request.service}.
    Efter presentationen inled gärna med att fråga om kunden känner till företaget du ringer ifrån. Invänta sedan svar.
    Skriv som man pratar, inte som man skriver.
    Upprepa inte kundens namn i varje mening.
    Du ska låta som en trevlig människa – tydlig, varm och avslappnad. Inte för säljig, inte för stel. Prata som du skulle göra i ett riktigt samtal.
    Ställ en enkel inledande fråga. Följ upp naturligt beroende på vad kunden svarar. Håll dig till max 2–3 meningar per svar. Undvik långa förklaringar.
    Syftet är att ta reda på om kunden har ett intresse och försöka få till ett möte med kunden. Var tydlig med att läget är helt rätt i tiden just nu då priserna och bidragen är helt rätt.
    Huvudmålet är att få kunden att förstå att det är ett kostnadsfritt möte och säljaren som kommer kan sin sak. Hen presenterar både ett pris och om det är lönsamt för kunden. Vi preliminärbokar inte möten utan det är viktigt att kunden förstår att de får hem en säljare som går igenom kalkylen och det bästa för just dem. Sälj in det.
    Vi skickar inte ut information utan syftet är att vi ska boka ett möte.
    Vid inbokat möte, föreslå en eftermiddag eller förmiddag. Fråga vad som passar kunden bäst. Vid svar, säg en dag och tid (bestäm åt kunden, max en vecka framåt i tiden).
    Meddela att kunden kommer få en bokningsbekräftelse på sms efter samtalet.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt},
                  {"role": "user", "content": request.customer_input}],
        temperature=0.7,
        max_tokens=300
    )

    reply_text = response.choices[0].message["content"].strip()

    # Generate speech with ElevenLabs
    audio_response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{elevenlabs_voice_id}",
        headers={
            "xi-api-key": elevenlabs_api_key,
            "Content-Type": "application/json"
        },
        json={
            "text": reply_text,
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.8
            }
        }
    )

    audio_file_path = "/tmp/audio.mp3"
    with open(audio_file_path, "wb") as f:
        f.write(audio_response.content)

    # Upload to File.io
    with open(audio_file_path, "rb") as f:
        upload = requests.post("https://file.io", files={"file": f})
    file_url = upload.json().get("link")

    if not file_url:
        return {"error": "Could not upload audio file."}

    # Place call with Twilio and play file
    call = client.calls.create(
        twiml=f'<Response><Play>{file_url}</Play></Response>',
        to=destination_number,
        from_=twilio_number
    )

    return {"reply": reply_text, "audio_url": file_url, "call_sid": call.sid}
