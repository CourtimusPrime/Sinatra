import Spotify from '@auth/core/providers/spotify';
import { SinatraAdapter, upsertTokens } from './auth-adapter.js';

async function refreshSpotifyToken(token) {
  try {
    const res = await fetch('https://accounts.spotify.com/api/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        refresh_token: token.refreshToken,
        client_id: process.env.SPOTIFY_CLIENT_ID,
        client_secret: process.env.SPOTIFY_CLIENT_SECRET,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Token refresh failed');

    const refreshed = {
      ...token,
      accessToken: data.access_token,
      refreshToken: data.refresh_token ?? token.refreshToken,
      expiresAt: Math.floor(Date.now() / 1000) + data.expires_in,
    };

    await upsertTokens(
      refreshed.userId,
      refreshed.accessToken,
      refreshed.refreshToken,
      refreshed.expiresAt
    );

    return refreshed;
  } catch (err) {
    console.error('Spotify token refresh failed:', err);
    return { ...token, error: 'RefreshTokenError' };
  }
}

export const authConfig = {
  adapter: SinatraAdapter(),
  providers: [
    Spotify({
      clientId: process.env.SPOTIFY_CLIENT_ID,
      clientSecret: process.env.SPOTIFY_CLIENT_SECRET,
      authorization: {
        params: {
          scope: [
            'user-read-private',
            'user-read-email',
            'user-read-recently-played',
            'user-read-playback-state',
            'user-top-read',
            'playlist-read-private',
          ].join(' '),
        },
      },
      profile(profile) {
        return {
          name: profile.display_name,
          email: profile.email,
          image: profile.images?.[1]?.url || profile.images?.[0]?.url,
          spotifyId: profile.id,
        };
      },
    }),
  ],
  session: { strategy: 'jwt' },
  basePath: '/api/auth',
  callbacks: {
    async jwt({ token, user, account }) {
      if (user) {
        token.userId = user.id;
        token.spotifyId = user.spotifyId;
        token.registered = user.registered;
      }

      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.expiresAt = account.expires_at;

        // Persist tokens for returning users (first sign-in handled by linkAccount)
        await upsertTokens(
          token.userId,
          account.access_token,
          account.refresh_token,
          account.expires_at
        );
      }

      // Preemptive refresh 5 minutes before expiry
      if (token.expiresAt && Date.now() / 1000 > token.expiresAt - 300) {
        return refreshSpotifyToken(token);
      }

      return token;
    },

    async session({ session, token }) {
      session.user.id = token.userId;
      session.user.spotifyId = token.spotifyId;
      session.user.registered = token.registered;
      session.accessToken = token.accessToken;
      return session;
    },
  },
  pages: {
    signIn: '/',
  },
  trustHost: true,
};
