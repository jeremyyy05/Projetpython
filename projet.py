import os
import time
import requests
import pandas as pd
import plotly.express as px
from scrapy import Selector
from urllib.parse import quote, urlencode
from config import API_KEY   

CITIES = [
    "Paris","Marseille","Lyon","Toulouse","Nice","Nantes","Strasbourg","Montpellier","Bordeaux","Lille",
    "Rennes","Reims","Saint-Étienne","Toulon","Grenoble","Dijon","Angers","Nîmes","Villeurbanne","Clermont-Ferrand",
    "Le Havre","Aix-en-Provence","Brest","Limoges","Tours","Amiens","Metz","Perpignan","Besançon","Orléans",
    "Rouen","Mulhouse","Caen","Nancy","Argenteuil"
]

os.makedirs("outputs/csv", exist_ok=True)

def geocode_city(city, country="FR"):
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": f"{city},{country}", "limit": 1, "appid": API_KEY}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data and len(data) > 0:
            return {"city": city, "lat": data[0]["lat"], "lon": data[0]["lon"]}
    except Exception:
        pass
    return None

rows = []
for c in CITIES:
    info = geocode_city(c)
    if info:
        rows.append(info)
    time.sleep(0.25)

cities_df = pd.DataFrame(rows)
cities_df.to_csv("outputs/csv/cities_geoloc.csv", index=False)
print(f"{len(cities_df)} villes géolocalisées avec succès.")

# ---------------------- API METEO 2.5 ----------------------
def get_weather_5days(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "lang": "fr",
        "appid": API_KEY
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# ---------------------- RECUPERATION DES DONNÉES ----------------------
weather_rows = []
for _, row in cities_df.iterrows():
    city, lat, lon = row["city"], row["lat"], row["lon"]
    print(f"Météo pour {city}...")
    try:
        data = get_weather_5days(lat, lon)
        for entry in data["list"]:
            weather_rows.append({
                "city": city,
                "lat": lat,
                "lon": lon,
                "date": pd.to_datetime(entry["dt"], unit="s").date(),
                "temp": entry["main"]["temp"],
                "clouds": entry["clouds"]["all"],
                "wind": entry["wind"]["speed"],
                "rain": entry.get("rain", {}).get("3h", 0)
            })
    except Exception as e:
        print(f"Erreur pour {city} : {e}")
    time.sleep(0.4)

weather_df = pd.DataFrame(weather_rows)
weather_df.to_csv("outputs/csv/weather_raw.csv", index=False)
print(f"météo collectée pour {len(weather_df)} lignes.")

# ---------------------- ANALYSE ET SCORE ----------------------
summary = (
    weather_df.groupby(["city", "lat", "lon"], as_index=False)
    .agg(
        temp_mean=("temp", "mean"),
        clouds_mean=("clouds", "mean"),
        wind_mean=("wind", "mean"),
        rain_sum=("rain", "sum")
    )
)

summary["weather_score"] = (
    summary["temp_mean"]
    - 0.2 * summary["clouds_mean"]
    - 0.3 * summary["wind_mean"]
    - 0.5 * summary["rain_sum"]
)

top5 = summary.sort_values("weather_score", ascending=False).head(5).reset_index(drop=True)
top5.to_csv("outputs/csv/top_cities.csv", index=False)
print("\nLes 5 villes avec la meilleure météo :")
print(top5[["city", "weather_score"]])

# ---------------------- CARTE METEO ----------------------
top5["size"] = top5["weather_score"].apply(lambda x: max(x, 0.1))

fig_weather = px.scatter_mapbox(
    top5,
    lat="lat", lon="lon",
    color="weather_score",
    size="size",
    hover_name="city",
    hover_data={"temp_mean": True, "clouds_mean": True, "wind_mean": True, "rain_sum": True},
    color_continuous_scale="YlOrRd",
    zoom=5, height=650,
    title="Les 5 villes avec la meilleure météo en France"
)

fig_weather.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=40, b=0))
fig_weather.write_image("outputs/mapweather.png")
print("Carte météo enregistrée : outputs/mapweather.png")

# ---------------------- SCRAPING HOTELS ----------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9"
}

def get_hotels_booking(city, max_hotels=5):
    url = f"https://www.booking.com/searchresults.html?ss={quote(city+', France')}&lang=fr"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    sel = Selector(text=r.text)
    names = sel.css('div[data-testid="property-card"] div[data-testid="title"]::text').getall()
    notes = sel.css('div[data-testid="review-score"] div[aria-label]::text').getall()
    hotels = []
    for i, n in enumerate(names[:max_hotels]):
        note = notes[i].strip() if i < len(notes) else "?"
        hotels.append({"city": city, "hotel": n.strip(), "rating": note})
    return hotels

hotels_rows = []
for _, row in top5.iterrows():
    city = row["city"]
    print(f"Recherche d’hôtels à {city}...")
    try:
        hotels = get_hotels_booking(city)
        hotels_rows.extend(hotels)
    except Exception as e:
        print(f"Erreur scraping pour {city} : {e}")
    time.sleep(1.2)

hotels_df = pd.DataFrame(hotels_rows)
hotels_df.to_csv("outputs/csv/hotels.csv", index=False)
print(f"{len(hotels_df)} hôtels collectés.")

# ---------------------- GEOLOCALISATION HOTELS ----------------------
def geocode_hotel(city, hotel):
    base = "https://nominatim.openstreetmap.org/search?"
    params = {"q": f"{hotel}, {city}, France", "format": "json", "limit": 1}
    url = base + urlencode(params)
    try:
        r = requests.get(url, headers={"User-Agent": "EFREI-Student-Project"}, timeout=15)
        data = r.json()
        if len(data) > 0:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None

lats, lons = [], []
for _, row in hotels_df.iterrows():
    lat, lon = geocode_hotel(row["city"], row["hotel"])
    lats.append(lat)
    lons.append(lon)
    time.sleep(1.0)

hotels_df["lat"], hotels_df["lon"] = lats, lons
hotels_df.to_csv("outputs/csv/hotels_with_coords.csv", index=False)
print("Coordonnées ajoutées aux hôtels.")

# ---------------------- CARTE HOTELS ----------------------
merged = hotels_df.merge(top5[["city", "weather_score", "temp_mean", "rain_sum"]], on="city", how="left")

fig_hotels = px.scatter_mapbox(
    merged,
    lat="lat", lon="lon",
    hover_name="hotel",
    hover_data={"city": True, "rating": True, "weather_score": True, "temp_mean": True},
    color="city",
    zoom=5, height=700,
    title="Les Meilleurs hôtels dans les 5 villes météo "
)
fig_hotels.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=40, b=0))
fig_hotels.write_image("outputs/maphotels.png")
print("Carte hôtels enregistrée : outputs/maphotels.png")

print("\nProjet Kayak terminé avec succès !")
