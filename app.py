from urllib.parse import quote_plus
from flask import Flask, abort, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
import psycopg2


app = Flask(__name__)
motdepasse=quote_plus('root')
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:{}@localhost:5432/mydb'.format(motdepasse)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers','Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods','GET,PATCH,POST,DELETE,OPTIONS')
    return response

def paginate(request):
    items = [item.format() for item in request]
    return items

################################################################
#
#             Classe Livres
#
################################################################


class Livre(db.Model):
    __tablename__ = 'livres'
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(12), nullable=False)
    titre = db.Column(db.String(150), nullable=False)
    date_publication = db.Column(db.Date, nullable=False)
    auteur = db.Column(db.String(150), nullable=False)
    editeur = db.Column(db.String(150), nullable=False)
    categorie_id = db.Column(db.Integer,db.ForeignKey('categories.categorie_id'))


    def __init__(self,isbn,titre, date_publication,auteur,editeur,categorie_id):
        self.isbn = isbn
        self.titre = titre
        self.date_publication = date_publication
        self.auteur = auteur
        self.editeur = editeur
        self.categorie_id = categorie_id

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def format(self):
        return {
            'id' : self.id,
            'isbn' : self.isbn,
            'titre' : self.titre,
            'date_publication' : self.date_publication,
            'auteur' : self.auteur,
            'editeur' : self.editeur,
            'categorie_id': self.categorie_id
        }
db.create_all()   

################################################################
#
#             Classe Categories
#
################################################################


class Categorie(db.Model):
    __tablename__ = 'categories'
    categorie_id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(150), nullable=False)
    valeur = db.relationship ("Livre",backref = "categories",lazy=True )

    def __init__(self,libelle):
        self.libelle = libelle

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def format(self):
        return {
            'id_categorie': self.categorie_id,
            'libelle_categorie' : self.libelle
       }
db.create_all()



@app.route('/index')
def index():
    return render_template('Index.html')


################################################################
#
#             Endpoint liste de tous les Livres et ajouter un livre
#
################################################################

@app.route('/livres',methods=['GET','POST'])
def liste_livres():
    if request.method=='GET':
        # requete avec SQLAlchemy pour récupérer la liste de tous les livres
        livres=Livre.query.all()
        livres_formatted=[lv.format() for lv in livres]
        return jsonify({
            'success':True,
            'total_livres':Livre.query.count(),
            'livres':livres_formatted
        })
        return render_template('liste_ajout.html', data=Livre.query.all())

    elif request.method=='POST':
        body = request.get_json()
        isbn = body['isbn']
        new_titre = body['titre']
        new_date = body['date_publication']
        new_auteur = body['auteur']
        new_editeur = body['editeur']
        categorie_id = body['categorie_id']
        livre = Livre(isbn=isbn, titre=new_titre, date_publication=new_date,
                auteur=new_auteur, editeur=new_editeur, categorie_id=categorie_id)
        livre.insert()
        count = Livre.query.count()
        return jsonify({
            'success': True,
            'added': livre.format(),
            'total_books': count,
        })  

################################################################
#
#             Endpoint selectionner un livre en particulier
#
################################################################
@app.route('/livres/<int:id>')
def get_book(id):
    livre = Livre.query.get(id)
    if livre is None:
        abort(404)
    else:
        return livre.format()   




####################################################################
#
#               Lister la liste des livres d'une categorie
#
#####################################################################

@app.route('/categories/<int:id>/livres')
def book_category(id):
    try:
        category = Categorie.query.get(id)
        books = Livre.query.filter_by(categorie_id=id).all()
        books = paginate(books)
        return jsonify({
            'Success': True,
            'Status_code': 200,
            'total': len(books),
            'categorie': category.format(),
            'livres': books
        })
    except:
        abort(404)
    finally:
        db.session.close()


################################################################
#
#             Endpoint Supprimer un Livre
#
################################################################
@app.route('/livres/<int:id>',methods=['DELETE'])
def delete_etudiant(id):
    livre=Livre.query.get(id)
    if livre is None:
        abort(404)
    else:
        #supprimer le livre
        livre.delete()
        return jsonify({
            'success':True,
            'id':id,
            'livre':livre.format(),
            'total_livres':Livre.query.count()
        })



################################################################
#
#             Endpoint Modifier un Livre
#
################################################################   
@app.route('/livres/<int:id>',methods=['PATCH'])
def modifier_livre(id):
    
    livre=Livre.query.get(id)
    if livre is None:
        abort(404)
    else:
        body=request.get_json()
        livre.titre=body.get('titre')
        livre.auteur=body.get('auteur')
        livre.editeur=body.get('editeur')
        livre.date_publication=body.get('date_publication')       
        livre.update()
        return jsonify({
            'success':True,
            'updated_id':id,
            'livre':livre.format()
        })     


################################################################
#
#             Endpoint liste de toutes les categories et enregistrer aussi une categories
#
################################################################

@app.route('/categories',methods=['GET','POST'])
def liste_categories():
    if request.method=='GET':
        # requete avec SQLAlchemy pour récupérer la liste de tous les livres
        categories=Categorie.query.all()
        categories_formatted=[cat.format() for cat in categories]
        return jsonify({
            'success':True,
            'total_categories':Categorie.query.count(),
            'categories':categories_formatted
        })
        return render_template('liste_cat.html', data=Categorie.query.all())

    elif request.method=='POST':
        def add_category():
            body = request.get_json()
            new_categorie = body['libelle_categorie']
            category = Categorie(libelle=new_categorie)
            category.insert()
            return jsonify({
                'success': True,
                'added': category.format(),
                'total_categories': Categorie.query.count()
            })   


################################################################
#
#             Endpoint selectionner une categorie en particulier
#
################################################################
@app.route('/categories/<int:id>')
def get_category(id):
    categorie = Categorie.query.get(id)
    if categorie is None:
        abort(404)
    else:
        return categorie.format()   

################################################################
#
#             Endpoint Supprimer une categorie
#
################################################################
@app.route('/categories/<int:id>',methods=['DELETE'])
def delete_cat(id):
    categorie=Categorie.query.get(id)
    if categorie is None:
        abort(404)
    else:
        #supprimer la categorie
        categorie.delete()
        return jsonify({
            'success':True,
            'id':id,
            'categorie':Categorie.format(),
            'total_cat':Categorie.query.count()
        })



################################################################
#
#             Endpoint Modifier un categorie
#
################################################################   
@app.route('/categories/<int:id>',methods=['PATCH'])
def modifier_cat(id):
    
    categorie=Categorie.query.get(id)
    if categorie is None:
        abort(404)
    else:
        body=request.get_json()
        categorie.libelle_categorie=body.get('libelle')               
        categorie.update()
        return jsonify({
            'success':True,
            'updated_id':id,
            'categorie':categorie.format()
        })


###################################################################
#
# Rechercher un livre par son titre ou son auteur
#
###################################################################
@app.route('/livres/<string:word>')
def search_book(word):
    mot = '%'+word+'%'
    titre = Livre.query.filter(Livre.titre.like(mot)).all()
    titre = paginate(titre)
    return jsonify({
        'livres': titre
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False, 
        "error": 404,
        "message": "Not found"
        }), 404
    
@app.errorhandler(500)
def not_found(error):
    return jsonify({
        "success": False, 
        "error": 500,
        "message": "Internal server Error"
        }), 500

@app.errorhandler(400)
def not_found(error):
    return jsonify({
        "success": False, 
        "error": 400,
        "message": "Mauvaise requete"
        }), 400        