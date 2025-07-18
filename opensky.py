# The "opensky_api" package is not available on PyPI.
# You need to download it from https://github.com/openskynetwork/opensky-api and place opensky_api.py in your project folder.
from opensky_api import OpenSkyApi
import json
from requests_oauthlib import OAuth2Session
import requests
from time import time
from datetime import datetime

# KHAF coordinates
lat = 37.6194
lon = -122.370

# Define a bounding box around KHAF (about ~10km radius)
bbox = (lat - 0.2, lat + 0.2, lon - 0.2, lon + 0.2)

# Authenticate (recommended for more results)
api = OpenSkyApi("Tor", "Tabletdarrell1")


if datetime.strip():
    dt = datetime.strptime(datetime, "%Y-%m-%d %H:%M:%S")
    chosen_time = int(dt.timestamp())
    states = api.get_states(bbox=bbox, time=chosen_time)
else:
    states = api.get_states(bbox=bbox)
# ...existing code...

# Get states in bounding box
states = api.get_states(bbox=bbox)

#debug area
print(states)
print(f"Number of aircraft found: {len(states.states) if states and states.states else 0}")


# Save ADS-B info to TXT
with open("ADSB.txt", "w", encoding="utf-8") as f:
    if states and states.states:
        for sv in states.states:
            f.write(str(sv) + "\n\n")
    else:
        f.write("No aircraft found near KHAF.\n")
        print("No aircraft found near KHAF.")
