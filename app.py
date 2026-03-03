from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
from difflib import SequenceMatcher
from dotenv import load_dotenv
from database import load_training_data, add_qa_pair, delete_qa_pair, init_storage

load_dotenv()

app = Flask(__name__)

# ── Configuration ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
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
- Capabilities: Text & voice Q&A. You understand English, Hindi, and Kannada.

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

# Language-specific instructions injected into the conversation
LANG_INSTRUCTIONS = {
    'hi-IN': '[RESPOND IN HINDI using Devanagari script (हिन्दी). Keep it conversational and natural.]',
    'kn-IN': '[RESPOND IN KANNADA using Kannada script (ಕನ್ನಡ). Keep it conversational and natural.]',
    'en-IN': '',  # Default English, no extra instruction needed
}

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

def chat_with_groq(message, lang='en-IN'):
    """Send a message using Groq and maintain conversation history."""
    global conversation_history

    # Prepend language instruction if not English
    lang_instruction = LANG_INSTRUCTIONS.get(lang, '')
    full_message = f"{lang_instruction}\n{message}" if lang_instruction else message

    conversation_history.append({
        "role": "user",
        "content": full_message
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
# (load_training_data, add_qa_pair, delete_qa_pair imported from database.py)

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
    lang = data.get('lang', 'en-IN')  # Language hint from the frontend dropdown
    if not message:
        return jsonify({'error': 'Empty message'}), 400

    # 1) Check personal training data first
    trained_answer = find_matching_qa(message)
    if trained_answer:
        return jsonify({'response': trained_answer, 'source': 'trained', 'lang': lang})

    # 2) Fall back to Groq AI
    if not client:
        return jsonify({
            'response': "I'm not fully configured yet. Please add your GROQ_API_KEY to a `.env` file and restart the server.",
            'source': 'error',
            'lang': lang
        })

    try:
        response_text = chat_with_groq(message, lang)
        return jsonify({'response': response_text, 'source': 'ai', 'lang': lang})
    except Exception as e:
        return jsonify({'response': f"Sorry, I encountered an error: {str(e)}", 'source': 'error', 'lang': lang})

@app.route('/api/train', methods=['POST'])
def train():
    data = request.json
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    if not question or not answer:
        return jsonify({'error': 'Both question and answer are required'}), 400

    new_id = add_qa_pair(question, answer)
    return jsonify({'success': True, 'id': new_id})

@app.route('/api/training-data', methods=['GET'])
def get_training_data():
    return jsonify(load_training_data())

@app.route('/api/training-data/<int:qa_id>', methods=['DELETE'])
def delete_training_data(qa_id):
    delete_qa_pair(qa_id)
    return jsonify({'success': True})

@app.route('/api/reset', methods=['POST'])
def reset_chat():
    global conversation_history
    conversation_history = []
    return jsonify({'success': True})

# ── Initialize on import (works with both dev server and gunicorn) ──
try:
    init_storage()
    init_groq()
except Exception as e:
    print(f"⚠️  Init warning: {e}")

# ── Main ───────────────────────────────────────────────────────
if __name__ == '__main__':
    groq_ok = client is not None
    port = int(os.environ.get('PORT', 5001))

    # Check for SSL certs (required for microphone access on mobile browsers)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cert_file = os.path.join(base_dir, 'cert.pem')
    key_file = os.path.join(base_dir, 'key.pem')
    use_ssl = os.path.exists(cert_file) and os.path.exists(key_file)

    protocol = 'https' if use_ssl else 'http'
    from database import use_database
    storage = 'PostgreSQL (Supabase)' if use_database() else 'Local JSON file'
    print("\n🤖  Navis AI Assistant")
    print(f"   AI Engine: {'✅ Groq (' + MODEL + ')' if groq_ok else '❌ No key — set GROQ_API_KEY in .env'}")
    print(f"   Storage: {storage}")
    if use_ssl:
        print(f"   🔒 HTTPS: Enabled (microphone will work on mobile)")
    else:
        print(f"   ⚠️  No SSL certs — run with HTTPS for mobile mic access")
    print(f"   🌐 Open: {protocol}://localhost:{port}\n")

    if use_ssl:
        app.run(debug=True, host='0.0.0.0', port=port, ssl_context=(cert_file, key_file))
    else:
        app.run(debug=True, host='0.0.0.0', port=port)
