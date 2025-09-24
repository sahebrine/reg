import time
from flask import Flask, request, render_template_string, redirect, url_for
import subprocess

app = Flask(__name__)

def RunProccess(sessionid):
    args = ["./test.out", sessionid]
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
        shell=False
    )

    X = ""
    while process.poll() is None:
        output = process.stdout.readline()
        if output:
            X += output
    if "\n" in X:
        X = X.replace("\n", "<br>")
    return X
base_template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Zayrix Stats</title>
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
    margin: 30px 10px;
    font-size: 12px;
    color: rgba(255,255,255,0.8);
}
.footer a {
    color: #fff;
    text-decoration: none;
    margin: 0 10px;
    font-weight: 600;
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
        <a href="https://t.me/xiSahe" target="_blank">Telegram</a>
        <a href="https://instagram.com/sahe" target="_blank">Instagram</a>
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

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        sessionid = request.form.get("sessionid", "").strip()
        if sessionid:
            return redirect(url_for("result", sessionid=sessionid))

    template = base_template.replace(
        "{% block content %}{% endblock %}",
        """
        <h2>Enter Your Sessionid</h2>
        <form method="post" onsubmit="showLoader()">
            <input type="text" name="sessionid" placeholder="">
            <button class="btn" type="submit">Create</button>
        </form>
        <div id="loader" class="loader"></div>
        """
    )
    return render_template_string(template)
@app.route("/result/<sessionid>")
def result(sessionid):
    output = RunProccess(sessionid)
    template = base_template.replace(
        "{% block content %}{% endblock %}",
        f"""
        <h2>Result for Created</h2>
        <div class="error-msg">{output}</div>
        """
    )
    return render_template_string(template)

app.jinja_env.globals['base_template'] = base_template
app.jinja_loader = app.create_global_jinja_loader()
app.jinja_env.from_string(base_template).stream().dump("base.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
