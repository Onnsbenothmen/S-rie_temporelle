# ============================================================
# 04_ARIMA_SARIMA.R
# SECTION 3.1 - Modelisation ARIMA / SARIMA (socle classique R)
# Serie temporelle energetique - Allemagne (ENTSO-E)
#
# Objectifs :
#   1. Ordres choisis via ACF/PACF (EDA) puis compares a auto.arima
#   2. Diagnostic des residus : Ljung-Box, Jarque-Bera, test ARCH-LM
#   3. Previsions h = jeu de test + metriques (MSE, RMSE, MAE, MAPE)
#
# POURQUOI ce script ?
#   - Il formalise le socle classique exigé (code R ET Python).
#   - Chaque choix est justifié en commentaire pour la défense orale.
# ============================================================

suppressMessages({
  library(readr)      # lecture des fichiers
  library(forecast)   # auto.arima, Arima, forecast, checkresiduals
  library(tseries)    # jarque.bera.test
})

set.seed(123)         # reproductibilite (aucun tirage ici, mais bonne pratique)


# ============================================================
# 1. CHARGEMENT + INTERPOLATION DES MANQUANTS
# ============================================================
# Pourquoi interpoler MAINTENANT et pas dans l'EDA ?
#   Les NA sont des heures isolees (74 pour Wind, 103 pour Solar) :
#   une interpolation precoce fausserait l'exploration. En revanche,
#   un modele ARIMA exige une serie complete -> na.interp (forecast),
#   interpolation lineaire sensible a la saisonnalite.
# POURQUOI pas une suppression des lignes NA ?
#   Supprimer briserait la regularite horaire (frequency = 24).

df <- read_csv("data/processed/germany_energy_analysis.csv",
               show_col_types = FALSE)
df <- df[order(df$DateTime), ]

df$Load  <- na.interp(df$Load)
df$Wind  <- na.interp(df$Wind)
df$Solar <- na.interp(df$Solar)

cat("================================================================\n")
cat("DONNEES : ", nrow(df), " observations, NA traites par interpolation\n")
print(colSums(is.na(df[c("Load", "Wind", "Solar")])))
cat("================================================================\n")


# ============================================================
# 2. SPLIT CHRONOLOGIQUE 90 % / 10 %
# ============================================================
# POURQUOI chronologique et jamais aleatoire ?
#   Un split aleatoire fui terait l'information future dans le train
#   et surestimerait artificiellement la performance des modeles.

n <- nrow(df)
n_train <- floor(0.90 * n)          # 45360 observations
n_test  <- n - n_train              # 5040 observations

test_start_idx <- n_train + 1

cat("Train :", n_train,
    "| Test :", n_test,
    "| debut du test :",
    format(df$DateTime[test_start_idx], "%Y-%m-%d %H:%M"), "\n")

# Passe-temps en serie ts horaire (frequency = 24 = cycle quotidien)
make_train_ts <- function(x) ts(x[1:n_train], frequency = 24)
make_test_ts  <- function(x) ts(x[test_start_idx:n], frequency = 24)

# La saisonnalite hebdomadaire (m=168) existe (ACF a 168 elevee) mais
# un SARIMA classique a m=168 est trop lourd sur 45 000 points.
# Choix : SARIMA m=24 (cycle quotidien), la saisonnalite hebdomadaire
# sera traitee par d'autres outils (regresseurs de Fourier / LSTM).


# ============================================================
# 3. FONCTIONS UTILITAIRES
# ============================================================

# Metriques de performance (MAPE sans division par zero)
metriques <- function(actual, predicted) {
  mse  <- mean((actual - predicted)^2)
  rmse <- sqrt(mse)
  mae  <- mean(abs(actual - predicted))
  val  <- actual != 0
  mape <- mean(abs((actual[val] - predicted[val]) / actual[val])) * 100
  data.frame(MSE = mse, RMSE = rmse, MAE = mae, MAPE = mape)
}

# Construction d'une matrice de retards (stats::lag ne gère pas
# plusieurs retards sur un vecteur nu)
build_lags <- function(x, q) {
  n <- length(x)
  out <- matrix(NA_real_, nrow = n, ncol = q)
  for (k in 1:q) {
    if (k < n) out[(k + 1):n, k] <- x[1:(n - k)]
  }
  colnames(out) <- paste0("L", 1:q)
  as.data.frame(out)
}

