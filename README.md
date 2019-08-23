# transit-freedom-calculator
Transit Freedom Calculator Data Processing Codebase

## Methodology

### Classifying Points of Interest
Points of Interest used to calculate scores for various aggrregate categories. These points of interest are extracted from Open Street Map and are classified using the amenity classification found [here](https://wiki.openstreetmap.org/wiki/Map_Features#Amenity):
* **Sustenance** includes:
    * `amenity.bars`
    * `amenity.biergarten`
    * `amenity.cafe`
    * `amenity.fast_food`
    * `amenity.pub`
    * `amenity.restaurant`
    * `building.supermarket`
* **Education** includes:
    * `amenity.college`
    * `amenity.library`
    * `amenity.school`
    * `amenity.university`
* **Other** includes:
    * `amenity.bank`
    * `amenity.dentist`
    * `amenity.clinic`
    * `amenity.doctors`
    * `amenity.hospital`
    * `amenity.marketplace`
    * `amenity.place_of_worship`
* **Leisure** categories include:
    * 
* **Entertainment, Arts, and Culture**
    * `cinema`
    * `nightclub`
    * `planetarium`
    * `social_centre`
    * `theatre`
* **Leisure**
    * `leisure.dance`
    * `leisure.fitness_centre`
    * 
* Religion

Code is run as follows:
`osmosis --read-pbf C:\OTP\graphs\edmonton\edmonton_canada.osm.pbf --node-key keyList="leisure" --write-xml C:\OTP\graphs\edmonton\leisure.osm`