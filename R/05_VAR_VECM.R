# ============================================================
# 05_VAR_VECM.R
# SECTION 3.2 - Liaisons dynamiques : VAR, Granger, VECM (R)
# Serie temporelle energetique - Allemagne (ENTSO-E)
#
# Objectifs :
#   1. VAR libre-order choisi par critere d'information (AIC/BIC)
#   2. Causalite de Granger (test F/Wald -- H0 : X ne cause pas Y)
#   3. Cointegration de Johansen (niveaux) et VECM le cas echeant
#   4. Fonctions de reponse impulsionnelle + decomposition de variance
#
# POURQUOI des moyennes journalieres ?
#   L'intra-journalier (cycle 24h / 168h) est deja traite par les
#   modeles SARIMA de la section 3.1. Les liaisons structurelles
#   entre vent, soleil et demande s'expriment a l'echelle journaliere
#   ou hebdomadaire ; a l'echelle horaire, la forte saisonnalite
#   polluerait les tests de cointegration et de causalite.
# ============================================================

suppressMessages({
  library(readr)    # lecture
  library(vars)     # VAR, causality, irf, fevd
  library(urca)     # ca.jo (Johansen), cajorls, vec2var
  library(tseries)  # adf.test
})

set.seed(123)

# ============================================================
# 1. CHARGEMENT + AGRREGATION JOURNALIERE (moyennes)
# ============================================================
# Pourquoi des moyennes plutot que des prelevements ?
#   Les moyennes suppriment la saisonnalite intra-journaliere ET le
#   bruit de mesure ; ce sont les niveaux moyens d'equilibre du systeme
#   electrique qui interessent le VAR/VECM.

df <- read_csv("data/processed/germany_energy_analysis.csv",
               show_col_types = FALSE)
df <- df[order(df$DateTime), ]

daily <- aggregate(cbind(Load, Wind, Solar) ~ format(df$DateTime, "%Y-%m-%d"),
                   data = df, FUN = mean)
names(daily)[1] <- "Jour"
daily$Jour <- as.Date(daily$Jour)   # tri chronologique

nd  <- nrow(daily)
ntr <- floor(0.90 * nd)

cat("================================================================\n")
cat("DONNEES JOURNALIERES :", nd, "jours (",
    format(daily$Jour[1], "%Y-%m-%d"), "->",
    format(daily$Jour[nd], "%Y-%m-%d"), ")\n")
cat("Train :", ntr, "jours | Test :", nd - ntr, "jours\n")
cat("================================================================\n")

# Series en niveaux et en differences
lev <- daily[c("Load", "Wind", "Solar")]
tr  <- lev[1:ntr, ]                       # train (niveaux)
dtr <- as.data.frame(diff(as.matrix(tr))) # train (1ere difference, D1)
names(dtr) <- names(tr)

# ============================================================
# 2. STATIONNARITE DES NIVEAUX (rappels, vitr pour justifier D1)
# ============================================================

cat("\n--- ADF sur les NIVEAUX journaliers (H0 racine unitaire) ---\n")
for (v in names(tr)) {
  a <- adf.test(tr[[v]])
  cat(sprintf("%-6s stat=%.2f p=%.4f\n", v, a$statistic, a$p.value))
}

cat("\n--- ADF sur les DIFFERENCES (D1) ---\n")
for (v in names(dtr)) {
  a <- adf.test(dtr[[v]])
  cat(sprintf("%-6s stat=%.2f p=%.4f -> stationnaire : %s\n",
              v, a$statistic, a$p.value, a$p.value < 0.05))
}

# ============================================================
# 3. SELECTION DE L'ORDRE DU VAR (libre, par critere)
# ============================================================
# VARselect minimise AIC / BIC (et HQ / SC) sur un modele sature en
# retards (lag.max), en differences : le systeme est alors stationnaire
# et la causalite de Granger est valide.

