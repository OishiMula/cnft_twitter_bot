# Twitter sales bot created by Oishi Mula for usage at Raging Teens Clan NFT.
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

# Creating the Twitter tweepy connection for V2
twitter = tweepy.Client(
    bearer_token=os.getenv('bearer_token'),
    consumer_key=os.getenv('consumer_key'),
    consumer_secret=os.getenv('consumer_secret'),
    access_token=os.getenv('access_token'),
    access_token_secret=os.getenv('access_token_secret')
)

# OpenCNFT endpoint for sales on selected Policy ID
rtc_sales_endpoint = f"https://api.opencnft.io/1/policy/{os.getenv('rtc_policyid')}/transactions?order=date"
furin_sales_endpoint = f"https://api.opencnft.io/1/policy/{os.getenv('furin_policyid')}/transactions?order=date"
ipfs_base = 'https://infura-ipfs.io/ipfs/'

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
def retrieve_sales(p):
    if p == 'rtc':
        response_API = requests.get(f'{rtc_sales_endpoint}')
    elif p == 'furin':
        response_API = requests.get(f'{furin_sales_endpoint}')
    return response_API.json()

@limits(calls=30, period=MINUTE)
def main():
    global first_run
    global running
    global ipfs_base
    while running == True:
        current_sales = retrieve_sales('rtc')['items']

        # Upon starting, it will check for a last_sold csve. If none exist, it will enter the most recent sale to begin the monitor.
        if first_run == True:
            first_run = False
            if last_sold_file.is_file() == False:
                pickle.dump(current_sales[0], open('last_sold.dat', 'wb'))
            
        current_time = current_sales[0]['sold_at']
        last_sold_meta = pickle.load(open('last_sold.dat', 'rb'))

        if int(current_time) > int(last_sold_meta['sold_at']):
            # check to see if the listing after was not skipped
            check_flag = True
            x = 0
            while check_flag == True:
                if current_time < current_sales[x]['sold_at']:
                    x += 1
                    current_time = current_sales[x]['sold_at']
                    print("Older listing is more recent")
                else:
                    check_flag = False
            
            # save data for persistent data
            pickle.dump(current_sales[x], open('last_sold.dat', 'wb'))

            # setup for the string formats
            asset = current_sales[x]['unit_name']
            sold_price = int(float(current_sales[x]['price']) / 1000000)
            asset_mp = current_sales[x]['marketplace']
            asset_img_raw = current_sales[x]['thumbnail']['thumbnail'][7:]

            asset_img = requests.get(f"{ipfs_base}{asset_img_raw}")
            if asset_img.status_code == 200:
                with open("image.png", 'wb') as f:
                    f.write(asset_img.content)

            # Waiting for Twitter V2 API approval
            #twitter.create_tweet(text="Hello World!")
            #twitter.create_tweet(text=f"{asset} was purchased from {asset_mp} for the price of {ada}{millify(sold_price)}.}")
            os.remove('image.png')
        time.sleep(3) 
        

if __name__ == "__main__":
    main()
