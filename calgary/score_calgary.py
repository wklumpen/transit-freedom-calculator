import pandas as pd
import urllib.request
import urllib.parse
from shapely.geometry import shape, GeometryCollection, Point, MultiPolygon
from shapely.errors import TopologicalError
from bs4 import BeautifulSoup
import json
import pandas as pd
import os
import numpy as np

# CURRENTLY CALGARY FOCUSED
workspace = 'data'

centroids = pd.read_csv(f'calgary_rtm_centroids.csv')

# Read the POI GeoJSON file produced by using Overpass Turbo
with open(os.path.join('calgary_poi.geojson'), encoding='UTF-8') as poi_infile:
    poi_json = json.load(poi_infile)

# Get the isochrone for a given GPS point
result_list = []
errors = []
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
    url = f"http://localhost:8080/otp/routers/calgary/isochrone?{qs}"
    header = {'Accept': 'application/json'}
    req = urllib.request.Request(url, headers=header)
    print(f"{count}. Loading isochrone for {origin.tz}")
    print(url)
    try:
        with urllib.request.urlopen(req) as u:
            data = u.read()
            isochrone = json.loads(data)
            # g = GeometryCollection([shape(feature["geometry"]) for feature in isochrone['features']]).geoms[0].buffer(0)
            g = shape(isochrone["features"][0]['geometry'])
            print(f"Valid geometry: {g.is_valid}")
            print(f"Area: {g.area}")
            area = g.area
            # if not g.is_valid:
            #     g = g.buffer(0)
            inside = 0
            # Add up population and employment based on overlapping centroids
            pop = 0
            jobs = 0
            for dix, dest in centroids.iterrows():
                p = Point(dest.X,dest.Y)
                try:
                    if p.within(g):
                        inside += 1
                        pop += dest.pop2014
                        jobs += dest.jobs2014
                except TopologicalError:
                    g = g.buffer(0)
                    new_area = g.area
                    print(f"Invalid Geometry, buffer applied. New area: {new_area}")
                    errors.append([origin.tz, area, new_area])

            # Iterate through POI geometry and add to the collection
            supermarkets = 0
            restaurants = 0
            pubs = 0
            playgrounds = 0
            schools = 0
            childcares = 0
            parks = 0
            pitches = 0
            theatres = 0
            cinemas = 0
            pharmacies = 0
            clinics = 0
            dentists = 0
            
            for feature in poi_json['features']:
                # First create the point from the geometry and see if it's in the isochrone
                point = shape(feature['geometry'])
                # print(point)
                poi = feature['properties']
                if point.within(g):
                    # Now we check based on ameity
                    if "shop" in poi and poi['shop'] == 'supermarket':
                        supermarkets += 1
                    elif "amenity" in poi and poi['amenity'] == 'pub':
                        pubs += 1
                    elif "amenity" in poi and poi['amenity'] == 'restaurant':
                        restaurants += 1
                    elif "leisure" in poi and poi['leisure'] == 'playground':
                        playgrounds += 1
                    elif "amenity" in poi and poi['amenity'] == 'school':
                        schools += 1
                    elif "amenity" in poi and poi['amenity'] == 'childcare':
                        childcares += 1
                    elif "leisure" in poi and poi['leisure'] == 'park':
                        parks += 1
                    elif "leisure" in poi and poi['leisure'] == 'pitch':
                        pitches += 1
                    elif "amenity" in poi and poi['amenity'] == 'theatre':
                        theatres += 1
                    elif "amenity" in poi and poi['amenity'] == 'cinema':
                        cinemas += 1
                    elif "amenity" in poi and poi['amenity'] == 'pharmacy':
                        pharmacies += 1
                    elif "amenity" in poi and (poi['amenity'] == 'clinic' or poi['amenity'] == 'hospital'):
                        clinics += 1
                    elif "amenity" in poi and poi['amenity'] == 'dentist':
                        dentists += 1

            result = [origin.tz, pop, jobs, supermarkets, restaurants, pubs, playgrounds, schools, childcares, parks, pitches, theatres, cinemas, pharmacies, clinics, dentists]
            result_list.append(result)
            print(result)
            print(f"You can reach {inside} centroids from {origin.tz}")
            print(f"You can reach {sum(result[2:])} pois from {origin.tz}")
    except urllib.error.HTTPError:
        print(f"ERROR: {url}")
        errors.append(origin.tz)

