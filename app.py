from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, send_from_directory
import json
import os
import hashlib
import time
import urllib.parse
import requests
import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'emote-bot-secret-key-2024'

# Firebase initialization with better error handling
db = None
firebase_initialized = False

# Try to initialize Firebase
try:
    # Check if firebase-key.json exists
    key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'firebase-key.json')
    
    if os.path.exists(key_path):
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        firebase_initialized = True
        print('[FIREBASE] ✅ Connected successfully!')
    else:
        print('[FIREBASE] ⚠️ firebase-key.json not found, using local database')
        print('[FIREBASE] 📝 To use Firebase, download service account key from Firebase Console and save as firebase-key.json')
except Exception as e:
    print(f'[FIREBASE] ❌ Connection failed: {e}')
    print('[FIREBASE] 📝 Using local database fallback')

# Always use absolute path next to app.py so it never gets lost
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.json')

DEFAULT_DB = {
    'users': {'admin': hashlib.sha256('admin123'.encode()).hexdigest()},
    'servers': [],
    'categories': [
        {'id': 'HOT', 'name': 'HOT', 'icon': '🔥', 'order': 1},
        {'id': 'EVO', 'name': 'EVO', 'icon': '⚡', 'order': 2},
        {'id': 'RARE', 'name': 'RARE', 'icon': '💎', 'order': 3}
    ],
    'emotes': [],
    'settings': {
        'maintenance': {'enabled': False, 'message': 'System is being upgraded. Please check back later.'},
        'footerLinks': {
            'telegram': '#',
            'github': '#',
            'discord': '#',
            'youtube': '#'
        }
    }
}

DATABASE = {k: v for k, v in DEFAULT_DB.items()}

# Helper functions for Firebase operations with better error handling
def firebase_save_all():
    """Save all data to Firebase"""
    if not firebase_initialized or not db:
        return False
    
    try:
        # Save servers
        for server in DATABASE.get('servers', []):
            doc_ref = db.collection('servers').document(str(server['id']))
            doc_ref.set(server)
        
        # Save categories
        for category in DATABASE.get('categories', []):
            doc_ref = db.collection('categories').document(str(category['id']))
            doc_ref.set(category)
        
        # Save emotes
        for emote in DATABASE.get('emotes', []):
            doc_ref = db.collection('emotes').document(str(emote['id']))
            doc_ref.set(emote)
        
        # Save settings
        settings_ref = db.collection('settings').document('app_settings')
        settings_ref.set(DATABASE.get('settings', {}))
        
        # Save users
        users_ref = db.collection('users').document('admin')
        users_ref.set(DATABASE.get('users', {}))
        
        print(f'[FIREBASE] ✅ Saved to Firebase: {len(DATABASE.get("emotes",[]))} emotes, {len(DATABASE.get("servers",[]))} servers')
        return True
    except Exception as e:
        print(f'[FIREBASE] ❌ Save error: {e}')
        return False

def firebase_load_all():
    """Load all data from Firebase"""
    if not firebase_initialized or not db:
        return False
    
    try:
        # Load servers
        servers_ref = db.collection('servers')
        servers = []
        for doc in servers_ref.stream():
            server_data = doc.to_dict()
            if server_data:
                servers.append(server_data)
        if servers:
            DATABASE['servers'] = servers
        
        # Load categories
        categories_ref = db.collection('categories')
        categories = []
        for doc in categories_ref.stream():
            category_data = doc.to_dict()
            if category_data:
                categories.append(category_data)
        if categories:
            DATABASE['categories'] = categories
        
        # Load emotes
        emotes_ref = db.collection('emotes')
        emotes = []
        for doc in emotes_ref.stream():
            emote_data = doc.to_dict()
            if emote_data:
                emotes.append(emote_data)
        if emotes:
            DATABASE['emotes'] = emotes
        
        # Load settings
        settings_ref = db.collection('settings').document('app_settings')
        settings_doc = settings_ref.get()
        if settings_doc.exists:
            DATABASE['settings'] = settings_doc.to_dict()
        
        # Load users
        users_ref = db.collection('users').document('admin')
        users_doc = users_ref.get()
        if users_doc.exists:
            DATABASE['users'] = users_doc.to_dict()
        
        print(f'[FIREBASE] ✅ Loaded from Firebase: {len(DATABASE.get("emotes",[]))} emotes, {len(DATABASE.get("servers",[]))} servers')
        return True
    except Exception as e:
        print(f'[FIREBASE] ❌ Load error: {e}')
        return False

