import json
import paho.mqtt.client as mqtt
import requests

# --- Configuration ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "m3_lab/sensor_readings"

FASTAPI_ENDPOINT = "https://m3-backend-api-xtiq.onrender.com/api/readings"


def on_connect(client, userdata, flags, rc, properties=None):
  """Callback function when the client connects to the HiveMQ broker."""
  if rc == 0:
    print(f" Connected successfully to MQTT Broker: {MQTT_BROKER}")
    client.subscribe(MQTT_TOPIC, qos=1)
    print(f" Subscribed to topic: '{MQTT_TOPIC}' with QoS 1\n")
  else:
    print(f" Failed to connect to MQTT broker. Return code: {rc}")


def on_message(client, userdata, msg):
  """Callback function when a new message is published to the subscribed topic."""
  try:
    raw_payload = msg.payload.decode("utf-8")
    print(f" Received MQTT Message on topic '{msg.topic}':")
    print(f"   Payload: {raw_payload}")

    # Parse JSON payload from hardware / emulator
    data = json.loads(raw_payload)

    # Provide safe defaults if fields are missing in raw payload
    data.setdefault("tds_stable_time", 0.0)
    data.setdefault("nh3_slope", 0.0)
    data.setdefault("concentration", "")

    # Increased timeout from 5 to 15 seconds for Render cold starts
    response = requests.post(FASTAPI_ENDPOINT, json=data, timeout=15)

    if response.status_code in [200, 201]:
      print(
          f" Successfully forwarded to FastAPI! Status: {response.status_code}"
      )
      print(f"   API Response: {response.json()}\n")
    else:
      print(f" API Error ({response.status_code}): {response.text}\n")

  except json.JSONDecodeError:
    print(" Error: Received message was not valid JSON!\n")
  except requests.exceptions.RequestException as e:
    print(f" Error forwarding data to FastAPI backend: {e}\n")


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