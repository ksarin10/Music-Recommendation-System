import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os


app = Flask(__name__)
# CORS setup
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
app.config['WTF_CSRF_ENABLED'] = False


client_id = '1e6eafb930cd48d69beb4e52dd4e2e4c'
client_secret = '32e469512632402894016e53345c1757'
auth_manager = SpotifyClientCredentials(
    client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)


file_path = '/Users/krishsarin/Downloads/Developer/song_database3.csv'
df = pd.read_csv(file_path)
recommended_songs = []


if not os.path.exists(file_path):
    df = pd.DataFrame(columns=[
        'id', 'title', 'artist', 'genres',
        'acousticness', 'danceability', 'energy',
        'instrumentalness', 'liveness', 'loudness',
        'speechiness', 'valence', 'tempo', 'uri'
    ])
    df.to_csv(file_path, index=False)
else:
    df = pd.read_csv(file_path)

features = ['acousticness', 'danceability', 'energy', 'instrumentalness',
            'liveness', 'loudness', 'speechiness', 'valence', 'tempo']

scaler = StandardScaler()
df[features] = scaler.fit_transform(df[features])


def fetch_song_features(song_name):
    try:
        results = sp.search(q=song_name, type='track', limit=1)
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            features_data = sp.audio_features(track['id'])[0]
            artist_info = sp.artist(track['artists'][0]['id'])
            song_data = {
                'id': track['id'],
                'title': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'genres': ', '.join(artist_info['genres']) if artist_info['genres'] else 'unknown',
                'acousticness': features_data['acousticness'],
                'danceability': features_data['danceability'],
                'energy': features_data['energy'],
                'instrumentalness': features_data['instrumentalness'],
                'liveness': features_data['liveness'],
                'loudness': features_data['loudness'],
                'speechiness': features_data['speechiness'],
                'valence': features_data['valence'],
                'tempo': features_data['tempo'],
                'uri': track['uri'],
                # Generate the embed link instead of fetching preview_url
                'embed_link': f"https://open.spotify.com/embed/track/{track['id']}?utm_source=generator"
            }

            return song_data
    except Exception as e:
        print(f"Error fetching features for '{song_name}': {e}")
    return None


def add_song_to_database(song_data, df, file_path):
    new_song_df = pd.DataFrame([song_data])
    new_song_df[features] = scaler.transform(new_song_df[features])
    df = pd.concat([df, new_song_df], ignore_index=True)
    df.to_csv(file_path, index=False)
    print(
        f"Song '{song_data['title']}' by {song_data['artist']} added to the database.")
    return df


def update_feature_weights(song_features, feedback, feature_weights):
    print(f"Song features before update: {song_features.to_dict()}")

    for feature in features:
        if feature in song_features:
            if feedback == "yes":
                feature_weights[feature] += song_features[feature]
            elif feedback == "no":
                feature_weights[feature] -= song_features[feature]
        else:
            print(
                f"Warning: Feature '{feature}' is missing from song_features.")

    total_weight = sum(abs(weight) for weight in feature_weights.values())
    if total_weight > 0:
        for feature in features:
            feature_weights[feature] /= total_weight


def weighted_knn_distances(song_features, feature_weights):
    weighted_features = np.array(
        [feature_weights[feature] * song_features[feature] for feature in features])
    return weighted_features


def update_recommendations(user_feedback, song_uri, liked_songs, disliked_songs, df, feature_weights):
    global recommended_songs  # Use a global list to track recommendations for the session

    song_index = df.index[df['uri'] == song_uri].tolist()
    if not song_index:
        print("Song URI not found in the database.")
        return None
    song_index = song_index[0]
    song_features = df.loc[song_index, features]

    missing_features = set(features) - set(song_features.index)
    if missing_features:
        print(f"Missing features in song_features: {missing_features}")
        print(f"Full song_features: {song_features.to_dict()}")
        return None

    update_feature_weights(song_features, user_feedback, feature_weights)

    if user_feedback.lower() == "yes":
        liked_songs.append(song_uri)
    elif user_feedback.lower() == "no":
        disliked_songs.append(song_uri)

    attempts = 0
    next_recommendation = None

    # Track songs already recommended in the current session
    session_recommended_songs = set(recommended_songs)

    while attempts < 5:
        next_recommendation_list = get_weighted_recommendations(
            df, liked_songs, disliked_songs, feature_weights, n_recommendations=1, exclude_uris=list(session_recommended_songs)
        )

        if next_recommendation_list:
            next_recommendation = next_recommendation_list[0]
            # Check if the song has already been recommended in the session
            if next_recommendation['uri'] != song_uri and next_recommendation['uri'] not in session_recommended_songs:
                session_recommended_songs.add(next_recommendation['uri'])
                # Add it to global tracking list
                recommended_songs.append(next_recommendation['uri'])
                break
        attempts += 1

    if next_recommendation:
        embed_link = f"https://open.spotify.com/embed/track/{next_recommendation['uri'].split(':')[-1]}?utm_source=generator"
        next_recommendation['embed_link'] = embed_link

        print(f"Generated embed link: {embed_link}")

    return next_recommendation if next_recommendation else None


