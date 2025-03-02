from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json

# Load API credentials
load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

app = Flask(__name__)

def get_token():
    """Retrieve Spotify API access token."""
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = { 
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = result.json()
    return json_result["access_token"]

def get_auth_header(token):
    """Generate headers for Spotify API requests."""
    return {"Authorization": f"Bearer {token}"}

@app.route("/search", methods=["GET"])
def search_artist():
    """Search for an artist on Spotify and return their top 5 songs."""
    artist_name = request.args.get("artist")
    if not artist_name:
        return jsonify({"error": "Missing artist name"}), 400

    token = get_token()

    # Search for the artist
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query_url = f"{url}?q={artist_name}&type=artist&limit=1"
    
    result = get(query_url, headers=headers)
    artists = result.json().get("artists", {}).get("items", [])
    
    if not artists:
        return jsonify({"error": "Artist not found"}), 404
    
    artist = artists[0]
    artist_id = artist["id"]

    # Get top tracks
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    result = get(url, headers=headers)
    tracks = result.json().get("tracks", [])[:5]  # Get only top 5 songs

    # Format response
    songs = [{"name": track["name"], "url": track["external_urls"]["spotify"]} for track in tracks]
    
    return jsonify({"artist": artist["name"], "songs": songs})

if __name__ == "__main__":
    app.run(debug=True)