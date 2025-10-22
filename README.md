# TypeTrainer — Typing Speed Tester

A **command-line typing trainer** built in **Python**, designed to help users improve typing speed and accuracy while storing performance data in a **MySQL database** for long-term tracking.

---

##  Features

 **Typing Modes**
- **Quick Test** – Type a short random sentence.  
- **Random Quote** – Practice with famous programming quotes.  
- **Word Drill** – Type a string of common English words.  
- **Custom Text** – Input your own text passage for practice.  

 **Performance Metrics**
- Calculates **WPM (Words Per Minute)**, **raw WPM**, **accuracy**, **error count**, and **time elapsed**.  
- Real-time feedback with color-coded text (green = correct, red = wrong, dim = remaining).  

 **Data Persistence**
- Automatically creates and stores session data in a **MySQL database**:
  - Mode  
  - WPM & raw WPM  
  - Accuracy  
  - Error count  
  - Session duration  
  - Timestamp  
  - Text length  

 **Progress Tracking**
- View last sessions, best score, average WPM, and a visual **ASCII chart** of progress.  
- Option to **reset history** anytime.

 **Cross-Platform Support**
- Works on **Windows** and **macOS** terminals.  
- Uses `msvcrt` for Windows

---

## ⚙️ Installation

###  Prerequisites
Make sure you have:
- **Python 3.8+**
- **MySQL Server** running locally or remotely
- **mysql-connector-python** library

Install MySQL connector:
```bash
pip install mysql-connector-python
```

---

###  Setup MySQL Database
Before running the program, update your MySQL credentials in the code:

```python
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "your_password"
DB_NAME = "typing_trainer"
DB_TABLE = "sessions"
```

The script automatically:
- Creates the database (`typing_trainer`)  
- Creates a table (`sessions`)  
- Inserts your session results after every test.

---

###  Run the Program
Run the script directly from terminal:
```bash
python typing_trainer.py
```

Then use the menu to select a typing mode:

```
== Typing Trainer — CLI ==
Select an option:
 1) Quick Test
 2) Random Quote
 3) Word Drill
 4) Custom Text
 5) View Progress
 6) Reset History
 7) Quit
```

---

##  How WPM is Calculated

**Standard Formula**:  
$begin:math:display$
\\text{WPM} = \\frac{(\\text{characters typed} / 5)}{\\text{minutes elapsed}}
$end:math:display$

- **Raw WPM** counts all characters.  
- **Net WPM** = Raw WPM × Accuracy  
- **Accuracy** = Correct characters ÷ Total characters  

---

##  Database Schema

| Column Name | Type | Description |
|--------------|------|-------------|
| `id` | INT (Auto Increment) | Unique session ID |
| `mode` | VARCHAR(64) | Typing mode used |
| `wpm` | DOUBLE | Net WPM |
| `raw_wpm` | DOUBLE | Raw WPM |
| `accuracy` | DOUBLE | Accuracy (0–1) |
| `errors` | INT | Number of wrong keystrokes |
| `seconds` | DOUBLE | Duration of session |
| `timestamp` | DOUBLE | UNIX timestamp of session |
| `text_len` | INT | Number of characters in target text |

---

##  Example Output

```
== Quick Test (Live) ==
Type the text below. Enter to finish, Esc to cancel, Backspace to correct.

Target:
The quick brown fox jumps over the lazy dog.

Your typing:
The quick browm fox

WPM 55.60 (raw 60.10)  |  Acc 91.0%  |  Errors 2  |  Time 12.5s

== Results ==
 WPM:       55.60  (raw 60.10)
 Accuracy:  91.0%  [###########################   ]
 Errors:    2
 Time:      12.5s
```

---

##  Progress Tracking

When you select **View Progress**, the program shows:
- **Best WPM**
- **Average of last 10 sessions**
- **ASCII performance chart**
- **Recent session list** with timestamps and accuracy

Example:
```
== Progress ==
Best WPM: 75.20 (Quick Test)
Avg (last 10): 68.45

███████████░░░░░░░░░░░░
█ █ █ █ █ █ █ █ █ █ █ █

Recent Sessions:
 - 2025-10-22 20:45 | Word Drill     | WPM 68.45 | Acc 95.2%
 - 2025-10-21 18:22 | Quick Test     | WPM 75.20 | Acc 98.1%
```

---

##  Project Structure

```
TypeTrainer/
│
├── typing_trainer.py      # Main program file
├── README.md              # Documentation
└── requirements.txt       # Dependencies (optional)
```

---

##  Known Limitations

- **Does not support IDLE input** (works best in real terminal / command prompt).  
- **ANSI colors** may not render in all terminal emulators (Windows 10+ is fine).  
- Requires **MySQL running locally** or accessible remotely.

---

##  Concepts Used

- Real-time character input and terminal refresh  
- String comparison for accuracy/error detection  
- MySQL CRUD operations using `mysql.connector`  
- ANSI color-coded terminal UI  
- ASCII data visualization  
- Data persistence and performance tracking  

---

##  Author

**Developed by:** *Sricharan*  
**Language:** Python 3.13.7  
**Database:** MySQL  
**Version:** 1.0  

