import os
import openai
import requests
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

    # 🔹 Första anropet – börja samtalet
    if not user_input:
        system_prompt = "Du är en AI-assistent som heter Sanna och jobbar för Handlr. Börja samtalet naturligt på svenska med att presentera dig och fråga om kunden funderar på något projekt i sitt hus."
        user_prompt = "Starta samtalet"

        try:
            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            gpt_reply = completion.choices[0].message.content.strip()
            print("🟢 GPT startfras:", gpt_reply)
        except Exception as e:
            print("❌ GPT-fel vid start:", str(e))
            response.say("Tyvärr kunde vi inte starta samtalet. Försök igen senare.", language="sv-SE")
            return Response(str(response), mimetype="application/xml")

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
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                }
            )
            if audio.status_code == 200:
                with open("response.mp3", "wb") as f:
                    f.write(audio.content)
            else:
                print("⚠️ ElevenLabs API-fel:", audio.status_code, audio.text)
                response.say("Fel med röstgenerering.", language="sv-SE")
                return Response(str(response), mimetype="application/xml")
        except Exception as e:
            print("❌ ElevenLabs-fel vid start:", str(e))
            response.say("Kunde inte spela upp svaret. Försök igen.", language="sv-SE")
            return Response(str(response), mimetype="application/xml")

        hosted_url = request.url_root.rstrip("/") + "/audio"
        response.play(hosted_url)

        gather = Gather(input="speech", language="sv-SE", speech_timeout="auto", action="/voice", method="POST")
        gather.say("Varsågod, du kan svara nu.", language="sv-SE")
        response.append(gather)
        return Response(str(response), mimetype="application/xml")

    # 🔹 Fortsätt konversationen
    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Fortsätt samtalet naturligt som en AI-assistent från Handlr. Svara på vad kunden säger och ställ en ny fråga."},
                {"role": "user", "content": user_input}
            ]
        )
        gpt_reply = completion.choices[0].message.content.strip()
        print("🤖 GPT svar:", gpt_reply)
    except Exception as e:
        print("❌ GPT-fel:", str(e))
        response.say("Ett fel uppstod i GPT-tjänsten.", language="sv-SE")
        return Response(str(response), mimetype="application/xml")

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
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
            }
        )
        if audio.status_code == 200:
            with open("response.mp3", "wb") as f:
                f.write(audio.content)
        else:
            print("⚠️ ElevenLabs API-fel:", audio.status_code, audio.text)
            response.say("Fel med röstgenerering.", language="sv-SE")
            return Response(str(response), mimetype="application/xml")
    except Exception as e:
        print("❌ ElevenLabs-fel:", str(e))
        response.say("Kunde inte spela upp svaret. Försök igen.", language="sv-SE")
        return Response(str(response), mimetype="application/xml")

    hosted_url = request.url_root.rstrip("/") + "/audio"
    response.play(hosted_url)

    gather = Gather(input="speech", language="sv-SE", speech_timeout="auto", action="/voice", method="POST")
    gather.say("Vad mer vill du veta?", language="sv-SE")
    response.append(gather)

    return Response(str(response), mimetype="application/xml")

@app.route("/audio", methods=["GET"])
def audio():
    filepath = "response.mp3"
    if os.path.exists(filepath):
        return send_file(filepath, mimetype="audio/mpeg")
    return "Ingen ljudfil tillgänglig", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
