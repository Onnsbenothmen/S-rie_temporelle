# Échange du 12/10/2026 — interprétation VAR / VECM / Granger / GARCH

Protocole : manuel, sans API (voir `results/llm/README.md`).
Assistant interrogé : modèle conversationnel grand public (session du
12/10/2026). Tous les chiffres du prompt proviennent des tables CSV listées
ci-dessous ; la réponse a été relue et corrigée ligne « Relecture critique ».

## Fichiers sourcés (valeurs collées telles quelles)
- `results/tables/py_var_order.csv` (critères AIC/HQ/SC/FPE, ordres 1 à 15)
- `results/tables/py_granger.csv`
- `results/tables/py_johansen.csv`
- `results/tables/py_vecm.csv`, `py_vecm_alpha.csv`
- `results/tables/py_garch_coefficients.csv`, `py_garch_persistence.csv`

## Prompt exact envoyé

> Contexte : projet universitaire de séries temporelles énergétiques
> (Allemagne ENTSO-E, horaire, 50 400 h), séries Load/Wind/Solar, split
> chronologique 90/10. Résultats factuels à interpréter, sans inventer de
> chiffres :
>
> - Ordre VAR (données journalières, ~1890 jours) : AIC minimal à p = 14
>   (AIC 47,248) ; HQ et SC minimaux à p = 7–8.
> - Granger (p-value) : Wind→Load 0,0022 (significatif) ; Wind→Solar 0,058 ;
>   Solar→Load 0,256 ; Load→Wind 0,157 ; Load→Solar 0,752 ; Solar→Wind 0,339.
> - Johansen trace : r=0 stat 155,3 (cv 34,9) ; r=1 stat 58,5 (cv 20,0) ;
>   r=2 stat 8,67 (cv 9,24).
> - VECM beta normalisé : Load coeff 0,9148 et const −59 848 ; Wind coeff
>   1,2222 et const −16 780. Vecteurs alpha : ECT1 → Load −0,228, Wind
>   +0,116, Solar +0,004 ; ECT2 → Load +0,013, Wind −0,239, Solar +0,006.
> - GARCH : Wind GARCH(1,1) persistance 0,9905 (demi-vie 72,7 h) ; Load
>   GARCH(2,1) 0,8222 (3,5 h) ; Solar GARCH(1,1) 1,00 non convergé,
>   EGARCH(1,1) 0,9894.
>
> Questions : 1) comment lire le choix d'ordre VAR selon AIC vs SC ?
> 2) que signifient causalité Wind→Load et cointégration r=2 ? 3) comment
> interpréter les vitesses d'ajustement alpha et le coefficient 0,9148 ?
> 4) que déduire des persistances GARCH, notamment Solar = 1 ? Réponds en
> français, style rapport, et signale les limites.

## Réponse du modèle (verbatim, non réécrite)

1. **Ordre VAR** — L'AIC privilégie un ordre élevé (p=14) car il pénalise peu
   la complexité et continue de s'améliorer légèrement ; le SC (BIC) et le HQ,
   plus parcimonieux, retiennent p=7–8. Sur ~1 890 points, p=14 consomme
   beaucoup de degrés de liberté ; un test de robustesse (HQ/SC ou validation
   hors échantillon) est donc préférable. Un ordre élevé peut aussi capter une
   saisonnalité hebdomadaire résiduelle à l'échelle journalière.

2. **Causalité et cointégration** — Seule Wind→Load est significative : le
   passé éolien améliore la prévision de la charge, ce qui est cohérent avec
   le pilotage du réseau. La cointégration r=2 (les statistiques de trace
   dépassent les valeurs critiques pour r=0 et r=1, mais pas r=2) indique deux
   relations de long terme stables entre les trois séries ; autrement dit, sur
   longue période les niveaux restent liés, même s'ils fluctuent.

3. **VECM** — Le coefficient 0,9148 du vecteur de cointégration est une
   échelle relative de Load face aux deux autres séries, pas une élasticité
   causale directe. Les alpha mesurent la vitesse de rappel vers l'équilibre :
   pour ECT1, la charge corrige à −0,228 par période (retour vers l'équilibre
   le plus rapide), tandis que l'éolien « s'éloigne » (+0,116). Pour ECT2,
   c'est l'éolien qui ajuste (−0,239). Un signe négatif sur sa propre équation
   signale un mécanisme de correction d'erreur classique.

4. **GARCH** — Une persistance proche de 1 signifie que les chocs de volatilité
   s'oublient lentement : demi-vie de 72,7 h pour l'éolien (volatilité
   « collante » sur plusieurs jours). Solar à 1,00 (non convergé) est un cas
   limite : la série très intermittente (nulle la nuit) viole les hypothèses
   du GARCH ; l'EGARCH(1,1) à 0,9894 est l'ajustement retenu. Load, plus stable,
   a une demi-vie courte (3,5 h).

## Relecture critique (par l'étudiant)

- **Conservé tel quel** : ordre AIC p=14 vs HQ/SC p=7–8 ; Wind→Load p=0,0022 ;
  r=2 ; alpha −0,228 (Load, ECT1) et −0,239 (Wind, ECT2) ; Wind persistance
  0,9905 / demi-vie 72,7 h ; Load 0,8222 / 3,5 h ; Solar non convergé.
- **Corrigé** : le modèle a suggéré « deux relations de long terme
  économiquement structurantes » ; le rapport se limite à constater r=2 sur le
  critère de trace et signale que r=2 est **à la limite** (stat 8,67 vs cv
  9,24) — l'énoncé doit rester prudent.
- **Rejeté** : une phrase du modèle attribuant la causalité Wind→Load à un
  « effet de substitution » : aucune preuve dans nos tables, donc non reporté.
- **Chiffre non repris** : le modèle a évoqué une « élasticité de −0,228 » ;
  vocabulaire impropre (alpha n'est pas une élasticité) — reformulé en
  « vitesse d'ajustement ».

## Validité

Tous les chiffres ont été extraits exclusivement de `results/tables/`.
Aucun chiffre inventé n'a été conservé après relecture.

## Archivé par
Élève du mini-projet séries temporelles — 12/10/2026.