out = pd.DataFrame(result_list, columns=['orig', 'population', 'jobs', 'supermarket', 'restaurant', 'pub', 'playground', 'school', 'childcare', 'park', 'pitch', 'theatre', 'cinema', 'pharmacy', 'clinic', 'dentist'])


out['pop_pctl'] = out.population.rank(pct=True)
out['job_pctl'] = out.jobs.rank(pct=True)
out['supermarket_pctl'] = out.supermarket.rank(pct=True)
out['basics_avg'] = (out.pop_pctl + out.job_pctl + out.supermarket_pctl)/3
col = 'basics_avg'
conditions  = [ out[col] < 0.2, out[col] < 0.4, out[col] < 0.6, out[col] < 0.8, out[col] < 0.9, out[col] >=0.9 ]
choices     = [ "F", 'D', 'C', "B", "A", "A+"]
out['basics_grade'] = np.select(conditions, choices, default=np.nan)

out['restaurant_pctl'] = out.restaurant.rank(pct=True)
out['pub_pctl'] = out.pub.rank(pct=True)
out['food_avg'] = (out.restaurant_pctl + out.pub_pctl)/2
col = 'food_avg'
conditions  = [ out[col] < 0.2, out[col] < 0.4, out[col] < 0.6, out[col] < 0.8, out[col] < 0.9, out[col] >=0.9 ]
choices     = [ "F", 'D', 'C', "B", "A", "A+"]
out['food_grade'] = np.select(conditions, choices, default=np.nan)

out['playground_pctl'] = out.playground.rank(pct=True)
out['school_pctl'] = out.school.rank(pct=True)
out['childcare_pctl'] = out.childcare.rank(pct=True)
out['family_avg'] = (out.playground_pctl + out.school_pctl + out.childcare_pctl)/3
col = 'family_avg'
conditions  = [ out[col] < 0.2, out[col] < 0.4, out[col] < 0.6, out[col] < 0.8, out[col] < 0.9, out[col] >=0.9 ]
choices     = [ "F", 'D', 'C', "B", "A", "A+"]
out['family_grade'] = np.select(conditions, choices, default=np.nan)

out['park_pctl'] = out.park.rank(pct=True)
out['pitch_pctl'] = out.pitch.rank(pct=True)
out['recreation_avg'] = (out.park_pctl + out.pitch_pctl)/2
col = 'recreation_avg'
conditions  = [ out[col] < 0.2, out[col] < 0.4, out[col] < 0.6, out[col] < 0.8, out[col] < 0.9, out[col] >=0.9 ]
choices     = [ "F", 'D', 'C', "B", "A", "A+"]
out['recreation_grade'] = np.select(conditions, choices, default=np.nan)

out['theatre_pctl'] = out.theatre.rank(pct=True)
out['cinema_pctl'] = out.cinema.rank(pct=True)
out['arts_avg'] = (out.theatre_pctl + out.cinema_pctl)/2
col = 'arts_avg'
conditions  = [ out[col] < 0.2, out[col] < 0.4, out[col] < 0.6, out[col] < 0.8, out[col] < 0.9, out[col] >=0.9 ]
choices     = [ "F", 'D', 'C', "B", "A", "A+"]
out['arts_grade'] = np.select(conditions, choices, default=np.nan)

out['pharmacy_pctl'] = out.pharmacy.rank(pct=True)
out['clinic_pctl'] = out.clinic.rank(pct=True)
out['dentist_pctl'] = out.dentist.rank(pct=True)
out['health_avg'] = (out.pharmacy_pctl + out.clinic_pctl + out.dentist_pctl)/3
col = 'health_avg'
conditions  = [ out[col] < 0.2, out[col] < 0.4, out[col] < 0.6, out[col] < 0.8, out[col] < 0.9, out[col] >=0.9 ]
choices     = [ "F", 'D', 'C', "B", "A", "A+"]
out['health_grade'] = np.select(conditions, choices, default=np.nan)

out['total_avg'] = (out.basics_avg + (out.family_avg + out.food_avg + out.recreation_avg + out.arts_avg + out.health_avg)/5)/2
col = 'total_avg'
conditions  = [ out[col] < 0.2, out[col] < 0.4, out[col] < 0.6, out[col] < 0.8, out[col] < 0.9, out[col] >=0.9 ]
choices     = [ "F", 'D', 'C', "B", "A", "A+"]
out['total_grade'] = np.select(conditions, choices, default=np.nan)

out = out[(out.jobs > 10) & (out.population > 10)]

out.to_csv(f'tfc_calgary.csv', index=False)

print("Errors:", errors)