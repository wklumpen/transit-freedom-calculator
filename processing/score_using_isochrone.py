import pandas as pd
import urllib.request
import urllib.parse
from shapely.geometry import shape, GeometryCollection, Point, MultiPolygon
import json
import pandas as pd

city = 'calgary'
workspace = 'data'

centroids = pd.read_csv('data\calgary_da_centroids.csv')
# Get the isochrone for a given GPS point

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
    print(f"{count}. Loading isochrone for {origin.DAUID}")
    with urllib.request.urlopen(url) as u:
        data = u.read()
        isochrone = json.loads(data)
        g = GeometryCollection([shape(feature["geometry"]) for feature in isochrone['features']]).geoms[0]
        inside = 0
        for dix, dest in centroids.iterrows():
            p = Point(dest.X,dest.Y)
            if g.contains(p):
                inside += 1
        print(f"You can reach {inside} centroids from {origin.DAUID}")
        
