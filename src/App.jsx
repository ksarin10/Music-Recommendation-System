import React, { useState } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import YourSongs from './components/YourSongs';

function App() {
    const [favoriteSongs, setFavoriteSongs] = useState('');
    const [recommendation, setRecommendation] = useState(null);
    const [likedSongs, setLikedSongs] = useState([]);
    const [featureWeights, setFeatureWeights] = useState({});
    const [stopRecommendations, setStopRecommendations] = useState(false);

    const handleSubmit = async () => {
        try {
            const weights = {
                acousticness: 1.0,
                danceability: 1.0,
                energy: 1.0,
                instrumentalness: 1.0,
                liveness: 1.0,
                loudness: 1.0,
                speechiness: 1.0,
                valence: 1.0,
                tempo: 1.0,
                ...featureWeights,
            };

            const response = await axios.post('http://127.0.0.1:5000/recommendations', {
                favorite_songs: favoriteSongs.split(',').map((song) => song.trim()),
                liked_songs: likedSongs.map(song => song.uri),
                feature_weights: weights,
            });

            if (!stopRecommendations) {
                setRecommendation(response.data.recommendations[0]);
            }
            setFavoriteSongs('');
        } catch (error) {
            console.error('Error fetching recommendations:', error);
            alert('An error occurred while fetching recommendations. Please try again later.');
        }
    };

    const handleStopRecommendations = () => {
        setStopRecommendations(true);
        setRecommendation(null);
    };

    const handleFeedback = async (songUri, feedback) => {
        try {
            const response = await axios.post('http://127.0.0.1:5000/feedback', {
                song_uri: songUri,
                feedback: feedback,
                liked_songs: likedSongs.map(song => song.uri),
                feature_weights: featureWeights,
            });

            setFeatureWeights(response.data.feature_weights);
            if (feedback === 'yes' && recommendation) {
                setLikedSongs([...likedSongs, recommendation]);
            }

            if (!stopRecommendations && response.data.next_recommendation) {
                setRecommendation(response.data.next_recommendation);
            } else {
                setRecommendation(null);
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            alert('An error occurred while submitting your feedback. Please try again later.');
        }
    };

    return (
        <Router>
            <div 
                className="min-h-screen flex flex-col items-center justify-center text-white"
                style={{
                    backgroundImage: "url('/image1.png')",
                    backgroundSize: "cover",
                    backgroundRepeat: "no-repeat",
                    backgroundPosition: "center center",
                    height: "100vh",
                }}
            >
                <Routes>
                    <Route 
                        path="/" 
                        element={
                            <div 
                                className="max-w-lg w-full p-6 rounded-lg shadow-lg"
                                style={{
                                    backgroundColor: "rgba(30, 41, 59, 0.7)", 
                                }}
                            >
                                <h1 className="text-3xl font-bold mb-6 text-center">Beats By Krish</h1>

                                <div className="mb-6"      
                                >
                                    <input
                                        style={{
                                            backgroundColor: "rgba(30, 41, 59, 0.7)", 
                                        }}
                                        type="text"
                                        className="border p-3 rounded w-full bg-gray-900 text-white placeholder-gray-400"
                                        placeholder="Enter your favorite songs, separated by commas..."
                                        value={favoriteSongs}
                                        onChange={(e) => setFavoriteSongs(e.target.value)}
                                    />
                                    <button
                                        className="bg-violet-600 text-white p-3 rounded mt-4 w-full hover:bg-violet-700 transition"
                                        onClick={handleSubmit}
                                    >
                                        Get Recommendations
                                    </button>
                                </div>

                                {recommendation && (
                                    <div className="mb-6">
                                        <h2 className="text-xl font-bold mb-4 text-center">Recommendation:</h2>
                                        <div className="p-4 mb-4 border rounded bg-gray-900"
                                            style={{
                                                backgroundColor: "rgba(30, 41, 59, 0.7)", 
                                            }}
                                        >
                                            <p className="text-lg mb-2">{recommendation.title} by {recommendation.artist}</p>
                                            <iframe
                                                src={recommendation.embed_link}
                                                width="100%"
                                                height="300"
                                                frameBorder="0"
                                                allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                                                className="rounded"
                                            ></iframe>
                                            <div className="flex justify-between mt-4">
                                                <button
                                                    className="bg-green-500 text-white p-2 rounded hover:bg-green-600 transition"
                                                    onClick={() => handleFeedback(recommendation.uri, 'yes')}
                                                >
                                                    Like
                                                </button>
                                                <button
                                                    className="bg-red-500 text-white p-2 rounded hover:bg-red-600 transition"
                                                    onClick={() => handleFeedback(recommendation.uri, 'no')}
                                                >
                                                    Dislike
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <div className="flex justify-between">
                                    <button
                                        className="bg-rose-900 text-white p-3 rounded w-full mr-2 hover:bg-rose-800 transition"
                                        onClick={handleStopRecommendations}
                                    >
                                        Stop Recommendations
                                    </button>
                                    <Link
                                        to="/your-songs"
                                        className="bg-blue-600 text-white p-3 rounded w-full hover:bg-blue-700 transition text-center"
                                    >
                                        Your Songs
                                    </Link>
                                </div>
                            </div>
                        }
                    />
                    <Route path="/your-songs" element={<YourSongs likedSongs={likedSongs} />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
