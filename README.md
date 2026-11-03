# Advanced Text-to-Speech Converter

A modern web application that converts text to speech with customizable voice settings.

## Features

- 📁 File Upload: Support for .txt files with drag-and-drop functionality
- 🎙️ Voice Selection: Choose from available system voices with gender indicators
- ⚡ Speed Control: Adjust speaking speed (50-300 WPM)
- 🔊 Volume Control: Fine-tune audio volume (0-100%)
- 🎵 Pitch Control: Modify voice pitch/tone (0-100)
- 📥 Download: Save generated audio as MP3 files
- 📱 Responsive Design: Works on desktop and mobile devices
- ⏱️ Real-time Progress: Live conversion status updates

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- A modern web browser

## Installation

1. Clone this repository or download the files
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the backend server:
   ```bash
   python app.py
   ```
   The server will start on http://localhost:5000

2. Open the `index.html` file in your web browser
   - You can use any web server to serve the file
   - For development, you can use Python's built-in server:
     ```bash
     python -m http.server 8000
     ```
   - Then open http://localhost:8000 in your browser

## Usage

1. Enter text directly in the text area or upload a .txt file
2. Select a voice from the dropdown menu
3. Adjust speed, volume, and pitch settings as desired
4. Click "Convert to Speech"
5. Wait for the conversion to complete
6. Download the generated MP3 file

## Notes

- The application uses your system's available text-to-speech voices
- Generated audio files are temporarily stored and automatically cleaned up after 1 hour
- Maximum text length is 5000 characters 