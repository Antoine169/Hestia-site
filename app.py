from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hestia-cle-secrete"

PRODUCT = {
    "nom": 'Tablette',
    "description": "Tablette de cuisine avec inventaire, alertes et recettes intelligentes.",
    "prix": 199
}


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_commande TEXT NOT NULL UNIQUE,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT NOT NULL,
            adresse TEXT NOT NULL,
            ville TEXT NOT NULL,
            code_postal TEXT NOT NULL,
            produit TEXT NOT NULL,
            quantite INTEGER NOT NULL,
            prix_unitaire REAL NOT NULL,
            total REAL NOT NULL,
            date_commande TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def generer_numero_commande():
    return "CMD-" + str(random.randint(100000, 999999))


@app.route("/")
def index():
    cart_quantity = session.get("cart_quantity", 0)
    return render_template("index.html", produit=PRODUCT, cart_quantity=cart_quantity)


@app.route("/ajouter-au-panier", methods=["POST"])
def ajouter_au_panier():
    quantite = request.form.get("quantite", type=int)

    if not quantite or quantite < 1:
        quantite = 1

    session["cart_quantity"] = quantite
    return redirect(url_for("panier"))


@app.route("/panier")
def panier():
    cart_quantity = session.get("cart_quantity", 0)

    if cart_quantity < 1:
        return render_template("panier.html", produit=PRODUCT, panier_vide=True, cart_quantity=0)

    total = PRODUCT["prix"] * cart_quantity

    return render_template(
        "panier.html",
        produit=PRODUCT,
        quantite=cart_quantity,
        total=total,
        panier_vide=False,
        cart_quantity=cart_quantity
    )


@app.route("/vider-panier", methods=["POST"])
def vider_panier():
    session["cart_quantity"] = 0
    return redirect(url_for("panier"))


@app.route("/valider-commande", methods=["POST"])
def valider_commande():
    cart_quantity = session.get("cart_quantity", 0)

    if cart_quantity < 1:
        return redirect(url_for("panier"))

    nom = request.form.get("nom", "").strip()
    prenom = request.form.get("prenom", "").strip()
    email = request.form.get("email", "").strip()
    adresse = request.form.get("adresse", "").strip()
    ville = request.form.get("ville", "").strip()
    code_postal = request.form.get("code_postal", "").strip()

    if not nom or not prenom or not email or not adresse or not ville or not code_postal:
        return "Erreur : veuillez remplir tous les champs.", 400

    prix_unitaire = PRODUCT["prix"]
    total = prix_unitaire * cart_quantity
    date_commande = datetime.now().strftime("%d/%m/%Y à %H:%M")
    numero_commande = generer_numero_commande()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO commandes (
            numero_commande, nom, prenom, email, adresse, ville, code_postal,
            produit, quantite, prix_unitaire, total, date_commande
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        numero_commande,
        nom,
        prenom,
        email,
        adresse,
        ville,
        code_postal,
        PRODUCT["nom"],
        cart_quantity,
        prix_unitaire,
        total,
        date_commande
    ))

    conn.commit()
    commande_id = cursor.lastrowid
    conn.close()

    session["last_order_id"] = commande_id
    session["cart_quantity"] = 0

    return redirect(url_for("commande"))


@app.route("/commande")
def commande():
    cart_quantity = session.get("cart_quantity", 0)
    last_order_id = session.get("last_order_id")

    if not last_order_id:
        return render_template("commande.html", commande=None, cart_quantity=cart_quantity)

    conn = get_db_connection()
    commande = conn.execute(
        "SELECT * FROM commandes WHERE id = ?",
        (last_order_id,)
    ).fetchone()
    conn.close()

    return render_template("commande.html", commande=commande, cart_quantity=cart_quantity)

@app.route("/commandes")
def voir_commandes():
    conn = get_db_connection()
    commandes = conn.execute("SELECT * FROM commandes").fetchall()
    conn.close()

    return render_template("commandes.html", commandes=commandes)

init_db()

if __name__ == "__main__":
    app.run()
