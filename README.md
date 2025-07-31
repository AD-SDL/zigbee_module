# Zigbee USB Dongle Setup and MQTT Integration

## **Hardware Setup**

1. **Unbox the dongle and open the case** by removing both screws on the USB side.  
2. **Switch the toggle to ON.**  
3. **Plug into your computer**.  
   - If using **macOS**, use [this flasher](https://github.com/Koenkk/zigbee2mqtt/wiki/Flashing-the-firmware#macos).  
   - **Flash the latest compatible firmware** available [here](https://www.zigbee2mqtt.io/guide/adapters/).  

---

## **Software Installation**

Follow the setup instructions from the [Zigbee2MQTT installation guide](https://www.zigbee2mqtt.io/guide/installation/).

**Ensure you install required packages:**

- **Node.js**
- **Homebrew**
- **Mosquitto MQTT Broker**

---

## **Zigbee2MQTT Configuration**

Paste the following into your configuration file (e.g., `configuration.yaml`), modifying ports/server as needed:

```yaml
serial:
  port: /dev/cu.SLAB_USBtoUART
  adapter: zstack
  rtscts: false

experimental:
  new_api: null

mqtt:
  base_topic: zigbee2mqtt
  server: mqtt://localhost:1883

advanced:
  network_key:
    - 221
    - 178
    - 152
    - 180
    - 101
    - 216
    - 174
    - 184
    - 162
    - 62
    - 84
    - 202
    - 217
    - 163
    - 7
    - 121

version: 4

frontend:
  enabled: true
  port: 8080


To access the dashboard, visit: http://localhost:8080

On the dashboard, press "Permit join (All)"

If pairing fails, check supported devices for instructions.

Device Pairing Tips
Sonoff Smart Plug: Plug in, then press and hold the power button for 5 seconds.

Contact Sensor: Remove battery dampener, then press the reset button for 5 seconds with a pin.

Water Leak Sensor: Open base and remove insulation sheet from battery.

You can rename devices using the Edit button on the Zigbee2MQTT dashboard.

Create MQTT Python Clients
Install required library:
pip install paho-mqtt

Create two files in your editor:

sub.py (subscriber file)
import random
from paho.mqtt import client as mqtt_client

broker = 'localhost'
port = 1883
topic = "zigbee2mqtt/Power Plug"
client_id = f'subscribe-{random.randint(0, 1000)}'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(client_id=client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def subscribe(client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(topic)
    client.on_message = on_message

def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()

if __name__ == '__main__':
    run()


pub.py (Publisher)
import random
import time
from paho.mqtt import client as mqtt_client

broker = 'localhost'
port = 1883
topic = "zigbee2mqtt/Power Plug"
client_id = f'publish-{random.randint(0, 1000)}'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client):
    msg_count = 1
    while msg_count <= 5:
        time.sleep(1)
        msg = f"Test message {msg_count}"
        result = client.publish(topic, msg)
        status = result[0]
        if status == 0:
            print(f"Sent `{msg}` to `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1

def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.loop_stop()

if __name__ == '__main__':
    run()


Testing Message Flow
To confirm your messages are being sent:

1. Open a terminal tab and run:
mosquitto_sub -h localhost -t zigbee2mqtt/Power\ Plug
2. In another tab, run your publisher:
python3 pub.py

**Alternative Configuration Example**
version: 4
mqtt:
  base_topic: zigbee2mqtt
  server: mqtt://mosquitto:1883

serial:
  port: >-
    /dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_74f7de58e66bef11b5179dadc169b110-if00-port0
  adapter: zstack
  rtscts: false

advanced:
  log_level: info
  channel: 11
  network_key:
    - 191
    - 121
    - 234
    - 238
    - 221
    - 195
    - 239
    - 151
    - 160
    - 92
    - 34
    - 219
    - 77
    - 163
    - 52
    - 10
  pan_id: 21945
  ext_pan_id:
    - 196
    - 237
    - 151
    - 241
    - 116
    - 69
    - 157
    - 88

frontend:
  enabled: true
  port: 8080

homeassistant:
  enabled: false

onboarding: false

devices:
  '0x44e2f8fffe0e92b8':
    friendly_name: Water Leak Detector
  '0x44e2f8fffe0c9982':
    friendly_name: Water Leak Detector 2
  '0xa4c1381dabf5c348':
    friendly_name: Contact Sensor
  '0x00124b002f89d81e':
    friendly_name: Power Plug


**Docker Setup**
docker network create zigbee_network

docker run -d \
  --name zigbee2mqtt \
  --restart unless-stopped \
  --network zigbee_network \
  --device=/dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_XXXX \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v /run/udev:/run/udev:ro \
  -e TZ=America/Chicago \
  ghcr.io/koenkk/zigbee2mqtt

docker run -d \
  --name mosquitto \
  --network zigbee_network \
  -p 1883:1883 \
  -v $(pwd)/mosquitto-config/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro \
  eclipse-mosquitto

docker run -it --rm --network zigbee_network alpine sh
apk add busybox-extras
telnet mosquitto 1883
exit

**More Resources:**
Zigbee2MQTT macOS Flashing: https://github.com/Koenkk/zigbee2mqtt#macos
Mosquitto on Windows: https://cedalo.com/blog/how-to-install-mosquitto-mqtt-broker-on-windows/
PDM Python Environment Manager: https://pdm-project.org/en/latest/
