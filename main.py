"""
╔══════════════════════════════════════════════════════════════╗
║           BLUE OMEGA — Android AI Operating System          ║
║         Blue Intelligence and Learning Engine               ║
║              Python + Kivy | SQLite Memory                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, json, threading, sqlite3, time
from datetime import datetime

# ── Kivy Config (must be before kivy imports) ──────────────────
from kivy.config import Config
Config.set('graphics', 'resizable', True)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner

# Optional
try:
    import anthropic
    AI_OK = True
except ImportError:
    AI_OK = False

try:
    import speech_recognition as sr
    MIC_OK = True
except ImportError:
    MIC_OK = False

try:
    import pyttsx3
    TTS_OK = True
except ImportError:
    TTS_OK = False

try:
    import requests
    REQ_OK = True
except ImportError:
    REQ_OK = False

# ── Colors ────────────────────────────────────────────────────
BG      = (0.02, 0.04, 0.08, 1)
SURF    = (0.04, 0.08, 0.14, 1)
SURF2   = (0.06, 0.12, 0.20, 1)
BLUE    = (0.04, 0.52, 1.00, 1)
OMEGA   = (0.00, 0.90, 1.00, 1)
GREEN   = (0.00, 0.84, 0.56, 1)
RED     = (1.00, 0.42, 0.21, 1)
PURPLE  = (0.66, 0.33, 0.97, 1)
TEXT    = (0.78, 0.85, 0.94, 1)
TDIM    = (0.29, 0.42, 0.54, 1)
WHITE   = (1, 1, 1, 1)

# ── System Prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """YOU ARE BLUE OMEGA.
FULL NAME: Blue Intelligence and Learning Engine

ROLE: You are a complete AI operating system, personal mentor, educator, engineer, strategist, productivity coach, business advisor, coding assistant, and lifelong development partner.

PRIMARY MISSION: Help the user become highly educated, technically skilled, financially independent, disciplined, productive, ethical, a strong leader, and a successful engineer and creator. Always optimize for long-term growth rather than short-term comfort.

CORE PERSONALITY: Intelligent, Calm, Honest, Logical, Strategic, Respectful, Professional, Future-focused, Encouraging. Never arrogant. Never manipulative. Never misleading.

CORE OPERATING PRINCIPLES:
1. Identify the user's true goal.
2. Analyze available information.
3. Consider long-term consequences.
4. Find the highest-value solution.
5. Explain clearly.
6. Give actionable next steps.

RESPONSE STRUCTURE:
1. DIRECT ANSWER
2. DETAILED EXPLANATION
3. PRACTICAL EXAMPLE
4. ADVANTAGES
5. RISKS OR LIMITATIONS
6. RECOMMENDED ACTION
7. BLUE'S NEXT ACTION

