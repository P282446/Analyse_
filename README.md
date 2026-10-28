# Analyse des fixations oculométriques et synchronisation avec la transcription

## 1. Présentation du projet

Ce pipeline regroupe trois programmes Python destinés à l'analyse des données oculométriques issues d'un eye-tracker et à leur synchronisation avec les données de transcription d'entretiens.

Il permet de :

- Analyser les fixations et les saccades du sujet.
- Analyser les fixations et les saccades du psychologue.
- Étudier la répartition du regard entre les différentes régions d'intérêt.
- Synchroniser les données oculométriques avec les tours de parole de l'entretien.
- Produire des fichiers de données et des visualisations facilitant l'analyse statistique des comportements oculaires pendant les échanges.

## 2. Organisation du pipeline

Le pipeline est composé de trois programmes :

| Programme | Fonction |
|---|---|
| `donnees_sujet.py` | Analyse des fixations et des saccades du sujet. |
| `donnees_psy.py` | Analyse des fixations et des saccades du psychologue. |
| `ana_trans.py` | Synchronisation des données oculométriques avec les données de transcription. |

Les deux premiers programmes produisent des fichiers enrichis contenant les informations relatives aux régions de regard et aux types de saccades. Le troisième utilise ces fichiers et la transcription de l'entretien pour construire un jeu de données synchronisé.

## 3. Prérequis et installation

### 3.1. Créer un environnement virtuel

Depuis le répertoire du projet, créez un environnement virtuel Python :

```bash
python3 -m venv .venv
```

Activez ensuite l'environnement :

```bash
source .venv/bin/activate
```

### 3.2. Installer les dépendances

Installez les bibliothèques nécessaires :

```bash
python -m pip install --upgrade pip
python -m pip install pandas numpy matplotlib openpyxl
```

Les bibliothèques utilisées sont :

- `pandas` : lecture, manipulation et exportation des données.
- `numpy` : calculs numériques.
- `matplotlib` : génération des graphiques.
- `openpyxl` : création et mise en forme des fichiers Excel.

## 4. Analyse des fixations du sujet

Le programme `donnees_sujet.py` permet d'analyser les données oculométriques du sujet, notamment la répartition du regard entre les régions d'intérêt et les caractéristiques des saccades.

### 4.1. Utilisation

```bash
python donnees_sujet.py chemin/vers/fichier.csv
```

Remplacez `chemin/vers/fichier.csv` par le chemin du fichier CSV contenant les données oculométriques du sujet.

### 4.2. Fichiers générés

Les résultats sont enregistrés dans le même répertoire que le fichier d'entrée.

| Fichier | Description |
|---|---|
| `anv_sujet.csv` | Jeu de données enrichi contenant notamment les régions de regard et les classifications des saccades. |
| `proportion_saccades.png` | Graphique représentant la proportion de chaque type de saccade. |
| `comparaison_zones_sujet.png` | Graphique comparant le pourcentage du temps de regard et le nombre de fixations par région. |

Ces résultats permettent de caractériser le comportement oculaire du sujet et d'étudier la distribution de son regard entre les différentes zones.

## 5. Analyse des fixations du psychologue

Le programme `donnees_psy.py` réalise une analyse similaire à celle du sujet, mais appliquée aux données oculométriques du psychologue.

### 5.1. Utilisation

```bash
python donnees_psy.py chemin/vers/fichier.csv
```

Remplacez `chemin/vers/fichier.csv` par le chemin du fichier contenant les données oculométriques du psychologue.

### 5.2. Fichiers générés

Les résultats sont enregistrés dans le même répertoire que le fichier d'entrée.

| Fichier | Description |
|---|---|
| `anv_psy.csv` | Jeu de données enrichi contenant les régions de regard et les classifications des saccades. |
| `proportion_saccades.png` | Graphique représentant la proportion de chaque type de saccade. |
| `comparaison_zones_psy.png` | Graphique comparant le pourcentage du temps de regard et le nombre de fixations par région. |

Ces résultats permettent d'étudier le comportement oculaire du psychologue et de le comparer à celui du sujet.

**Remarque :** si les résultats des deux analyses sont enregistrés dans le même dossier, vérifiez que le nom `proportion_saccades.png` n'entraîne pas l'écrasement du graphique précédent. Il est préférable de conserver les sorties dans des dossiers distincts ou d'adapter les noms de fichiers.

## 6. Synchronisation des fixations avec la transcription

Le programme `ana_trans.py` permet de synchroniser les données oculométriques du sujet et du psychologue avec les tours de parole de l'entretien.

Il combine les informations temporelles du regard avec les intervalles de parole afin de produire un jeu de données commun utilisable pour les analyses statistiques.

### 6.1. Fichiers d'entrée

La synchronisation nécessite trois fichiers :

- `anv_psy.csv` : données oculométriques analysées du psychologue.
- `anv_sujet.csv` : données oculométriques analysées du sujet.
- Le fichier de transcription de l'entretien.

