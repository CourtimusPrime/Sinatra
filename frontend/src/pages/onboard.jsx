// src/pages/onboard.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import OnboardingSteps from '../components/OnboardingSteps';
import { apiGet, apiPost } from '../utils/api';
import { motion } from '@motionone/react';
import '../styles/onboard.css';
import { applyRootThemeVars } from '../utils/theme';
import Loader from '../components/Loader';

function Onboard() {
  const navigate = useNavigate();
  const { user } = useUser(); // ✅ Use context for user_id
  const [searchParams, setSearchParams] = useSearchParams();

  const [spotifyUser, setSpotifyUser] = useState(null);
  const [step, setStep] = useState(0);
  const [canProceed, setCanProceed] = useState(false);
  const [log, setLog] = useState('');
  const [isFinalizing, setIsFinalizing] = useState(false);

  const [onboardData, setOnboardData] = useState({
    display_name: '',
    user_id: '',
    profile_picture: '',
    selected_playlists: [],
    featured_playlists: [],
  });

  // Load user + genre data
  useEffect(() => {
    const init = async () => {
      try {
        const uid = searchParams.get('user_id') || user?.user_id;
        const spotifyRes = await apiGet(`/spotify-me?user_id=${uid}`);
        setSpotifyUser(spotifyRes);
        setOnboardData((prev) => ({
          ...prev,
          user_id: spotifyRes.id || '', // ✅ Inject user_id from context
          display_name: spotifyRes.display_name,
          profile_picture: spotifyRes.images?.[0]?.url || '',
        }));
      } catch (err) {
        setLog('Error during onboarding init.');
        console.error('Onboarding init error:', err);
      }
    };
    init();
  }, [user?.user_id]);

  // Reset canProceed when step changes
  useEffect(() => {
    setCanProceed(false);
  }, [step]);

  // Final step: submit + redirect
  useEffect(() => {
    if (step === 4) {
      setIsFinalizing(true);
      const finalize = async () => {
        try {
          await apiPost('/register', onboardData);
          navigate('/home');
        } catch (err) {
          console.error('Error finalizing account:', err);
          setLog('Finalization error. Try again.');
          setIsFinalizing(false);
        }
      };
      finalize();
    }
  }, [step]);

  const handleNext = () => {
    if (step > 0 && !canProceed) return;
    setStep((prev) => prev + 1);
  };

  const handleBack = () => {
    if (step > 0) setStep((prev) => prev - 1);
  };

  if (isFinalizing) {
    return <Loader />;
  }

  return (
    <div className="onboard-container flex flex-col min-h-screen">
      <div className="sticky-progress z-10" />

      <div className="onboard-content flex-1 overflow-y-auto">
        <motion.div
          key={step}
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <OnboardingSteps
            step={step}
            user={spotifyUser}
            onboardData={onboardData}
            setOnboardData={setOnboardData}
            setCanProceed={setCanProceed}
          />
        </motion.div>
      </div>

      {step < 4 && (
        <div className="onboard-footer sticky bottom-0 bg-white dark:bg-black shadow z-10 p-4 flex justify-between">
          <button
            onClick={handleBack}
            className={`px-6 py-2 rounded-lg text-white font-semibold transition-colors duration-300 ${
              step === 0
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-red-600 hover:bg-red-700'
            }`}
            disabled={step === 0}
          >
            Go Back
          </button>
          <button
            onClick={handleNext}
            className={`px-6 py-2 rounded-lg text-white font-semibold transition-colors duration-300 ${
              step === 0 || canProceed
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-400 cursor-not-allowed'
            }`}
            disabled={step !== 0 && !canProceed}
          >
            {step < 3 ? 'Next' : 'Finish'}
          </button>
        </div>
      )}

      {log && <div className="onboard-log">{log}</div>}
    </div>
  );
}

export default Onboard;
