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
da_centroids = pd.read_csv(f'calgary_da_centroids.csv')

# Read the POI GeoJSON file produced by using Overpass Turbo
with open(os.path.join('calgary_poi.geojson'), encoding='UTF-8') as poi_infile:
    poi_json = json.load(poi_infile)

# Read the foursquare CSV file

foursquare = pd.read_csv('foursquare_poi_yyc.csv')

# Get the isochrone for a given GPS point
result_list = []
errors = []
# Go through each centroid
count = 0
for oix, origin in da_centroids.iterrows():
    count += 1
    params = {
    'fromPlace': f"{origin.Y},{origin.X}",
    'time': '9:00am',
    'date': '9-11-2019',
    'maxWalkDistance': 1600,
    'arriveBy': 'false',
    'walkReluctance': 5,
    'waitReluctance': 10,
    'cutoffSec': 900
    }
    # Fetch the isochrone
    qs = urllib.parse.urlencode(params)
    url = f"http://localhost:8080/otp/routers/calgary/isochrone?{qs}"
    header = {'Accept': 'application/json'}
    req = urllib.request.Request(url, headers=header)
    print(f"{count}. Loading isochrone for {origin.DAUID}")
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
            # Add up employment based on overlapping centroids
            pop = 0
            jobs = 0
            for dix, dest in centroids.iterrows():
                p = Point(dest.X,dest.Y)
                try:
                    if p.within(g):
                        inside += 1
                        jobs += dest.jobs2014
                except TopologicalError:
                    g = g.buffer(0)
                    new_area = g.area
                    print(f"Invalid Geometry, buffer applied. New area: {new_area}")
                    errors.append([origin.DAUID, area, new_area])
            # Add up employment based on overlapping centroids
            for dix, dest in da_centroids.iterrows():
                p = Point(dest.X,dest.Y)
                try:
                    if p.within(g):
                        inside += 1
                        pop += dest.total_pop
                except TopologicalError:
                    g = g.buffer(0)
                    new_area = g.area
                    print(f"Invalid Geometry, buffer applied. New area: {new_area}")
                    errors.append([origin.DAUID, area, new_area])

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
            
            # Iterate through foursquare POI and add to their own collection
            fsq_supermarkets = 0
            fsq_foods = 0
            fsq_bars = 0
            fsq_playgrounds = 0
            fsq_schools = 0
            fsq_daycares = 0
            fsq_parks = 0
            fsq_theatres = 0
            fsq_movies = 0
            fsq_pharmacies = 0
            fsq_hospitals = 0
            fsq_dentists = 0

            for fsqx, fsq in foursquare.iterrows():
                p = Point(fsq.lon, fsq.lat)
                if p.within(g):
                    # Now we check based on ameity
                    if fsq.category == 'Supermarket':
                        fsq_supermarkets += 1
                    elif fsq.category == 'Bar&Nightclub':
                        fsq_bars += 1
                    elif fsq.category == 'Food':
                        fsq_foods += 1
                    elif fsq.category == 'Playground':
                        fsq_playgrounds += 1
                    elif fsq.category == 'School':
                        fsq_schools += 1
                    elif fsq.category == 'Daycare':
                        fsq_daycares += 1
                    elif fsq.category == 'Park':
                        fsq_parks += 1
                    elif fsq.category == 'Theater':
                        fsq_theatres += 1
                    elif fsq.category == 'Movie Theater':
                        fsq_movies += 1
                    elif fsq.category == 'Pharmacy':
                        fsq_pharmacies += 1
                    elif fsq.category == 'Hospital':
                        fsq_hospitals += 1
                    elif fsq.category == "Dentist's Office":
                        fsq_dentists += 1

            result = [int(origin.DAUID), int(pop), jobs, supermarkets, restaurants, pubs, playgrounds, schools, 
            childcares, parks, pitches, theatres, cinemas, pharmacies, clinics, dentists,
            fsq_supermarkets, fsq_foods, fsq_bars, fsq_playgrounds, fsq_schools, fsq_daycares, fsq_parks, 
            fsq_theatres, fsq_movies, fsq_pharmacies, fsq_hospitals, fsq_dentists]
            result_list.append(result)
            print(result)
            print(f"You can reach {inside} centroids from {origin.DAUID}")
            print(f"You can reach {sum(result[2:])} pois from {origin.DAUID}")
    except urllib.error.HTTPError:
        print(f"ERROR: {url}")
        errors.append(origin.DAUID)

