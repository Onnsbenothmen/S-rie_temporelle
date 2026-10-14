# ============================================================
# MINI-PROJET - SERIES TEMPORELLES
# DATA SCIENCE & IA
#
# 03 - DIAGNOSTICS : STATIONNARITE
#
# Donnees : Allemagne
# Variables :
#   - Load  : consommation electrique
#   - Wind  : production eolienne
#   - Solar : production solaire
# ============================================================


# ============================================================
# 1. CHARGEMENT DES PACKAGES
# ============================================================

library(readr)
library(dplyr)
library(ggplot2)
library(forecast)
library(tseries)


# ============================================================
# 2. CHARGEMENT DES DONNEES
# ============================================================

germany_clean <- read_csv(
  "data/processed/germany_energy_analysis.csv"
)

cat("\n")
cat("============================================================\n")
cat("DONNEES CHARGEES\n")
cat("============================================================\n")

cat("Nombre de lignes :", nrow(germany_clean), "\n")
cat("Nombre de colonnes :", ncol(germany_clean), "\n")


# ============================================================
# 3. VERIFICATION DES VALEURS MANQUANTES
# ============================================================

cat("\n")
cat("============================================================\n")
cat("VALEURS MANQUANTES\n")
cat("============================================================\n")

print(
  colSums(
    is.na(
      germany_clean[
        ,
        c("DateTime", "Load", "Wind", "Solar")
      ]
    )
  )
)


# ============================================================
# 4. PREPARATION DES SERIES
# ============================================================
#
# Pour les tests statistiques, nous devons disposer de series
# sans valeurs manquantes.
#
# Les valeurs manquantes sont tres rares dans notre dataset.
# Ici, on retire uniquement les observations manquantes pour
# effectuer les tests de stationnarite.
#
# Le traitement definitif des valeurs manquantes sera justifie
# avant la modelisation.
# ============================================================

load_series <- germany_clean$Load[
  !is.na(germany_clean$Load)
]

wind_series <- germany_clean$Wind[
  !is.na(germany_clean$Wind)
]

solar_series <- germany_clean$Solar[
  !is.na(germany_clean$Solar)
]


cat("\n")
cat("Nombre d'observations utilisees :\n")

cat("Load  :", length(load_series), "\n")
cat("Wind  :", length(wind_series), "\n")
cat("Solar :", length(solar_series), "\n")


# ============================================================
# 5. CREATION DES SERIES TEMPORELLES
# ============================================================

load_ts <- ts(
  load_series,
  frequency = 24
)

wind_ts <- ts(
  wind_series,
  frequency = 24
)

solar_ts <- ts(
  solar_series,
  frequency = 24
)


# ============================================================
# 6. VISUALISATION DES SERIES
# ============================================================

cat("\n")
cat("============================================================\n")
cat("VISUALISATION DES SERIES\n")
cat("============================================================\n")


plot(
  load_ts,
  main = "Serie temporelle - Load",
  xlab = "Temps",
  ylab = "Load"
)


plot(
  wind_ts,
  main = "Serie temporelle - Wind",
  xlab = "Temps",
  ylab = "Wind"
)


plot(
  solar_ts,
  main = "Serie temporelle - Solar",
  xlab = "Temps",
  ylab = "Solar"
)


# ============================================================
# 7. ACF ET PACF - LOAD\n# ============================================================

cat("\n")
cat("============================================================\n")
cat("ACF / PACF - LOAD\n")
cat("============================================================\n")


acf(
  load_ts,
  lag.max = 168,
  main = "ACF - Load"
)

pacf(
  load_ts,
  lag.max = 168,
  main = "PACF - Load"
)


# ============================================================
# 8. ACF ET PACF - WIND\n# ============================================================

cat("\n")
cat("============================================================\n")
cat("ACF / PACF - WIND\n")
cat("============================================================\n")


acf(
  wind_ts,
  lag.max = 168,
  main = "ACF - Wind"
)

