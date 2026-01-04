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

BASE_URL = os.getenv("FIGHT_EVENTS_URL")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

SAVE_PATH = "data/raw/fights.csv"

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

# Event Links
def get_event_links(pages=3):
    links = []
    print(" Fetching event links...")
    for page in range(1, pages + 1):
        url = BASE_URL.format(page)
        response = safe_request(url)
        if not response:
            continue
        soup = BeautifulSoup(response.content, "html.parser")
        for a in soup.select("tr.b-statistics__table-row a"):
            href = a.get("href", "")
            if "event-details" in href and href not in links:
                links.append(href)
        time.sleep(random.uniform(2, 3))
    print(f"Found {len(links)} events.")
    return links

# Fight Links (from event)
def get_fight_links(event_url):
    response = safe_request(event_url)
    if not response:
        return []
    soup = BeautifulSoup(response.content, "html.parser")
    return [a["href"] for a in soup.select("a") if "fight-details" in a.get("href", "")]


# Fight Details
def get_fight_details(fight_url):
    response = safe_request(fight_url)
    if not response:
        return None

    soup = BeautifulSoup(response.content, "html.parser")

    # Event Information
    event_name = soup.select_one("h2.b-content__title")
    event_name = event_name.text.strip() if event_name else "N/A"

    # Fighters 
    fighters = [f.text.strip() for f in soup.select(".b-fight-details__person-name a")]
    result = [r.text.strip() for r in soup.select(".b-fight-details__person-status")]
    if len(fighters) < 2:
        return None

    # Meta Information (Method, Round, Time, Format)
    meta = {"method": "N/A", "round": "N/A", "time": "N/A", "time_format": "N/A"}

    meta_block = soup.select_one("p.b-fight-details__text")
    if meta_block:
        labels = meta_block.select("i.b-fight-details__label")
        for label_tag in labels:
            label = label_tag.text.strip().replace(":", "").lower()
            value_tag = label_tag.find_next("i", style=True)
            value = value_tag.text.strip() if value_tag else "N/A"

            if "method" in label:
                meta["method"] = value
            elif "round" in label and "time" not in label:
                meta["round"] = value
            elif label == "time":
                meta["time"] = value
            elif "time format" in label:
                meta["time_format"] = value


    # Parse Table into Dicts 
    def parse_fight_table(table):
        fighters_data = []
        if not table:
            return fighters_data

        headers = [h.text.strip() for h in table.select("thead th")]
        rows = table.select("tbody tr.b-fight-details__table-row")

        if not rows:
            return fighters_data

        row = rows[0]  # single row containing both fighters
        cols = row.select("td.b-fight-details__table-col")

        fighter_a_data, fighter_b_data = {}, {}

        # Skip first header ("Fighter") and zip remaining headers with columns
        for header, col in zip(headers[1:], cols):
            ps = col.select("p.b-fight-details__table-text")
            if len(ps) >= 2:
                fighter_a_data[header] = ps[0].text.strip()
                fighter_b_data[header] = ps[1].text.strip()
            elif len(ps) == 1:
                fighter_a_data[header] = ps[0].text.strip()
                fighter_b_data[header] = "N/A"
            else:
                fighter_a_data[header] = fighter_b_data[header] = "N/A"

        fighters_data.append(fighter_a_data)
        fighters_data.append(fighter_b_data)
        return fighters_data


    # Totals (Striking + Grappling combined)
    totals_section = soup.find("p", string=lambda t: t and "Totals" in t)
    totals = {"fighter_a_sig_str": "N/A", "fighter_b_sig_str": "N/A",
              "fighter_a_total_str": "N/A", "fighter_b_total_str": "N/A",
              "fighter_a_td": "N/A", "fighter_b_td": "N/A",
              "fighter_a_ctrl": "N/A", "fighter_b_ctrl": "N/A",
              "fighter_a_sub": "N/A", "fighter_b_sub": "N/A"}
    if totals_section:
        totals_table = totals_section.find_next("table")
        if totals_table:
            fighters_data = parse_fight_table(totals_table)
            if len(fighters_data) == 2:
                fa, fb = fighters_data
                totals.update({
                    "fighter_a_sig_str": fa.get("Sig. str.", "N/A"),
                    "fighter_b_sig_str": fb.get("Sig. str.", "N/A"),
                    "fighter_a_total_str": fa.get("Total str.", "N/A"),
                    "fighter_b_total_str": fb.get("Total str.", "N/A"),
                    "fighter_a_td": fa.get("Td", "N/A"),
                    "fighter_b_td": fb.get("Td", "N/A"),
                    "fighter_a_ctrl": fa.get("Ctrl", "N/A"),
                    "fighter_b_ctrl": fb.get("Ctrl", "N/A"),
                    "fighter_a_sub": fa.get("Sub. att", "N/A"),
                    "fighter_b_sub": fb.get("Sub. att", "N/A"),
                })

    #  Significant Strikes Table 
    sig_section = soup.find("p", string=lambda t: t and "Significant Strikes" in t)
    sig_stats = {"fighter_a_head":"N/A","fighter_b_head":"N/A",
                 "fighter_a_body":"N/A","fighter_b_body":"N/A",
                 "fighter_a_leg":"N/A","fighter_b_leg":"N/A",
                 "fighter_a_distance":"N/A","fighter_b_distance":"N/A",
                 "fighter_a_ground":"N/A","fighter_b_ground":"N/A"}
    if sig_section:
        sig_table = sig_section.find_next("table")
        if sig_table:
            sig_data = parse_fight_table(sig_table)
            if len(sig_data) == 2:
                fa, fb = sig_data
                sig_stats.update({
                    "fighter_a_head": fa.get("Head","N/A"),
                    "fighter_b_head": fb.get("Head","N/A"),
                    "fighter_a_body": fa.get("Body","N/A"),
                    "fighter_b_body": fb.get("Body","N/A"),
                    "fighter_a_leg": fa.get("Leg","N/A"),
                    "fighter_b_leg": fb.get("Leg","N/A"),
                    "fighter_a_distance": fa.get("Distance","N/A"),
                    "fighter_b_distance": fb.get("Distance","N/A"),
                    "fighter_a_ground": fa.get("Ground","N/A"),
                    "fighter_b_ground": fb.get("Ground","N/A"),
                })

    # Combine Everything (Flattened)
    fight_data = {
        "event_name": event_name,
        "fighter_a": fighters[0],
        "fighter_b": fighters[1],
        "result_a": result[0] if len(result) > 0 else "N/A",
        "result_b": result[1] if len(result) > 1 else "N/A",
        "method": meta["method"],
        "round": meta["round"],
        "time": meta["time"],
        "time_format": meta["time_format"],
        "fight_url": fight_url,
        
    }

    # Merge totals and sig stats
    fight_data.update(totals)
    fight_data.update(sig_stats)

    return fight_data


