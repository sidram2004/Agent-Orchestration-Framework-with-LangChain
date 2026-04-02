
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from pypdf import PdfReader
from orchestration import run_workflow  # Ensure this file exists in your directory

app = Flask(__name__)
app.secret_key = "your_secret_encryption_key"

# --- DATABASE UTILITIES ---
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

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

# ... (keep your existing imports and database init code) ...

@app.route('/register', methods=['GET', 'POST'])
@app.route('/register.html', methods=['GET', 'POST'])
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
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 1. Get data from the HTML form
        u = request.form.get('username')
        p = request.form.get('password')
        
        db = get_db()
        
        # 2. Query the database (This creates the 'user' variable)
        user = db.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        
        # 3. Now check if 'user' exists and the password is correct
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
    
    # Fetch all unique chats for the sidebar
    rows = db.execute("SELECT DISTINCT chat_id FROM chats WHERE username=?", (session['user'],)).fetchall()
    chat_list = [r['chat_id'] for r in rows]
    if not chat_list: chat_list = ["Chat 1"]
    
    # Fetch message history for the current selected chat
    history = db.execute("SELECT message, response FROM chats WHERE username=? AND chat_id=?", 
                         (session['user'], current_chat)).fetchall()
    
    return render_template('index.html', chat_list=chat_list, current_chat=current_chat, history=history)

@app.route('/send_message', methods=['POST'])
def send_message():
    """Handles AJAX chat requests including PDF processing."""
    chat_id = request.form['chat_id']
    user_input = request.form.get('message', '')

    # PDF Logic: If a file is uploaded, extract text and use it as input
    if 'pdf' in request.files and request.files['pdf'].filename != '':
        reader = PdfReader(request.files['pdf'])
        user_input = "".join([p.extract_text() for p in reader.pages])[:1000]

    # Run your AI Agent logic
    # ai_response = run_workflow(user_input)
    result = run_workflow(user_input)

    ai_response = result.get("answer", "")
    email_response = result.get("email", "")
    tools_used = result.get("tools_used", [])

    # Save interaction to DB
    db = get_db()
    db.execute("INSERT INTO chats (chat_id, username, message, response) VALUES (?,?,?,?)",
               (chat_id, session['user'], user_input, ai_response))
    db.commit()
    
    return jsonify({"message": user_input, "response": ai_response, "email": email_response, "tools_used": tools_used})

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
# import streamlit as st
# import sqlite3
# from pypdf import PdfReader
# from werkzeug.security import generate_password_hash, check_password_hash

# from orchestration import run_workflow

# # ---------------- CONFIG ----------------
# st.set_page_config(page_title="AI Multi-Agent System", layout="wide")

# # ---------------- DB ----------------
# def init_db():
#     conn = sqlite3.connect("database.db")
#     c = conn.cursor()

#     c.execute("""CREATE TABLE IF NOT EXISTS users(
#         id INTEGER PRIMARY KEY,
#         username TEXT UNIQUE,
#         password TEXT)""")

#     c.execute("""CREATE TABLE IF NOT EXISTS chats(
#         id INTEGER PRIMARY KEY,
#         chat_id TEXT,      
#         username TEXT,
#         message TEXT,
#         response TEXT)""")

#     conn.commit()
#     conn.close()

# init_db()

# # ---------------- SESSION ----------------
# if "user" not in st.session_state:
#     st.session_state.user = None

# if "chat_id" not in st.session_state:
#     st.session_state.chat_id = "Chat 1"

# if "chat_list" not in st.session_state:
#     st.session_state.chat_list = ["Chat 1"]
# # ---------------- VOICE ----------------

# # ---------------- PDF ----------------
# def read_pdf(file):
#     reader = PdfReader(file)
#     text = ""
#     for page in reader.pages:
#         text += page.extract_text()
#     return text

# # ---------------- LOGIN ----------------
# def login():
#     st.title("🔐 Login")

#     u = st.text_input("Username")
#     p = st.text_input("Password", type="password")

#     if st.button("Login"):
#         db = sqlite3.connect("database.db")
#         user = db.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()

#         if user and check_password_hash(user[2], p):
#             st.session_state.user = u
#             st.success("Login successful")
#             st.rerun()
#         else:
#             st.error("Invalid credentials")

# # ---------------- REGISTER ----------------
# def register():
#     st.title("📝 Register")

#     u = st.text_input("Username")
#     p = st.text_input("Password", type="password")

#     if st.button("Register"):
#         db = sqlite3.connect("database.db")
#         try:
#             db.execute(
#                 "INSERT INTO users VALUES(NULL,?,?)",
#                 (u, generate_password_hash(p))
#             )
#             db.commit()
#             st.success("Account created")
#         except:
#             st.error("User exists")

# # ---------------- CHAT ----------------
# def chat():