cols = ['orig', 'population', 'jobs', 'supermarket', 'restaurant', 'pub', 'playground', 'school', 
'childcare', 'park', 'pitch', 'theatre', 'cinema', 'pharmacy', 'clinic', 'dentist',
'fsq_supermarkets', 'fsq_foods', 'fsq_bars', 'fsq_playgrounds', 'fsq_schools', 'fsq_daycares', 'fsq_parks', 
'fsq_theatres', 'fsq_movies', 'fsq_pharmacies', 'fsq_hospitals', 'fsq_dentists']

out = pd.DataFrame(result_list, columns=cols)

# OSM Percentiles
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
out['total_grade_osm'] = np.select(conditions, choices, default=np.nan)

# Foursquare percentiles
out['fsq_supermarket_pctl'] = out.fsq_supermarkets.rank(pct=True)
out['fsq_food_pctl'] = out.fsq_foods.rank(pct=True)
out['fsq_bars_pctl'] = out.fsq_bars.rank(pct=True)
out['fsq_playgrounds_pctl'] = out.fsq_playgrounds.rank(pct=True)
out['fsq_schools_pctl'] = out.fsq_schools.rank(pct=True)
out['fsq_daycares_pctl'] = out.fsq_daycares.rank(pct=True)
out['fsq_parks_pctl'] = out.fsq_parks.rank(pct=True)
out['fsq_theatres_pctl'] = out.fsq_theatres.rank(pct=True)
out['fsq_movies_pctl'] = out.fsq_movies.rank(pct=True)
out['fsq_pharmacies_pctl'] = out.fsq_pharmacies.rank(pct=True)
out['fsq_hospitals_pctl'] = out.fsq_hospitals.rank(pct=True)
out['fsq_dentists_pctl'] = out.fsq_dentists.rank(pct=True)

# Now let's assign points based on McNeil (2011)
# OSM Data first
out['parks_pts'] = np.where(out['park'] > 0, 10.0, 0.0)
out['childcare_pts'] = np.where(out['childcare'] > 0, 2.5, 0.0)
out['school_pts'] = np.where(out['school'] > 0, 7.5, 0.0)
out['supermarket_pts'] = np.where(out['supermarket'] < 3, out['supermarket']*3.75, 7.5)
out['drinking_pts'] = np.where(out['pub'] < 5, out['pub']*1.25, 5.0)
out['restaurant_pts'] = np.where(out['restaurant'] < 13, out['restaurant']*0.625, 7.5)
out['movie_pts'] = np.where(out['cinema'] < 3, out['cinema']*1.25, 2.5)
out['theatre_pts'] = np.where(out['theatre'] < 3, out['theatre']*1.25, 2.5)
out['pitch_pts'] = np.where(out['pitch'] < 3, out['pitch']*2.5, 5)

out['osm_pts'] = out.parks_pts + out.childcare_pts + out.school_pts + out.supermarket_pts + out.drinking_pts + out.restaurant_pts + out.movie_pts + out.theatre_pts + out.pitch_pts
out['osm_pts_pctl'] = out.osm_pts.rank(pct=True)

# Now the Foursquare data
out['fsq_parks_pts'] = np.where(out['fsq_parks'] > 0, 10.0, 0.0)
out['fsq_childcare_pts'] = np.where(out['fsq_daycares'] > 0, 2.5, 0.0)
out['fsq_school_pts'] = np.where(out['fsq_schools'] > 0, 7.5, 0.0)
out['fsq_supermarket_pts'] = np.where(out['fsq_supermarkets'] < 3, out['fsq_supermarkets']*3.75, 7.5)
out['fsq_drinking_pts'] = np.where(out['fsq_bars'] < 5, out['fsq_bars']*1.25, 5.0)
out['fsq_foods_pts'] = np.where(out['fsq_foods'] < 13, out['fsq_foods']*0.625, 7.5)
out['fsq_movie_pts'] = np.where(out['fsq_movies'] < 3, out['fsq_movies']*1.25, 2.5)
out['fsq_theatre_pts'] = np.where(out['fsq_theatres'] < 3, out['fsq_theatres']*1.25, 2.5)

out['fsq_pts'] = out.fsq_parks_pts + out.fsq_childcare_pts + out.fsq_school_pts + out.fsq_supermarket_pts + out.fsq_drinking_pts + out.fsq_foods_pts + out.fsq_movie_pts + out.fsq_theatre_pts
out['fsq_pts_pctl'] = out.fsq_pts.rank(pct=True)
# out = out[(out.jobs > 10) & (out.population > 10)]

out.to_csv(f'tfc_calgary_da_fsq_15min.csv', index=False)

print("Errors:", errors)