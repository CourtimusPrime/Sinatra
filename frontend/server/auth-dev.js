import 'dotenv/config';
import express from 'express';
import { ExpressAuth } from '@auth/express';
import { authConfig } from '../lib/auth-config.js';

const app = express();
app.set('trust proxy', true);
app.use('/api/auth/*', ExpressAuth(authConfig));

const port = process.env.AUTH_PORT || 3001;
app.listen(port, () => {
  console.log(`Auth server running on http://localhost:${port}`);
});
