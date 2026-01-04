import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import time
import random
import os
from datetime import datetime
from dotenv import load_dotenv

# CONFIG
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
load_dotenv(dotenv_path=ENV_PATH)

BASE_URL = os.getenv("FIGHTERS_URL")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

SAVE_PATH = "data/raw/fighters.csv"

# Safe Request Function
def safe_request(url, retries=3, delay=5):
    for i in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                return response
            else:
                print(f"Status {response.status_code} for {url}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {i+1}/{retries} failed for {url}: {e}")
        time.sleep(delay + random.uniform(1, 3))
    print(f"Skipping {url} after {retries} retries.")
    return None


# Scraping Functions
def get_fighter_links():
    links = []
    print("Fetching fighter detail links...")

    for letter in "abcdefghijklmnopqrstuvwxyz":
        url = BASE_URL.format(letter)
        response = safe_request(url)
        if not response:
            continue

        soup = BeautifulSoup(response.content, "html.parser")
        for a in soup.select("tr.b-statistics__table-row a"):
            href = a.get("href", "")
            if "fighter-details" in href:
                links.append(href)

        print(f"{letter.upper()}: {len(links)} links so far")
        time.sleep(random.uniform(1, 2))

    print(f"\n Total fighter links found: {len(links)}")
    return list(set(links))

def get_fighter_details(fighter_url):
    response = safe_request(fighter_url)
    if not response:
        return None
    soup = BeautifulSoup(response.content, "html.parser")

    # Basic Information
    name_tag = soup.find("span", class_="b-content__title-highlight")
    name = name_tag.get_text(strip=True) if name_tag else None

    nickname_tag = soup.find("p", class_="b-content__Nickname")
    nickname = nickname_tag.get_text(strip=True) if nickname_tag else None

    # Record (Wins, Losses, Draws)
    record_tag = soup.find("span", class_="b-content__title-record")
    if record_tag:
        record_text = record_tag.get_text(strip=True).replace("Record:", "").strip()
        parts = record_text.split("-")
        wins = parts[0] if len(parts) > 0 else None
        losses = parts[1] if len(parts) > 1 else None
        draws = parts[2] if len(parts) > 2 else None
    else:
        wins = losses = draws = None

    # Physical Information (Height, Weight, Reach, Stance, DOB)
    def extract_info(label):
        for li in soup.select("li.b-list__box-list-item"):
            if label in li.get_text():
                return li.get_text(strip=True).replace(label, "").strip()
        return None

    height = extract_info("Height:")
    weight = extract_info("Weight:")
    reach = extract_info("Reach:")
    stance = extract_info("STANCE:")
    dob = extract_info("DOB:")

    # Career Statistics 
    def extract_stat(label):
        for li in soup.select("li.b-list__box-list-item"):
            if label in li.get_text():
                return li.get_text(strip=True).replace(label, "").strip()
        return None

    slpm = extract_stat("SLpM:")
    str_acc = extract_stat("Str. Acc.:")
    sapm = extract_stat("SApM:")
    str_def = extract_stat("Str. Def:")
    td_avg = extract_stat("TD Avg.:")
    td_acc = extract_stat("TD Acc.:")
    td_def = extract_stat("TD Def.:")
    sub_avg = extract_stat("Sub. Avg.:")

    #  Determine Active / Inactive 
    active = "Inactive"
    date_tags = soup.select("p.b-fight-details__table-text")

    fight_dates = []
    for d in date_tags:
        try:
            fight_date = datetime.strptime(d.text.strip(), "%b. %d, %Y")
            fight_dates.append(fight_date)
        except:
            continue

    if fight_dates:
        last_fight = max(fight_dates)
        years_diff = (datetime.now() - last_fight).days / 365
        if years_diff <= 2:
            active = "Active"

    # Return data as dictionary
    return {
        "Name": name,
        "Nickname": nickname,
        "Wins": wins,
        "Losses": losses,
        "Draws": draws,
        "Height": height,
        "Weight": weight,
        "Reach": reach,
        "Stance": stance,
        "DOB": dob,
        "SLpM": slpm,
        "Str_Acc": str_acc,
        "SApM": sapm,
        "Str_Def": str_def,
        "TD_Avg": td_avg,
        "TD_Acc": td_acc,
        "TD_Def": td_def,
        "Sub_Avg": sub_avg,
        "Active_Status": active,
    }

# Main Script
if __name__ == "__main__":
    os.makedirs("data/raw", exist_ok=True)

    # Load progress if available
    if os.path.exists(SAVE_PATH):
        existing_df = pd.read_csv(SAVE_PATH)
        processed_fighters = set(existing_df["URL"].tolist())
        print(f"Resuming... {len(processed_fighters)} fighters already scraped.")
    else:
        existing_df = pd.DataFrame()
        processed_fighters = set()

    # Step 1: Get all fighter URLs (A–Z)
    fighter_links = get_fighter_links()

    all_fighters = []

    # Step 2: Scrape each fighter's details
    for url in tqdm(fighter_links, desc="Scraping Fighter Profiles"):
        if url in processed_fighters:
            continue

        details = get_fighter_details(url)
        if details:
            details["URL"] = url  # add fighter URL for reference
            all_fighters.append(details)
            processed_fighters.add(url)

        # Auto-save every 10 fighters
        if len(all_fighters) % 10 == 0:
            temp_df = pd.DataFrame(all_fighters)
            combined = pd.concat([existing_df, temp_df], ignore_index=True)
            combined.drop_duplicates(subset=["URL"], inplace=True)
            combined.to_csv(SAVE_PATH, index=False)
            print(f"Progress saved ({len(combined)} fighters).")

    # Final Save
    # Final save — append new fighters safely
    if all_fighters:
        new_df = pd.DataFrame(all_fighters)

        combined_df = pd.concat(
            [existing_df, new_df],
            ignore_index=True
        )

        combined_df.drop_duplicates(subset=["URL"], inplace=True)

        combined_df.to_csv(SAVE_PATH, index=False)

        print(f"Finished! Total fighters saved: {len(combined_df)}")
    else:
        print("No new fighters found. Dataset already up to date.")

