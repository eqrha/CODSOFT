import threading
import re
import tkinter as tk
from tkinter import messagebox
import queue
import time

# Speech + TTS (may require installation)
import speech_recognition as sr
import pyttsx3

# ---------------------------
# Utility: safe eval for math
# ---------------------------
ALLOWED_CHARS_RE = re.compile(r'^[0-9\s\.\+\-\*\/\(\)]+$')

def safe_eval(expr: str):
    # remove spaces
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty expression")
    # basic safety check: only allow digits, operators, parentheses, dot and spaces
    if not ALLOWED_CHARS_RE.match(expr):
        raise ValueError("Disallowed characters in expression.")
    # Evaluate
    try:
        # eval is safe-ish here because we've restricted characters above
        return eval(expr, {"__builtins__": None}, {})
    except Exception as e:
        raise

# ---------------------------
# Text -> expression parsing
# ---------------------------
# Basic mapping for operator words
OP_MAP = {
    'plus': '+', 'add': '+', 'added': '+',
    'minus': '-', 'subtract': '-', 'less': '-',
    'times': '*', 'x': '*', 'multiply': '*', 'multiplied': '*',
    'into': '*',
    'divide': '/', 'divided': '/', 'over': '/',
    'by': '/',  # often appears in 'divided by' - handled contextually
    'mod': '%', 'modulo': '%'
}

# Basic words to numbers (0-19)
NUM_WORDS = {
    'zero':0, 'one':1, 'two':2, 'three':3, 'four':4, 'five':5, 'six':6,
    'seven':7, 'eight':8, 'nine':9, 'ten':10, 'eleven':11, 'twelve':12,
    'thirteen':13, 'fourteen':14, 'fifteen':15, 'sixteen':16, 'seventeen':17,
    'eighteen':18, 'nineteen':19
}
TENS = {
    'twenty':20, 'thirty':30, 'forty':40, 'fifty':50,
    'sixty':60, 'seventy':70, 'eighty':80, 'ninety':90
}

def words_to_number(tokens, i):
    """
    Try to parse a number starting at tokens[i].
    Returns (number_as_string, new_index)
    Example: tokens = ['twenty', 'one'] -> returns ('21', i+2)
    Handles decimals with the word 'point'.
    """
    num = 0
    consumed = 0
    got_any = False
    # Handle optional sign words (not common, but keep)
    if tokens[i] in ('negative', 'minus') and i+1 < len(tokens):
        # parse next token as number then negate
        sub_num_str, new_i = words_to_number(tokens, i+1)
        return ('-' + sub_num_str, new_i)

    # units / teens
    if tokens[i] in NUM_WORDS:
        num += NUM_WORDS[tokens[i]]
        consumed += 1
        got_any = True
        i2 = i + 1
        # look ahead for "point" or more tens/units (like "twenty one" would be handled elsewhere)
        return (str(num), i + consumed)

    # tens like twenty one
    if tokens[i] in TENS:
        num += TENS[tokens[i]]
        consumed += 1
        got_any = True
        # possible unit after tens
        if i+1 < len(tokens) and tokens[i+1] in NUM_WORDS:
            num += NUM_WORDS[tokens[i+1]]
            consumed += 1
        return (str(num), i + consumed)

    # pure digits (like '5' or '12')
    if re.fullmatch(r'\d+(\.\d+)?', tokens[i]):
        return (tokens[i], i+1)

    # decimal handling if token is 'point'
    if tokens[i] == 'point' and i+1 < len(tokens) and re.fullmatch(r'\d+', tokens[i+1]):
        # ".5" style, but we want "0.5"
        decimals = []
        j = i+1
        while j < len(tokens) and re.fullmatch(r'\d+', tokens[j]):
            decimals.append(tokens[j])
            j += 1
        return ('0.' + ''.join(decimals), j)

    # try to parse number like "one hundred twenty three"
    # limited support: hundred and thousand
    if tokens[i] in NUM_WORDS or tokens[i] in TENS:
        j = i
        val = 0
        while j < len(tokens):
            tok = tokens[j]
            if tok in NUM_WORDS:
                val += NUM_WORDS[tok]
            elif tok in TENS:
                val += TENS[tok]
            elif tok == 'hundred':
                if val == 0:
                    val = 100
                else:
                    val *= 100
            elif tok == 'thousand':
                if val == 0:
                    val = 1000
                else:
                    val *= 1000
            elif tok == 'point':
                # parse remainder digits as decimals
                j2 = j+1
                decimals = []
                while j2 < len(tokens) and (tokens[j2].isdigit() or tokens[j2] in NUM_WORDS):
                    if tokens[j2].isdigit():
                        decimals.append(tokens[j2])
                    else:
                        decimals.append(str(NUM_WORDS.get(tokens[j2], '0')))
                    j2 += 1
                if decimals:
                    return (str(val) + '.' + ''.join(decimals), j2)
                else:
                    return (str(val), j)
            else:
                break
            j += 1
        if j > i:
            return (str(val), j)

    return (None, i)

