# Twitter sales bot created by Oishi Mula for usage at El Matador NFT.
# Copyright (c) 2022, Oishi Mula
# All rights reserved.
# This source code is licensed under the MIT-style license found in the
# LICENSE file in the root directory of this source tree. 
import logging
import os
import pickle
import time
from pathlib import Path
from requests.adapters import HTTPAdapter, Retry

import requests
import tweepy
from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI
from ratelimit import limits

load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M'
)

# Creating the Twitter tweepy connection for V1.1 (media_upload)
twitter_auth = tweepy.OAuth1UserHandler(
    consumer_key=os.getenv('consumer_key'),
    consumer_secret=os.getenv('consumer_secret'),
    access_token=os.getenv('access_token'),
    access_token_secret=os.getenv('access_token_secret')
)

twitter = tweepy.API(
    twitter_auth,
    retry_count = 5,
    retry_delay = 10,
    wait_on_rate_limit=True
)

cg = CoinGeckoAPI()

# Project name, file to store last tweeted information, OpenCNFT endpoint
PROJECT = "El Matador"
LAST_TWEETED_FILE = Path('last_sold.dat')
PAGE_NUM = 1
OPENCNFT_API = f"https://api.opencnft.io/1/policy/{os.getenv('project')}/transactions?page={PAGE_NUM}&order=date"
MINUTE = 60
ADA = '₳'

# The function to retrieve the JSON listings
def retrieve_sales(url):
    opencnft_session = requests.Session()
    retries = Retry(
        total = 5,
        connect = 3,
        read = 3,
        backoff_factor = 0.3,
    )
    adapter = HTTPAdapter(max_retries=retries)
    opencnft_session.mount("https://", adapter)
    
    while True:
        try:
            opencnft_response = opencnft_session.get(f'{url}')
            opencnft_response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            logging.warning(f"{e} - Retrying")
            time.sleep(5)
            continue

        except requests.exceptions.RequestException as e:
            logging.error("Endpoint failure - going to sleep.")
            time.sleep(300)
            continue

        break
    return opencnft_response.json()

def next_page(opencnft_api, page_num):
    page_num += 1
    opencnft_api = f"https://api.opencnft.io/1/policy/{os.getenv('project')}/transactions?page={page_num}&order=date"
    return retrieve_sales(opencnft_api), page_num

def prev_page(opencnft_api, page_num):
    page_num -= 1
    num = 19
    opencnft_api = f"https://api.opencnft.io/1/policy/{os.getenv('project')}/transactions?page={page_num}&order=date"
    return retrieve_sales(opencnft_api), page_num, num

# Creating a payload message to tweet
def tweet_sale(listing):
    asset = listing['unit_name']
    sold_price = int(float(listing['price']) / 1000000)
    asset_mp = listing['marketplace']
    asset_img_raw = listing['thumbnail']['thumbnail'][7:]    
    # Making exception incase CoinGecko / Twitter are having issues
    while True:
        try:
            asset_media_id = retrieve_media_id(asset_img_raw)
            usd = cg.get_price(ids='cardano', vs_currencies='usd')
            twitter.update_status(status=f"{asset} was purchased from {asset_mp} for the price of {ADA}{sold_price:,} (${(usd['cardano']['usd'] * sold_price):,.2f}).", media_ids=[asset_media_id.media_id])
            logging.info(f"{asset} - Purchased for {ADA}{sold_price:,}")
            break
        except (requests.exceptions.RequestException, tweepy.TweepyException) as e:
            logging.error(f"{asset} - Error! Retrying... ")
            time.sleep(30)
            continue

def retrieve_media_id(img_raw):
    ipfs_base = 'https://infura-ipfs.io/ipfs/'
    asset_img = requests.get(f"{ipfs_base}{img_raw}")
    if asset_img.status_code == 200:
        with open("image.png", 'wb') as f:
            f.write(asset_img.content)
            media_id = twitter.media_upload("image.png")
        os.remove('image.png')
        return media_id
    else:
        return twitter.media_upload("404.jpg")

@limits(calls=30, period=MINUTE)
def main():
    # Upon starting, it will check for a last_sold file. If none exist, it will enter the most recent sale to begin the monitor.
    logging.info(f"Starting the {PROJECT} Twitter bot.")
    if LAST_TWEETED_FILE.is_file() == False:
        logging.warning(f"{LAST_TWEETED_FILE} not found. Creating file now.")
        cnft_listing = retrieve_sales(OPENCNFT_API)
        pickle.dump(cnft_listing['items'][0], open(LAST_TWEETED_FILE, 'wb'))

    while True:
        last_tweeted = pickle.load(open(LAST_TWEETED_FILE, 'rb'))

        # Check if listings were retrieved, if not, timeout in case OpenCNFT is down
        cnft_listing = retrieve_sales(OPENCNFT_API)
        if cnft_listing == None:
            time.sleep(120)
            continue

        check_flag = True
        num = 0
        page_num = 1
        total_listings = 0
        while check_flag == True:
            # Check the listing downloaded and compare to what was last tweeted
            # If downloaded listing is newer, check the next listing / page
            if int(cnft_listing['items'][num]['sold_at']) > int(last_tweeted['sold_at']):
                total_listings += 1
                logging.info(f"Listing #{total_listings} - {cnft_listing['items'][num]['unit_name']} is a new sale.")
                num += 1
                if num == 20:
                    num = 0
                    (cnft_listing, page_num) = next_page(OPENCNFT_API, page_num)
                time.sleep(1)

            # If there were new listings, begin to tweet them from oldest to newest.
            elif num > 0:
                logging.info(f"Found {total_listings} listing{'' if total_listings == 1 else 's'}.")
                while num > 0 or page_num > 1:
                    num -= 1
                    tweet_sale(cnft_listing['items'][num])
                    if num == 0 and page_num > 1:
                        (cnft_listing, page_num, num) = prev_page(OPENCNFT_API, page_num)
                    time.sleep(2)
                pickle.dump(cnft_listing['items'][num], open(LAST_TWEETED_FILE, 'wb'))
                check_flag = False

            # If there was nothing new - skip to end.
            else:
                check_flag = False

        time.sleep(30)
        
if __name__ == "__main__":
    main()
