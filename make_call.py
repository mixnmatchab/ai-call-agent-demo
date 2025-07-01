import os
from twilio.rest import Client

# Hämta miljövariabler
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("TWILIO_PHONE_NUMBER")
to_number = os.getenv("MY_PHONE_NUMBER")

client = Client(twilio_sid, twilio_token)

# Starta samtal – Twilio hämtar TwiML från din Railway-backend
call = client.calls.create(
    to=to_number,
    from_=from_number,
    url="https://ai-call-agent-demo-production.up.railway.app/voice",  # TwiML hämtas härifrån
    method="POST"
)

print(f"📞 Samtal på väg! Call SID: {call.sid}")