def text_to_expression(text: str) -> str:
    """
    Convert spoken text into a math expression string.
    Examples:
      "five plus seven" -> "5+7"
      "what is twelve divided by three point five" -> "12/3.5"
    """
    # normalize
    t = text.lower()
    # remove filler words
    t = t.replace('-', ' ')
    t = re.sub(r"[^a-z0-9\.\s\%]+", " ", t)  # keep letters, digits, dot, percent
    t = re.sub(r'\b(what is|calculate|compute|equals|=|answer|please|hey|ok|please)\b', ' ', t)
    tokens = t.split()
    out = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        # operator words
        if tok in OP_MAP:
            op = OP_MAP[tok]
            # special case: 'by' often in 'divided by' - if previous token was 'divide' we already added '/'
            if tok == 'by':
                # skip if last output was operator
                if out and out[-1] in '+-*/%':
                    i += 1
                    continue
                else:
                    # ambiguous - treat as '/'
                    out.append('/')
                    i += 1
                    continue
            out.append(op)
            i += 1
            continue

        # try to parse a number (words or digits)
        num_str, new_i = words_to_number(tokens, i)
        if num_str is not None:
            out.append(num_str)
            i = new_i
            continue

        # if token looks like a direct arithmetic operator symbol
        if re.fullmatch(r'[\+\-\*\/\(\)\%\.]', tok):
            out.append(tok)
            i += 1
            continue

        # token is maybe a digit like '5' or '3.14'
        if re.fullmatch(r'\d+(\.\d+)?', tok):
            out.append(tok)
            i += 1
            continue

        # ignore unknown filler words
        i += 1

    # join but ensure spacing between numbers/operators as needed
    expr = ""
    for part in out:
        # avoid things like '5' '10' merging: add operator or space if both numbers in a row -> add '*'? no: add space so safe_eval will reject if required
        expr += (part if expr == "" else (' ' + part if (re.match(r'^\d', part) and re.match(r'\d$', expr[-1])) else part if part in '+-*/%()' else part))
    # final cleanup: remove spaces for evaluation, but keep safe chars
    expr_clean = re.sub(r'\s+', '', expr)
    return expr_clean

# ---------------------------
# Speech recognition (tries pocketsphinx offline, else google)
# ---------------------------
def recognize_speech_from_mic(recognizer, microphone, timeout=6, phrase_time_limit=6):
    """
    Returns a dict: {"success":bool, "error": None or string, "transcription": None or str}
    Tries pocketsphinx offline first if available, else uses Google (online).
    """
    if not isinstance(recognizer, sr.Recognizer):
        raise ValueError("Recognizer must be sr.Recognizer instance")
    if not isinstance(microphone, sr.Microphone):
        raise ValueError("Microphone must be sr.Microphone instance")

    response = {"success": True, "error": None, "transcription": None}

    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    except sr.WaitTimeoutError:
        response["success"] = False
        response["error"] = "Listening timed out while waiting for phrase to start"
        return response
    except Exception as e:
        response["success"] = False
        response["error"] = f"Microphone error: {e}"
        return response

    # try pocketsphinx offline
    try:
        transcription = recognizer.recognize_sphinx(audio)
        response["transcription"] = transcription
        return response
    except Exception:
        # fallback to google online
        try:
            transcription = recognizer.recognize_google(audio)
            response["transcription"] = transcription
            return response
        except sr.RequestError:
            response["success"] = False
            response["error"] = "API unavailable/unresponsive (Google) and pocketsphinx failed or not installed."
            return response
        except sr.UnknownValueError:
            response["success"] = False
            response["error"] = "Unable to recognize speech"
            return response

