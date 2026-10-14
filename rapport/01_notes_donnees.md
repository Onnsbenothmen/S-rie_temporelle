# Section 1 — Données

## Fiche synthétique

| Champ | Valeur |
|---|---|
| Thématique | Énergie / Environnement — Allemagne |
| Source | ENTSO-E Transparency Platform, via **Open Power System Data** (portail open-data) |
| Fichier brut | `data/raw/time_series_60min_singleindex.csv` |
| Fréquence | Horaire (60 min), timestamps **UTC** (aucune ambiguïté de changement d'heure) |
| Période analysée | **2015-01-01 00:00 → 2020-09-30 23:00** (5,75 ans ≥ 3 ans exigés) |
| Observations | 50 400 heures exactement |
| Variables | `Load`, `Wind`, `Solar` (MW) — voir détail ci-dessous |
| Fichier préparé | `data/processed/germany_energy_analysis.csv` |

## Source et transformations fournisseur

Le jeu brut (Open Power System Data) est une extraction agrégée de la
**ENTSO-E Transparency Platform** : consommation et production réelles
rapportées par les gestionnaires de réseau de transport (TSO). Points à
connaître avant toute modélisation :

- **Agrégation** : les valeurs sont des totaux **pays** (Allemagne
  entière). L'éolien total (`DE_wind_generation_actual`) combine déjà
  onshore + offshore ; la consommation correspond aux échanges
  physiquement comptés.
- **Heure** : les timestamps sont fournis en **UTC** ET en heure locale
  (CET/CEST). On retient exclusivement l'UTC → grille strictement
  horaire, indépendante des changements d'heure d'été.
- **Unités** : MW (puissance moyenne sur l'heure de livraison) pour la
  charge et les productions. À vérifier sur l'historique ENTSO-E car
  certaines variables de capacité sont aussi en MW.
- **Données réelles vs prévision** : on ne garde que les séries
  `*_generation_actual` et `*_load_actual` (réalisées), jamais les
  prévisions.

## Variables retenues

| Variable | Colonne source | Rôle |
|---|---|---|
| `Load` | `DE_load_actual_entsoe_transparency` | Consommation électrique (endogène principale) |
| `Wind` | `DE_wind_generation_actual` | Production éolienne (participant, très volatile) |
| `Solar` | `DE_solar_generation_actual` | Production solaire (saisonnalité journalière forte, nulle la nuit) |

Choix des 3 variables : une série **multidimensionnelle** cohérente
(consommation + deux production de renouvelables) qui justifie un volet
VAR/VECM complet, et pas une simple juxtaposition de séries univariées.

## Contrôles qualité réalisés

Mesurés sur la version analytique (`germany_energy_analysis.csv`) :

- **Continuité** : l'index horaire attendu (date_range `freq='h'`) et les
  timestamps présents coïncident exactement → **0 trou**, **0 doublon**.
- **Valeurs manquantes** :
  | Variable | NA | Répartition |
  |---|---|---|
  | `Load` | 0 | — |
  | `Wind` | 74 | heures isolées éparses |
  | `Solar` | 103 | heures isolées éparses |
  Les blocs NA sont courts (quelques heures isolées). Ils sont donc
  **conservés NA dans le fichier analytique** et seront interpolés plus
  tard, avec justification, juste avant la modélisation (`forecast::na.interp`
  côté R, interpolation justifiée côté Python). Ne jamais deviner une donnée
  avant l'EDA.
- **Première observation** du brut (31/12/2014 23h) : entièrement vide
  (Load, Wind, Solar tous NA) → retirée, l'analyse commence au 01/01/2015.

## Transformations appliquées par nous (jusqu'ici)

1. Sélection des 4 colonnes Allemagne dans le fichier européen brut.
2. Conversion des timestamps en `DatetimeIndex` UTC.
3. Tri chronologique + dédoublonnage.
4. Suppression de l'observation initiale entièrement manquante.
5. Export des versions *timeseries* (brute nettoyée) et *analysis*
   (début 2015) en CSV.

Aucune transformation statistique (différenciation, log, désaisonnalisation)
n'est appliquée à ce stade : elle est décidée par l'EDA (section 2).

## Objet série temporelle natif

`src/data_loader.py` expose `load_germany_series()`, qui retourne un
`DataFrame` pandas avec `DatetimeIndex` UTC et **fréquence déclarée
`freq='h'`** — c'est l'objet consommé par tous les notebooks. Côté R,
l'équivalent est `ts(...)` avec `frequency = 24` (heures par jour).

Le split train/test chronologique 90/10 est fourni par
`chronological_split()` (jamais aléatoire, voir justification dans le module).

## Reproductibilité

- `requirements.txt` liste les dépendances.
- Les versions précises des packages utilisés seront figées en en-tête
  de chaque notebook.
- Aucun chemin en dur : tout passe par `src/data_loader.py`.