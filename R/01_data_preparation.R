
# ============================================================
# PROJET : SERIES TEMPORELLES
# Sujet : Analyse energetique de l'Allemagne
# Script : 01_data_preparation.R
# ============================================================


# ============================================================
# 1. CHARGEMENT DE LA BIBLIOTHEQUE
# ============================================================

library(readr)


# ============================================================
# 2. LECTURE DU FICHIER ORIGINAL
# ============================================================

cat("========== LECTURE DES DONNEES ==========\n")

# Verifier les fichiers disponibles
print(list.files("data/raw"))

# Charger le dataset original
df <- read_csv(
  "data/raw/time_series_60min_singleindex.csv",
  show_col_types = FALSE
)

# Dimensions du fichier original
cat("\nDimensions du fichier original :\n")
print(dim(df))

# Structure du timestamp
cat("\nStructure du timestamp :\n")
str(df$utc_timestamp)

# Verifier les timestamps manquants
cat("\nTimestamps manquants :\n")
print(sum(is.na(df$utc_timestamp)))


# ============================================================
# 3. SELECTION DES VARIABLES ALLEMANDES
# ============================================================

colonnes_requises <- c(
  "utc_timestamp",
  "DE_load_actual_entsoe_transparency",
  "DE_wind_generation_actual",
  "DE_solar_generation_actual"
)

# Verifier que toutes les colonnes existent
colonnes_absentes <- setdiff(
  colonnes_requises,
  names(df)
)

if (length(colonnes_absentes) > 0) {
  stop(
    paste(
      "Colonnes absentes du dataset :",
      paste(colonnes_absentes, collapse = ", ")
    )
  )
}

# Creer le dataframe de l'Allemagne
germany <- data.frame(
  DateTime = df$utc_timestamp,
  Load = df$DE_load_actual_entsoe_transparency,
  Wind = df$DE_wind_generation_actual,
  Solar = df$DE_solar_generation_actual
)

# Afficher les premieres observations
cat("\nPremieres observations :\n")
print(head(germany))

# Afficher les dernieres observations
cat("\nDernieres observations :\n")
print(tail(germany))

# Structure des donnees
cat("\nStructure du dataframe :\n")
str(germany)

# Dimensions
cat("\nDimensions du dataframe :\n")
print(dim(germany))


# ============================================================
# 4. ANALYSE DES VALEURS MANQUANTES
# ============================================================

cat("\n========== VALEURS MANQUANTES ==========\n")

# Nombre de valeurs manquantes par variable
print(colSums(is.na(germany)))

# Nombre total de valeurs manquantes
cat("\nNombre total de valeurs manquantes :\n")
print(sum(is.na(germany)))

# Positions des NA dans Load
cat("\nPositions des NA dans Load :\n")
print(which(is.na(germany$Load)))

# Positions des NA dans Wind
cat("\nPositions des NA dans Wind :\n")
print(which(is.na(germany$Wind)))

# Positions des NA dans Solar
cat("\nPositions des NA dans Solar :\n")
print(which(is.na(germany$Solar)))


# ============================================================
# 5. PERIODE COUVERTE
# ============================================================

cat("\n========== PERIODE DES DONNEES ==========\n")

print(
  range(
    germany$DateTime,
    na.rm = TRUE
  )
)


# ============================================================
# 6. VERIFICATION DES DOUBLONS
# ============================================================

nb_doublons <- sum(
  duplicated(germany$DateTime)
)

cat("\nNombre de timestamps dupliques :\n")
print(nb_doublons)


# ============================================================
# 7. TRI CHRONOLOGIQUE
# ============================================================

germany <- germany[
  order(germany$DateTime),
]

cat("\nPeriode apres le tri :\n")

print(
  range(
    germany$DateTime,
    na.rm = TRUE
  )
)


# ============================================================
# 8. VERIFICATION DE LA CONTINUITE TEMPORELLE
# ============================================================

# Calculer l'ecart entre deux timestamps consecutifs
time_diff <- as.numeric(
  difftime(
    germany$DateTime[-1],
    germany$DateTime[-nrow(germany)],
    units = "hours"
  )
)

# Distribution des ecarts
cat("\nDistribution des ecarts en heures :\n")
print(table(time_diff))

# Nombre d'ecarts differents d'une heure
nb_ecarts_anormaux <- sum(
  time_diff != 1,
  na.rm = TRUE
)

cat("\nNombre d'ecarts differents d'une heure :\n")
print(nb_ecarts_anormaux)


# ============================================================
# 9. NETTOYAGE DES TIMESTAMPS
# ============================================================

# Supprimer uniquement les lignes sans timestamp
germany_clean <- germany[
  !is.na(germany$DateTime),
]

cat("\nDimensions apres nettoyage des timestamps :\n")
print(dim(germany_clean))

cat("\nValeurs manquantes restantes :\n")
print(colSums(is.na(germany_clean)))


# ============================================================
# 10. CREATION DU DOSSIER DE SORTIE
# ============================================================

if (!dir.exists("data/processed")) {
  dir.create(
    "data/processed",
    recursive = TRUE
  )
}


# ============================================================
# 11. FONCTION POUR ANALYSER LES BLOCS DE NA
# ============================================================

