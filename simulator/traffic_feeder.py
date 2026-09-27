import time
import random
import argparse
import requests
from datetime import datetime, timezone

CAMERAS = ["CAM-001", "CAM-002", "CAM-003", "CAM-004", "CAM-005", "CAM-006"]

NORMAL_PLATES = [
    ("GJ01AB5566", "SEDAN", "Silver"),
    ("GJ27XY8899", "MOTORCYCLE", "Black"),
    ("GJ05KM4411", "HATCHBACK", "Blue"),
    ("GJ01PQ7722", "SUV", "Grey"),
    ("GJ18KL9012", "TRUCK", "Yellow"),
    ("GJ03MN3344", "SEDAN", "White"),
]

WATCHLIST_TARGETS = [
    ("GJ01XX0001", "SUV", "White"),
    ("GJ05AB1234", "SUV", "Red"),
    ("GJ27CD9988", "SUV", "Black"),
]

def generate_random_bbox():
    x = random.randint(50, 350)
    y = random.randint(60, 200)
    w = random.randint(180, 260)
    h = random.randint(120, 180)
    return {"x": x, "y": y, "width": w, "height": h}

def run_simulation(base_url="http://127.0.0.1:8000", interval=4, count=0):
    events_url = f"{base_url}/api/v1/analytics/events"
    step = 0

    print(f"Starting okDriver AI Traffic Feeder against {base_url} (Interval: {interval}s)")

    while True:
        step += 1
        cam_id = random.choice(CAMERAS)

        if step % 5 == 0:
            plate, vtype, color = random.choice(WATCHLIST_TARGETS)
            confidence = round(random.uniform(0.92, 0.99), 2)
            speed = round(random.uniform(65.0, 95.0), 1)
        else:
            plate, vtype, color = random.choice(NORMAL_PLATES)
            confidence = round(random.uniform(0.85, 0.98), 2)
            speed = round(random.uniform(35.0, 75.0), 1)

        payload = {
            "camera_id": cam_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "ANPR",
            "entity_identifier": plate,
            "entity_type": vtype,
            "confidence": confidence,
            "color": color,
            "speed_kmh": speed,
            "bounding_box": generate_random_bbox(),
            "metadata_json": {
                "lane": random.randint(1, 3),
                "weather": "Clear",
                "sensor_fps": 30
            }
        }

        try:
            resp = requests.post(events_url, json=payload, timeout=5)
            if resp.status_code == 201:
                res_data = resp.json()
                alert_flag = "🚨 [WATCHLIST ALERT TRIGGERED]" if res_data.get("alert_triggered") else ""
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {cam_id} -> {plate} ({vtype}, {speed} km/h) {alert_flag}")
            else:
                print(f"Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"Connection failed: {e}")

        if count > 0 and step >= count:
            break

        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base backend URL")
    parser.add_argument("--interval", type=float, default=4.0, help="Interval between detections in seconds")
    parser.add_argument("--count", type=int, default=0, help="Number of events to generate (0 for infinite)")
    args = parser.parse_args()

    run_simulation(base_url=args.url, interval=args.interval, count=args.count)
