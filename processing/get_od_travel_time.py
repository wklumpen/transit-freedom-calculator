import pandas as pd
import urllib.request
import json
from bs4 import BeautifulSoup

city = 'edmonton'
date = '8-14-2019'
time = '9:00am'
maxWalkDistance = 1200

centroid_file = r"data\edmonton_da_centroids.csv"

centroids = pd.read_csv(centroid_file)

with urllib.request.urlopen(f'http://localhost:8080/otp/routers/{city}/plan?fromPlace=53.5449195,-113.5506499&toPlace=53.5243152,-113.4650627&time={time}&date={date}&mode=TRANSIT,WALK&maxWalkDistance={maxWalkDistance}&arriveBy=false') as u:
    data = u.read()
    df = json.loads(data)
    duration = df['plan']['itineraries'][0]['duration']

print(centroids.head())
