// src/pages/public.jsx
import React, { useEffect, useState, lazy, Suspense } from 'react';
import { useParams } from 'react-router-dom';
import RecentlyPlayedCard from '../components/RecentlyPlayedCard';
import PlaylistCardMini from '../components/PlaylistCardMini';
import { normalizePlaylist } from '../utils/normalize';
import { apiGet } from '../utils/api';
import Loader from '../components/Loader';
import { motion } from '@motionone/react';
import { Share } from 'lucide-react';
import Spotify from '../assets/spotify.svg';
import UserHeader from '../components/UserHeader';
import { signIn } from '../lib/auth-client';

// Lazy-loaded components
const MusicTaste = lazy(() => import('../components/music/MusicTaste'));
const AllPlaylistsModal = lazy(() => import('../components/AllPlaylistsModal'));

export default function PublicProfile() {
  const { user_id } = useParams();
  const [profile, setProfile] = useState(() => {
    try {
      const cached = localStorage.getItem(`publicProfile:${user_id}`);
      return cached ? JSON.parse(cached) : null;
    } catch {
      return null;
    }
  });
  const [showCTA, setShowCTA] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isAllModalOpen, setAllModalOpen] = useState(false);

  const handleLogin = () => {
    signIn('spotify', { callbackUrl: '/home' });
  };

  useEffect(() => {
    const cached = localStorage.getItem(`publicProfile:${user_id}`);
    if (cached) {
      try {
        setProfile(JSON.parse(cached));
      } catch {
        /* ignore parse errors */
      }
    }

    async function load() {
      try {
        const userData = await apiGet(`/public-profile/${user_id}`);

        const parsed = {
          ...userData,
          last_played_track: userData.last_played || null,
          profile_image_url: userData.profile_picture,
          featured_playlists: Array.isArray(userData.playlists?.featured)
            ? userData.playlists.featured.map(normalizePlaylist)
            : [],
          all_playlists: Array.isArray(userData.playlists?.all)
            ? userData.playlists.all.map(normalizePlaylist)
            : [],
          genres_data: userData.genres || {},
        };

        setProfile(parsed);
        localStorage.setItem(
          `publicProfile:${user_id}`,
          JSON.stringify(parsed)
        );

        setTimeout(() => setShowCTA(true), 1500);
      } catch (err) {
        console.error('❌ Failed to load public profile:', err);
      }
    }

    load();
  }, [user_id]);

  if (!profile) return <Loader />;

  const {
    display_name,
    profile_picture,
    genres_data,
    last_played_track,
    featured_playlists,
    all_playlists,
  } = profile;

  const lastUpdated = last_played_track?.played_at
    ? new Date(last_played_track.played_at)
    : null;

  return (
    <div className="max-w-md w-full mx-auto p-4">
      <div className="flex justify-end mb-2">
        <button
          onClick={() => {
            const profileUrl = `https://sinatra.live/u/${user_id}`;
            navigator.clipboard.writeText(profileUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
          }}
          aria-label="Copy profile link"
          className="text-black dark:text-white hover:opacity-60 transition"
        >
          {copied ? (
            <span className="text-xs font-semibold">✅</span>
          ) : (
            <Share className="w-5 h-5" />
          )}
        </button>
      </div>

      <UserHeader userState={profile} genresData={genres_data} />

      {last_played_track ? (
        <RecentlyPlayedCard
          track={last_played_track?.track || last_played_track}
          lastUpdated={lastUpdated}
          isRefreshing={false}
          animateTrackChange={false}
          onRefresh={null}
        />
      ) : (
        <div className="text-center text-sm text-gray-500">
          No recent track data available.
        </div>
      )}

      <Suspense
        fallback={
          <div className="text-center text-sm text-gray-400">
            Loading music taste...
          </div>
        }
      >
        <div className="mt-3">
          <MusicTaste
            key={user_id + '_taste'}
            genresData={genres_data}
            userId={user_id}
          />
        </div>
      </Suspense>

      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          hidden: {},
          visible: { transition: { staggerChildren: 0.08 } },
        }}
        className="bg-white dark:bg-gray-900 rounded-2xl shadow p-4 mt-3"
      >
        <div className="flex justify-between items-center mb-2">
          <div className="font-semibold text-lg flex items-center gap-1">
            <span>🌟</span> Featured Playlists
          </div>
          <button
            aria-label="Open all user's playlists"
            onClick={() => setAllModalOpen(true)}
            className="underline text-sm text-blue-600 dark:text-blue-400"
          >
            See All →
          </button>
        </div>

        <div className="flex flex-col gap-3">
          {Array.isArray(featured_playlists) &&
          featured_playlists.length > 0 ? (
            featured_playlists.map((playlist, i) => {
              const isValid =
                playlist &&
                typeof playlist === 'object' &&
                typeof playlist.name === 'string' &&
                typeof playlist.tracks === 'number';

              if (!isValid) {
                console.warn(`❌ Invalid playlist at index ${i}:`, playlist);
                return (
                  <div key={playlist?.id || i} className="text-red-500 text-sm">
                    ⚠️ Skipped invalid playlist
                  </div>
                );
              }

              return (
                <PlaylistCardMini
                  key={playlist.id || i}
                  playlist={playlist}
                  index={i}
                  showTracks
                />
              );
            })
          ) : (
            <div className="text-gray-500 text-sm text-center">
              No featured playlists found.
            </div>
          )}
        </div>
      </motion.div>

      <div className="fixed bottom-0 left-0 w-full sm:hidden z-50 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-4 shadow-md">
        <button
          onClick={handleLogin}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-full bg-green-600 hover:bg-green-700 text-white text-base font-medium transition"
        >
          <img src={Spotify} alt="Spotify logo" className="w-5 h-5" />
          Create Your Own →
        </button>
      </div>
      <div className="h-20 sm:hidden" />
      <Suspense fallback={null}>
        {isAllModalOpen && (
          <AllPlaylistsModal
            isOpen={isAllModalOpen}
            onClose={() => setAllModalOpen(false)}
            playlists={all_playlists}
            user_id={user_id}
            user={profile}
          />
        )}
      </Suspense>
    </div>
  );
}
