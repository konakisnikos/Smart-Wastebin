# Smart-Wastebin

A Raspberry Pi–based smart waste bin that detects motion near the bin using
an HC-SR501 PIR sensor and logs events for downstream processing.

---

## Team

| Name | GitHub |
|---|---|
| Nikos Konakis | [@konakisnikos](https://github.com/konakisnikos) |
| Giannis Giannakouras | [@Giannak19](https://github.com/Giannak19) |
| Vasilis Sokos | [@VasiliosSokos](https://github.com/VasiliosSokos) |

---

## Project Structure

```
Smart-Wastebin/
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Setup

**Prerequisites:** Python 3.9 or newer, Git.

```bash
# 1. Clone the repository
git clone https://github.com/konakisnikos/Smart-Wastebin.git
cd Smart-Wastebin

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate it
source venv/bin/activate      # Linux / macOS / Raspberry Pi OS
# venv\Scripts\activate       # Windows

# 4. Install dependencies
pip install -r requirements.txt
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| click | 8.1.8 | CLI argument parsing |
