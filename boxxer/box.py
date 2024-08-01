import time
import random
import requests
import json
import schedule
from fake_useragent import UserAgent
from loguru import logger
import threading

# Utility Functions

def wait(ms):
    """Pause execution for the specified number of milliseconds."""
    time.sleep(ms / 1000)

def compute_taps(today_left):
    """Calculate the number of taps that can be performed."""
    amount = 0
    taps = 0

    while amount + taps + 1 <= today_left:
        taps += 1
        amount += taps

    return taps

# Generate a fake user agent
ua = UserAgent()
fake_user_agent = ua.random

# API Interaction Functions

HEADERS = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'origin': 'https://app.boxxer.world',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://app.boxxer.world/',
    'sec-ch-ua': '"Not)A;Brand";v="99", "Brave";v="127", "Chromium";v="127"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'sec-gpc': '1',
    'user-agent': fake_user_agent,
}

def fetch_user_data(token, token_id):
    """Fetch user data using the provided token."""
    try:
        response = requests.post(
            'https://api.boxxer.world/auth/user/info',
            json={},
            headers={**HEADERS, 'Authorization': token}
        )
        response.raise_for_status()
        return response.json()['data']
    except requests.RequestException as e:
        logger.error(f"Error in fetch_user_data for token {token_id}: {e}")
        return None

def perform_taps(token, total_taps, token_id):
    """Perform the tap actions up to the specified number of taps."""
    remaining_taps = total_taps
    taps_performed = 0

    while remaining_taps > 0 and taps_performed < 1000:
        tap_count = min(remaining_taps, 1000 - taps_performed)
        for i in range(tap_count):
            try:
                requests.post(
                    'https://api.boxxer.world/boxxer/tap',
                    headers={**HEADERS, 'Authorization': token},
                    json={'tapNumber': taps_performed + i + 1}
                )
                taps_performed += 1
                remaining_taps -= 1
                logger.success(f"Token {token_id}: Success {taps_performed} time(s)! Taps left: {remaining_taps}")
                wait(random.randint(5000, 15000))
            except requests.RequestException as e:
                logger.error(f"Token {token_id}: Error in perform_taps: {e}")

        if remaining_taps > 0:
            logger.info(f"Token {token_id}: Pausing before the next batch...")
            wait(random.randint(10000, 30000))

    profile = fetch_user_data(token, token_id)
    return profile['boxxer']['tap']['todayLeft'] if profile else None

# Bot Execution Function

def execute_bot(token, amount, is_scheduled=False, token_id=None):
    """Run the bot with the given token and tap amount. Adjusts for scheduled runs."""
    try:
        profile = fetch_user_data(token, token_id)
        if not profile:
            return

        if is_scheduled:
            amount = compute_taps(profile['boxxer']['tap']['todayLeft'])

        if amount > profile['boxxer']['tap']['todayLeft']:
            logger.warning(f"Token {token_id}: You can't do more than your available taps!")
        else:
            response = perform_taps(token, amount, token_id)
            if response is not None:
                logger.info(f"Token {token_id}: All processes have been completed!")
                logger.info(f"Token {token_id}: Taps left: {response}")
                if response > 0:
                    logger.info(f"Token {token_id}: You can still tap {response} more time(s).")
                else:
                    logger.info(f"Token {token_id}: All chances have been used, try again tomorrow!")
    except Exception as e:
        logger.error(f"Token {token_id}: Error in execute_bot: {e}")

# Threaded Bot Execution Function

def threaded_bot_execution(token, amount, token_id):
    execute_bot(token, amount, True, token_id)
    schedule.every().day.at("00:00").do(execute_bot, token, amount, True, token_id)

# Main Function

def main():
    with open('auths.json', 'r') as f:
        tokens = json.load(f)

    default_amount = 0  # Assuming you want to set a default amount, modify as needed

    threads = []
    for idx, token in enumerate(tokens, start=1):
        logger.info(f"Running bot for token {idx} ......")
        t = threading.Thread(target=threaded_bot_execution, args=(token, default_amount, idx))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
