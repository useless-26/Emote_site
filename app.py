from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, send_from_directory
import json
import os
import hashlib
import time
import urllib.parse
import requests

app = Flask(__name__)
app.secret_key = 'emote-bot-secret-key-2024'

# In-memory database
DATABASE = {
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

# Load database from file
def load_database():
    global DATABASE
    try:
        if os.path.exists('database.json'):
            with open('database.json', 'r') as f:
                DATABASE = json.load(f)
    except:
        pass

# Save database to file
def save_database():
    try:
        with open('database.json', 'w') as f:
            json.dump(DATABASE, f, indent=2)
    except:
        pass

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Check if user is logged in
def require_login():
    if 'logged_in' not in session:
        return False
    return True

# ========== HTML TEMPLATES ==========

INDEX_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XCY LIVE  - Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --bg-dark: #0a0a0a;
            --bg-darker: #050505;
            --card-bg: rgba(20, 20, 20, 0.8);
            --card-border: rgba(0, 150, 255, 0.3);
            --primary-blue: #0096FF;
            --primary-blue-glow: rgba(0, 150, 255, 0.4);
            --text-white: #ffffff;
            --text-gray: #a0a0a0;
            --success-green: #00ff88;
            --danger-red: #ff0844;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #001a33 0%, #000000 50%, #000d1a 100%);
            color: var(--text-white);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .particles-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: 0;
            pointer-events: none;
        }
        
        .particle {
            position: absolute;
            width: 3px;
            height: 3px;
            background: var(--primary-blue);
            border-radius: 50%;
            opacity: 0;
            animation: float 15s infinite ease-in-out;
        }
        
        .particle:nth-child(1) { left: 20%; animation-delay: 0s; animation-duration: 14s; }
        .particle:nth-child(2) { left: 50%; animation-delay: 3s; animation-duration: 16s; }
        .particle:nth-child(3) { left: 80%; animation-delay: 6s; animation-duration: 15s; }
        
        @keyframes float {
            0% {
                transform: translateY(100vh) scale(0);
                opacity: 0;
            }
            10% { opacity: 0.5; }
            50% { opacity: 0.6; transform: translateY(50vh) scale(1); }
            90% { opacity: 0.2; }
            100% {
                transform: translateY(-10vh) scale(0);
                opacity: 0;
            }
        }
        
        .login-body {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: radial-gradient(circle at center, #001a33 0%, #000000 100%);
            position: relative;
        }
        
        .login-container {
            width: 100%;
            max-width: 480px;
            padding: 20px;
            position: relative;
            z-index: 1;
        }
        
        .login-box {
            background: var(--card-bg);
            border: 2px solid var(--card-border);
            border-radius: 20px;
            padding: 50px 40px;
            backdrop-filter: blur(20px);
            box-shadow: 0 0 30px var(--primary-blue-glow);
            position: relative;
            overflow: hidden;
        }
        
        .brand-section {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .lightning-icon-wrapper {
            position: relative;
            display: inline-block;
            margin-bottom: 15px;
        }
        
        .lightning-icon {
            font-size: 72px;
        }
        
        .brand-name {
            font-size: 36px;
            font-weight: 800;
            letter-spacing: 3px;
            color: var(--primary-blue);
            text-shadow: 0 0 15px var(--primary-blue-glow);
            margin-bottom: 8px;
        }
        
        .brand-tagline {
            font-size: 14px;
            color: var(--text-gray);
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .login-form {
            display: flex;
            flex-direction: column;
            gap: 25px;
        }
        
        .input-container {
            position: relative;
        }
        
        .login-input {
            width: 100%;
            padding: 18px 50px 18px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: var(--text-white);
            font-size: 15px;
            transition: all 0.3s ease;
        }
        
        .login-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 15px var(--primary-blue-glow);
        }
        
        .lock-icon {
            position: absolute;
            right: 18px;
            top: 50%;
            transform: translateY(-50%);
            width: 22px;
            height: 22px;
            color: var(--text-gray);
            z-index: 3;
            transition: color 0.3s ease;
        }
        
        .login-input:focus ~ .lock-icon {
            color: var(--primary-blue);
        }
        
        .login-btn {
            padding: 18px;
            background: var(--primary-blue);
            border: none;
            border-radius: 12px;
            color: var(--text-white);
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .login-btn:hover {
            background: #008ae6;
            box-shadow: 0 0 25px var(--primary-blue-glow);
            transform: translateY(-2px);
        }
        
        .error-message {
            padding: 12px;
            background: rgba(255, 0, 0, 0.1);
            border: 1px solid rgba(255, 0, 0, 0.3);
            border-radius: 8px;
            color: #ff4444;
            text-align: center;
            font-size: 14px;
        }
        
        .hidden {
            display: none !important;
        }
        
        .social-footer {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 35px;
        }
        
        .social-link {
            width: 45px;
            height: 45px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-gray);
            transition: all 0.3s ease;
            text-decoration: none;
        }
        
        .social-link:hover {
            background: rgba(0, 150, 255, 0.2);
            border-color: var(--primary-blue);
            color: var(--text-white);
            transform: translateY(-3px);
        }
        
        .social-link svg {
            width: 22px;
            height: 22px;
        }
        
        .shake {
            animation: shake 0.3s ease;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-10px); }
            75% { transform: translateX(10px); }
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body class="login-body">
    <div class="particles-container">
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
    </div>

    <div class="login-container">
        <div class="login-box">
            <div class="brand-section">
                <div class="lightning-icon-wrapper">
                    <div class="lightning-icon">⚡</div>
                </div>
                <h1 class="brand-name">XCY LIVE </h1>
                <p class="brand-tagline">XCY LIVE  Control Panel</p>
            </div>

            <form id="loginForm" class="login-form">
                <div class="input-container">
                    <input 
                        type="password" 
                        id="loginPassword" 
                        placeholder="Enter Access Password" 
                        required 
                        autocomplete="off"
                        class="login-input"
                    >
                    <svg class="lock-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke-width="2"/>
                        <path d="M7 11V7a5 5 0 0110 0v4" stroke-width="2"/>
                    </svg>
                </div>

                <button type="submit" class="login-btn">
                    <span class="btn-text">Access Dashboard</span>
                    <span class="btn-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M5 12h14M12 5l7 7-7 7" stroke-width="2"/>
                        </svg>
                    </span>
                </button>

                <div id="loginError" class="error-message hidden"></div>
            </form>

            <div class="social-footer">
                <a href="#" id="telegram" class="social-link">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
                    </svg>
                </a>
                <a href="#" id="github" class="social-link">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2A10 10 0 002 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z"/>
                    </svg>
                </a>
                <a href="#" id="discord" class="social-link">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028 13.83 13.83 0 001.226-1.994.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03z"/>
                    </svg>
                </a>
                <a href="#" id="youtube" class="social-link">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                    </svg>
                </a>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const password = document.getElementById('loginPassword').value;
            const errorMsg = document.getElementById('loginError');
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: 'password=' + encodeURIComponent(password)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    window.location.href = '/dashboard';
                } else {
                    document.getElementById('loginPassword').classList.add('shake');
                    errorMsg.textContent = '❌ Invalid Password';
                    errorMsg.classList.remove('hidden');
                    
                    setTimeout(() => {
                        document.getElementById('loginPassword').classList.remove('shake');
                        errorMsg.classList.add('hidden');
                    }, 2000);
                }
            } catch (error) {
                errorMsg.textContent = '❌ Connection Error';
                errorMsg.classList.remove('hidden');
            }
        });
        
        // Load social links
        async function loadSocialLinks() {
            try {
                const response = await fetch('/api/settings');
                const data = await response.json();
                const links = data.footerLinks || {};
                
                document.getElementById('telegram').href = links.telegram || '#';
                document.getElementById('github').href = links.github || '#';
                document.getElementById('discord').href = links.discord || '#';
                document.getElementById('youtube').href = links.youtube || '#';
            } catch (error) {
                console.log('Social links not configured yet');
            }
        }
        
        loadSocialLinks();
    </script>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XCY LIVE  - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --bg-dark: #0a0a0a;
            --bg-darker: #050505;
            --card-bg: rgba(20, 20, 20, 0.8);
            --card-border: rgba(0, 150, 255, 0.3);
            --primary-blue: #0096FF;
            --primary-blue-glow: rgba(0, 150, 255, 0.4);
            --text-white: #ffffff;
            --text-gray: #a0a0a0;
            --success-green: #00ff88;
            --danger-red: #ff0844;
            --indian-orange: #FF9933;
            --bangladesh-green: #006A4E;
            --other-purple: #8A2BE2;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #001a33 0%, #000000 50%, #000d1a 100%);
            color: var(--text-white);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .dashboard-bg-particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: 0;
            pointer-events: none;
        }
        
        .bg-particle {
            position: absolute;
            background: radial-gradient(circle, rgba(0, 150, 255, 0.1) 0%, transparent 70%);
            border-radius: 50%;
            animation: drift 25s infinite ease-in-out;
        }
        
        .bg-particle:nth-child(1) {
            width: 400px;
            height: 400px;
            top: 20%;
            left: -10%;
        }
        
        @keyframes drift {
            0%, 100% {
                transform: translate(0, 0);
                opacity: 0.2;
            }
            50% {
                transform: translate(30px, -20px);
                opacity: 0.3;
            }
        }
        
        .dashboard-body {
            background: radial-gradient(circle at top, #001a33 0%, #000000 100%);
            position: relative;
        }
        
        .dashboard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }
        
        .dashboard-header {
            background: var(--card-bg);
            border: 2px solid var(--card-border);
            border-radius: 16px;
            padding: 20px 25px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            backdrop-filter: blur(20px);
        }
        
        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .header-brand .lightning-icon {
            font-size: 32px;
        }
        
        .header-brand h1 {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: 2px;
            color: var(--primary-blue);
            text-shadow: 0 0 10px var(--primary-blue-glow);
        }
        
        .icon-button {
            width: 45px;
            height: 45px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            color: var(--text-white);
        }
        
        .icon-button:hover {
            background: rgba(0, 150, 255, 0.2);
            border-color: var(--primary-blue);
            transform: scale(1.05);
        }
        
        .icon-button svg {
            width: 22px;
            height: 22px;
        }
        
        .panel-section {
            background: var(--card-bg);
            border: 2px solid var(--card-border);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
            backdrop-filter: blur(20px);
        }
        
        .section-title {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .title-icon-wrapper {
            width: 34px;
            height: 34px;
            background: rgba(0, 150, 255, 0.1);
            border: 1px solid var(--primary-blue);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .title-icon {
            width: 20px;
            height: 20px;
            color: var(--primary-blue);
        }
        
        .section-title h2 {
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: var(--primary-blue);
        }
        
        .server-select-container {
            position: relative;
        }
        
        .server-select {
            width: 100%;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            color: var(--text-white);
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 15px center;
            background-size: 20px;
            padding-right: 45px;
        }
        
        .server-select:focus {
            outline: none;
            border-color: var(--primary-blue);
            background-color: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 15px var(--primary-blue-glow);
        }
        
        .input-section {
            background: linear-gradient(135deg, rgba(0, 150, 255, 0.05) 0%, rgba(20, 20, 20, 0.95) 100%);
        }
        
        .input-group-box {
            margin-bottom: 15px;
        }
        
        .input-group-box label {
            display: block;
            font-size: 12px;
            color: var(--text-gray);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .required {
            color: var(--primary-blue);
        }
        
        .config-input {
            width: 100%;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: var(--text-white);
            font-size: 15px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .config-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 12px var(--primary-blue-glow);
        }
        
        .add-uid-btn {
            width: 100%;
            padding: 15px;
            background: rgba(0, 255, 136, 0.1);
            border: 2px solid rgba(0, 255, 136, 0.3);
            border-radius: 12px;
            color: var(--success-green);
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .add-uid-btn:hover:not(:disabled) {
            background: rgba(0, 255, 136, 0.2);
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
        }
        
        .add-uid-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .emote-section {
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.03) 0%, rgba(20, 20, 20, 0.95) 100%);
            border: 2px solid rgba(0, 255, 136, 0.2);
        }
        
        .category-tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .category-tab {
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            color: var(--text-white);
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        
        .category-tab:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
        }
        
        .category-tab.active {
            background: var(--primary-blue);
            border-color: var(--primary-blue);
            box-shadow: 0 0 20px var(--primary-blue-glow);
        }
        
        .emote-grid-wrapper {
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 12px;
        }
        
        .emote-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            max-height: 400px;
            overflow-y: auto;
            padding: 5px;
        }
        
        .emote-card {
            aspect-ratio: 1 / 1;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .emote-card:hover {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.06) 100%);
            border-color: rgba(0, 150, 255, 0.6);
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0, 150, 255, 0.3);
        }
        
        .emote-card.selected {
            border-color: var(--success-green);
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.2) 0%, rgba(0, 255, 136, 0.1) 100%);
            box-shadow: 0 0 25px rgba(0, 255, 136, 0.5);
            transform: scale(1.02);
        }
        
        .emote-card.selected::after {
            content: '✓';
            position: absolute;
            top: -6px;
            right: -6px;
            width: 22px;
            height: 22px;
            background: var(--success-green);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: bold;
            color: var(--bg-dark);
            box-shadow: 0 3px 10px rgba(0, 255, 136, 0.5);
            border: 2px solid var(--bg-dark);
            z-index: 10;
        }
        
        .emote-image-wrapper {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.08) 0%, rgba(0, 0, 0, 0.4) 100%);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .emote-card img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 10px;
            transition: transform 0.3s ease;
        }
        
        .emote-card:hover img {
            transform: scale(1.1);
        }
        
        .emote-name {
            font-size: 10px;
            color: var(--text-gray);
            font-weight: 700;
            margin: 6px 0 4px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: color 0.3s ease;
            padding: 0 4px;
        }
        
        .emote-card:hover .emote-name {
            color: var(--text-white);
        }
        
        .emote-card.selected .emote-name {
            color: var(--success-green);
        }
        
        .no-emotes {
            text-align: center;
            color: var(--text-gray);
            padding: 40px 20px;
            font-size: 14px;
            grid-column: 1 / -1;
        }
        
        .stats-section {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(20, 20, 20, 0.95) 100%);
        }
        
        .stats-grid {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 15px 18px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        .stat-item:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(0, 150, 255, 0.3);
        }
        
        .stat-icon {
            font-size: 20px;
            width: 35px;
            height: 35px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(0, 150, 255, 0.1);
            border-radius: 8px;
            flex-shrink: 0;
        }
        
        .stat-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex: 1;
        }
        
        .stat-label {
            font-size: 13px;
            color: var(--text-gray);
            font-weight: 500;
        }
        
        .stat-value {
            font-size: 14px;
            font-weight: 700;
            color: var(--primary-blue);
        }
        
        .toast-container {
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 99999;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .toast {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px 22px;
            border-radius: 12px;
            min-width: 300px;
            max-width: 400px;
            opacity: 0;
            transform: translateX(400px);
            transition: all 0.4s ease;
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(15px);
            border: 1.5px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }
        
        .toast.show {
            opacity: 1;
            transform: translateX(0);
        }
        
        .toast-success {
            background: rgba(0, 255, 136, 0.15);
            border-color: rgba(0, 255, 136, 0.4);
        }
        
        .toast-error {
            background: rgba(255, 8, 68, 0.15);
            border-color: rgba(255, 8, 68, 0.4);
        }
        
        .toast-info {
            background: rgba(59, 130, 246, 0.15);
            border-color: rgba(59, 130, 246, 0.4);
        }
        
        .toast-icon {
            font-size: 24px;
            font-weight: bold;
            color: var(--text-white);
            flex-shrink: 0;
        }
        
        .toast-message {
            color: var(--text-white);
            font-size: 14px;
            font-weight: 600;
            flex: 1;
        }
        
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(5px);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        }
        
        .spinner-container {
            position: relative;
            width: 70px;
            height: 70px;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: var(--primary-blue);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        
        @keyframes spin {
            to { transform: translate(-50%, -50%) rotate(360deg); }
        }
        
        .maintenance-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            backdrop-filter: blur(10px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }
        
        .maintenance-box {
            background: var(--card-bg);
            border: 2px solid var(--card-border);
            border-radius: 18px;
            padding: 40px 35px;
            max-width: 450px;
            text-align: center;
        }
        
        .maintenance-icon {
            font-size: 56px;
            margin-bottom: 18px;
        }
        
        .maintenance-box h2 {
            font-size: 24px;
            margin-bottom: 12px;
            color: var(--primary-blue);
        }
        
        .maintenance-box p {
            color: var(--text-gray);
            margin-bottom: 25px;
            line-height: 1.6;
            font-size: 14px;
        }
        
        .maintenance-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 25px;
            background: var(--primary-blue);
            border-radius: 8px;
            color: var(--text-white);
            font-weight: 700;
            text-decoration: none;
            transition: all 0.3s ease;
            font-size: 14px;
        }
        
        .dashboard-footer {
            margin-top: 25px;
            padding: 20px;
            text-align: center;
        }
        
        .footer-social {
            display: flex;
            justify-content: center;
            gap: 12px;
        }
        
        .footer-link {
            width: 40px;
            height: 40px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-gray);
            transition: all 0.3s ease;
            text-decoration: none;
        }
        
        .footer-link:hover {
            background: rgba(0, 150, 255, 0.2);
            border-color: var(--primary-blue);
            color: var(--text-white);
            transform: translateY(-2px);
        }
        
        .hidden {
            display: none !important;
        }
        
        @media (max-width: 768px) {
            .dashboard-container {
                padding: 15px;
            }
            
            .panel-section {
                padding: 20px;
            }
            
            .emote-grid {
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
            }
            
            .dashboard-header {
                flex-direction: column;
                gap: 15px;
            }
        }
        
        @media (max-width: 480px) {
            .emote-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
            }
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body class="dashboard-body">
    
    <div class="dashboard-bg-particles">
        <div class="bg-particle"></div>
    </div>

    <div id="maintenanceOverlay" class="maintenance-overlay hidden">
        <div class="maintenance-box">
            <div class="maintenance-icon">🛠️</div>
            <h2>Under Maintenance</h2>
            <p id="maintenanceMsg">System is being upgraded. Please check back later.</p>
            <a href="#" id="maintenanceTG" class="maintenance-btn">
                <span>Join Telegram</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M5 12h14M12 5l7 7-7 7" stroke-width="2"/>
                </svg>
            </a>
        </div>
    </div>

    <div class="dashboard-container">
        <!-- Header -->
        <header class="dashboard-header">
            <div class="header-brand">
                <div class="lightning-icon">⚡</div>
                <h1>XCY LIVE </h1>
            </div>
            <button id="logoutBtn" class="icon-button">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" stroke-width="2"/>
                </svg>
            </button>
        </header>

        <!-- 🇮🇳 INDIAN SERVERS -->
        <section class="panel-section">
            <div class="section-title">
                <div class="title-icon-wrapper">
                    <span style="font-size: 20px;">🇮🇳</span>
                </div>
                <h2>INDIAN SERVERS</h2>
            </div>

            <div class="server-select-container">
                <select id="indianServerSelect" class="server-select">
                    <option value="">Select Indian Server...</option>
                </select>
            </div>
        </section>

        <!-- 🇧🇩 BANGLADESH SERVERS -->
        <section class="panel-section">
            <div class="section-title">
                <div class="title-icon-wrapper">
                    <span style="font-size: 20px;">🇧🇩</span>
                </div>
                <h2>BANGLADESH SERVERS</h2>
            </div>

            <div class="server-select-container">
                <select id="bangladeshServerSelect" class="server-select">
                    <option value="">Select Bangladesh Server...</option>
                </select>
            </div>
        </section>

        <!-- 🌍 OTHER SERVERS -->
        <section class="panel-section">
            <div class="section-title">
                <div class="title-icon-wrapper">
                    <span style="font-size: 20px;">🌍</span>
                </div>
                <h2>OTHER SERVERS</h2>
            </div>

            <div class="server-select-container">
                <select id="otherServerSelect" class="server-select">
                    <option value="">Select Other Server...</option>
                </select>
            </div>
        </section>

        <!-- CONFIGURATION -->
        <section class="panel-section input-section">
            <div class="section-title">
                <div class="title-icon-wrapper">
                    <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" stroke-width="2"/>
                    </svg>
                </div>
                <h2>CONFIGURATION</h2>
            </div>

            <div class="input-group-box">
                <label>TEAM CODE <span class="required">*</span></label>
                <input type="text" id="teamCode" placeholder="Enter team code" class="config-input" required>
            </div>

            <div class="input-group-box">
                <label>TARGET UID 1 <span class="required">*</span></label>
                <input type="text" id="uid1" placeholder="Enter UID (9-12 digits)" class="config-input uid-input" pattern="[0-9]{9,12}" required>
            </div>

            <div id="uidContainer"></div>

            <button class="add-uid-btn" id="addUidBtn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M12 5v14M5 12h14" stroke-width="2"/>
                </svg>
                ADD UID
            </button>
        </section>

        <!-- EMOTE SELECTION -->
        <section class="panel-section emote-section">
            <div class="section-title">
                <div class="title-icon-wrapper">
                    <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <circle cx="12" cy="12" r="10" stroke-width="2"/>
                        <path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01" stroke-width="2"/>
                    </svg>
                </div>
                <h2>EMOTE SELECTION</h2>
            </div>

            <!-- Category Tabs -->
            <div class="category-tabs" id="categoryTabs"></div>

            <!-- Emote Grid -->
            <div class="emote-grid-wrapper">
                <div class="emote-grid" id="emoteGrid"></div>
            </div>
        </section>

        <!-- STATUS -->
        <section class="panel-section stats-section">
            <div class="section-title">
                <div class="title-icon-wrapper">
                    <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2 2V5a2 2 0 012-2h11" stroke-width="2"/>
                    </svg>
                </div>
                <h2>STATUS</h2>
            </div>

            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-icon">🖥️</div>
                    <div class="stat-content">
                        <span class="stat-label">Server:</span>
                        <span class="stat-value" id="statServer">Not Selected</span>
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-icon">👥</div>
                    <div class="stat-content">
                        <span class="stat-label">UIDs:</span>
                        <span class="stat-value" id="statUids">1</span>
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-icon">😊</div>
                    <div class="stat-content">
                        <span class="stat-label">Emote:</span>
                        <span class="stat-value" id="statEmote">Not Selected</span>
                    </div>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="dashboard-footer">
            <div class="footer-social">
                <a href="#" id="footerTelegram" class="footer-link">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
                    </svg>
                </a>
                <a href="#" id="footerGithub" class="footer-link">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2A10 10 0 002 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z"/>
                    </svg>
                </a>
                <a href="#" id="footerDiscord" class="footer-link">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028 13.83 13.83 0 001.226-1.994.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03z"/>
                    </svg>
                </a>
                <a href="#" id="footerYoutube" class="footer-link">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                    </svg>
                </a>
            </div>
        </footer>
    </div>

    <!-- Toast Notification Container -->
    <div id="toastContainer" class="toast-container"></div>

    <!-- Loading Spinner -->
    <div id="loadingSpinner" class="loading-overlay hidden">
        <div class="spinner-container">
            <div class="spinner"></div>
        </div>
        <p class="loading-text">Sending...</p>
    </div>

    <script>
        // DASHBOARD SCRIPT
        let currentCategory = null;
        let selectedEmoteId = null;
        let selectedServerUrl = null;
        let uidCount = 1;
        const maxUids = 5;
        let toastQueue = [];
        let isProcessingToast = false;
        
        // Toast Notification System
        function showToast(message, type = 'success') {
            toastQueue.push({ message, type });
            if (!isProcessingToast) {
                processToastQueue();
            }
        }
        
        function processToastQueue() {
            if (toastQueue.length === 0) {
                isProcessingToast = false;
                return;
            }
            
            isProcessingToast = true;
            
            const existingToasts = document.querySelectorAll('.toast');
            existingToasts.forEach(toast => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 200);
            });
            
            const { message, type } = toastQueue.shift();
            
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            
            const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
            
            toast.innerHTML = `
                <div class="toast-icon">${icon}</div>
                <div class="toast-message">${message}</div>
            `;
            
            const container = document.getElementById('toastContainer');
            if (container) {
                container.appendChild(toast);
                
                setTimeout(() => toast.classList.add('show'), 10);
                
                setTimeout(() => {
                    toast.classList.remove('show');
                    setTimeout(() => {
                        toast.remove();
                        if (toastQueue.length > 0) {
                            processToastQueue();
                        } else {
                            isProcessingToast = false;
                        }
                    }, 300);
                }, 3000);
            }
        }
        
        // Load data from server
        async function loadData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                // Load servers
                const servers = data.servers || [];
                const indianSelect = document.getElementById('indianServerSelect');
                const bangladeshSelect = document.getElementById('bangladeshServerSelect');
                const otherSelect = document.getElementById('otherServerSelect');
                
                indianSelect.innerHTML = '<option value="">Select Indian Server...</option>';
                bangladeshSelect.innerHTML = '<option value="">Select Bangladesh Server...</option>';
                otherSelect.innerHTML = '<option value="">Select Other Server...</option>';
                
                servers.sort((a, b) => (a.order || 0) - (b.order || 0));
                
                servers.forEach(server => {
                    const option = document.createElement('option');
                    option.value = server.baseUrl;
                    option.textContent = server.name;
                    
                    if (server.region === 'indian') {
                        indianSelect.appendChild(option);
                    } else if (server.region === 'bangladesh') {
                        bangladeshSelect.appendChild(option);
                    } else {
                        otherSelect.appendChild(option);
                    }
                });
                
                // Load categories
                const categories = data.categories || [];
                const categoryTabs = document.getElementById('categoryTabs');
                categoryTabs.innerHTML = '';
                
                categories.sort((a, b) => (a.order || 0) - (b.order || 0));
                
                categories.forEach((cat, index) => {
                    const btn = document.createElement('button');
                    btn.className = 'category-tab' + (index === 0 ? ' active' : '');
                    btn.dataset.category = cat.id;
                    btn.textContent = `${cat.icon || ''} ${cat.name}`;
                    btn.addEventListener('click', () => {
                        document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
                        btn.classList.add('active');
                        currentCategory = cat.id;
                        loadEmotes(cat.id);
                    });
                    categoryTabs.appendChild(btn);
                    
                    if (index === 0) currentCategory = cat.id;
                });
                
                // Load emotes
                loadEmotes(currentCategory);
                
                // Load footer links
                const links = data.settings.footerLinks || {};
                document.getElementById('footerTelegram').href = links.telegram || '#';
                document.getElementById('footerGithub').href = links.github || '#';
                document.getElementById('footerDiscord').href = links.discord || '#';
                document.getElementById('footerYoutube').href = links.youtube || '#';
                
                // Check maintenance
                const maintenance = data.settings.maintenance || {};
                if (maintenance.enabled) {
                    document.getElementById('maintenanceMsg').textContent = maintenance.message;
                    document.getElementById('maintenanceOverlay').classList.remove('hidden');
                }
                
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }
        
        // Load emotes
        async function loadEmotes(category) {
            try {
                const response = await fetch('/api/emotes');
                const data = await response.json();
                const emotes = data.emotes || [];
                const emoteGrid = document.getElementById('emoteGrid');
                emoteGrid.innerHTML = '';
                
                const categoryEmotes = emotes.filter(emote => emote.category === category);
                
                if (categoryEmotes.length === 0) {
                    emoteGrid.innerHTML = '<div class="no-emotes">No emotes in this category</div>';
                    return;
                }
                
                categoryEmotes.forEach(emote => {
                    const card = document.createElement('div');
                    card.className = 'emote-card';
                    card.innerHTML = `
                        <div class="emote-image-wrapper">
                            <img src="${emote.imageUrl}" alt="${emote.emoteId}" loading="lazy" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22%3E%3Crect fill=%22%23333%22 width=%22100%22 height=%22100%22/%3E%3Ctext fill=%22%23666%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22%3E?%3C/text%3E%3C/svg%3E'">
                        </div>
                        <p class="emote-name">${emote.emoteId}</p>
                    `;
                    card.addEventListener('click', () => sendEmoteInstantly(emote.emoteId, card));
                    emoteGrid.appendChild(card);
                });
                
            } catch (error) {
                console.error('Error loading emotes:', error);
            }
        }
        
        // Send emote
        async function sendEmoteInstantly(emoteId, cardElement) {
            selectedEmoteId = emoteId;
            const statEmote = document.getElementById('statEmote');
            if (statEmote) statEmote.textContent = emoteId;
            
            document.querySelectorAll('.emote-card').forEach(c => c.classList.remove('selected'));
            cardElement.classList.add('selected');
            
            const teamCodeInput = document.getElementById('teamCode');
            const uid1Input = document.getElementById('uid1');
            
            if (!selectedServerUrl) {
                showToast('⚠️ Select server first', 'error');
                return;
            }
            
            if (!teamCodeInput || !uid1Input) {
                showToast('❌ Form error', 'error');
                return;
            }
            
            const tc = teamCodeInput.value.trim();
            const uid1 = uid1Input.value.trim();
            
            if (!tc) {
                showToast('⚠️ Enter team code', 'error');
                return;
            }
            
            if (!uid1 || !/^[0-9]{9,12}$/.test(uid1)) {
                showToast('⚠️ Valid UID required (9-12 digits)', 'error');
                return;
            }
            
            const params = new URLSearchParams({
                server: selectedServerUrl,
                tc: tc,
                uid1: uid1,
                emote_id: emoteId
            });
            
            for (let i = 2; i <= maxUids; i++) {
                const inp = document.getElementById(`uid${i}`);
                if (inp?.value.trim() && /^[0-9]{9,12}$/.test(inp.value.trim())) {
                    params.append(`uid${i}`, inp.value.trim());
                }
            }
            
            const url = `/api/send-emote?${params.toString()}`;
            
            showLoader();
            
            try {
                const response = await fetch(url);
                const result = await response.json();
                
                hideLoader();
                
                if (result.success) {
                    showToast(`✓ ${emoteId} sent successfully`, 'success');
                } else {
                    showToast(`✗ ${result.error || 'Failed'}`, 'error');
                }
                
            } catch (error) {
                hideLoader();
                showToast(`❌ ${error.message}`, 'error');
            }
        }
        
        // UID Management
        const addUidBtn = document.getElementById('addUidBtn');
        addUidBtn.addEventListener('click', () => {
            if (uidCount < maxUids) {
                uidCount++;
                addUidField(uidCount);
                const statUids = document.getElementById('statUids');
                if (statUids) {
                    statUids.textContent = uidCount;
                }
                
                if (uidCount >= maxUids) {
                    addUidBtn.disabled = true;
                    addUidBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 13l4 4L19 7" stroke-width="2"/></svg> MAX UIDs ADDED';
                }
            }
        });
        
        function addUidField(number) {
            const container = document.getElementById('uidContainer');
            const uidBox = document.createElement('div');
            uidBox.className = 'input-group-box uid-field';
            uidBox.id = `uidBox${number}`;
            uidBox.innerHTML = `
                <label>TARGET UID ${number} <span style="color: var(--text-gray); font-size: 11px;">(Optional)</span></label>
                <div style="display: flex; gap: 10px;">
                    <input type="text" id="uid${number}" placeholder="Enter UID (9-12 digits)" class="config-input uid-input" pattern="[0-9]{9,12}">
                    <button class="remove-uid-btn" onclick="removeUid(${number})">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M18 6L6 18M6 6l12 12" stroke-width="2"/>
                        </svg>
                    </button>
                </div>
            `;
            container.appendChild(uidBox);
        }
        
        window.removeUid = function(number) {
            const uidBox = document.getElementById(`uidBox${number}`);
            if (uidBox) {
                uidBox.remove();
                uidCount--;
                const statUids = document.getElementById('statUids');
                if (statUids) {
                    statUids.textContent = uidCount;
                }
                
                const addBtn = document.getElementById('addUidBtn');
                if (addBtn) {
                    addBtn.disabled = false;
                    addBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 5v14M5 12h14" stroke-width="2"/></svg> ADD UID';
                }
            }
        };
        
        // Server selection
        function setupServerSelection() {
            const indianSelect = document.getElementById('indianServerSelect');
            const bangladeshSelect = document.getElementById('bangladeshServerSelect');
            const otherSelect = document.getElementById('otherServerSelect');
            const statServer = document.getElementById('statServer');
            
            function handleServerChange(e) {
                selectedServerUrl = e.target.value;
                const selectedText = e.target.options[e.target.selectedIndex].text;
                
                if (statServer) {
                    statServer.textContent = selectedText || 'Not Selected';
                }
                
                if (selectedServerUrl) {
                    showToast(`Server "${selectedText}" selected`, 'success');
                    
                    if (e.target === indianSelect) {
                        bangladeshSelect.value = '';
                        otherSelect.value = '';
                    } else if (e.target === bangladeshSelect) {
                        indianSelect.value = '';
                        otherSelect.value = '';
                    } else if (e.target === otherSelect) {
                        indianSelect.value = '';
                        bangladeshSelect.value = '';
                    }
                }
            }
            
            indianSelect.addEventListener('change', handleServerChange);
            bangladeshSelect.addEventListener('change', handleServerChange);
            otherSelect.addEventListener('change', handleServerChange);
        }
        
        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => {
            window.location.href = '/logout';
        });
        
        // Loader functions
        function showLoader() {
            const loader = document.getElementById('loadingSpinner');
            if (loader) loader.classList.remove('hidden');
        }
        
        function hideLoader() {
            const loader = document.getElementById('loadingSpinner');
            if (loader) loader.classList.add('hidden');
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            loadData();
            setupServerSelection();
        });
    </script>
