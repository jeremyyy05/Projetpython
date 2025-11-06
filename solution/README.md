# Projets2-python
Projet Kayak – Analyse météo et recherche d’hôtels
Objectif

Ce projet vise à identifier les villes françaises présentant les meilleures conditions météorologiques grâce aux données issues de l’API OpenWeatherMap. Les cinq villes ayant les conditions les plus favorables sont ensuite utilisées pour rechercher les meilleurs hôtels sur Booking.com.

Fonctionnement

Récupération des coordonnées géographiques (latitude et longitude) des principales villes françaises.
Collecte des prévisions météorologiques sur cinq jours (température, vent, nuages, pluie).
Calcul d’un score météo basé sur la moyenne des paramètres collectés.
Sélection des cinq villes ayant le meilleur score.
Recherche et géolocalisation des hôtels correspondants.
Production de deux cartes synthétiques :
Carte des villes présentant les meilleures conditions météo.
Carte des hôtels situés dans ces villes.
Fichiers générés
cities_geoloc.csv : coordonnées des villes.
weather_raw.csv : données météorologiques collectées.
top_cities.csv : liste des cinq meilleures villes.
hotels_with_coords.csv : informations sur les hôtels avec coordonnées GPS.
mapweather.png et maphotels.png : cartes finales illustrant les résultats.

Conclusion

Ce projet met en œuvre la collecte et l’exploitation de données issues d’API externes, leur traitement statistique ainsi que leur représentation géographique à l’aide de la bibliothèque Plotly. Il illustre une approche complète de l’analyse de données appliquée à un cas concret de recommandation de destinations touristiques.
kayak/
├── outputs/
│   ├── csv/                   # Fichiers de résultats (météo, hôtels, etc.)
│   ├── mapweather.png         # Carte des meilleures villes météo
│   └── maphotels.png          # Carte des meilleurs hôtels
├── Projet2.py                 # Script principal
└── config.py                  # Fichier contenant la clé API