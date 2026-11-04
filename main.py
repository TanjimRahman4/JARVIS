import os
import sys
import time
import platform
import webbrowser
import urllib.parse
from datetime import datetime
from pathlib import Path

import requests
import pyautogui
import pyttsx3
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "JARVIS"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"

try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
except Exception:
    webdriver = None
    ChromeOptions = None

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15

try:
    speaker = pyttsx3.init()
    speaker.setProperty("rate", 180)
except Exception:
    speaker = None

driver = None
conversation = [
    {
        "role": "system",
        "content": (
            "You are JARVIS, a practical Windows desktop assistant. "
            "Be concise, helpful, and honest. You cannot see the user's screen unless "
            "a screenshot or page text is explicitly provided. Never claim an action "
            "succeeded unless the program confirms it."
        ),
    }
]


def say(text: str) -> None:
    """Print and speak a response. TTS failure never stops the assistant."""
    print(f"\n{APP_NAME}: {text}\n")
    if speaker:
        try:
            speaker.say(text)
            speaker.runAndWait()
        except Exception:
            pass


def open_url(url: str) -> str:
    if not url.startswith(("https://", "http://")):
        url = "https://" + url
    opened = webbrowser.open(url)
    return f"Opened {url}." if opened else f"I tried to open {url}, but Windows did not confirm it."


def search_web(query: str) -> str:
    """Search DuckDuckGo HTML and extract readable result titles/snippets."""
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for item in soup.select(".result")[:5]:
            title_el = item.select_one(".result__title")
            snippet_el = item.select_one(".result__snippet")
            link_el = item.select_one(".result__url")
            title = title_el.get_text(" ", strip=True) if title_el else ""
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            link = link_el.get_text(" ", strip=True) if link_el else ""
            if title:
                results.append(f"- {title}\n  {snippet}\n  {link}")
        return "\n".join(results) if results else "No search results were extracted. The search site may have changed its page layout."
    except requests.RequestException as exc:
        return f"Web search failed: {exc}"


def scrape_page(url: str) -> str:
    if not url.startswith(("https://", "http://")):
        url = "https://" + url
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        title = soup.title.get_text(" ", strip=True) if soup.title else url
        text = " ".join(soup.get_text(" ", strip=True).split())
        return f"Page title: {title}\nURL: {url}\n\n{text[:5000]}"
    except requests.RequestException as exc:
        return f"Could not read that page: {exc}"


def launch_selenium(url: str = "https://www.google.com") -> str:
    global driver
    if webdriver is None:
        return "Selenium is not installed. Run: python -m pip install selenium"
    try:
        if driver is None:
            options = ChromeOptions()
            options.add_experimental_option("detach", True)
            driver = webdriver.Chrome(options=options)
        driver.get(url)
        return f"Selenium opened {driver.current_url}"
    except Exception as exc:
        return (
            f"Could not start Chrome with Selenium: {exc}\n"
            "Make sure Google Chrome is installed and update Selenium with: "
            "python -m pip install --upgrade selenium"
        )


def ask_ai(prompt: str) -> str:
    if not GROQ_API_KEY:
        return (
            "AI chat is not configured yet. Add your Groq API key to the .env file. "
            "I can still open websites, search the web, read pages, and run local commands."
        )
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        conversation.append({"role": "user", "content": prompt})
        # Keep the most recent turns so the request stays manageable.
        messages = [conversation[0]] + conversation[-12:]
        result = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=700,
        )
        answer = result.choices[0].message.content or "I didn't get a text response."
        conversation.append({"role": "assistant", "content": answer})
        return answer
    except Exception as exc:
        return f"AI request failed: {exc}"


def listen() -> str:
    if sr is None:
        say("Voice input is unavailable. Install SpeechRecognition and PyAudio, or type your command.")
        return ""
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening... (speak now)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=12)
        # Google Web Speech recognition does not need an API key, but requires internet.
        return recognizer.recognize_google(audio)
    except sr.WaitTimeoutError:
        return ""
    except Exception as exc:
        print(f"Voice input error: {exc}")
        return ""


def handle_command(raw: str) -> bool:
    """Return False to stop the main loop."""
    command = raw.strip()
    if not command:
        return True
    lower = command.lower()

    if lower in {"exit", "quit", "shutdown jarvis", "stop jarvis", "goodbye"}:
        say("Shutting down. Goodbye.")
        return False

    if lower in {"help", "commands", "what can you do"}:
        say(
            "Try: open youtube.com; search web for Python tutorials; read page https://example.com; "
            "selenium open https://google.com; type hello world; press enter; take screenshot; "
            "system status; what time is it; or ask me a question. Type voice to use the microphone."
        )
        return True

    if lower == "voice":
        spoken = listen()
        if spoken:
            print(f"You (voice): {spoken}")
            return handle_command(spoken)
        say("I didn't catch anything. Try again or type your command.")
        return True

    if lower in {"what time is it", "time", "current time"}:
        say(datetime.now().strftime("It is %I:%M %p on %A, %d %B %Y."))
        return True

    if lower in {"system status", "computer status", "pc status"}:
        import shutil
        total, used, free = shutil.disk_usage(Path.home().anchor)
        say(
            f"System: {platform.system()} {platform.release()}, {platform.machine()}. "
            f"Python {platform.python_version()}. Disk free on system drive: {free / (1024**3):.1f} GB."
        )
        return True

    if lower.startswith("open "):
        target = command[5:].strip()
        if " " not in target and "." in target:
            say(open_url(target))
        else:
            say(open_url("https://www.google.com/search?q=" + urllib.parse.quote_plus(target)))
        return True

    if lower.startswith("search web for "):
        query = command[len("search web for "):].strip()
        say(search_web(query))
        return True

    if lower.startswith("search "):
        query = command[len("search "):].strip()
        say(search_web(query))
        return True

    if lower.startswith("read page "):
        url = command[len("read page "):].strip()
        say(scrape_page(url))
        return True

    if lower.startswith("selenium open "):
        url = command[len("selenium open "):].strip()
        say(launch_selenium(url))
        return True

    if lower.startswith("type "):
        text_to_type = command[5:]
        try:
            pyautogui.write(text_to_type, interval=0.02)
            say("Typed the text into the currently focused window.")
        except Exception as exc:
            say(f"Typing failed: {exc}")
        return True

    if lower in {"press enter", "press tab", "press escape", "press esc"}:
        key = {"press enter": "enter", "press tab": "tab", "press escape": "esc", "press esc": "esc"}[lower]
        try:
            pyautogui.press(key)
            say(f"Pressed {key}.")
        except Exception as exc:
            say(f"Keyboard action failed: {exc}")
        return True

    if lower in {"take screenshot", "screenshot"}:
        try:
            folder = Path.home() / "Pictures" / "JARVIS"
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"screenshot_{datetime.now():%Y%m%d_%H%M%S}.png"
            pyautogui.screenshot().save(path)
            say(f"Screenshot saved to {path}")
        except Exception as exc:
            say(f"Screenshot failed: {exc}")
        return True

    # General questions go to the AI provider if configured.
    say(ask_ai(command))
    return True


def main() -> None:
    say("Online. Type help to see commands. Type voice to use your microphone, or type exit to quit.")
    while True:
        try:
            command = input("You: ")
            if not handle_command(command):
                break
        except KeyboardInterrupt:
            print()
            say("Stopped.")
            break
        except Exception as exc:
            say(f"An unexpected error occurred: {exc}")


if __name__ == "__main__":
    main()
