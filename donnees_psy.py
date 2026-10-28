#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse des saccades et des fixations du regard du Psy.

Traduction Python du script R d'origine.

Usage :
    python analyse_saccades.py chemin/vers/fichier.csv

Sorties (enregistrées dans le même répertoire que le fichier d'entrée) :
    - anv_psy.csv                   : jeu de données avec région et saccade
    - proportion_saccades.png       : proportion de chaque type de saccade
    - comparaison_zones_psy.png     : % du temps de regard et nombre de
                                      fixations par zone

Dépendances : pandas, numpy, matplotlib
"""

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")  # pas besoin d'écran pour sauvegarder les figures
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ------------------------------------------------------------------------------
# Paramètres
# ------------------------------------------------------------------------------
COLONNES_UTILES = ["Frame", "Capture.Time", "Lft.X.Pos", "Lft.Y.Pos", "region", "type_absence"]

TITRE_TEMPS = "Répartition du temps de regard du Psy par zone"
TITRE_NB_FIX = "Nombre de fixations du Psy par zone"

ABSENCE = "Absence_valeurs"
INVALIDE = "Frame_invalide"


# ------------------------------------------------------------------------------
# Lecture et préparation des données
# ------------------------------------------------------------------------------
def lire_csv(chemin):
    """Lit le CSV (séparateur détecté automatiquement) et normalise les noms
    de colonnes à la manière de R : 'Capture Time' -> 'Capture.Time'."""
    df = pd.read_csv(chemin, sep=None, engine="python")
    df.columns = [str(c).strip().replace(" ", ".") for c in df.columns]

    manquantes = [c for c in COLONNES_UTILES if c not in df.columns]
    if manquantes:
        sys.exit(f"Colonnes introuvables dans le fichier : {manquantes}\n"
                 f"Colonnes disponibles : {list(df.columns)}")
    return df


def recoder_region(serie):
    """Recode la colonne region (codes numériques -> noms de zones)."""
    reg = pd.to_numeric(serie, errors="coerce")
    correspondance = {
        0: "Autre",
        1: "Yeux",
        2: "Bouche_Nez",
        3: "Visage",
        5: "Visage",
        4: "Corps",
        255: ABSENCE,
        254: INVALIDE,  # frame mal segmentée
    }
    # Toute valeur inattendue devient NaN
    return reg.map(correspondance)


# ------------------------------------------------------------------------------
# Détermination des saccades
# ------------------------------------------------------------------------------
def rle(valeurs):
    """Équivalent de rle() en R : retourne (valeurs, longueurs)."""
    vals, longs = [], []
    for v in valeurs:
        if vals and vals[-1] == v:
            longs[-1] += 1
        else:
            vals.append(v)
            longs.append(1)
    return vals, np.array(longs)


def detecter_saccades(anv):
    """Ajoute la colonne 'saccade' ('inter' / 'intra' / NaN).

    Retourne (anv, positions_inter, positions_intra) ; les positions sont des
    indices de ligne (base 0)."""
    # NaN remplacés par un libellé pour que la comparaison de texte fonctionne
    labels = anv["region"].astype(object).where(anv["region"].notna(), "NA")
    vals, longueurs = rle(labels.tolist())
    n_runs = len(vals)
    fins = np.cumsum(longueurs) - 1  # dernier indice de chaque run (base 0)

    saccade = pd.Series([np.nan] * len(anv), index=anv.index, dtype=object)
    pos_inter, pos_intra = [], []

    for r in range(n_runs - 1):
        # On ne part jamais d'un run "Absence_valeurs" lui-même
        if vals[r] == ABSENCE:
            continue

        pos_avant = int(fins[r])  # dernière position du run réel courant

        if vals[r + 1] != ABSENCE:
            # Transition directe entre deux régions réelles -> changement de zone
            saccade.iloc[pos_avant] = "inter"
            pos_inter.append(pos_avant)
        else:
            # Le run suivant est un gap : on regarde le run APRÈS le gap
            if r + 2 <= n_runs - 1:
                if vals[r + 2] == vals[r]:
                    saccade.iloc[pos_avant] = "intra"
                    pos_intra.append(pos_avant)
                else:
                    saccade.iloc[pos_avant] = "inter"
                    pos_inter.append(pos_avant)
            # Si le gap va jusqu'à la fin des données : rien n'est marqué

    anv["saccade"] = saccade
    return anv, pos_inter, pos_intra


# ------------------------------------------------------------------------------
# Fixations
# ------------------------------------------------------------------------------
def calculer_fixations(anv, pos_inter, pos_intra):
    """Détermine début, fin, durée et zone de chaque fixation (temps en minutes,
    le temps de capture étant en microsecondes)."""
    pos = sorted(pos_inter + pos_intra)
    n_sac = len(pos)
    n_rows = len(anv)
    temps = anv["Capture.Time"].to_numpy(dtype=float)
    regions = anv["region"].to_numpy(dtype=object)

    debut = np.zeros(n_sac + 1)
    fin = np.zeros(n_sac + 1)
    zone = [None] * (n_sac + 1)

    zone[0] = regions[0]
    fin[0] = temps[pos[0]] if n_sac > 0 else temps[n_rows - 1]

    for k in range(n_sac):
        i = pos[k]
        if i + 1 >= n_rows:
            continue
        debut[k + 1] = temps[i + 1]
        zone[k + 1] = regions[i + 1]
        fin[k + 1] = temps[pos[k + 1]] if k < n_sac - 1 else temps[n_rows - 1]

    recap = pd.DataFrame({"zone_fix": zone, "debut_fix": debut, "fin_fix": fin})
    recap["duree_fix"] = recap["fin_fix"] - recap["debut_fix"]

    # microsecondes -> minutes
    for c in ["debut_fix", "fin_fix", "duree_fix"]:
        recap[c] = recap[c] / 1e6 / 60
    return recap


def resumer_par_zone(recap_fix):
    """Agrégats par zone (hors absence de valeurs et frames invalides)."""
    f = recap_fix[recap_fix["zone_fix"].notna()
                  & ~recap_fix["zone_fix"].isin([ABSENCE, INVALIDE])]
    recap_zone = (
        f.groupby("zone_fix")
        .agg(nb_fixations=("duree_fix", "size"),
             temps_total_min=("duree_fix", "sum"),
             duree_moyenne_min=("duree_fix", "mean"))
        .reset_index()
    )
    recap_zone["pct_temps"] = recap_zone["temps_total_min"] / recap_zone["temps_total_min"].sum() * 100
    recap_zone["pct_fix"] = recap_zone["nb_fixations"] / recap_zone["nb_fixations"].sum() * 100
    return recap_zone.sort_values("pct_temps", ascending=False).reset_index(drop=True)


# ------------------------------------------------------------------------------
# Graphiques
# ------------------------------------------------------------------------------
def style_axes(ax):
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.xaxis.grid(True, color="#e5e5e5")
    ax.set_axisbelow(True)


def barh_etiquettes(ax, labels, valeurs, couleurs, formatter, xlim=None):
    ax.barh(labels, valeurs, color=couleurs, height=0.6)
    vmax = max(valeurs) if len(valeurs) else 1
    for i, v in enumerate(valeurs):
        ax.text(v + vmax * 0.01, i, formatter(v), va="center", fontsize=11)
    if xlim is not None:
        ax.set_xlim(*xlim)
    else:
        ax.set_xlim(0, vmax * 1.15)
    style_axes(ax)


def graphe_saccades(anv, chemin_png):
    recap = (anv.dropna(subset=["saccade"])
             .groupby("saccade").size().reset_index(name="nb_saccades"))
    recap["pct_nb"] = recap["nb_saccades"] / recap["nb_saccades"].sum() * 100
    recap = recap.sort_values("pct_nb")

    palette = {"inter": "#e8743b", "intra": "#19a979"}
    fig, ax = plt.subplots(figsize=(8, 4))
    barh_etiquettes(ax, recap["saccade"].tolist(), recap["pct_nb"].tolist(),
                    [palette.get(s, "#888888") for s in recap["saccade"]],
                    lambda v: f"{v:.1f}%", xlim=(0, 100))
    ax.set_title("Proportion de chaque type de saccade", loc="left", fontsize=13)
    ax.set_xlabel("% du nombre total de saccades")
    fig.tight_layout()
    fig.savefig(chemin_png, dpi=300)
    plt.close(fig)


def graphe_zones(recap_zone, chemin_png):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    d1 = recap_zone.sort_values("pct_temps")
    barh_etiquettes(ax1, d1["zone_fix"].tolist(), d1["pct_temps"].tolist(),
                    "#2a78d6", lambda v: f"{v:.1f}%", xlim=(0, 100))
    ax1.set_title(TITRE_TEMPS, loc="left", fontsize=13)
    ax1.set_xlabel("% du temps total")

    d2 = recap_zone.sort_values("nb_fixations")
    pct_par_zone = dict(zip(d2["nb_fixations"], d2["pct_fix"]))  # étiquette = % de fixations
    barh_etiquettes(ax2, d2["zone_fix"].tolist(), d2["nb_fixations"].tolist(),
                    "#1baf7a", lambda v: f"{pct_par_zone[v]:.1f}%")
    ax2.set_title(TITRE_NB_FIX, loc="left", fontsize=13)
    ax2.set_xlabel("Nombre de fixations")

    fig.tight_layout()
    fig.savefig(chemin_png, dpi=300)
    plt.close(fig)


# ------------------------------------------------------------------------------
# Programme principal
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Analyse des saccades et fixations du regard du Psy.")
    parser.add_argument("csv", help="Chemin du fichier CSV d'entrée")
    args = parser.parse_args()

    chemin_csv = os.path.abspath(args.csv)
    out_dir = os.path.dirname(chemin_csv)  # sorties dans le même répertoire

    # Extraction des variables d'intérêt
    X = lire_csv(chemin_csv)
    anv_psy = X[COLONNES_UTILES].copy()
    anv_psy["region"] = recoder_region(anv_psy["region"])

    # Saccades
    anv_psy, pos_inter, pos_intra = detecter_saccades(anv_psy)

    # Sauvegarde du jeu de données
    chemin_anv = os.path.join(out_dir, "anv_psy.csv")
    anv_psy.to_csv(chemin_anv, index=False, encoding="utf-8")

    # Graphe des saccades
    graphe_saccades(anv_psy, os.path.join(out_dir, "proportion_saccades.png"))

    # Fixations
    recap_fix = calculer_fixations(anv_psy, pos_inter, pos_intra)
    recap_zone = resumer_par_zone(recap_fix)
    print(recap_zone.to_string(index=False))

    # Graphe des fixations par zone
    graphe_zones(recap_zone, os.path.join(out_dir, "comparaison_zones_psy.png"))

    print(f"\nFichiers enregistrés dans : {out_dir}")
    print("  - anv_psy.csv")
    print("  - proportion_saccades.png")
    print("  - comparaison_zones_psy.png")


if __name__ == "__main__":
    main()