def save_database():
    """Save database - tries Firebase first, then local file"""
    # Try Firebase first
    if firebase_initialized:
        if firebase_save_all():
            return True
    
    # Fallback to local file
    save_local_database()

def load_database():
    """Load database - tries Firebase first, then local file"""
    # Try Firebase first
    if firebase_initialized:
        if firebase_load_all():
            return
    
    # Fallback to local file
    load_local_database()

def load_local_database():
    global DATABASE
    try:
        if os.path.exists(DB_PATH):
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            for key in DEFAULT_DB:
                if key in loaded:
                    DATABASE[key] = loaded[key]
            print(f'[DB] ✅ Loaded from local file: {DB_PATH}')
        else:
            print(f'[DB] 📝 No local database found, using defaults')
            save_local_database()
    except Exception as e:
        print(f'[DB] ❌ Load error: {e} — using defaults')

def save_local_database():
    """Save to local JSON file as fallback"""
    tmp_path = DB_PATH + '.tmp'
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(DATABASE, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, DB_PATH)
        print(f'[DB] ✅ Saved to local file: {len(DATABASE.get("emotes",[]))} emotes, {len(DATABASE.get("servers",[]))} servers')
    except Exception as e:
        print(f'[DB] ❌ SAVE ERROR: {e}')
        try:
            os.remove(tmp_path)
        except:
            pass

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def require_login():
    if 'logged_in' not in session:
        return False
    return True

# ========== HTML TEMPLATES ==========

# NOTE: I'm keeping your original HTML exactly as you had them
# Just make sure to copy your original INDEX_HTML, DASHBOARD_HTML, ADMIN_HTML here
# For now, I'll put placeholder comments - you need to paste your original HTML

