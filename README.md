# Rozetka Collector

An asynchronous web scraper that collects all product URLs from a category page and extracts product details (PDP) and customer reviews.

## Project Structure

```text
rozetka_collector/
├── config.py
├── fetcher.py
├── logger_config.py
├── main.py
├── parser.py
├── requirements.txt
└── README.md
```

## Tech Stack

- Python
- asyncio
- curl_cffi
- lxml
- XPath
- Pydantic

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd rozetka_collector
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the scraper with a category URL:

```bash
python main.py -u "https://rozetka.com.ua/ua/notebooks/c80004/"
```

## Module Responsibilities

| Module | Description |
|---|---|
| `config.py` | Project configuration |
| `fetcher.py` | HTTP requests and response handling |
| `parser.py` | HTML parsing and data extraction |
| `logger_config.py` | Logging configuration |
| `main.py` | Application entry point |
