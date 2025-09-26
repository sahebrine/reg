import random
import secrets
import string
import uuid
import hashlib
from datetime import datetime, timedelta, UTC
from flask import Flask, request, render_template_string, redirect, url_for, Response, make_response
import subprocess
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "REGSAHEOLDBESTTEDLOL"
DATABASE_URL = os.getenv("mysql://root:CUZCiplwhyNGkRMvHCXpyYIdfecCeOEF@shortline.proxy.rlwy.net:27996/")
if DATABASE_URL and DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
class Key(db.Model):
    __tablename__ = "keys"
    key = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(64))
    expires_at = db.Column(db.DateTime(timezone=True))
    device_token = db.Column(db.String(64), nullable=True)
    used = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()
sessions = {}
def generate_code(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def make_device_token():
    return uuid.uuid4().hex

def short_ua_hash(user_agent: str):
    return hashlib.sha256(user_agent.encode(errors="ignore")).hexdigest()[:32]

def is_request_from_same_device(device_info, request):
    ua_hash = short_ua_hash(request.headers.get("User-Agent", ""))
    ip = request.remote_addr or ""
    if device_info["user_agent_hash"] != ua_hash:
        return False
    if device_info["ip"] != ip:
        return False
    return True
def require_activation(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        device_token = request.cookies.get("device_token", "")
        if not device_token:
            return redirect(url_for("activate", next=request.path))

        key = Key.query.filter_by(device_token=device_token).first()
        if not key:
            return redirect(url_for("activate", next=request.path))

        if datetime.now(UTC) > key.expires_at:
            return render_template_string(base_template.replace(
                "{% block content %}{% endblock %}",
                "<h2>Activation expired</h2><p>Key expired or session timed out.</p><a href='/' class='btn'>Activate</a>"
            ))

        return f(*args, **kwargs)
    return wrapped
@app.route("/create_key", methods=["POST"])
def create_key():
	data = request.get_json()
	name = data.get("name")
	duration = data.get("date") 
	amount, unit = duration.split()
	amount = int(amount)
	expires_at = None
	unit_symbol = None
	if unit.startswith("day"):
		expires_at = datetime.now(UTC) + timedelta(days=amount)
		unit_symbol = "D"
	elif unit.startswith("month"):
		expires_at = datetime.now(UTC) + relativedelta(months=amount)
		unit_symbol = "M"
	elif unit.startswith("year"):
		expires_at = datetime.now(UTC) + relativedelta(years=amount)
		unit_symbol = "Y"
	elif unit.startswith("hour"):
		expires_at = datetime.now(UTC) + timedelta(hours=amount)
		unit_symbol = "H"
	else:
		return {
			"success":False,
			"error": "Invalid duration"
		}, 400
	new_key = f"REG-{amount}{unit_symbol}-{secrets.token_hex(8)}".upper()
	key = Key(key=new_key, name=name, expires_at=expires_at)
	db.session.add(key)
	db.session.commit()
	return {
		"success":True,
		"key": new_key,
		"name": name,
		"expires_at": expires_at.isoformat()
	}, 200

@app.route("/", methods=["GET", "POST"])
def activate():
    error = None
    if request.method == "POST":
        key_str = request.form.get("key", "").strip()
        key = Key.query.filter_by(key=key_str).first()

        if not key:
            error = "❌ Invalid Key"
        else:
            if datetime.now(UTC) > key.expires_at:
                error = "⏳ Key Expired"
            else:
                device_token = request.cookies.get("device_token")
                if key.used and key.device_token != device_token:
                    error = "⚠️ This key is already used on another device"
                else:
                    if not device_token:
                        device_token = secrets.token_hex(16)
                    key.device_token = device_token
                    key.used = 1
                    db.session.commit()

                    resp = make_response(redirect(url_for("reg")))
                    resp.set_cookie("device_token", device_token, max_age=60*60*24*30, httponly=True)
                    return resp

    return render_template_string(base_template.replace("{% block content %}{% endblock %}", f"""
        <h2>Enter Your Activation Key</h2>
        <form method="post">
            <input type="text" name="key" placeholder="">
            <button class="btn" type="submit">Activate</button>
        </form>
        {"<p style='color:red;'>" + error + "</p>" if error else ""}
    """))

@app.route("/reg", methods=["GET", "POST"])
@require_activation
def reg():
    device_token = request.cookies.get("device_token")
    if not device_token:
        return redirect(url_for("activate"))

    key = Key.query.filter_by(device_token=device_token).first()
    if not key:
        return redirect(url_for("activate"))

    remaining = key.expires_at - datetime.now(UTC)
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_left = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"

    if request.method == "POST":
        sessionid = request.form.get("sessionid", "").strip()
        if sessionid:
            code = generate_code(8)
            sessions[code] = sessionid
            return redirect(url_for("result", code=code))

    template = base_template.replace(
        "{% block content %}{% endblock %}",
        f"""
        <div style="max-width: 400px; margin: 30px auto; text-align: center;">
            <div class="info" style="margin-bottom: 15px;">Welcome {key.name}</div>
            <h2 style="margin-bottom: 10px;">Enter Your Sessionid</h2>
            <form method="post">
                <input type="text" name="sessionid" placeholder="" style="margin-bottom: 15px;">
                <button class="btn" type="submit">Register</button>
            </form>
            <p style="font-size: 12px; margin-top: 8px; color: #ccc;">
                Subscription expires in: {time_left}
            </p>
        </div>
        """
    )
    return render_template_string(template)

def generate_output(code):
    if "Thank You For Using" in sessions[code]:
        text = sessions.get(code, "")
        for line in text.splitlines():
            line = line.strip()
            color = "white"
            yield f"data: <span style='color:{color}'>{line}</span><br>\n\n"
    else:
        exe_path = "./test.out"
        process = subprocess.Popen(
            [exe_path, sessions[code]],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore",
            shell=False
        )
        sessions[code] = ""
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            sessions[code] += line + "\n"
            color = "white"
            yield f"data: <span style='color:{color}'>{line}</span><br>\n\n"
        process.stdout.close()
        process.wait()

@app.route("/result/<code>")
@require_activation
def result(code):
    try:
        template = base_template.replace(
            "{% block content %}{% endblock %}",
            f"""
            <h2>Registry Result</h2>
            <div id="log" 
                style="
                    background: #111;
                    color: #fff;
                    padding: 15px;
                    height: 300px;
                    max-width: 300px;
                    margin: 20px auto;
                    overflow-y: auto;
                    font-family: monospace;
                    font-size: 14px;
                    border-radius: 12px;
                    box-shadow: 0 0 15px rgba(255,255,255,0.2);
                ">
            </div>
            <script>
            var source = new EventSource("/stream/{code}");
            source.onmessage = function(event) {{
                var logDiv = document.getElementById("log");
                logDiv.innerHTML += event.data;
                logDiv.scrollTop = logDiv.scrollHeight;
            }};
            source.onerror = function() {{
                source.close();
            }};
            </script>
            """
        )
        return render_template_string(template)
    except:
        template = base_template.replace(
        "{% block content %}{% endblock %}",
            f"""
            <h2>Something went wrong</h2>
            <div style="margin-top:20px;">
                <a href="/reg" class="btn" style="
                    display:inline-block;
                    text-decoration:none;
                    text-align:center;
                ">Go Home</a>
            </div>
            """
        )
        return render_template_string(template)

@app.route("/stream/<code>")
def stream(code):
    return Response(generate_output(code), mimetype="text/event-stream")

base_template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Zayrix | Register</title>
<link rel="icon" type="image/png" href="https://i.imgur.com/6UAme8g.png">
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Poppins:wght@400;600;700&display=swap');

body {
    margin: 0;
    padding: 0;
    font-family: 'Poppins', sans-serif;
    text-align: center;
    color: #fff;
    background: linear-gradient(
        270deg,
        #000000, #050505, #0a0a0a, #0f0f0f,
        #141414, #1a1a1a, #202020, #000000
    );
    background-size: 1600% 1600%;
    animation: blackGradient 25s ease infinite;
}
@keyframes blackGradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.header {
    padding: 15px;
    border-bottom: 1px solid #ffffff22;
}
.logo {
    width: 90px;
    height: 90px;
}
.info {
    font-size: 14px;
    margin-top: 5px;
    font-weight: 600;
    background: linear-gradient(270deg, #ffffff, #aaaaaa, #666666, #ffffff);
    background-size: 600% 600%;
    animation: textShine 6s linear infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
@keyframes textShine {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

h2 {
    font-family: 'Orbitron', sans-serif;
    font-size: 22px;
    margin: 30px 0 20px;
    text-shadow: 0 0 15px rgba(255,255,255,0.5);
}

form {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 15px;
    margin: 20px;
}

input {
    padding: 12px;
    border-radius: 10px;
    border: none;
    outline: none;
    font-size: 16px;
    width: 85%;
    max-width: 320px;
    text-align: center;
    background: #111;
    color: white;
    box-shadow: 0 0 12px rgba(255,255,255,0.2) inset;
    transition: all 0.3s ease;
}
input:focus {
    box-shadow: 0 0 20px rgba(255,255,255,0.5) inset;
}

.btn {
    position: relative;
    padding: 12px 25px;
    font-size: 18px;
    font-weight: 700;
    font-family: 'Orbitron', sans-serif;
    letter-spacing: 1px;
    cursor: pointer;
    border-radius: 12px;
    border: none;
    color: #fff;
    background: linear-gradient(90deg, #0f0f0f, #1a1a1a, #2a2a2a, #0f0f0f);
    background-size: 400% 400%;
    animation: gradientFlow 8s ease infinite;
    box-shadow: 0 0 15px rgba(255,255,255,0.25), inset 0 0 10px rgba(255,255,255,0.15);
    transition: all 0.3s ease;
    overflow: hidden;
}
.btn::before {
    content: "";
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(120deg, transparent, rgba(255,255,255,0.25), transparent);
    transform: rotate(25deg);
    animation: shine 3s infinite;
}
@keyframes shine {
    0% { transform: translateX(-100%) rotate(25deg); }
    50% { transform: translateX(100%) rotate(25deg); }
    100% { transform: translateX(100%) rotate(25deg); }
}
.btn:hover {
    transform: scale(1.05);
    box-shadow: 0 0 25px rgba(255,255,255,0.6), inset 0 0 20px rgba(255,255,255,0.25);
}

.error-msg {
    margin-top: 15px;
    font-size: 14px;
    font-weight: bold;
    color: #ff4444;
    text-shadow: 0 0 6px #800;
}
.footer {
    margin: 40px 10px;
    font-size: 14px;
    color: rgba(255,255,255,0.8);
}
.footer .credit {
    display: block;
    margin-top: 5px;
    font-size: 13px;
    color: #777;
}
.footer a {
    color: #fff;
    text-decoration: none;
    margin: 0 12px;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}
.footer a:hover {
    text-decoration: underline;
}
.icon {
    width: 20px;
    height: 20px;
}
.footer a:hover { text-decoration: underline; }

.loader {
    border: 4px solid rgba(255, 255, 255, 0.1);
    border-left-color: #fff;
    border-radius: 50%;
    width: 35px;
    height: 35px;
    animation: spin 1s linear infinite;
    margin: 15px auto;
    display: none;
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
</style>
</head>
<body>
    <div class="header">
        <img src="https://i.imgur.com/hxYvvmM.png" class="logo">
        <div class="info">Time: <span id="clock"></span></div>
    </div>

    {% block content %}{% endblock %}

    <div class="footer">
        <a href="https://t.me/xiSahe" target="_blank">
            <svg class="icon" viewBox="0 0 240 240" fill="currentColor">
                <path d="M120,0C53.73,0,0,53.73,0,120s53.73,120,120,120,120-53.73,120-120S186.27,0,120,0Zm58.59,85.75-19.2,90.7c-1.45,6.61-5.34,8.25-10.82,5.14l-29.89-22.05-14.42,13.87c-1.59,1.59-2.92,2.92-5.96,2.92l2.13-30.27,55.11-49.79c2.39-2.13-.52-3.33-3.7-1.2l-68.1,42.91-29.26-9.14c-6.36-2-6.49-6.36,1.33-9.4l114.41-44.1c5.29-1.93,9.92,1.28,8.23,9.4Z"/>
            </svg>
            Telegram
        </a>
        <a href="https://instagram.com/sahe" target="_blank">
            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M7.5 2h9A5.5 5.5 0 0 1 22 7.5v9a5.5 5.5 0 0 1-5.5 5.5h-9A5.5 5.5 0 0 1 2 16.5v-9A5.5 5.5 0 0 1 7.5 2Zm0 2A3.5 3.5 0 0 0 4 7.5v9A3.5 3.5 0 0 0 7.5 20h9a3.5 3.5 0 0 0 3.5-3.5v-9A3.5 3.5 0 0 0 16.5 4h-9ZM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10Zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm5.25-.75a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5Z"/>
            </svg>
            Instagram
        </a>
        <span class="credit">Developed by @sahe</span>
    </div>

<script>
function updateClock() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2,'0');
    const day = String(now.getDate()).padStart(2,'0');
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2,'0');
    const seconds = String(now.getSeconds()).padStart(2,'0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    hours = String(hours).padStart(2,'0');
    document.getElementById("clock").innerText =
        `${year}/${month}/${day} ${hours}:${minutes}:${seconds} ${ampm}`;
}
setInterval(updateClock, 1000);
updateClock();

function showLoader() {
    document.getElementById("loader").style.display = "block";
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