</body>
</html>
'''

ADMIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XCY LIVE  - Admin Panel</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --bg-dark: #0a0a0a;
            --bg-darker: #050505;
            --card-bg: rgba(20, 20, 20, 0.8);
            --card-border: rgba(0, 150, 255, 0.3);
            --primary-blue: #0096FF;
            --primary-blue-glow: rgba(0, 150, 255, 0.4);
            --text-white: #ffffff;
            --text-gray: #a0a0a0;
            --success-green: #00ff88;
            --danger-red: #ff0844;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #001a33 0%, #000000 50%, #000d1a 100%);
            color: var(--text-white);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .login-body {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: radial-gradient(circle at center, #001a33 0%, #000000 100%);
            position: relative;
        }
        
        .login-container {
            width: 100%;
            max-width: 480px;
            padding: 20px;
            position: relative;
            z-index: 1;
        }
        
        .login-box {
            background: var(--card-bg);
            border: 2px solid var(--card-border);
            border-radius: 20px;
            padding: 50px 40px;
            backdrop-filter: blur(20px);
            box-shadow: 0 0 30px var(--primary-blue-glow);
            position: relative;
            overflow: hidden;
        }
        
        .brand-section {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .lightning-icon {
            font-size: 72px;
            margin-bottom: 15px;
        }
        
        .brand-name {
            font-size: 36px;
            font-weight: 800;
            letter-spacing: 3px;
            color: var(--primary-blue);
            text-shadow: 0 0 15px var(--primary-blue-glow);
            margin-bottom: 8px;
        }
        
        .brand-tagline {
            font-size: 14px;
            color: var(--text-gray);
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .login-form {
            display: flex;
            flex-direction: column;
            gap: 25px;
        }
        
        .input-container {
            position: relative;
        }
        
        .login-input {
            width: 100%;
            padding: 18px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: var(--text-white);
            font-size: 15px;
            transition: all 0.3s ease;
        }
        
        .login-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 15px var(--primary-blue-glow);
        }
        
        .login-btn {
            padding: 18px;
            background: var(--primary-blue);
            border: none;
            border-radius: 12px;
            color: var(--text-white);
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .login-btn:hover {
            background: #008ae6;
            box-shadow: 0 0 25px var(--primary-blue-glow);
        }
        
        .error-message {
            padding: 12px;
            background: rgba(255, 0, 0, 0.1);
            border: 1px solid rgba(255, 0, 0, 0.3);
            border-radius: 8px;
            color: #ff4444;
            text-align: center;
            font-size: 14px;
        }
        
        .hidden {
            display: none !important;
        }
        
        .dashboard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .dashboard-header {
            background: var(--card-bg);
            border: 2px solid var(--card-border);
            border-radius: 16px;
            padding: 20px 25px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            backdrop-filter: blur(20px);
        }
        
        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .header-brand .lightning-icon {
            font-size: 32px;
        }
        
        .header-brand h1 {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: 2px;
            color: var(--primary-blue);
            text-shadow: 0 0 10px var(--primary-blue-glow);
        }
        
        .panel-section {
            background: var(--card-bg);
            border: 2px solid var(--card-border);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
            backdrop-filter: blur(20px);
        }
        
        .section-title {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .title-icon {
            width: 24px;
            height: 24px;
            color: var(--primary-blue);
        }
        
        .section-title h2 {
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: var(--primary-blue);
        }
        
        .admin-form {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .config-input {
            width: 100%;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: var(--text-white);
            font-size: 15px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .config-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 12px var(--primary-blue-glow);
        }
        
        .action-btn-large {
            width: 100%;
            padding: 18px;
            background: var(--primary-blue);
            border: none;
            border-radius: 12px;
            color: var(--text-white);
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .action-btn-large:hover {
            background: #008ae6;
            box-shadow: 0 0 25px var(--primary-blue-glow);
        }
        
        .admin-list {
            margin-top: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .admin-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        .admin-item:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(0, 150, 255, 0.3);
        }
        
        .admin-item-info {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .admin-item-info strong {
            font-size: 14px;
            color: var(--text-white);
        }
        
        .admin-item-actions {
            display: flex;
            gap: 10px;
        }
        
        .action-icon-btn {
            width: 40px;
            height: 40px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .action-icon-btn:hover {
            background: rgba(0, 150, 255, 0.2);
            border-color: var(--primary-blue);
        }
        
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(5px);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: var(--primary-blue);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .form-grid {
                grid-template-columns: 1fr;
            }
            
            .admin-item {
                flex-direction: column;
                gap: 15px;
                align-items: flex-start;
            }
            
            .admin-item-actions {
                align-self: flex-end;
            }
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
    
    <!-- Admin Login View -->
    <div id="adminLoginView" class="login-body">
        <div class="login-container">
            <div class="login-box">
                <div class="brand-section">
                    <div class="lightning-icon">🔐</div>
                    <h1 class="brand-name">ADMIN PANEL</h1>
                    <p class="brand-tagline">XCY LIVE  Control Center</p>
                </div>

                <form id="adminLoginForm" class="login-form">
                    <div class="input-container">
                        <input type="email" id="adminEmail" value="admin@example.com" placeholder="Admin Email" required class="login-input" autocomplete="email">
                    </div>
                    <div class="input-container">
                        <input type="password" id="adminPassword" placeholder="Password" required class="login-input" autocomplete="current-password">
                    </div>
                    <button type="submit" class="login-btn">
                        <span>Access Admin Panel</span>
                    </button>
                    <div id="adminLoginError" class="error-message hidden"></div>
                </form>
            </div>
        </div>
    </div>

    <!-- Admin Dashboard -->
    <div id="adminDashboard" class="dashboard-container hidden">
        <header class="dashboard-header">
            <div class="header-brand">
                <div class="lightning-icon" style="font-size: 28px;">⚡</div>
                <h1>ADMIN PANEL</h1>
            </div>
            <button id="adminLogout" class="icon-button">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" stroke-width="2"/>
                </svg>
            </button>
        </header>

        <!-- Server Management -->
        <section class="panel-section">
            <div class="section-title">
                <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <rect x="2" y="2" width="20" height="8" rx="2" ry="2" stroke-width="2"/>
                    <rect x="2" y="14" width="20" height="8" rx="2" ry="2" stroke-width="2"/>
                </svg>
                <h2>SERVER MANAGEMENT</h2>
            </div>

            <form id="serverForm" class="admin-form">
                <input type="hidden" id="editServerId">
                <div class="form-grid">
                    <input type="text" id="serverName" placeholder="Server Name (e.g., India Server 1)" required class="config-input">
                    <input type="url" id="serverUrl" placeholder="https://example.com" required class="config-input">
                </div>
                <div class="form-grid">
                    <select id="serverRegion" required class="config-input">
                        <option value="">Select Region</option>
                        <option value="indian">🇮🇳 Indian Servers</option>
                        <option value="bangladesh">🇧🇩 Bangladesh Servers</option>
                        <option value="other">🌍 Other Servers</option>
                    </select>
                    <input type="number" id="serverOrder" placeholder="Order (1, 2, 3...)" class="config-input" min="1">
                </div>
                <button type="submit" class="action-btn-large">
                    <span id="serverBtnText">ADD SERVER</span>
                </button>
                <button type="button" id="cancelServerEdit" class="action-btn-large" style="background: rgba(255, 255, 255, 0.05); display: none;">CANCEL</button>
            </form>

            <div id="serverList" class="admin-list"></div>
        </section>

        <!-- Category Management -->
        <section class="panel-section">
            <div class="section-title">
                <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <circle cx="12" cy="12" r="10" stroke-width="2"/>
                    <path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01" stroke-width="2"/>
                </svg>
                <h2>CATEGORY MANAGEMENT</h2>
            </div>

            <form id="categoryForm" class="admin-form">
                <input type="hidden" id="editCategoryId">
                <div class="form-grid">
                    <input type="text" id="categoryName" placeholder="Category Name (e.g., HOT)" required class="config-input">
                    <input type="text" id="categoryIcon" placeholder="Icon (e.g., 🔥)" class="config-input">
                </div>
                <input type="number" id="categoryOrder" placeholder="Order (1, 2, 3...)" class="config-input" min="1">
                <button type="submit" class="action-btn-large">
                    <span id="categoryBtnText">ADD CATEGORY</span>
                </button>
                <button type="button" id="cancelCategoryEdit" class="action-btn-large" style="background: rgba(255, 255, 255, 0.05); display: none;">CANCEL</button>
            </form>

            <div id="categoryList" class="admin-list"></div>
        </section>

        <!-- Emote Management -->
        <section class="panel-section">
            <div class="section-title">
                <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M4 6h16M4 12h16M4 18h16" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <h2>EMOTE MANAGEMENT</h2>
            </div>

            <form id="emoteForm" class="admin-form">
                <input type="hidden" id="editEmoteId">
                <div class="form-grid">
                    <input type="url" id="emoteImageUrl" placeholder="Image URL" required class="config-input">
                    <select id="emoteCategory" required class="config-input">
                        <option value="">Select Category</option>
                    </select>
                </div>
                <div id="emotePreview" class="emote-preview-container"></div>
                <button type="submit" class="action-btn-large">
                    <span id="emoteBtnText">ADD EMOTE</span>
                </button>
                <button type="button" id="cancelEmoteEdit" class="action-btn-large" style="background: rgba(255, 255, 255, 0.05); display: none;">CANCEL</button>
            </form>

            <div id="emoteList" class="admin-list"></div>
        </section>

        <!-- Footer Links -->
        <section class="panel-section">
            <div class="section-title">
                <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" stroke-width="2"/>
                </svg>
                <h2>FOOTER LINKS</h2>
            </div>

            <form id="linksForm" class="admin-form">
                <input type="url" id="telegramUrl" placeholder="Telegram URL" required class="config-input">
                <input type="url" id="githubUrl" placeholder="GitHub URL" required class="config-input">
                <input type="url" id="discordUrl" placeholder="Discord URL" required class="config-input">
                <input type="url" id="youtubeUrl" placeholder="YouTube URL" required class="config-input">
                <button type="submit" class="action-btn-large">
                    <span>UPDATE LINKS</span>
                </button>
            </form>
        </section>

        <!-- Maintenance Mode -->
        <section class="panel-section">
            <div class="section-title">
                <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z" stroke-width="2"/>
                </svg>
                <h2>MAINTENANCE MODE</h2>
            </div>

            <form id="maintenanceForm" class="admin-form">
                <div style="display: flex; align-items: center; gap: 15px; padding: 15px; background: rgba(255, 255, 255, 0.03); border-radius: 10px;">
                    <label style="position: relative; display: inline-block; width: 60px; height: 34px;">
                        <input type="checkbox" id="maintenanceToggle" style="opacity: 0; width: 0; height: 0;">
                        <span style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(255, 255, 255, 0.1); transition: .4s; border-radius: 34px;"></span>
                        <span style="position: absolute; content: ""; height: 26px; width: 26px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%;"></span>
                    </label>
                    <span style="font-size: 14px; font-weight: 600; color: var(--text-white);">Enable Maintenance Mode</span>
                </div>
                <textarea id="maintenanceMessage" placeholder="Maintenance message for users..." rows="3" class="config-input"></textarea>
                <button type="submit" class="action-btn-large">
                    <span>SAVE SETTINGS</span>
                </button>
            </form>
        </section>

        <!-- Password Manager -->
        <section class="panel-section">
            <div class="section-title">
                <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke-width="2"/>
                    <path d="M7 11V7a5 5 0 0110 0v4" stroke-width="2"/>
                </svg>
                <h2>LOGIN PASSWORD</h2>
            </div>

            <form id="passwordForm" class="admin-form">
                <input type="password" id="newPassword" placeholder="New Login Password" required class="config-input">
                <button type="submit" class="action-btn-large">
                    <span>UPDATE PASSWORD</span>
                </button>
            </form>
        </section>
    </div>

    <!-- Loading Spinner -->
    <div id="adminLoader" class="loading-overlay hidden">
        <div class="spinner"></div>
        <p>Processing...</p>
    </div>

    <script>
        // Admin Panel Script
        
        async function showLoader() {
            document.getElementById('adminLoader').classList.remove('hidden');
        }
        
        async function hideLoader() {
            document.getElementById('adminLoader').classList.add('hidden');
        }
        
        // Admin Login
        document.getElementById('adminLoginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('adminEmail').value;
            const password = document.getElementById('adminPassword').value;
            const errorDiv = document.getElementById('adminLoginError');
            
            showLoader();
            
            try {
                const response = await fetch('/api/admin/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('adminLoginView').classList.add('hidden');
                    document.getElementById('adminDashboard').classList.remove('hidden');
                    loadAdminData();
                } else {
                    errorDiv.textContent = '❌ Invalid credentials';
                    errorDiv.classList.remove('hidden');
                    setTimeout(() => errorDiv.classList.add('hidden'), 3000);
                }
            } catch (error) {
                errorDiv.textContent = '❌ Connection error';
                errorDiv.classList.remove('hidden');
            } finally {
                hideLoader();
            }
        });
        
        // Admin Logout
        document.getElementById('adminLogout').addEventListener('click', () => {
            document.getElementById('adminLoginView').classList.remove('hidden');
            document.getElementById('adminDashboard').classList.add('hidden');
            document.getElementById('adminPassword').value = '';
        });
        
        // Load admin data
        async function loadAdminData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                // Load servers
                loadServers(data.servers);
                
                // Load categories
                loadCategories(data.categories);
                loadCategoryDropdown(data.categories);
                
                // Load emotes
                loadEmotes(data.emotes);
                
                // Load settings
                const settings = data.settings || {};
                document.getElementById('telegramUrl').value = settings.footerLinks?.telegram || '';
                document.getElementById('githubUrl').value = settings.footerLinks?.github || '';
                document.getElementById('discordUrl').value = settings.footerLinks?.discord || '';
                document.getElementById('youtubeUrl').value = settings.footerLinks?.youtube || '';
                document.getElementById('maintenanceToggle').checked = settings.maintenance?.enabled || false;
                document.getElementById('maintenanceMessage').value = settings.maintenance?.message || '';
                
            } catch (error) {
                console.error('Error loading admin data:', error);
            }
        }
        
        // Server Management
        function loadServers(servers) {
            const serverList = document.getElementById('serverList');
            serverList.innerHTML = '';
            
            if (!servers || servers.length === 0) {
                serverList.innerHTML = '<p style="color: var(--text-gray); text-align: center;">No servers added yet</p>';
                return;
            }
            
            servers.sort((a, b) => (a.order || 0) - (b.order || 0));
            
            servers.forEach(server => {
                const item = document.createElement('div');
                item.className = 'admin-item';
                item.innerHTML = `
                    <div class="admin-item-info">
                        <strong>${server.name}</strong>
                        <span style="color: var(--text-gray); font-size: 12px;">${server.baseUrl}</span>
                        <span style="color: var(--text-gray); font-size: 11px; display: block; margin-top: 2px;">
                            Region: ${server.region} | Order: ${server.order || 0}
                        </span>
                    </div>
                    <div class="admin-item-actions">
                        <button class="action-icon-btn" onclick="editServer('${server.id}', '${server.name}', '${server.baseUrl}', '${server.region}', ${server.order || 0})">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke-width="2"/>
                            </svg>
                        </button>
                        <button class="action-icon-btn" onclick="deleteServer('${server.id}')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M18 6L6 18M6 6l12 12" stroke-width="2"/>
                            </svg>
                        </button>
                    </div>
                `;
                serverList.appendChild(item);
            });
        }
        
        document.getElementById('serverForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const editId = document.getElementById('editServerId').value;
            const name = document.getElementById('serverName').value;
            const baseUrl = document.getElementById('serverUrl').value;
            const region = document.getElementById('serverRegion').value;
            const order = parseInt(document.getElementById('serverOrder').value) || 0;
            
            if (!region) {
                alert('❌ Please select a region');
                return;
            }
            
            showLoader();
            
            try {
                const method = editId ? 'PUT' : 'POST';
                const url = editId ? `/api/servers?id=${editId}` : '/api/servers';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ id: editId, name, baseUrl, region, order })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('serverForm').reset();
                    document.getElementById('editServerId').value = '';
                    document.getElementById('serverBtnText').textContent = 'ADD SERVER';
                    document.getElementById('cancelServerEdit').style.display = 'none';
                    
                    loadAdminData();
                    alert('✅ Server saved successfully!');
                } else {
                    alert('❌ Error: ' + result.error);
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            } finally {
                hideLoader();
            }
        });
        
        window.editServer = function(id, name, url, region, order) {
            document.getElementById('editServerId').value = id;
            document.getElementById('serverName').value = name;
            document.getElementById('serverUrl').value = url;
            document.getElementById('serverRegion').value = region;
            document.getElementById('serverOrder').value = order;
            document.getElementById('serverBtnText').textContent = 'UPDATE SERVER';
            document.getElementById('cancelServerEdit').style.display = 'block';
        };
        
        window.deleteServer = async function(id) {
            if (confirm('❌ Delete this server?')) {
                showLoader();
                
                try {
                    const response = await fetch(`/api/servers?id=${id}`, {
                        method: 'DELETE'
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        loadAdminData();
                        alert('✅ Server deleted!');
                    }
                } catch (error) {
                    alert('❌ Error: ' + error.message);
                } finally {
                    hideLoader();
                }
            }
        };
        
        document.getElementById('cancelServerEdit').addEventListener('click', () => {
            document.getElementById('serverForm').reset();
            document.getElementById('editServerId').value = '';
            document.getElementById('serverBtnText').textContent = 'ADD SERVER';
            document.getElementById('cancelServerEdit').style.display = 'none';
        });
        
        // Category Management
        function loadCategories(categories) {
            const categoryList = document.getElementById('categoryList');
            categoryList.innerHTML = '';
            
            if (!categories || categories.length === 0) {
                categoryList.innerHTML = '<p style="color: var(--text-gray); text-align: center;">No categories added yet</p>';
                return;
            }
            
            categories.sort((a, b) => (a.order || 0) - (b.order || 0));
            
            categories.forEach(cat => {
                const item = document.createElement('div');
                item.className = 'admin-item';
                item.innerHTML = `
                    <div class="admin-item-info">
                        <strong>${cat.icon || ''} ${cat.name}</strong>
                        <span style="color: var(--text-gray); font-size: 12px;">Order: ${cat.order || 0}</span>
                    </div>
                    <div class="admin-item-actions">
                        <button class="action-icon-btn" onclick="editCategory('${cat.id}', '${cat.name}', '${cat.icon || ''}', ${cat.order || 0})">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke-width="2"/>
                            </svg>
                        </button>
                        <button class="action-icon-btn" onclick="deleteCategory('${cat.id}')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M18 6L6 18M6 6l12 12" stroke-width="2"/>
                            </svg>
                        </button>
                    </div>
                `;
                categoryList.appendChild(item);
            });
        }
        
        function loadCategoryDropdown(categories) {
            const select = document.getElementById('emoteCategory');
            select.innerHTML = '<option value="">Select Category</option>';
            
            if (!categories) return;
            
            categories.sort((a, b) => (a.order || 0) - (b.order || 0));
            
            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.id;
                option.textContent = `${cat.icon || ''} ${cat.name}`;
                select.appendChild(option);
            });
        }
        
        document.getElementById('categoryForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const editId = document.getElementById('editCategoryId').value;
            const name = document.getElementById('categoryName').value;
            const icon = document.getElementById('categoryIcon').value;
            const order = parseInt(document.getElementById('categoryOrder').value) || 0;
            
            showLoader();
            
            try {
                const method = editId ? 'PUT' : 'POST';
                const url = editId ? `/api/categories?id=${editId}` : '/api/categories';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ id: editId || name.toUpperCase().replace(/ /g, '_'), name, icon, order })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('categoryForm').reset();
                    document.getElementById('editCategoryId').value = '';
                    document.getElementById('categoryBtnText').textContent = 'ADD CATEGORY';
                    document.getElementById('cancelCategoryEdit').style.display = 'none';
                    
                    loadAdminData();
                    alert('✅ Category saved!');
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            } finally {
                hideLoader();
            }
        });
        
        window.editCategory = function(id, name, icon, order) {
            document.getElementById('editCategoryId').value = id;
            document.getElementById('categoryName').value = name;
            document.getElementById('categoryIcon').value = icon;
            document.getElementById('categoryOrder').value = order;
            document.getElementById('categoryBtnText').textContent = 'UPDATE CATEGORY';
            document.getElementById('cancelCategoryEdit').style.display = 'block';
        };
        
        window.deleteCategory = async function(id) {
            if (confirm('❌ Delete this category?')) {
                showLoader();
                
                try {
                    const response = await fetch(`/api/categories?id=${id}`, {
                        method: 'DELETE'
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        loadAdminData();
                        alert('✅ Category deleted!');
                    }
                } catch (error) {
                    alert('❌ Error: ' + error.message);
                } finally {
                    hideLoader();
                }
            }
        };
        
        document.getElementById('cancelCategoryEdit').addEventListener('click', () => {
            document.getElementById('categoryForm').reset();
            document.getElementById('editCategoryId').value = '';
            document.getElementById('categoryBtnText').textContent = 'ADD CATEGORY';
            document.getElementById('cancelCategoryEdit').style.display = 'none';
        });
        
        // Emote Management
        document.getElementById('emoteImageUrl').addEventListener('input', (e) => {
            const url = e.target.value;
            const preview = document.getElementById('emotePreview');
            if (preview) {
                if (url) {
                    preview.innerHTML = `<img src="${url}" style="max-width: 150px; max-height: 150px; border-radius: 10px;">`;
                } else {
                    preview.innerHTML = '';
                }
            }
        });
        
        function loadEmotes(emotes) {
            const emoteList = document.getElementById('emoteList');
            emoteList.innerHTML = '';
            
            if (!emotes || emotes.length === 0) {
                emoteList.innerHTML = '<p style="color: var(--text-gray); text-align: center;">No emotes added yet</p>';
                return;
            }
            
            emotes.forEach(emote => {
                const item = document.createElement('div');
                item.className = 'admin-item';
                item.innerHTML = `
                    <div class="admin-item-info" style="display: flex; align-items: center; gap: 10px;">
                        <img src="${emote.imageUrl}" style="width: 40px; height: 40px; object-fit: contain; border-radius: 8px;">
                        <div>
                            <strong>${emote.emoteId}</strong>
                            <span style="color: var(--text-gray); font-size: 12px; display: block;">Category: ${emote.category}</span>
                        </div>
                    </div>
                    <div class="admin-item-actions">
                        <button class="action-icon-btn" onclick="editEmote('${emote.id}', '${emote.imageUrl}', '${emote.category}')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke-width="2"/>
                            </svg>
                        </button>
                        <button class="action-icon-btn" onclick="deleteEmote('${emote.id}')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M18 6L6 18M6 6l12 12" stroke-width="2"/>
                            </svg>
                        </button>
                    </div>
                `;
                emoteList.appendChild(item);
            });
        }
        
        document.getElementById('emoteForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const editId = document.getElementById('editEmoteId').value;
            const imageUrl = document.getElementById('emoteImageUrl').value;
            const category = document.getElementById('emoteCategory').value;
            const emoteId = imageUrl.split('/').pop().split('.')[0];
            
            showLoader();
            
            try {
                const method = editId ? 'PUT' : 'POST';
                const url = editId ? `/api/emotes?id=${editId}` : '/api/emotes';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ id: editId, imageUrl, category, emoteId })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('emoteForm').reset();
                    document.getElementById('editEmoteId').value = '';
                    document.getElementById('emoteBtnText').textContent = 'ADD EMOTE';
                    document.getElementById('cancelEmoteEdit').style.display = 'none';
                    document.getElementById('emotePreview').innerHTML = '';
                    
                    loadAdminData();
                    alert('✅ Emote saved!');
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            } finally {
                hideLoader();
            }
        });
        
        window.editEmote = function(id, url, category) {
            document.getElementById('editEmoteId').value = id;
            document.getElementById('emoteImageUrl').value = url;
            document.getElementById('emoteCategory').value = category;
            document.getElementById('emoteBtnText').textContent = 'UPDATE EMOTE';
            document.getElementById('cancelEmoteEdit').style.display = 'block';
            document.getElementById('emotePreview').innerHTML = `<img src="${url}" style="max-width: 150px; max-height: 150px; border-radius: 10px;">`;
        };
        
        window.deleteEmote = async function(id) {
            if (confirm('❌ Delete this emote?')) {
                showLoader();
                
                try {
                    const response = await fetch(`/api/emotes?id=${id}`, {
                        method: 'DELETE'
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        loadAdminData();
                        alert('✅ Emote deleted!');
                    }
                } catch (error) {
                    alert('❌ Error: ' + error.message);
                } finally {
                    hideLoader();
                }
            }
        };
        
        document.getElementById('cancelEmoteEdit').addEventListener('click', () => {
            document.getElementById('emoteForm').reset();
            document.getElementById('editEmoteId').value = '';
            document.getElementById('emoteBtnText').textContent = 'ADD EMOTE';
            document.getElementById('cancelEmoteEdit').style.display = 'none';
            document.getElementById('emotePreview').innerHTML = '';
        });
        
        // Footer Links
        document.getElementById('linksForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            showLoader();
            
            try {
                const response = await fetch('/api/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        type: 'footerLinks',
                        telegram: document.getElementById('telegramUrl').value,
                        github: document.getElementById('githubUrl').value,
                        discord: document.getElementById('discordUrl').value,
                        youtube: document.getElementById('youtubeUrl').value
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('✅ Links updated!');
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            } finally {
                hideLoader();
            }
        });
        
        // Maintenance Mode
        document.getElementById('maintenanceForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            showLoader();
            
            try {
                const response = await fetch('/api/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        type: 'maintenance',
                        enabled: document.getElementById('maintenanceToggle').checked,
                        message: document.getElementById('maintenanceMessage').value
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('✅ Maintenance settings saved!');
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            } finally {
                hideLoader();
            }
        });
        
        // Password Manager
        document.getElementById('passwordForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const newPassword = document.getElementById('newPassword').value;
            
            showLoader();
            
            try {
                const response = await fetch('/api/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        type: 'password',
                        password: newPassword
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('✅ Password updated!');
                    document.getElementById('newPassword').value = '';
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            } finally {
                hideLoader();
            }
        });
    </script>
</body>
</html>
'''

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
    
    # Check if it's first time setup
    if not DATABASE['users']:
        DATABASE['users']['admin'] = hashlib.sha256('admin123'.encode()).hexdigest()
        save_database()
    
    # Check password
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

