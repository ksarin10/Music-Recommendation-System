import React from 'react';
import { Link } from 'react-router-dom';

function YourSongs({ likedSongs }) {
    return (
        <div 
            className="max-w-lg w-full p-6 rounded-lg shadow-lg"
            style={{
                backgroundColor: "rgba(30, 41, 59, 0.8)", // Dark slate color with 80% opacity
            }}
        >
            <h1 className="text-3xl font-bold mb-6 text-center">Your Songs</h1>
            <div>
                <h2 className="text-xl font-bold mb-4 text-center">Liked Songs:</h2>
                <ul>
                    {likedSongs.map((song, index) => (
                        <li key={index} className="p-3 border rounded mb-2 bg-gray-900">
                            {song.title} by {song.artist}
                        </li>
                    ))}
                </ul>
                <Link
                    to="/"
                    className="bg-blue-600 text-white p-3 rounded w-full text-center hover:bg-blue-700 transition block mt-4"
                >
                    Back to Recommendations
                </Link>
            </div>
        </div>
    );
}

export default YourSongs;