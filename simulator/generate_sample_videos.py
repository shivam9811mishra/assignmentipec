import os
import cv2
import numpy as np
from pathlib import Path

def create_synthetic_cctv_feed(output_path: str, camera_name: str, road_color=(45, 45, 50), num_frames=180, fps=25):
    width, height = 640, 360
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    cars = [
        {"x": 100, "y": 80, "speed": 3, "color": (230, 230, 240), "w": 60, "h": 100, "plate": "GJ01XX0001"},
        {"x": 260, "y": 20, "speed": 4, "color": (40, 40, 200), "w": 55, "h": 90, "plate": "GJ05AB1234"},
        {"x": 420, "y": 140, "speed": 2.5, "color": (180, 180, 180), "w": 65, "h": 110, "plate": "GJ01AB5566"},
    ]

    for frame_idx in range(num_frames):
        frame = np.full((height, width, 3), 30, dtype=np.uint8)

        cv2.rectangle(frame, (60, 0), (580, height), road_color, -1)

        for lane_x in (220, 380):
            dash_offset = (frame_idx * 6) % 40
            for y in range(-40 + dash_offset, height, 40):
                cv2.line(frame, (lane_x, y), (lane_x, y + 20), (220, 220, 220), 2)

        for car in cars:
            car_y = int((car["y"] + frame_idx * car["speed"] * 1.5) % (height + 150) - 100)
            cx, cy, cw, ch = car["x"], car_y, car["w"], car["h"]
            cv2.rectangle(frame, (cx, cy), (cx + cw, cy + ch), car["color"], -1)
            cv2.rectangle(frame, (cx + 5, cy + 15), (cx + cw - 5, cy + ch - 25), (70, 70, 70), -1)

            if 20 < cy < height - 60:
                cv2.rectangle(frame, (cx - 4, cy - 4), (cx + cw + 4, cy + ch + 4), (0, 255, 120), 1)
                tag = f"{car['plate']}"
                cv2.putText(frame, tag, (cx - 4, cy - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 120), 1)

        cv2.rectangle(frame, (0, 0), (width, 36), (15, 15, 20), -1)
        timestamp_str = f"REC [LIVE] 2026-09-24 10:{(frame_idx//25):02d}:{(frame_idx%25):02d}.{frame_idx%10}"
        cv2.putText(frame, camera_name, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 255), 1)
        cv2.putText(frame, timestamp_str, (width - 250, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        cv2.circle(frame, (width - 15, 18), 5, (0, 0, 255), -1)

        out.write(frame)

    out.release()

if __name__ == "__main__":
    assets_dir = Path("static/assets/videos")
    assets_dir.mkdir(parents=True, exist_ok=True)

    create_synthetic_cctv_feed(
        str(assets_dir / "feed1_junction.mp4"),
        "CAM-001 | SG Highway Junction, Ahmedabad",
        road_color=(40, 42, 45)
    )
    create_synthetic_cctv_feed(
        str(assets_dir / "feed2_station.mp4"),
        "CAM-002 | Kalupur Station Gate Checkpost",
        road_color=(45, 40, 42)
    )
    create_synthetic_cctv_feed(
        str(assets_dir / "feed3_highway.mp4"),
        "CAM-003 | Gandhinagar CH-0 Toll Plaza",
        road_color=(38, 44, 48)
    )
    print("Synthetic CCTV feeds generated successfully in static/assets/videos!")
