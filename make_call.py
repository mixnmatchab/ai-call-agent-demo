import os
from twilio.rest import Client
from dotenv import load_dotenv

# Läs in miljövariabler från .env om du kör lokalt
load_dotenv()

# Miljövariabler
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("TWILIO_PHONE_NUMBER")   # Ditt Twilio-nummer
to_number = os.getenv("MY_PHONE_NUMBER")         # Ditt verifierade nummer
voice_url = "https://ai-call-agent-demo-production.up.railway.app/voice"  # Din Railway-endpoint

# Twilio-klient
client = Client(account_sid, auth_token)

# Initiera samtal
call = client.calls.create(
    to=to_number,
    from_=from_number,
    url=voice_url
)

print(f"🔔 Ringer upp {to_number}...")