def get_weighted_recommendations(df, liked_songs, disliked_songs, feature_weights, n_recommendations=5, exclude_uris=[]):
    weighted_songs = df[features].apply(
        lambda x: weighted_knn_distances(x, feature_weights), axis=1)

    knn = NearestNeighbors(
        n_neighbors=n_recommendations + 1, algorithm='ball_tree')
    knn.fit(np.vstack(weighted_songs.values))

    recommendations = []

    for song_uri in liked_songs:
        song_index_list = df.index[df['uri'] == song_uri].tolist()
        if not song_index_list:
            continue
        song_index = song_index_list[0]
        song_features = weighted_knn_distances(
            df.loc[song_index, features], feature_weights).reshape(1, -1)
        distances, indices = knn.kneighbors(song_features)

        for idx in indices[0]:
            recommended_song = {
                'uri': df.iloc[idx]['uri'],
                'title': df.iloc[idx]['title'],
                'artist': df.iloc[idx]['artist'],
                'embed_link': f"https://open.spotify.com/embed/track/{df.iloc[idx]['uri'].split(':')[-1]}?utm_source=generator"
            }
            if recommended_song['uri'] != song_uri and recommended_song['uri'] not in [rec['uri'] for rec in recommendations]:
                recommendations.append(recommended_song)
                print(f"Added recommendation: {recommended_song}")
            if len(recommendations) >= n_recommendations:
                break

        if len(recommendations) >= n_recommendations:
            break

    liked_uris = [uri for uri in liked_songs]
    disliked_uris = [uri for uri in disliked_songs]

    if len(recommendations) < n_recommendations:
        remaining = n_recommendations - len(recommendations)
        potential_songs = df[~df['uri'].isin(
            liked_uris + disliked_uris + [rec['uri'] for rec in recommendations] + exclude_uris)]
        random_recs = potential_songs.sample(n=remaining)
        for _, row in random_recs.iterrows():
            rec = {
                'uri': row['uri'],
                'title': row['title'],
                'artist': row['artist'],
                'embed_link': f"https://open.spotify.com/embed/track/{row['uri'].split(':')[-1]}?utm_source=generator"
            }
            print(f"Random recommendation added: {rec}")

            recommendations.append(rec)

    return recommendations[:n_recommendations]


@app.route('/feedback', methods=['OPTIONS', 'POST'])
def feedback():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'Options request'}), 200

    data = request.json
    song_uri = data.get('song_uri')
    feedback = data.get('feedback')
    liked_songs = data.get('liked_songs', [])
    disliked_songs = data.get('disliked_songs', [])

    feature_weights = data.get('feature_weights', {})
    feature_weights = {feature: feature_weights.get(
        feature, 1.0) for feature in features}

    print(f"Feature weights before update: {feature_weights}")

    next_recommendation = update_recommendations(
        feedback, song_uri, liked_songs, disliked_songs, df, feature_weights)

    if next_recommendation:
        print(f"Next recommendation to be sent: {next_recommendation}")

    return jsonify({'message': 'Feedback received', 'next_recommendation': next_recommendation, 'feature_weights': feature_weights})


@app.route('/recommendations', methods=['POST'])
def recommendations():
    global df
    try:
        data = request.json
        favorite_songs = data.get('favorite_songs', [])
        liked_songs = data.get('liked_songs', [])
        disliked_songs = data.get('disliked_songs', [])
        feature_weights = data.get(
            'feature_weights', {feature: 1.0 for feature in features})

        new_songs = []
        for song_name in favorite_songs:
            if df[df['title'].str.strip().str.lower() == song_name.strip().lower()].empty:
                song_data = fetch_song_features(song_name)
                if song_data:
                    df = add_song_to_database(song_data, df, file_path)
                    new_songs.append(song_data)
            else:
                print(f"'{song_name}' is already in the database.")

        recommendations = get_weighted_recommendations(
            df, liked_songs, disliked_songs, feature_weights, n_recommendations=1)

        if recommendations:
            recommended_song = recommendations[0]
            recommended_song[
                'embed_link'] = f"https://open.spotify.com/embed/track/{recommended_song['uri'].split(':')[-1]}"
        else:
            recommended_song = None

        return jsonify({'recommendations': [recommended_song] if recommended_song else [], 'new_songs': new_songs})

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/')
def home():
    return "Music Recommendation API is running!"


if __name__ == '__main__':
    app.run(debug=True)
