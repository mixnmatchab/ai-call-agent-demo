import os
from twilio.rest import Client

# Hämta miljövariabler
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("TWILIO_PHONE_NUMBER")
to_number = os.getenv("MY_PHONE_NUMBER")

client = Client(twilio_sid, twilio_token)

# Sätt TwiML som en vanlig sträng, INTE som f-string
twiml_string = """
<Response>
    <Say language="sv-SE" voice="Polly.Maja">
        Hej! Det här är Sanna från Handlr. Ett ögonblick så startar vi samtalet.
    </Say>
    <Pause length="1"/>
    <Gather input="speech" speechTimeout="auto" language="sv-SE" action="https://ai-call-agent-demo-production.up.railway.app/voice" method="POST">
        <Say language="sv-SE" voice="Polly.Maja">Vad kan jag hjälpa dig med idag?</Say>
    </Gather>
</Response>
"""

# Starta samtal
call = client.calls.create(
    twiml=twiml_string,
    to=to_number,
    from_=from_number
)

print(f"📞 Samtal på väg! Call SID: {call.sid}")