analyser_na <- function(x, datetime) {
  
  # Verifier la longueur des donnees
  if (length(x) != length(datetime)) {
    stop("Les donnees et les dates doivent avoir la meme longueur.")
  }
  
  # Verifier que la serie n'est pas vide
  if (length(x) == 0) {
    stop("La serie est vide.")
  }
  
  # Identifier les valeurs manquantes
  est_na <- is.na(x)
  
  # Si aucune valeur manquante n'existe
  if (!any(est_na)) {
    return(
      data.frame(
        Debut = as.POSIXct(character(), tz = "UTC"),
        Fin = as.POSIXct(character(), tz = "UTC"),
        Nombre_heures = integer()
      )
    )
  }
  
  n <- length(x)
  
  # Identifier les blocs de valeurs manquantes
  if (n > 1) {
    
    ecart <- as.numeric(
      difftime(
        datetime[-1],
        datetime[-n],
        units = "hours"
      )
    )
    
    nouveau_bloc <- c(
      TRUE,
      (est_na[-1] != est_na[-n]) |
        (ecart != 1)
    )
    
  } else {
    
    nouveau_bloc <- TRUE
    
  }
  
  # Numeroter les groupes
  groupe <- cumsum(nouveau_bloc)
  
  # Recuperer les indices des valeurs manquantes
  indices_na <- which(est_na)
  
  # Regrouper les NA consecutifs
  groupes_na <- split(
    indices_na,
    groupe[indices_na]
  )
  
  # Calculer le debut, la fin et la duree de chaque bloc
  resultat <- do.call(
    rbind,
    lapply(groupes_na, function(indices) {
      
      data.frame(
        Debut = min(datetime[indices]),
        Fin = max(datetime[indices]),
        Nombre_heures = length(indices)
      )
      
    })
  )
  
  # Reinitialiser les numeros de lignes
  rownames(resultat) <- NULL
  
  return(resultat)
}


# ============================================================
# 12. ANALYSE DES NA DANS LOAD
# ============================================================

na_load <- analyser_na(
  germany_clean$Load,
  germany_clean$DateTime
)

cat("\n========== NA DANS LOAD ==========\n")

print(na_load)


# ============================================================
# 13. ANALYSE DES NA DANS WIND
# ============================================================

na_wind <- analyser_na(
  germany_clean$Wind,
  germany_clean$DateTime
)

cat("\n========== NA DANS WIND ==========\n")

print(na_wind)


# ============================================================
# 14. ANALYSE DES NA DANS SOLAR
# ============================================================

na_solar <- analyser_na(
  germany_clean$Solar,
  germany_clean$DateTime
)

cat("\n========== NA DANS SOLAR ==========\n")

print(na_solar)


# ============================================================
# 15. SAUVEGARDE DES DONNEES PREPAREES
# ============================================================

write_csv(
  germany_clean,
  "data/processed/germany_energy_timeseries.csv"
)

cat("\nFichier prepare enregistre :\n")
cat("data/processed/germany_energy_timeseries.csv\n")


# ============================================================
# 16. CREATION DE LA VERSION POUR L'ANALYSE
# ============================================================

# Definir le debut de la periode d'analyse
date_debut <- as.POSIXct(
  "2015-01-01 00:00:00",
  tz = "UTC"
)

# Supprimer la premiere observation du 31/12/2014 a 23h
# car Load, Wind et Solar sont tous manquants a cette date.
# Les autres valeurs manquantes sont conservees.

germany_analysis <- germany_clean[
  germany_clean$DateTime >= date_debut,
]

# Verifier les dimensions
cat("\n========== VERSION ANALYTIQUE ==========\n")

cat("\nDimensions :\n")
print(dim(germany_analysis))

# Verifier les valeurs manquantes restantes
cat("\nValeurs manquantes par variable :\n")
print(colSums(is.na(germany_analysis)))

# Verifier la periode
cat("\nPeriode analysee :\n")

print(
  range(
    germany_analysis$DateTime,
    na.rm = TRUE
  )
)

# Verifier les doublons
cat("\nNombre de doublons temporels :\n")
print(sum(duplicated(germany_analysis$DateTime)))

# Sauvegarder la version analytique
write_csv(
  germany_analysis,
  "data/processed/germany_energy_analysis.csv"
)

cat("\nFichier analytique enregistre :\n")
cat("data/processed/germany_energy_analysis.csv\n")


# ============================================================
# 17. RESUME FINAL
# ============================================================

cat("\n")
cat("================================================\n")
cat("PREPARATION DES DONNEES TERMINEE\n")
cat("================================================\n")

cat(
  "Observations dans le fichier original : ",
  nrow(df),
  "\n",
  sep = ""
)

cat(
  "Variables dans le fichier original : ",
  ncol(df),
  "\n",
  sep = ""
)

cat(
  "Observations apres selection de l'Allemagne : ",
  nrow(germany),
  "\n",
  sep = ""
)

cat(
  "Observations apres nettoyage des timestamps : ",
  nrow(germany_clean),
  "\n",
  sep = ""
)

cat(
  "Observations dans la version analytique : ",
  nrow(germany_analysis),
  "\n",
  sep = ""
)

cat(
  "Nombre de variables etudiees : ",
  ncol(germany_analysis),
  "\n",
  sep = ""
)

cat(
  "Valeurs manquantes restantes : ",
  sum(is.na(germany_analysis)),
  "\n",
  sep = ""
)

cat(
  "Timestamps manquants : ",
  sum(is.na(germany_analysis$DateTime)),
  "\n",
  sep = ""
)

cat(
  "Doublons temporels : ",
  sum(duplicated(germany_analysis$DateTime)),
  "\n",
  sep = ""
)

cat("\nFichiers crees :\n")

cat(
  "1. data/processed/germany_energy_timeseries.csv\n"
)

cat(
  "2. data/processed/germany_energy_analysis.csv\n"
)

cat("================================================\n")

