"""
TypeTrainer

Features
- Modes: Quick Test, Word Drill, Custom Text, Random Quote
- Metrics: WPM, raw WPM, accuracy, errors, time
- History: stored in MySQL (auto-creates DB/table)
- Progress: view last N runs, best/avg WPM, simple ASCII chart

WPM formula: (characters / 5) / minutes  [standard]
Raw WPM counts all typed chars; Net WPM multiplies by accuracy.
"""

from __future__ import annotations
import os
import random
import sys
import textwrap
import time

# ----------------------- MySQL Setup ----------------------- #
# 1) pip install mysql-connector-python
# 2) Update credentials below
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "typing_trainer"
DB_TABLE = "sessions"

try:
    import mysql.connector as mysql
except Exception:
    mysql = None  

def db_connect():
    """Connect to MySQL server (not yet selecting a DB)."""
    if mysql is None:
        raise RuntimeError("mysql-connector-python is not installed. Install it with: pip install mysql-connector-python")
    return mysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)

def db_init():
    """Create database and table if they don't exist."""
    conn = db_connect()
    cur = conn.cursor()
    try:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cur.execute(f"USE {DB_NAME}")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {DB_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                mode VARCHAR(64),
                wpm DOUBLE,
                raw_wpm DOUBLE,
                accuracy DOUBLE,
                errors INT,
                seconds DOUBLE,
                timestamp DOUBLE,
                text_len INT
            )
            """
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

def save_session(res: dict):
    """Insert one session into MySQL."""
    conn = db_connect()
    cur = conn.cursor()
    try:
        cur.execute(f"USE {DB_NAME}")
        cur.execute(
            f"""INSERT INTO {DB_TABLE}
                (mode, wpm, raw_wpm, accuracy, errors, seconds, timestamp, text_len)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                res["mode"], res["wpm"], res["raw_wpm"], res["accuracy"], res["errors"],
                res["seconds"], res["timestamp"], res["text_len"]
            ),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

def load_history():
    """Load all sessions (oldest→newest) from MySQL."""
    conn = db_connect()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(f"USE {DB_NAME}")
        cur.execute(
            f"""SELECT mode, wpm, raw_wpm, accuracy, errors, seconds, timestamp, text_len
                FROM {DB_TABLE}
                ORDER BY id ASC"""
        )
        return list(cur.fetchall())
    finally:
        cur.close()
        conn.close()

def reset_history_db():
    """Delete all rows."""
    conn = db_connect()
    cur = conn.cursor()
    try:
        cur.execute(f"USE {DB_NAME}")
        cur.execute(f"TRUNCATE TABLE {DB_TABLE}")
        conn.commit()
    finally:
        cur.close()
        conn.close()

# Ensure DB and table exist
db_init()

# ----------------------- Sample Text Library ----------------------- #
QUOTES = [
    "The quick brown fox jumps over the lazy dog.",
    "Simplicity is the soul of efficiency.",
    "Programs must be written for people to read, and only incidentally for machines to execute.",
    "Premature optimization is the root of all evil.",
    "In the middle of difficulty lies opportunity.",
    "Code is like humor. When you have to explain it, it’s bad.",
    "First, solve the problem. Then, write the code.",
    "Experience is the name everyone gives to their mistakes.",
    "Before software can be reusable it first has to be usable.",
    "Talk is cheap. Show me the code.",
]

COMMON_WORDS = (
    "the of and to in is you that it he was for on are as with his they I at be this have from or one had by word but not what all were we when your can said there use an each which she do how their if will up other about out many then them these so some her would make like him into time has look two more write go see number no way could people my than first water been call who oil its now find long down day did get come made may part"
).split()

# ----------------------- Utilities ----------------------- #

def clear():
    os.system("cls" if os.name == "nt" else "clear")

ANSI_CODES = {
    "RESET": "\033[0m",
    "DIM": "\033[2m",
    "BOLD": "\033[1m",
    "GREEN": "\033[32m",
    "RED": "\033[31m",
    "YELLOW": "\033[33m",
    "CYAN": "\033[36m",
}
def A(name):
    return ANSI_CODES.get(name, "")

def wrap(s, width=80):
    """Wrap long lines for nicer display."""
    return textwrap.fill(str(s), width=width)

# ----------------------- Metrics ----------------------- #

