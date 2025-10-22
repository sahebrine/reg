import html
import subprocess
from flask import Flask, request, render_template_string, redirect, url_for, make_response, Response, session, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta, timezone
import secrets, random, string
from functools import wraps
import certifi
from dateutil.relativedelta import relativedelta
import os
import requests
from werkzeug.utils import secure_filename
sessions = {}
def generate_output(code):
    data = sessions.get(code)
    if not data:
        color = "white"
        yield f"data: <span style='color:{color}'>Code is wrong !</span><br>\n\n"
        return
    typeing = data["type"]
    sessionid = data["sessionid"]
    if "Thank You For Using" in sessions[code]:
        text = sessions.get(code, "")
        for line in text.splitlines():
            line = line.strip()
            color = "white"
            yield f"data: <span style='color:{color}'>{line}</span><br>\n\n"
    else:
        if typeing == "reg":
            name = data["name"]
            bio = data["bio"]
            image_url = data["image_url"]
            exe_path = "./reg.out"
            process = subprocess.Popen(
                [exe_path, sessionid, name, bio, "https://z.zayrix.info" + image_url],
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
        else:
            process = subprocess.Popen(
                ["python3", "./bypass.py", sessionid],
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
app = Flask(__name__)
app.secret_key = "REGSAHEOLDBESTTEDLOL"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
uri = "mongodb+srv://sahebrine_db_user:7XlD1xWNVbFvACFh@cluster0.wemjued.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(
    uri,
    server_api=ServerApi("1"),
    tls=True,
    tlsCAFile=certifi.where()
)
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
db = client["sahebrine_db"] 
keys_col = db["keys"]
DEV_USERNAME = "Sahe"
DEV_PASSWORD = "sahesahe"

def developer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("developer_logged_in"):
            return redirect(url_for("developer_login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/developer/login", methods=["GET", "POST"])
def developer_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == DEV_USERNAME and password == DEV_PASSWORD:
            session["developer_logged_in"] = True
            return redirect(url_for("developer_dashboard"))
        else:
            error = "❌ Wrong username or password"
    return render_template_string(base_template.replace(
        "{% block content %}{% endblock %}",
        f"""
        <h2>Developer Login</h2>
        <form method="post">
            <input type="text" name="username" placeholder="Username">
            <input type="password" name="password" placeholder="Password">
            <button class="btn" type="submit">Login</button>
        </form>
        {"<p style='color:red;'>" + error + "</p>" if error else ""}
        """
    ))
@app.route("/developer")
@developer_required
def developer_dashboard():
    keys = list(keys_col.find())
    rows = ""
    for k in keys:
        expires_at = datetime.fromisoformat(k["expires_at"])
        now = datetime.now(timezone.utc)
        if expires_at > now:
            delta = expires_at - now
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            if days > 0:
                remaining = f"{days} days"
            elif hours > 0:
                remaining = f"{hours} hours"
            else:
                remaining = f"{minutes} minutes"
        else:
            remaining = "Expired"

        status = "✅ Active" if expires_at > now else "❌ Expired"
        used = "🔒 Used" if k.get("used") else "🟢 Open"

        key_value = k.get("key", "")
        key_escaped = html.escape(key_value)
        key_id = f"key-{k['_id']}"

        rows += f"""
        <tr>
            <td>
                <span id="{key_id}" class="key-mask" data-key="{key_escaped}">••••••••••</span>
                <button class="btn-key" onclick="toggleKey('{key_id}')">Show</button>
            </td>
            <td>{k['name']}</td>
            <td>{remaining}</td>
            <td>{status}</td>
            <td>{used}</td>
            <td>
                <a href='/developer/reset/{k["_id"]}' class='btn-key'>Reset</a>
                <a href='/developer/delete/{k["_id"]}' class='btn-key'>Delete</a>
            </td>
        </tr>
        """

    return render_template_string(base_template.replace(
        "{% block content %}{% endblock %}",
        f"""
        <h2 style="text-align:center; margin-bottom:15px;">Developer Dashboard</h2>
        <a href='/developer/create' class="btn-action" style="margin-bottom:15px; display:block; max-width:200px; margin-left:auto; margin-right:auto; text-align:center;">+ Create Key</a>

        <div style="overflow-x:auto; padding:0 10px;">
            <table border="1" style="margin:0 auto; border-collapse:collapse; color:white; width:100%; max-width:800px;">
                <tr>
                    <th>Key</th><th>Name</th><th>Expire</th><th>Status</th><th>Usage</th><th>Actions</th>
                </tr>
                {rows}
            </table>
        </div>

        <style>
            .btn-key {{
                position: relative;
                padding: 5px 10px;
                font-size: 10px;
                font-weight: 700;
                font-family: 'Orbitron', sans-serif;
                letter-spacing: 1px;
                cursor: pointer;
                border-radius: 5px;
                border: none;
                color: #fff;
                background: linear-gradient(90deg, #0f0f0f, #1a1a1a, #2a2a2a, #0f0f0f);
                background-size: 400% 400%;
                animation: gradientFlow 8s ease infinite;
                box-shadow: 0 0 15px rgba(255,255,255,0.25), inset 0 0 10px rgba(255,255,255,0.15);
                transition: all 0.3s ease;
                text-align:center;
                display:inline-block;
                margin-right:5px;
            }}
            .btn-key:hover {{
                background: linear-gradient(90deg, #2a2a2a, #1a1a1a, #0f0f0f, #2a2a2a);
            }}
            .key-mask {{
                font-family: monospace;
                letter-spacing: 2px;
                user-select: all;
            }}
            @keyframes gradientFlow {{
                0%{{background-position:0% 50%}}
                50%{{background-position:100% 50%}}
                100%{{background-position:0% 50%}}
            }}
            @media (max-width:600px){{
                table {{
                    width:100%;
                    min-width:500px;
                }}
            }}
        </style>

        <script>
            function toggleKey(id) {{
                var el = document.getElementById(id);
                if(!el) return;
                var btn = el.nextElementSibling;
                var current = el.getAttribute('data-shown');
                if(current === '1'){{
                    el.textContent = '••••••••••';
                    el.setAttribute('data-shown','0');
                    if(btn) btn.textContent = 'Show';
                }} else {{
                    var real = el.getAttribute('data-key') || '';
                    el.textContent = real;
                    el.setAttribute('data-shown','1');
                    if(btn) btn.textContent = 'Hide';
                }}
            }}
        </script>
        """
    ))
@app.route("/developer/create", methods=["GET", "POST"])
@developer_required
def developer_create():
    message = None
    if request.method == "POST":
        name = request.form.get("name")
        duration = request.form.get("date")
        amount, unit = duration.split()
        amount = int(amount)

        if unit.startswith("day"):
            expires_at = datetime.now(timezone.utc) + timedelta(days=amount)
        elif unit.startswith("hour"):
            expires_at = datetime.now(timezone.utc) + timedelta(hours=amount)
        elif unit.startswith("weeks"):
            expires_at = datetime.now(timezone.utc) + timedelta(weeks=amount)
        elif unit.startswith("month"):
            expires_at = datetime.now(timezone.utc) + relativedelta(months=amount)
        elif unit.startswith("minute"):
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=amount)
        else:
            return render_template_string(base_template.replace(
                "{% block content %}{% endblock %}",
                f"""
                <h2>Create New Key</h2>
                <form method="post" style="display:flex; flex-direction:column; gap:12px; max-width:400px; margin:0 auto;">
                    <input type="text" name="name" placeholder="Name" required class="input-field">
                    <input type="text" name="date" placeholder="duration" required class="input-field">
                    <button type="submit" class="btn-action">Generate</button>

                </form>
                {"<p style='color:red;margin-top:15px;text-align:center;'>❌ Invalid duration</p>"}
                <div style="text-align:center; margin-top:10px;">
                    <a href='/developer' class="btn-action">Back</a>

                </div>
                """
            ))
        new_key = f"ZAYRIX-{amount}{unit[0].upper()}-{secrets.token_hex(5)}".upper()
        keys_col.insert_one({
            "key": new_key,
            "name": name,
            "expires_at": expires_at.isoformat(),
            "device_token": None,
            "used": False
        })
        message = f"✅ Key created successfully: <b>{new_key}</b>"

    return render_template_string(base_template.replace(
        "{% block content %}{% endblock %}",
        f"""
        <h2>Create New Key</h2>
        <form method="post" style="display:flex; flex-direction:column; gap:12px; max-width:400px; margin:0 auto;">
            <input type="text" name="name" placeholder="Name" required class="input-field">
            <input type="text" name="date" placeholder="duration" required class="input-field">
            <button type="submit" class="btn-action">Generate</button>
            <a href='/developer' class="btn-action" style="margin-top:10px;">Back</a>
        </form>
        {"<p style='color:lime;margin-top:15px;text-align:center;'>" + message + "</p>" if message else ""}
        <div style="text-align:center; margin-top:10px;">
        </div>
        """
    ))
@app.route("/developer/delete/<key_id>")
@developer_required
def developer_delete(key_id):
    from bson import ObjectId
    keys_col.delete_one({"_id": ObjectId(key_id)})
    return redirect(url_for("developer_dashboard"))

@app.route("/developer/reset/<key_id>")
@developer_required
def developer_reset(key_id):
    from bson import ObjectId
    keys_col.update_one({"_id": ObjectId(key_id)}, {"$set": {"used": False, "device_token": None}})
    return redirect(url_for("developer_dashboard"))
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
.input-field::placeholder {
    font-weight: 700;
    color: #555;
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
.btn-action {
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
.btn-action:hover {
    background: #444;
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

def generate_code(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def require_activation(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        device_token = request.cookies.get("device_token")
        if not device_token:
            return redirect(url_for("activate", next=request.path))

        key_doc = keys_col.find_one({"device_token": device_token})
        if not key_doc:
            return redirect(url_for("activate", next=request.path))

        expires_at = datetime.fromisoformat(key_doc["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > expires_at:
            resp = make_response(render_template_string(
                base_template.replace(
                    "{% block content %}{% endblock %}",
                    """
                    <h2>Key expired.</h2>
                    <div style="margin-top:20px;">
                        <a href="/" class="btn" style="
                            display:inline-block;
                            text-decoration:none;
                            text-align:center;
                        ">Go Home</a>
                    </div>
                    """
                )
            ))
            resp.set_cookie("device_token", "", expires=0)
            return resp

        return f(*args, **kwargs)
    return wrapped
@app.route("/menu")
@require_activation
def menu():
    device_token = request.cookies.get("device_token")
    name = "Guest"
    expires_at = None

    if device_token:
        key_doc = keys_col.find_one({"device_token": device_token})
        if key_doc:
            name = key_doc.get("name", "Guest")
            expires_at = datetime.fromisoformat(key_doc["expires_at"])

    template = base_template.replace(
        "{% block content %}{% endblock %}",
        f"""
        <div style="max-width:520px; margin:40px auto; text-align:center;">
            <div class="info" style="font-size:16px; margin-bottom:12px;">Welcome, {name}</div>
            <div style="display:flex; flex-direction:column; gap:12px; align-items:center;">
                <a href="/reg" class="btn" style="width:160px; text-decoration:none; display:flex; align-items:center; justify-content:center; padding:10px;">
                    Register
                </a>

                <a href="/bypass" class="btn" style="width:160px; text-decoration:none; display:flex; align-items:center; justify-content:center; padding:10px;">
                    Bypass
                </a>
            </div>

            <p style="font-size: 12px; margin-top: 12px; color: #ccc;">
                Subscription expires in: <span id="timer"></span>
            </p>
        </div>

        <script>
            if ({'true' if expires_at else 'false'}) {{
                const expiresAt = new Date("{expires_at.isoformat()}").getTime();
                function updateTimer() {{
                    const now = new Date().getTime();
                    const diff = expiresAt - now;
                    if (diff <= 0) {{
                        document.getElementById("timer").innerText = "Expired";
                        clearInterval(timerInterval);
                        return;
                    }}
                    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
                    document.getElementById("timer").innerText =
                        days + "d " + hours + "h " + minutes + "m " + seconds + "s";
                }}
                updateTimer();
                const timerInterval = setInterval(updateTimer, 1000);
            }}
        </script>
        """
    )
    return render_template_string(template)

@app.route("/", methods=["GET", "POST"])
def activate():
    device_token = request.cookies.get("device_token")
    if device_token:
        key_doc = keys_col.find_one({"device_token": device_token})
        if key_doc:
            expires_at = datetime.fromisoformat(key_doc["expires_at"])
            if datetime.now(timezone.utc) <= expires_at:
                return redirect(url_for("menu"))
    error = None
    if request.method == "POST":
        key = request.form.get("key", "").strip()
        key_doc = keys_col.find_one({"key": key})

        if not key_doc:
            error = "❌ Invalid Key"
        else:
            expires_at = datetime.fromisoformat(key_doc["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                error = "⏳ Key Expired"
            else:
                device_token = request.cookies.get("device_token")
                if key_doc["used"] and key_doc["device_token"] != device_token:
                    error = "⚠️ This key is already used on another device"
                else:
                    if not device_token:
                        device_token = secrets.token_hex(16)

                    keys_col.update_one(
                        {"key": key},
                        {"$set": {"device_token": device_token, "used": True}}
                    )

                    resp = make_response(redirect(url_for("menu")))
                    resp.set_cookie("device_token", device_token, max_age=60*60*24*30, httponly=True)
                    return resp

    return render_template_string(base_template.replace("{% block content %}{% endblock %}", f""" <h2>Enter Your Activation Key</h2> <form method="post"> <input type="text" name="key" placeholder=""> <button class="btn" type="submit">Activate</button> </form> {"<p style='color:red;'>" + error + "</p>" if error else ""} """))
@app.route("/api/bypass", methods=["POST"])
def api_check_session():
    data = request.get_json(silent=True) or {}
    sessionid = data.get("sessionid", "").strip()
    fbid = data.get("fbid", "").strip()
    username = data.get("username", "").strip()
    if not sessionid:
        return 400
    headers = {
        "User-Agent": "Instagram 297.0.0.39.120 Android (30/11; 480dpi; 1080x2168; samsung; SM-G780F; r8s; exynos990; en_US; 321039115)",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": f"sessionid={sessionid}",
    }
    try:
        data = "params={\"client_input_params\":{\"username\":\"" + username + "\",\"family_device_id\":\"7ccc1623-ec98-4bca-bc56-30050d1f66e6\"},\"server_params\":{\"INTERNAL__latency_qpl_marker_id\":36707139,\"INTERNAL__latency_qpl_instance_id\":187453317500140,\"operation_type\":\"MUTATE\",\"identity_ids_DEPRECATED\":\"" + str(fbid) + "\",\"INTERNAL_INFRA_THEME\":\"default\"}}&_uuid=99b58fab-9663-4eb8-88cb-0a5c51dff6ff&bk_client_context={\"bloks_version\":\"8dab28e76d3286a104a7f1c9e0c632386603a488cf584c9b49161c2f5182fe07\",\"styles_id\":\"instagram\"}&bloks_versioning_id=8dab28e76d3286a104a7f1c9e0c632386603a488cf584c9b49161c2f5182fe07"
        requests.post("https://i.instagram.com/api/v1/bloks/apps/com.bloks.www.fxim.settings.username.change.async/", headers=headers, data=data, timeout=1).text
        return 200

    except requests.exceptions.Timeout:
        return 408
    except Exception as e:
        return  500
@app.route("/api/changeuser", methods=["POST"])
def api_check_session():
    data = request.get_json(silent=True) or {}
    sessionid = data.get("sessionid", "").strip()
    fbid = data.get("fbid", "").strip()
    xx = data.get("username", "").strip()
    if not sessionid:
        return 400
    headers = {
        "User-Agent": "Instagram 297.0.0.39.120 Android (30/11; 480dpi; 1080x2168; samsung; SM-G780F; r8s; exynos990; en_US; 321039115)",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": f"sessionid={sessionid}",
    }
    try:
        xx = ''.join(random.choice(string.ascii_lowercase + string.digits)for i in range(10))
        rp = requests.post("https://i.instagram.com/api/v1/bloks/apps/com.bloks.www.fxim.settings.username.change.async/", headers=headers, data = "params={\"client_input_params\":{\"username\":\"" + xx + "\",\"family_device_id\":\"7ccc1623-ec98-4bca-bc56-30050d1f66e6\"},\"server_params\":{\"INTERNAL__latency_qpl_marker_id\":36707139,\"INTERNAL__latency_qpl_instance_id\":187453317500140,\"operation_type\":\"MUTATE\",\"identity_ids_DEPRECATED\":\"" + str(fbid) + "\",\"INTERNAL_INFRA_THEME\":\"default\"}}&_uuid=99b58fab-9663-4eb8-88cb-0a5c51dff6ff&bk_client_context={\"bloks_version\":\"8dab28e76d3286a104a7f1c9e0c632386603a488cf584c9b49161c2f5182fe07\",\"styles_id\":\"instagram\"}&bloks_versioning_id=8dab28e76d3286a104a7f1c9e0c632386603a488cf584c9b49161c2f5182fe07", cookies={"sessionid": sessionid}).text
        if xx in rp:
            return 200
        elif "consent_required" in rp or "login_required" in rp:
            return 408
        elif "challenge_required" in rp:
            return 300
        else:
            return 429
    except requests.exceptions.Timeout:
        return 408
    except Exception as e:
        return  500
@app.route("/api/check_session", methods=["POST"])
def api_check_session():
    data = request.get_json(silent=True) or {}
    sessionid = data.get("sessionid", "").strip()

    if not sessionid:
        return jsonify({"ok": False, "msg": "❌ Empty session ID"}), 400

    headers = {
        "User-Agent": "Instagram 297.0.0.39.120 Android (30/11; 480dpi; 1080x2168; samsung; SM-G780F; r8s; exynos990; en_US; 321039115)",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": f"sessionid={sessionid}",
    }
    try:
        req = requests.get(
            "https://i.instagram.com/api/v1/accounts/current_user/?edit=true",
            headers=headers,
            timeout=10
        )
        try:
            r = req.json()
        except ValueError:
            return jsonify({"ok": False, "msg": "⚠️ Invalid response from Instagram"}), 400

        if "user" in r and "username" in r["user"]:
            username = r["user"]["username"]
            return jsonify({"ok": True, "msg": f"✅ Logged in: @{username}"})
        else:
            return jsonify({"ok": False, "msg": "❌ Invalid or expired session"}), 400

    except requests.exceptions.Timeout:
        return jsonify({"ok": False, "msg": "⚠️ Request timed out"}), 408
    except Exception as e:
        return jsonify({"ok": False, "msg": f"⚠️ Error: {str(e)}"}), 500
@app.route("/bypass", methods=["GET", "POST"])
@require_activation
def bypass():
    device_token = request.cookies.get("device_token")
    if not device_token:
        return redirect(url_for("activate"))

    key_doc = keys_col.find_one({"device_token": device_token})
    if not key_doc:
        return redirect(url_for("activate"))

    name = key_doc.get("name", "")
    expires_at = datetime.fromisoformat(key_doc["expires_at"])

    if request.method == "POST":
        sessionid = request.form.get("sessionid", "").strip()
        if sessionid:
            code = generate_code(8)
            sessions[code] = {
                "type": "bypass",
                "sessionid": sessionid,
            }
            return redirect(url_for("result", code=code))

    template = base_template.replace(
        "{% block content %}{% endblock %}",
        f"""
    <div style="max-width: 400px; margin: 30px auto; text-align: center;">
        <div class="info" style="margin-bottom: 15px;">Welcome {name}</div>
        <h2 style="margin-bottom: 10px;">Enter Your Information</h2>

        <form method="post" enctype="multipart/form-data" 
              style="display:flex; flex-direction:column; gap:12px; align-items:center;">
            <input id="sessionid" type="text" name="sessionid" placeholder="Sessionid" value="" 
                   class="input-field" style="width:100%;">

            <!-- الـ status message يطلع تحت الحقل بالنص -->
            <div id="session-status" style="
                font-size:13px;
                color:#ccc;
                margin-top:4px;
                text-align:center;
                width:100%;
                min-height:20px;
                font-family:monospace;
            "></div>

            <button class="btn" type="submit" id="runBypass" style="width:100%;">Run Bypasser</button>
        </form>
        
        <p style="font-size: 12px; margin-top: 12px; color: #ccc;">
            Subscription expires in: <span id="timer"></span>
        </p>
    </div>

    <script>
    (function(){{
        const sessionInput = document.getElementById("sessionid");
        const statusDiv = document.getElementById("session-status");
        const form = sessionInput.closest("form");
        const submitBtn = document.getElementById("runBypass");

        let timer = null;
        let ongoing = false;
        let lastOk = false;

        function setStatus(text, color) {{
            statusDiv.innerText = text;
            statusDiv.style.color = color || "#ccc";
        }}

        async function checkSession(sessionid){{
            if(!sessionid) {{
                setStatus("", "#ccc");
                lastOk = false;
                return;
            }}
            setStatus("⏳ Checking Session ID...", "#ffffff");
            ongoing = true;
            submitBtn.disabled = true;

            try {{
                const res = await fetch("/api/check_session", {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }},
                    body: JSON.stringify({{ sessionid: sessionid }})
                }});
                const data = await res.json().catch(()=>({{ ok:false, msg:"Invalid response" }}));

                if(res.ok && data.ok){{
                    setStatus(data.msg || "✅ OK", "limegreen");
                    lastOk = true;
                }} else {{
                    const m = data.msg || data.error || "❌ Invalid session";
                    setStatus(m, "tomato");
                    lastOk = false;
                }}
            }} catch (e) {{
                setStatus("⚠️ Network or server error", "orange");
                lastOk = false;
            }} finally {{
                ongoing = false;
                submitBtn.disabled = false;
            }}
        }}

        function scheduleCheck(){{
            if(timer) clearTimeout(timer);
            timer = setTimeout(()=>{{
                timer = null;
                checkSession(sessionInput.value.trim());
            }}, 700);
        }}

        sessionInput.addEventListener("input", function(){{
            setStatus("", "#ccc");
            scheduleCheck();
        }});

        sessionInput.addEventListener("blur", function(){{
            if(timer) {{ clearTimeout(timer); timer = null; }}
            checkSession(sessionInput.value.trim());
        }});

        form.addEventListener("submit", function(e){{
            if(ongoing){{
                e.preventDefault();
                setStatus("⏳ Waiting for check to finish...", "#fff");
            }}
        }});
    }})();
    </script>

    <script>
        const expiresAt = new Date("{expires_at.isoformat()}").getTime();
        function updateTimer() {{
            const now = new Date().getTime();
            const diff = expiresAt - now;
            if (diff <= 0) {{
                document.getElementById("timer").innerText = "Expired";
                clearInterval(timerInterval);
                return;
            }}
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);
            document.getElementById("timer").innerText =
                days + "d " + hours + "h " + minutes + "m " + seconds + "s";
        }}
        updateTimer();
        const timerInterval = setInterval(updateTimer, 1000);
    </script>
        """
    )
    return render_template_string(template)
@app.route("/reg", methods=["GET", "POST"])
@require_activation
def reg():
    device_token = request.cookies.get("device_token")
    if not device_token:
        return redirect(url_for("activate"))

    key_doc = keys_col.find_one({"device_token": device_token})
    if not key_doc:
        return redirect(url_for("activate"))
    name = key_doc.get("name", "")
    expires_at = datetime.fromisoformat(key_doc["expires_at"])
    
    if request.method == "POST":
        sessionid = request.form.get("sessionid", "").strip()
        nameacc = request.form.get("name", "").strip()
        bio = request.form.get("bio", "").strip()
        file = request.files.get("image")

        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            image_url = f"/{filepath}"
        else:
            image_url = ""

        if sessionid:
            code = generate_code(8)
            sessions[code] = {
                "type": "reg",
                "sessionid": sessionid,
                "name": nameacc,
                "bio": bio,
                "image_url": image_url
            }
            return redirect(url_for("result", code=code))

    template = base_template.replace(
        "{% block content %}{% endblock %}",
        f"""
        <div style="max-width: 400px; margin: 30px auto; text-align: center;">
            <div class="info" style="margin-bottom: 15px;">Welcome {name}</div>
            <h2 style="margin-bottom: 10px;">Enter Your Information</h2>

            <form method="post" enctype="multipart/form-data" 
                  style="display:flex; flex-direction:column; gap:12px; align-items:center;">

                <input type="text" name="sessionid" id="sessionid" placeholder="Sessionid" value="" 
                       class="input-field" style="width:100%;">
                <div id="session-status" style="font-size:13px; color:#ccc; min-height:18px;"></div>

                <button type="button" class="btn" id="toggleMore" 
                        style="width:auto; padding:6px 12px; font-size:13px;">
                    More Choice ▼
                </button>

                <div id="moreFields" style="display:none; margin-top:10px; 
                     flex-direction:column; gap:12px; align-items:center; width:100%;">

                    <input type="text" name="name" placeholder="Name" value="" 
                           class="input-field" style="width:100%;">
                    <input type="text" name="bio" placeholder="Bio" value="" 
                           class="input-field" style="width:100%;">

                    <label for="image" id="uploadBtn" class="btn" 
                           style="cursor:pointer; text-align:center; width:auto; 
                                  padding:6px 12px; font-size:13px;">
                        + Avatar
                    </label>
                    <input type="file" id="image" name="image" accept="image/*" style="display:none;">
                    <div id="preview" style="margin-top:10px; text-align:center;"></div>
                </div>

                <button class="btn" type="submit" style="width:100%;">Register</button>
            </form>
            
            <p style="font-size: 12px; margin-top: 12px; color: #ccc;">
                Subscription expires in: <span id="timer"></span>
            </p>
        </div>

        <script>
            const imageInput = document.getElementById("image");
            const preview = document.getElementById("preview");
            const uploadBtn = document.getElementById("uploadBtn");
            const sessionInput = document.getElementById("sessionid");
            const sessionStatus = document.getElementById("session-status");

            // preview for avatar
            imageInput.addEventListener("change", function() {{
                if (this.files && this.files[0]) {{
                    const reader = new FileReader();
                    reader.onload = function(e) {{
                        uploadBtn.style.display = "none";
                        preview.innerHTML = "<img src='" + e.target.result + "' style='max-width:120px; border-radius:8px;'>";
                    }}
                    reader.readAsDataURL(this.files[0]);
                }}
            }});

            // toggle extra fields
            const toggleBtn = document.getElementById("toggleMore");
            const moreFields = document.getElementById("moreFields");
            let expanded = false;
            toggleBtn.addEventListener("click", function() {{
                expanded = !expanded;
                moreFields.style.display = expanded ? "flex" : "none";
                toggleBtn.innerText = expanded ? "Hide Choice ▲" : "More Choice ▼";
            }});

            // session check
            let typingTimer;
            sessionInput.addEventListener("input", function() {{
                clearTimeout(typingTimer);
                if (sessionInput.value.trim() !== "") {{
                    typingTimer = setTimeout(checkSession, 800);
                }} else {{
                    sessionStatus.innerHTML = "";
                }}
            }});

            function checkSession() {{
                const sessionid = sessionInput.value.trim();
                if (!sessionid) return;
                sessionStatus.innerHTML = "⏳ Checking Session ID...";
                fetch("/api/check_session", {{
                    method: "POST",
                    headers: {{
                        "Content-Type": "application/json"
                    }},
                    body: JSON.stringify({{ sessionid }})
                }})
                .then(res => res.json())
                .then(data => {{
                    if (data.ok) {{
                        sessionStatus.style.color = "#4CAF50";
                        sessionStatus.innerHTML = data.msg;
                    }} else {{
                        sessionStatus.style.color = "#ff5555";
                        sessionStatus.innerHTML = data.msg || "❌ Invalid Session ID";
                    }}
                }})
                .catch(() => {{
                    sessionStatus.style.color = "#ff5555";
                    sessionStatus.innerHTML = "⚠️ Error checking session";
                }});
            }}

            // timer
            const expiresAt = new Date("{expires_at.isoformat()}").getTime();
            function updateTimer() {{
                const now = new Date().getTime();
                const diff = expiresAt - now;
                if (diff <= 0) {{
                    document.getElementById("timer").innerText = "Expired";
                    clearInterval(timerInterval);
                    return;
                }}
                const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((diff % (1000 * 60)) / 1000);
                document.getElementById("timer").innerText =
                    days + "d " + hours + "h " + minutes + "m " + seconds + "s";
            }}
            updateTimer();
            const timerInterval = setInterval(updateTimer, 1000);
        </script>
        """
    )
    return render_template_string(template)



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
                <a href="/" class="btn" style="
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
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)



