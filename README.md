# CNFT Sales Twitter Bot
A Cardano NFT Twitter bot that monitors sales for a collection. It pulls and monitors data from [OpenCNFT](https://opencnft.io/) and posts any new sales on Twitter. The bot was created with Python 3.10 and has low requirements to allow anyone to download and modify it for their usage.<br>

# Requirements
* A [Twitter developer account](https://developer.twitter.com/) - Will require [Elevated Access](https://developer.twitter.com/en/portal/products/elevated) for full twitter functions.
* Python 3.10 and basic knowledge of Python
* The Policy ID of the CNFT project
* Libraries required in requriements.txt
  * Tweepy: Twitter actions
  * Requests: GET data from OpenCNFT
  * Ratelimit: Respect API
  * PyCoingecko: Real-time Crypto prices
  * Pillow: Image manipulation

# Usage
The <b>core logic</b> behind the bot is upon the first start, it will check to see if you have a local file on the computer that contains previous tweet information. If no file is made, it will create one with the newest posting and begin the monitor.<br>

* The <b>main program</b> is running on a While loop, and the core function is compare_listings which takes a project name and a file that is saved locally which contains the last tweeted information.<br>
* You need to just enter the policy id for the CNFT project you are trying to monitor. I have policy ids saved in a .env file but you can hard-code a policy id. You can find the shortcut in the <b>retrieve_sales</b> function/<b>sales_endpoing</b> var.<br>
* The Twitter posting function, <b>tweet_sale</b>, can modify the payload message easily.<br>
* This will work exclusively for Cardano NFTs. For other NFTs, a bit of the logic must be changed.
