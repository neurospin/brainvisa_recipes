# Twin game

To win the game, you have to choose the correct pairs of twins, based on the morphology of the folds. It permits to get an intuition on what is dependent on genetics and what is dependent on neurodevelopment. Here is the screenshot of the game:

![Screenshot](images/screenshot.png)

## Get started

First, you need to have installed pyanatomist and pyaims (see the [../README.md](../README.md) at the root of brainvisa_recipes).

The following will work if the HCP dataset is in the directory /neurospin/dico/data/bv_databases/human/not_labeled/hcp, which is the case if you are running the software from the neurospin computer:

If you have installed brainvisa using the ApptTainer way:
* Either:
```
bv python twingame.py -c twin_config_hcp.json
```
* Or:
```
bv bash
python twingame.py -c twin_config_hcp.json
```
Otherwise, if you have installed pyanatomist and pyaims with pixi:
```
pixi shell
python twingame.py -c twin_config_hcp.json
```


## Miscellaneous (some developper comments)

1 fenêtre
panneau gauche: boutons
espace droite: vues 3D
menu: réglages
utilisable sans souris sur un écran tactile

chaque vue a une poignée colorée pour associer ou dépacer les vues

zoom ? la forme globale du cerveau rend peut-être le jeu trop facile ?
-> ne pas montrer le maillage individuel, mais un maillage moyen ?

actions:
- démarrer / remettre à 0
- déplacer une vue pour la mettre à côté d'une autre
- associer une paire: cocher 2 boutons et cliquer sur "associer"
- dissocier une paire (revenir en arrière)
- voir la solution, diffs avec l'essai du joueur
- sync views

- reset zoom, points de vue ?

réglages:
- nombre de paires visibles
- hémisphère
- associer des hémisphères ?

dataset:
fichier .json en entrée