pacf(
  wind_ts,
  lag.max = 168,
  main = "PACF - Wind"
)


# ============================================================
# 9. ACF ET PACF - SOLAR\n# ============================================================

cat("\n")
cat("============================================================\n")
cat("ACF / PACF - SOLAR\n")
cat("============================================================\n")


acf(
  solar_ts,
  lag.max = 168,
  main = "ACF - Solar"
)

pacf(
  solar_ts,
  lag.max = 168,
  main = "PACF - Solar"
)


# ============================================================
# 10. TEST ADF - AUGMENTED DICKEY-FULLER
# ============================================================
#
# H0 : la serie possede une racine unitaire
#      => serie non stationnaire
#
# H1 : la serie est stationnaire
#
# Si p-value < 0.05 :
#      on rejette H0
#      => serie stationnaire
#
# Si p-value >= 0.05 :
#      on ne rejette pas H0
#      => serie probablement non stationnaire
# ============================================================

cat("\n")
cat("============================================================\n")
cat("TEST ADF\n")
cat("============================================================\n")


adf_load <- adf.test(
  load_ts,
  alternative = "stationary"
)

adf_wind <- adf.test(
  wind_ts,
  alternative = "stationary"
)

adf_solar <- adf.test(
  solar_ts,
  alternative = "stationary"
)


cat("\n--- ADF Load ---\n")
print(adf_load)

cat("\n--- ADF Wind ---\n")
print(adf_wind)

cat("\n--- ADF Solar ---\n")
print(adf_solar)


# ============================================================
# 11. TEST KPSS
# ============================================================
#
# H0 : la serie est stationnaire
#
# H1 : la serie est non stationnaire
#
# Si p-value < 0.05 :
#      on rejette H0
#      => serie non stationnaire
#
# Si p-value >= 0.05 :
#      on ne rejette pas H0
#      => serie compatible avec la stationnarite
# ============================================================

cat("\n")
cat("============================================================\n")
cat("TEST KPSS\n")
cat("============================================================\n")


kpss_load <- kpss.test(
  load_ts,
  null = "Level"
)

kpss_wind <- kpss.test(
  wind_ts,
  null = "Level"
)

kpss_solar <- kpss.test(
  solar_ts,
  null = "Level"
)


cat("\n--- KPSS Load ---\n")
print(kpss_load)

cat("\n--- KPSS Wind ---\n")
print(kpss_wind)

cat("\n--- KPSS Solar ---\n")
print(kpss_solar)


# ============================================================
# 12. DIFFERENCIATION
# ============================================================

cat("\n")
cat("============================================================\n")
cat("DIFFERENCIATION\n")
cat("============================================================\n")


load_diff <- diff(load_ts)

wind_diff <- diff(wind_ts)

solar_diff <- diff(solar_ts)


cat("\nNombre d'observations apres differenciation :\n")

cat("Load  :", length(load_diff), "\n")
cat("Wind  :", length(wind_diff), "\n")
cat("Solar :", length(solar_diff), "\n")


# ============================================================
# 13. VISUALISATION DES SERIES DIFFERENCIEES
# ============================================================

cat("\n")
cat("============================================================\n")
cat("SERIES APRES DIFFERENCIATION\n")
cat("============================================================\n")


plot(
  load_diff,
  main = "Load apres differenciation",
  xlab = "Temps",
  ylab = "Difference Load"
)


plot(
  wind_diff,
  main = "Wind apres differenciation",
  xlab = "Temps",
  ylab = "Difference Wind"
)


plot(
  solar_diff,
  main = "Solar apres differenciation",
  xlab = "Temps",
  ylab = "Difference Solar"
)


# ============================================================
# 14. ACF / PACF APRES DIFFERENCIATION - LOAD
# ============================================================

cat("\n")
cat("============================================================\n")
cat("ACF / PACF LOAD APRES DIFFERENCIATION\n")
cat("============================================================\n")


