from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, requests, hashlib, sqlite3
from dotenv import load_dotenv
from utils.ai_food_detector import detect_food
from utils.bluetooth_robot import send_robot_message

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "smartfoodsecret")

DB_PATH = "users.db"
HF_API = os.getenv("HF_TOKEN")
USDA_API = os.getenv("USDA_API_KEY")

# ---------------- Database Setup ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        age INTEGER,
        weight REAL,
        target_weight REAL,
        weeks INTEGER,
        daily_calories REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS food_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        food_name TEXT,
        calories REAL,
        date TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# ---------------- Helpers ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def calculate_daily_calories(weight, target_weight, weeks):
    diff = weight - target_weight
    if diff <= 0: return 2000
    safe_loss = min(diff / weeks, 1)
    return 2000 - (safe_loss * 500)

# ---------------- Routes ----------------
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = hash_password(request.form['password'])
        age = int(request.form['age'])
        weight = float(request.form['weight'])
        target = float(request.form['target'])
        weeks = int(request.form['weeks'])

        if target > weight or (weight - target)/weeks > 1.5:
            return render_template('signup.html', error="Unrealistic goal! Try again.")

        daily_cal = calculate_daily_calories(weight, target, weeks)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (email, password, age, weight, target_weight, weeks, daily_calories) VALUES (?,?,?,?,?,?,?)",
                      (email, password, age, weight, target, weeks, daily_cal))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template('signup.html', error="Email already registered.")
        conn.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hash_password(request.form['password'])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = email
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    email = session['user']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, daily_calories FROM users WHERE email=?", (email,))
    user = c.fetchone()
    user_id, daily_cal = user
    c.execute("SELECT food_name, calories, date FROM food_logs WHERE user_id=?", (user_id,))
    logs = c.fetchall()
    conn.close()
    return render_template('dashboard.html', logs=logs, daily=daily_cal)

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 403

    image = request.files['image']
    path = f"static/uploads/{image.filename}"
    os.makedirs("static/uploads", exist_ok=True)
    image.save(path)

    food_name, calories, msg = detect_food(path)
    send_robot_message(f"{food_name}, {int(calories)} calories, {msg}")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE email=?", (session['user'],))
    user_id = c.fetchone()[0]
    from datetime import date
    c.execute("INSERT INTO food_logs (user_id, food_name, calories, date) VALUES (?,?,?,?)",
              (user_id, food_name, calories, str(date.today())))
    conn.commit()
    conn.close()

    return jsonify({'food': food_name, 'calories': calories, 'message': msg})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
