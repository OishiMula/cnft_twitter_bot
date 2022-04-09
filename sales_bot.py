# Twitter sales bot created by Oishi Mula for usage at El Matador NFT.
# Copyright (c) 2022, Oishi Mula
# All rights reserved.
# This source code is licensed under the MIT-style license found in the
# LICENSE file in the root directory of this source tree. 
import math
import os
import pickle
import time
from pathlib import Path

import requests
import tweepy
from dotenv import load_dotenv
from ratelimit import limits

load_dotenv()

# Creating the Twitter tweepy connection for V1.1 (media_upload) -- waiting for approval
#twitter_v1_1_auth = tweepy.OAuth1UserHandler(
#    consumer_key=os.getenv('consumer_key'),
#    consumer_secret=os.getenv('consumer_secret'),
#    access_token=os.getenv('access_token'),
#    access_token_secret=os.getenv('access_token_secret')
#)

#twitter = tweepy.API(twitter_v1_1_auth)

# OpenCNFT endpoint for sales on selected Policy ID
sales_endpoint = f"https://api.opencnft.io/1/policy/{os.getenv('elmatador')}/transactions?order=date"

# Creating a first run to see if the file to store last transaciton is made
first_run = True
last_sold_file = Path('last_sold.dat')

running = True
MINUTE = 60
ada = '₳'

millnames = ['',' K',' M',' B',' T']
def millify(n):
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])

# The function to retrieve the JSON listings
def retrieve_sales():
    response_API = requests.get(f'{sales_endpoint}')
    if response_API.status_code == 200: return response_API.json()
    else: return None

def tweet_sale(listing):
    # strings for easy tweeting
    asset = listing['unit_name']
    sold_price = int(float(listing['price']) / 1000000)
    asset_mp = listing['marketplace']
    asset_img_raw = listing['thumbnail']['thumbnail'][7:]
    asset_media_id = retrieve_media_id(asset_img_raw)

    #twitter.update_status(status=f"{asset} was purchased from {asset_mp} for the price of {ada}{millify(sold_price)}.", media_ids=[asset_media_id.media_id])
    os.remove('image.png')

def retrieve_media_id(img_raw):
    ipfs_base = 'https://infura-ipfs.io/ipfs/'
    asset_img = requests.get(f"{ipfs_base}{img_raw}")
#    if asset_img.status_code == 200:
#        with open("image.png", 'wb') as f:
#            f.write(asset_img.content)
#            return twitter.media_upload("image.png")
#    else:
#        return twitter.media_upload("404.jpg")

def compare_listings(current_listing, saved_listing):
    last_sold_saved = pickle.load(open(saved_listing, 'rb'))

    # This is a catch-up function, in case OpenCNFT is down and there were listings not posted
    check_flag = True
    x = 0
    while check_flag == True:
        if int(last_sold_saved['sold_at']) < current_listing['items'][x]['sold_at']:
            x += 1
            new_current = current_listing['items'][x]
            print(f"Current: {new_current['unit_name']}")
            print("Older listing is more recent, adding.")
            time.sleep(3)
        else:
            if x == 0:
                print(f"Current: {current_listing['items'][0]['unit_name']} - pass")
            while x > 0:
                print(f"you have {x} listings. - tweeting now")
                #tweet_sale(current_listing['items'][x])
                x -= 1 
                time.sleep(3)
            check_flag = False

    if int(current_listing['items'][0]['sold_at']) > int(last_sold_saved['sold_at']):
        pickle.dump(current_listing['items'][0], open(saved_listing, 'wb'))
        print("Ding - New sale. Tweeting now.")
        #tweet_sale(current_listing['items'][0])

@limits(calls=30, period=MINUTE)
def main():
    global first_run
    global running

    # Upon starting, it will check for a last_sold file. If none exist, it will enter the most recent sale to begin the monitor.
    if first_run == True:
        first_run = False
        if last_sold_file.is_file() == False:
            current_sales = retrieve_sales()
            pickle.dump(current_sales['items'][0], open(last_sold_file, 'wb'))

    while running == True:
        # Check if listings were retrieved, if not, timeout in case OpenCNFT is down
        current_sales = retrieve_sales()
        if current_sales == None:
            time.sleep(120)
            continue

        compare_listings(current_sales, last_sold_file)
        time.sleep(30)
        
if __name__ == "__main__":
    main()
