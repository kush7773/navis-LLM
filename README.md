# 🤖 Navis – AI Assistant

> Built by **Robo Manthan** × **BNMIT, Bangalore**

Navis is an AI-powered assistant with voice input/output, trainable Q&A, and a sleek dark-theme UI. Powered by **Groq's Llama 3.3 70B** model for ultra-fast responses.

![Navis Screenshot](https://img.shields.io/badge/AI-Groq%20Llama%203.3-blue) ![Python](https://img.shields.io/badge/Python-3.9+-green) ![Flask](https://img.shields.io/badge/Flask-Backend-red)

---

## ✨ Features

- 🧠 **AI Chat** — Powered by Groq (Llama 3.3 70B Versatile)
- 🎙️ **Voice Input** — Speak your questions using the microphone
- 🔊 **Voice Output** — Always-on text-to-speech replies
- 🎓 **Trainable** — Add custom Q&A pairs via the Train panel
- ⏹️ **Stop Button** — Interrupt AI responses and voice mid-speech
- 📱 **Cross-Platform** — Works on desktop, mobile, and tablet
- 🌙 **Dark Theme** — Premium glassmorphism UI with animations

---

## 🚀 Run Locally

### Prerequisites

- **Python 3.9+** installed ([download](https://www.python.org/downloads/))
- A **Groq API key** (free at [console.groq.com](https://console.groq.com))

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/kush7773/navis-LLM.git
cd navis-LLM

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate the virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create your .env file with your Groq API key
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```

> 💡 Get a free Groq API key at [console.groq.com/keys](https://console.groq.com/keys)

### Run

```bash
python app.py
```

Open **http://localhost:5001** in your browser. That's it! 🎉

---

## 📁 Project Structure

```
navis-LLM/
├── app.py                  # Flask backend + Groq AI integration
├── training_data.json      # Custom Q&A training pairs
├── requirements.txt        # Python dependencies
├── render.yaml             # Render.com deployment config
├── .env                    # API keys (not in git)
├── .env.example            # Template for .env
├── templates/
│   └── index.html          # Main page
└── static/
    ├── css/style.css       # Dark theme styles
    ├── js/app.js           # Frontend logic (chat, voice, training)
    └── images/             # Logos
```

---

## 🎓 Training Navis

1. Click the **🧠 Train** button in the top-right
2. Enter a **Question** and **Answer**
3. Click **Save** — Navis will use this for matching questions
4. Trained answers show a 🎓 badge; AI answers show ✨

---

## 🌐 Deploy Online (Free)

### Render.com

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo
4. Set **Start Command**: `gunicorn app:app`
5. Add environment variable: `GROQ_API_KEY` = your key
6. Deploy! 🚀

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask (Python) |
| AI Model | Llama 3.3 70B via Groq |
| Frontend | HTML, CSS, JavaScript |
| Voice | Web Speech API |
| Deployment | Gunicorn + Render |

---

## 📝 Environment Variables

| Variable | Description | Required |
|----------|------------|----------|
| `GROQ_API_KEY` | Your Groq API key | ✅ Yes |
| `PORT` | Server port (default: 5001) | ❌ No |

---

## 👥 Team

- **Robo Manthan** — Robotics & AI Company, Bengaluru
- **BNMIT** — B.N.M. Institute of Technology, Bangalore

---

*Made with ❤️ by the Robo Manthan team*
