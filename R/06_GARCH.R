# ============================================================
# 06_GARCH.R
# SECTION 3.3 - Modelisation de la volatilite : ARCH / GARCH (R)
# Serie temporelle energetique - Allemagne (ENTSO-E)
#
# Objectif :
#   Modeliser la variance conditionnelle (volatilite par grappes)
#   des variations journalieres de Load, Wind et Solar.
#
# Pourquoi faut-il un GARCH ici ?
#   Les diagnostics des sections 3.1 et 3.2 (tests ARCH-LM) ont
#   systematiquement rejete l'hypothese "pas d'effet ARCH" :
#   les residus des modeles lineaires presentent une volatilite
#   qui varie dans le temps. Un GARCH capture cette variance
#   conditionnelle, ce que ne font ni SARIMA ni VAR/VECM.
#
# Specifications comparees (moyennes JOURNALIERES, D1 -> stationnaire) :
#   1) GARCH(1,1)   : specification la plus parcimonieuse
#   2) GARCH(2,1)   : relaxation (effets d'ordre superieur)
#   3) EGARCH(1,1)  : asymetrie (chocs negatifs vs positifs)
#
# Innovation etudiee en t de Student (std) : les queues lourdes
# evidentes dans les residus (tests de Jarque-Bera) plaident pour
# une distribution a queues epaisses ; le parametre nu (shape) est
# alors a interpreter : plus nu est petit, plus les queues sont lourdes.
# ============================================================

suppressMessages({
  library(readr)     # lecture
  library(rugarch)   # ugarchspec / ugarchfit
  library(tseries)   # jarque.bera.test
})

set.seed(123)

# ============================================================
# 1. CHARGEMENT + MOYENNES JOURNALIERES + D1
# ============================================================

df <- read_csv("data/processed/germany_energy_analysis.csv",
               show_col_types = FALSE)
df <- df[order(df$DateTime), ]

daily <- aggregate(cbind(Load, Wind, Solar) ~ format(df$DateTime, "%Y-%m-%d"),
                   data = df, FUN = mean)
names(daily)[1] <- "Jour"
daily$Jour <- as.Date(daily$Jour)

dseries <- as.data.frame(diff(as.matrix(daily[c("Load", "Wind", "Solar")])))
names(dseries) <- c("Load", "Wind", "Solar")

cat("================================================================\n")
cat("DONNEES : variations journalieres (D1) ", nrow(dseries), " jours\n")
cat("================================================================\n")

# ============================================================
# 2. OUTILS DE DIAGNOSTIC
# ============================================================

# Ljung-Box sur les residus et sur les residus au carre.
# Residus standardises : p > 0.05 -> pas d'autocorrelation.
# Le degre de liberte fitdf vaut 1 : parametres du modele de moyenne
# (AR(1)) a prendre en compte.
lb_test <- function(x, lag = 12, fitdf = 1) {
  b <- Box.test(x, lag = lag, type = "Ljung-Box", fitdf = fitdf)
  data.frame(stat = round(b$statistic, 2), p = round(b$p.value, 4))
}

# Persistance de la volatilite selon la specification.
# ATTENTION : pour un sGARCH, la persistance est la SOMME de TOUS les
# coefficients ARCH (alpha1..alpha_p) plus TOUS les coefficients GARCH
# (beta1..beta_q). Se limiter a alpha1 + beta1 sous-estime fortement la
# persistance d'un GARCH(2,1) (alpha2 est alors oublie) -> correction.
#   - sGARCH : alpha1 + ... + alpha_p + beta1 + ... + beta_q ;
#   - eGARCH : beta1 (coefficient AR de log(sigma^2)).
persistance_vol <- function(cf, nm) {
  if (nm == "EGARCH(1,1)") {
    return(unname(cf["beta1"]))
  }
  alphas <- cf[grep("^alpha", names(cf))]
  betas  <- cf[grep("^beta",  names(cf))]
  sum(alphas) + sum(betas)
}

# ============================================================
# 3. SPECIFICATIONS ARMA(1,0)-GARCH
# ============================================================
# La structure de moyenne est un AR(1) : la moyenne de Delta X depend
# de la valeur de la veille. Le GARCH concerne la variance.

specs <- list(
  "GARCH(1,1)" = ugarchspec(
    mean.model = list(armaOrder = c(1, 0), include.mean = TRUE),
    variance.model = list(model = "sGARCH", garchOrder = c(1, 1)),
    distribution.model = "std"),
  "GARCH(2,1)" = ugarchspec(
    mean.model = list(armaOrder = c(1, 0), include.mean = TRUE),
    variance.model = list(model = "sGARCH", garchOrder = c(2, 1)),
    distribution.model = "std"),
  "EGARCH(1,1)" = ugarchspec(
    mean.model = list(armaOrder = c(1, 0), include.mean = TRUE),
    variance.model = list(model = "eGARCH", garchOrder = c(1, 1)),
    distribution.model = "std")
)

variables <- c("Load", "Wind", "Solar")
table_coef  <- data.frame()
table_diag  <- data.frame()
table_pers  <- data.frame()

