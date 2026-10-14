# ============================================================
# PROJET : SERIES TEMPORELLES
# Analyse exploratoire des donnees (EDA)
# Etude : Consommation et production d'energie en Allemagne
# ============================================================


# ============================================================
# 1. INSTALLATION ET CHARGEMENT DES PACKAGES
# ============================================================

packages <- c(
  "readr",
  "dplyr",
  "ggplot2",
  "lubridate",
  "tidyr"
)

for (pkg in packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg)
  }
}

library(readr)
library(dplyr)
library(ggplot2)
library(lubridate)
library(tidyr)


# ============================================================
# 2. CONFIGURATION DU PROJET
# ============================================================

# Verifier que le repertoire courant est la racine du projet

if (!dir.exists("data/processed")) {
  stop(
    "Le dossier data/processed est introuvable. ",
    "Placez-vous dans la racine du projet."
  )
}

# Creer les dossiers de sortie si necessaire

dir.create("results", showWarnings = FALSE)
dir.create("results/figures", recursive = TRUE,
           showWarnings = FALSE)
dir.create("results/tables", recursive = TRUE,
           showWarnings = FALSE)

# Fichier d'entree
# Ce fichier contient encore les valeurs manquantes
# eventuelles des variables energetiques.

input_file <- "data/processed/germany_energy_analysis.csv"

if (!file.exists(input_file)) {
  stop(
    "Le fichier germany_energy_analysis.csv est introuvable. ",
    "Verifiez le chemin du fichier."
  )
}


# ============================================================
# 3. IMPORTATION DES DONNEES
# ============================================================

germany_clean <- read_csv(
  input_file,
  show_col_types = FALSE
)

# Convertir DateTime en date-heure si necessaire

germany_clean <- germany_clean %>%
  mutate(
    DateTime = as.POSIXct(
      DateTime,
      tz = "UTC"
    )
  ) %>%
  arrange(DateTime)

cat("\n========================================\n")
cat("IMPORTATION DES DONNEES\n")
cat("========================================\n")

cat("Nombre de lignes :", nrow(germany_clean), "\n")
cat("Nombre de colonnes :", ncol(germany_clean), "\n")

cat("\nStructure des donnees :\n")
str(germany_clean)

cat("\nPremieres observations :\n")
print(head(germany_clean))

cat("\nDernieres observations :\n")
print(tail(germany_clean))


# ============================================================
# 4. VERIFICATION DE LA QUALITE DES DONNEES
# ============================================================

cat("\n========================================\n")
cat("QUALITE DES DONNEES\n")
cat("========================================\n")

# Verifier les valeurs manquantes

missing_summary <- data.frame(
  Variable = names(germany_clean),
  Valeurs_manquantes = sapply(
    germany_clean,
    function(x) sum(is.na(x))
  )
)

print(missing_summary)

write_csv(
  missing_summary,
  "results/tables/missing_values.csv"
)

# Verifier les dates dupliquees

duplicate_dates <- sum(
  duplicated(germany_clean$DateTime)
)

cat(
  "\nNombre de dates dupliquees :",
  duplicate_dates,
  "\n"
)

# Verifier les dates manquantes

cat(
  "Nombre de dates manquantes :",
  sum(is.na(germany_clean$DateTime)),
  "\n"
)

# Verifier les intervalles entre observations

time_differences <- diff(
  as.numeric(germany_clean$DateTime)
) / 3600

cat("\nFrequence des intervalles horaires :\n")
print(table(time_differences, useNA = "ifany"))

cat(
  "\nNombre d'intervalles differents de 1 heure :",
  sum(time_differences != 1, na.rm = TRUE),
  "\n"
)


# ============================================================
# 5. STATISTIQUES DESCRIPTIVES
# ============================================================

cat("\n========================================\n")
cat("STATISTIQUES DESCRIPTIVES\n")
cat("========================================\n")

energy_variables <- c("Load", "Wind", "Solar")

# Verifier la presence des variables

if (!all(energy_variables %in% names(germany_clean))) {
  stop("Une ou plusieurs variables energetiques sont absentes.")
}

# Resume statistique general

