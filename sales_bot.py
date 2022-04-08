# Twitter sales bot created by Oishi Mula for usage at Raging Teens Clan NFT.
# Copyright (c) 2022, Oishi Mula
# All rights reserved.
# This source code is licensed under the MIT-style license found in the
# LICENSE file in the root directory of this source tree. 
import requests
from ratelimit import limits
import time
import os
import math
import pickle
import tweepy
from pathlib import Path

# Authentication for Twitter, using env to store

# Creating the Twitter tweepy connection for V2
twitter = tweepy.Client(
    bearer_token=bearer_token_t,
    consumer_key=consumer_key_t,
    consumer_secret=consumer_secret_t,
    access_token=access_token_t,
    access_token_secret=access_token_secret_t
)

# OpenCNFT endpoint for sales on selected Policy ID
rtc_sales_endpoint = 'https://api.opencnft.io/1/policy/ec2e1c314ee754cea4ba3afc69f74b2130f87bb3928e1a1e8534c209/transactions?order=date'
furin_sales_endpoint = 'https://api.opencnft.io/1/policy/2a89138bffea582b621a747015c1c90259d6b4751eeccaa39c4a7dfb/transactions?order=date'
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
        current_sales = retrieve_sales('rtc')

        if first_run == True:
            first_run = False
            if last_sold_file.is_file() == False:
                first_time_dict = {"sold_at" : "0"}
                pickle.dump(first_time_dict, open('last_sold.dat', 'wb'))
            
        current_time = current_sales['items'][0]['sold_at']
        last_sold_meta = pickle.load(open('last_sold.dat', 'rb'))
        if int(current_time) > int(last_sold_meta['sold_at']):
            pickle.dump(current_sales['items'][0], open('last_sold.dat', 'wb'))
            asset = current_sales['items'][0]['unit_name']
            sold_price = int(float(current_sales['items'][0]['price']) / 1000000)
            asset_mp = current_sales['items'][0]['marketplace']
            asset_img_raw = current_sales['items'][0]['thumbnail']['thumbnail'][7:]
            asset_img = requests.get(f"{ipfs_base}{asset_img_raw}")
            if asset_img.status_code == 200:
                with open("image.png", 'wb') as f:
                    f.write(asset_img.content)
            twitter.create_tweet(text="Hello World!")
            #twitter.create_tweet(text=f"{asset} was purchased from {asset_mp} for the price of {ada}{millify(sold_price)}.}")
            os.remove('image.png')
        else:
            print("No new sales")
        time.sleep(3)
    

if __name__ == "__main__":
    main()
