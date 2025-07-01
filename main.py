import os
import openai
import requests
from flask import Flask, request, Response, send_file
from twilio.twiml.voice_response import VoiceResponse

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
    print(f"🗣️ Användaren sa: {user_input}")

    response = VoiceResponse()

    if not user_input:
        response.say("Jag hörde inte vad du sa. Kan du upprepa?", language="sv-SE")
        response.listen()
        return Response(str(response), mimetype="application/xml")

    # 🔹 GPT-anrop
    try:
        completion = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du är en AI-assistent som heter Sanna och jobbar för Handlr. Du för en naturlig konversation med villaägare på svenska."},
                {"role": "user", "content": user_input}
            ]
        )
        gpt_reply = completion.choices[0].message.content.strip()
        print(f"🤖 G
