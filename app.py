#!/usr/bin/env python3
"""
LABO PEDAGOGIQUE SQLi -- VOLONTAIREMENT VULNERABLE
A utiliser UNIQUEMENT en local, pour s'entrainer avec sqlmap.
Ne JAMAIS exposer ce code sur un reseau non controle.
"""
import os
import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "shop.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn


PAGE_HEADER = """
<!doctype html>
<html><head><title>SQLi Demo Shop</title>
<style>
body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }
nav a { margin-right: 15px; }
input { padding: 6px; margin: 4px 0; }
table { border-collapse: collapse; width: 100%; margin-top: 15px; }
td, th { border: 1px solid #ccc; padding: 8px; text-align: left; }
.err { color: #b00020; font-family: monospace; white-space: pre-wrap; }
</style>
</head><body>
<nav>
  <a href="/">Accueil</a>
  <a href="/product?id=1">Produits (vulnerable: id)</a>
  <a href="/login">Login (vulnerable: username)</a>
  <a href="/search?q=clavier">Recherche (vulnerable: q)</a>
</nav>
<hr>
"""
PAGE_FOOTER = "</body></html>"


@app.route("/")
def index():
    return PAGE_HEADER + "<h1>Boutique de demo (volontairement vulnerable)</h1><p>Utilisez le menu pour tester les points d'injection.</p>" + PAGE_FOOTER


@app.route("/product")
def product():
    pid = request.args.get("id", "1")
    conn = get_db()
    cur = conn.cursor()
    # VULNERABLE: concatenation directe, pas de parametrage
    query = f"SELECT id, name, description, price FROM products WHERE id = {pid}"
    html = PAGE_HEADER + f"<h2>Produit (id={pid})</h2><p><code>{query}</code></p>"
    try:
        cur.execute(query)
        rows = cur.fetchall()
        html += "<table><tr><th>id</th><th>name</th><th>description</th><th>price</th></tr>"
        for r in rows:
            html += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
        html += "</table>"
    except Exception as e:
        html += f"<p class='err'>SQL Error: {e}</p>"
    conn.close()
    return html + PAGE_FOOTER


@app.route("/search")
def search():
    q = request.args.get("q", "")
    conn = get_db()
    cur = conn.cursor()
    # VULNERABLE: concatenation directe dans un LIKE
    query = f"SELECT id, name, description, price FROM products WHERE name LIKE '%{q}%'"
    html = PAGE_HEADER + f"<h2>Recherche: {q}</h2><p><code>{query}</code></p>"
    try:
        cur.execute(query)
        rows = cur.fetchall()
        html += "<table><tr><th>id</th><th>name</th><th>description</th><th>price</th></tr>"
        for r in rows:
            html += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
        html += "</table>"
    except Exception as e:
        html += f"<p class='err'>SQL Error: {e}</p>"
    conn.close()
    return html + PAGE_FOOTER


@app.route("/login", methods=["GET", "POST"])
def login():
    html = PAGE_HEADER + "<h2>Connexion</h2>"
    html += """
    <form method="post">
      <label>Username: <input name="username"></label><br>
      <label>Password: <input name="password" type="password"></label><br>
      <button type="submit">Se connecter</button>
    </form>
    """
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = get_db()
        cur = conn.cursor()
        # VULNERABLE: auth bypass classique via concatenation
        query = f"SELECT id, username, is_admin FROM users WHERE username = '{username}' AND password = '{password}'"
        html += f"<p><code>{query}</code></p>"
        try:
            cur.execute(query)
            row = cur.fetchone()
            if row:
                html += f"<p><b>Connexion reussie</b>: id={row[0]} username={row[1]} is_admin={row[2]}</p>"
            else:
                html += "<p>Identifiants invalides.</p>"
        except Exception as e:
            html += f"<p class='err'>SQL Error: {e}</p>"
        conn.close()
    return html + PAGE_FOOTER


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Base de donnees absente, lancez d'abord: python3 seed_db.py")
    app.run(host="127.0.0.1", port=5500, debug=False)