#     st.title("🤖 AI Multi-Agent Assistant")
#     st.markdown(f"### 💬 {st.session_state.chat_id}")

#     db = sqlite3.connect("database.db")
#     # -------- LOAD CHAT LIST FROM DB --------
#     chat_ids = db.execute(
#        "SELECT DISTINCT chat_id FROM chats WHERE username=?",
#        (st.session_state.user,)
#     ).fetchall()

#     db_chat_list = [c[0] for c in chat_ids]

# # Merge with session chat list
#     for chat in db_chat_list:
#       if chat not in st.session_state.chat_list:
#         st.session_state.chat_list.append(chat)

#      # Sidebar UI
#     st.sidebar.title("💬 Chats")

#     # New Chat
#     if st.sidebar.button("➕ New Chat"):
#         new_chat = f"chat{len(st.session_state.chat_list)+1}"
#         st.session_state.chat_list.append(new_chat)
#         st.session_state.chat_id = new_chat
#         st.rerun()
#      # Rename Chat
#     new_name = st.sidebar.text_input("Rename Chat")
#     if st.sidebar.button("✏ Rename"):
#         if new_name:
#             index = st.session_state.chat_list.index(st.session_state.chat_id)
#             st.session_state.chat_list[index] = new_name
#             st.session_state.chat_id = new_name
#             st.rerun()

#     # Delete Chat
#     if st.sidebar.button("🗑 Delete Chat"):

#        # Step 1: store current chat FIRST
#         current_chat = st.session_state.chat_id

#         # Step 2: remove from list
#         if current_chat in st.session_state.chat_list:
#            st.session_state.chat_list.remove(current_chat)

#          # Step 3: reset chat safely
#         if not st.session_state.chat_list:
#            st.session_state.chat_list = ["Chat 1"]

#         st.session_state.chat_id = st.session_state.chat_list[0]

#         # Step 4: delete from database
#         db.execute(
#             "DELETE FROM chats WHERE username=? AND chat_id=?",
#             (st.session_state.user, current_chat)
#         )
#         db.commit()

#         st.rerun()
       

#     # Chat selection
#     for chat_name in st.session_state.chat_list:
#         if st.sidebar.button(chat_name):
#             st.session_state.chat_id = chat_name
#             st.rerun()

#     # Load history
#     chats = db.execute(
#         "SELECT message,response FROM chats WHERE username=? AND chat_id=?",
#         (st.session_state.user, st.session_state.chat_id)
#     ).fetchall()

#     for m, r in chats:
#         st.chat_message("user").write(m)
#         st.chat_message("assistant").write(r)


#     # Input
#     user_input = st.chat_input("Type your prompt...")

#     uploaded_file = st.sidebar.file_uploader("📄 Upload PDF")

#     if uploaded_file:
#         pdf_text = read_pdf(uploaded_file)
#         st.success("PDF Loaded")
#         user_input = pdf_text[:500]

#     if user_input and user_input.strip() != "":

#        # Show user message
#        st.chat_message("user").write(user_input)

#        # Run AI
#        with st.spinner("🤖 Thinking..."):
#          result = run_workflow(user_input)

#        # Show response
#        st.chat_message("assistant").write(result)

#       # Save to DB (INSIDE SAME BLOCK)
#        db.execute(
#           "INSERT INTO chats VALUES(NULL,?,?,?,?)",
#            (st.session_state.chat_id, st.session_state.user, user_input, result)
#     )
#     db.commit()

#      # -------- Extra Controls --------
#     st.sidebar.markdown("## ⚙️ Options")

#     # Clear current chat
#     if st.sidebar.button("🧹 Clear Current Chat"):
#         db.execute(
#             "DELETE FROM chats WHERE username=? AND chat_id=?",
#             (st.session_state.user, st.session_state.chat_id)
#         )
#         db.commit()
#         st.rerun()

#     # Download chat
#     if st.sidebar.button("⬇ Download Chat"):
#         chats = db.execute(
#             "SELECT message,response FROM chats WHERE username=? AND chat_id=?",
#             (st.session_state.user, st.session_state.chat_id)
#         ).fetchall()

#         text = ""
#         for m, r in chats:
#             text += f"You: {m}\nAI: {r}\n\n"

#         st.download_button("Download", text, file_name="chat.txt")
#     # Logout
#     if st.sidebar.button("🚪 Logout"):
#         st.session_state.user = None
#         st.rerun()
# # ---------------- SIDEBAR ----------------
# menu = st.sidebar.selectbox("Menu", ["Login", "Register", "Chat"])

# if st.session_state.user:
#     st.sidebar.success(f"👤 {st.session_state.user}")

    

# # ---------------- ROUTING ----------------
# if menu == "Login":
#     login()

# elif menu == "Register":
#     register()

# elif menu == "Chat":
#     if st.session_state.user:
#         chat()
#     else:
#         st.warning("Please login first")