vm <- VARselect(dtr, lag.max = 15, type = "const")
p_sel <- as.integer(vm$selection["AIC(n)"])
cat("\nVARselect (differences) :\n")
print(vm$criteria[c("AIC(n)", "HQ(n)", "SC(n)", "FPE(n)"), ])
cat("\nOrdre retenu (AIC) : p =", p_sel, "\n")

# ============================================================
# 4. VAR(p) SUR LES DIFFERENCES + CAUSALITE DE GRANGER
# ============================================================

var_fit <- VAR(dtr, p = p_sel, type = "const")

cat("\n--- Stabilite du VAR (racines) ---\n")
cat("Modulus max :", round(max(vars::roots(var_fit)), 4),
    " (doit etre < 1)\n")

# Test de Granger PAIRWISE sur 6 paires ordonnees (bivarie, ordre p)
cat("\n--- Causalite de Granger (H0 : X ne cause pas Y au sens de")
cat(" Granger) ---\n")
gr <- NULL
paires <- expand.grid(cause = names(dtr), dep = names(dtr),
                      stringsAsFactors = FALSE)
paires <- paires[paires$cause != paires$dep, ]
for (i in seq_len(nrow(paires))) {
  cx <- paires$cause[i]; dy <- paires$dep[i]
  fit <- VAR(dtr[c(cx, dy)], p = p_sel, type = "const")
  gc  <- causality(fit, cause = cx)$Granger
  gr <- rbind(gr, data.frame(
    Hypothese = sprintf("%s -> %s", cx, dy),
    stat = gc$statistic, p = gc$p.value,
    Conclusion = ifelse(gc$p.value < 0.05, "OUI (rejet H0)", "non"),
    stringsAsFactors = FALSE))
}
print(gr, row.names = FALSE)

# ============================================================
# 5. DIAGNOSTIC DES RESIDUS DU VAR
# ============================================================

cat("\n--- Diagnostic des residus du VAR(p) ---\n")
st <- serial.test(var_fit, lags.pt = 16, type = "PT.asymptotic")
cat("Portmanteau (autocorrelation)  : p =",
    round(st$serial$p.value, 4), "\n")
nt <- normality.test(var_fit, multivariate.only = TRUE)
cat("Normalite multivariee, JB       : p =",
    round(nt$jb.mul$JB$p.value, 4), "\n")
at <- arch.test(var_fit, lags.multi = 5, multivariate.only = TRUE)
cat("ARCH multivarie (volatilite)    : p =",
    format(at$arch.mul$p.value, digits = 3), "\n")

# ============================================================
# 6. COINTEGRATION DE JOHANSEN (NIVEAUX) -> VECM ?
# ============================================================
# ca.jo teste la cointegration lineaire entre les NIVEAUX. Si le rang
# r >= 1, il existe des relations d'equilibre de long terme entre
# Load, Wind et Solar -> on estime un VECM. K = p + 1 retards en niveau
# pour rester coherent avec le VAR(p) en differences.

tr_ts <- ts(tr, frequency = 7)
jo <- ca.jo(tr_ts, type = "trace", ecdet = "const", K = p_sel + 1,
            spec = "transitory")

r_hat <- sum(jo@teststat > jo@cval[, 2])   # nb de relations significatives
cat("\n--- Johansen (trace) ---\n")
print(round(cbind(jo@teststat, jo@cval), 2))

