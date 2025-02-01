import os
import logging
import googlemaps
import requests
import openai
import anthropic
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv  # Load environment variables
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ✅ Load environment variables from .env file
load_dotenv()

# ✅ Secure API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
MEDICINE_API_URL = os.getenv("MEDICINE_API_URL", "https://api.example.com/medicines")

# ✅ Initialize APIs
openai.api_key = OPENAI_API_KEY
gmaps = googlemaps.Client(key="AIzaSyC1ROYF-7Qgq3k3jZLbIyd3z8_GewfcE8w")
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ✅ Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Flask App
app = Flask(__name__)

@app.route('/')
def home():
    return "Healthcare AI API is running!"

# ✅ AI-based Disease Prediction
@app.route('/predict_disease', methods=['POST'])
def predict_disease():
    data = request.json
    symptoms = data.get("symptoms", "")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Predict disease from symptoms: {symptoms}"}]
        )
        return jsonify({"disease_prediction": response['choices'][0]['message']['content']})
    except Exception as e:
        logger.error(f"Error predicting disease: {e}")
        return jsonify({"error": "Unable to predict disease at the moment."})

# ✅ Find Nearby Hospitals
@app.route('/find_hospitals', methods=['POST'])
def find_hospitals():
    data = request.json
    location = data.get("location", "New York")

    try:
        places = gmaps.places_nearby(location, radius=5000, type="hospital")
        hospitals = [place["name"] for place in places["results"][:3]]
        return jsonify({"nearby_hospitals": hospitals})
    except Exception as e:
        logger.error(f"Error finding hospitals: {e}")
        return jsonify({"error": "Unable to find hospitals."})

# ✅ Get Medicine Suggestions
@app.route('/get_medicine', methods=['POST'])
def get_medicine():
    data = request.json
    disease = data.get("disease", "")

    try:
        response = requests.get(f"{MEDICINE_API_URL}?query={disease}")
        data = response.json()
        return jsonify({"medicines": data.get("medicines", ["No medicine found"])[:3]})
    except Exception as e:
        logger.error(f"Error fetching medicines: {e}")
        return jsonify({"error": "Unable to fetch medicines."})

# ✅ Skin Disease Detection (Placeholder)
@app.route('/detect_skin_disease', methods=['POST'])
def detect_skin_disease():
    return jsonify({"skin_analysis": "Please consult a dermatologist for a professional diagnosis."})

# ✅ Claude AI Integration
def interact_with_claude(prompt):
    try:
        response = claude_client.messages.create(
            model="claude-v1",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content
    except Exception as e:
        logger.error(f"Error interacting with Claude API: {e}")
        return None

# ✅ Telegram Bot Setup
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    response = predict_disease_text(user_input)
    await update.message.reply_text(response)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    image_stream = BytesIO()
    await photo.download(out=image_stream)
    image_bytes = image_stream.getvalue()

    result = detect_skin_disease()
    await update.message.reply_text(f"🩺 Detected Condition: {result}")

def predict_disease_text(symptoms):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Predict disease from symptoms: {symptoms}"}]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Error predicting disease: {e}")
        return "Unable to predict disease at the moment."

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Hello! Send symptoms or an image.")))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.run_polling()

# ✅ Run Flask Server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)