descriptive_stats <- germany_clean %>%
  select(all_of(energy_variables)) %>%
  pivot_longer(
    cols = everything(),
    names_to = "Variable",
    values_to = "Valeur"
  ) %>%
  group_by(Variable) %>%
  summarise(
    Nombre_observations = sum(!is.na(Valeur)),
    Nombre_manquants = sum(is.na(Valeur)),
    Moyenne = mean(Valeur, na.rm = TRUE),
    Mediane = median(Valeur, na.rm = TRUE),
    Ecart_type = sd(Valeur, na.rm = TRUE),
    Minimum = min(Valeur, na.rm = TRUE),
    Premier_quartile = quantile(
      Valeur, 0.25, na.rm = TRUE
    ),
    Troisieme_quartile = quantile(
      Valeur, 0.75, na.rm = TRUE
    ),
    Maximum = max(Valeur, na.rm = TRUE),
    .groups = "drop"
  )

print(descriptive_stats)

write_csv(
  descriptive_stats,
  "results/tables/descriptive_statistics.csv"
)


# ============================================================
# 6. MOYENNES DES VARIABLES ENERGETIQUES
# ============================================================

energy_means <- germany_clean %>%
  summarise(
    Load_mean = mean(Load, na.rm = TRUE),
    Wind_mean = mean(Wind, na.rm = TRUE),
    Solar_mean = mean(Solar, na.rm = TRUE)
  )

cat("\nMoyennes des variables energetiques :\n")
print(energy_means)

write_csv(
  energy_means,
  "results/tables/energy_means.csv"
)


# ============================================================
# 7. EVOLUTION TEMPORELLE DES VARIABLES
# ============================================================

# Fonction pour creer et enregistrer une serie temporelle

plot_time_series <- function(data, variable, couleur, titre) {
  
  p <- ggplot(
    data,
    aes(
      x = DateTime,
      y = .data[[variable]]
    )
  ) +
    geom_line(
      color = couleur,
      linewidth = 0.35,
      na.rm = TRUE
    ) +
    labs(
      title = titre,
      subtitle = "Periode d'etude : 2015-2020",
      x = "Date",
      y = "Valeur",
      caption = "Source : donnees energetiques de l'Allemagne"
    ) +
    theme_minimal(base_size = 12) +
    theme(
      plot.title = element_text(
        face = "bold",
        size = 14
      ),
      axis.text.x = element_text(
        angle = 45,
        hjust = 1
      )
    )
  
  print(p)
  
  ggsave(
    filename = paste0(
      "results/figures/",
      variable,
      "_time_series.png"
    ),
    plot = p,
    width = 12,
    height = 5,
    dpi = 300
  )
  
  return(p)
}

p_load <- plot_time_series(
  germany_clean,
  "Load",
  "steelblue",
  "Evolution temporelle de la consommation d'energie"
)

p_wind <- plot_time_series(
  germany_clean,
  "Wind",
  "darkgreen",
  "Evolution temporelle de la production eolienne"
)

p_solar <- plot_time_series(
  germany_clean,
  "Solar",
  "orange",
  "Evolution temporelle de la production solaire"
)


# ============================================================
# 8. PREPARATION DES VARIABLES CALENDAIRES
# ============================================================

germany_clean <- germany_clean %>%
  mutate(
    Hour = hour(DateTime),
    Day = wday(
      DateTime,
      label = TRUE,
      abbr = FALSE,
      week_start = 1
    ),
    Month = month(
      DateTime,
      label = TRUE,
      abbr = FALSE
    ),
    Year = year(DateTime)
  )

cat("\nVariables calendaires ajoutees.\n")
print(head(germany_clean))


# ============================================================
# 9. ANALYSE DES PROFILS HORAIRES
# ============================================================

hourly_summary <- germany_clean %>%
  group_by(Hour) %>%
  summarise(
    Load_mean = mean(Load, na.rm = TRUE),
    Wind_mean = mean(Wind, na.rm = TRUE),
    Solar_mean = mean(Solar, na.rm = TRUE),
    .groups = "drop"
  )

print(hourly_summary)

write_csv(
  hourly_summary,
  "results/tables/hourly_summary.csv"
)

# Transformer le tableau pour faciliter les graphiques

hourly_long <- hourly_summary %>%
  pivot_longer(
    cols = c(Load_mean, Wind_mean, Solar_mean),
    names_to = "Variable",
    values_to = "Moyenne"
  ) %>%
  mutate(
    Variable = recode(
      Variable,
      Load_mean = "Load",
      Wind_mean = "Wind",
      Solar_mean = "Solar"
    )
  )