acf(
  load_diff,
  lag.max = 168,
  main = "ACF - Load differenciee"
)

pacf(
  load_diff,
  lag.max = 168,
  main = "PACF - Load differenciee"
)


# ============================================================
# 15. ACF / PACF APRES DIFFERENCIATION - WIND
# ============================================================

cat("\n")
cat("============================================================\n")
cat("ACF / PACF WIND APRES DIFFERENCIATION\n")
cat("============================================================\n")


acf(
  wind_diff,
  lag.max = 168,
  main = "ACF - Wind differenciee"
)

pacf(
  wind_diff,
  lag.max = 168,
  main = "PACF - Wind differenciee"
)


# ============================================================
# 16. ACF / PACF APRES DIFFERENCIATION - SOLAR
# ============================================================

cat("\n")
cat("============================================================\n")
cat("ACF / PACF SOLAR APRES DIFFERENCIATION\n")
cat("============================================================\n")


acf(
  solar_diff,
  lag.max = 168,
  main = "ACF - Solar differenciee"
)

pacf(
  solar_diff,
  lag.max = 168,
  main = "PACF - Solar differenciee"
)


# ============================================================
# 17. TEST ADF APRES DIFFERENCIATION
# ============================================================

cat("\n")
cat("============================================================\n")
cat("ADF APRES DIFFERENCIATION\n")
cat("============================================================\n")


adf_load_diff <- adf.test(
  load_diff,
  alternative = "stationary"
)

adf_wind_diff <- adf.test(
  wind_diff,
  alternative = "stationary"
)

adf_solar_diff <- adf.test(
  solar_diff,
  alternative = "stationary"
)


cat("\n--- ADF Load differenciee ---\n")
print(adf_load_diff)

cat("\n--- ADF Wind differenciee ---\n")
print(adf_wind_diff)

cat("\n--- ADF Solar differenciee ---\n")
print(adf_solar_diff)


# ============================================================
# 18. KPSS APRES DIFFERENCIATION
# ============================================================

cat("\n")
cat("============================================================\n")
cat("KPSS APRES DIFFERENCIATION\n")
cat("============================================================\n")


kpss_load_diff <- kpss.test(
  load_diff,
  null = "Level"
)

kpss_wind_diff <- kpss.test(
  wind_diff,
  null = "Level"
)

kpss_solar_diff <- kpss.test(
  solar_diff,
  null = "Level"
)


cat("\n--- KPSS Load differenciee ---\n")
print(kpss_load_diff)

cat("\n--- KPSS Wind differenciee ---\n")
print(kpss_wind_diff)

cat("\n--- KPSS Solar differenciee ---\n")
print(kpss_solar_diff)


# ============================================================
# 19. RESUME DES TESTS
# ============================================================

cat("\n")
cat("============================================================\n")
cat("RESUME - STATIONNARITE\n")
cat("============================================================\n")


cat("\n")
cat("ADF - serie originale\n")

cat(
  "Load  p-value :",
  adf_load$p.value,
  "\n"
)

cat(
  "Wind  p-value :",
  adf_wind$p.value,
  "\n"
)

cat(
  "Solar p-value :",
  adf_solar$p.value,
  "\n"
)


cat("\n")
cat("KPSS - serie originale\n")

cat(
  "Load  p-value :",
  kpss_load$p.value,
  "\n"
)

cat(
  "Wind  p-value :",
  kpss_wind$p.value,
  "\n"
)

cat(
  "Solar p-value :",
  kpss_solar$p.value,
  "\n"
)


cat("\n")
cat("ADF - serie differenciee\n")

cat(
  "Load  p-value :",
  adf_load_diff$p.value,
  "\n"
)

cat(
  "Wind  p-value :",
  adf_wind_diff$p.value,
  "\n"
)

cat(
  "Solar p-value :",
  adf_solar_diff$p.value,
  "\n"
)


