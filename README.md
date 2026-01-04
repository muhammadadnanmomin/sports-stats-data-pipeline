# Sports Statistics Data Pipeline (Scraping & ETL)

## Overview
This repository demonstrates a **production-style web scraping and ETL pipeline** built in Python.
It focuses on **incremental scraping**, **resume-safe execution**, and **ethical configuration management**.
The project is intended **strictly for educational purposes** to showcase data engineering fundamentals
that are commonly used before analytics and machine learning workflows.

> Note: The actual data source is intentionally abstracted via environment variables.

---

## Key Features
- Incremental scraping (only new records are added)
- Resume-safe execution (pipeline can restart without duplicating records)
- Retry logic with timeouts
- Rate limiting to reduce server load
- Clean separation of configuration from code
- No datasets committed to the repository

---

## Tech Stack
- **Python**
- **Requests** – HTTP requests
- **BeautifulSoup** – HTML parsing
- **Pandas** – data structuring & persistence
- **tqdm** – progress monitoring
- **python-dotenv** – environment variable management

---

## Project Structure
```
sports-stats-ml-pipeline/
│
├── scrapers/
│ ├── fight_scraper.py
│ └── fighters_scraper.py
│
├── config/
│ └── config.example.env
│
├── data/ # ignored (no datasets committed)
│
├── requirements.txt
├── .gitignore
└── README.md
```
---
## How to Run

### 1. Clone the repository
```
git clone https://github.com/<your-username>/sports-stats-ml-pipeline.git
```
```
cd sports-stats-ml-pipeline
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Create environment file
```
cp config/config.example.env config/.env
```
Update the values inside config/.env as needed.

### 4. Run scrapers
```
python scrapers/fighters_scraper.py
```
```
python scrapers/fight_scraper.py
```
> Ensure Python 3.9+ is installed before running the scripts.

---
## 🔐 Configuration
All target URLs and sensitive configuration values are loaded from environment variables.
This keeps the repository generic, ethical, and safe to share.

---
## ⚠️ Disclaimer
- This project is created strictly for educational and learning purposes.
- The repository does not include any scraped datasets.
- The data source is intentionally abstracted.
- Users are responsible for ensuring compliance with any website’s Terms of Service and robots.txt policies.
- The author claims no affiliation with any sports organization.

---
## Next Steps
- Feature engineering for analytics
- Unsupervised learning (clustering & embeddings)
- Deep learning with autoencoders (TensorFlow / PyTorch)
- Visualization & dashboards
- ML-based prediction systems

---
## License
This project is licensed under the MIT License.