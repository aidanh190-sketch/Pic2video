import os, time, tempfile
from flask import Flask, render_template, request, send_file, abort
from werkzeug.utils import secure_filename
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()
ALLOWED_IMG = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def allowed_image(fn): 
    return os.path.splitext(fn)[1].lower() in ALLOWED_IMG

def make_video(image, text, secs, music=None):
    W, H = 1080, 1920  # vertical video; change to 1920,1080 for landscape
    base = ImageClip(image).resize(height=H).on_color(size=(W,H), color=(0,0,0), pos="center").set_duration(secs)
    clips=[base]
    if text.strip():
        caption = TextClip(text, fontsize=60, color="white", stroke_color="black",
                           stroke_width=3, method="caption", size=(W-120,None)
                          ).set_duration(secs).set_position(("center", H*0.82))
        clips.append(caption)
    video = CompositeVideoClip(clips, size=(W,H))
    if music and os.path.exists(music):
        audio = AudioFileClip(music).volumex(0.85)
        audio = audio.loop(duration=secs) if audio.duration < secs else audio.subclip(0,secs)
        video = video.set_audio(audio)
    out = os.path.join(tempfile.gettempdir(), f"vid_{int(time.time())}.mp4")
    video.write_videofile(out, fps=30, codec="libx264", audio_codec="aac")
    return out

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/render", methods=["POST"])
def render_vid():
    if "image" not in request.files: abort(400, "No image.")
    f = request.files["image"]
    if not f or f.filename == "": abort(400, "Empty file.")
    if not allowed_image(f.filename): abort(400, "Unsupported format.")
    desc = request.form.get("description", "")
    secs = float(request.form.get("seconds", "3") or 3)
    music = request.files.get("music")
    img = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(f.filename)); f.save(img)
    mpath = None
    if music and music.filename:
        mpath = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(music.filename)); music.save(mpath)
    out = make_video(img, desc, secs, mpath)
    return send_file(out, as_attachment=True, download_name="your_video.mp4")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