for (v in variables) {
  cat("\n\n####################################################\n")
  cat("SERIE :", v, "\n")
  cat("####################################################\n")

  x <- as.numeric(dseries[[v]])
  # Standardisation : la persistance (alpha+beta) est invariante par
  # changement d'echelle, mais le conditionnement de l'optimisation est
  # bien meilleur en unites de variance -> omega a interpreter sur la
  # serie centree-reduite.
  x <- (x - mean(x)) / sd(x)
  fit_list <- list()

  for (nm in names(specs)) {
    fit <- tryCatch(
      ugarchfit(specs[[nm]], x, solver = "hybrid"),
      error = function(e) NA
    )
    fit_list[[nm]] <- fit
    if (!inherits(fit, "uGARCHfit")) {
      cat("Echec d'estimation pour :", v, nm, "\n")
      next
    }

    cf <- coef(fit)
    ic <- infocriteria(fit)
    a1 <- cf["alpha1"]; b1 <- cf["beta1"]
    a2 <- if ("alpha2" %in% names(cf)) cf["alpha2"] else NA_real_
    # Persistance (voir persistance_vol) : somme de tous les alpha et beta
    # pour un sGARCH, beta1 pour un eGARCH.
    pers <- persistance_vol(cf, nm)
    demi_vie <- if (0 < pers && pers < 1) round(log(0.5)/log(pers), 1) else NA

    table_coef <- rbind(table_coef, data.frame(
      Variable = v, Modele = nm,
      mu = round(cf["mu"], 3),
      ar1 = round(cf["ar1"], 4),
      omega = format(signif(cf["omega"], 4), scientific = TRUE),
      alpha1 = round(a1, 4), alpha2 = round(a2, 4), beta1 = round(b1, 4),
      Persistance = round(pers, 4), Demi_vie = demi_vie,
      Cov_stationnaire = pers < 1,
      nu_t      = round(cf["shape"], 2),
      AIC = round(ic[1, 1], 2), BIC = round(ic[2, 1], 2),
      stringsAsFactors = FALSE))
  }

  # ----------------------------------------------------------
  # 3.1 Diagnostic du GARCH(1,1) (reference)
  # ----------------------------------------------------------
  f <- fit_list[["GARCH(1,1)"]]
  if (inherits(f, "uGARCHfit")) {
  stdr <- as.numeric(residuals(f, standardize = TRUE))
  lb_r   <- lb_test(stdr, lag = 12)
  lb_r2  <- lb_test(stdr^2, lag = 12)
  jb     <- jarque.bera.test(stdr)

  table_diag <- rbind(table_diag, data.frame(
    Variable = v, Modele = "GARCH(1,1)",
    LB_res_12 = lb_r$p, LB_res2_12 = lb_r2$p,
    JB_stat = round(jb$statistic, 2), JB_p = jb$p.value,
    stringsAsFactors = FALSE))

  cat("\n--- Diagnostic GARCH(1,1) :", v, "---\n")
  cat("Ljung-Box residus std (lag 12)     : p =", lb_r$p, "\n")
  cat("Ljung-Box residus std^2 (lag 12)   : p =", lb_r2$p,
      " (moteur de la volatilite)\n")
  cat("Jarque-Bera residus std            :", round(jb$statistic, 1),
      " (normalite rejetee : ATTENDU, les residus suivent une t nu)\n")
  }

  # ----------------------------------------------------------
  # 3.2 Persistance de la volatilite (par modele)
  # ----------------------------------------------------------
  # Persistance calculee par persistance_vol() : somme de tous les
  # coefficients ARCH + GARCH pour un sGARCH (alpha2 inclus), beta1 pour
  # un eGARCH. Un modele est covariation-stationnaire si persistance < 1.
  if (all(sapply(fit_list, inherits, "uGARCHfit"))) {
    for (nm in names(specs)) {
      cf <- coef(fit_list[[nm]])
      pers <- persistance_vol(cf, nm)
      demi_vie <- if (0 < pers && pers < 1) round(log(0.5)/log(pers), 1) else NA
      table_pers <- rbind(table_pers, data.frame(
        Variable = v, Modele = nm,
        Persistance = round(pers, 4), Demi_vie = demi_vie,
        Cov_stationnaire = pers < 1,
        stringsAsFactors = FALSE))
    }
  }

  # ----------------------------------------------------------
  # 3.3 Graphique : volatilite conditionnelle (sigma) + episodes
  # ----------------------------------------------------------
  if (inherits(fit_list[["GARCH(1,1)"]], "uGARCHfit")) {
  # Sigma remis a l'echelle reelle (MW/jour) pour le graphique
  sig <- as.numeric(sigma(fit_list[["GARCH(1,1)"]])) * sd(dseries[[v]])
  dates <- as.Date(daily$Jour[2:nrow(daily)])

  png(file.path("results", "figures", paste0("R_garch_", v, ".png")),
      width = 1800, height = 900, res = 150)
  par(mfrow = c(2, 1))
  plot(dates, dseries[[v]], type = "l", col = "grey50",
       main = paste("Variations journalieres de", v, "(MW/jour)"),
       xlab = "", ylab = paste("Delta", v))
  lines(dates, sig, col = "darkred", lwd = 1.5)
  ord <- order(sig, decreasing = TRUE)[1:3]
  points(dates[ord], sig[ord], col = "darkred", pch = 19)
  text(dates[ord], sig[ord], format(dates[ord], "%d/%m/%Y"),
       pos = 3, cex = 0.8)
  plot(dates, sig, type = "l", col = "darkred",
       main = "Volatilite conditionnelle (sigma, MW/jour) - GARCH(1,1)",
       xlab = "", ylab = "sigma")
  dev.off()
  }
}

# ============================================================
# 4. SAUVEGARDE
# ============================================================

dir.create("results/tables", recursive = TRUE, showWarnings = FALSE)
write.csv(table_coef, "results/tables/R_garch_coefficients.csv",
          row.names = FALSE)
write.csv(table_diag, "results/tables/R_garch_diagnostics.csv",
          row.names = FALSE)
write.csv(table_pers, "results/tables/R_garch_persistence.csv",
          row.names = FALSE)

cat("\n\n================================================================\n")
cat("SECTION 3.3 TERMINEE - ARCH / GARCH (R)\n")
cat("================================================================\n")

print(table_coef, row.names = FALSE)
cat("----------------------------------------------------------------\n")
print(table_diag, row.names = FALSE)