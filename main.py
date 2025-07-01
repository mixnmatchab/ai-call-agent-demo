import os
import openai
import requests
from flask import Flask, request, Response, send_file
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

# Miljövariabler
openai.api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_voice_id = os.getenv("VOICE_ID")

@app.route("/", methods=["GET"])
def home():
    return "✅ AI-agent är igång!"

@app.route("/voice", methods=["POST"])
def voice():
    user_input = request.values.get("SpeechResult", "")
    print(f"🗣️ Användaren sa: {user_input}")

    response = VoiceResponse()

    if not user_input:
        response.say("Jag hörde inte vad du sa. Kan du upprepa?", language="sv-SE")
        response.listen()
        return Response(str(response), mimetype="application/xml")

    try:
        completion = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du är en AI-assistent som heter Sanna och jobbar för Handlr. Du för en naturlig konversation med villaägare på svenska."},
                {"role": "user", "content": user_input}
            ]
        )
        gpt_reply = completion.choices[0].message.content.strip()
        print(f"🤖 GPT svar: {gpt_reply}")
    except Exception as e:
        print(f"❌ GPT-fel: {e}")
        response.say("Tyvärr uppstod ett problem. Försök igen senare.", language="sv-SE")
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
            print("⚠️ ElevenLabs-fel:", audio.status_code, audio.text)
            response.say(gpt_reply, language="sv-SE")
            response.listen()
            return Response(str(response), mimetype="application/xml")

    hosted_url = request.url_root.rstrip("/") + "/audio"
    response.play(hosted_url)
    response.listen()
    return Response(str(response), mimetype="application/xml")

@app.route("/audio", methods=["GET"])
def audio():
    filepath = "response.mp3"
    if os.path.exists(filepath):
        return send_file(filepath, mimetype="audio/mpeg")
    return "Ingen ljudfil tillgänglig", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
