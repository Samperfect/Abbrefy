from flask import Blueprint, render_template, session, redirect, request, jsonify, url_for, flash
from abbrefy.links.models import Link
from abbrefy.users.models import User
from datetime import datetime
from validators.url import url
from abbrefy.links.tools import check_duplicate, get_title
from abbrefy.users.tools import api_key_required, api_key_con_required
import os
import requests
# attaching the links blueprint
linksApi = Blueprint('linksApi', __name__)


# public API route for abbrefying links
@linksApi.route('/api/v1/url/abbrefy/', methods=['POST'])
@api_key_con_required
def publicAbbrefy(user):

    try:
        # getting the request data
        data = request.get_json()
        # validating the data was sent
        if not data:
            return jsonify({"status": False, "error": "DATA_ERROR"}), 400
        # validating that data sent is a URL
        if not url(data['url']):
            return jsonify({"status": False, "error": "URL_ERROR"}), 400
        # validating that URL isn't already abbrefied
        slug = check_duplicate(data['url'])
        if slug and Link.check_slug(slug):
            return jsonify({"status": False, "error": "DUPLICATE_ERROR"}), 400
        # creating the URL object and abbrefying it
        author = user
        new_link = Link(url=data['url'],
                        author=author)
        response = new_link.abbrefy()
        return jsonify(response)

    except KeyError:
        return jsonify({"status": False, "error": "DATA_ERROR"}), 400


# the link update route
@linksApi.route('/api/v1/url/update/', methods=['PUT'])
@api_key_required
def update(user):
    data = request.get_json()
    # validating the data was sent
    if not data:
        return jsonify({"status": False, "error": "DATA_ERROR"}), 400
    # validating that URL isn't already abbrefied
    try:
        # checking if the link exists on abbrefy
        if not Link.check_slug(data['idSlug']):
            return jsonify({"status": False, "error": "EXISTENCE_ERROR"}), 404

        if "slug" in data:
            if data['slug'] and Link.check_slug(data['slug']):
                return jsonify({"status": False, "error": "USAGE_ERROR"}), 400

        link = Link().get_link(data['idSlug'])
        author = user
        if link['author'] != author:
            return jsonify({"status": False, "error": "AUTHORIZATION_ERROR"}), 401

         # updating the Link object and saving to the database
        update_data = {}
        for key in data:
            if key == "idSlug":
                continue
            update_data[key] = data[key]
            link[key] = data[key]
        filter = {"slug": data['idSlug']}
        update = {"$set": update_data}
        # print(update_data)

        response = Link.update_link(filter, link, update)
        if response['status'] == False:
            return jsonify({"status": False, "error": "UNKNOWN_ERROR"})
        return jsonify({"status": True, "message": "UPDATE_SUCCESS", "data": response}), 201

    except KeyError:
        return jsonify({"status": False, "error": "DATA_ERROR"}), 400

    except:
        return jsonify({"status": False, "error": "UNKNOWN_ERROR"}), 400


# public API route for deleting links
@linksApi.route('/api/v1/url/delete/', methods=['DELETE'])
@api_key_required
def publicDelete(user):
    data = request.get_json()
    # validating the data was sent
    if not data:
        return jsonify({"status": False, "error": "DATA_ERROR"}), 400
    # validating that URL isn't already abbrefied
    try:
        # checking if the link exists on abbrefy
        if not Link.check_slug(data['idSlug']):
            return jsonify({"status": False, "error": "EXISTENCE_ERROR"}), 404

        # retrieving the link from the DB
        link = Link().get_link(data['idSlug'])
        author = user

        if link['author'] != author:
            return jsonify({"status": False, "error": "AUTHORIZATION_ERROR"}), 401

        response = Link.delete(link)
        if response['status'] == False:
            return jsonify({"status": False, "error": "UNKNOWN_ERROR"}), 400

        return jsonify({"status": True, "message": "DELETE_SUCCESS", "data": response}), 200

    except KeyError:
        return jsonify({"status": False, "error": "DATA_ERROR"}), 400

    except:
        return jsonify({"status": False, "error": "UNKNOWN_ERROR"}), 400
