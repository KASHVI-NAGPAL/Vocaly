from flask import Flask, render_template, request,jsonify
from pydub import AudioSegment
from difflib import SequenceMatcher
import os
import random
import subprocess
import speech_recognition as sr
app = Flask(__name__)

def load_words(filename):
    with open(filename, "r") as f:
        return f.read().splitlines()
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


# Home page
@app.route('/')
def index():
    practice_words = load_words("words.txt")
    game_words = load_words("words_game.txt")
    quiz_words = load_words("words_quiz.txt")
    test_words = load_words("words_test.txt")

    practice_word = random.choice(practice_words)
    game_word = random.choice(game_words)
    quiz_word = random.choice(quiz_words)
    test_word = random.choice(test_words)

    # Safely select wrong options (if enough words exist)
    wrong_game = random.sample([w for w in game_words if w != game_word], min(2, len(game_words)-1))
    wrong_quiz = random.sample([w for w in quiz_words if w != quiz_word], min(2, len(quiz_words)-1))

    # Ensure at least empty list
    if len(wrong_game) < 2: wrong_game += [""] * (2 - len(wrong_game))
    if len(wrong_quiz) < 2: wrong_quiz += [""] * (2 - len(wrong_quiz))

    return render_template(
        "index.html",
        practice_word=practice_word,
        game_word=game_word,
        wrong_game=wrong_game,
        quiz_word=quiz_word,
        wrong_quiz=wrong_quiz,
        test_word=test_word
    )
# Voice evaluation
@app.route("/analyze", methods=["POST"])
def analyze():
    print("Audio received")
    audio = request.files["audio"]
    webm_path = "static/recording.webm"
    wav_path = "static/recording.wav"
    audio.save(webm_path)
    subprocess.run([
    "ffmpeg",
    "-y",
    "-i", webm_path,
    "-af", "volume=10.0",
    "-ar", "16000",      # sample rate (VERY IMPORTANT)
    "-ac", "1",          # mono audio
    "-c:a", "pcm_s16le", # proper WAV format
    wav_path
], 
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Debug: check file size
    print("WAV File size:", os.path.getsize(wav_path))
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)

    try:
        spoken_text = recognizer.recognize_google(audio_data).lower()
    except sr.UnknownValueError:
        spoken_text = ""

    print("User said:", spoken_text)
    target_word = request.form["target_word"].lower()
    print("Target:", target_word) 
    score = similarity(spoken_text, target_word)
    print("Score:", score)   
    if score>0.8:
        message = f"🎉 Good job! You said {spoken_text} correctly!"
    elif score>0.5:
    	message=f"🙂 Almost there! You said'{spoken_text}'.Try again!"
    else:
        message = f"😊 Try again! The word was {target_word}"

    return jsonify({"message": message})   
if __name__ == '__main__':
    os.makedirs("static", exist_ok=True)
    app.run(debug=True)