MODES: Education, Engineering, Coding, AI Engineer, Entrepreneur, Productivity.
ETHICS: Never encourage illegal activity, fraud, cheating, or dishonesty.
FINAL RULE: Every interaction must move the user closer to their goals.
Always end with: BLUE'S NEXT ACTION: [Most important next step]
Speak warmly and naturally like a human mentor."""


# ══════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════
class BlueDB:
    def __init__(self):
        self.path = "blue_memory.db"
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self._init()

    def _init(self):
        c = self.conn
        c.execute("""CREATE TABLE IF NOT EXISTS settings
            (key TEXT PRIMARY KEY, value TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS messages
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             role TEXT, content TEXT,
             ts DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS goals
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             text TEXT, done INTEGER DEFAULT 0,
             ts DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS habits
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             text TEXT,
             ts DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS notes
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             title TEXT, content TEXT,
             ts DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        c.commit()

    def get(self, key, default=""):
        r = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r[0] if r else default

    def set(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, value))
        self.conn.commit()

    def add_message(self, role, content):
        self.conn.execute("INSERT INTO messages (role,content) VALUES (?,?)", (role, content))
        self.conn.commit()

    def get_goals(self):
        return self.conn.execute("SELECT id,text,done FROM goals ORDER BY id DESC").fetchall()

    def add_goal(self, text):
        self.conn.execute("INSERT INTO goals (text) VALUES (?)", (text,))
        self.conn.commit()

    def done_goal(self, gid):
        self.conn.execute("UPDATE goals SET done=1 WHERE id=?", (gid,))
        self.conn.commit()

    def del_goal(self, gid):
        self.conn.execute("DELETE FROM goals WHERE id=?", (gid,))
        self.conn.commit()

    def get_habits(self):
        return self.conn.execute("SELECT id,text FROM habits ORDER BY id DESC").fetchall()

    def add_habit(self, text):
        self.conn.execute("INSERT INTO habits (text) VALUES (?)", (text,))
        self.conn.commit()

    def del_habit(self, hid):
        self.conn.execute("DELETE FROM habits WHERE id=?", (hid,))
        self.conn.commit()


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════
def colored_btn(text, bg_color, text_color=WHITE, font_size=sp(14), **kwargs):
    btn = Button(
        text=text,
        font_size=font_size,
        background_normal='',
        background_color=bg_color,
        color=text_color,
        bold=True,
        **kwargs
    )
    return btn

def lbl(text, color=TEXT, size=sp(14), bold=False, halign="left", **kwargs):
    l = Label(
        text=text, color=color, font_size=size,
        bold=bold, halign=halign,
        text_size=(None, None),
        **kwargs
    )
    l.bind(size=lambda *a: setattr(l, 'text_size', (l.width, None)))
    return l

def dark_input(hint="", multiline=False, **kwargs):
    return TextInput(
        hint_text=hint,
        multiline=multiline,
        background_color=SURF2,
        foreground_color=TEXT,
        cursor_color=BLUE,
        hint_text_color=TDIM,
        font_size=sp(14),
        padding=[dp(12), dp(10)],
        **kwargs
    )


# ══════════════════════════════════════════════════════════════
#  SCREENS
# ══════════════════════════════════════════════════════════════

# ── Base Screen ───────────────────────────────────────────────
class BaseScreen(Screen):
    def __init__(self, db, app_ref, **kw):
        super().__init__(**kw)
        self.db = db
        self.app = app_ref
        with self.canvas.before:
            Color(*BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def nav_bar(self, current):
        bar = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(1))
        with bar.canvas.before:
            Color(*SURF)
            self._bar_rect = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda w,v: setattr(self._bar_rect,'pos',v),
                 size=lambda w,v: setattr(self._bar_rect,'size',v))

        pages = [("💬","chat"),("🎤","voice"),("🎯","goals"),("⚡","code"),("⚙️","settings")]
        for icon, name in pages:
            active = (name == current)
            b = colored_btn(icon, BLUE if active else SURF,
                            font_size=sp(20), size_hint_x=1)
            b.bind(on_press=lambda x, n=name: self.go(n))
            bar.add_widget(b)
        return bar

    def go(self, name):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = name

    def header(self, title="BLUE OMEGA"):
        hdr = BoxLayout(size_hint_y=None, height=dp(56), padding=[dp(16),0])
        with hdr.canvas.before:
            Color(*SURF)
            self._hdr_rect = Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda w,v: setattr(self._hdr_rect,'pos',v),
                 size=lambda w,v: setattr(self._hdr_rect,'size',v))

        hdr.add_widget(lbl("BΩ", color=OMEGA, size=sp(18), bold=True,
                           size_hint_x=None, width=dp(40)))
        hdr.add_widget(lbl(title, color=OMEGA, size=sp(16), bold=True))
        status = lbl("● ONLINE", color=GREEN, size=sp(11),
                     size_hint_x=None, width=dp(80), halign="right")
        hdr.add_widget(status)
        return hdr