# Test ARCH-LM implemente manuellement (package FinTS non installe).
# Idea : si les residus ont de la volatilite, le carre des residus
# est autocorrele -> on regresse e^2 sur ses 12 retards et on calcule
# LM = n * R^2 ~ chi2(12) sous H0 "pas d'effet ARCH".
arch_lm_test <- function(resid, q = 12) {
  e2  <- resid^2
  lagged <- build_lags(e2, q)
  m <- lm(e2 ~ ., data = lagged, na.action = na.omit)
  lm <- length(predict(m)) * summary(m)$r.squared
  p  <- pchisq(lm, df = q, lower.tail = FALSE)
  list(statistic = lm, p.value = p, q = q)
}

# Diagnostic complet des residus d'un modele ARIMA
diagnostiquer <- function(model, nom) {
  residus <- as.numeric(stats::residuals(model))
  # Nombre de parametres ARMA pour degres de liberte du Ljung-Box
  ord <- arimaorder(model)                      # p d q  P D Q m
  fitdf <- ord["p"] + ord["q"] + ord["P"] + ord["Q"]

  lb  <- Box.test(residus, lag = 24, type = "Ljung-Box", fitdf = fitdf)
  jb  <- jarque.bera.test(residus)              # normalite (n>5000)
  ar  <- arch_lm_test(residus, q = 12)          # effet ARCH

  cat("\n--- Diagnostic :", nom, "---\n")
  cat("Ljung-Box (lag 24)  : stat =", round(lb$statistic, 1),
      " p =", round(lb$p.value, 4), "\n")
  cat("Jarque-Bera         : stat =", round(jb$statistic, 1),
      " p < 2.2e-16 (normalite rejetee) \n")
  cat("ARCH-LM (12 retards): stat =", round(ar$statistic, 1),
      " p =", format(ar$p.value, digits = 3), "\n")

  data.frame(
    Variable     = nom,
    LB_stat      = round(lb$statistic, 2),  LB_p        = lb$p.value,
    JB_stat      = round(jb$statistic, 2),  JB_p        = jb$p.value,
    ARCH_stat    = round(ar$statistic, 2),  ARCH_p      = ar$p.value,
    LjungBox_OK  = lb$p.value > 0.05,       JB_normal_OK = jb$p.value > 0.05,
    ARCH_absent  = ar$p.value > 0.05,
    stringsAsFactors = FALSE
  )
}


# ============================================================
# 4. BOUCLE SUR LES 3 SERIES
# ============================================================

variables <- c("Load", "Wind", "Solar")
modeles   <- list()   # pour ne pas perdre les modeles
table_comp <- data.frame()
table_diag <- data.frame()
table_met  <- data.frame()

