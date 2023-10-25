from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route('/health', methods=['GET'])
def health():
    return jsonify(dict(status="OK")), 200

@app.route('/count', methods=['GET'])
def count():
    count = db.songs.count_documents({})
    return {"count": count}, 200

@app.route('/song', methods=['GET'])
def songs():
    songs = db.songs.find({})
    return {"songs": parse_json(songs)}

@app.route('/song/<int:song_id>', methods=['GET'])
def get_song_by_id(song_id):
    song = db.songs.find_one({'id': song_id})
    if song:
        return parse_json(song), 200  # Return the entire picture data
    else:
        abort(404)

@app.route('/song', methods=['POST'])
def create_song():
    data = request.get_json()
    if db.songs.find_one({"id": data["id"]}):
        return {"Message": "song with id {} already present".format(data['id'])}, 302
    db.songs.insert_one(data)
    return {"inserted id": data["id"]}, 201


@app.route('/song/<int:song_id>', methods=['PUT'])
def update_song(song_id):

    # get data from the json body
    updated_song = request.get_json()
    song = db.songs.find_one({"id": song_id})
    if song == None:
        return {"message": "song not found"}, 404
    updated_data = {"$set": updated_song}
    result = db.songs.update_one({"id": song_id}, updated_data)
    if result.modified_count == 0:
        return {"message": "song found, but nothing updated"}, 200
    else:
        return parse_json(db.songs.find_one({"id": song_id})), 201


@app.route('/song/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    result = db.songs.delete_one({"id": song_id})
    if result.deleted_count == 0:
        return {"message": "song not found"}, 404
    else:
        return "Successfully Deleted", 204