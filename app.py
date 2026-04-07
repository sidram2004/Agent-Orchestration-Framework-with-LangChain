
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from pypdf import PdfReader
import docx
import pandas as pd
from pptx import Presentation
import io
import functools
from orchestration import run_workflow

app = Flask(__name__)
app.secret_key = "your_secret_encryption_key"

# --- DATABASE UTILITIES ---
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def extract_text_from_file(file):
    filename = file.filename.lower()
    content = ""
    
    try:
        if filename.endswith('.pdf'):
            reader = PdfReader(file)
            content = "".join([p.extract_text() for p in reader.pages])
            
        elif filename.endswith('.docx'):
            doc = docx.Document(file)
            content = "\n".join([para.text for para in doc.paragraphs])
            
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(file)
            content = df.to_string(index=False)
            
        elif filename.endswith('.csv'):
            df = pd.read_csv(file)
            content = df.to_string(index=False)
            
        elif filename.endswith('.pptx'):
            prs = Presentation(file)
            text_runs = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text_runs.append(shape.text)
            content = "\n".join(text_runs)
            
        elif filename.endswith('.txt'):
            content = file.read().decode('utf-8')
            
        return content.strip()
    except Exception as e:
        print(f"Extraction Error: {str(e)}")
        return f"[Error extracting text from {filename}]"

def init_db():
    """Initializes the database tables on startup."""
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)""")
        db.execute("""CREATE TABLE IF NOT EXISTS chats(
            id INTEGER PRIMARY KEY, chat_id TEXT, username TEXT, 
            message TEXT, response TEXT)""")
        db.commit()

init_db()

# --- AUTHENTICATION ROUTES ---
@app.route('/')
@app.route('/landing.html')
def index():
    if 'user' in session:
        return redirect(url_for('chat_interface'))
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                       (u, generate_password_hash(p)))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists.", 400
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        
        if user and check_password_hash(user['password'], p):
            session['user'] = u
            return redirect(url_for('chat_interface'))
        
        # If login fails
        return "Invalid credentials. <a href='/login'>Try again</a>", 401
        
    return render_template('login.html')

# --- CHAT ROUTES ---
@app.route('/chat')
def chat_interface():
    if 'user' not in session: return redirect(url_for('login'))
    
    current_chat = request.args.get('chat_id', 'Chat 1')
    db = get_db()
    
    # Fetch all unique chats for the sidebar, ordered by the most recent message
    rows = db.execute("""
        SELECT chat_id, MAX(id) as last_msg_id 
        FROM chats 
        WHERE username=? 
        GROUP BY chat_id 
        ORDER BY last_msg_id DESC
    """, (session['user'],)).fetchall()
    chat_list = [r['chat_id'] for r in rows]
    if not chat_list: chat_list = ["Chat 1"]
    
    # Fetch message history for the current selected chat with IDs
    history = db.execute("SELECT id, message, response FROM chats WHERE username=? AND chat_id=?", 
                         (session['user'], current_chat)).fetchall()
    
    return render_template('index.html', chat_list=chat_list, current_chat=current_chat, history=history)

@app.route('/send_message', methods=['POST'])
def send_message():
    """Handles AJAX chat requests including PDF processing."""
    chat_id = request.form['chat_id']
    user_input = request.form.get('message', '')

    # PDF/Document Logic: If a file is uploaded, extract text and merge with message
    if 'pdf' in request.files and request.files['pdf'].filename != '':
        file = request.files['pdf']
        doc_text = extract_text_from_file(file)
        if doc_text:
            user_input = f"{user_input}\n\n[Context from Attached Document ({file.filename})]:\n{doc_text}"

    # Check if this is the first message for this chat to trigger naming
    db = get_db()
    count = db.execute("SELECT COUNT(*) as c FROM chats WHERE username=? AND chat_id=?", 
                       (session['user'], chat_id)).fetchone()['c']
    is_new_chat = (count == 0)

    # Run your AI Agent logic
    result = run_workflow(user_input, is_new_chat=is_new_chat)

    ai_response = result.get("answer", "")
    email_response = result.get("email", "")
    routing_decision = result.get("routing", "")
    tools_used = result.get("tools_used", [])
    suggested_name = result.get("suggested_name")

    # Save interaction to DB and get the ID
    db = get_db()
    cursor = db.execute("INSERT INTO chats (chat_id, username, message, response) VALUES (?,?,?,?)",
               (chat_id, session['user'], user_input, ai_response))
    new_id = cursor.lastrowid
    db.commit()
    
    return jsonify({
        "id": new_id,
        "message": user_input, 
        "response": ai_response, 
        "answer": ai_response,
        "routing": routing_decision,
        "email": email_response, 
        "tools_used": tools_used,
        "suggested_name": suggested_name
    })

@app.route('/edit_message', methods=['POST'])
@login_required
def edit_message():
    """Updates an existing message and regenerates the response."""
    msg_id = request.form['msg_id']
    new_text = request.form['message']
    username = session['user']
    
    # Run the updated workflow
    result = run_workflow(new_text, is_new_chat=False)
    new_response = result.get("answer", "")
    
    db = get_db()
    try:
        db.execute("UPDATE chats SET message=?, response=? WHERE id=? AND username=?", 
                   (new_text, new_response, msg_id, username))
        db.commit()
        return jsonify({
            "success": True, 
            "new_response": new_response,
            "tools_used": result.get("tools_used", [])
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/rename_workspace', methods=['POST'])
def rename_workspace():
    """Updates session ID (chat_id) in the database for auto-naming."""
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    old_id = request.form['old_id']
    new_id = request.form['new_id']
    username = session['user']
    
    db = get_db()
    try:
        db.execute("UPDATE chats SET chat_id=? WHERE username=? AND chat_id=?", (new_id, username, old_id))
        db.commit()
        return jsonify({"success": True, "new_id": new_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    chat_id = request.form['chat_id']
    username = session['user']
    db = get_db()
    try:
        db.execute("DELETE FROM chats WHERE username=? AND chat_id=?", (username, chat_id))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/delete_chat/<chat_id>')
def delete_chat(chat_id):
    db = get_db()
    db.execute("DELETE FROM chats WHERE username=? AND chat_id=?", (session['user'], chat_id))
    db.commit()
    return redirect(url_for('chat_interface'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/style.css')
def style():
    return send_from_directory('static', 'style.css')

@app.route('/script.js')
def script():
    return send_from_directory('static', 'script.js')

if __name__ == '__main__':
    app.run(debug=True)