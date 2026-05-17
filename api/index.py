from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import re

app = Flask(__name__)

DOWNLOAD_FOLDER = '/tmp/downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def detect_platform(url):
    if 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    elif 'tiktok.com' in url:
        return 'tiktok'
    elif 'instagram.com' in url:
        return 'instagram'
    elif 'facebook.com' in url or 'fb.watch' in url:
        return 'facebook'
    return 'unknown'

def download_video(url, quality='medium'):
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    
    if quality == 'high':
        ydl_opts['format'] = 'best[height<=1080]'
    elif quality == 'medium':
        ydl_opts['format'] = 'best[height<=720]'
    elif quality == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return {
                'success': True,
                'filename': os.path.basename(filename),
                'title': info.get('title', 'video'),
                'platform': detect_platform(url)
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    quality = data.get('quality', 'medium')
    result = download_video(url, quality)
    return jsonify(result)

@app.route('/download-file/<filename>')
def download_file(filename):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    return send_file(filepath, as_attachment=True)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>Ranz Downloader</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            background: linear-gradient(165deg, #0b1120 0%, #1a1a3e 30%, #2d1b4e 60%, #7c2d5e 85%, #e06c4e 100%);
            min-height: 100vh;
            padding: 24px;
        }
        .container { max-width: 680px; margin: 0 auto; }
        .card {
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(16px);
            border-radius: 32px;
            padding: 28px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        h1 {
            font-size: 1.8rem;
            font-weight: 700;
            color: white;
            text-align: center;
            margin-bottom: 8px;
        }
        .sub {
            text-align: center;
            color: rgba(255,255,255,0.7);
            font-size: 0.85rem;
            margin-bottom: 32px;
        }
        .platforms {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 32px;
            flex-wrap: wrap;
        }
        .platform {
            padding: 6px 18px;
            background: rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 40px;
            font-size: 0.75rem;
            color: rgba(255,255,255,0.8);
            cursor: pointer;
        }
        .platform.active { background: #FF5E00; border-color: #FF5E00; color: white; }
        .input-label { color: rgba(255,255,255,0.6); font-size: 0.75rem; margin-bottom: 8px; }
        .url-input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px;
            color: white;
            font-size: 0.9rem;
            font-family: monospace;
        }
        .url-input:focus { outline: none; border-color: #FF5E00; }
        .quality-group { margin: 24px 0; }
        .quality-options { display: flex; flex-wrap: wrap; gap: 8px; }
        .quality-btn {
            padding: 6px 14px;
            background: rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 40px;
            color: rgba(255,255,255,0.7);
            font-size: 0.7rem;
            cursor: pointer;
        }
        .quality-btn.active { background: #FF5E00; border-color: #FF5E00; color: white; }
        .download-btn {
            width: 100%;
            padding: 14px;
            background: #FF5E00;
            border: none;
            border-radius: 28px;
            font-size: 0.9rem;
            font-weight: 600;
            color: white;
            cursor: pointer;
        }
        .download-btn:disabled { opacity: 0.5; }
        .loading { display: none; text-align: center; padding: 24px; }
        .loading.show { display: block; }
        .spinner {
            width: 32px;
            height: 32px;
            border: 2px solid rgba(255,94,0,0.3);
            border-top-color: #FF5E00;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
            margin: 0 auto 8px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .result { display: none; background: rgba(0,0,0,0.4); border-radius: 24px; padding: 16px; margin-top: 20px; }
        .result.show { display: block; }
        .result-row { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .result-icon { width: 40px; height: 40px; background: rgba(255,94,0,0.15); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
        .result-title { color: white; font-weight: 500; font-size: 0.85rem; }
        .result-meta { color: rgba(255,255,255,0.5); font-size: 0.65rem; }
        .save-link { display: block; text-align: center; padding: 10px; background: #22C55E; border-radius: 20px; color: white; text-decoration: none; font-weight: 500; font-size: 0.8rem; }
        .alert { display: none; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); border-radius: 20px; padding: 10px; color: #F87171; font-size: 0.75rem; margin-top: 16px; text-align: center; }
        .alert.show { display: block; }
        .footer { text-align: center; margin-top: 32px; font-size: 0.6rem; color: rgba(255,255,255,0.3); }
        @media (max-width: 640px) { .card { padding: 20px; } }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>ranz downloader</h1>
        <div class="sub">youtube · tiktok · instagram · facebook</div>
        <div class="platforms">
            <span class="platform active" data-platform="youtube">YouTube</span>
            <span class="platform" data-platform="tiktok">TikTok</span>
            <span class="platform" data-platform="instagram">Instagram</span>
            <span class="platform" data-platform="facebook">Facebook</span>
        </div>
        <div class="input-label">link</div>
        <input type="text" class="url-input" id="urlInput" placeholder="https://youtube.com/watch?v=...">
        <div class="quality-group">
            <div class="quality-options">
                <span class="quality-btn" data-quality="best">best</span>
                <span class="quality-btn" data-quality="high">1080p</span>
                <span class="quality-btn active" data-quality="medium">720p</span>
                <span class="quality-btn" data-quality="low">480p</span>
                <span class="quality-btn" data-quality="audio">mp3</span>
            </div>
        </div>
        <button class="download-btn" id="downloadBtn">download</button>
        <div class="loading" id="loading"><div class="spinner"></div><div class="loading-text">processing...</div></div>
        <div class="alert" id="alert"></div>
        <div class="result" id="result">
            <div class="result-row"><div class="result-icon" id="resultIcon">🎬</div><div class="result-info"><div class="result-title" id="resultTitle">video title</div><div class="result-meta" id="resultMeta">youtube · 720p</div></div></div>
            <a href="#" class="save-link" id="saveLink" target="_blank">save file</a>
        </div>
    </div>
    <div class="footer"><p>ranz · 2026</p></div>
</div>
<script>
    let currentQuality = 'medium';
    let currentPlatform = 'youtube';
    document.querySelectorAll('.platform').forEach(el => {
        el.addEventListener('click', () => {
            document.querySelectorAll('.platform').forEach(p => p.classList.remove('active'));
            el.classList.add('active');
            currentPlatform = el.dataset.platform;
        });
    });
    document.querySelectorAll('.quality-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.quality-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentQuality = btn.dataset.quality;
        });
    });
    async function download() {
        const url = document.getElementById('urlInput').value.trim();
        if (!url) return showAlert('masukkan link');
        showLoading(true);
        hideAlert();
        hideResult();
        try {
            const res = await fetch('/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, quality: currentQuality })
            });
            const data = await res.json();
            if (data.success) {
                showResult(data);
            } else {
                showAlert(data.error || 'gagal');
            }
        } catch (err) {
            showAlert('error: ' + err.message);
        } finally {
            showLoading(false);
        }
    }
    function showResult(data) {
        const icons = { youtube: '🎬', tiktok: '🎵', instagram: '📸', facebook: '📘' };
        document.getElementById('resultIcon').innerHTML = icons[data.platform] || '📹';
        document.getElementById('resultTitle').innerText = data.title.substring(0, 50);
        document.getElementById('resultMeta').innerHTML = `${data.platform} · ${currentQuality}`;
        document.getElementById('saveLink').href = `/download-file/${encodeURIComponent(data.filename)}`;
        document.getElementById('result').classList.add('show');
    }
    function showLoading(show) { document.getElementById('loading').classList.toggle('show', show); document.getElementById('downloadBtn').disabled = show; }
    function showAlert(msg) { const alertEl = document.getElementById('alert'); alertEl.innerHTML = msg; alertEl.classList.add('show'); setTimeout(() => alertEl.classList.remove('show'), 3000); }
    function hideAlert() { document.getElementById('alert').classList.remove('show'); }
    function hideResult() { document.getElementById('result').classList.remove('show'); }
    document.getElementById('urlInput').addEventListener('keypress', (e) => { if (e.key === 'Enter') download(); });
    document.getElementById('downloadBtn').addEventListener('click', download);
</script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(debug=True)
