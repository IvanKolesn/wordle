"""Browser-based UI for playing Wordle locally."""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request, render_template_string

from wordle import corpus
from wordle.models import simple_solver as slv
from .env import ALPHABET_EN, ALPHABET_RU, WordleEnv


_ALPHABETS = {"en": ALPHABET_EN, "ru": ALPHABET_RU}
_CORPORA = {
    "en": Path(__file__).parent / "corpus" / "english.txt",
    "ru": Path(__file__).parent / "corpus" / "russian.txt",
}

_HTML = r"""<!doctype html>
<html lang="{{ language }}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wordle</title>
<style>
body{font-family:system-ui,sans-serif;max-width:520px;margin:30px auto;padding:0 16px;text-align:center;background:#fafafa;color:#222}
h1{margin-bottom:8px}.sub{color:#666}.board{display:grid;gap:6px;margin:24px auto;width:min(330px,90vw)}
.row{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}.tile{aspect-ratio:1;border:2px solid #ccc;display:grid;place-items:center;font-size:28px;font-weight:700;text-transform:uppercase;background:white}
.green{background:#6aaa64;color:white;border-color:#6aaa64}.yellow{background:#c9b458;color:white;border-color:#c9b458}.gray{background:#787c7e;color:white;border-color:#787c7e}
form{display:flex;gap:8px;justify-content:center}.guess{font-size:18px;padding:10px;width:180px;text-transform:lowercase}.btn{padding:10px 16px;font-weight:700;cursor:pointer}.message{min-height:28px;margin:14px}.hint{margin:10px}.new{margin-top:10px}.lang{margin:10px}
</style></head>
<body>
<h1>Wordle</h1><div class="sub">{{ 'English' if language == 'en' else 'Русский' }}</div>
<div id="board" class="board"></div>
<form id="form"><input id="guess" class="guess" maxlength="5" autocomplete="off" autofocus><button class="btn">Guess</button></form>
<div id="message" class="message"></div><button id="hint" class="btn hint">Hint</button><button id="new" class="btn new">New game</button>
<script>
const lang={{ language|tojson }};
const board=document.getElementById('board'), msg=document.getElementById('message'), input=document.getElementById('guess');
function draw(data){board.innerHTML='';for(let r=0;r<6;r++){let row=document.createElement('div');row.className='row';for(let c=0;c<5;c++){let t=document.createElement('div');t.className='tile';if(data.guesses[r]){t.textContent=data.guesses[r][c];let f=data.feedback[r][c];t.classList.add(f==='g'?'green':f==='y'?'yellow':'gray')}row.appendChild(t)}board.appendChild(row)}}
async function state(){let r=await fetch('/api/state');let d=await r.json();draw(d)}
document.getElementById('form').onsubmit=async e=>{e.preventDefault();let r=await fetch('/api/guess',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({guess:input.value})});let d=await r.json();draw(d);msg.textContent=d.message||'';input.value='';input.focus()};
document.getElementById('hint').onclick=async()=>{let r=await fetch('/api/hint');let d=await r.json();msg.textContent='Hint: '+d.word};
document.getElementById('new').onclick=async()=>{await fetch('/api/new',{method:'POST'});msg.textContent='';input.value='';await state();input.focus()};state();
</script></body></html>"""


def _words(language: str) -> list[str]:
    raw = corpus.load_corpus(str(_CORPORA[language]))
    return corpus.clean_corpus(raw, alphabet=set(_ALPHABETS[language]), word_length=5)


def create_app(language: str = "ru") -> Flask:
    """Create a Flask application with one game session."""
    if language not in _CORPORA:
        raise ValueError(f"Unsupported language: {language}")
    words = _words(language)
    env = WordleEnv(words, max_steps=6, word_length=5, alphabet=_ALPHABETS[language])
    _, info = env.reset()
    app = Flask(__name__)

    def state(message: str | None = None):
        return {
            "guesses": env.guesses,
            "feedback": env.feedbacks,
            "candidates": len(env.candidates),
            "message": message,
            "done": env.done,
        }

    @app.get("/")
    def index():
        return render_template_string(_HTML, language=language)

    @app.get("/api/state")
    def api_state():
        return jsonify(state())

    @app.post("/api/new")
    def api_new():
        env.reset()
        return jsonify(state())

    @app.post("/api/guess")
    def api_guess():
        guess = str(request.json.get("guess", "")).strip().lower()
        if len(guess) != 5 or guess not in env.word_to_idx:
            return jsonify(state("That word is not in the dictionary.")), 400
        if env.done:
            return jsonify(state("Start a new game.")), 400
        _, _, terminated, truncated, _ = env.step(env.word_to_idx[guess])
        if terminated:
            message = f"Nice! You guessed it in {env.step_count} tries."
        elif truncated:
            message = f"Out of guesses. The word was {env.target}."
        else:
            message = None
        return jsonify(state(message))

    @app.get("/api/hint")
    def api_hint():
        return jsonify({"word": slv.best_guess(env.candidates)})

    return app


def play(language: str = "ru", host: str = "127.0.0.1", port: int = 5000) -> None:
    """Start the local web UI and open it in the default browser."""
    app = create_app(language)
    url = f"http://{host}:{port}/"
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    app.run(host=host, port=port, debug=False, use_reloader=False)
