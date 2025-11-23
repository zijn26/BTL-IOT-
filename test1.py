from flask import Flask, request, render_template, jsonify, flash, redirect, url_for
import requests
import json
import os
import wave
import tempfile
from werkzeug.utils import secure_filename
import time

# ==== CONFIG ====
WIT_AI_TOKEN = "XNEACJL4ODFGEWYCYGOLRYGYX2OFP54G"   # Thay bằng token của bạn
SAMPLE_RATE = 16000
CHANNELS = 1
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Tạo thư mục upload nếu chưa có
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Kiểm tra file có đúng định dạng không"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_witai(file_path):
    """Upload file lên Wit.ai và nhận kết quả text"""
    headers = {
        "Authorization": f"Bearer {WIT_AI_TOKEN}",
        "Content-Type": "audio/wav"
    }
    
    try:
        print(f"📤 Uploading file: {file_path}")
        
        with open(file_path, "rb") as f:
            response = requests.post(
                "https://api.wit.ai/speech?v=20220622",
                headers=headers,
                data=f,
                timeout=30
            )
        
        if response.status_code == 200:
            try:
                data = response.json()
                text_out = data.get("text", "").strip()
                
                if text_out:
                    print(f"✅ Transcription successful!")
                    print(f"📝 Text: {text_out}")
                    return {
                        'success': True,
                        'text': text_out,
                        'raw_response': data
                    }
                else:
                    print(f"🔇 No clear speech detected in the audio")
                    return {
                        'success': False,
                        'error': 'No clear speech detected in the audio',
                        'raw_response': data
                    }
                    
            except json.JSONDecodeError:
                print(f"💥 JSON error: {response.text[:100]}")
                return {
                    'success': False,
                    'error': f'JSON decode error: {response.text[:100]}',
                    'raw_response': response.text
                }
                
        elif response.status_code == 429:
            print(f"⚠️ Rate limit reached! Please try again later.")
            return {
                'success': False,
                'error': 'Rate limit reached! Please try again later.',
                'raw_response': response.text
            }
            
        else:
            print(f"💥 HTTP {response.status_code}: {response.text[:100]}")
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text[:100]}',
                'raw_response': response.text
            }
            
    except requests.exceptions.Timeout:
        print(f"⏰ Upload timeout")
        return {
            'success': False,
            'error': 'Upload timeout',
            'raw_response': None
        }
    except FileNotFoundError:
        print(f"💥 File not found: {file_path}")
        return {
            'success': False,
            'error': f'File not found: {file_path}',
            'raw_response': None
        }
    except Exception as e:
        print(f"💥 Upload error: {e}")
        return {
            'success': False,
            'error': f'Upload error: {str(e)}',
            'raw_response': None
        }

def validate_wav_file(file_path):
    """Kiểm tra file WAV có hợp lệ không"""
    try:
        with wave.open(file_path, "rb") as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            frames = wf.getnframes()
            duration = frames / sample_rate
            
            file_info = {
                'channels': channels,
                'sample_rate': sample_rate,
                'duration': duration,
                'frames': frames,
                'valid': True
            }
            
            # Kiểm tra định dạng
            if channels != CHANNELS:
                file_info['warning'] = f"Expected {CHANNELS} channel(s), got {channels}"
            
            if sample_rate != SAMPLE_RATE:
                file_info['warning'] = f"Expected {SAMPLE_RATE} Hz, got {sample_rate} Hz"
            
            if duration > 20:
                file_info['warning'] = f"File is {duration:.1f}s long. Wit.ai has a 20s limit."
            
            return file_info
            
    except Exception as e:
        return {
            'valid': False,
            'error': f"Invalid WAV file: {str(e)}"
        }

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Xử lý upload file"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file selected'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Validate file
        file_info = validate_wav_file(file_path)
        
        if not file_info['valid']:
            os.remove(file_path)  # Xóa file nếu không hợp lệ
            return jsonify({
                'success': False, 
                'error': file_info['error']
            })
        
        # Upload to Wit.ai
        result = upload_to_witai(file_path)
        
        # Thêm thông tin file vào kết quả
        result['file_info'] = file_info
        result['filename'] = filename
        
        # Xóa file tạm
        try:
            os.remove(file_path)
        except:
            pass
        
        return jsonify(result)
    
    return jsonify({'success': False, 'error': 'Invalid file format. Please upload a .wav file'})

if __name__ == "__main__":
    print("🎙️ WAV TO TEXT WEB CONVERTER")
    print("=" * 50)
    print("🌐 Starting web server...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("=" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping server...")
    except Exception as e:
        print(f"💥 Server error: {e}")