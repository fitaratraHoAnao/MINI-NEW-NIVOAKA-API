import os
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

# Configuration de l'API Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialisation de l'application Flask
app = Flask(__name__)

# Définition du modèle Gemini
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Fonction pour télécharger un fichier vers Gemini
def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

@app.route('/ask', methods=['POST'])
def ask():
    """Route pour envoyer un prompt et recevoir une réponse"""
    data = request.get_json()
    user_input = data.get('prompt', '')
    
    if not user_input:
        return jsonify({"error": "Prompt is required"}), 400

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [user_input],
            }
        ]
    )
    
    response = chat_session.send_message(user_input)
    return jsonify({"response": response.text})


@app.route('/api/image', methods=['POST'])
def api_image():
    """Route pour envoyer une image avec un prompt et discuter continuellement"""
    if 'image' not in request.files:
        return jsonify({"error": "Image is required"}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filename = secure_filename(image_file.filename)
    image_file.save(os.path.join('uploads', filename))
    
    # Upload the image to Gemini
    uploaded_image = upload_to_gemini(os.path.join('uploads', filename), mime_type=image_file.content_type)
    
    user_input = request.form.get('prompt', '')
    if not user_input:
        return jsonify({"error": "Prompt is required"}), 400

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [uploaded_image, user_input],
            }
        ]
    )
    
    response = chat_session.send_message(user_input)
    return jsonify({"response": response.text})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
