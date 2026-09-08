# 20 heures : traqueur d'habitudes

Un outil pour acquérir des habitudes en suivant la méthode de Josh Kaufman dans
*The First 20 Hours* : choisir une compétence, définir un niveau cible, la
déconstruire, éliminer les barrières, puis pratiquer par courtes sessions
chronométrées jusqu'à 20 heures cumulées (ou N jours tenus pour les habitudes
d'abstinence).

Le point de départ, c'est le constat qu'on est en multitâche permanent et qu'on
ne prend plus jamais le temps de juste penser, comme Einstein, Darwin ou
Poincaré le faisaient. L'habitude principale est donc le **mode Shabbat** : ne
rien faire, sans portable, juste marcher ou regarder et laisser ses pensées
divaguer. L'objectif est de compter combien de fois on le fait *réellement*.

Deux façons de l'utiliser, avec le même format de données :

- **La page web** (`index.html`), à ouvrir depuis GitHub Pages sur n'importe quel appareil.
- **Le script Python** (`habits.py`), sans dépendance, dans un terminal.

## Utiliser depuis GitHub (page web)

1. Sur GitHub : *Settings → Pages → Build and deployment → Source : Deploy from a branch*, branche `main`, dossier `/ (root)`, puis *Save*.
2. Après une minute, la page est en ligne sur `https://ahaddad75.github.io/Beautiful-Soup-Tutorial/`.
3. Ajoute-la à l'écran d'accueil du téléphone : elle fonctionne comme une petite appli.

Les sessions sont enregistrées dans le navigateur (localStorage). Le bouton
**Exporter** produit un `sessions.json` à commiter dans `data/` pour garder
l'historique dans le dépôt, et **Importer** le recharge sur un autre appareil.

En local sans GitHub Pages : `python -m http.server` dans le dossier, puis
`http://localhost:8000`.

## Utiliser dans un terminal (script Python)

```bash
python habits.py list                   # toutes les habitudes et leur progression
python habits.py deconstruct shabbat    # pourquoi, cible, sous-compétences, checklist
python habits.py start shabbat          # checklist, minuteur de 20 min, bilan honnête
python habits.py log shabbat 25 --ok -q 4 -n "banc du parc"   # session faite sans le script
python habits.py log nofap --ok         # cocher la journée d'une habitude en jours
python habits.py log nofap --ko -d 2026-09-06                 # noter un écart un autre jour
python habits.py status                 # progression détaillée
python habits.py history                # dernières sessions
python habits.py plan shabbat -w 4      # combien pratiquer par jour pour finir en 4 semaines
python habits.py science shabbat        # ce que disent les études (sans argument : sur la méthode)
python habits.py add lecture-anglais    # créer une nouvelle habitude (questions guidées)
```

## Les habitudes incluses

| Identifiant | Habitude | Mesure | Contrainte vérifiée après chaque session |
| --- | --- | --- | --- |
| `shabbat` | Mode Shabbat : ne rien faire | 20 h par sessions de 20 min | Portable resté hors de portée |
| `monotache` | Mono-tâche : une seule chose à la fois | 20 h par sessions de 25 min | Aucune autre tâche, onglet ou notification |
| `meditation` | Méditation | 20 h par sessions de 10 min | Resté assis jusqu'à la fin sans regarder l'heure |
| `nofap` | No fap : reprendre le contrôle | 90 jours tenus | Journée tenue, sans consommation |
| `lecture` | Lecture profonde | 20 h par sessions de 25 min | Lecture sans interruption ni portable |
| `journal` | Journal : écrire ce qui se passe | 20 h par sessions de 10 min | Écrit sans s'arrêter ni relire |

Chaque habitude est définie dans `habits.json` avec son pourquoi, son niveau
cible, ses sous-compétences, ses outils, sa checklist et ses références
scientifiques. On peut en ajouter ou en modifier directement dans le fichier.

## Ce qui compte comme « vraiment réussi »

À la fin de chaque session, deux questions :

