import requests
import time
import random

URL = "http://localhost:8000/update"  # This is your FastAPI backend

while True:
    data = {
        "heart_rate": random.randint(60, 150),
        "spo2": random.randint(80, 100),
        "motion": random.choice(["stable", "jerking"]),
        "seizure": random.choice(["Yes", "No"])
    }

    try:
        response = requests.post(URL, json=data)
        print("✅ Posted:", data, "| Response:", response.status_code)
    except Exception as e:
        print("❌ Error posting data:", e)

    time.sleep(5)