p_hourly <- ggplot(
  hourly_long,
  aes(
    x = Hour,
    y = Moyenne,
    color = Variable
  )
) +
  geom_line(linewidth = 1) +
  geom_point(size = 1.8) +
  scale_x_continuous(
    breaks = 0:23
  ) +
  labs(
    title = "Profil horaire moyen de l'energie",
    x = "Heure de la journee",
    y = "Valeur moyenne",
    color = "Variable"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold")
  )

print(p_hourly)

ggsave(
  "results/figures/hourly_profiles.png",
  p_hourly,
  width = 10,
  height = 6,
  dpi = 300
)


# ============================================================
# 10. ANALYSE DU PROFIL HEBDOMADAIRE
# ============================================================

weekly_summary <- germany_clean %>%
  group_by(Day) %>%
  summarise(
    Load_mean = mean(Load, na.rm = TRUE),
    Wind_mean = mean(Wind, na.rm = TRUE),
    Solar_mean = mean(Solar, na.rm = TRUE),
    .groups = "drop"
  )

print(weekly_summary)

write_csv(
  weekly_summary,
  "results/tables/weekly_summary.csv"
)

weekly_long <- weekly_summary %>%
  pivot_longer(
    cols = c(Load_mean, Wind_mean, Solar_mean),
    names_to = "Variable",
    values_to = "Moyenne"
  ) %>%
  mutate(
    Variable = recode(
      Variable,
      Load_mean = "Load",
      Wind_mean = "Wind",
      Solar_mean = "Solar"
    )
  )

p_weekly <- ggplot(
  weekly_long,
  aes(
    x = Day,
    y = Moyenne,
    fill = Variable
  )
) +
  geom_col(
    position = "dodge"
  ) +
  labs(
    title = "Profil hebdomadaire moyen",
    x = "Jour de la semaine",
    y = "Valeur moyenne",
    fill = "Variable"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold"),
    axis.text.x = element_text(
      angle = 35,
      hjust = 1
    )
  )

print(p_weekly)

ggsave(
  "results/figures/weekly_profiles.png",
  p_weekly,
  width = 10,
  height = 6,
  dpi = 300
)


# ============================================================
# 11. ANALYSE DES PROFILS MENSUELS
# ============================================================

monthly_summary <- germany_clean %>%
  group_by(Month) %>%
  summarise(
    Load_mean = mean(Load, na.rm = TRUE),
    Wind_mean = mean(Wind, na.rm = TRUE),
    Solar_mean = mean(Solar, na.rm = TRUE),
    .groups = "drop"
  )

print(monthly_summary)

write_csv(
  monthly_summary,
  "results/tables/monthly_summary.csv"
)

monthly_long <- monthly_summary %>%
  pivot_longer(
    cols = c(Load_mean, Wind_mean, Solar_mean),
    names_to = "Variable",
    values_to = "Moyenne"
  ) %>%
  mutate(
    Variable = recode(
      Variable,
      Load_mean = "Load",
      Wind_mean = "Wind",
      Solar_mean = "Solar"
    )
  )

p_monthly <- ggplot(
  monthly_long,
  aes(
    x = Month,
    y = Moyenne,
    fill = Variable
  )
) +
  geom_col(
    position = "dodge"
  ) +
  labs(
    title = "Profil mensuel moyen",
    x = "Mois",
    y = "Valeur moyenne",
    fill = "Variable"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold"),
    axis.text.x = element_text(
      angle = 45,
      hjust = 1
    )
  )

print(p_monthly)

ggsave(
  "results/figures/monthly_profiles.png",
  p_monthly,
  width = 12,
  height = 6,
  dpi = 300
)


# ============================================================
# 12. EVOLUTION ANNUELLE
# ============================================================

yearly_summary <- germany_clean %>%
  group_by(Year) %>%
  summarise(
    Load_mean = mean(Load, na.rm = TRUE),
    Wind_mean = mean(Wind, na.rm = TRUE),
    Solar_mean = mean(Solar, na.rm = TRUE),
    .groups = "drop"
  )

print(yearly_summary)

write_csv(
  yearly_summary,
  "results/tables/yearly_summary.csv"
)

yearly_long <- yearly_summary %>%
  pivot_longer(
    cols = c(Load_mean, Wind_mean, Solar_mean),
    names_to = "Variable",
    values_to = "Moyenne"
  ) %>%
  mutate(
    Variable = recode(
      Variable,
      Load_mean = "Load",
      Wind_mean = "Wind",
      Solar_mean = "Solar"
    )
  )