# Main Script
if __name__ == "__main__":
    os.makedirs("data/raw", exist_ok=True)

    # Load progress if available
    if os.path.exists(SAVE_PATH):
        existing_df = pd.read_csv(SAVE_PATH)
        processed_fights = set(existing_df["fight_url"].tolist())
        print(f"Resuming... {len(processed_fights)} fights already scraped.")
    else:
        existing_df = pd.DataFrame()
        processed_fights = set()

    events = get_event_links(pages=3)
    all_fights = []

    for e in tqdm(events, desc="Scraping fights"):
        fight_links = get_fight_links(e)
        for f in fight_links:
            if f in processed_fights:
                continue
            details = get_fight_details(f)
            if details:
                all_fights.append(details)
                processed_fights.add(f)

            # Auto-save every 5 fights
            if len(all_fights) % 5 == 0:
                temp_df = pd.DataFrame(all_fights)
                combined = pd.concat([existing_df, temp_df], ignore_index=True)
                combined.drop_duplicates(subset=["fight_url"], inplace=True)
                combined.to_csv(SAVE_PATH, index=False)
                print(f" Progress saved ({len(combined)} fights).")
            time.sleep(random.uniform(1, 2))

# Final save
# Final save — APPEND MODE
if all_fights:
    new_df = pd.DataFrame(all_fights)

    # Combine old + new
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)

    # Remove duplicates safely
    combined_df.drop_duplicates(subset=["fight_url"], inplace=True)

    # Save back
    combined_df.to_csv(SAVE_PATH, index=False)

    print(f"Finished! Total fights saved: {len(combined_df)}")
else:
    print("No new fights found. Dataset is already up to date.")