def compute_stats(target, typed, elapsed_sec):
    """Compute net WPM, raw WPM, accuracy, and errors."""
    errors = 0
    for i, ch in enumerate(typed):
        if i >= len(target) or typed[i] != target[i]:
            errors += 1
    if len(typed) < len(target):
        errors += len(target) - len(typed)
    correct = max(len(target) - errors, 0)

    minutes = max(elapsed_sec / 60.0, 1e-6)
    raw_wpm = (len(typed) / 5.0) / minutes
    accuracy = correct / max(len(target), 1)
    net_wpm = raw_wpm * accuracy
    return net_wpm, raw_wpm, accuracy, errors

def color_compare(target, typed) -> str:
    """Color the target string based on correctness vs what was typed."""
    out = []
    tlen = len(typed)
    for i, ch in enumerate(target):
        if i < tlen:
            if typed[i] == ch:
                out.append(f"{A('GREEN')}{ch}{A('RESET')}")
            else:
                out.append(f"{A('RED')}{ch}{A('RESET')}")
        else:
            out.append(f"{A('DIM')}{ch}{A('RESET')}")
    if tlen > len(target):
        extras = typed[len(target):]
        out.append(f"{A('RED')}{extras}{A('RESET')}")
    return ''.join(out)

# ----------------------- Single-key input (for real terminals) ----------------------- #

if os.name == 'nt':
    import msvcrt
    def read_key() -> str:
        ch = msvcrt.getwch()
        if ch == '\r':
            return '\n'
        return ch
else:
    import termios, tty
    def read_key() -> str:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch

# ----------------------- Render Helpers ----------------------- #

def print_header(title):
    print(f"{A('BOLD')}{A('CYAN')}== {title} =={A('RESET')}")

def progress_bar(p, width=30):
    p = max(0.0, min(1.0, p))
    filled = int(round(p * width))
    return f"[{('#'*filled).ljust(width)}]"

def print_result(res):
    bar = progress_bar(res["accuracy"])
    print(
        f"\n{A('BOLD')}Results{A('RESET')}\n"
        f" WPM:       {A('GREEN')}{res['wpm']:.2f}{A('RESET')}  (raw {res['raw_wpm']:.2f})\n"
        f" Accuracy:  {A('YELLOW')}{res['accuracy']*100:.1f}%{A('RESET')}  {bar}\n"
        f" Errors:    {res['errors']}\n"
        f" Time:      {res['seconds']:.2f}s\n"
    )

def ascii_chart(values, height=8, width=40):
    """Simple vertical chart for WPM history."""
    if not values:
        return "(no data)"
    vmin, vmax = min(values), max(values)
    if vmax - vmin < 1e-9:
        vmax = vmin + 1.0
    step = max(1, len(values) // width)
    samples = values[::step]
    rows = []
    for h in reversed(range(height)):
        y = vmin + (vmax - vmin) * (h / (height - 1))
        row = ''.join('█' if v >= y else ' ' for v in samples)
        rows.append(row)
    return "\n".join(rows)

# ----------------------- Modes ----------------------- #

def run_quick_test():
    target = random.choice(QUOTES)
    return start_session("Quick Test", target)

def run_random_quote():
    target = random.choice(QUOTES)
    return start_session("Random Quote", target)

def run_custom_text():
    clear()
    print_header("Custom Text Mode")
    print("Paste or type your custom text below. Finish with an empty line.\n")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)
    target = " ".join(lines).strip()
    if not target:
        print(f"{A('RED')}No text provided. Returning to menu.{A('RESET')}")
        time.sleep(1)
        return None  # type: ignore
    return start_session("Custom Text", target)

def run_word_drill(n_words=25):
    words = [random.choice(COMMON_WORDS) for _ in range(n_words)]
    target = " ".join(words) + "."
    return start_session("Word Drill", target)

def start_session(mode_name, target):
    # Keep original behavior: live mode (works in real terminals)
    return run_realtime_prompt(mode_name, target)

# ----------------------- Core live prompt ----------------------- #