p_yearly <- ggplot(
  yearly_long,
  aes(
    x = Year,
    y = Moyenne,
    color = Variable,
    group = Variable
  )
) +
  geom_line(linewidth = 1) +
  geom_point(size = 2) +
  scale_x_continuous(
    breaks = sort(unique(germany_clean$Year))
  ) +
  labs(
    title = "Evolution annuelle moyenne",
    x = "Annee",
    y = "Valeur moyenne",
    color = "Variable"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold")
  )

print(p_yearly)

ggsave(
  "results/figures/yearly_profiles.png",
  p_yearly,
  width = 10,
  height = 6,
  dpi = 300
)


# ============================================================
# 13. ANALYSE DES VALEURS MANQUANTES DANS LE TEMPS
# ============================================================

missing_by_date <- germany_clean %>%
  filter(
    is.na(Load) |
      is.na(Wind) |
      is.na(Solar)
  ) %>%
  select(
    DateTime,
    Load,
    Wind,
    Solar
  )

cat(
  "\nNombre de dates avec au moins une valeur manquante :",
  nrow(missing_by_date),
  "\n"
)

write_csv(
  missing_by_date,
  "results/tables/missing_dates.csv"
)

missing_long <- germany_clean %>%
  select(
    DateTime,
    all_of(energy_variables)
  ) %>%
  pivot_longer(
    cols = all_of(energy_variables),
    names_to = "Variable",
    values_to = "Valeur"
  ) %>%
  mutate(
    Manquante = is.na(Valeur)
  )

p_missing <- ggplot(
  missing_long %>% filter(Manquante),
  aes(
    x = DateTime,
    y = Variable
  )
) +
  geom_point(
    color = "red",
    size = 0.7
  ) +
  labs(
    title = "Repartition temporelle des valeurs manquantes",
    x = "Date",
    y = "Variable"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold")
  )

print(p_missing)

ggsave(
  "results/figures/missing_values.png",
  p_missing,
  width = 12,
  height = 5,
  dpi = 300
)


# ============================================================
# 14. PERIODE D'ETUDE ET DUREE
# ============================================================

first_date <- min(
  germany_clean$DateTime,
  na.rm = TRUE
)

last_date <- max(
  germany_clean$DateTime,
  na.rm = TRUE
)

duration_days <- as.numeric(
  difftime(
    last_date,
    first_date,
    units = "days"
  )
)

cat("\n========================================\n")
cat("PERIODE D'ETUDE\n")
cat("========================================\n")

cat("Premiere date :", as.character(first_date), "\n")
cat("Derniere date :", as.character(last_date), "\n")
cat("Duree en jours :", duration_days, "\n")
cat("Duree en annees :", round(duration_days / 365.25, 2), "\n")


# ============================================================
# 15. VERIFICATIONS FINALES
# ============================================================

cat("\n========================================\n")
cat("VERIFICATIONS FINALES\n")
cat("========================================\n")

cat("Nombre final de lignes :", nrow(germany_clean), "\n")
cat("Nombre final de colonnes :", ncol(germany_clean), "\n")

cat("\nValeurs manquantes par variable energetique :\n")

print(
  sapply(
    germany_clean[energy_variables],
    function(x) sum(is.na(x))
  )
)

cat(
  "\nNombre de dates dupliquees :",
  sum(duplicated(germany_clean$DateTime)),
  "\n"
)

cat("\nFichiers produits :\n")
cat("- results/tables/descriptive_statistics.csv\n")
cat("- results/tables/energy_means.csv\n")
cat("- results/tables/hourly_summary.csv\n")
cat("- results/tables/weekly_summary.csv\n")
cat("- results/tables/monthly_summary.csv\n")
cat("- results/tables/yearly_summary.csv\n")
cat("- results/tables/missing_values.csv\n")
cat("- results/tables/missing_dates.csv\n")
cat("- results/figures/Load_time_series.png\n")
cat("- results/figures/Wind_time_series.png\n")
cat("- results/figures/Solar_time_series.png\n")
cat("- results/figures/hourly_profiles.png\n")
cat("- results/figures/weekly_profiles.png\n")
cat("- results/figures/monthly_profiles.png\n")
cat("- results/figures/yearly_profiles.png\n")
cat("- results/figures/missing_values.png\n")


cat("\nAnalyse exploratoire terminee avec succes !\n")