for (v in variables) {

  cat("\n\n####################################################\n")
  cat("SERIE :", v, "\n")
  cat("####################################################\n")

  train <- make_train_ts(df[[v]])
  test  <- make_test_ts(df[[v]])

  # ----------------------------------------------------------
  # 4.1 Modele MANUEL guide par l'ACF/PACF (EDA)
  #     L'EDA montre : d=1 requis, saisonnalite quotidienne forte
  #     (rebonds ACF/PACF a 24 et 168) -> SARIMA(1,1,1)(1,1,1)_24
  #     comme candidat parcimonieux genere par les correlogrammes.
  # ----------------------------------------------------------
  manuel <- tryCatch(
    Arima(train, order = c(1, 1, 1), seasonal = c(1, 1, 1), method = "ML"),
    error = function(e) NA
  )

  # ----------------------------------------------------------
  # 4.2 auto.arima NON saisonnier  (d force a 1, issu de l'EDA)
  #     Reference "ARIMA" du comparatif.
  # ----------------------------------------------------------
  auto_ar <- auto.arima(train, d = 1, seasonal = FALSE,
                        stepwise = TRUE, approximation = TRUE)

  # ----------------------------------------------------------
  # 4.3 auto.arima SAISONNIER (SARIMA m=24)
  #     Reference "SARIMA" : recherche bornee pour rester raisonnable.
  # ----------------------------------------------------------
  auto_sa <- auto.arima(train, d = 1, seasonal = TRUE,
                        stepwise = TRUE, approximation = TRUE,
                        max.p = 2, max.q = 2, max.P = 1, max.Q = 1)

  # ----------------------------------------------------------
  # 4.4 Comparaison AIC / AICc / BIC
  # ----------------------------------------------------------
  ligne <- function(lab, mdl) {
    data.frame(Variable = v, Modele = lab,
               AIC = AIC(mdl), AICc = mdl$aicc, BIC = BIC(mdl),
               Spec = paste0("ARIMA", paste(arimaorder(mdl), collapse = ",")),
               stringsAsFactors = FALSE)
  }
  comp <- rbind(ligne("SARIMA_manuel", manuel),
                ligne("ARIMA_auto",   auto_ar),
                ligne("SARIMA_auto",  auto_sa))
  table_comp <- rbind(table_comp, comp)
  print(comp)

  # Selection du modele retenu : on minimise UNIQUEMENT l'AICc (critere
  # d'information corrige pour petits echantillons) parmi les trois
  # candidats. L'ancienne version melangeait AIC et AICc
  # (auto_sa$aicc < AIC(meilleur)), ce qui rendait le modele utilise pour
  # les diagnostics ('meilleur') potentiellement different du modele
  # annonce ('choix'). Desormais les deux sont identiques et bases sur AICc.
  i_best   <- which.min(comp$AICc)
  choix    <- as.character(comp$Modele[i_best])
  meilleur <- switch(choix,
                     SARIMA_manuel = manuel,
                     ARIMA_auto    = auto_ar,
                     SARIMA_auto   = auto_sa)
  cat("\nModele retenu (AICc minimal) :", choix, "\n")

  # ----------------------------------------------------------
  # 4.5 Diagnostic des residus du meilleur modele
  # ----------------------------------------------------------
  diag <- diagnostiquer(meilleur, v)
  table_diag <- rbind(table_diag, diag)

  # Graphique de diagnostic sauvegarde
  png(file.path("results", "figures",
                paste0("R_resid_", v, ".png")), width = 1600, height = 1000, res = 140)
  checkresiduals(meilleur)
  dev.off()

  # ----------------------------------------------------------
  # 4.6 Previsions et metriques
  #     Le cahier des charges demande des previsions a h = 5-10 pas.
  #     On evalue donc principalement a h = 24 (une journee) et h = 10 ;
  #     la trajectoire h = 5040 est conservee pour DOCUMENTER la divergence
  #     multi-pas des modeles (resultat honnete, discute dans le rapport).
  # ----------------------------------------------------------
  for (lab in c("SARIMA_manuel", "ARIMA_auto", "SARIMA_auto")) {
    mdl <- switch(lab,
      SARIMA_manuel = manuel, ARIMA_auto = auto_ar, SARIMA_auto = auto_sa)
    if (inherits(mdl, "Arima")) {
      for (h in c(10, 24, n_test)) {
        fc <- forecast(mdl, h = h)
        met <- metriques(as.numeric(test[1:h]), as.numeric(fc$mean))
        met <- cbind(Variable = v, Modele = lab, Horizon = h, met)
        table_met <- rbind(table_met, met)
      }
      # Graphique de prevision (h=24) pour le modele retenu uniquement
      if (lab == choix) {
        png(file.path("results", "figures",
                      paste0("R_prev_", v, ".png")), width = 1600, height = 700, res = 140)
        plot(forecast(mdl, h = 24), main = paste("Prevision", choix, "-", v, "(h=24)"),
             xlab = "Temps", ylab = v)
        dev.off()
      }
    }
  }
}


# ============================================================
# 5. SAUVEGARDE DES TABLEAUX DE RESULTATS
# ============================================================

dir.create("results/tables", recursive = TRUE, showWarnings = FALSE)
write.csv(table_comp, "results/tables/R_arima_model_comparison.csv",
          row.names = FALSE)
write.csv(table_diag, "results/tables/R_arima_diagnostics.csv",
          row.names = FALSE)
write.csv(table_met,  "results/tables/R_arima_metrics.csv",
          row.names = FALSE)

cat("\n\n================================================================\n")
cat("TABLEAU COMPARATIF DES MODELES (AIC/AICc/BIC)\n")
print(table_comp, row.names = FALSE)
cat("================================================================\n")
cat("MESURES DE PERFORMANCE (TEST)\n")
print(table_met, row.names = FALSE)
cat("================================================================\n")
cat("DIAGNOSTIC DES RESIDUS\n")
print(table_diag, row.names = FALSE)
cat("================================================================\n")
cat("SCRIPT 05 TERMINE - SOCLE ARIMA/SARIMA (R)\n")
cat("================================================================\n")