INDEX_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EMOTE BOT — ACCESS</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --c0:#000;--c1:#0a0f0a;--c2:#0d1a0d;
  --green:#00ff41;--green2:#00cc33;--green3:rgba(0,255,65,0.12);
  --green4:rgba(0,255,65,0.06);--green5:rgba(0,255,65,0.25);
  --text:#c8ffc8;--muted:#4a7a4a;--border:rgba(0,255,65,0.2);
}
body{font-family:'Share Tech Mono',monospace;background:var(--c0);color:var(--text);min-height:100vh;overflow:hidden;position:relative;}
body::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.15) 2px,rgba(0,0,0,0.15) 4px);pointer-events:none;z-index:9999;}
.grid-bg{position:fixed;inset:0;background-image:linear-gradient(rgba(0,255,65,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,65,0.03) 1px,transparent 1px);background-size:40px 40px;z-index:0;}
@keyframes glowPulse{0%,100%{opacity:0.3;}50%{opacity:0.7;}}
@keyframes borderGlow{0%,100%{box-shadow:0 0 5px rgba(0,255,65,0.2),inset 0 0 5px rgba(0,255,65,0.1);}50%{box-shadow:0 0 20px rgba(0,255,65,0.5),inset 0 0 10px rgba(0,255,65,0.2);}}
.glow-tl{position:fixed;top:-100px;left:-100px;width:400px;height:400px;background:radial-gradient(circle,rgba(0,255,65,0.08) 0%,transparent 70%);z-index:0;pointer-events:none;animation:glowPulse 4s ease-in-out infinite;}
.glow-br{position:fixed;bottom:-100px;right:-100px;width:400px;height:400px;background:radial-gradient(circle,rgba(0,255,65,0.05) 0%,transparent 70%);z-index:0;pointer-events:none;animation:glowPulse 4s ease-in-out infinite reverse;}
.glow-center{position:fixed;top:50%;left:50%;width:600px;height:600px;transform:translate(-50%,-50%);background:radial-gradient(circle,rgba(0,255,65,0.03) 0%,transparent 70%);z-index:0;pointer-events:none;}
#matrix{position:fixed;inset:0;z-index:1;opacity:0.18;pointer-events:none;}
.login-wrap{position:relative;z-index:10;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;}
.login-box{width:100%;max-width:440px;border:1px solid var(--border);background:linear-gradient(135deg,rgba(0,20,0,0.95),rgba(0,10,0,0.98));padding:50px 40px;position:relative;clip-path:polygon(12px 0%,100% 0%,100% calc(100% - 12px),calc(100% - 12px) 100%,0% 100%,0% 12px);animation:borderGlow 3s ease-in-out infinite;}
.login-box::before{content:'';position:absolute;inset:0;border:1px solid var(--border);clip-path:polygon(12px 0%,100% 0%,100% calc(100% - 12px),calc(100% - 12px) 100%,0% 100%,0% 12px);pointer-events:none;}
.login-box::after{content:'';position:absolute;top:0;left:12px;right:0;height:2px;background:linear-gradient(90deg,var(--green),transparent);animation:borderGlow 2s ease-in-out infinite;}
.brand{text-align:center;margin-bottom:40px;}
.brand-icon{font-size:48px;display:block;margin-bottom:12px;filter:drop-shadow(0 0 20px var(--green));animation:glowPulse 2s ease-in-out infinite;}
.brand-name{font-family:'Rajdhani',sans-serif;font-size:32px;font-weight:700;letter-spacing:6px;color:var(--green);text-shadow:0 0 20px var(--green),0 0 40px rgba(0,255,65,0.3);}
.brand-sub{font-size:11px;color:var(--muted);letter-spacing:4px;margin-top:4px;}
.sys-line{font-size:10px;color:var(--muted);margin-bottom:30px;padding:8px 12px;border-left:2px solid var(--green);background:rgba(0,255,65,0.03);}
.sys-line span{color:var(--green);}
.input-wrap{position:relative;margin-bottom:20px;}
.input-label{font-size:10px;color:var(--muted);letter-spacing:3px;margin-bottom:8px;display:block;}
.login-input{width:100%;padding:14px 18px;background:rgba(0,255,65,0.04);border:1px solid rgba(0,255,65,0.25);color:var(--green);font-family:'Share Tech Mono',monospace;font-size:14px;outline:none;transition:all 0.3s;caret-color:var(--green);}
.login-input::placeholder{color:var(--muted);}
.login-input:focus{border-color:var(--green);background:rgba(0,255,65,0.07);box-shadow:0 0 20px rgba(0,255,65,0.1),inset 0 0 20px rgba(0,255,65,0.02);}
.login-btn{width:100%;padding:16px;background:transparent;border:1px solid var(--green);color:var(--green);font-family:'Share Tech Mono',monospace;font-size:13px;letter-spacing:4px;cursor:pointer;transition:all 0.3s;position:relative;overflow:hidden;margin-top:8px;}
.login-btn::before{content:'';position:absolute;inset:0;background:var(--green);transform:translateX(-100%);transition:transform 0.3s;}
.login-btn:hover::before{transform:translateX(0);}
.login-btn:hover{color:#000;box-shadow:0 0 30px rgba(0,255,65,0.3);}
.login-btn span{position:relative;z-index:1;}
.login-btn:active{transform:scale(0.98);}
.err-msg{padding:10px 14px;background:rgba(255,0,60,0.08);border:1px solid rgba(255,0,60,0.3);color:#ff3c5a;font-size:11px;letter-spacing:1px;text-align:center;margin-top:12px;}
.hidden{display:none!important;}
.social-row{display:flex;justify-content:center;gap:12px;margin-top:35px;padding-top:25px;border-top:1px solid rgba(0,255,65,0.1);}
.soc-btn{width:38px;height:38px;border:1px solid rgba(0,255,65,0.2);display:flex;align-items:center;justify-content:center;color:var(--muted);transition:all 0.3s;text-decoration:none;}
.soc-btn:hover{border-color:var(--green);color:var(--green);background:rgba(0,255,65,0.08);box-shadow:0 0 15px rgba(0,255,65,0.2);transform:scale(1.1) rotate(5deg);}
.soc-btn svg{width:18px;height:18px;}
.status-bar{position:absolute;bottom:0;left:0;right:0;padding:6px 14px;background:rgba(0,255,65,0.04);border-top:1px solid rgba(0,255,65,0.1);display:flex;justify-content:space-between;font-size:9px;color:var(--muted);}
.status-bar .online{color:var(--green);}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0;}}
.cursor{animation:blink 1s step-end infinite;}
.ripple{position:fixed;border-radius:50%;background:radial-gradient(circle, rgba(0,255,65,0.6) 0%, rgba(0,255,65,0) 70%);width:0;height:0;transform:translate(-50%,-50%);animation:rippleAnim 0.8s ease-out forwards;pointer-events:none;z-index:99999;}
@keyframes rippleAnim{0%{width:0;height:0;opacity:0.8;}100%{width:200px;height:200px;opacity:0;}}
</style>
</head>
<body>
<div class="grid-bg"></div>
<div class="glow-tl"></div>
<div class="glow-br"></div>
<div class="glow-center"></div>
<canvas id="matrix"></canvas>
<div class="login-wrap">
  <div class="login-box">
    <div class="brand">
      <span class="brand-icon">⚡</span>
      <div class="brand-name">EMOTE BOT</div>
      <div class="brand-sub">// CONTROL PANEL v3.0</div>
    </div>
    <div class="sys-line">SYS: <span>AUTHENTICATION REQUIRED</span> — ENTER CREDENTIALS<span class="cursor">_</span></div>
    <form id="loginForm">
      <div class="input-wrap">
        <span class="input-label">// ACCESS KEY</span>
        <input type="password" id="loginPassword" placeholder="••••••••••••" class="login-input" required autocomplete="off">
      </div>
      <button type="submit" class="login-btn"><span>[ AUTHENTICATE ]</span></button>
      <div id="loginError" class="err-msg hidden">// ERROR: INVALID ACCESS KEY — DENIED</div>
    </form>
    <div class="social-row">
      <a href="#" id="telegram" class="soc-btn"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/></svg></a>
      <a href="#" id="github" class="soc-btn"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2A10 10 0 002 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z"/></svg></a>
      <a href="#" id="discord" class="soc-btn"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028 13.83 13.83 0 001.226-1.994.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03z"/></svg></a>
      <a href="#" id="youtube" class="soc-btn"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg></a>
    </div>
    <div class="status-bar">
      <span><span class="online">●</span> ONLINE</span>
      <span>NODE: AUTH-01</span>
      <span id="sysTime">--:--:--</span>
    </div>
  </div>