# ---------------------------
# GUI App
# ---------------------------
class VoiceCalculatorApp:
    def __init__(self, root):
        self.root = root
        root.title("Voice Calculator")
        root.resizable(False, False)
        self.style_setup()

        # display (expression)
        self.display_var = tk.StringVar()
        self.display = tk.Entry(root, textvariable=self.display_var, font=("Segoe UI", 20), bd=8, relief=tk.RIDGE, justify='right', width=18)
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=12)

        # secondary label: shows spoken sentence
        self.spoken_var = tk.StringVar()
        self.spoken_lbl = tk.Label(root, textvariable=self.spoken_var, font=("Segoe UI", 9), anchor='w', fg='gray')
        self.spoken_lbl.grid(row=1, column=0, columnspan=4, sticky='w', padx=12)

        # buttons layout (calculator style)
        btn_texts = [
            ('7','8','9','/'),
            ('4','5','6','*'),
            ('1','2','3','-'),
            ('0','.','%','+'),
        ]
        for r, row in enumerate(btn_texts, start=2):
            for c, txt in enumerate(row):
                b = tk.Button(root, text=txt, font=("Segoe UI", 16), width=5, height=2,
                              command=lambda t=txt: self.on_button(t))
                b.grid(row=r, column=c, padx=4, pady=4)

        # equals, clear, voice, speak result
        eq = tk.Button(root, text='=', font=("Segoe UI", 16), width=11, height=2, command=self.calculate)
        eq.grid(row=6, column=0, columnspan=2, padx=4, pady=6)

        clear = tk.Button(root, text='C', font=("Segoe UI", 16), width=5, height=2, command=self.clear)
        clear.grid(row=6, column=2, padx=4, pady=6)

        voice = tk.Button(root, text='🎤', font=("Segoe UI", 16), width=5, height=2, command=self.start_listen_thread)
        voice.grid(row=6, column=3, padx=4, pady=6)

        # status label
        self.status_var = tk.StringVar(value="Ready")
        status_lbl = tk.Label(root, textvariable=self.status_var, font=("Segoe UI", 9), anchor='w', fg='blue')
        status_lbl.grid(row=7, column=0, columnspan=4, sticky='w', padx=10, pady=(0,8))

        # speech engine
        self.engine = pyttsx3.init()
        # queue for thread results
        self.queue = queue.Queue()

        # speech recognizer & mic
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
        except Exception as e:
            self.microphone = None
            messagebox.showwarning("Microphone", f"Microphone not found or accessible: {e}")

        # poll queue periodically
        self.root.after(200, self.process_queue)

    def style_setup(self):
        self.root.configure(padx=6, pady=6, bg="#f5f5f5")

    # button press handler
    def on_button(self, char):
        cur = self.display_var.get()
        if char == '%':
            # modulo -> treat as %
            self.display_var.set(cur + '%')
        else:
            self.display_var.set(cur + char)

    def clear(self):
        self.display_var.set("")
        self.spoken_var.set("")
        self.status_var.set("Cleared")

    def calculate(self):
        expr = self.display_var.get()
        expr = expr.replace('×', '*').replace('÷', '/')
        # replace percent operator if present: convert "a%b" -> a % b (python uses %)
        expr = expr.replace('%', '%')
        try:
            result = safe_eval(expr)
            self.display_var.set(str(result))
            self.status_var.set("Computed")
            self.speak_text(f"The result is {result}")
        except Exception as e:
            self.status_var.set("Error")
            messagebox.showerror("Error", f"Could not evaluate: {e}")

    def start_listen_thread(self):
        if not self.microphone:
            messagebox.showerror("Microphone", "Microphone is not available.")
            return
        # launch recognition in a thread
        t = threading.Thread(target=self._listen_and_process, daemon=True)
        t.start()
        self.status_var.set("Listening... (sphinx if installed, else Google)")

    def _listen_and_process(self):
        # do recognition (blocking) and put results to queue
        res = recognize_speech_from_mic(self.recognizer, self.microphone)
        self.queue.put(('recognized', res))

    def process_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                tag, payload = item
                if tag == 'recognized':
                    res = payload
                    if not res['success']:
                        self.status_var.set("Recognition failed")
                        if res.get('error'):
                            messagebox.showerror("Speech Recognition", res['error'])
                        continue
                    transcription = res.get('transcription', '')
                    self.spoken_var.set("Heard: " + transcription)
                    self.status_var.set("Parsing...")
                    expr = text_to_expression(transcription)
                    if not expr:
                        self.status_var.set("Could not parse speech to expression")
                        messagebox.showerror("Parse Error", "Couldn't parse the spoken math expression.")
                        continue
                    # show expression in display
                    self.display_var.set(expr)
                    self.status_var.set("Evaluating...")
                    try:
                        result = safe_eval(expr)
                        self.display_var.set(str(result))
                        self.status_var.set("Done")
                        self.speak_text(f"The result is {result}")
                    except Exception as e:
                        self.status_var.set("Evaluation error")
                        messagebox.showerror("Evaluation Error", f"Could not compute '{expr}': {e}")
                else:
                    pass
        except queue.Empty:
            pass
        # keep polling
        self.root.after(200, self.process_queue)

    def speak_text(self, text):
        # speak in background thread to avoid blocking
        def _speak():
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print("TTS error:", e)
        t = threading.Thread(target=_speak, daemon=True)
        t.start()


if __name__ == '__main__':
    root = tk.Tk()
    app = VoiceCalculatorApp(root)
    root.mainloop()
