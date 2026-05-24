from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, send_from_directory
import json
import os
import hashlib
import time
import urllib.parse
import requests

app = Flask(__name__)
app.secret_key = 'emote-bot-secret-key-2024'

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

def load_database():
    global DATABASE
    try:
        if os.path.exists(DB_PATH):
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            # Merge loaded data into default structure so missing keys dont crash
            for key in DEFAULT_DB:
                if key in loaded:
                    DATABASE[key] = loaded[key]
            print(f'[DB] Loaded from {DB_PATH}')
        else:
            print(f'[DB] No database.json found, starting fresh at {DB_PATH}')
    except Exception as e:
        print(f'[DB] Load error: {e} — starting with defaults')

def save_database():
    """Atomic write: write to temp file then rename so a crash never corrupts the DB."""
    tmp_path = DB_PATH + '.tmp'
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(DATABASE, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, DB_PATH)
        print(f'[DB] Saved {len(DATABASE.get("emotes",[]))} emotes, {len(DATABASE.get("servers",[]))} servers')
    except Exception as e:
        print(f'[DB] SAVE ERROR: {e}')
        # Remove failed temp file if it exists
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

INDEX_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>XCY LIVE — ACCESS</title>
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

/* SCANLINES */
body::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.15) 2px,rgba(0,0,0,0.15) 4px);pointer-events:none;z-index:9999;}

/* GRID BG */
.grid-bg{position:fixed;inset:0;background-image:linear-gradient(rgba(0,255,65,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,65,0.03) 1px,transparent 1px);background-size:40px 40px;z-index:0;}

/* CORNER GLOWS */
.glow-tl{position:fixed;top:-100px;left:-100px;width:400px;height:400px;background:radial-gradient(circle,rgba(0,255,65,0.08) 0%,transparent 70%);z-index:0;pointer-events:none;}
.glow-br{position:fixed;bottom:-100px;right:-100px;width:400px;height:400px;background:radial-gradient(circle,rgba(0,255,65,0.05) 0%,transparent 70%);z-index:0;pointer-events:none;}

/* MATRIX RAIN */
#matrix{position:fixed;inset:0;z-index:1;opacity:0.18;pointer-events:none;}

.login-wrap{position:relative;z-index:10;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;}
.login-box{width:100%;max-width:440px;border:1px solid var(--border);background:linear-gradient(135deg,rgba(0,20,0,0.95),rgba(0,10,0,0.98));padding:50px 40px;position:relative;clip-path:polygon(12px 0%,100% 0%,100% calc(100% - 12px),calc(100% - 12px) 100%,0% 100%,0% 12px);}
.login-box::before{content:'';position:absolute;inset:0;border:1px solid var(--border);clip-path:polygon(12px 0%,100% 0%,100% calc(100% - 12px),calc(100% - 12px) 100%,0% 100%,0% 12px);pointer-events:none;}

/* TOP ACCENT LINE */
.login-box::after{content:'';position:absolute;top:0;left:12px;right:0;height:2px;background:linear-gradient(90deg,var(--green),transparent);pointer-events:none;}