# ========== API ENDPOINTS ==========

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
    
    # Simple admin login (in production, use proper authentication)
    if email == 'admin@example.com' and password == 'admin123':
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/api/servers', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_servers():
    if request.method == 'GET':
        return jsonify({'servers': DATABASE['servers']})
    
    elif request.method == 'POST':
        data = request.json
        server = {
            'id': str(int(time.time())),
            'name': data.get('name'),
            'baseUrl': data.get('baseUrl'),
            'region': data.get('region'),
            'order': data.get('order', 0)
        }
        DATABASE['servers'].append(server)
        save_database()
        return jsonify({'success': True, 'server': server})
    
    elif request.method == 'PUT':
        data = request.json
        server_id = data.get('id')
        
        for i, server in enumerate(DATABASE['servers']):
            if server['id'] == server_id:
                DATABASE['servers'][i] = {
                    'id': server_id,
                    'name': data.get('name'),
                    'baseUrl': data.get('baseUrl'),
                    'region': data.get('region'),
                    'order': data.get('order', 0)
                }
                save_database()
                return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Server not found'})
    
    elif request.method == 'DELETE':
        server_id = request.args.get('id')
        DATABASE['servers'] = [s for s in DATABASE['servers'] if s['id'] != server_id]
        save_database()
        return jsonify({'success': True})

