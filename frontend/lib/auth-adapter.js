import pg from 'pg';

const isLocal =
  process.env.DATABASE_URL?.includes('localhost') ||
  process.env.DATABASE_URL?.includes('127.0.0.1');

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
  max: 5,
  ...(isLocal ? {} : { ssl: { rejectUnauthorized: false } }),
});

function mapUser(row) {
  return {
    id: String(row.user_id),
    name: row.display_name,
    image: row.profile_image_url,
    spotifyId: row.spotify_id,
    registered: row.registered,
  };
}

export async function upsertTokens(
  userId,
  accessToken,
  refreshToken,
  expiresAt
) {
  await pool.query(
    `INSERT INTO users.tokens (user_id, access_token, refresh_token, expires_at)
     VALUES ($1, $2, $3, to_timestamp($4))
     ON CONFLICT (user_id) DO UPDATE SET
       access_token = EXCLUDED.access_token,
       refresh_token = EXCLUDED.refresh_token,
       expires_at = EXCLUDED.expires_at`,
    [userId, accessToken, refreshToken, expiresAt]
  );
}

export function SinatraAdapter() {
  return {
    async createUser({ name, image, spotifyId }) {
      const { rows } = await pool.query(
        `INSERT INTO users.profiles (spotify_id, display_name, profile_image_url)
         VALUES ($1, $2, $3)
         RETURNING user_id, spotify_id, display_name, profile_image_url, registered`,
        [spotifyId, name || '', image || null]
      );
      return mapUser(rows[0]);
    },

    async getUser(id) {
      const { rows } = await pool.query(
        `SELECT user_id, spotify_id, display_name, profile_image_url, registered
         FROM users.profiles WHERE user_id = $1`,
        [id]
      );
      return rows[0] ? mapUser(rows[0]) : null;
    },

    async getUserByEmail() {
      return null;
    },

    async getUserByAccount({ providerAccountId }) {
      const { rows } = await pool.query(
        `SELECT user_id, spotify_id, display_name, profile_image_url, registered
         FROM users.profiles WHERE spotify_id = $1`,
        [providerAccountId]
      );
      return rows[0] ? mapUser(rows[0]) : null;
    },

    async updateUser({ id, name, image }) {
      const { rows } = await pool.query(
        `UPDATE users.profiles
         SET display_name = COALESCE($2, display_name),
             profile_image_url = COALESCE($3, profile_image_url)
         WHERE user_id = $1
         RETURNING user_id, spotify_id, display_name, profile_image_url, registered`,
        [id, name, image]
      );
      return mapUser(rows[0]);
    },

    async deleteUser(id) {
      await pool.query('DELETE FROM users.tokens WHERE user_id = $1', [id]);
      await pool.query('DELETE FROM users.profiles WHERE user_id = $1', [id]);
    },

    async linkAccount(account) {
      await upsertTokens(
        account.userId,
        account.access_token,
        account.refresh_token,
        account.expires_at
      );
    },

    async unlinkAccount({ providerAccountId }) {
      const { rows } = await pool.query(
        'SELECT user_id FROM users.profiles WHERE spotify_id = $1',
        [providerAccountId]
      );
      if (rows[0]) {
        await pool.query('DELETE FROM users.tokens WHERE user_id = $1', [
          rows[0].user_id,
        ]);
      }
    },
  };
}
