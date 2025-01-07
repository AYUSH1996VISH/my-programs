import pyttsx3
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from contextlib import asynccontextmanager
import os
from tkinter import Tk
from tkinter.filedialog import asksaveasfilename

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Any startup logic can go here
    yield
    # Any shutdown logic can go here

app = FastAPI(lifespan=lifespan)

# Allow CORS for API usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates directory
TEMPLATES_DIR = Path("templates")
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

def text_to_audio(input_text, save_path):
    """
    Convert input text to audio with a clear and understandable male voice.
    """
    try:
        # Initialize pyttsx3 engine
        engine = pyttsx3.init()

        # Configure voice settings
        voices = engine.getProperty('voices')
        for voice in voices:
            if 'Male' in voice.name or 'David' in voice.name:
                engine.setProperty('voice', voice.id)
                break

        engine.setProperty('rate', 160)  # Adjust speaking rate
        engine.setProperty('volume', 0.9)  # Adjust volume

        # Save audio file
        engine.save_to_file(input_text, save_path)
        engine.runAndWait()
        return save_path

    except Exception as e:
        raise RuntimeError(f"An error occurred during text-to-speech conversion: {e}")

@app.get("/", response_class=HTMLResponse)
async def interface(request: Request):
    """
    Render the text-to-speech interface.
    """
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Text-to-Speech</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f9;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                }
                h1 {
                    color: #333;
                    text-align: center;
                    margin-bottom: 20px;
                }
                form {
                    background: #fff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    width: 400px;
                }
                textarea {
                    width: 90%;
                    height: 150px;
                    padding: 10px;
                    margin-bottom: 15px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    font-size: 16px;
                }
                button {
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                }
                button:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <form action="/text-to-audio" method="post">
                <h1>Text-to-Speech Converter</h1>
                <textarea name="text" placeholder="Enter your text here..."></textarea>
                <button type="submit">Convert to Audio</button>
            </form>
        </body>
        </html>
        """,
        status_code=200
    )


@app.post("/text-to-audio")
async def text_to_audio_api(text: str = Form(...)):
    """
    Convert input text to audio and allow the user to select where to save the file via a system popup.
    """
    try:
        # Use a system popup to ask the user where to save the file
        root = Tk()
        root.withdraw()  # Hide the main Tkinter window
        root.attributes('-topmost', True)  # Bring the dialog to the front
        save_path = asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("Audio Files", "*.mp3")],
            title="Save Audio File"
        )
        root.destroy()

        # If the user cancels the save dialog
        if not save_path:
            raise HTTPException(status_code=400, detail="Save operation cancelled by the user.")

        # Perform text-to-speech conversion
        output_file = text_to_audio(text, save_path)
        return {"message": "Audio file saved successfully", "path": output_file}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/download-audio")
async def download_audio():
    """
    Endpoint to download the generated audio file.
    """
    files = list(Path.cwd().glob("*.mp3"))  # Looks for audio files in the current working directory
    if files:
        return FileResponse(files[0], media_type="audio/mpeg", filename=files[0].name)
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")
