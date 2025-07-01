import os
import openai
import requests
import traceback
from flask import Flask, request, Response, send_file
from twilio.twiml.voice_response import VoiceResponse, Gather

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_voice_id = os.getenv("VOICE_ID")

@app.route("/", methods=["GET"])
def home():
    return "✅ AI-agent är igång!"

@app.route("/voice", methods=["POST"])
def voice():
    user_input = request.values.get("SpeechResult", "")
    print("✅ /voice anropad")
    print("SpeechResult:", user_input)

    response = VoiceResponse()

    def fallback_and_listen(msg="Jag kunde inte svara just nu. Vad vill du prata om?"):
        response.say(msg, language="sv-SE")
        gather = Gather(input="speech", language="sv-SE", speech_timeout="auto", action="/voice", method="POST")
        gather.say("Jag lyssnar.", language="sv-SE")
        response.append(gather)
        return Response(str(response), mimetype="application/xml")

    if not user_input:
        # 🔹 Första interaktion: ge kunden chans att säga hej
        gather = Gather(input="speech", language="sv-SE", speech_timeout="auto", action="/voice", method="POST")
        gather.say("Hej! Det här är Sanna från Handlr. Jag ringer angående projekt i hemmet. Vad kan jag hjälpa dig med idag?", language="sv-SE")
        response.append(gather)
        return Response(str(response), mimetype="application/xml")

    # 🔹 GPT-anrop
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du är en AI-assistent som heter Sanna och jobbar för Handlr. "
                        "Du ringer villaägare för att höra om de funderar på att ta hjälp med något projekt i hemmet, "
                        "som solceller, fönsterbyte eller renovering. "
                        "Svara trevligt, kortfattat och avsluta med en enkel fråga. Du ska låta mänsklig."
                    )
                },
                {"role": "user", "content": user_input}
            ]
        )
        gpt_reply = completion.choices[0].message["content"].strip()
        print("🤖 GPT svar:", gpt_reply)
    except Exception as e:
        print("❌ GPT-fel:")
        traceback.print_exc()
        return fallback_and_listen("Jag kunde inte hämta något svar just nu.")

    # 🔹 ElevenLabs-anrop
    try:
        audio = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{elevenlabs_voice_id}",
            headers={
                "xi-api-key": elevenlabs_api_key,
                "Content-Type": "application/json"
            },
            json={
                "text": gpt_reply,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.4, "similarity_boost": 0.8}
            },
            stream=True  # Viktigt!
        )
        if audio.status_code == 200:
            with open("response.mp3", "wb") as f:
                for chunk in audio.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        else:
            print("⚠️ ElevenLabs API-fel:", audio.status_code, audio.text)
            return fallback_and_listen("Jag kunde inte generera ljudet.")
    except Exception as e:
        print("❌ ElevenLabs-fel:")
        traceback.print_exc()
        return fallback_and_listen("Jag kunde inte spela upp svaret.")

    # 🔹 Spela upp
    hosted_url = request.url_root.rstrip("/") + "/audio"
    if os.path.exists("response.mp3"):
        response.play(hosted_url)
    else:
        return fallback_and_listen("Jag kunde inte hitta ljudfilen.")

    # 🔹 Lyssna efter nytt svar (inga extra frågor längre)
    gather = Gather(input="speech", language="sv-SE", speech_timeout="auto", action="/voice", method="POST")
    response.append(gather)

    return Response(str(response), mimetype="application/xml")

@app.route("/audio", methods=["GET"])
def audio():
    filepath = "response.mp3"
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            data = f.read()
        return Response(data, mimetype="audio/mpeg", headers={
            "Content-Disposition": "inline; filename=response.mp3",
            "Cache-Control": "no-cache",
            "Content-Length": str(len(data))
        })
    return "Ingen ljudfil tillgänglig", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