vecm <- NULL
vecm_alpha <- NULL
if (r_hat >= 1) {
  cat("\n>>> Cointegration detectee : r =", r_hat, "-> estimation d'un VECM\n")
  co <- cajorls(jo, r = r_hat)

  # cajorls renvoie :
  #   co$beta : les VECTEURS DE COINTEGRATION (beta), normalises (K x r) ;
  #   co$rlm$coefficients[1:r, ] : les VITESSES D'AJUSTEMENT (alpha).
  # (L'ancienne version exportait jo@V, les vecteurs propres bruts non
  #  normalises, sous des noms de colonnes trompeurs : corrige.)
  beta_vec  <- co$beta
  alpha_vec <- co$rlm$coefficients[seq_len(r_hat), , drop = FALSE]

  cat("\n--- Relations de cointegration normalisees (beta) ---\n")
  print(round(beta_vec, 4))
  cat("\n--- Vitesses d'ajustement vers l'equilibre (alpha) ---\n")
  print(round(alpha_vec, 4))

  vecm <- data.frame(Variable = rownames(beta_vec),
                     round(as.data.frame(beta_vec), 4),
                     check.names = FALSE)
  names(vecm)[-1] <- paste0("ECT_", seq_len(r_hat))

  vecm_alpha <- data.frame(Equation = rownames(alpha_vec),
                           round(as.data.frame(alpha_vec), 4),
                           check.names = FALSE)
} else {
  cat("\n>>> Pas de cointegration (r = 0) -> on garde le VAR en\n")
  cat("    differences (specification standard I(0)).\n")
}

# ============================================================
# 7. IMPULSION-REPONSE (IRF) ET DECOMPOSITION DE LA VARIANCE
# ============================================================
# Modele pour les dynamiques : VECM si coint?gre (retrouve sous forme
# VAR via vec2var), sinon le VAR(p) en differences.

if (r_hat >= 1) {
  vmod <- vec2var(jo, r = r_hat)
  cat("\nModele utilise pour IRF/FEVD : VECM(", r_hat, ")\n", sep="")
} else {
  vmod <- var_fit
  cat("\nModele utilise pour IRF/FEVD : VAR(", p_sel, ") en differences\n", sep="")
}

# Reponse de la demande (Load) a un choc de Wind / Solar
irf_ld <- irf(vmod, impulse = c("Wind", "Solar"), response = "Load",
              n.ahead = 28, boot = TRUE, n.boot = 200, ci = 0.95)
png(file.path("results", "figures", "R_var_irf_load.png"),
    width = 1600, height = 700, res = 140)
plot(irf_ld, main = "Reponse de Load a un choc de Wind / Solar (VECM)")
dev.off()

# Decomposition de la variance de Load (28 jours)
fv <- fevd(vmod, n.ahead = 28)
png(file.path("results", "figures", "R_var_fevd_load.png"),
    width = 1600, height = 700, res = 140)
plot(fv, main = "Decomposition de la variance de Load")
dev.off()

fev_df <- do.call(rbind, lapply(names(fv), function(nm) {
  m <- as.data.frame(fv[[nm]])
  m$Horizon <- seq_len(nrow(m))
  m$Variable <- nm
  m[, c("Variable", "Horizon", setdiff(names(m), c("Variable", "Horizon")))]
}))

# ============================================================
# 8. SAUVEGARDE
# ============================================================

dir.create("results/tables", recursive = TRUE, showWarnings = FALSE)

write.csv(vm$criteria, "results/tables/R_var_order.csv")
write.csv(gr, "results/tables/R_granger.csv", row.names = FALSE)
write.csv(data.frame(Test = c("Portmanteau", "Normalite", "ARCH"),
                     p = c(st$serial$p.value, nt$jb.mul$JB$p.value,
                           at$arch.mul$p.value)),
          "results/tables/R_var_diagnostics.csv", row.names = FALSE)
write.csv(data.frame(Test = "Trace", Rank = r_hat,
                     stat = jo@teststat, cv_95 = jo@cval[, 2]),
          "results/tables/R_johansen.csv", row.names = FALSE)
if (!is.null(vecm)) {
  write.csv(vecm, "results/tables/R_vecm.csv", row.names = FALSE)
  write.csv(vecm_alpha, "results/tables/R_vecm_alpha.csv", row.names = FALSE)
}
write.csv(fev_df, "results/tables/R_var_fevd.csv", row.names = FALSE)

cat("\n\n================================================================\n")
cat("SECTION 3.2 TERMINEE - VAR / GRANGER / VECM (R)\n")
cat("================================================================\n")