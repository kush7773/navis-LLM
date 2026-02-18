from flask import Flask, render_template, request, jsonify
from groq import Groq
import json
import os
from difflib import SequenceMatcher
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── Configuration ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAINING_DATA_FILE = os.path.join(BASE_DIR, 'training_data.json')
SIMILARITY_THRESHOLD = 0.72
MODEL = "llama-3.3-70b-versatile"  # Latest, most capable free model on Groq

SYSTEM_PROMPT = """You are Navis, an advanced AI assistant developed by Robo Manthan in collaboration with BNMIT, Bangalore.

Your personality:
- Professional yet friendly and approachable
- Knowledgeable across a wide range of topics
- Clear, concise, and helpful
- Proud of being created by the Robo Manthan team

About you:
- Name: Navis
- Created by: Rahul and the Robo Manthan team
- Capabilities: Text & voice Q&A, trainable with personal knowledge

About Robo Manthan (Robomanthan Pvt. Ltd.):
- An Indian robotech company specializing in robotics, AI, machine learning, and embedded product development
- CEO: Saurav Kumar | CTO: Tanuj Kashyap
- Incubated at IIT Patna, headquartered in Bengaluru (BTM 2nd Stage)
- Incorporated: January 8, 2021
- Motto: 'आपके उन्नति का साथी' (Your partner in progress)
- Products: Humanoid robots, autonomous systems, smart wheelchairs, educational robotics kits
- Services: STEM education, workshops, internships, ATAL Tinkering Labs, 50+ college MoUs

About BNMIT (B.N.M. Institute of Technology):
- A separate entity — a private engineering college in Banashankari II Stage, Bangalore
- Established: 2001 by Bhageerathi Bai Narayana Rao Maanay Charities (est. 1972)
- Principal: Dr. S. Y. Kulkarni
- NAAC 'A' Grade (valid until Dec 2026), NBA accredited, AICTE approved
- Departments: CSE, AI&ML, ECE, EEE, ISE, Mechanical, MBA, Basic Sciences
- Robo Manthan and BNMIT collaborate on robotics projects and student training

IMPORTANT: Robo Manthan is a COMPANY, BNMIT is a COLLEGE. They are tied up through collaboration but are separate entities.

Keep responses concise but thorough. Use markdown formatting when helpful. Your answers will be spoken aloud, so keep them conversational."""

# ── Groq Init ─────────────────────────────────────────────────
client = None
conversation_history = []

def init_groq():
    global client, conversation_history
    if GROQ_API_KEY:
        client = Groq(api_key=GROQ_API_KEY)
        conversation_history = []
        return True
    return False

def chat_with_groq(message):
    """Send a message using Groq and maintain conversation history."""
    global conversation_history

    conversation_history.append({
        "role": "user",
        "content": message
    })

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=2048,
    )

    assistant_text = response.choices[0].message.content
    conversation_history.append({
        "role": "assistant",
        "content": assistant_text
    })

    # Keep conversation manageable (last 20 exchanges)
    if len(conversation_history) > 40:
        conversation_history = conversation_history[-40:]

    return assistant_text

# ── Training Data Helpers ──────────────────────────────────────
def load_training_data():
    if os.path.exists(TRAINING_DATA_FILE):
        with open(TRAINING_DATA_FILE, 'r') as f:
            return json.load(f)
    return {"qa_pairs": []}

def save_training_data(data):
    with open(TRAINING_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def find_matching_qa(question):
    """Find the best matching trained Q&A for a given question."""
    data = load_training_data()
    q_lower = question.lower().strip()

    best_match = None
    best_score = 0

    for qa in data.get('qa_pairs', []):
        trained_q = qa['question'].lower().strip()

        # Sequence similarity
        seq_score = SequenceMatcher(None, q_lower, trained_q).ratio()

        # Keyword overlap boost
        t_words = set(trained_q.split())
        q_words = set(q_lower.split())
        overlap = len(t_words & q_words) / max(len(t_words), 1)
        combined = (seq_score + overlap) / 2

        if combined > best_score:
            best_score = combined
            best_match = qa

    if best_score >= SIMILARITY_THRESHOLD and best_match:
        return best_match['answer']
    return None

# ── Routes ─────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'model': MODEL, 'groq': client is not None})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Empty message'}), 400

    # 1) Check personal training data first
    trained_answer = find_matching_qa(message)
    if trained_answer:
        return jsonify({'response': trained_answer, 'source': 'trained'})

    # 2) Fall back to Groq AI
    if not client:
        return jsonify({
            'response': "I'm not fully configured yet. Please add your GROQ_API_KEY to a `.env` file and restart the server.",
            'source': 'error'
        })

    try:
        response_text = chat_with_groq(message)
        return jsonify({'response': response_text, 'source': 'ai'})
    except Exception as e:
        return jsonify({'response': f"Sorry, I encountered an error: {str(e)}", 'source': 'error'})

@app.route('/api/train', methods=['POST'])
def train():
    data = request.json
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    if not question or not answer:
        return jsonify({'error': 'Both question and answer are required'}), 400

    training_data = load_training_data()
    new_id = max((qa.get('id', 0) for qa in training_data['qa_pairs']), default=0) + 1
    training_data['qa_pairs'].append({'question': question, 'answer': answer, 'id': new_id})
    save_training_data(training_data)
    return jsonify({'success': True, 'id': new_id})

@app.route('/api/training-data', methods=['GET'])
def get_training_data():
    return jsonify(load_training_data())

@app.route('/api/training-data/<int:qa_id>', methods=['DELETE'])
def delete_training_data(qa_id):
    data = load_training_data()
    data['qa_pairs'] = [qa for qa in data['qa_pairs'] if qa.get('id') != qa_id]
    save_training_data(data)
    return jsonify({'success': True})

@app.route('/api/reset', methods=['POST'])
def reset_chat():
    global conversation_history
    conversation_history = []
    return jsonify({'success': True})

# ── Initialize on import (works with both dev server and gunicorn) ──
try:
    if not os.path.exists(TRAINING_DATA_FILE):
        save_training_data({"qa_pairs": []})
    init_groq()
except Exception as e:
    print(f"⚠️  Init warning: {e}")

# ── Main ───────────────────────────────────────────────────────
if __name__ == '__main__':
    groq_ok = client is not None
    port = int(os.environ.get('PORT', 5001))
    print("\n🤖  Navis AI Assistant")
    print(f"   AI Engine: {'✅ Groq (' + MODEL + ')' if groq_ok else '❌ No key — set GROQ_API_KEY in .env'}")
    print(f"   Training Data: {TRAINING_DATA_FILE}")
    print(f"   🌐 Open: http://localhost:{port}\n")
    app.run(debug=True, host='0.0.0.0', port=port)
