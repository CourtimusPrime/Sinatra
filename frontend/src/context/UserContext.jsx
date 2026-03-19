// src/context/UserContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { apiGet } from '../utils/api';
import { getSession } from '../lib/auth-client';

const UserContext = createContext();

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  async function login() {
    try {
      const authSession = await getSession();
      if (!authSession) {
        setLoading(false);
        return;
      }

      // Set cookie for backward compatibility with Python backend
      document.cookie = `sinatra_user_id=${authSession.user.id}; path=/; max-age=2592000; SameSite=Lax`;

      // Fetch full user data from backend
      const session = await apiGet('/session');
      setUser(session);
    } catch (err) {
      console.error('Login failed:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Public page — no need to fetch session
    if (location.pathname.startsWith('/u/')) {
      setLoading(false);
    } else {
      login();
    }
  }, [location.pathname]);

  const user_id = user?.user_id;
  const importantPlaylists = user?.important_playlists || [];

  return (
    <UserContext.Provider
      value={{
        user,
        setUser,
        login,
        user_id,
        loading,
        importantPlaylists,
      }}
    >
      {children}
    </UserContext.Provider>
  );
}

export const useUser = () => useContext(UserContext);
