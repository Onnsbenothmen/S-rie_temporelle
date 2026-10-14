# Échange du 12/10/2026 — hiérarchie des modèles, DM et recommandations

Protocole : manuel, sans API. Assistant : modèle conversationnel grand public
(session du 12/10/2026). Chiffres issus des tables CSV listées ci-dessous.

## Fichiers sourcés (valeurs collées telles quelles)
- `results/tables/py_evaluation_ranking.csv` (classement RMSE)
- `results/tables/py_arima_metrics.csv`, `py_lstm_gru_metrics.csv`
- `results/tables/py_walkforward_metrics.csv`, `py_diebold_mariano.csv`

## Prompt exact envoyé

> Contexte : Allemagne ENTSO-E, horaire, split 90/10 (test du 05/03/2020 au
> 30/09/2020, 5 040 h, début de la pandémie). Horizons h = 10, 24, 5 040.
> Résultats factuels (aucun chiffre à inventer) :
>
> - Load : à h=10, LSTM RMSE 881 vs SARIMA_manuel 898 ; à h=24, SARIMA_manuel
>   1 069 vs LSTM 1 872 ; à h=5 040, LSTM 11 838 vs SARIMA_manuel 65 852.
> - Wind : h=10 ARIMA_auto 516 ; h=24 ARIMA_auto 11 828 vs SARIMA_manuel
>   12 662 ; h=5 040 ARIMA_auto 9 574 vs LSTM 35 205.
> - Solar : h=10 SARIMA_auto 552 (MAPE 558 %) ; h=24 SARIMA_manuel 772 ;
>   h=5 040 LSTM 13 594.
> - Walk-forward 1 pas (5 040 h) RMSE : Load LSTM/GRU 790 vs naïf 2 328 ;
>   Wind 705 vs 1 090 ; Solar 1 295 vs 2 849. DM : LSTM significativement
>   meilleur que naïf et saisonnier-naïf (p < 1e-60) sur les 3 séries.
>
> Questions : hiérarchiser les modèles par horizon et par série ; commenter la
> contradiction entre la supériorité LSTM en walk-forward 1 pas et la
> supériorité SARIMA à h=24 ; formuler 6 recommandations hiérarchisées. Style
> rapport, signale les faiblesses, français.

## Réponse du modèle (verbatim, non réécrite)

**Hiérarchie par horizon.** À court terme (h=10), les modèles sont proches :
le SARIMA saisonnier et le LSTM se tiennent en quelques dizaines de MW sur
Load, le LSTM étant marginalement devant. À moyen terme (h=24, un cycle
jour), le SARIMA saisonnier (m=24) reprend l'avantage sur Load : il exploite
explicitement la saisonnalité quotidienne, que le LSTM récursif sur fenêtre de
168 h amortit. À très long terme (h=5 040), le LSTM domine nettement sur Load
(11,8 k vs 65,9 k), tandis que sur Wind c'est ARIMA_auto (9,6 k) qui résiste le
mieux et que le LSTM se dégrade (35,2 k). Solar est instable : toutes les
métriques en pourcentage sont inutilisables (MAPE 558 % à h=10) à cause des
valeurs quasi nulles la nuit.

**Walk-forward vs trajectoire.** La supériorité du LSTM/GRU en walk-forward
1 pas (RMSE 790/705/1 295) face au naïf, confirmée par Diebold–Mariano, mesure
la qualité à **un pas glissant** : chaque prévision dispose des observations
les plus récentes. La supériorité SARIMA à h=24 sur Load mesure une
**trajectoire fixe de 24 h** émise depuis une seule origine : les deux
protocoles ne sont pas comparables directement. Il est normal que le LSTM, très
fort en mise à jour pas-à-pas, soit relativisé dès qu'on fixe l'origine et
qu'on compose 24 pas récursifs.

**Recommandations hiérarchisées.**
1. Privilégier le SARIMA saisonnier pour l'horizon journalier (h≈24) sur Load.
2. Utiliser le LSTM/GRU en prévision opérationnelle 1 pas (mise à jour horaire).
3. Conserver ARIMA_auto comme référence robuste sur Wind (pas d'avantage clair
   de la saisonnalité journalière).
4. Proscrire le MAPE/P avec les zéros de Solar ; utiliser RMSE/MAE et un
   indicateur tronqué (par ex. sMAPE sur valeurs > seuil).
5. Envisager des régresseurs de Fourier (m=168) ou un LSTM multivarié
   (Load+Wind+Solar) pour capter la saisonnalité hebdomadaire à h moyen.
6. Isoler la période COVID dans l'analyse des erreurs longues (h=5 040).

## Relecture critique (par l'étudiant)

- **Conservé** : les RMSE cités sont identiques aux tables ; l'opposition
  « walk-forward 1 pas » vs « trajectoire fixe depuis une origine » est
  méthodologiquement exacte et a été reprise dans le chapitre d'évaluation.
- **Corrigé** : le modèle a écrit « le LSTM bat tous les modèles » en
  généralisant à partir du seul walk-forward ; reformulé en « bat les
  baselines naïves », car le SARIMA n'était pas encore dans le walk-forward de
  façon fiable et ARIMA_auto reste meilleur sur Wind à h=5 040.
- **Rejeté** : une recommandation du modèle proposant d'« augmenter les
  epochs pour rattraper SARIMA à h=24 » — non fondée, l'écart vient du
  protocole récursif, pas du budget d'entraînement.
- **Ajouté par l'étudiant** : la mention du biais COVID (test débutant le
  05/03/2020), absente de la réponse du modèle.

## Validité

Chiffres uniquement issus de `results/tables/`. Les affirmations non
vérifiables ont été retirées après relecture.

## Archivé par
Élève du mini-projet séries temporelles — 12/10/2026.