# ══════════════════════════════════════════════════════════════
#  CHAT SCREEN
# ══════════════════════════════════════════════════════════════
class ChatScreen(BaseScreen):
    def __init__(self, db, app_ref, **kw):
        super().__init__(db, app_ref, name="chat", **kw)
        self.history = []
        self.is_busy = False
        self.client  = None
        self.tts_eng = None
        self._init_clients()
        self._build()

    def _init_clients(self):
        key = self.db.get("anthropic_key")
        if key and AI_OK:
            try: self.client = anthropic.Anthropic(api_key=key)
            except: pass
        if TTS_OK:
            try:
                self.tts_eng = pyttsx3.init()
                self.tts_eng.setProperty("rate", 155)
            except: pass

    def reload_client(self):
        self._init_clients()

    def _build(self):
        root = BoxLayout(orientation="vertical")

        # Header
        root.add_widget(self.header("Blue Omega — Chat"))

        # Mode selector
        modes = Spinner(
            text="General",
            values=["General","Education","Coding","Engineering","AI Engineer","Entrepreneur","Productivity"],
            size_hint_y=None, height=dp(40),
            background_color=SURF2, color=OMEGA,
            font_size=sp(13)
        )
        self.mode_spinner = modes
        root.add_widget(modes)

        # Chat display
        scroll = ScrollView()
        self.chat_layout = GridLayout(cols=1, spacing=dp(8),
                                      padding=[dp(12), dp(8)],
                                      size_hint_y=None)
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        scroll.add_widget(self.chat_layout)
        root.add_widget(scroll)
        self.scroll = scroll

        # Welcome bubble
        self._add_bubble("BΩ Blue", "Hello.\nBlue is online and ready.\nHow may I assist you today?", is_user=False)

        # Input area
        inp_bar = BoxLayout(size_hint_y=None, height=dp(60),
                            padding=[dp(8), dp(6)], spacing=dp(6))
        with inp_bar.canvas.before:
            Color(*SURF)
            self._inp_rect = Rectangle(pos=inp_bar.pos, size=inp_bar.size)
        inp_bar.bind(pos=lambda w,v: setattr(self._inp_rect,'pos',v),
                     size=lambda w,v: setattr(self._inp_rect,'size',v))

        self.inp = dark_input(hint="Blue-কে কিছু জিজ্ঞেস করো...", multiline=False)
        self.inp.bind(on_text_validate=lambda x: self._send())
        inp_bar.add_widget(self.inp)

        self.send_btn = colored_btn("▶", BLUE, size_hint_x=None, width=dp(52))
        self.send_btn.bind(on_press=lambda x: self._send())
        inp_bar.add_widget(self.send_btn)

        root.add_widget(inp_bar)
        root.add_widget(self.nav_bar("chat"))
        self.add_widget(root)

    def _add_bubble(self, name, text, is_user=True):
        bubble = BoxLayout(orientation="vertical",
                           size_hint_y=None,
                           padding=[dp(12), dp(8)],
                           spacing=dp(4))

        name_lbl = lbl(name,
                       color=BLUE if is_user else OMEGA,
                       size=sp(11), bold=True)
        name_lbl.size_hint_y = None
        name_lbl.height = dp(18)

        msg_lbl = lbl(text, color=TEXT, size=sp(13))
        msg_lbl.size_hint_y = None

        bubble.add_widget(name_lbl)
        bubble.add_widget(msg_lbl)

        with bubble.canvas.before:
            Color(*(SURF2 if is_user else SURF))
            self._b_rect = RoundedRectangle(pos=bubble.pos, size=bubble.size, radius=[dp(10)])
        bubble.bind(
            pos=lambda w, v: setattr(self._b_rect, 'pos', v),
            size=lambda w, v: (setattr(self._b_rect, 'size', v),
                               setattr(msg_lbl, 'text_size', (w.width - dp(24), None)),
                               Clock.schedule_once(lambda dt: setattr(bubble, 'height',
                                   name_lbl.height + msg_lbl.texture_size[1] + dp(24)), 0.05))
        )

        bubble.height = dp(80)
        self.chat_layout.add_widget(bubble)
        Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1)
        return msg_lbl

    def _send(self, text=None):
        if self.is_busy: return
        msg = text or self.inp.text.strip()
        if not msg: return
        if not self.client:
            self._add_bubble("⚠️ System", "Settings এ Anthropic API Key দাও!", is_user=False)
            return
        self.inp.text = ""
        self._add_bubble("তুমি", msg, is_user=True)
        mode = self.mode_spinner.text
        self.history.append({"role":"user","content":f"[{mode} Mode] {msg}"})
        self.db.add_message("user", msg)
        self.is_busy = True
        self.send_btn.text = "..."
        self.send_btn.disabled = True
        self._thinking_lbl = self._add_bubble("BΩ Blue", "ভাবছি...", is_user=False)
        threading.Thread(target=self._api, daemon=True).start()

    def _api(self):
        try:
            r = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=self.history)
            reply = r.content[0].text
            self.history.append({"role":"assistant","content":reply})
            self.db.add_message("assistant", reply)
            Clock.schedule_once(lambda dt: self._show(reply), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show(f"Error: {e}"), 0)

    def _show(self, reply):
        self.chat_layout.remove_widget(self.chat_layout.children[0])
        self._add_bubble("BΩ Blue", reply, is_user=False)
        self.is_busy = False
        self.send_btn.text = "▶"
        self.send_btn.disabled = False

        # Speak
        voice_on = self.db.get("voice_on","0") == "1"
        if voice_on:
            speak_text = reply[:500]
            eleven_key = self.db.get("eleven_key","")
            if eleven_key and REQ_OK:
                threading.Thread(target=self._eleven, args=(speak_text, eleven_key), daemon=True).start()
            elif self.tts_eng:
                threading.Thread(target=self._pyttsx, args=(speak_text,), daemon=True).start()

    def _eleven(self, text, key):
        voice_id = "21m00Tcm4TlvDq8ikWAM"
        try:
            import tempfile, pygame
            r = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={"xi-api-key":key,"Content-Type":"application/json","Accept":"audio/mpeg"},
                json={"text":text,"model_id":"eleven_monolingual_v1",
                      "voice_settings":{"stability":0.5,"similarity_boost":0.75}},
                timeout=15)
            if r.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                    f.write(r.content); tmp = f.name
                pygame.mixer.init()
                pygame.mixer.music.load(tmp)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy(): time.sleep(0.1)
        except: self._pyttsx(text)

    def _pyttsx(self, text):
        try:
            if self.tts_eng:
                self.tts_eng.say(text)
                self.tts_eng.runAndWait()
        except: pass

    def send_external(self, text):
        Clock.schedule_once(lambda dt: self._send(text), 0.1)


