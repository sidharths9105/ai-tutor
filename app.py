import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up the Flask app
app = Flask(__name__)

# Configure the Gemini API
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
    # Initialize the model
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    # Use a fallback or handle the error appropriately
    model = None

# This is the original logic from your script, now as functions
def generate_lesson_content(topic: str, level: str, subject: str) -> str:
    """Generate a lesson on the given topic"""
    if not model:
        return "Error: Generative model is not initialized."
    
    prompt = f"""
    Create a comprehensive English lesson on {topic} for a {level} level student.
    Subject: {subject}
    
    Include:
    1) Clear Learning Objectives
    2) Detailed Explanation with examples
    3) Practical Applications
    4) Summary of Key Concepts
    5) Common mistakes to avoid
    
    Keep it between 400-500 words and use simple language.
    Use Markdown for formatting (e.g., **bold**, *italics*, lists).
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred while generating the lesson: {e}"

def generate_quiz_data(topic: str, level: str, subject: str) -> dict:
    """Generate a quiz on the given topic"""
    if not model:
        return {"error": "Generative model is not initialized."}

    prompt = f"""
    Create a 5-question assessment on {topic} ({subject}) for {level} level students.
    Include multiple choice questions with 4 options each.
    Format the entire output as a single, valid JSON object with a root key "questions".
    The "questions" key should be a list of question objects.
    Each question object must have these keys: "question", "options" (a list of 4 strings), "answer" (the correct string from options), and "explanation".
    
    Make questions progressively harder and provide clear explanations for answers.
    Do not include any text or formatting before or after the JSON object.
    """
    try:
        response = model.generate_content(prompt)
        # Clean up the response to ensure it's valid JSON
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except Exception as e:
        print(f"Error generating or parsing quiz JSON: {e}")
        # Return a fallback quiz structure on error
        return {
            "questions": [
                {
                    "question": f"Could not generate a quiz for {topic}. Please try again.",
                    "options": ["N/A", "N/A", "N/A", "N/A"],
                    "answer": "N/A",
                    "explanation": "There was an error communicating with the AI model to generate the quiz."
                }
            ]
        }

# --- Flask Routes ---

@app.route('/')
def index():
    """Render the main HTML page."""
    return render_template('index.html')

@app.route('/generate_lesson', methods=['POST'])
def handle_lesson():
    """Handle the lesson generation request from the frontend."""
    data = request.json
    lesson = generate_lesson_content(data['topic'], data['level'], data['subject'])
    return jsonify({'lesson_html': lesson})

@app.route('/generate_quiz', methods=['POST'])
def handle_quiz():
    """Handle the quiz generation request from the frontend."""
    data = request.json
    quiz_data = generate_quiz_data(data['topic'], data['level'], data['subject'])
    return jsonify(quiz_data)

# To run this app locally for testing:
if __name__ == '__main__':
    app.run(debug=True, port=5001)
