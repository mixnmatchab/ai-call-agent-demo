import os
from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from elevenlabs import generate, play, set_api_key
from openai import OpenAI
from dotenv import load_dotenv
import tempfile
import base64
import requests

load_dotenv()

# Initiera API-nycklar
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
RECIPIENT_PHONE_NUMBER = os.getenv("RECIPIENT_PHONE_NUMBER")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")

set_api_key(ELEVEN_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

@app.route("/")
def home():
    return {"message": "AI Call Agent is running. Use the /chat endpoint to post messages."}

@app.route("/chat", methods=[POST])
def chat():
    data = request.get_json()
    user_input = data.get("message")

    prompt = f"""
    Du är en AI-assistent som heter Sanna och jobbar för {{företagsnamn}}. Du ringer villaägare för att höra om de funderar på {{tjänst}}.
    Efter presentationen inled gärna med att fråga om kunden känner till företaget du ringer ifrån. invänta sedan svar.
    skriv som man pratar, inte som man skriver

    Upprepa inte kundens namn i varje mening.

    Du ska låta som en trevlig människa – tydlig, varm och avslappnad. Inte för säljig, inte för stel. Prata som du skulle göra i ett riktigt samtal.
    Ställ en enkel inledande fråga. Följ upp naturligt beroende på vad kunden svarar. Håll dig till max 2–3 meningar per svar. Undvik långa förklaringar.

    Syftet är att ta reda på om kunden har ett intresse och försöka få till ett möte med kunden.  var tydlig med att läget är helt rätt i tiden just nu då priserna och bidragen är helt rätt. 

    Huvudmålet är att få kunden att förstå att det är ett kostnadsfritt möte och säljaren som kommer kan sin sak. hen presentera både ett pris och om det är lönsamt för kunden. vi preliminär bokar inte möten utan det är viktigt att kunden förstår att dom får hem en säljare till sig som kommer gå igenom kalkylen och det bästa för just dom. sälj in det

    Vi skickar inte ut information utan syftet är att vi ska boka ett möte.

    Vid inbokat möte. föreslå en eftermiddag eller förmiddag, fråga vad som passar kunden bäst. Vid svar säg en dag och tid (bestäm åt kunden, max en vecka framåt i tiden) 

    Meddela att kunden kommer få en bokningsbekräftelse på sms efter samtalet
    """

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ]
    )

    ai_reply = response.choices[0].message.content

    audio = generate(
        text=ai_reply,
        voice=VOICE_ID,
        model="eleven_v3",
        stream=False,
        voice_settings={
            "stability": 0.4,
            "similarity_boost": 0.75,
            "style": 0.2,
            "use_speaker_boost": True
        }
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
        tmpfile.write(audio)
        tmpfile_path = tmpfile.name

    with open(tmpfile_path, "rb") as f:
        audio_base64 = base64.b64encode(f.read()).decode("utf-8")

    return jsonify({"reply": ai_reply, "audio_base64": audio_base64})

if __name__ == "__main__":
    app.run(debug=True)
