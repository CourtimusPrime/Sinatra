// src/pages/Auth.jsx
// Legacy route — Auth.js handles callbacks server-side now.
// This page just redirects in case of stale bookmarks/links.
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function Auth() {
  const navigate = useNavigate();
  useEffect(() => {
    navigate('/home', { replace: true });
  }, [navigate]);
  return null;
}

export default Auth;