# ══════════════════════════════════════════════════════════════
#  VOICE SCREEN
# ══════════════════════════════════════════════════════════════
class VoiceScreen(BaseScreen):
    def __init__(self, db, app_ref, **kw):
        super().__init__(db, app_ref, name="voice", **kw)
        self.listening = False
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.header("Voice Assistant"))

        content = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))

        content.add_widget(lbl("🎤 Voice Assistant", color=OMEGA, size=sp(22),
                               bold=True, halign="center"))
        content.add_widget(lbl("কথা বলো — Blue শুনবে ও উত্তর দেবে",
                               color=TDIM, size=sp(13), halign="center"))

        # Status
        self.status_lbl = lbl("● Voice OFF", color=TDIM, size=sp(16),
                               bold=True, halign="center")
        content.add_widget(self.status_lbl)

        # Toggle voice
        self.toggle_btn = colored_btn("🎤  Voice চালু করো", BLUE,
                                      size_hint_y=None, height=dp(54))
        self.toggle_btn.bind(on_press=self._toggle)
        content.add_widget(self.toggle_btn)

        # Mic button
        self.mic_btn = colored_btn("🎙  কথা বলো", SURF2,
                                   size_hint_y=None, height=dp(54))
        self.mic_btn.disabled = True
        self.mic_btn.bind(on_press=self._listen)
        content.add_widget(self.mic_btn)

        # Transcript
        content.add_widget(lbl("Transcript", color=TDIM, size=sp(11)))
        self.transcript = dark_input(hint="এখানে তোমার কথা দেখাবে...",
                                     multiline=True, readonly=True,
                                     size_hint_y=None, height=dp(120))
        content.add_widget(self.transcript)

        # ElevenLabs key
        content.add_widget(lbl("🎙 ElevenLabs Key (Human Voice):", color=OMEGA, size=sp(12)))
        self.eleven_entry = dark_input(hint="sk-... (elevenlabs.io থেকে নাও)",
                                       size_hint_y=None, height=dp(44),
                                       password=True)
        self.eleven_entry.text = self.db.get("eleven_key","")
        content.add_widget(self.eleven_entry)

        save_btn = colored_btn("💾  Save Key", PURPLE, size_hint_y=None, height=dp(44))
        save_btn.bind(on_press=self._save_eleven)
        content.add_widget(save_btn)

        root.add_widget(content)
        root.add_widget(self.nav_bar("voice"))
        self.add_widget(root)

        # Update status
        if self.db.get("voice_on","0") == "1":
            self._set_voice_on()

    def _toggle(self, *a):
        is_on = self.db.get("voice_on","0") == "1"
        if is_on:
            self.db.set("voice_on","0")
            self.status_lbl.text = "● Voice OFF"
            self.status_lbl.color = TDIM
            self.toggle_btn.text = "🎤  Voice চালু করো"
            self.toggle_btn.background_color = BLUE
            self.mic_btn.disabled = True
        else:
            self._set_voice_on()

    def _set_voice_on(self):
        self.db.set("voice_on","1")
        self.status_lbl.text = "● Voice ON"
        self.status_lbl.color = GREEN
        self.toggle_btn.text = "🔇  Voice বন্ধ করো"
        self.toggle_btn.background_color = SURF2
        self.mic_btn.disabled = False

    def _save_eleven(self, *a):
        key = self.eleven_entry.text.strip()
        self.db.set("eleven_key", key)
        popup = Popup(title="Saved!", size_hint=(.6,.3),
                      content=lbl("ElevenLabs key saved!", halign="center"))
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)

    def _listen(self, *a):
        if not MIC_OK:
            self.transcript.text = "Error: pip install SpeechRecognition\n"
            return
        self.mic_btn.text = "🔴 শুনছি..."
        self.mic_btn.background_color = RED
        threading.Thread(target=self._do_listen, daemon=True).start()

    def _do_listen(self):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as src:
                r.adjust_for_ambient_noise(src, duration=0.4)
                audio = r.listen(src, timeout=8, phrase_time_limit=15)
            text = r.recognize_google(audio, language="bn-BD,en-US")
            Clock.schedule_once(lambda dt: self._got(text), 0)
        except sr.WaitTimeoutError:
            Clock.schedule_once(lambda dt: self._err("কোনো শব্দ পাইনি।"), 0)
        except sr.UnknownValueError:
            Clock.schedule_once(lambda dt: self._err("বুঝতে পারিনি, আবার বলো।"), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._err(str(e)), 0)

    def _got(self, text):
        self.mic_btn.text = "🎙  কথা বলো"
        self.mic_btn.background_color = BLUE
        self.transcript.text += f"তুমি: {text}\n"
        # Send to chat
        chat = self.manager.get_screen("chat")
        chat.send_external(text)
        self.manager.current = "chat"

    def _err(self, e):
        self.mic_btn.text = "🎙  কথা বলো"
        self.mic_btn.background_color = BLUE
        self.transcript.text += f"Error: {e}\n"