.brand{text-align:center;margin-bottom:40px;}
.brand-icon{font-size:48px;display:block;margin-bottom:12px;filter:drop-shadow(0 0 20px var(--green));}
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
.login-btn:hover{color:#000;}
.login-btn span{position:relative;z-index:1;}
.login-btn:active{transform:scale(0.98);}

.err-msg{padding:10px 14px;background:rgba(255,0,60,0.08);border:1px solid rgba(255,0,60,0.3);color:#ff3c5a;font-size:11px;letter-spacing:1px;text-align:center;margin-top:12px;}
.hidden{display:none!important;}

.social-row{display:flex;justify-content:center;gap:12px;margin-top:35px;padding-top:25px;border-top:1px solid rgba(0,255,65,0.1);}
.soc-btn{width:38px;height:38px;border:1px solid rgba(0,255,65,0.2);display:flex;align-items:center;justify-content:center;color:var(--muted);transition:all 0.3s;text-decoration:none;}
.soc-btn:hover{border-color:var(--green);color:var(--green);background:rgba(0,255,65,0.08);box-shadow:0 0 15px rgba(0,255,65,0.2);}
.soc-btn svg{width:18px;height:18px;}

.status-bar{position:absolute;bottom:0;left:0;right:0;padding:6px 14px;background:rgba(0,255,65,0.04);border-top:1px solid rgba(0,255,65,0.1);display:flex;justify-content:space-between;font-size:9px;color:var(--muted);}
.status-bar .online{color:var(--green);}

@keyframes blink{0%,100%{opacity:1;}50%{opacity:0;}}
.cursor{animation:blink 1s step-end infinite;}
</style>
</head>
<body>
<div class="grid-bg"></div>
<div class="glow-tl"></div>
<div class="glow-br"></div>
<canvas id="matrix"></canvas>

<div class="login-wrap">
  <div class="login-box">
    <div class="brand">
      <span class="brand-icon">⚡</span>
      <div class="brand-name">XCY LIVE</div>
      <div class="brand-sub">// CONTROL PANEL v2.0</div>
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
// Matrix rain
const canvas = document.getElementById('matrix');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;
const cols = Math.floor(canvas.width / 18);
const drops = Array(cols).fill(1);
const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノ';
function drawMatrix(){
  ctx.fillStyle='rgba(0,0,0,0.05)';
  ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.fillStyle='#00ff41';
  ctx.font='14px Share Tech Mono';
  drops.forEach((y,i)=>{
    const c=chars[Math.floor(Math.random()*chars.length)];
    ctx.fillText(c,i*18,y*18);
    if(y*18>canvas.height&&Math.random()>0.975) drops[i]=0;
    drops[i]++;
  });
}
setInterval(drawMatrix,50);

// Clock
function tick(){
  const n=new Date();
  document.getElementById('sysTime').textContent=n.toTimeString().slice(0,8);
}
setInterval(tick,1000);tick();

// Login
document.getElementById('loginForm').addEventListener('submit',async e=>{
  e.preventDefault();
  const pw=document.getElementById('loginPassword').value;
  const err=document.getElementById('loginError');
  try{
    const r=await fetch('/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'password='+encodeURIComponent(pw)});
    const res=await r.json();
    if(res.success){window.location.href='/dashboard';}
    else{
      err.classList.remove('hidden');
      document.getElementById('loginPassword').value='';
      setTimeout(()=>err.classList.add('hidden'),3000);
    }
  }catch(ex){err.classList.remove('hidden');}
});

async function loadLinks(){
  try{
    const r=await fetch('/api/settings');
    const d=await r.json();
    const l=d.footerLinks||{};
    document.getElementById('telegram').href=l.telegram||'#';
    document.getElementById('github').href=l.github||'#';
    document.getElementById('discord').href=l.discord||'#';
    document.getElementById('youtube').href=l.youtube||'#';
  }catch(e){}
}
loadLinks();
</script>
</body>
</html>'''

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>XCY LIVE — DASHBOARD</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --green:#00ff41;--green2:#00cc33;--green3:rgba(0,255,65,0.12);
  --green4:rgba(0,255,65,0.06);--green5:rgba(0,255,65,0.3);
  --text:#c8ffc8;--muted:#4a7a4a;--border:rgba(0,255,65,0.18);
  --card:rgba(0,15,0,0.85);--red:#ff3c5a;--amber:#ffaa00;
}
body{font-family:'Share Tech Mono',monospace;background:#000;color:var(--text);min-height:100vh;overflow-x:hidden;position:relative;}

/* SCANLINES */
body::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.1) 2px,rgba(0,0,0,0.1) 4px);pointer-events:none;z-index:9998;}

/* GRID BG */
.grid-bg{position:fixed;inset:0;background-image:linear-gradient(rgba(0,255,65,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,65,0.025) 1px,transparent 1px);background-size:40px 40px;z-index:0;}

/* CLICK RIPPLE */
.ripple{position:fixed;border-radius:50%;background:rgba(0,255,65,0.3);width:0;height:0;transform:translate(-50%,-50%);animation:rippleAnim 0.6s ease-out forwards;pointer-events:none;z-index:99999;}
@keyframes rippleAnim{to{width:100px;height:100px;opacity:0;}}

.wrap{max-width:820px;margin:0 auto;padding:16px;position:relative;z-index:10;}

/* HEADER */
.hdr{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border:1px solid var(--border);background:var(--card);margin-bottom:16px;position:relative;overflow:hidden;}
.hdr::after{content:'';position:absolute;bottom:0;left:0;right:0;height:1px;background:linear-gradient(90deg,var(--green),transparent);}
.hdr-brand{display:flex;align-items:center;gap:10px;}
.hdr-brand .ico{font-size:26px;filter:drop-shadow(0 0 8px var(--green));}
.hdr-brand h1{font-family:'Rajdhani',sans-serif;font-size:22px;font-weight:700;letter-spacing:5px;color:var(--green);text-shadow:0 0 15px rgba(0,255,65,0.5);}
.hdr-right{display:flex;gap:8px;align-items:center;}
.sys-clock{font-size:11px;color:var(--muted);padding:6px 10px;border:1px solid rgba(0,255,65,0.12);letter-spacing:2px;}
.hdr-btn{width:36px;height:36px;border:1px solid rgba(0,255,65,0.2);background:transparent;color:var(--muted);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;}
.hdr-btn:hover{border-color:var(--green);color:var(--green);background:rgba(0,255,65,0.08);box-shadow:0 0 12px rgba(0,255,65,0.2);}
.hdr-btn svg{width:18px;height:18px;}

/* PANEL */
.panel{border:1px solid var(--border);background:var(--card);padding:18px 20px;margin-bottom:14px;position:relative;overflow:hidden;}
.panel::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,var(--green),transparent);}
.panel-title{display:flex;align-items:center;gap:10px;margin-bottom:16px;}
.panel-title .tag{font-size:9px;letter-spacing:3px;color:var(--muted);}
.panel-title h2{font-family:'Rajdhani',sans-serif;font-size:14px;font-weight:700;letter-spacing:3px;color:var(--green);}
.panel-title .flag{font-size:18px;}
.corner-tl{position:absolute;top:0;left:0;width:8px;height:8px;border-top:2px solid var(--green);border-left:2px solid var(--green);}
.corner-br{position:absolute;bottom:0;right:0;width:8px;height:8px;border-bottom:2px solid var(--green);border-right:2px solid var(--green);}

/* SERVER SELECT */
.server-select{width:100%;padding:12px 16px;background:rgba(0,255,65,0.04);border:1px solid rgba(0,255,65,0.2);color:var(--green);font-family:'Share Tech Mono',monospace;font-size:13px;cursor:pointer;outline:none;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2300ff41' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;padding-right:36px;transition:all 0.3s;}
.server-select:focus{border-color:var(--green);background-color:rgba(0,255,65,0.07);box-shadow:0 0 15px rgba(0,255,65,0.1);}
.server-select option{background:#0a0f0a;color:var(--text);}

/* CONFIG GRID - UID + EMOTE side by side */
.config-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;}
@media(max-width:640px){.config-grid{grid-template-columns:1fr;}}

/* INPUT */
.field{margin-bottom:12px;}
.field label{font-size:9px;color:var(--muted);letter-spacing:3px;display:block;margin-bottom:6px;}
.cfg-input{width:100%;padding:11px 14px;background:rgba(0,255,65,0.04);border:1px solid rgba(0,255,65,0.18);color:var(--green);font-family:'Share Tech Mono',monospace;font-size:13px;outline:none;transition:all 0.3s;caret-color:var(--green);}
.cfg-input::placeholder{color:var(--muted);}
.cfg-input:focus{border-color:var(--green);background:rgba(0,255,65,0.07);box-shadow:0 0 12px rgba(0,255,65,0.08);}

/* UID ROW */
.uid-row{display:flex;gap:8px;align-items:center;}
.uid-row .cfg-input{flex:1;}
.uid-del{width:34px;height:34px;flex-shrink:0;background:rgba(255,60,90,0.08);border:1px solid rgba(255,60,90,0.25);color:var(--red);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;font-size:16px;line-height:1;}
.uid-del:hover{background:rgba(255,60,90,0.15);border-color:var(--red);}

.add-uid-btn{width:100%;padding:10px;background:transparent;border:1px dashed rgba(0,255,65,0.25);color:var(--muted);font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:3px;cursor:pointer;transition:all 0.3s;margin-top:4px;}
.add-uid-btn:hover:not(:disabled){border-color:var(--green);color:var(--green);background:rgba(0,255,65,0.04);}
.add-uid-btn:disabled{opacity:0.3;cursor:not-allowed;}

/* EMOTE SECTION */
.cat-tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;}
.cat-tab{padding:6px 14px;background:transparent;border:1px solid rgba(0,255,65,0.18);color:var(--muted);font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;cursor:pointer;transition:all 0.25s;}
.cat-tab:hover{border-color:var(--green);color:var(--green);}
.cat-tab.active{background:var(--green);color:#000;border-color:var(--green);font-weight:700;}

/* EMOTE GRID — 5 col by default, never overflow */
.emote-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;max-height:320px;overflow-y:auto;padding-right:4px;}
.emote-grid::-webkit-scrollbar{width:4px;}
.emote-grid::-webkit-scrollbar-track{background:rgba(0,255,65,0.04);}
.emote-grid::-webkit-scrollbar-thumb{background:rgba(0,255,65,0.3);}
@media(max-width:640px){.emote-grid{grid-template-columns:repeat(4,1fr);}}
@media(max-width:380px){.emote-grid{grid-template-columns:repeat(3,1fr);}}

.emote-card{aspect-ratio:1;border:1px solid rgba(0,255,65,0.12);background:rgba(0,255,65,0.03);cursor:pointer;transition:all 0.25s;position:relative;overflow:hidden;display:flex;flex-direction:column;}
.emote-card:hover{border-color:rgba(0,255,65,0.5);background:rgba(0,255,65,0.08);transform:scale(1.04);box-shadow:0 0 18px rgba(0,255,65,0.2);}
.emote-card.selected{border-color:var(--green);background:rgba(0,255,65,0.15);box-shadow:0 0 25px rgba(0,255,65,0.4);}
.emote-card.selected::after{content:'✓';position:absolute;top:2px;right:3px;font-size:10px;color:var(--green);font-weight:bold;}
.emote-img-wrap{flex:1;display:flex;align-items:center;justify-content:center;overflow:hidden;}
.emote-card img{width:100%;height:100%;object-fit:cover;transition:transform 0.25s;}
.emote-card:hover img{transform:scale(1.1);}
.emote-lbl{font-size:8px;color:var(--muted);text-align:center;padding:3px 2px 4px;letter-spacing:0.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.emote-card.selected .emote-lbl{color:var(--green);}
.no-emotes{grid-column:1/-1;text-align:center;color:var(--muted);padding:30px;font-size:11px;}

/* STATUS BAR */
.status-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;}
@media(max-width:500px){.status-grid{grid-template-columns:1fr;}}
.stat-box{padding:12px 14px;border:1px solid rgba(0,255,65,0.12);background:rgba(0,255,65,0.03);}
.stat-lbl{font-size:9px;color:var(--muted);letter-spacing:2px;margin-bottom:5px;}
.stat-val{font-size:13px;color:var(--green);font-family:'Rajdhani',sans-serif;font-weight:600;letter-spacing:1px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}

/* TOAST */
#toastBox{position:fixed;top:70px;right:16px;z-index:99999;display:flex;flex-direction:column;gap:8px;}
.toast{display:flex;align-items:center;gap:10px;padding:12px 18px;border:1px solid;background:rgba(0,10,0,0.95);font-size:11px;letter-spacing:1px;opacity:0;transform:translateX(120%);transition:all 0.35s;min-width:260px;max-width:360px;backdrop-filter:blur(10px);}
.toast.show{opacity:1;transform:translateX(0);}
.toast.t-ok{border-color:rgba(0,255,65,0.4);color:var(--green);}
.toast.t-err{border-color:rgba(255,60,90,0.4);color:var(--red);}
.toast.t-inf{border-color:rgba(255,170,0,0.4);color:var(--amber);}
.toast-ico{font-size:14px;flex-shrink:0;}
.toast-msg{flex:1;}

/* LOADING */
#loader{position:fixed;inset:0;background:rgba(0,0,0,0.92);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:99999;backdrop-filter:blur(4px);}
.spin-ring{width:50px;height:50px;border:2px solid rgba(0,255,65,0.1);border-top:2px solid var(--green);border-radius:50%;animation:spin 0.7s linear infinite;margin-bottom:14px;}
@keyframes spin{to{transform:rotate(360deg);}}
.load-txt{font-size:10px;color:var(--muted);letter-spacing:4px;animation:blink 1s step-end infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0;}}

/* MAINTENANCE */
.maint-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.97);display:flex;align-items:center;justify-content:center;z-index:99990;backdrop-filter:blur(8px);}
.maint-box{border:1px solid var(--border);padding:40px;max-width:420px;text-align:center;background:rgba(0,15,0,0.95);position:relative;}
.maint-box::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--green),transparent);}
.maint-ico{font-size:48px;margin-bottom:16px;}
.maint-box h2{font-family:'Rajdhani',sans-serif;font-size:24px;font-weight:700;letter-spacing:4px;color:var(--green);margin-bottom:12px;}
.maint-box p{color:var(--muted);font-size:12px;line-height:1.7;margin-bottom:24px;}
.maint-link{display:inline-block;padding:12px 28px;border:1px solid var(--green);color:var(--green);text-decoration:none;font-size:11px;letter-spacing:3px;transition:all 0.3s;}
.maint-link:hover{background:var(--green);color:#000;}

/* FOOTER */
.footer{display:flex;justify-content:center;gap:10px;padding:20px 0;}
.foot-link{width:36px;height:36px;border:1px solid rgba(0,255,65,0.15);display:flex;align-items:center;justify-content:center;color:var(--muted);text-decoration:none;transition:all 0.25s;}
.foot-link:hover{border-color:var(--green);color:var(--green);background:rgba(0,255,65,0.08);}
.foot-link svg{width:16px;height:16px;}

.hidden{display:none!important;}
</style>
</head>
<body>
<div class="grid-bg"></div>

<div id="maintOverlay" class="maint-overlay hidden">
  <div class="maint-box">
    <div class="maint-ico">🛠</div>
    <h2>MAINTENANCE</h2>
    <p id="maintMsg">System is being upgraded. Please check back later.</p>
    <a href="#" id="maintTG" class="maint-link">JOIN TELEGRAM</a>
  </div>
</div>

<div class="wrap">
  <!-- HEADER -->
  <header class="hdr">
    <div class="hdr-brand">
      <span class="ico">⚡</span>
      <h1>XCY LIVE</h1>
    </div>
    <div class="hdr-right">
      <div class="sys-clock" id="clock">--:--:--</div>
      <button class="hdr-btn" id="logoutBtn" title="Logout">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" stroke-width="2"/></svg>
      </button>
    </div>
  </header>

  <!-- SERVERS -->
  <div class="panel">
    <div class="corner-tl"></div><div class="corner-br"></div>
    <div class="panel-title"><span class="flag">🇮🇳</span><h2>INDIAN SERVERS</h2><span class="tag">// SELECT NODE</span></div>
    <select id="indianSrv" class="server-select"><option value="">-- SELECT INDIAN SERVER --</option></select>
  </div>

  <div class="panel">
    <div class="corner-tl"></div><div class="corner-br"></div>
    <div class="panel-title"><span class="flag">🇧🇩</span><h2>BANGLADESH SERVERS</h2><span class="tag">// SELECT NODE</span></div>
    <select id="bangladeshSrv" class="server-select"><option value="">-- SELECT BANGLADESH SERVER --</option></select>
  </div>

  <div class="panel">
    <div class="corner-tl"></div><div class="corner-br"></div>
    <div class="panel-title"><span class="flag">🌍</span><h2>OTHER SERVERS</h2><span class="tag">// SELECT NODE</span></div>
    <select id="otherSrv" class="server-select"><option value="">-- SELECT OTHER SERVER --</option></select>
  </div>

  <!-- CONFIG + EMOTE SIDE BY SIDE -->
  <div class="config-grid">
    <!-- UID CONFIG -->
    <div class="panel" style="margin-bottom:0;">
      <div class="corner-tl"></div><div class="corner-br"></div>
      <div class="panel-title"><h2>CONFIGURATION</h2></div>
      <div class="field">
        <label>// TEAM CODE *</label>
        <input type="text" id="teamCode" placeholder="Enter team code" class="cfg-input">
      </div>
      <div class="field">
        <label>// TARGET UID 1 *</label>
        <input type="text" id="uid1" placeholder="9–12 digit UID" class="cfg-input" pattern="[0-9]{9,12}">
      </div>
      <div id="uidContainer"></div>
      <button class="add-uid-btn" id="addUidBtn">+ ADD UID</button>
    </div>

    <!-- EMOTE SELECTION -->
    <div class="panel" style="margin-bottom:0;">
      <div class="corner-tl"></div><div class="corner-br"></div>
      <div class="panel-title"><h2>EMOTE SELECTION</h2></div>
      <div class="cat-tabs" id="catTabs"></div>
      <div class="emote-grid" id="emoteGrid"></div>
    </div>
  </div>

  <!-- STATUS -->
  <div class="panel" style="margin-top:14px;">
    <div class="corner-tl"></div><div class="corner-br"></div>
    <div class="panel-title"><h2>STATUS</h2><span class="tag">// LIVE READOUT</span></div>
    <div class="status-grid">
      <div class="stat-box"><div class="stat-lbl">// SERVER</div><div class="stat-val" id="stSrv">NOT SELECTED</div></div>
      <div class="stat-box"><div class="stat-lbl">// EMOTE</div><div class="stat-val" id="stEmote">NOT SELECTED</div></div>
      <div class="stat-box"><div class="stat-lbl">// UIDS</div><div class="stat-val" id="stUids">1</div></div>
    </div>
  </div>

  <!-- FOOTER -->
  <footer class="footer">
    <a href="#" id="ftTelegram" class="foot-link"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/></svg></a>
    <a href="#" id="ftGithub" class="foot-link"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2A10 10 0 002 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z"/></svg></a>
    <a href="#" id="ftDiscord" class="foot-link"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028 13.83 13.83 0 001.226-1.994.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03z"/></svg></a>
    <a href="#" id="ftYoutube" class="foot-link"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg></a>
  </footer>
</div>

<div id="toastBox"></div>
<div id="loader" class="hidden">
  <div class="spin-ring"></div>
  <div class="load-txt">PROCESSING...</div>
</div>

<script>
// ---- CLICK RIPPLE EFFECT ----
document.addEventListener('click',e=>{
  const r=document.createElement('div');
  r.className='ripple';
  r.style.left=e.clientX+'px';
  r.style.top=e.clientY+'px';
  document.body.appendChild(r);
  setTimeout(()=>r.remove(),600);
});

// ---- CLOCK ----
function tick(){document.getElementById('clock').textContent=new Date().toTimeString().slice(0,8);}
setInterval(tick,1000);tick();

// ---- TOAST ----
function toast(msg,type='ok'){
  const box=document.getElementById('toastBox');
  const t=document.createElement('div');
  const ico=type==='ok'?'✓':type==='err'?'✗':'!';
  t.className=`toast t-${type}`;
  t.innerHTML=`<span class="toast-ico">${ico}</span><span class="toast-msg">${msg}</span>`;
  box.appendChild(t);
  setTimeout(()=>t.classList.add('show'),10);
  setTimeout(()=>{t.classList.remove('show');setTimeout(()=>t.remove(),400);},3200);
}

// ---- STATE ----
let selSrv=null,selEmote=null,uidCount=1;
const MAX_UID=5;

// ---- LOADER ----
function showLoad(){document.getElementById('loader').classList.remove('hidden');}
function hideLoad(){document.getElementById('loader').classList.add('hidden');}

// ---- LOAD DATA ----
async function loadData(){
  try{
    const r=await fetch('/api/data');
    const d=await r.json();

    // Servers
    const iSrv=document.getElementById('indianSrv');
    const bSrv=document.getElementById('bangladeshSrv');
    const oSrv=document.getElementById('otherSrv');
    iSrv.innerHTML='<option value="">-- SELECT INDIAN SERVER --</option>';
    bSrv.innerHTML='<option value="">-- SELECT BANGLADESH SERVER --</option>';
    oSrv.innerHTML='<option value="">-- SELECT OTHER SERVER --</option>';
    (d.servers||[]).sort((a,b)=>(a.order||0)-(b.order||0)).forEach(s=>{
      const o=`<option value="${s.baseUrl}">${s.name}</option>`;
      if(s.region==='indian') iSrv.insertAdjacentHTML('beforeend',o);
      else if(s.region==='bangladesh') bSrv.insertAdjacentHTML('beforeend',o);
      else oSrv.insertAdjacentHTML('beforeend',o);
    });

    // Categories
    const cats=(d.categories||[]).sort((a,b)=>(a.order||0)-(b.order||0));
    const tabsEl=document.getElementById('catTabs');
    tabsEl.innerHTML='';
    let firstCat=null;
    cats.forEach((c,i)=>{
      const btn=document.createElement('button');
      btn.className='cat-tab'+(i===0?' active':'');
      btn.dataset.id=c.id;
      btn.textContent=(c.icon||'')+' '+c.name;
      btn.addEventListener('click',()=>{
        document.querySelectorAll('.cat-tab').forEach(x=>x.classList.remove('active'));
        btn.classList.add('active');
        loadEmotes(c.id,d.emotes||[]);
      });
      tabsEl.appendChild(btn);
      if(i===0) firstCat=c.id;
    });
    loadEmotes(firstCat,d.emotes||[]);

    // Footer
    const l=d.settings.footerLinks||{};
    document.getElementById('ftTelegram').href=l.telegram||'#';
    document.getElementById('ftGithub').href=l.github||'#';
    document.getElementById('ftDiscord').href=l.discord||'#';
    document.getElementById('ftYoutube').href=l.youtube||'#';

    // Maintenance
    const m=d.settings.maintenance||{};
    if(m.enabled){
      document.getElementById('maintMsg').textContent=m.message||'';
      document.getElementById('maintOverlay').classList.remove('hidden');
    }
  }catch(e){console.error(e);}
}

function loadEmotes(catId,emotes){
  const grid=document.getElementById('emoteGrid');
  grid.innerHTML='';
  const list=(emotes||[]).filter(e=>e.category===catId);
  if(!list.length){grid.innerHTML='<div class="no-emotes">// NO EMOTES IN THIS CATEGORY</div>';return;}
  list.forEach(em=>{
    const card=document.createElement('div');
    card.className='emote-card';
    card.innerHTML=`<div class="emote-img-wrap"><img src="${em.imageUrl}" alt="${em.emoteId}" loading="lazy" onerror="this.parentNode.innerHTML='<span style=color:var(--muted);font-size:20px>?</span>'"></div><div class="emote-lbl">${em.emoteId}</div>`;
    card.addEventListener('click',()=>handleEmoteClick(em.emoteId,card));
    grid.appendChild(card);
  });
}

async function handleEmoteClick(emoteId,card){
  document.querySelectorAll('.emote-card').forEach(c=>c.classList.remove('selected'));
  card.classList.add('selected');
  selEmote=emoteId;
  document.getElementById('stEmote').textContent=emoteId;

  // Validate before send
  if(!selSrv){toast('// SELECT SERVER FIRST','err');return;}
  const tc=document.getElementById('teamCode').value.trim();
  const u1=document.getElementById('uid1').value.trim();
  if(!tc){toast('// TEAM CODE REQUIRED','err');return;}
  if(!u1||!/^[0-9]{9,12}$/.test(u1)){toast('// VALID UID REQUIRED (9-12 DIGITS)','err');return;}

  const params=new URLSearchParams({server:selSrv,tc,uid1:u1,emote_id:emoteId});
  for(let i=2;i<=MAX_UID;i++){
    const v=document.getElementById(`uid${i}`)?.value.trim();
    if(v&&/^[0-9]{9,12}$/.test(v)) params.append(`uid${i}`,v);
  }

  showLoad();
  try{
    const r=await fetch('/api/send-emote?'+params.toString());
    const res=await r.json();
    hideLoad();
    if(res.success) toast('// '+emoteId+' SENT OK','ok');
    else toast('// ERROR: '+(res.error||'FAILED'),'err');
  }catch(e){hideLoad();toast('// CONNECTION ERROR','err');}
}

// ---- UID MANAGEMENT ----
document.getElementById('addUidBtn').addEventListener('click',()=>{
  if(uidCount>=MAX_UID) return;
  uidCount++;
  document.getElementById('stUids').textContent=uidCount;
  const c=document.getElementById('uidContainer');
  const d=document.createElement('div');
  d.className='field';d.id='uf'+uidCount;
  d.innerHTML=`<label>// TARGET UID ${uidCount} <span style="color:var(--muted);font-size:9px;">(OPTIONAL)</span></label><div class="uid-row"><input type="text" id="uid${uidCount}" placeholder="9–12 digit UID" class="cfg-input" pattern="[0-9]{9,12}"><button class="uid-del" onclick="delUid(${uidCount})" title="Remove">✕</button></div>`;
  c.appendChild(d);
  if(uidCount>=MAX_UID){const b=document.getElementById('addUidBtn');b.disabled=true;b.textContent='MAX UIDS REACHED';}
});

window.delUid=function(n){
  document.getElementById('uf'+n)?.remove();
  uidCount--;
  document.getElementById('stUids').textContent=uidCount;
  const b=document.getElementById('addUidBtn');
  b.disabled=false;b.textContent='+ ADD UID';
};

// ---- SERVER SELECTION ----
function setupServers(){
  const sels=['indianSrv','bangladeshSrv','otherSrv'];
  sels.forEach(id=>{
    document.getElementById(id).addEventListener('change',function(){
      if(!this.value) return;
      selSrv=this.value;
      document.getElementById('stSrv').textContent=this.options[this.selectedIndex].text;
      sels.filter(x=>x!==id).forEach(x=>{document.getElementById(x).value='';});
      toast('// SERVER SELECTED: '+this.options[this.selectedIndex].text,'inf');
    });
  });
}

document.getElementById('logoutBtn').addEventListener('click',()=>{window.location.href='/logout';});

loadData();
setupServers();
</script>
</body>
</html>'''

ADMIN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>XCY LIVE — ADMIN</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
:root{--green:#00ff41;--text:#c8ffc8;--muted:#4a7a4a;--border:rgba(0,255,65,0.18);--card:rgba(0,15,0,0.9);--red:#ff3c5a;}
body{font-family:'Share Tech Mono',monospace;background:#000;color:var(--text);min-height:100vh;}
body::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.1) 2px,rgba(0,0,0,0.1) 4px);pointer-events:none;z-index:9998;}
.grid-bg{position:fixed;inset:0;background-image:linear-gradient(rgba(0,255,65,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,65,0.025) 1px,transparent 1px);background-size:40px 40px;z-index:0;}

/* LOGIN */
.auth-wrap{position:relative;z-index:10;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;}
.auth-box{width:100%;max-width:420px;border:1px solid var(--border);background:var(--card);padding:45px 36px;position:relative;}
.auth-box::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--green),transparent);}
.auth-ico{font-size:42px;text-align:center;display:block;margin-bottom:10px;}
.auth-title{font-family:'Rajdhani',sans-serif;font-size:26px;font-weight:700;letter-spacing:5px;color:var(--green);text-align:center;margin-bottom:4px;}
.auth-sub{font-size:9px;color:var(--muted);text-align:center;letter-spacing:3px;margin-bottom:30px;}
.auth-form{display:flex;flex-direction:column;gap:14px;}
.auth-input{width:100%;padding:13px 16px;background:rgba(0,255,65,0.04);border:1px solid rgba(0,255,65,0.2);color:var(--green);font-family:'Share Tech Mono',monospace;font-size:13px;outline:none;transition:all 0.3s;caret-color:var(--green);}
.auth-input::placeholder{color:var(--muted);}
.auth-input:focus{border-color:var(--green);background:rgba(0,255,65,0.07);}
.auth-btn{padding:14px;background:transparent;border:1px solid var(--green);color:var(--green);font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:4px;cursor:pointer;transition:all 0.3s;position:relative;overflow:hidden;}
.auth-btn::before{content:'';position:absolute;inset:0;background:var(--green);transform:translateX(-100%);transition:transform 0.3s;}
.auth-btn:hover::before{transform:translateX(0);}
.auth-btn:hover{color:#000;}
.auth-btn span{position:relative;z-index:1;}
.err{padding:10px;border:1px solid rgba(255,60,90,0.3);color:var(--red);font-size:11px;text-align:center;}

/* DASHBOARD */
.dash{max-width:820px;margin:0 auto;padding:16px;position:relative;z-index:10;}
.hdr{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border:1px solid var(--border);background:var(--card);margin-bottom:16px;position:relative;}
.hdr::after{content:'';position:absolute;bottom:0;left:0;right:0;height:1px;background:linear-gradient(90deg,var(--green),transparent);}
.hdr h1{font-family:'Rajdhani',sans-serif;font-size:20px;font-weight:700;letter-spacing:5px;color:var(--green);}
.hdr-btn{width:34px;height:34px;border:1px solid rgba(0,255,65,0.2);background:transparent;color:var(--muted);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;}
.hdr-btn:hover{border-color:var(--green);color:var(--green);}
.hdr-btn svg{width:17px;height:17px;}

.panel{border:1px solid var(--border);background:var(--card);padding:18px 20px;margin-bottom:14px;position:relative;}
.panel::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,var(--green),transparent);}
.panel h2{font-family:'Rajdhani',sans-serif;font-size:14px;font-weight:700;letter-spacing:3px;color:var(--green);margin-bottom:16px;}