@app.route('/api/categories', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_categories():
    if request.method == 'GET':
        return jsonify({'categories': DATABASE['categories']})
    
    elif request.method == 'POST':
        data = request.json
        category = {
            'id': data.get('id') or data.get('name', '').upper().replace(' ', '_'),
            'name': data.get('name'),
            'icon': data.get('icon', ''),
            'order': data.get('order', 0)
        }
        DATABASE['categories'].append(category)
        save_database()
        return jsonify({'success': True, 'category': category})
    
    elif request.method == 'PUT':
        data = request.json
        category_id = data.get('id')
        
        for i, category in enumerate(DATABASE['categories']):
            if category['id'] == category_id:
                DATABASE['categories'][i] = {
                    'id': category_id,
                    'name': data.get('name'),
                    'icon': data.get('icon', ''),
                    'order': data.get('order', 0)
                }
                save_database()
                return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Category not found'})
    
    elif request.method == 'DELETE':
        category_id = request.args.get('id')
        DATABASE['categories'] = [c for c in DATABASE['categories'] if c['id'] != category_id]
        save_database()
        return jsonify({'success': True})

@app.route('/api/emotes', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_emotes():
    if request.method == 'GET':
        return jsonify({'emotes': DATABASE['emotes']})
    
    elif request.method == 'POST':
        data = request.json
        emote = {
            'id': str(int(time.time())),
            'imageUrl': data.get('imageUrl'),
            'category': data.get('category'),
            'emoteId': data.get('emoteId') or data.get('imageUrl', '').split('/')[-1].split('.')[0]
        }
        DATABASE['emotes'].append(emote)
        save_database()
        return jsonify({'success': True, 'emote': emote})
    
    elif request.method == 'PUT':
        data = request.json
        emote_id = data.get('id')
        
        for i, emote in enumerate(DATABASE['emotes']):
            if emote['id'] == emote_id:
                DATABASE['emotes'][i] = {
                    'id': emote_id,
                    'imageUrl': data.get('imageUrl'),
                    'category': data.get('category'),
                    'emoteId': data.get('emoteId') or data.get('imageUrl', '').split('/')[-1].split('.')[0]
                }
                save_database()
                return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Emote not found'})
    
    elif request.method == 'DELETE':
        emote_id = request.args.get('id')
        DATABASE['emotes'] = [e for e in DATABASE['emotes'] if e['id'] != emote_id]
        save_database()
        return jsonify({'success': True})

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    if request.method == 'GET':
        return jsonify(DATABASE['settings'])
    
    elif request.method == 'POST':
        data = request.json
        setting_type = data.get('type')
        
        if setting_type == 'maintenance':
            DATABASE['settings']['maintenance'] = {
                'enabled': data.get('enabled', False),
                'message': data.get('message', '')
            }
        elif setting_type == 'footerLinks':
            DATABASE['settings']['footerLinks'] = {
                'telegram': data.get('telegram', '#'),
                'github': data.get('github', '#'),
                'discord': data.get('discord', '#'),
                'youtube': data.get('youtube', '#')
            }
        elif setting_type == 'password':
            new_password = data.get('password')
            if new_password:
                DATABASE['users']['admin'] = hash_password(new_password)
        
        save_database()
        return jsonify({'success': True})

@app.route('/api/send-emote', methods=['GET'])
def send_emote():
    # This is the proxy endpoint that forwards to actual servers
    server = request.args.get('server')
    tc = request.args.get('tc')
    emote_id = request.args.get('emote_id')
    
    # Collect UIDs
    uids = {}
    for i in range(1, 6):
        uid = request.args.get(f'uid{i}')
        if uid:
            uids[f'uid{i}'] = uid
    
    # Validate
    if not server or not tc or not emote_id:
        return jsonify({'success': False, 'error': 'Missing required parameters'})
    
    # Build the target URL
    params = {'tc': tc, 'emote_id': emote_id, **uids}
    query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    target_url = f"{server}/join?{query_string}"
    
    try:
        # Make the actual HTTP request
        response = requests.get(target_url, timeout=10)
        return jsonify({
            'success': True,
            'status': response.status_code,
            'message': 'Emote sent successfully',
            'data': response.text
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Load database on startup
load_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)  # REMOVE port=5000