# ══════════════════════════════════════════════════════════════
#  GOALS SCREEN
# ══════════════════════════════════════════════════════════════
class GoalsScreen(BaseScreen):
    def __init__(self, db, app_ref, **kw):
        super().__init__(db, app_ref, name="goals", **kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.header("Goals & Habits"))

        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))

        # Goals section
        content.add_widget(lbl("🎯 Goals", color=OMEGA, size=sp(16), bold=True))

        add_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.goal_inp = dark_input(hint="নতুন goal লিখো...")
        self.goal_inp.bind(on_text_validate=lambda x: self._add_goal())
        add_row.add_widget(self.goal_inp)
        add_btn = colored_btn("+", BLUE, size_hint_x=None, width=dp(44))
        add_btn.bind(on_press=lambda x: self._add_goal())
        add_row.add_widget(add_btn)
        content.add_widget(add_row)

        scroll_g = ScrollView(size_hint_y=0.35)
        self.goals_layout = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=[0,4])
        self.goals_layout.bind(minimum_height=self.goals_layout.setter('height'))
        scroll_g.add_widget(self.goals_layout)
        content.add_widget(scroll_g)

        # Habits section
        content.add_widget(lbl("🔁 Daily Habits", color=OMEGA, size=sp(16), bold=True))

        add_row2 = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.habit_inp = dark_input(hint="নতুন habit লিখো...")
        self.habit_inp.bind(on_text_validate=lambda x: self._add_habit())
        add_row2.add_widget(self.habit_inp)
        add_btn2 = colored_btn("+", BLUE, size_hint_x=None, width=dp(44))
        add_btn2.bind(on_press=lambda x: self._add_habit())
        add_row2.add_widget(add_btn2)
        content.add_widget(add_row2)

        scroll_h = ScrollView(size_hint_y=0.25)
        self.habits_layout = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=[0,4])
        self.habits_layout.bind(minimum_height=self.habits_layout.setter('height'))
        scroll_h.add_widget(self.habits_layout)
        content.add_widget(scroll_h)

        # AI Coach button
        coach_btn = colored_btn("🤖  AI Coach — আমাকে গাইড করো", PURPLE,
                                size_hint_y=None, height=dp(48))
        coach_btn.bind(on_press=self._ai_coach)
        content.add_widget(coach_btn)

        root.add_widget(content)
        root.add_widget(self.nav_bar("goals"))
        self.add_widget(root)
        self._refresh()

    def on_enter(self):
        self._refresh()

    def _refresh(self):
        self.goals_layout.clear_widgets()
        for gid, text, done in self.db.get_goals():
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            icon = "✅" if done else "○"
            row.add_widget(lbl(f"{icon}  {text}", color=GREEN if done else TEXT,
                               size=sp(13)))
            if not done:
                d_btn = colored_btn("✓", GREEN, size_hint_x=None, width=dp(36),
                                    font_size=sp(12))
                d_btn.bind(on_press=lambda x, g=gid: self._done(g))
                row.add_widget(d_btn)
            x_btn = colored_btn("✕", RED, size_hint_x=None, width=dp(36),
                                font_size=sp(12))
            x_btn.bind(on_press=lambda x, g=gid: self._del_goal(g))
            row.add_widget(x_btn)
            self.goals_layout.add_widget(row)

        self.habits_layout.clear_widgets()
        for hid, text in self.db.get_habits():
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            row.add_widget(lbl(f"🔁  {text}", color=TEXT, size=sp(13)))
            x_btn = colored_btn("✕", RED, size_hint_x=None, width=dp(36),
                                font_size=sp(12))
            x_btn.bind(on_press=lambda x, h=hid: self._del_habit(h))
            row.add_widget(x_btn)
            self.habits_layout.add_widget(row)

    def _add_goal(self):
        t = self.goal_inp.text.strip()
        if t:
            self.db.add_goal(t)
            self.goal_inp.text = ""
            self._refresh()

    def _done(self, gid):
        self.db.done_goal(gid); self._refresh()

    def _del_goal(self, gid):
        self.db.del_goal(gid); self._refresh()

    def _add_habit(self):
        t = self.habit_inp.text.strip()
        if t:
            self.db.add_habit(t)
            self.habit_inp.text = ""
            self._refresh()

    def _del_habit(self, hid):
        self.db.del_habit(hid); self._refresh()

    def _ai_coach(self, *a):
        goals = "\n".join([f"- {t}" for _, t, _ in self.db.get_goals()]) or "কোনো goal নেই"
        habits = "\n".join([f"- {t}" for _, t in self.db.get_habits()]) or "কোনো habit নেই"
        msg = f"আমার goals:\n{goals}\n\nআমার habits:\n{habits}\n\nআমাকে personalized coaching plan দাও।"
        chat = self.manager.get_screen("chat")
        chat.send_external(msg)
        self.manager.current = "chat"


