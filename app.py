from flask import Flask, render_template, redirect, url_for, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from video_tools import trim_video, split_video, add_captions, mute_audio, add_background_music
from config import Config
from werkzeug.utils import secure_filename
from gtts import gTTS
import os
import re

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager = LoginManager(app)

chat_history = []

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(username=request.form['username'], password=request.form['password'])
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    video_path = None
    response = None
    history = []

    if request.method == "POST" and "video" in request.files:
        video = request.files["video"]
        upload_path = os.path.join("static", "uploads", secure_filename(video.filename))
        video.save(upload_path)
        video_path = "/" + upload_path.replace("\\", "/")

    trimmed_exists = os.path.exists("static/previews/trimmed.mp4")
    voice_exists = os.path.exists("static/previews/voice.mp3")
    captioned_exists = os.path.exists("static/previews/captioned.mp4")
    split_exists = os.path.exists("static/previews/split_part1.mp4") and os.path.exists("static/previews/split_part2.mp4")
    muted_exists = os.path.exists("static/previews/muted.mp4")
    music_exists = os.path.exists("static/previews/music_added.mp4")

    return render_template("dashboard.html",
        video_path=video_path,
        trimmed_exists=trimmed_exists,
        voice_exists=voice_exists,
        captioned_exists=captioned_exists,
        split_exists=split_exists,
        muted_exists=muted_exists,
        music_exists=music_exists,
        response=response,
        history=history,
        current_user=current_user
    )

@app.route('/trim', methods=['POST'])
def trim():
    url_path = request.form['path']
    filename = os.path.basename(url_path)
    real_path = os.path.join("static", "uploads", secure_filename(filename))

    start = int(request.form['start'])
    end = int(request.form['end'])

    output = trim_video(real_path, start, end)
    return send_file(output)

@app.route('/voice', methods=['POST'])
def voice():
    text = request.form['text']
    tts = gTTS(text=text, lang='en')
    output_path = "static/previews/voice.mp3"
    tts.save(output_path)

    trimmed_exists = os.path.exists("static/previews/trimmed.mp4")
    voice_exists = os.path.exists(output_path)

    return render_template("dashboard.html",
        video_path="/static/uploads/videoplayback.mp4",
        trimmed_exists=trimmed_exists,
        voice_exists=voice_exists,
        captioned_exists=os.path.exists("static/previews/captioned.mp4"),
        split_exists=os.path.exists("static/previews/split_part1.mp4") and os.path.exists("static/previews/split_part2.mp4"),
        muted_exists=os.path.exists("static/previews/muted.mp4"),
        music_exists=os.path.exists("static/previews/music_added.mp4"),
        response="Voiceover generated!",
        history=[],
        current_user=current_user
    )

@app.route("/chat", methods=["POST"])
def chat():
    prompt = request.form["prompt"]
    video_path = "static/uploads/videoplayback.mp4"

    trimmed_exists = False
    voice_exists = os.path.exists("static/previews/voice.mp3")
    captioned_exists = False
    split_exists = False
    muted_exists = False
    music_exists = False
    response = ""

    match = re.search(r"trim.*?(\d+).*?(\d+)", prompt.lower())
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        trim_video(video_path, start, end)
        trimmed_exists = True
        response = f"Trimmed video from {start} to {end} seconds."

    elif "split" in prompt.lower():
        match = re.search(r"split.*?(\d+)", prompt.lower())
        if match:
            time = int(match.group(1))
            split_video(video_path, time)
            split_exists = True
            response = f"Video split at {time} seconds."

    elif "caption" in prompt.lower() or "subtitle" in prompt.lower():
        match = re.search(r"(caption|subtitle).*?:\s*(.+)", prompt.lower())
        if match:
            text = match.group(2)
            add_captions(video_path, text)
            captioned_exists = True
            response = f"Caption added: {text}"

    elif "mute" in prompt.lower():
        mute_audio(video_path)
        muted_exists = True
        response = "Muted the video."

    elif "music" in prompt.lower():
        music_path = "static/audio/background.mp3"
        add_background_music(video_path, music_path)
        music_exists = True
        response = "Background music added."

    else:
        response = "Sorry, I didn't understand that command. Try 'Trim from 5 to 10 seconds' or 'Add captions: Hello world'."

    return render_template("dashboard.html",
        video_path="/" + video_path,
        trimmed_exists=trimmed_exists,
        voice_exists=voice_exists,
        captioned_exists=captioned_exists,
        split_exists=split_exists,
        muted_exists=muted_exists,
        music_exists=music_exists,
        response=response,
        history=[{"command": prompt, "response": response}],
        current_user=current_user
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
