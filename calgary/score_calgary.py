import pandas as pd
import urllib.request
import urllib.parse
from shapely.geometry import shape, GeometryCollection, Point, MultiPolygon
from bs4 import BeautifulSoup
import json
import pandas as pd
import os

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
            g = GeometryCollection([shape(feature["geometry"]) for feature in isochrone['features']]).geoms[0].buffer(0)
            inside = 0

            # Add up population and employment based on overlapping centroids
            pop = 0
            jobs = 0
            for dix, dest in centroids.iterrows():
                p = Point(dest.X,dest.Y)
                if p.within(g):
                    inside += 1
                    pop += dest.pop2014
                    jobs += dest.jobs2014

            # Iterate through POI geometry and add to the collection
            supermarkets = 0
            restaurants = 0
            pubs = 0
            playgrounds = 0
            schools = 0
            childcares = 0
            parks = 0
            fitnesses = 0
            theatres = 0
            cinemas = 0
            museums = 0
            fitnesses = 0
            pharmacies = 0
            clinics = 0
            dentists = 0
            
            for feature in poi_json['features']:
                # First create the point from the geometry and see if it's in the isochrone
                point = shape(feature['geometry'])
                poi = feature['properties']
                if g.contains(point):
                    # Now we check based on ameity
                    if "shop" in poi and poi['shop'] == 'supermarket':
                        supermarkets += 1
                    elif "amenity" in poi and poi['amenity'] == 'pub':
                        pubs += 1
                    elif "amenity" in poi and poi['amenity'] == 'restaurant':
                        restaurants += 1
                    elif "leisure" in poi and poi['leisure'] == 'playground':
                        pubs += 1
                    elif "amenity" in poi and poi['amenity'] == 'school':
                        schools += 1
                    elif "amenity" in poi and poi['amenity'] == 'childcare':
                        childcares += 1
                    elif "leisure" in poi and poi['leisure'] == 'park':
                        parks += 1
                    elif "amenity" in poi and (poi['amenity'] == 'fitness_centre' or poi['amenity'] == 'sports_centre'):
                        fitnesses += 1
                    elif "amenity" in poi and poi['amenity'] == 'theatre':
                        theatres += 1
                    elif "amenity" in poi and poi['amenity'] == 'cinema':
                        cinemas += 1
                    elif "amenity" in poi and poi['amenity'] == 'museum':
                        museums += 1
                    elif "amenity" in poi and poi['amenity'] == 'pharmacy':
                        pharmacies += 1
                    elif "amenity" in poi and (poi['amenity'] == 'clinic' or poi['amenity'] == 'hospital'):
                        clinics += 1
                    elif "amenity" in poi and poi['amenity'] == 'dentist':
                        dentists += 1

            result = [origin.tz, pop, jobs, supermarkets, restaurants, pubs, playgrounds, schools, childcares, parks, fitnesses, theatres, cinemas, museums, pharmacies, clinics, dentists]
            result_list.append(result)
            print(result)
            print(f"You can reach {inside} centroids from {origin.tz}")
            print(f"You can reach {sum(result[2:])} pois from {origin.tz}")
    except urllib.error.HTTPError:
        print(f"ERROR: {url}")
        errors.append(origin.tz)

print(errors)
out = pd.DataFrame(result_list, columns=['orig', 'population', 'jobs', 'supermarket', 'restaurant', 'pub', 'playground', 'school', 'childcare', 'park', 'fitness', 'theatre', 'cinema', 'museum', 'pharmacy', 'clinic', 'dentist'])

out['pop_pctl'] = out.population.rank(pct=True)
out['job_pctl'] = out.jobs.rank(pct=True)
out['supermarket_pctl'] = out.supermarket.rank(pct=True)
out['basics_avg'] = (out.pop_pctl + out.job_pctl + out.supermarket_pctl)/3

out['restaurant_pctl'] = out.restaurant.rank(pct=True)
out['pub_pctl'] = out.pub.rank(pct=True)
out['food_avg'] = (out.restaurant_pctl + out.pub_pctl)/2

out['playground_pctl'] = out.playground.rank(pct=True)
out['school_pctl'] = out.school.rank(pct=True)
out['childcare_pctl'] = out.childcare.rank(pct=True)
out['family_avg'] = (out.playground_pctl + out.school_pctl + out.childcare_pctl)/3

out['park_pctl'] = out.park.rank(pct=True)
out['fitness_pctl'] = out.fitness.rank(pct=True)
out['recreation_avg'] = (out.park_pctl + out.fitness_pctl)/2

out['theatre_pctl'] = out.theatre.rank(pct=True)
out['cinema_pctl'] = out.cinema.rank(pct=True)
out['musuem_pctl'] = out.museum.rank(pct=True)
out['arts_avg'] = (out.theatre_pctl + out.cinema_pctl + out.musuem_pctl)/3

out['pharmacy_pctl'] = out.pharmacy.rank(pct=True)
out['clinic_pctl'] = out.clinic.rank(pct=True)
out['dentist_pctl'] = out.dentist.rank(pct=True)
out['health_avg'] = (out.pharmacy_pctl + out.clinic_pctl + out.dentist_pctl)/3

out.to_csv(f'tfc_calgary.csv', index=False)
        