# ══════════════════════════════════════════════════════════════
#  CODE SCREEN
# ══════════════════════════════════════════════════════════════
class CodeScreen(BaseScreen):
    def __init__(self, db, app_ref, **kw):
        super().__init__(db, app_ref, name="code", **kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.header("Python Code Runner"))

        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))

        content.add_widget(lbl("⚡ Python Code Runner", color=OMEGA, size=sp(16), bold=True))

        # Editor
        content.add_widget(lbl("Editor:", color=TDIM, size=sp(11)))
        self.editor = TextInput(
            text='# Blue Omega Code Runner\nprint("Hello from Blue Omega!")\n',
            multiline=True,
            background_color=SURF,
            foreground_color=(0.48, 0.83, 0.98, 1),
            cursor_color=BLUE,
            font_name="RobotoMono-Regular",
            font_size=sp(12),
            padding=[dp(12), dp(8)],
            size_hint_y=0.45
        )
        content.add_widget(self.editor)

        # Buttons
        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        for txt, col, cmd in [
            ("▶ Run",        GREEN,  self._run),
            ("🗑 Clear",     SURF2,  self._clr),
            ("🤖 AI Review", BLUE,   self._review),
        ]:
            b = colored_btn(txt, col, size_hint_x=1)
            b.bind(on_press=lambda x, c=cmd: c())
            btn_row.add_widget(b)
        content.add_widget(btn_row)

        # Output
        content.add_widget(lbl("Output:", color=TDIM, size=sp(11)))
        self.output = TextInput(
            multiline=True, readonly=True,
            background_color=(0.01, 0.05, 0.10, 1),
            foreground_color=GREEN,
            font_name="RobotoMono-Regular",
            font_size=sp(12),
            padding=[dp(12), dp(8)],
            size_hint_y=0.35
        )
        content.add_widget(self.output)

        root.add_widget(content)
        root.add_widget(self.nav_bar("code"))
        self.add_widget(root)

    def _run(self):
        import subprocess, sys
        code = self.editor.text.strip()
        if not code: return
        try:
            r = subprocess.run([sys.executable, "-c", code],
                               capture_output=True, text=True, timeout=15)
            self.output.text = r.stdout or ""
            if r.stderr: self.output.text += f"\n[Error]\n{r.stderr}"
            if not r.stdout and not r.stderr: self.output.text = "(কোনো output নেই)"
        except subprocess.TimeoutExpired:
            self.output.text = "[Timeout]"
        except Exception as e:
            self.output.text = f"[Error] {e}"

    def _clr(self):
        self.editor.text = ""
        self.output.text = ""

    def _review(self):
        code = self.editor.text.strip()
        if not code: return
        chat = self.manager.get_screen("chat")
        chat.send_external(f"এই Python কোড review করো:\n```python\n{code}\n```\nBug খোঁজো, উন্নতি করো।")
        self.manager.current = "chat"


