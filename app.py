from flask import Flask, render_template, request, redirect, url_for
from twilio.rest import Client
from dotenv import load_dotenv
import os
import random
import time

load_dotenv()
app = Flask(__name__)

# Test mode setup
USE_TEST_MODE = True

# Load credentials for test mode
if USE_TEST_MODE:
    TWILIO_SID = os.getenv("TEST_TWILIO_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TEST_TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TEST_TWILIO_PHONE_NUMBER")
    RECEIVER_PHONE_NUMBER = os.getenv("TEST_RECEIVER_PHONE")
else:
    TWILIO_SID = os.getenv("TWILIO_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    RECEIVER_PHONE_NUMBER = "+12065496950"  # Replace with your actual number

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# A mock database for users
users_db = {
    "testuser": {
        "password": "password123",
        "phone": RECEIVER_PHONE_NUMBER,
        "mfa_enabled": True,
    }
}

# In-memory OTP storage
otp_store = {}


def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))


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
    """Send an OTP to the user's registered phone number."""
    user_phone = users_db[username]["phone"]
    otp = generate_otp()
    otp_store[username] = {
        "otp": otp,
        "expiry": time.time() + 300,
    }  # Expires in 5 minutes

    # Print the OTP for testing purposes
    print(f"Generated OTP: {otp}")  # print OTP on console

    try:
        message = client.messages.create(
            body=f"Your verification code is {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=user_phone,
        )
        print(f"Message SID: {message.sid}")
    except Exception as e:
        print(f"Error while sending message: {e}")
        return f"Error: {e}"

    return render_template("verify_mfa.html", username=username)


@app.route("/verify_mfa", methods=["POST"])
def verify_mfa():
    """Verify the submitted OTP."""
    username = request.form["username"]
    mfa_code = request.form["mfa_code"]

    if username in otp_store:
        stored_otp = otp_store[username]
        if time.time() > stored_otp["expiry"]:
            return "OTP has expired. Please request a new one."
        if mfa_code == stored_otp["otp"]:
            del otp_store[username]  # Remove OTP after successful verification
            return redirect(url_for("logged_in"))
    return "Invalid MFA code"


@app.route("/logged_in")
def logged_in():
    return "Logged in successfully!"


@app.route("/logged_out")
def logged_out():
    return "Logged out."


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        phone = request.form["phone"]

        if username in users_db:
            return "Username already exists."

        users_db[username] = {
            "password": password,
            "phone": phone,
            "mfa_enabled": True,
        }

        return redirect(url_for("index"))

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
