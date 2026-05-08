# Deep Chess AI realise par ZEKARI Adam

Un projet complet de moteur d'echecs avec IA, en appliquant PyTorch et TensorFlow/Keras : representation du plateau, reseau neuronal, recherche minimax alpha-beta, entrainement par auto-jeu et interface jouable contre l'IA.

## Objectifs du projet

- Construire une IA capable de choisir des coups legaux avec Pythorch/TensorFlow-Keras.
- Proposer 3 niveaux de difficulte: facile, moyen, difficile.
- Montrer une architecture propre, testable et extensible.

## Fonctionnalites

- Jeu humain contre IA avec interface graphique Tkinter.
- Jeu humain contre IA en terminal.
- Choix de couleur: blancs ou noirs.
- Choix du niveau:
  - `facile`: coups rapides avec recherche faible et bruit aleatoire.
  - `moyen`: evaluation neuronale + recherche minimax.
  - `difficile`: recherche plus profonde + tri des coups + evaluation materielle.
- Mode entrainement par auto-jeu pour generer des donnees.
- Mode entrainement supervise a partir des parties generees.
- Version PyTorch avec sauvegarde/chargement de modeles `.pt`.
- Version TensorFlow/Keras avec sauvegarde/chargement de modeles `.keras`.
- Tests unitaires sur l'encodage et le moteur.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> Note: PyTorch et TensorFlow sont des bibliotheques lourdes. Si l'installation via `requirements.txt` echoue selon ta version de Python, installe PyTorch depuis https://pytorch.org/get-started/locally/ et TensorFlow selon la documentation officielle. Sur certaines machines, TensorFlow peut demander une version de Python plus stable comme 3.11 ou 3.12.

## Lancer le jeu

Interface graphique sans modele entraine:

```powershell
python -m chess_ai.gui
```

Si tu n'as pas encore entraine de modele, utilise cette commande. Les fichiers
`models/chess_value_net.pt` et `models/tf_chess_value_net.keras` sont crees
seulement apres l'entrainement.

Interface graphique avec un modele PyTorch:

```powershell
python -m chess_ai.gui --backend pytorch --model models/chess_value_net.pt
```

Interface graphique avec un modele TensorFlow:

```powershell
python -m chess_ai.gui --backend tensorflow --model models/tf_chess_value_net.keras
```

Interface terminal:

```powershell
python -m chess_ai.play --level medium
python -m chess_ai.play --level hard --human black --model models/chess_value_net.pt
python -m chess_ai.play --level hard --backend tensorflow --model models/tf_chess_value_net.keras
```

Pendant la partie terminal, entre les coups au format UCI:

```text
e2e4
g1f3
e7e8q
```

## Entrainer l'IA

Generer des parties par auto-jeu:

```powershell
python -m chess_ai.train_self_play --games 50 --output data/self_play.jsonl
```

Entrainer le reseau PyTorch:

```powershell
python -m chess_ai.train_value_model --data data/self_play.jsonl --epochs 8 --output models/chess_value_net.pt
```

Entrainer le reseau TensorFlow/Keras:

```powershell
python -m chess_ai.train_tensorflow_value_model --data data/self_play.jsonl --epochs 8 --output models/tf_chess_value_net.keras
```

## Structure

```text
pytorch-chess-ai/
  chess_ai/
    board_encoding.py              # transforme un echiquier en tenseur numerique
    engine.py                      # choix des coups selon le niveau
    evaluation.py                  # evaluation materielle + PyTorch
    tf_evaluation.py               # evaluation avec TensorFlow/Keras
    gui.py                         # interface graphique Tkinter
    model.py                       # CNN PyTorch
    tf_model.py                    # CNN TensorFlow/Keras
    search.py                      # minimax alpha-beta
    play.py                        # jeu humain vs IA
    train_self_play.py             # generation de dataset
    train_value_model.py           # entrainement PyTorch
    train_tensorflow_value_model.py # entrainement TensorFlow/Keras
  web/
    index.html                    # site web du projet
    styles.css                    # design responsive
    app.js                        # demo interactive + connexion locale
    server.js                     # serveur temps reel pour salons + chat
  tests/
    test_board_encoding.py
    test_engine.py
  requirements.txt
```
