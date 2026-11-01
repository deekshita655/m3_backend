
import json
import os
import paho.mqtt.client as mqtt
import requests
from dotenv import load_dotenv
# --- Configuration ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "smartmilk/demo/device01/data"


load_dotenv()

FASTAPI_ENDPOINT = os.getenv(
    "FASTAPI_ENDPOINT",
    "http://127.0.0.1:8000/api/readings"
)

def on_connect(client, userdata, flags, reason_code, properties):
    """Subscribe to the firmware's MQTT topic after connecting."""
    if reason_code == 0:
        print(f"Connected to MQTT broker: {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC, qos=1)
        print(f"Subscribed to topic: {MQTT_TOPIC}\n")
    else:
        print(f"MQTT connection failed: {reason_code}")


def on_message(client, userdata, msg):
    """Receive M1 firmware data and forward mapped readings to M3."""
    try:
        raw_payload = msg.payload.decode("utf-8")
        print(f"\nReceived message on: {msg.topic}")
        print(f"Raw payload: {raw_payload}")

        data = json.loads(raw_payload)

        # Map the actual firmware fields to the M3 API schema.
        payload = {
            "session_id": f"device01_sample_{data.get('sample', 'unknown')}",
            "ph": data.get("ph"),
            "tds": data.get("tds_ppm"),
            "mq135_voltage": data.get("mq135_voltage"),
            "ph_simulated": data.get("ph_simulated"),

            # These measurements are not currently provided
            # as calibrated values by the firmware.
            "temperature": None,
            "nh3": None,
            "tds_stable_time": None,
            "nh3_slope": None,
            "concentration": None
        }

        print(f"Mapped API payload: {payload}")

        response = requests.post(
            FASTAPI_ENDPOINT,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        print("Successfully forwarded to FastAPI!")
        print(f"API response: {response.json()}\n")

    except json.JSONDecodeError:
        print("Error: Received message is not valid JSON.")

    except requests.exceptions.RequestException as e:
        print(f"Error forwarding data to FastAPI: {e}")

    except (KeyError, TypeError, ValueError) as e:
        print(f"Error processing firmware payload: {e}")


# --- Initialize MQTT Client ---
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message


if __name__ == "__main__":
    print(f"Starting MQTT Subscriber for {MQTT_BROKER}...")

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_forever()

    except KeyboardInterrupt:
        print("\nStopping MQTT Subscriber...")
        client.disconnect()

    except Exception as e:
        print(f"Subscriber error: {e}")
        client.disconnect()
