import pandas as pd
import urllib.request
import urllib.parse
import json
from bs4 import BeautifulSoup

city = 'edmonton'
date = '8-14-2019'
time = '9:00am'
maxWalkDistance = 1800

centroid_file = r"data\edmonton_da_centroids.csv"

centroids = pd.read_csv(centroid_file)

tt = []
print(centroids.shape)
count = 0
# for oix, orig in centroids.iterrows():
orig = centroids[centroids.DAUID == 48111089].iloc[0]
for dix, dest in centroids.iterrows():
    count += 1
    params = {
        'fromPlace': f"{orig.Y},{orig.X}",
        'toPlace': f"{dest.Y},{dest.X}",
        'time': time,
        'date': date,
        'maxWalkDistance': maxWalkDistance,
        'arriveBy': 'false',
        'walkReluctance': 5,
        'waitReluctance': 10
    }
    if count % 100 == 0:
        print(f"{count} pairs processed")
    if orig.DAUID != dest.DAUID:
        qs = urllib.parse.urlencode(params)
        url = f'http://localhost:8080/otp/routers/{city}/plan?{qs}'
        # print(url)
        with urllib.request.urlopen(url) as u:
            data = u.read()
            df = json.loads(data)
            try:
                duration = df['plan']['itineraries'][0]['duration']
            except KeyError:
                duration = None
            tt.append([orig.DAUID, dest.DAUID, duration])
    else:
        tt.append([orig.DAUID, dest.DAUID, 0])

ttdf = pd.DataFrame(tt, columns=['orig', 'dest', 'tt'])

ttdf.to_csv(f"{city}_tt.csv", index=False)
