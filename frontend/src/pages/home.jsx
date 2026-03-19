// src/pages/home.jsx
import React, { useEffect, useState, lazy, Suspense, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { apiGet, apiDelete, apiPost } from '../utils/api';
import { Menu, Share } from 'lucide-react';
import { motion } from '@motionone/react';
import { signOut } from '../lib/auth-client';

import UserHeader from '../components/UserHeader';
import RecentlyPlayedCard from '../components/RecentlyPlayedCard';
import FeaturedPlaylists from '../components/FeaturedPlaylists';
import '../styles/loader.css';

const MusicTaste = lazy(() => import('../components/music/MusicTaste'));
const SettingsModal = lazy(
  () => import('../components/settings/SettingsModal')
);
const AllPlaylistsModal = lazy(() => import('../components/AllPlaylistsModal'));

function Home() {
  const navigate = useNavigate();
  const { user, loading, setUser } = useUser();

  const [track, setTrack] = useState(user?.last_played || null);
  const [lastUpdated, setLastUpdated] = useState(() => {
    const localTime = localStorage.getItem('last_played_updated_at');
    return localTime
      ? new Date(localTime)
      : user?.last_played?.timestamp
        ? new Date(user.last_played.timestamp)
        : null;
  });
  const [genresData, setGenresData] = useState(null);
  const [copied, setCopied] = useState(false);

  const [isAllModalOpen, setAllModalOpen] = useState(false);
  const [isSettingsOpen, setSettingsOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [animateTrackChange, setAnimateTrackChange] = useState(false);

  const featuredPlaylists = useMemo(
    () => (user?.playlists?.featured || []).slice(0, 3),
    [user?.playlists?.featured]
  );

  useEffect(() => {
    loadNowPlaying();
  }, []);

  useEffect(() => {
    if (loading) return;

    if (!user) {
      navigate('/');
      return;
    }

    if (user.registered === false) {
      navigate('/onboard');
      return;
    }

    setGenresData(user.genres);
  }, [loading, user]);

  useEffect(() => {
    if (user?.last_played) {
      setTrack(user.last_played);
      const ts = user.last_played.timestamp;
      setLastUpdated(ts ? new Date(ts) : new Date());
    }
  }, [user?.last_played]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        loadNowPlaying();
      }
    }, 20000); // 20 seconds

    return () => clearInterval(interval);
  }, [user]);

  async function loadNowPlaying() {
    setIsRefreshing(true);
    try {
      // First try live playback
      const playbackRes = await apiPost(`/update-playing`);
      let latestTrack = playbackRes.track;

      if (!latestTrack) {
        // Nothing playing? Fallback to recently played
        const recentRes = await apiGet(`/recently-played`);
        latestTrack = recentRes.track;
      }

      if (!latestTrack) return;

      const isSame = JSON.stringify(latestTrack) === JSON.stringify(track);
      if (!isSame) {
        setAnimateTrackChange(true);
        setTrack(latestTrack);
        setLastUpdated(new Date());
        localStorage.setItem('last_played_track', JSON.stringify(latestTrack));
        localStorage.setItem(
          'last_played_updated_at',
          new Date().toISOString()
        );
        setTimeout(() => setAnimateTrackChange(false), 500);
      }
    } catch (err) {
      console.error('Error during loadNowPlaying():', err);
    } finally {
      setTimeout(() => setIsRefreshing(false), 600);
    }
  }

  function logout() {
    localStorage.clear();
    document.cookie = 'sinatra_user_id=; path=/; max-age=0';
    signOut({ callbackUrl: '/' });
  }

  async function deleteAccount() {
    if (!window.confirm('You sure you wanna delete your account?')) return;
    try {
      await apiDelete(`/delete-user?user_id=${user.user_id}`);
      logout();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  }

  const isReady = user && genresData && !loading;
  if (!isReady) {
    return (
      <div className="loader-container">
        <div className="loader" />
      </div>
    );
  }

  return (
    <div className="max-w-md w-full mx-auto p-4 space-y-4">
      {/* 🔗 Share + ⚙️ Settings */}
      <motion.div
        className="flex justify-between"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        {user?.user_id && (
          <button
            onClick={() => {
              navigator.clipboard.writeText(
                `https://sinatra.live/u/${user.user_id}`
              );
              setCopied(true);
              setTimeout(() => setCopied(false), 1500);
            }}
          >
            {copied ? (
              <span className="text-xs font-semibold">✅</span>
            ) : (
              <Share className="w-5 h-5" />
            )}
          </button>
        )}
        <button onClick={() => setSettingsOpen(true)}>
          <Menu className="w-5 h-5" />
        </button>
      </motion.div>

      {/* 🧑‍🎤 User Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <UserHeader userState={user} genresData={genresData} />
      </motion.div>

      {/* 🎧 Recently Played */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <RecentlyPlayedCard
          track={track}
          lastUpdated={lastUpdated}
          isRefreshing={isRefreshing}
          animateTrackChange={animateTrackChange}
          onRefresh={loadNowPlaying}
        />
      </motion.div>

      {/* 🎼 Music Taste */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Suspense
          fallback={
            <div className="text-center text-sm text-gray-400">
              Loading music taste...
            </div>
          }
        >
          <MusicTaste genresData={genresData} userId={user?.user_id} />
        </Suspense>
      </motion.div>

      {/* 📻 Featured Playlists */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <FeaturedPlaylists
          playlists={featuredPlaylists}
          onSeeAll={() => setAllModalOpen(true)}
        />
      </motion.div>

      {/* ⚙️ Modals */}
      <Suspense fallback={null}>
        {isAllModalOpen && (
          <AllPlaylistsModal
            isOpen
            onClose={() => setAllModalOpen(false)}
            playlists={user?.playlists?.all || []}
            user={user}
          />
        )}
        {isSettingsOpen && (
          <SettingsModal
            isOpen
            onClose={() => setSettingsOpen(false)}
            onLogout={logout}
            onDelete={deleteAccount}
            user={user}
            user_id={user?.user_id}
            setUser={setUser}
            onSave={async () => {
              try {
                const fresh = await apiGet('/dashboard');
                setUser((prev) => ({
                  ...prev,
                  playlists: fresh.playlists,
                  genres: fresh.genres,
                  last_played: fresh.last_played,
                }));
              } catch (err) {
                console.error(
                  'Failed to refresh user after featured update:',
                  err
                );
              }
            }}
          />
        )}
      </Suspense>
    </div>
  );
}

export default Home;
