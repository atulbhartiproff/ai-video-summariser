"""
AI Video Summarizer Backend
FastAPI application that processes video files and generates summaries using Gemini AI
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import subprocess
import google.generativeai as genai
from typing import Optional

# Initialize FastAPI app
app = FastAPI(
    title="AI Video Summarizer API",
    description="Upload videos and get AI-generated summaries",
    version="1.0.0"
)

# CORS middleware - allow all origins for development/deployment flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

# Log API key status (first 5 and last 5 chars only for security)
key_len = len(GEMINI_API_KEY) if GEMINI_API_KEY else 0
first5 = GEMINI_API_KEY[:5] if key_len >= 5 else GEMINI_API_KEY or ""
last5 = GEMINI_API_KEY[-5:] if key_len >= 5 else ""
masked = f"{first5}...{last5}" if key_len >= 10 else (first5 or "INVALID")
print(f"Gemini API Key loaded: {masked} (length: {key_len})")

genai.configure(api_key=GEMINI_API_KEY)

# Model selection
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
print(f"Using Gemini model: {GEMINI_MODEL}")

# Maximum file size (500MB default)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "500"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "ai-video-summarizer-backend"}


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload and process video file
    
    Args:
        file: Video file to process
        
    Returns:
        JSON with summary of the video content
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a video file."
        )
    
    # Create temporary directory for processing
    temp_dir = tempfile.mkdtemp()
    input_path = None
    audio_path = None
    
    try:
        # Save uploaded file
        input_path = os.path.join(temp_dir, file.filename or "video.mp4")
        
        # Read file in chunks to handle large files
        file_size = 0
        with open(input_path, "wb") as f:
            while True:
                chunk = await file.read(8192)  # 8KB chunks
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE_BYTES:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB."
                    )
                f.write(chunk)
        
        # Extract audio from video using ffmpeg
        audio_path = os.path.join(temp_dir, "audio.wav")
        
        # Run ffmpeg to extract audio
        # -i: input file
        # -vn: disable video
        # -acodec pcm_s16le: PCM 16-bit little-endian audio codec
        # -ar 44100: sample rate 44.1kHz
        # -ac 2: stereo audio
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # Audio codec
            "-ar", "44100",  # Sample rate
            "-ac", "2",  # Audio channels (stereo)
            "-y",  # Overwrite output file
            audio_path
        ]
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract audio: {result.stderr}"
            )
        
        # Check if audio file was created
        if not os.path.exists(audio_path):
            raise HTTPException(
                status_code=500,
                detail="Audio extraction failed - output file not found"
            )
        
        # Use Gemini to process audio and generate summary
        try:
            # Initialize Gemini model (configurable via GEMINI_MODEL)
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            # Create prompt for summarization
            prompt = """Please analyze this video/audio content and provide a comprehensive summary with the following structure:

1. **Main Topic**: A brief one-sentence description of what this video is about
2. **Key Points**: Bullet points covering the main ideas, concepts, or information presented
3. **Important Details**: Any specific facts, numbers, dates, or noteworthy information
4. **Takeaways**: Key lessons or actionable insights from the content

Format the response in a clear, organized manner with proper sections."""

            # Read audio file and send to Gemini
            with open(audio_path, "rb") as audio_file:
                audio_data = audio_file.read()
                
                # Generate content using Gemini (multimodal input)
                response = model.generate_content([
                    prompt,
                    {
                        "mime_type": "audio/wav",
                        "data": audio_data
                    }
                ])
            
            # Extract summary text
            summary_text = response.text if hasattr(response, 'text') else str(response)
            
            return {
                "summary": summary_text,
                "filename": file.filename,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate summary with Gemini: {str(e)}"
            )
    
    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Processing timeout - video file may be too large or complex"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
    finally:
        # Cleanup temporary files
        try:
            if input_path and os.path.exists(input_path):
                os.unlink(input_path)
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

