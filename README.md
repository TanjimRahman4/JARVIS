# JARVIS Python Desktop Assistant

A practical Windows starter assistant with:
- Text-to-speech responses (`pyttsx3`)
- Optional microphone input (`SpeechRecognition` + `PyAudio`)
- AI answers through Groq (optional API key)
- Web search and page text extraction (`requests` + `BeautifulSoup`)
- Chrome automation (`Selenium`)
- Basic desktop typing and screenshots (`PyAutoGUI`)

## 1. Install Python packages

Open PowerShell in this folder:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `PyAudio` fails to install, the rest of JARVIS can still work; remove `PyAudio` from the command and use typed commands. Voice input requires a working microphone and PyAudio.

## 2. Configure AI (optional)

Copy `.env.example` to `.env`, then add your own Groq API key:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Never share your API key or upload your `.env` file to GitHub.

## 3. Run

```powershell
python main.py
```

Type `help` to see commands.

## Commands

- `open youtube.com`
- `open notepad` (searches the web for the phrase; it does not launch arbitrary apps)
- `search web for Python tutorials`
- `read page https://example.com`
- `selenium open https://www.google.com`
- `type Hello from JARVIS`
- `press enter`
- `take screenshot`
- `system status`
- `what time is it`
- `voice`
- `exit`

## Important notes

- `PyAutoGUI` types into whichever window currently has focus. Click the intended text field first.
- Move the mouse to the top-left corner of the screen to trigger PyAutoGUI's fail-safe stop.
- Selenium requires Google Chrome. Recent Selenium versions normally manage ChromeDriver automatically.
- Some websites block automated requests or render content with JavaScript; `read page` may not capture those pages. Use `selenium open` for a browser-based check.
- The microphone recognizer uses Google's online speech recognition service, so internet is required.
- This starter intentionally does not execute arbitrary terminal commands, delete files, or send messages without user review.