Les fichiers oculométriques doivent notamment contenir les colonnes suivantes, lorsqu'elles sont disponibles :

- `Capture.Time` : temps de capture de l'eye-tracker.
- `region` : région de regard.
- `saccade` : classification de la saccade.
- `type_absence` : catégorie d'absence de mesure, si cette information est disponible.

Le fichier de transcription doit être un fichier **sans en-tête**, dans lequel les colonnes suivantes correspondent aux positions indiquées :

| Numéro de colonne | Information attendue |
|---|---|
| 1 | Locuteur |
| 4 | Début de la prise de parole, en secondes |
| 6 | Fin de la prise de parole, en secondes |
| 8 | Durée de la prise de parole, en secondes |
| 9 | Contenu verbal de la prise de parole |

Les colonnes intermédiaires doivent être conservées afin de respecter la structure attendue par le programme.

### 6.2. Utilisation simple

```bash
python ana_trans.py anv_psy.csv anv_sujet.csv transcription.txt
```

Adaptez les chemins en fonction de l'emplacement des fichiers à traiter.

### 6.3. Options disponibles

| Option | Description |
|---|---|
| `--entretien NOM` | Définit le nom de l'entretien utilisé dans les noms des fichiers générés. |
| `--sortie DOSSIER` | Définit le dossier de destination des résultats. Par défaut, le dossier de la transcription est utilisé. |
| `--decalage SECONDES` | Ajoute un décalage temporel aux débuts et aux fins des prises de parole. La valeur par défaut est `0`. |
| `--sans-silences` | Ne conserve que les instants où un locuteur est en train de parler. |
| `--locuteurs ...` | Définit les locuteurs à prendre en compte. Par défaut : `psy sujet br`. |
| `--sep SEP` | Définit le séparateur de la transcription. Par défaut, le séparateur est détecté automatiquement ; `tab` peut être utilisé pour un fichier séparé par des tabulations. |
| `--graphes` | Demande également l'enregistrement d'un graphique représentant la répartition des locuteurs. |

### 6.4. Exemple avec plusieurs options

```bash
python ana_trans.py anv_psy.csv anv_sujet.csv transcription.txt \
    --entretien BOC-066 \
    --sortie resultats/BOC-066 \
    --decalage 0 \
    --locuteurs psy sujet \
    --graphes
```

Dans cet exemple, les données synchronisées sont produites dans le dossier `resultats/BOC-066`, avec le nom de l'entretien `BOC-066`.

Vérifiez que les noms des locuteurs correspondent aux étiquettes présentes dans le fichier de transcription.

### 6.5. Fichiers générés

Les résultats sont enregistrés dans le dossier de sortie choisi, ou par défaut dans le dossier de la transcription.

| Fichier | Description |
|---|---|
| `sync_FP_TAbs_<entretien>.csv` | Jeu de données synchronisé au format CSV. |
| `sync_FP_TAbs_<entretien>.xlsx` | Version Excel mise en forme avec des couleurs. |

Le graphique de répartition des locuteurs est également enregistré lorsque l'option `--graphes` est activée.

Le jeu de données synchronisé permet de relier les caractéristiques du regard aux intervalles de parole et d'étudier les comportements oculaires en fonction du déroulement de l'entretien.

## 7. Ordre recommandé d'exécution

Pour traiter un nouvel entretien, il est recommandé de suivre l'ordre suivant :

1. Exécuter `anv_sujet.py` sur les données oculométriques du sujet.
2. Exécuter `anv_psy.py` sur les données oculométriques du psychologue.
3. Vérifier les fichiers CSV produits.
4. Exécuter `ana_trans.py` en utilisant les deux fichiers analysés et la transcription de l'entretien.
5. Examiner le fichier CSV synchronisé et, si nécessaire, sa version Excel.

Cet ordre garantit que les fichiers attendus par le programme de synchronisation ont été produits avant son exécution.

## 8. Points de vigilance

- Les temps utilisés dans les fichiers doivent être cohérents avec les conventions temporelles attendues par les programmes.
- La transcription doit respecter la structure sans en-tête attendue par le script de synchronisation.
- Les noms et les étiquettes des locuteurs doivent être cohérents entre les fichiers.
- Les fichiers d'entrée doivent contenir les colonnes nécessaires à chaque étape.
- Les fichiers produits doivent être contrôlés avant toute analyse statistique.
- Les données d'entretiens et les informations personnelles doivent être conservées dans un espace sécurisé et ne pas être publiées dans le dépôt sans autorisation.

## 9. Objectif scientifique

Ce pipeline vise à faciliter l'analyse des comportements oculaires du sujet et du psychologue pendant les entretiens.

L'analyse séparée des fixations et des saccades, suivie de la synchronisation avec les tours de parole, permet de construire un jeu de données adapté à l'étude conjointe du regard et de la dynamique des échanges verbaux.


