import pandas as pd
import urllib.request
import urllib.parse
from shapely.geometry import shape, GeometryCollection, Point, MultiPolygon
from bs4 import BeautifulSoup
import json
import pandas as pd

# CURRENTLY CALGARY FOCUSED

city = 'calgary'
workspace = 'data'

centroids = pd.read_csv(f'data\\{city}_rtm_centroids.csv')

# Basics include Pop/Emp and Supermarkets
supermarket = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\supermarket.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        supermarket.append([float(node['lon']), float(node['lat'])])

# Food/Drink includes restaurants and bars/pubs
restaurant = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\restaurant.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        restaurant.append([float(node['lon']), float(node['lat'])])

pub = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\bar_pub.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        pub.append([float(node['lon']), float(node['lat'])])

# Family includes playgrounds, schools, and childcare elements
playground = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\playground.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        playground.append([float(node['lon']), float(node['lat'])])

school = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\school.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        school.append([float(node['lon']), float(node['lat'])])

childcare = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\childcare.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        childcare.append([float(node['lon']), float(node['lat'])])

# Recreation includes parks and leisure centres (fitness)
park = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\park.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        park.append([float(node['lon']), float(node['lat'])])

fitness = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\fitness.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        fitness.append([float(node['lon']), float(node['lat'])])

# Arts and culture includes theatre, cinema, and museums
theatre = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\theatre.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        theatre.append([float(node['lon']), float(node['lat'])])

cinema = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\cinema.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        cinema.append([float(node['lon']), float(node['lat'])])

museum = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\museum.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        museum.append([float(node['lon']), float(node['lat'])])

# Health contains pharmacy, clinic/hospital, and dentist
pharmacy = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\pharmacy.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        pharmacy.append([float(node['lon']), float(node['lat'])])

clinic = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\clinic.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        clinic.append([float(node['lon']), float(node['lat'])])

dentist = []
with open(f"C:\\OTP\\graphs\\{city}\\poi\\dentist.osm", encoding='utf-8') as infile:
    data = BeautifulSoup(infile, 'lxml')
    for node in data.find_all('node'):
        dentist.append([float(node['lon']), float(node['lat'])])

# sm = pd.DataFrame(supermarket, columns=['lon', 'lat'])
# sm.to_csv('calgary_supermarket.csv')

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
    url = f"http://localhost:8080/otp/routers/{city}/isochrone?{qs}"
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
                    
            # Add up amenities based on amenity location
            # Start with Supermarkets
            supermarkets = 0
            for s in supermarket:
                p = Point(s[0], s[1])
                if p.within(g):
                    supermarkets += 1
            
            restaurants = 0
            for s in restaurant:
                p = Point(s[0], s[1])
                if p.within(g):
                    restaurants += 1
            
            pubs = 0
            for s in pub:
                p = Point(s[0], s[1])
                if p.within(g):
                    pubs += 1

            playgrounds = 0
            for s in playground:
                p = Point(s[0], s[1])
                if p.within(g):
                    playgrounds += 1

            schools = 0
            for s in school:
                p = Point(s[0], s[1])
                if p.within(g):
                    schools += 1

            childcares = 0
            for s in childcare:
                p = Point(s[0], s[1])
                if p.within(g):
                    childcares += 1

            parks = 0
            for s in park:
                p = Point(s[0], s[1])
                if p.within(g):
                    parks += 1

            fitnesses = 0
            for s in fitness:
                p = Point(s[0], s[1])
                if p.within(g):
                    fitnesses += 1

            theatres = 0
            for s in theatre:
                p = Point(s[0], s[1])
                if p.within(g):
                    theatres += 1

            cinemas = 0
            for s in cinema:
                p = Point(s[0], s[1])
                if p.within(g):
                    cinemas += 1

            museums = 0
            for s in museum:
                p = Point(s[0], s[1])
                if p.within(g):
                    museums += 1

            fitnesses = 0
            for s in fitness:
                p = Point(s[0], s[1])
                if p.within(g):
                    fitnesses += 1

            pharmacies = 0
            for s in pharmacy:
                p = Point(s[0], s[1])
                if p.within(g):
                    pharmacies += 1

            clinics = 0
            for s in clinic:
                p = Point(s[0], s[1])
                if p.within(g):
                    clinics += 1

            dentists = 0
            for s in dentist:
                p = Point(s[0], s[1])
                if p.within(g):
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

out.to_csv(f'tfc_{city}.csv', index=False)
        
