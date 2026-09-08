# Traqueur d'habitudes « 20 heures »

Un petit outil en Python (sans dépendance) pour acquérir une habitude en suivant
la méthode de Josh Kaufman dans *The First 20 Hours* : choisir une compétence,
définir un niveau cible, la déconstruire, éliminer les barrières, puis pratiquer
par courtes sessions chronométrées jusqu'à 20 heures cumulées.

L'habitude préconfigurée est le **mode Shabbat** : ne rien faire, sans portable,
juste marcher ou regarder et laisser ses pensées divaguer. L'objectif est de
compter combien de fois on le fait *réellement*, pas seulement combien de fois
on a essayé.

## Démarrer

```bash
python habits.py deconstruct shabbat   # relire la cible, les sous-compétences, la checklist
python habits.py start shabbat         # checklist, minuteur de 20 min, bilan honnête
python habits.py status                # progression vers les 20 heures
```

Session faite sans le script (montre, minuteur de cuisine) ? Enregistre-la après coup :

```bash
python habits.py log shabbat 25 -q 4 --phone-free -n "banc du parc"
python habits.py log shabbat 40 -q 2 --phone-used -d 2026-09-06
```

Autres commandes :

```bash
python habits.py list                  # toutes les habitudes en une ligne chacune
python habits.py history shabbat       # dernières sessions
python habits.py plan shabbat -w 4     # combien pratiquer par jour pour finir en 4 semaines
python habits.py add lecture           # créer une nouvelle habitude (questions guidées)
```

## Ce qui compte comme « vraiment rien »

À la fin de chaque session, on répond à deux questions :

1. **Qualité de 1 à 5** : 1 = j'ai craqué, 5 = vraiment rien, marcher, regarder, laisser divaguer.
2. **Le portable est-il resté hors de portée tout le long ?**

Une session est comptée comme « vraiment rien » seulement si le portable est
resté hors de portée **et** que la qualité est d'au moins 4. Toutes les sessions
comptent dans les 20 heures (la pratique ratée est de la pratique), mais le
compteur « vraiment rien » est le vrai indicateur de progrès.

Exemple de `status` :

```
Mode Shabbat : ne rien faire  (shabbat)
[##......................................] 1h15 / 20h  (6 %)
Sessions : 3   dont « vraiment rien » : 2 (67 %)
Série : 2 jour(s)   Cette semaine : 2 session(s), 55 min   L○ M● M· J· V· S· D·
Rythme sur 14 jours : 5 min/jour → objectif atteint vers le 6 avr. 2027
Qualité moyenne : 3.7/5   Plus longue session : 30 min
```

Dans la grille de la semaine : `·` rien, `○` une session, `●` au moins une
session « vraiment rien ».

## Les principes de Kaufman et où ils vivent dans l'outil

| Principe (*The First 20 Hours*) | Dans le projet |
| --- | --- |
| 1. Choisir un projet qu'on aime | Champ `why` de chaque habitude, affiché par `deconstruct` |
| 2. Une compétence à la fois | `list` montre chaque habitude, mais on ne pratique qu'une seule `start` à la fois |
| 3. Définir un niveau cible | `target_performance` : « tenir 45 min sans portable… », affiché avant chaque session |
| 4. Déconstruire en sous-compétences | Liste `subskills` (poser le portable, marcher sans but, laisser passer l'envie…) |
| 5. Obtenir les outils critiques | Liste `tools` (minuteur qui n'est pas le téléphone, un banc, un créneau fixe) |
| 6. Éliminer les barrières | La `checklist` s'affiche à chaque `start` et bloque si tout n'est pas en place |
| 7. Réserver du temps de pratique | `plan` calcule les minutes par jour nécessaires pour finir à la date voulue |
| 8. Boucle de feedback rapide | Bilan immédiat après chaque session : qualité, portable, total, série |
| 9. Pratiquer par courtes rafales chronométrées | `start` lance un minuteur de 20 min (`burst_minutes`, modifiable avec `-m`) |
| 10. Quantité et vitesse plutôt que perfection | Toutes les sessions comptent dans les 20 h, même les ratées ; on vise la fréquence |

Le seuil des **20 heures** correspond au constat du livre : le plus dur est
d'être mauvais au début, et 20 heures de pratique délibérée suffisent pour passer
de « nul » à « raisonnablement bon ». Le `status` projette la date à laquelle on
y arrive au rythme des 14 derniers jours.

## Fichiers

- `habits.py` : le script, Python 3.10+ et bibliothèque standard uniquement.
- `habits.json` : la définition des habitudes (cible, sous-compétences, outils, checklist).
- `data/sessions.json` : toutes les sessions enregistrées. Ce fichier est versionné
  volontairement : le commiter régulièrement garde un historique du parcours.
- `tests/test_habits.py` : tests unitaires (`python -m unittest discover -s tests`).

La variable d'environnement `HABITS_DIR` permet de pointer vers un autre dossier
de données, utile pour tester sans toucher au vrai journal.

## Ajouter une autre habitude

`python habits.py add <id>` pose les questions dans l'ordre du livre : pourquoi,
niveau cible, sous-compétences, outils, checklist. On peut aussi éditer
`habits.json` directement.