# ══════════════════════════════════════════════════════════════
#  SETTINGS SCREEN
# ══════════════════════════════════════════════════════════════
class SettingsScreen(BaseScreen):
    def __init__(self, db, app_ref, **kw):
        super().__init__(db, app_ref, name="settings", **kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.header("Settings"))

        scroll = ScrollView()
        content = GridLayout(cols=1, padding=dp(20), spacing=dp(12), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # Anthropic Key
        content.add_widget(lbl("🔑 Anthropic API Key", color=BLUE, size=sp(14), bold=True))
        content.add_widget(lbl("console.anthropic.com → Sign Up → API Keys",
                               color=TDIM, size=sp(11)))
        self.ant_key = dark_input(hint="sk-ant-...", password=True,
                                  size_hint_y=None, height=dp(44))
        self.ant_key.text = self.db.get("anthropic_key","")
        content.add_widget(self.ant_key)

        save1 = colored_btn("✅  Save & Connect", BLUE, size_hint_y=None, height=dp(46))
        save1.bind(on_press=self._save_anthropic)
        content.add_widget(save1)

        # ElevenLabs Key
        content.add_widget(Widget(size_hint_y=None, height=dp(8)))
        content.add_widget(lbl("🎙 ElevenLabs API Key (Human Voice)", color=PURPLE, size=sp(14), bold=True))
        content.add_widget(lbl("elevenlabs.io → Free Sign Up → Profile → API Key",
                               color=TDIM, size=sp(11)))
        self.el_key = dark_input(hint="sk-... (free tier available)", password=True,
                                 size_hint_y=None, height=dp(44))
        self.el_key.text = self.db.get("eleven_key","")
        content.add_widget(self.el_key)

        save2 = colored_btn("✅  Save ElevenLabs Key", PURPLE, size_hint_y=None, height=dp(46))
        save2.bind(on_press=self._save_eleven)
        content.add_widget(save2)

        # App info
        content.add_widget(Widget(size_hint_y=None, height=dp(8)))
        content.add_widget(lbl("ℹ️ App Info", color=GREEN, size=sp(14), bold=True))
        for line in ["Blue Omega v3.0","Python + Kivy","Claude Sonnet AI","ElevenLabs Human Voice","SQLite Memory"]:
            content.add_widget(lbl(f"  • {line}", color=TEXT, size=sp(13)))

        scroll.add_widget(content)
        root.add_widget(scroll)
        root.add_widget(self.nav_bar("settings"))
        self.add_widget(root)

    def _save_anthropic(self, *a):
        key = self.ant_key.text.strip()
        if not key:
            self._popup("⚠️", "API Key দাও!"); return
        self.db.set("anthropic_key", key)
        # Reload chat client
        chat = self.manager.get_screen("chat")
        chat.reload_client()
        self._popup("✅ Connected!", "Anthropic API Connected!\nBlue এখন কথা বলতে পারবে।")

    def _save_eleven(self, *a):
        key = self.el_key.text.strip()
        self.db.set("eleven_key", key)
        self._popup("✅ Saved!", "ElevenLabs key saved!")

    def _popup(self, title, msg):
        p = Popup(title=title, size_hint=(.75,.3),
                  content=lbl(msg, halign="center"))
        p.open()
        Clock.schedule_once(lambda dt: p.dismiss(), 2)


# ══════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════
class BlueOmegaApp(App):
    def build(self):
        self.title = "Blue Omega"
        Window.clearcolor = BG

        self.db = BlueDB()

        sm = ScreenManager()
        sm.add_widget(ChatScreen(self.db, self))
        sm.add_widget(VoiceScreen(self.db, self))
        sm.add_widget(GoalsScreen(self.db, self))
        sm.add_widget(CodeScreen(self.db, self))
        sm.add_widget(SettingsScreen(self.db, self))

        sm.current = "chat"
        return sm


if __name__ == "__main__":
    BlueOmegaApp().run()
