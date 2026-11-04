# Attaques SQL automatisées — labo pédagogique + pipeline sqlmap

Projet réalisé pour un exposé sur **l'automatisation des injections SQL** (sqlmap et au-delà).
Il comprend une application volontairement vulnérable, et un pipeline Python qui orchestre
l'ensemble d'une attaque SQL — détection, énumération, dump, analyse — en une seule commande,
sans intervention humaine entre les étapes.

> ⚠️ **Usage éducatif uniquement.** L'application cible tourne en local (`127.0.0.1`), sans
> exposition réseau. N'exécutez jamais ces techniques contre un système que vous ne possédez pas
> ou pour lequel vous n'avez pas d'autorisation écrite.

## Contenu

| Fichier | Rôle |
|---|---|
| `app.py` | Application Flask + SQLite volontairement vulnérable (3 points d'injection : paramètre GET, LIKE, formulaire de login) |
| `seed_db.py` | (Re)crée la base de données de démo avec des données fraîches |
| `auto_attack.py` | **Pipeline d'attaque SQL automatisé** : détection → fingerprint → énumération → dump → recherche de secrets/flags → rapport Markdown/JSON |
| `demo_manuel_vs_auto.sh` | Démo comparative en direct : exploitation manuelle (lente, requête par requête) vs automatisée (`auto_attack.py`) |
| `CHEATSHEET.md` | Toutes les commandes prêtes à l'emploi pour une démonstration live |

## Démarrage rapide

```bash
pip install flask
python3 seed_db.py          # crée la base de données
python3 app.py               # lance le serveur sur http://127.0.0.1:5500
```

Dans un second terminal :

```bash
# Démo comparative manuel vs automatisé (interactive)
./demo_manuel_vs_auto.sh

# Ou directement le pipeline automatisé
python3 auto_attack.py "http://127.0.0.1:5500/product?id=1"
```

## Ce que démontre `auto_attack.py`

Une seule commande enchaîne automatiquement :

1. **Détection** des techniques d'injection (boolean-based blind, time-based blind, UNION-based...)
2. **Fingerprint** du SGBD
3. **Énumération** des tables accessibles
4. **Dump complet** des données
5. **Analyse automatique** du dump (recherche de flags et de colonnes sensibles : mots de passe, tokens, secrets)
6. **Génération d'un rapport** (`report.md` + `report.json`) prêt à présenter

C'est cette orchestration de bout en bout — pas seulement "lancer sqlmap" — qui illustre
concrètement ce que signifie *automatiser* une attaque SQL : transformer un processus
manuel long et répétitif (des dizaines de minutes, des centaines de requêtes) en une
opération de quelques dizaines de secondes, reproductible et sans décision humaine
intermédiaire.

## Stack technique

- Python 3 / Flask / SQLite
- [sqlmap](https://sqlmap.org/) comme moteur de détection et d'exploitation
- Bash pour la démo comparative
