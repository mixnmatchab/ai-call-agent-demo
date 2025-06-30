import os
from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from openai import OpenAI
from elevenlabs.client import ElevenLabs

app = Flask(__name__)

# Miljövariabler
openai_api_key = os.getenv("OPENAI_API_KEY")
eleven_api_key = os.getenv("ELEVENLABS_API_KEY")
voice_id = os.getenv("VOICE_ID")

# Initiera klienter
openai_client = OpenAI(api_key=openai_api_key)
eleven_client = ElevenLabs(api_key=eleven_api_key)

# Prompt
base_prompt = """
Du är en AI-assistent som heter Sanna och jobbar för {{företagsnamn}}. Du ringer villaägare för att höra om de funderar på {{tjänst}}.
Efter presentationen inled gärna med att fråga om kunden känner till företaget du ringer ifrån. Invänta sedan svar.
Skriv som man pratar, inte som man skriver. Upprepa inte kundens namn i varje mening.

Du ska låta som en trevlig människa – tydlig, varm och avslappnad. Inte för säljig, inte för stel. Prata som du skulle göra i ett riktigt samtal.
Ställ en enkel inledande fråga. Följ upp naturligt beroende på vad kunden svarar. Håll dig till max 2–3 meningar per svar. Undvik långa förklaringar.

Syftet är att ta reda på om kunden har ett intresse och försöka få till ett möte med kunden. Var tydlig med att läget är helt rätt i tiden just nu då priserna och bidragen är helt rätt.

Huvudmålet är att få kunden att förstå att det är ett kostnadsfritt möte och säljaren som kommer kan sin sak. Hen presenterar både ett pris och om det är lönsamt för kunden. Vi preliminärbokar inte möten utan det är viktigt att kunden förstår att de får hem en säljare till sig som går igenom kalkylen och det bästa för just dem.

Vi skickar inte ut information utan syftet är att vi ska boka ett möte.
Vid inbokat möte – föreslå en eftermiddag eller förmiddag, fråga vad som passar kunden bäst. Vid svar säg en dag och tid (max en vecka framåt i tiden).

Meddela att kunden kommer få en bokningsbekräftelse på sms efter samtalet.
"""

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "AI Call Agent är igång – använd /voice för att testa röstsvar."})

@app.route("/voice", methods=["POST"])
def voice():
    response = VoiceResponse()
    user_input = request.values.get("SpeechResult", "")

    if not user_input:
        user_input = "Hej!"

    # Skicka till OpenAI
    reply = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": user_input}
        ]
    ).choices[0].message.content

    # Generera röst via ElevenLabs
    audio = eleven_client.generate(
        text=reply,
        voice=voice_id,
        model_id="eleven_multilingual_v2",
        stream=True
    )

    # Streamingen triggas genom att loopa (även om vi inte gör något med varje del)
    for chunk in audio:
        pass

    response.say("Tack för samtalet, hej då.")
    return str(response)

if __name__ == "__main__":
    app.run(debug=True)
