from flask import Flask, render_template, request, redirect, url_for
from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

# Set up Twilio credentials (use environment variables for security)
TWILIO_SID = os.getenv("TWILIO_SID")  # ============added or modified==========
TWILIO_AUTH_TOKEN = os.getenv(
    "TWILIO_AUTH_TOKEN"
)  # ============added or modified==========
TWILIO_PHONE_NUMBER = os.getenv(
    "TWILIO_PHONE_NUMBER"
)  # ============added or modified==========

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# A simple mock database for users
users_db = {
    "testuser": {"password": "password123", "phone": "+1234567890", "mfa_enabled": True}
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    if username in users_db and users_db[username]["password"] == password:
        if users_db[username]["mfa_enabled"]:
            return redirect(url_for("send_mfa_code", username=username))
        else:
            return redirect(url_for("logged_in"))
    else:
        return "Invalid credentials"


@app.route("/send_mfa_code/<username>")
def send_mfa_code(username):
    user_phone = users_db[username]["phone"]
    otp = "123456"  # In a real app, generate this dynamically
    message = client.messages.create(
        body=f"Your verification code is {otp}",
        from_=TWILIO_PHONE_NUMBER,
        to=user_phone,
    )
    return render_template("verify_mfa.html", username=username)


@app.route("/verify_mfa", methods=["POST"])
def verify_mfa():
    username = request.form["username"]
    mfa_code = request.form["mfa_code"]
    if mfa_code == "123456":  # In a real app, compare with the OTP sent
        return redirect(url_for("logged_in"))
    else:
        return "Invalid MFA code"


@app.route("/logged_in")
def logged_in():
    return "Logged in successfully!"


@app.route("/logged_out")
def logged_out():
    return "Logged out."


# 회원가입 라우트 추가
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # 폼에서 받은 데이터 처리
        username = request.form["username"]
        password = request.form["password"]
        phone = request.form["phone"]

        # 사용자 정보 저장 (간단한 예시로 `users_db` 사용)
        if username in users_db:
            return "Username already exists."

        users_db[username] = {
            "password": password,
            "phone": phone,
            "mfa_enabled": True,  # 기본값으로 MFA 활성화
        }

        return redirect(url_for("index"))  # 회원가입 완료 후 로그인 페이지로 리디렉션

    return render_template("register.html")  # 회원가입 페이지 렌더링


if __name__ == "__main__":
    app.run(debug=True)