</div>
<script>
document.addEventListener('click', function(e) {const ripple = document.createElement('div');ripple.className = 'ripple';ripple.style.left = e.clientX + 'px';ripple.style.top = e.clientY + 'px';document.body.appendChild(ripple);setTimeout(() => ripple.remove(), 800);});
const canvas = document.getElementById('matrix');const ctx = canvas.getContext('2d');canvas.width = window.innerWidth;canvas.height = window.innerHeight;const cols = Math.floor(canvas.width / 18);const drops = Array(cols).fill(1);const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノ';
function drawMatrix(){ctx.fillStyle='rgba(0,0,0,0.05)';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#00ff41';ctx.font='14px Share Tech Mono';drops.forEach((y,i)=>{const c=chars[Math.floor(Math.random()*chars.length)];ctx.fillText(c,i*18,y*18);if(y*18>canvas.height&&Math.random()>0.975) drops[i]=0;drops[i]++;});}
setInterval(drawMatrix,50);
function tick(){const n=new Date();document.getElementById('sysTime').textContent=n.toTimeString().slice(0,8);}
setInterval(tick,1000);tick();
document.getElementById('loginForm').addEventListener('submit',async e=>{e.preventDefault();const pw=document.getElementById('loginPassword').value;const err=document.getElementById('loginError');try{const r=await fetch('/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'password='+encodeURIComponent(pw)});const res=await r.json();if(res.success){window.location.href='/dashboard';}else{err.classList.remove('hidden');document.getElementById('loginPassword').value='';setTimeout(()=>err.classList.add('hidden'),3000);}}catch(ex){err.classList.remove('hidden');}});
async function loadLinks(){try{const r=await fetch('/api/settings');const d=await r.json();const l=d.footerLinks||{};document.getElementById('telegram').href=l.telegram||'#';document.getElementById('github').href=l.github||'#';document.getElementById('discord').href=l.discord||'#';document.getElementById('youtube').href=l.youtube||'#';}catch(e){}}
loadLinks();
</script>
</body>
</html>'''

# ========== ROUTES ==========

@app.route('/')
def index():
    if require_login():
        return redirect('/dashboard')
    return render_template_string(INDEX_HTML)

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password', '')
    hashed_input = hash_password(password)
    if not DATABASE['users']:
        DATABASE['users']['admin'] = hashlib.sha256('admin123'.encode()).hexdigest()
        save_database()
    if hashed_input == DATABASE['users'].get('admin'):
        session['logged_in'] = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Invalid password'})

@app.route('/dashboard')
def dashboard():
    if not require_login():
        return redirect('/')
    # You need to paste your DASHBOARD_HTML here
    return "<h1>Dashboard - Paste your DASHBOARD_HTML here</h1>"

@app.route('/admin')
def admin():
    # You need to paste your ADMIN_HTML here
    return "<h1>Admin Panel - Paste your ADMIN_HTML here</h1>"

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

@app.route('/api/data')
def get_data():
    if not require_login():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({
        'servers': DATABASE['servers'],
        'categories': DATABASE['categories'],
        'emotes': DATABASE['emotes'],
        'settings': DATABASE['settings']
    })

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    email = data.get('email', '')
    password = data.get('password', '')
    if email == 'xcy@example.com' and password == 'Bijayvip':
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/api/servers', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_servers():
    if request.method == 'GET':
        return jsonify({'servers': DATABASE['servers']})
    elif request.method == 'POST':
        try:
            data = request.json
            server_id = str(int(time.time() * 1000))
            server = {
                'id': server_id,
                'name': data.get('name', '').strip(),
                'baseUrl': data.get('baseUrl', '').strip().rstrip('/'),
                'region': data.get('region', ''),
                'order': int(data.get('order') or 0)
            }
            DATABASE['servers'].append(server)
            save_database()
            print(f'[SERVER] Added: {server["name"]}')
            return jsonify({'success': True, 'server': server})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    elif request.method == 'PUT':
        try:
            data = request.json
            server_id = str(data.get('id', ''))
            found = False
            for i, server in enumerate(DATABASE['servers']):
                if str(server['id']) == server_id:
                    DATABASE['servers'][i] = {
                        'id': server_id,
                        'name': data.get('name', '').strip(),
                        'baseUrl': data.get('baseUrl', '').strip().rstrip('/'),
                        'region': data.get('region', ''),
                        'order': int(data.get('order') or 0)
                    }
                    found = True
                    break
            if not found:
                return jsonify({'success': False, 'error': 'Server not found'})
            save_database()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    elif request.method == 'DELETE':
        try:
            server_id = str(request.args.get('id', ''))
            DATABASE['servers'] = [s for s in DATABASE['servers'] if str(s['id']) != server_id]
            save_database()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/categories', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_categories():
    if request.method == 'GET':
        return jsonify({'categories': DATABASE['categories']})
    elif request.method == 'POST':
        try:
            data = request.json
            name = data.get('name', '').strip()
            cat_id = data.get('id') or name.upper().replace(' ', '_')
            category = {
                'id': cat_id,
                'name': name,
                'icon': data.get('icon', ''),
                'order': int(data.get('order') or 0)
            }
            DATABASE['categories'].append(category)
            save_database()
            print(f'[CAT] Added: {name}')
            return jsonify({'success': True, 'category': category})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    elif request.method == 'PUT':
        try:
            data = request.json
            category_id = str(data.get('id', ''))
            found = False
            for i, category in enumerate(DATABASE['categories']):
                if str(category['id']) == category_id:
                    DATABASE['categories'][i] = {
                        'id': category_id,
                        'name': data.get('name', '').strip(),
                        'icon': data.get('icon', ''),
                        'order': int(data.get('order') or 0)
                    }
                    found = True
                    break
            if not found:
                return jsonify({'success': False, 'error': 'Category not found'})
            save_database()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    elif request.method == 'DELETE':
        try:
            category_id = str(request.args.get('id', ''))
            DATABASE['categories'] = [c for c in DATABASE['categories'] if str(c['id']) != category_id]
            save_database()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/emotes', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_emotes():
    if request.method == 'GET':
        return jsonify({'emotes': DATABASE['emotes']})
    elif request.method == 'POST':
        try:
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': 'No data received'})
            image_url = data.get('imageUrl', '').strip()
            category = data.get('category', '').strip()
            if not image_url or not category:
                return jsonify({'success': False, 'error': 'imageUrl and category are required'})
            emote_name = data.get('emoteId') or image_url.split('/')[-1].split('.')[0]
            emote = {
                'id': str(int(time.time() * 1000)),
                'imageUrl': image_url,
                'category': category,
                'emoteId': emote_name
            }
            DATABASE['emotes'].append(emote)
            save_database()
            print(f'[EMOTE] Added: {emote_name} in {category}, total: {len(DATABASE["emotes"])}')
            return jsonify({'success': True, 'emote': emote})
        except Exception as e:
            print(f'[EMOTE] POST error: {e}')
            return jsonify({'success': False, 'error': str(e)})
    elif request.method == 'PUT':
        try:
            data = request.json
            emote_id = str(data.get('id', ''))
            image_url = data.get('imageUrl', '').strip()
            category = data.get('category', '').strip()
            found = False
            for i, emote in enumerate(DATABASE['emotes']):
                if str(emote['id']) == emote_id:
                    DATABASE['emotes'][i] = {
                        'id': emote_id,
                        'imageUrl': image_url,
                        'category': category,
                        'emoteId': data.get('emoteId') or image_url.split('/')[-1].split('.')[0]
                    }
                    found = True
                    break
            if not found:
                return jsonify({'success': False, 'error': f'Emote id={emote_id} not found'})
            save_database()
            return jsonify({'success': True})
        except Exception as e:
            print(f'[EMOTE] PUT error: {e}')
            return jsonify({'success': False, 'error': str(e)})
    elif request.method == 'DELETE':
        try:
            emote_id = str(request.args.get('id', ''))
            before = len(DATABASE['emotes'])
            DATABASE['emotes'] = [e for e in DATABASE['emotes'] if str(e['id']) != emote_id]
            save_database()
            print(f'[EMOTE] Deleted id={emote_id}, removed {before - len(DATABASE["emotes"])} item(s)')
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    if request.method == 'GET':
        return jsonify(DATABASE['settings'])
    elif request.method == 'POST':
        data = request.json
        setting_type = data.get('type')
        if setting_type == 'maintenance':
            DATABASE['settings']['maintenance'] = {'enabled': data.get('enabled', False), 'message': data.get('message', '')}
        elif setting_type == 'footerLinks':
            DATABASE['settings']['footerLinks'] = {'telegram': data.get('telegram', '#'), 'github': data.get('github', '#'), 'discord': data.get('discord', '#'), 'youtube': data.get('youtube', '#')}
        elif setting_type == 'password':
            new_password = data.get('password')
            if new_password:
                DATABASE['users']['admin'] = hash_password(new_password)
        save_database()
        return jsonify({'success': True})

@app.route('/api/send-emote', methods=['GET'])
def send_emote():
    server = request.args.get('server')
    tc = request.args.get('tc')
    emote_id = request.args.get('emote_id')
    uids = {}
    for i in range(1, 6):
        uid = request.args.get(f'uid{i}')
        if uid:
            uids[f'uid{i}'] = uid
    if not server or not tc or not emote_id:
        return jsonify({'success': False, 'error': 'Missing required parameters'})
    params = {'tc': tc, 'emote_id': emote_id, **uids}
    query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    target_url = f"{server}/join?{query_string}"
    try:
        response = requests.get(target_url, timeout=10)
        return jsonify({'success': True, 'status': response.status_code, 'message': 'Emote sent successfully', 'data': response.text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Load database on startup
load_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)