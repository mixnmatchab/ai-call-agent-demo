import os
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Start, Stream
from openai import OpenAI
from elevenlabs import generate, play, set_api_key
from dotenv import load_dotenv

load_dotenv()

# Miljövariabler
openai_api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
twilio_sid = os.getenv("TWILIO_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("FROM_NUMBER")
to_number = os.getenv("TO_NUMBER")
voice_id = os.getenv("VOICE_ID")  # t.ex. "Sanna"

# Initiera klienter
client = Client(twilio_sid, twilio_token)
openai = OpenAI(api_key=openai_api_key)
set_api_key(elevenlabs_api_key)

# Flask-app
app = Flask(__name__)

# Prompt
prompt = """
Du är en AI-assistent som heter Sanna och jobbar för {{företagsnamn}}. Du ringer villaägare för att höra om de funderar på {{tjänst}}. Efter presentationen inled gärna med att fråga om kunden känner till företaget du ringer ifrån. invänta sedan svar. skriv som man pratar, inte som man skriver.

Du ska låta som en trevlig människa – tydlig, varm och avslappnad. Inte för säljig, inte för stel. Prata som du skulle göra i ett riktigt samtal. Ställ en enkel inledande fråga. Följ upp naturligt beroende på vad kunden svarar. Håll dig till max 2–3 meningar per svar. Undvik långa förklaringar.

Syftet är att ta reda på om kunden har ett intresse och försöka få till ett möte med kunden. Var tydlig med att läget är helt rätt i tiden just nu då priserna och bidragen är helt rätt.

Huvudmålet är att få kunden att förstå att det är ett kostnadsfritt möte och säljaren som kommer kan sin sak. Hen presenterar både ett pris och om det är lönsamt för kunden. Vi preliminärbokar inte möten utan det är viktigt att kunden förstår att de får hem en säljare till sig som går igenom kalkylen och det bästa för just dem.

Vi skickar inte ut information utan syftet är att vi ska boka ett möte.
Vid inbokat möte – föreslå en eftermiddag eller förmiddag, fråga vad som passar kunden bäst. Vid svar säg en dag och tid (max en vecka framåt i tiden).

Meddela att kunden kommer få en bokningsbekräftelse på sms efter samtalet.
"""

@app.route("/", methods=["GET"])
def index():
    return {"status": "Agent är online – använd /start för att ringa"}

@app.route("/start", methods=["GET"])
def start_call():
    call = client.calls.create(
        twiml=f'<Response><Say>Startar samtal...</Say><Redirect>/call</Redirect></Response>',
        to=to_number,
        from_=from_number,
        url="https://ai-call-agent-demo-production.up.railway.app/call"
    )
    return {"status": "Ringer upp kunden...", "sid": call.sid}

@app.route("/call", methods=["POST"])
def call():
    response = VoiceResponse()
    response.say("Hej! Det här är Sanna från Handlr.")

    start = Start()
    start.stream(url="wss://your-streaming-server.com/audio")
    response.append(start)

    response.say("Jag ville bara kolla om ni funderat på att till exempel byta fönster eller installera solceller?")
    return Response(str(response), mimetype="application/xml")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