cat("\n")
cat("KPSS - serie differenciee\n")

cat(
  "Load  p-value :",
  kpss_load_diff$p.value,
  "\n"
)

cat(
  "Wind  p-value :",
  kpss_wind_diff$p.value,
  "\n"
)

cat(
  "Solar p-value :",
  kpss_solar_diff$p.value,
  "\n"
)


# ============================================================
# 20. SAUVEGARDE DES FIGURES ET DU TABLEAU DE STATIONNARITE
# ============================================================
# La version precedente n'ecrivait rien sur disque (tout a la console).
# On enregistre ici les correlogrammes ACF/PACF et un tableau recapitulatif
# des tests ADF/KPSS, sous prefixe R_ (le tableau Python s'appelle
# stationarity_tests.csv ; celui-ci est R_stationarity_tests.csv).

dir.create("results/figures", recursive = TRUE, showWarnings = FALSE)
dir.create("results/tables",  recursive = TRUE, showWarnings = FALSE)

sauver_acf_pacf <- function(serie, nom) {
  png(file.path("results", "figures", paste0("R_acf_pacf_", nom, ".png")),
      width = 1400, height = 1000, res = 130)
  par(mfrow = c(2, 1))
  acf(serie,  lag.max = 168, main = paste0("ACF - ", nom))
  pacf(serie, lag.max = 168, main = paste0("PACF - ", nom))
  dev.off()
}

# Series brutes
sauver_acf_pacf(load_ts,  "Load_raw")
sauver_acf_pacf(wind_ts,  "Wind_raw")
sauver_acf_pacf(solar_ts, "Solar_raw")
# Series differencees (ordre 1)
sauver_acf_pacf(load_diff,  "Load_d1")
sauver_acf_pacf(wind_diff,  "Wind_d1")
sauver_acf_pacf(solar_diff, "Solar_d1")

# Tableau recapitulatif ADF / KPSS (brute et d1)
resume_stationnarite <- data.frame(
  Variable   = rep(c("Load", "Wind", "Solar"), each = 2),
  Transformation = rep(c("brute", "d1"), times = 3),
  ADF_stat = c(adf_load$statistic, adf_load_diff$statistic,
               adf_wind$statistic, adf_wind_diff$statistic,
               adf_solar$statistic, adf_solar_diff$statistic),
  ADF_p    = c(adf_load$p.value, adf_load_diff$p.value,
               adf_wind$p.value, adf_wind_diff$p.value,
               adf_solar$p.value, adf_solar_diff$p.value),
  KPSS_stat = c(kpss_load$statistic, kpss_load_diff$statistic,
                kpss_wind$statistic, kpss_wind_diff$statistic,
                kpss_solar$statistic, kpss_solar_diff$statistic),
  KPSS_p    = c(kpss_load$p.value, kpss_load_diff$p.value,
                kpss_wind$p.value, kpss_wind_diff$p.value,
                kpss_solar$p.value, kpss_solar_diff$p.value),
  stringsAsFactors = FALSE
)
resume_stationnarite$ADF_stationnaire  <- resume_stationnarite$ADF_p  < 0.05
resume_stationnarite$KPSS_stationnaire <- resume_stationnarite$KPSS_p >= 0.05
resume_stationnarite$Conclusion_stationnaire <-
  resume_stationnarite$ADF_stationnaire & resume_stationnarite$KPSS_stationnaire

write.csv(resume_stationnarite,
          "results/tables/R_stationarity_tests.csv", row.names = FALSE)

cat("\nFigures ACF/PACF sauvegardees dans results/figures/ (prefixe R_acf_pacf_).\n")
cat("Tableau : results/tables/R_stationarity_tests.csv\n")


# ============================================================
# 21. FIN
# ============================================================

cat("\n")
cat("============================================================\n")
cat("FIN DE L'ANALYSE DE STATIONNARITE\n")
cat("============================================================\n")

