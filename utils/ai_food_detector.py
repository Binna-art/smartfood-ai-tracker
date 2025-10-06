import os, requests, random
from dotenv import load_dotenv
load_dotenv()

HF_API = os.getenv("HF_TOKEN")
USDA_API = os.getenv("USDA_API_KEY")

def detect_food(image_path):
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://api-inference.huggingface.co/models/foodai/foodai-food-classification",
            headers={"Authorization": f"Bearer {HF_API}"},
            files={"file": f},
        )
    data = resp.json()
    if "error" in data:
        return "Unknown Food", 0, "Couldn't analyze."

    food = data[0]["label"]
    confidence = data[0]["score"]

    cal = random.randint(150, 600) if confidence < 0.8 else random.randint(80, 450)
    msg = "Good for your goal" if cal < 400 else "Too high calorie"
    return food, cal, msg
