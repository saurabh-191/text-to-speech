from flask import Flask, request, jsonify, send_file, send_from_directory, url_for
from flask_cors import CORS
import pyttsx3
import os
import tempfile
import uuid
from datetime import datetime
import threading
import time
import json
import platform
import wave
import struct

app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

# Global dictionary to store conversion status
conversion_status = {}

# Language to voice mapping with fallback options
LANGUAGE_VOICES = {
    'en': ['en-US', 'en-GB', 'en'],
    'hi': ['hi-IN', 'hi'],
    'bn': ['bn-IN', 'bn'],
    'ta': ['ta-IN', 'ta'],
    'te': ['te-IN', 'te'],
    'mr': ['mr-IN', 'mr'],
    'gu': ['gu-IN', 'gu'],
    'kn': ['kn-IN', 'kn'],
    'ml': ['ml-IN', 'ml'],
    'pa': ['pa-IN', 'pa']
}

class TextToSpeechConverter:
    def __init__(self):
        self.engine = None
        self.temp_dir = tempfile.mkdtemp()
        self.initialize_engine()
        
    def initialize_engine(self):
        """Initialize the TTS engine"""
        try:
            self.engine = pyttsx3.init()
            # Set default properties
            self.engine.setProperty('rate', 200)
            self.engine.setProperty('volume', 0.9)
            return True
        except Exception as e:
            print(f"Error initializing TTS engine: {e}")
            return False
    
    def get_available_voices(self, language=None):
        """Get all available voices, optionally filtered by language"""
        if not self.engine:
            if not self.initialize_engine():
                return []
        
        try:
            voices = self.engine.getProperty('voices')
            voice_list = []
            
            # If no voices are found, return a default voice
            if not voices:
                system = platform.system()
                if system == 'Windows':
                    default_voice = {
                        'id': 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_DAVID_11.0',
                        'name': 'Microsoft David Desktop',
                        'gender': 'male',
                        'language': 'en'
                    }
                elif system == 'Darwin':  # macOS
                    default_voice = {
                        'id': 'com.apple.speech.synthesis.voice.alex',
                        'name': 'Alex',
                        'gender': 'male',
                        'language': 'en'
                    }
                else:  # Linux
                    default_voice = {
                        'id': 'english-us',
                        'name': 'English (US)',
                        'gender': 'male',
                        'language': 'en'
                    }
                return [default_voice]
            
            for voice in voices:
                # Get voice ID and name
                voice_id = voice.id
                voice_name = voice.name
                
                # Determine gender
                gender = 'female' if any(x in voice_name.lower() for x in ['female', 'zira', 'samantha']) else 'male'
                
                # Determine language
                lang = 'en'  # default
                for code, patterns in LANGUAGE_VOICES.items():
                    if any(pattern in voice_id.lower() for pattern in patterns):
                        lang = code
                        break
                
                # Skip if language filter is set and voice doesn't match
                if language and lang != language:
                    continue
                
                voice_info = {
                    'id': voice_id,
                    'name': voice_name,
                    'gender': gender,
                    'language': lang
                }
                voice_list.append(voice_info)
            
            # If no voices match the language filter, return all voices
            if language and not voice_list:
                return self.get_available_voices()
            
            return voice_list
            
        except Exception as e:
            print(f"Error getting voices: {e}")
            return []
    
    def convert_text_to_speech(self, text, voice_id=None, rate=200, volume=0.9, pitch=50, depth=50):
        """Convert text to speech with specified parameters"""
        try:
            if not self.engine:
                if not self.initialize_engine():
                    return None, "Failed to initialize TTS engine"
            
            # Set voice
            if voice_id:
                self.engine.setProperty('voice', voice_id)
            
            # Set rate (speed)
            self.engine.setProperty('rate', rate)
            
            # Set volume
            self.engine.setProperty('volume', volume)
            
            # Apply pitch and depth adjustments
            adjusted_pitch = pitch + (depth - 50) / 2
            self.engine.setProperty('pitch', adjusted_pitch)
            
            # Generate unique filename
            filename = f"tts_{uuid.uuid4().hex}.wav"
            filepath = os.path.join(self.temp_dir, filename)
            
            # Save to file with high quality settings
            self.engine.save_to_file(text, filepath)
            self.engine.runAndWait()
            
            # Enhance audio quality
            self._enhance_audio_quality(filepath)
            
            return filepath, None
            
        except Exception as e:
            return None, str(e)
    
    def _enhance_audio_quality(self, filepath):
        """Enhance the audio quality of the WAV file"""
        try:
            # Read the WAV file
            with wave.open(filepath, 'rb') as wav_file:
                # Get audio parameters
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                # Read all frames
                frames = wav_file.readframes(n_frames)
                
                # Convert to list of samples
                if sample_width == 2:  # 16-bit audio
                    samples = struct.unpack(f'<{n_frames * n_channels}h', frames)
                else:  # 8-bit audio
                    samples = struct.unpack(f'<{n_frames * n_channels}B', frames)
                
                # Apply quality enhancements
                # 1. Normalize audio
                max_sample = max(abs(s) for s in samples)
                if max_sample > 0:
                    normalized_samples = [int(s * 32767 / max_sample) for s in samples]
                else:
                    normalized_samples = samples
                
                # 2. Convert back to bytes
                if sample_width == 2:
                    enhanced_frames = struct.pack(f'<{len(normalized_samples)}h', *normalized_samples)
                else:
                    enhanced_frames = struct.pack(f'<{len(normalized_samples)}B', *normalized_samples)
            
            # Write enhanced audio back to file
            with wave.open(filepath, 'wb') as wav_file:
                wav_file.setnchannels(n_channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(frame_rate)
                wav_file.writeframes(enhanced_frames)
                
        except Exception as e:
            print(f"Error enhancing audio quality: {e}")

# Initialize converter
tts_converter = TextToSpeechConverter()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/api/voices', methods=['GET'])
def get_voices():
    """Get available voices"""
    try:
        language = request.args.get('language', 'en')
        voices = tts_converter.get_available_voices(language)
        return jsonify({
            'success': True,
            'voices': voices
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/convert', methods=['POST'])
def convert_text():
    """Convert text to speech"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            }), 400
        
        text = data['text']
        if not text.strip():
            return jsonify({
                'success': False,
                'error': 'Text cannot be empty'
            }), 400
        
        # Get parameters
        voice_id = data.get('voice_id')
        rate = int(data.get('rate', 200))  # Speed (50-300)
        volume = float(data.get('volume', 0.9))  # Volume (0.0-1.0)
        pitch = int(data.get('pitch', 50))  # Pitch (0-100)
        depth = int(data.get('depth', 50))  # Depth (0-100)
        language = data.get('language', 'en')
        
        # Validate parameters
        rate = max(50, min(300, rate))
        volume = max(0.0, min(1.0, volume))
        pitch = max(0, min(100, pitch))
        depth = max(0, min(100, depth))
        
        # Generate conversion ID
        conversion_id = str(uuid.uuid4())
        conversion_status[conversion_id] = {
            'status': 'processing',
            'progress': 0,
            'filepath': None,
            'error': None,
            'created_at': datetime.now()
        }
        
        # Start conversion in background
        def convert_async():
            try:
                conversion_status[conversion_id]['progress'] = 25
                filepath, error = tts_converter.convert_text_to_speech(
                    text, voice_id, rate, volume, pitch, depth
                )
                
                if error:
                    conversion_status[conversion_id].update({
                        'status': 'failed',
                        'error': error,
                        'progress': 0
                    })
                else:
                    conversion_status[conversion_id].update({
                        'status': 'completed',
                        'filepath': filepath,
                        'progress': 100
                    })
            except Exception as e:
                conversion_status[conversion_id].update({
                    'status': 'failed',
                    'error': str(e),
                    'progress': 0
                })
        
        thread = threading.Thread(target=convert_async)
        thread.start()
        
        return jsonify({
            'success': True,
            'conversion_id': conversion_id,
            'message': 'Conversion started'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status/<conversion_id>', methods=['GET'])
def get_conversion_status(conversion_id):
    """Get conversion status"""
    if conversion_id not in conversion_status:
        return jsonify({
            'success': False,
            'error': 'Conversion not found'
        }), 404
    
    status = conversion_status[conversion_id]
    return jsonify({
        'success': True,
        'status': status['status'],
        'progress': status['progress'],
        'error': status.get('error')
    })

@app.route('/api/download/<conversion_id>', methods=['GET'])
def download_file(conversion_id):
    """Download the converted audio file"""
    if conversion_id not in conversion_status:
        return jsonify({
            'success': False,
            'error': 'Conversion not found'
        }), 404
    
    status = conversion_status[conversion_id]
    
    if status['status'] != 'completed':
        return jsonify({
            'success': False,
            'error': 'Conversion not completed'
        }), 400
    
    filepath = status['filepath']
    if not filepath or not os.path.exists(filepath):
        return jsonify({
            'success': False,
            'error': 'File not found'
        }), 404
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"converted_speech_{conversion_id}.wav",
        mimetype='audio/wav'
    )

@app.route('/api/upload', methods=['POST'])
def upload_text_file():
    """Upload and read text file"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not file.filename.endswith('.txt'):
            return jsonify({
                'success': False,
                'error': 'Only .txt files allowed'
            }), 400
        
        # Read file content
        content = file.read().decode('utf-8')
        
        return jsonify({
            'success': True,
            'content': content,
            'filename': file.filename
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Cleanup old conversions periodically
def cleanup_old_conversions():
    """Clean up old conversion files and status"""
    while True:
        try:
            current_time = datetime.now()
            expired_ids = []
            
            for conv_id, status in conversion_status.items():
                # Remove conversions older than 1 hour
                if (current_time - status['created_at']).seconds > 3600:
                    expired_ids.append(conv_id)
                    
                    # Delete file if exists
                    if status.get('filepath') and os.path.exists(status['filepath']):
                        os.remove(status['filepath'])
            
            # Remove expired conversions
            for conv_id in expired_ids:
                del conversion_status[conv_id]
                
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        time.sleep(300)  # Run every 5 minutes

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_conversions, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)