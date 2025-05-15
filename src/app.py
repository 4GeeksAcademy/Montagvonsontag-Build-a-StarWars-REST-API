"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Favourite
from sqlalchemy import select
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/users', methods=['GET'])
def get_users():
    # esto se puede poner dentro del execute() sin problemas
    stmt = select(User) 
    # devuelve una lista con todos los registros de la tabla, cada uno como un <Objeto>
    users = db.session.execute(stmt).scalars().all() 
    # el scalars() se ocupa de devolverlos como objeto, sino seran devueltos como tuplas.
    # como tupla NO pueden ejecutar el serialize
    print('users sin serialize',users) #users sin serialize [<User 1>, <User 2>]
    print('users despues de loop con serialize', [user.serialize() for user in users])
    #users despues de loop con serialize 
    # [
    # {'id': 1, 'email': 'alice@example.com', 'profile': {'id': 1, 'bio': 'Soy Alice'}}, 
    # {'id': 2, 'email': 'bob@example.com', 'profile': {'id': 2, 'bio': 'Soy Bob'}}
    #]
    #siempre que se nos devuelva una lista/coleccion, hay que serializar dentro de un loop
    return jsonify([user.serialize() for user in users]), 200

# GET: Get one user by id
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    stmt = select(User).where(User.user_id == user_id)
    user = db.session.execute(stmt).scalar_one_or_none()
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.serialize()), 200

# POST: Create new user
@app.route("/users", methods=["POST"])
def create_user():
    #extraemos la informacion del body puede ser con request.json
    data = request.get_json()
    #verificamos que tenemos los elementos OBLIGATORIOS para crear un registro nuevo
    if not data or "user_name" not in data or "first_name" not in data or "last_name" not in data or "email" not in data or "password" not in data:
        return jsonify({"error": "Missing data"}), 400
    
    new_user = User(
        user_name=data["user_name"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        password=data["password"],  # To be hashed (in production)
    )
    #Addition to DB
    db.session.add(new_user)
    #storage of data
    db.session.commit()
    return jsonify(new_user.serialize()), 201
   
# DELETE USER 
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    stmt = select(User).where(User.user_id == user_id)
    user = db.session.execute(stmt).scalar_one_or_none()
    if user is None:
        return jsonify({'error':'User not found'}), 404
    if user.favourites:
        db.session.delete(user.favourites)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message':'user deleted'}),200

# UPDATE USER
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    stmt = select(User).where(User.user_id == user_id)
    user = db.session.execute(stmt).scalar_one_or_none()
    if user is None:
        return jsonify({'error':'User not found'}), 404
    if "email" in data:
        user.email=data["email"]
    if "user_name" in data:
        user.user_name=data["user_name"]
    if "first_name" in data:
        user.first_name=data["first_name"]
    if "last_name" in data:
        user.last_name=data["last_name"]
    if "password" in data:
        user.password=data["password"]
    #Storage of data
    db.session.commit()
    return jsonify(user.serialize()),200

@app.route('/characters', methods=['GET'])
def get_characters():
    stmt = select(Character) 
    characters = db.session.execute(stmt).scalars().all() 
    return jsonify([character.serialize() for character in characters]), 200

@app.route("/characters", methods=["POST"])
def create_character():
    data = request.get_json()
    if not data or "character_name" not in data:
        return jsonify({"error": "Missing data"}), 400
    new_character = Character(
        character_name=data["character_name"],
    )
    #Addition to DB
    db.session.add(new_character)
    #Storage of data
    db.session.commit()
    return jsonify(new_character.serialize()), 201

# DELETE Character 
@app.route('/characters/<int:id_character>', methods=['DELETE'])
def delete_character(id_character):
    stmt = select(Character).where(Character.id_character == id_character)
    character = db.session.execute(stmt).scalar_one_or_none()
    if character is None:
        return jsonify({'error':'Character not found'}), 404
    if character.favourites:
        db.session.delete(character.favourites)
    db.session.delete(character)
    db.session.commit()
    return jsonify({'message':'character deleted'}),200

@app.route("/favourites", methods=["GET"])
def get_favourites():
    stmt = select(Favourite) 
    favourites = db.session.execute(stmt).scalars().all() 
    return jsonify([favourite.serialize() for favourite in favourites]), 200

#POST: Favourites
@app.route('/favourites/<int:user_id>/<int:id_character>', methods=['POST'])
def add_favourite(user_id, id_character):
    user = db.session.get(User, user_id)
    character = db.session.get(Character, id_character)
    if not user:
        return jsonify({"error": "User does not exist"}), 404
    if not character:
        return jsonify({"error": "Character does not exist"}), 404

    #Check for duplicate favourite  
    existing = db.session.execute(
        select(Favourite).where(Favourite.user_id==user_id, Favourite.id_character==id_character)
    ).scalar_one_or_none()
    if existing:
        return jsonify({"error": "Favourite already exists"}), 409
    new_favourite = Favourite(
        user_id=user_id,
        id_character=id_character
    )
    db.session.add(new_favourite)
    db.session.commit() 
    return jsonify(new_favourite.serialize()), 201

# DELETE FAVOURITE
@app.route('/favourites/<int:user_id>/<int:id_character>', methods=['DELETE'])
def delete_favourite(user_id, id_character):
    stmt = select(Favourite).where(Favourite.user_id == user_id and Favourite.id_character == id_character)
    favourite = db.session.execute(stmt).scalar_one_or_none()
    if favourite is None:
        return jsonify({'error':'favourite not found'}), 404
    db.session.delete(favourite)
    db.session.commit()
    return jsonify({'message':'favourite deleted'}),200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
