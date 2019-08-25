import pandas as pd
import urllib.request
import urllib.parse
from shapely.geometry import shape, GeometryCollection, Point, MultiPolygon
from bs4 import BeautifulSoup
import json
import pandas as pd

city = 'calgary'
workspace = 'data'

centroids = pd.read_csv(f'data\\{city}_rtm_centroids.csv')

supermarket = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\supermarket.osm") as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        supermarket.append([float(node['lon']), float(node['lat'])])

# Get the isochrone for a given GPS point
result_list = []
# Go through each centroid
count = 0
for oix, origin in centroids.iterrows():
    count += 1
    params = {
    'fromPlace': f"{origin.Y},{origin.X}",
    'time': '9:00am',
    'date': '9-11-2019',
    'maxWalkDistance': 1600,
    'arriveBy': 'false',
    'walkReluctance': 5,
    'waitReluctance': 10,
    'cutoffSec': 1800
    }
    # Fetch the isochrone
    qs = urllib.parse.urlencode(params)
    url = f"http://localhost:8080/otp/routers/{city}/isochrone?{qs}"
    header = {'Accept': 'application/json'}
    req = urllib.request.Request(url, headers=header)
    print(f"{count}. Loading isochrone for {origin.tz}")
    print(url)
    try:
        with urllib.request.urlopen(req) as u:
            data = u.read()
            isochrone = json.loads(data)
            g = GeometryCollection([shape(feature["geometry"]) for feature in isochrone['features']]).geoms[0]
            inside = 0
            pop = 0
            jobs = 0
            supermarkets = 0
            for dix, dest in centroids.iterrows():
                p = Point(dest.X,dest.Y)
                if g.contains(p):
                    inside += 1
                    # Now we score it with the data we have

                    # First we add population
                    pop += dest.pop2014
                    jobs += dest.jobs2014
                    for s in supermarket:
                        p = Point(s[0], s[1])
                        if g.contains(p):
                            supermarkets += 1

            result = [origin.tz, pop, jobs, supermarkets]
            result_list.append(result)
            print(result)
            print(f"You can reach {inside} centroids from {origin.tz}")
            print(f"You can reach {supermarkets} supermarkets from {origin.tz}")
    except urllib.error.HTTPError:
        print(f"ERROR: {url}")

out = pd.DataFrame(result_list, columns=['orig', 'dest', 'pop', 'jobs', 'supermarket'])
out.to_csv(f'od_{city}.csv', index=False)
        