1. **Qualité de 1 à 5**, avec des libellés propres à chaque habitude (pour le mode Shabbat : 1 = j'ai craqué, 5 = vraiment rien, marcher, regarder, laisser divaguer).
2. **La contrainte a-t-elle été respectée ?** (portable hors de portée, aucune autre tâche, journée tenue, etc.)

Une session est « vraiment réussie » seulement si la contrainte est respectée
**et** que la qualité est d'au moins 4. Toutes les sessions comptent dans les
20 heures (la pratique ratée est de la pratique), mais le compteur « vraiment
réussies » est le vrai indicateur. Pour une habitude en jours, seul le respect
de la contrainte compte, et la série mesure les jours tenus d'affilée.

Exemple de `status` :

```
Mode Shabbat : ne rien faire  (shabbat)
[##......................................] 1h15 / 20h  (6 %)
Sessions : 3   dont « vraiment réussies » : 2 (67 %)
Série : 2 jour(s)   Cette semaine : 2 session(s), 55 min   L○ M● M· J· V· S· D·
Rythme sur 14 jours : 5 min/jour → objectif atteint vers le 6 avr. 2027
Qualité moyenne : 3.7/5   Plus longue session : 30 min
```

Dans la grille de la semaine : `·` rien, `○` une session, `●` au moins une
session vraiment réussie (ou une journée tenue).

## Ce que disent les études

Chaque habitude embarque ses références, lisibles avec `python habits.py science <id>`
ou dans la section « Ce que disent les études » de la page web. Quelques points
clés :

**Ne rien faire**

- Au repos, le cerveau active le « réseau du mode par défaut », impliqué dans la mémoire, la projection dans le futur et la compréhension des autres (Raichle et al., 2001, *PNAS* ; Immordino-Yang et al., 2012, *Perspectives on Psychological Science*).
- Laisser ses pensées divaguer pendant une pause améliore la résolution créative de problèmes laissés en suspens (Baird et al., 2012, *Psychological Science*).
- Quelques minutes de repos éveillé sans stimulation renforcent la mémoire de ce qu'on vient d'apprendre, encore une semaine plus tard (Dewar et al., 2012, *Psychological Science*).
- Rester seul avec ses pensées est difficile pour la plupart des gens : certains préfèrent s'administrer un choc électrique (Wilson et al., 2014, *Science*). C'est donc une compétence, ce qui justifie de l'entraîner comme telle.
- La simple présence du smartphone, même éteint, réduit la capacité cognitive disponible ; l'effet disparaît s'il est dans une autre pièce (Ward et al., 2017, *Journal of the Association for Consumer Research*).
- Marcher en nature réduit la rumination (Bratman et al., 2015, *PNAS*) et restaure l'attention dirigée (Berman, Jonides & Kaplan, 2008, *Psychological Science*). S'ennuyer augmente ensuite la créativité (Mann & Cadman, 2014, *Creativity Research Journal*).

**Mono-tâche**

- Les gros consommateurs de multitâche médiatique filtrent moins bien les distractions et changent moins bien de tâche (Ophir, Nass & Wagner, 2009, *PNAS* ; revue : Uncapher & Wagner, 2018, *PNAS*).
- Chaque bascule entre tâches a un coût en temps (Rubinstein, Meyer & Evans, 2001, *JEP: Human Perception and Performance*).
- Le travail interrompu se finit, mais avec plus de stress et de pression (Mark, Gudith & Klocke, 2008, *CHI*). Une simple notification non consultée dégrade l'attention autant que l'usage du téléphone (Stothart et al., 2015, *JEP: HPP*).

**Méditation**

- Méta-analyse de 47 essais : bénéfices modérés sur l'anxiété, la dépression et la douleur (Goyal et al., 2014, *JAMA Internal Medicine*).
- Huit semaines de pratique augmentent la densité de matière grise dans l'hippocampe (Hölzel et al., 2011) ; quatre jours de 20 min améliorent déjà l'attention (Zeidan et al., 2010).

**No fap** (état honnête des preuves)

- L'abstinence en soi n'a pas d'effet démontré sur la testostérone à long terme ni sur les performances. L'étude hormonale souvent citée (Jiang et al., 2003) porte sur 28 hommes et n'a jamais été répliquée.
- Le bénéfice documenté concerne la sortie d'un usage compulsif : la consommation intensive de pornographie est corrélée à un plus petit striatum (Kühn & Gallinat, 2014, *JAMA Psychiatry*), et l'OMS reconnaît le trouble du comportement sexuel compulsif depuis 2019 (CIM-11, 6C72). Une grande part du sentiment d'être « accro » relève du conflit avec ses propres valeurs (Grubbs et al., 2019).
- Le lien entre pornographie et troubles de l'érection n'est pas établi (Prause & Pfaus, 2015).

**La méthode elle-même**

- La pratique délibérée, avec retour immédiat, fait progresser plus que le temps passé (Ericsson et al., 1993, *Psychological Review*).
- Des sessions courtes espacées battent la même durée concentrée (Cepeda et al., 2006, *Psychological Bulletin*).
- Une habitude devient automatique en 66 jours en médiane, entre 18 et 254 selon les cas, et sauter un jour n'annule pas le processus (Lally et al., 2010, *European Journal of Social Psychology*).

## Penser comme avant

Darwin faisait chaque jour ses tours de « Sandwalk » pour réfléchir en marchant.
Einstein a construit la relativité sur des expériences de pensée, sans
matériel. Poincaré raconte que la solution lui est venue en montant dans un
omnibus, après avoir cessé d'y travailler. Kant marchait à heure si fixe que
les voisins réglaient leur montre dessus. Nietzsche écrivait que seules les
pensées qu'on a en marchant ont de la valeur. Les IRM disent aujourd'hui la
même chose : le cerveau au repos travaille, et la marche sans écran restaure
l'attention.

## Les principes de Kaufman et où ils vivent dans l'outil

| Principe (*The First 20 Hours*) | Dans le projet |
| --- | --- |
| 1. Choisir un projet qu'on aime | Champ `why` de chaque habitude, affiché en tête |
| 2. Une compétence à la fois | Un onglet actif à la fois, un seul minuteur |
| 3. Définir un niveau cible | `target_performance`, affiché avant chaque session |
| 4. Déconstruire en sous-compétences | Liste `subskills` |
| 5. Obtenir les outils critiques | Liste `tools` |
| 6. Éliminer les barrières | La `checklist` bloque le minuteur tant que tout n'est pas coché |
| 7. Réserver du temps de pratique | `plan` calcule les minutes par jour pour finir à la date voulue |
| 8. Boucle de feedback rapide | Bilan immédiat : qualité, contrainte, total, série |
| 9. Pratiquer par courtes rafales chronométrées | Minuteur de `burst_minutes` (20 min par défaut) |
| 10. Quantité et vitesse plutôt que perfection | Toutes les sessions comptent, même ratées ; on vise la fréquence |

## Fichiers

- `index.html` : la page web, sans dépendance, servie par GitHub Pages.
- `habits.py` : le script terminal, Python 3.10+ et bibliothèque standard uniquement.
- `habits.json` : les habitudes (cible, sous-compétences, outils, checklist, études) et les références sur la méthode.
- `data/sessions.json` : le journal des sessions, versionné volontairement.
- `tests/test_habits.py` : tests unitaires, lancés par GitHub Actions à chaque push (`python -m unittest discover -s tests`).

La variable d'environnement `HABITS_DIR` permet de pointer le script vers un
autre dossier de données, utile pour tester sans toucher au vrai journal.