def run_realtime_prompt(mode_name, target):
    clear()
    print_header(f"{mode_name} (Live)")
    print(f"{A('DIM')}Type the text below. {A('RESET')}{A('YELLOW')}Enter{A('RESET')} to finish, {A('YELLOW')}Esc{A('RESET')} to cancel, {A('YELLOW')}Backspace{A('RESET')} to correct.\n")
    print(f"{A('BOLD')}Target:{A('RESET')}\n{wrap(target)}\n")
    typed = []
    t0 = time.perf_counter()
    try:
        while True:
            # Render live view
            elapsed = max(time.perf_counter() - t0, 1e-6)
            current = ''.join(typed)
            wpm, raw, acc, errs = compute_stats(target[:len(current)], current, elapsed)

            clear()
            print_header(f"{mode_name} (Live)")
            print(f"{A('BOLD')}Target:{A('RESET')}\n{color_compare(target, current)}\n")
            print(f"{A('BOLD')}Your typing:{A('RESET')}\n{current}\n")
            print(
                f" WPM {A('GREEN')}{wpm:.2f}{A('RESET')} (raw {raw:.2f})  |  "
                f"Acc {A('YELLOW')}{acc*100:.1f}%{A('RESET')}  |  Errors {errs}  |  Time {elapsed:.1f}s"
            )

            ch = read_key()
            if ch == '\x1b':  # ESC
                raise KeyboardInterrupt
            elif ch == '\n':  # Enter
                break
            elif ch in ('\x08', '\x7f'):  # Backspace
                if typed:
                    typed.pop()
            elif ch == '\r':
                break
            else:
                typed.append(ch)
    except KeyboardInterrupt:
        # Treat as canceled session
        return {
            "mode": mode_name+" (canceled)",
            "wpm": 0.0,
            "raw_wpm": 0.0,
            "accuracy": 0.0,
            "errors": 0,
            "seconds": time.perf_counter()-t0,
            "timestamp": time.time(),
            "text_len": len(target),
        }

    elapsed = time.perf_counter() - t0
    final = ''.join(typed)
    wpm, raw, acc, errs = compute_stats(target, final, elapsed)
    return {
        "mode": mode_name+" (Live)",
        "wpm": wpm,
        "raw_wpm": raw,
        "accuracy": acc,
        "errors": errs,
        "seconds": elapsed,
        "timestamp": time.time(),
        "text_len": len(target),
    }

# ----------------------- History Views ----------------------- #

def view_progress(history):
    """Show best WPM, avg of last 10, and chart (uses what's in memory now)."""
    clear()
    print_header("Progress")
    if not history:
        print("No history yet. Complete a test to see your progress.\n")
        input("Press Enter to return to menu...")
        return

    last = history[-10:]
    best = max(history, key=lambda r: r["wpm"])
    avg = sum(r["wpm"] for r in last) / len(last)

    print(f"Best WPM: {A('GREEN')}{best['wpm']:.2f}{A('RESET')} ({best['mode']})")
    print(f"Avg (last {len(last)}): {A('YELLOW')}{avg:.2f}{A('RESET')}\n")

    values = [r["wpm"] for r in history]
    chart = ascii_chart(values, height=8, width=50)
    print(chart)

    print("\nRecent Sessions:")
    for r in last:
        print(
            f" - {time.strftime('%Y-%m-%d %H:%M', time.localtime(r['timestamp']))} | {r['mode']:14} | WPM {r['wpm']:6.2f} | Acc {r['accuracy']*100:5.1f}%"
        )
    print()
    input("Press Enter to return to menu...")

def reset_history():
    """Clear all rows in MySQL."""
    reset_history_db()
    print(f"{A('RED')}History cleared in MySQL.{A('RESET')}")

# ----------------------- Menu ----------------------- #

def main_menu():
    # Load existing sessions from MySQL at startup to display progress.
    history = load_history()
    while True:
        clear()
        print_header("Typing Trainer — CLI")
        print(
            "Select an option:\n"
            " 1) Quick Test (random short sentence)\n"
            " 2) Random Quote\n"
            " 3) Word Drill (25 words)\n"
            " 4) Custom Text\n"
            " 5) View Progress\n"
            f" 6) {A('RED')}Reset History{A('RESET')}\n"
            " 7) Quit\n"
        )
        try:
            choice = input("> ").strip().lower()
        except EOFError:
            print("\nGoodbye!")
            return

        if choice == "1":
            res = run_quick_test()
        elif choice == "2":
            res = run_random_quote()
        elif choice == "3":
            res = run_word_drill()
        elif choice == "4":
            res = run_custom_text()
            if res is None:
                continue
        elif choice == "5":
            # Reload from DB to reflect any changes made outside this run too
            history = load_history()
            view_progress(history)
            continue
        elif choice == "6":
            reset_history()
            history = []
            continue
        elif choice == "7":
            print("Goodbye!")
            return
        else:
            print("Invalid choice. Retry...")
            time.sleep(1)
            continue

        # Show result, save to DB, and update in-memory history for this run
        clear()
        print_header("Session Complete")
        print_result(res)
        save_session(res)
        history.append(res)
        input("Press Enter to return to menu...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nInterrupted. Bye!")
