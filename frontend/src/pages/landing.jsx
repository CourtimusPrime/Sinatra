// src/pages/Landing.jsx
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import Spotify from '../assets/spotify.svg';
import Loader from '../components/Loader';
import { signIn } from '../lib/auth-client';

function Landing() {
  const navigate = useNavigate();
  const { user, loading } = useUser();

  useEffect(() => {
    if (!loading && user) {
      navigate('/home');
    }
  }, [loading, user, navigate]);

  if (loading) {
    return <Loader />;
  }

  const handleLogin = () => {
    signIn('spotify', { callbackUrl: '/home' });
  };

  return (
    <div className="min-h-screen bg-white dark:bg-black text-black dark:text-white flex items-center justify-center">
      <div className="text-center max-w-xl w-full px-4">
        <h1 className="text-6xl font-duckie bg-gradient-to-r from-pink-500 via-cyan-400 to-purple-400 bg-clip-text text-transparent animate-gradient mb-4">
          Sinatra
        </h1>
        <p className="text-xl font-light mb-6">
          A public page for your music taste.
        </p>

        <div className="flex justify-center">
          <button
            onClick={handleLogin}
            className="flex items-center gap-2 px-6 py-3 rounded-full bg-green-600 hover:bg-green-700 text-white text-lg shadow-md transition"
          >
            <img src={Spotify} alt="Spotify logo" className="w-5 h-5" />
            Login with Spotify
          </button>
        </div>
      </div>
    </div>
  );
}

export default Landing;
