# Life Hack 2025

This repository contains three main components to facilitate sustainability-driven product search and comparison:

1. **Python Service** (run.py)
2. **sustainability-api** (Node.js API)
3. **sustainability-companion** (Chrome Extension)

---

## Prerequisites

* **Python 3.8+** and `pip`
* **Node.js 14+** and `npm`
* **Google Chrome** (for the extension)

---

## 1. Python Service

This service lives at the root of the `search_eng` folder and is started via `run.py`.

### Setup

1. **Create a virtual environment**

   ```bash
   python -m venv venv
   ```
2. **Activate it**

   * macOS/Linux: `source venv/bin/activate`
   * Windows: `venv\Scripts\activate`
3. **Install dependencies**
   Ensure you have a `requirements.txt` listing all Python packages. If you don’t yet have one, generate it after installing your packages:

   ```bash
   pip install <your-dependencies>
   pip freeze > requirements.txt
   ```

   Then install from it:

   ```bash
   pip install -r requirements.txt
   ```

### Running

```bash
python run.py
```

The service will start on the configured host/port (check `run.py` or your env settings).

---

## 2. sustainability-api (Node.js)

An Express-based API that aggregates sustainability metrics.

### Setup

1. **Go into the API folder**

   ```bash
   cd sustainability-api
   ```
2. **Install dependencies**

   ```bash
   npm install
   ```
3. **Configure environment**
   Copy the example file:

   ```bash
   cp .env.example .env
   ```

   and fill in your API keys, DB URLs, etc.

### Development

```bash
npm run dev
```

This launches the server in watch mode (using nodemon).

---

## 3. sustainability-companion (Chrome Extension)

A lightweight Chrome extension that surfaces scores and alternatives in real time on e‑commerce sites.

### Setup

1. **Initialize git submodules** (if any)

   ```bash
   git submodule update --init --recursive
   ```
2. **Configure environment**
   Copy the env template if needed:

   ```bash
   cd sustainability-companion
   cp .env.example .env
   ```
3. **Load into Chrome**

   * Open `chrome://extensions/`
   * Enable **Developer mode**
   * Click **Load unpacked**
   * Select the `sustainability-companion` directory

You should now see the extension icon in your toolbar.

---

## License

This project is licensed under the MIT License. Feel free to explore, modify, and contribute!
