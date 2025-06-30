# make_call.py
import os
from twilio.rest import Client

# Miljövariabler
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("TWILIO_PHONE_NUMBER")  # Ditt Twilio-nummer
to_number = os.getenv("MY_PHONE_NUMBER")        # Ditt riktiga nummer

# URL till /voice endpoint i Railway-appen
voice_url = "https://ai-call-agent-demo-production.up.railway.app/voice"

client = Client(account_sid, auth_token)

call = client.calls.create(
    to=to_number,
    from_=from_number,
    url=voice_url,  # Twilio hämtar instruktioner härifrån
)

print(f"🔔 Ringer upp {to_number}...")
