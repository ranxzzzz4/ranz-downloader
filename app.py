from flask import Flask, render_template, request, jsonify, send_file
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
    elif 'facebook.com'' in url or 'fb.watch' in url:
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

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True)