.adm-form{display:flex;flex-direction:column;gap:12px;}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
@media(max-width:600px){.fg{grid-template-columns:1fr;}}
.adm-input{width:100%;padding:11px 14px;background:rgba(0,255,65,0.04);border:1px solid rgba(0,255,65,0.18);color:var(--green);font-family:'Share Tech Mono',monospace;font-size:12px;outline:none;transition:all 0.3s;}
.adm-input::placeholder{color:var(--muted);}
.adm-input:focus{border-color:var(--green);background:rgba(0,255,65,0.06);}
.adm-btn{width:100%;padding:13px;background:transparent;border:1px solid var(--green);color:var(--green);font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:3px;cursor:pointer;transition:all 0.3s;}
.adm-btn:hover{background:var(--green);color:#000;}
.adm-btn-cancel{width:100%;padding:13px;background:transparent;border:1px solid rgba(0,255,65,0.2);color:var(--muted);font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:3px;cursor:pointer;transition:all 0.3s;}
.adm-btn-cancel:hover{border-color:var(--green);color:var(--green);}

.list{margin-top:16px;display:flex;flex-direction:column;gap:8px;}
.list-item{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border:1px solid rgba(0,255,65,0.1);background:rgba(0,255,65,0.03);transition:all 0.2s;}
.list-item:hover{border-color:rgba(0,255,65,0.3);}
.li-info strong{font-size:13px;color:var(--text);display:block;}
.li-info span{font-size:10px;color:var(--muted);}
.li-actions{display:flex;gap:8px;}
.li-btn{width:32px;height:32px;border:1px solid rgba(0,255,65,0.18);background:transparent;color:var(--muted);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;}
.li-btn:hover{border-color:var(--green);color:var(--green);}
.li-btn svg{width:14px;height:14px;}

.toggle-wrap{display:flex;align-items:center;gap:14px;padding:12px 16px;border:1px solid rgba(0,255,65,0.1);background:rgba(0,255,65,0.02);}
input[type=checkbox]{width:18px;height:18px;accent-color:var(--green);cursor:pointer;}

.loader{position:fixed;inset:0;background:rgba(0,0,0,0.92);display:flex;align-items:center;justify-content:center;z-index:99999;}
.spin{width:44px;height:44px;border:2px solid rgba(0,255,65,0.1);border-top:2px solid var(--green);border-radius:50%;animation:spin 0.7s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}

.hidden{display:none!important;}
</style>
</head>
<body>
<div class="grid-bg"></div>

<!-- LOGIN -->
<div id="loginView" class="auth-wrap">
  <div class="auth-box">
    <span class="auth-ico">🔐</span>
    <div class="auth-title">ADMIN</div>
    <div class="auth-sub">// SECURE ACCESS</div>
    <form id="adminLoginForm" class="auth-form">
      <input type="email" id="adminEmail" value="admin@example.com" placeholder="Email" class="auth-input" required>
      <input type="password" id="adminPassword" placeholder="Password" class="auth-input" required>
      <button type="submit" class="auth-btn"><span>[ AUTHENTICATE ]</span></button>
      <div id="loginErr" class="err hidden">// INVALID CREDENTIALS</div>
    </form>
  </div>
</div>

<!-- DASHBOARD -->
<div id="adminDash" class="dash hidden">
  <header class="hdr">
    <h1>⚡ ADMIN PANEL</h1>
    <button id="adminLogout" class="hdr-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" stroke-width="2"/></svg></button>
  </header>

  <!-- SERVERS -->
  <div class="panel">
    <h2>SERVER MANAGEMENT</h2>
    <form id="serverForm" class="adm-form">
      <input type="hidden" id="editSrvId">
      <div class="fg">
        <input type="text" id="srvName" placeholder="Server Name" required class="adm-input">
        <input type="url" id="srvUrl" placeholder="https://api.example.com" required class="adm-input">
      </div>
      <div class="fg">
        <select id="srvRegion" required class="adm-input">
          <option value="">-- Select Region --</option>
          <option value="indian">🇮🇳 Indian</option>
          <option value="bangladesh">🇧🇩 Bangladesh</option>
          <option value="other">🌍 Other</option>
        </select>
        <input type="number" id="srvOrder" placeholder="Order (1,2,3...)" class="adm-input" min="1">
      </div>
      <button type="submit" class="adm-btn"><span id="srvBtnTxt">[ ADD SERVER ]</span></button>
      <button type="button" id="cancelSrv" class="adm-btn-cancel hidden">[ CANCEL ]</button>
    </form>
    <div id="srvList" class="list"></div>
  </div>

  <!-- CATEGORIES -->
  <div class="panel">
    <h2>CATEGORY MANAGEMENT</h2>
    <form id="catForm" class="adm-form">
      <input type="hidden" id="editCatId">
      <div class="fg">
        <input type="text" id="catName" placeholder="Category Name (e.g. HOT)" required class="adm-input">
        <input type="text" id="catIcon" placeholder="Icon (e.g. 🔥)" class="adm-input">
      </div>
      <input type="number" id="catOrder" placeholder="Order (1,2,3...)" class="adm-input" min="1">
      <button type="submit" class="adm-btn"><span id="catBtnTxt">[ ADD CATEGORY ]</span></button>
      <button type="button" id="cancelCat" class="adm-btn-cancel hidden">[ CANCEL ]</button>
    </form>
    <div id="catList" class="list"></div>
  </div>

  <!-- EMOTES -->
  <div class="panel">
    <h2>EMOTE MANAGEMENT</h2>
    <form id="emoteForm" class="adm-form">
      <input type="hidden" id="editEmoteId">
      <div class="fg">
        <input type="url" id="emoteUrl" placeholder="Image URL" required class="adm-input">
        <select id="emotecat" required class="adm-input"><option value="">-- Select Category --</option></select>
      </div>
      <div id="emotePreview"></div>
      <button type="submit" class="adm-btn"><span id="emoteBtnTxt">[ ADD EMOTE ]</span></button>
      <button type="button" id="cancelEmote" class="adm-btn-cancel hidden">[ CANCEL ]</button>
    </form>
    <div id="emoteList" class="list"></div>
  </div>

  <!-- FOOTER LINKS -->
  <div class="panel">
    <h2>FOOTER LINKS</h2>
    <form id="linksForm" class="adm-form">
      <input type="url" id="tgUrl" placeholder="Telegram URL" class="adm-input">
      <input type="url" id="ghUrl" placeholder="GitHub URL" class="adm-input">
      <input type="url" id="dcUrl" placeholder="Discord URL" class="adm-input">
      <input type="url" id="ytUrl" placeholder="YouTube URL" class="adm-input">
      <button type="submit" class="adm-btn"><span>[ UPDATE LINKS ]</span></button>
    </form>
  </div>

  <!-- MAINTENANCE -->
  <div class="panel">
    <h2>MAINTENANCE MODE</h2>
    <form id="maintForm" class="adm-form">
      <div class="toggle-wrap">
        <input type="checkbox" id="maintToggle">
        <label for="maintToggle" style="font-size:12px;letter-spacing:2px;cursor:pointer;">ENABLE MAINTENANCE MODE</label>
      </div>
      <textarea id="maintMsg" placeholder="Maintenance message..." rows="3" class="adm-input"></textarea>
      <button type="submit" class="adm-btn"><span>[ SAVE SETTINGS ]</span></button>
    </form>
  </div>

  <!-- PASSWORD -->
  <div class="panel">
    <h2>LOGIN PASSWORD</h2>
    <form id="pwForm" class="adm-form">
      <input type="password" id="newPw" placeholder="New password" required class="adm-input">
      <button type="submit" class="adm-btn"><span>[ UPDATE PASSWORD ]</span></button>
    </form>
  </div>
</div>

<div id="adminLoader" class="loader hidden"><div class="spin"></div></div>

<script>
const showLoad=()=>document.getElementById('adminLoader').classList.remove('hidden');
const hideLoad=()=>document.getElementById('adminLoader').classList.add('hidden');

document.getElementById('adminLoginForm').addEventListener('submit',async e=>{
  e.preventDefault();
  showLoad();
  const r=await fetch('/api/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('adminEmail').value,password:document.getElementById('adminPassword').value})});
  const d=await r.json();
  hideLoad();
  if(d.success){document.getElementById('loginView').classList.add('hidden');document.getElementById('adminDash').classList.remove('hidden');loadAdminData();}
  else{document.getElementById('loginErr').classList.remove('hidden');setTimeout(()=>document.getElementById('loginErr').classList.add('hidden'),3000);}
});

document.getElementById('adminLogout').addEventListener('click',()=>{
  document.getElementById('loginView').classList.remove('hidden');
  document.getElementById('adminDash').classList.add('hidden');
  document.getElementById('adminPassword').value='';
});

async function loadAdminData(){
  const r=await fetch('/api/data');
  const d=await r.json();
  renderServers(d.servers||[]);
  renderCats(d.categories||[]);
  renderCatDropdown(d.categories||[]);
  renderEmotes(d.emotes||[]);
  const s=d.settings||{};
  document.getElementById('tgUrl').value=s.footerLinks?.telegram||'';
  document.getElementById('ghUrl').value=s.footerLinks?.github||'';
  document.getElementById('dcUrl').value=s.footerLinks?.discord||'';
  document.getElementById('ytUrl').value=s.footerLinks?.youtube||'';
  document.getElementById('maintToggle').checked=s.maintenance?.enabled||false;
  document.getElementById('maintMsg').value=s.maintenance?.message||'';
}

function renderServers(list){
  const el=document.getElementById('srvList');
  el.innerHTML=list.length?'':'<p style="color:var(--muted);font-size:11px;text-align:center">// NO SERVERS YET</p>';
  list.sort((a,b)=>(a.order||0)-(b.order||0)).forEach(s=>{
    const d=document.createElement('div');d.className='list-item';
    d.innerHTML=`<div class="li-info"><strong>${s.name}</strong><span>${s.baseUrl} — ${s.region} #${s.order||0}</span></div><div class="li-actions"><button class="li-btn" onclick="editSrv('${s.id}','${s.name}','${s.baseUrl}','${s.region}',${s.order||0})"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke-width="2"/></svg></button><button class="li-btn" onclick="delSrv('${s.id}')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M18 6L6 18M6 6l12 12" stroke-width="2"/></svg></button></div>`;
    el.appendChild(d);
  });
}

document.getElementById('serverForm').addEventListener('submit',async e=>{
  e.preventDefault();
  const id=document.getElementById('editSrvId').value;
  const body={id:id||undefined,name:document.getElementById('srvName').value,baseUrl:document.getElementById('srvUrl').value,region:document.getElementById('srvRegion').value,order:parseInt(document.getElementById('srvOrder').value)||0};
  showLoad();
  const r=await fetch(id?`/api/servers?id=${id}`:'/api/servers',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();hideLoad();
  if(d.success){resetSrvForm();loadAdminData();alert('✅ Server saved!');}
  else alert('❌ '+d.error);
});
window.editSrv=(id,name,url,region,order)=>{document.getElementById('editSrvId').value=id;document.getElementById('srvName').value=name;document.getElementById('srvUrl').value=url;document.getElementById('srvRegion').value=region;document.getElementById('srvOrder').value=order;document.getElementById('srvBtnTxt').textContent='[ UPDATE SERVER ]';document.getElementById('cancelSrv').classList.remove('hidden');};
window.delSrv=async id=>{if(!confirm('Delete server?'))return;showLoad();await fetch(`/api/servers?id=${id}`,{method:'DELETE'});hideLoad();loadAdminData();};
document.getElementById('cancelSrv').addEventListener('click',resetSrvForm);
function resetSrvForm(){document.getElementById('serverForm').reset();document.getElementById('editSrvId').value='';document.getElementById('srvBtnTxt').textContent='[ ADD SERVER ]';document.getElementById('cancelSrv').classList.add('hidden');}

function renderCats(list){
  const el=document.getElementById('catList');
  el.innerHTML=list.length?'':'<p style="color:var(--muted);font-size:11px;text-align:center">// NO CATEGORIES YET</p>';
  list.sort((a,b)=>(a.order||0)-(b.order||0)).forEach(c=>{
    const d=document.createElement('div');d.className='list-item';
    d.innerHTML=`<div class="li-info"><strong>${c.icon||''} ${c.name}</strong><span>Order: ${c.order||0}</span></div><div class="li-actions"><button class="li-btn" onclick="editCat('${c.id}','${c.name}','${c.icon||''}',${c.order||0})"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke-width="2"/></svg></button><button class="li-btn" onclick="delCat('${c.id}')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M18 6L6 18M6 6l12 12" stroke-width="2"/></svg></button></div>`;
    el.appendChild(d);
  });
}
function renderCatDropdown(list){
  const sel=document.getElementById('emotecat');
  sel.innerHTML='<option value="">-- Select Category --</option>';
  list.sort((a,b)=>(a.order||0)-(b.order||0)).forEach(c=>{
    const o=document.createElement('option');o.value=c.id;o.textContent=(c.icon||'')+' '+c.name;sel.appendChild(o);
  });
}
document.getElementById('catForm').addEventListener('submit',async e=>{
  e.preventDefault();
  const id=document.getElementById('editCatId').value;
  const name=document.getElementById('catName').value;
  const body={id:id||name.toUpperCase().replace(/ /g,'_'),name,icon:document.getElementById('catIcon').value,order:parseInt(document.getElementById('catOrder').value)||0};
  showLoad();
  const r=await fetch(id?`/api/categories?id=${id}`:'/api/categories',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();hideLoad();
  if(d.success){resetCatForm();loadAdminData();alert('✅ Category saved!');}
});
window.editCat=(id,name,icon,order)=>{document.getElementById('editCatId').value=id;document.getElementById('catName').value=name;document.getElementById('catIcon').value=icon;document.getElementById('catOrder').value=order;document.getElementById('catBtnTxt').textContent='[ UPDATE CATEGORY ]';document.getElementById('cancelCat').classList.remove('hidden');};
window.delCat=async id=>{if(!confirm('Delete category?'))return;showLoad();await fetch(`/api/categories?id=${id}`,{method:'DELETE'});hideLoad();loadAdminData();};
document.getElementById('cancelCat').addEventListener('click',resetCatForm);
function resetCatForm(){document.getElementById('catForm').reset();document.getElementById('editCatId').value='';document.getElementById('catBtnTxt').textContent='[ ADD CATEGORY ]';document.getElementById('cancelCat').classList.add('hidden');}

function renderEmotes(list){
  const el=document.getElementById('emoteList');
  el.innerHTML=list.length?'':'<p style="color:var(--muted);font-size:11px;text-align:center">// NO EMOTES YET</p>';
  list.forEach(em=>{
    const d=document.createElement('div');d.className='list-item';
    d.innerHTML=`<div class="li-info" style="display:flex;align-items:center;gap:10px;"><img src="${em.imageUrl}" style="width:36px;height:36px;object-fit:contain;border:1px solid var(--border);"><div><strong>${em.emoteId}</strong><span>Category: ${em.category}</span></div></div><div class="li-actions"><button class="li-btn" onclick="editEmote('${em.id}','${em.imageUrl}','${em.category}')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke-width="2"/></svg></button><button class="li-btn" onclick="delEmote('${em.id}')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M18 6L6 18M6 6l12 12" stroke-width="2"/></svg></button></div>`;
    el.appendChild(d);
  });
}
document.getElementById('emoteUrl').addEventListener('input',e=>{
  const p=document.getElementById('emotePreview');
  p.innerHTML=e.target.value?`<img src="${e.target.value}" style="max-width:80px;max-height:80px;border:1px solid var(--border);margin-top:4px;">`:''
});
document.getElementById('emoteForm').addEventListener('submit',async e=>{
  e.preventDefault();
  const id=document.getElementById('editEmoteId').value;
  const imageUrl=document.getElementById('emoteUrl').value;
  const body={id:id||undefined,imageUrl,category:document.getElementById('emotecat').value,emoteId:imageUrl.split('/').pop().split('.')[0]};
  showLoad();
  const r=await fetch(id?`/api/emotes?id=${id}`:'/api/emotes',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();hideLoad();
  if(d.success){resetEmoteForm();loadAdminData();alert('✅ Emote saved!');}
});
window.editEmote=(id,url,cat)=>{document.getElementById('editEmoteId').value=id;document.getElementById('emoteUrl').value=url;document.getElementById('emotecat').value=cat;document.getElementById('emoteBtnTxt').textContent='[ UPDATE EMOTE ]';document.getElementById('cancelEmote').classList.remove('hidden');document.getElementById('emotePreview').innerHTML=`<img src="${url}" style="max-width:80px;max-height:80px;border:1px solid var(--border);margin-top:4px;">`};
window.delEmote=async id=>{if(!confirm('Delete emote?'))return;showLoad();await fetch(`/api/emotes?id=${id}`,{method:'DELETE'});hideLoad();loadAdminData();};
document.getElementById('cancelEmote').addEventListener('click',resetEmoteForm);
function resetEmoteForm(){document.getElementById('emoteForm').reset();document.getElementById('editEmoteId').value='';document.getElementById('emoteBtnTxt').textContent='[ ADD EMOTE ]';document.getElementById('cancelEmote').classList.add('hidden');document.getElementById('emotePreview').innerHTML='';}

document.getElementById('linksForm').addEventListener('submit',async e=>{
  e.preventDefault();showLoad();
  const r=await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'footerLinks',telegram:document.getElementById('tgUrl').value,github:document.getElementById('ghUrl').value,discord:document.getElementById('dcUrl').value,youtube:document.getElementById('ytUrl').value})});
  const d=await r.json();hideLoad();if(d.success)alert('✅ Links updated!');
});

document.getElementById('maintForm').addEventListener('submit',async e=>{
  e.preventDefault();showLoad();
  const r=await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'maintenance',enabled:document.getElementById('maintToggle').checked,message:document.getElementById('maintMsg').value})});
  const d=await r.json();hideLoad();if(d.success)alert('✅ Maintenance settings saved!');
});

document.getElementById('pwForm').addEventListener('submit',async e=>{
  e.preventDefault();showLoad();
  const r=await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'password',password:document.getElementById('newPw').value})});
  const d=await r.json();hideLoad();if(d.success){alert('✅ Password updated!');document.getElementById('newPw').value='';}
});
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
    return render_template_string(DASHBOARD_HTML)

@app.route('/admin')
def admin():
    return render_template_string(ADMIN_HTML)

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
            server = {
                'id': str(int(time.time() * 1000)),
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

load_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)