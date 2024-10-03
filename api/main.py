import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import google.generativeai as genai

# Configurer l'API de Gemini avec votre clé API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Créer le répertoire 'uploads' s'il n'existe pas
upload_folder = '/opt/render/project/src/uploads'  # Utilisez un chemin absolu dans l'environnement de déploiement
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

# Autoriser certains types de fichiers
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

# Fonction pour vérifier si le fichier a une extension valide
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Créer l'application Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16 Mo pour les fichiers

# Route pour /api/image - Pour télécharger l'image et envoyer un prompt
@app.route('/api/image', methods=['POST'])
def api_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file part"}), 400

    image_file = request.files['image']
    prompt = request.form.get('prompt', '')

    if image_file and allowed_file(image_file.filename):
        # Sécuriser le nom du fichier
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Sauvegarder le fichier image dans le répertoire 'uploads/'
        image_file.save(image_path)
        print(f"Image sauvegardée sous {image_path}")

        # Interagir avec l'API Gemini
        # Assurez-vous d'avoir mis en place votre logique pour gérer la réponse ici
        # Cette section peut être adaptée selon vos besoins pour analyser ou utiliser l'image

        try:
            chat_session = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 8192,
                    "response_mime_type": "text/plain",
                }
            ).start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [image_path, prompt],
                    },
                ]
            )

            # Envoyer un message et obtenir la réponse
            response = chat_session.send_message(prompt)

            return jsonify({"response": response.text}), 200

        except Exception as e:
            print(f"Erreur lors de l'interaction avec Gemini: {e}")
            return jsonify({"error": "Une erreur est survenue avec l'API Gemini"}), 500

    else:
        return jsonify({"error": "Fichier non autorisé"}), 400


# Route pour /ask - Pour poser des questions et obtenir une réponse textuelle
@app.route('/ask', methods=['POST'])
def ask():
    prompt = request.form.get('prompt', '')

    if prompt:
        try:
            # Créer une session de chat et envoyer un message
            chat_session = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 8192,
                    "response_mime_type": "text/plain",
                }
            ).start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [prompt],
                    },
                ]
            )

            # Envoyer un message et obtenir la réponse
            response = chat_session.send_message(prompt)

            return jsonify({"response": response.text}), 200

        except Exception as e:
            print(f"Erreur lors de l'interaction avec Gemini: {e}")
            return jsonify({"error": "Une erreur est survenue avec l'API Gemini"}), 500
    else:
        return jsonify({"error": "Aucun prompt fourni"}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
