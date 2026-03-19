# db/queries.py
"""Data access layer — all PostgreSQL queries for the Sinatra backend.

Every function accepts spotify_id (the Spotify user/playlist/track ID string)
as the external identifier. Internal bigint PKs are resolved within queries.
"""

from __future__ import annotations

from datetime import UTC, datetime

from db.pg import get_conn

# ── Internal helpers ─────────────────────────────────────────


def _user_pk(cur, spotify_id: str) -> int | None:
    cur.execute("SELECT user_id FROM users.profiles WHERE spotify_id = %s", (spotify_id,))
    row = cur.fetchone()
    return row["user_id"] if row else None


def _require_user_pk(cur, spotify_id: str) -> int:
    uid = _user_pk(cur, spotify_id)
    if uid is None:
        raise ValueError(f"User not found: {spotify_id}")
    return uid


# ── Users ────────────────────────────────────────────────────


def get_user(spotify_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT spotify_id, display_name, profile_image_url, theme,
                       registered, created_at
                FROM users.profiles WHERE spotify_id = %s
                """,
                (spotify_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "user_id": row["spotify_id"],
                "display_name": row["display_name"],
                "profile_image_url": row["profile_image_url"],
                "theme": row["theme"],
                "registered": row["registered"],
                "created_at": row["created_at"],
            }


def upsert_user(
    spotify_id: str,
    display_name: str,
    profile_image_url: str | None = None,
    theme: str = "default",
) -> dict:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users.profiles (spotify_id, display_name, profile_image_url, theme)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (spotify_id) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    profile_image_url = EXCLUDED.profile_image_url,
                    theme = EXCLUDED.theme
                RETURNING spotify_id, display_name, profile_image_url, theme
                """,
                (spotify_id, display_name, profile_image_url, theme),
            )
            row = cur.fetchone()
            conn.commit()
    return {
        "user_id": row["spotify_id"],
        "display_name": row["display_name"],
        "profile_image_url": row["profile_image_url"],
        "theme": row["theme"],
    }


def set_user_registered(spotify_id: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users.profiles SET registered = true WHERE spotify_id = %s",
                (spotify_id,),
            )
            conn.commit()


def delete_user(spotify_id: str) -> None:
    """Delete user and all related data (FK cascades handle most of it)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            uid = _user_pk(cur, spotify_id)
            if uid is None:
                return
            # featured_playlists FK references saved_playlists, so delete first
            cur.execute("DELETE FROM users.featured_playlists WHERE user_id = %s", (uid,))
            cur.execute("DELETE FROM users.profiles WHERE user_id = %s", (uid,))
            conn.commit()


# ── Tokens ───────────────────────────────────────────────────


def get_tokens(spotify_id: str) -> dict | None:
    """Returns {access_token, refresh_token, expires_at} where expires_at is an int timestamp."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.access_token, t.refresh_token, t.expires_at
                FROM users.tokens t
                JOIN users.profiles p ON t.user_id = p.user_id
                WHERE p.spotify_id = %s
                """,
                (spotify_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "access_token": row["access_token"],
                "refresh_token": row["refresh_token"],
                "expires_at": int(row["expires_at"].timestamp()),
            }


def upsert_tokens(spotify_id: str, access_token: str, refresh_token: str, expires_at: int) -> None:
    expires_dt = datetime.fromtimestamp(expires_at, tz=UTC)
    with get_conn() as conn:
        with conn.cursor() as cur:
            uid = _require_user_pk(cur, spotify_id)
            cur.execute(
                """
                INSERT INTO users.tokens (user_id, access_token, refresh_token, expires_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at
                """,
                (uid, access_token, refresh_token, expires_dt),
            )
            conn.commit()


# ── Sessions (auth.js) ──────────────────────────────────────


def get_user_by_session(session_token: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.spotify_id, p.display_name, p.profile_image_url, p.theme
                FROM users.sessions s
                JOIN users.profiles p ON s.user_id = p.user_id
                WHERE s.session_token = %s AND s.expires > now()
                """,
                (session_token,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "user_id": row["spotify_id"],
                "display_name": row["display_name"],
                "profile_image_url": row["profile_image_url"],
                "theme": row["theme"],
            }


# ── Playlists ────────────────────────────────────────────────


def add_saved_playlists(user_spotify_id: str, playlists: list[dict]) -> int:
    """Save enriched playlists for a user. Each dict needs: id, name, image, tracks, external_url."""
    count = 0
    with get_conn() as conn:
        with conn.cursor() as cur:
            uid = _require_user_pk(cur, user_spotify_id)
            for pl in playlists:
                cur.execute(
                    """
                    INSERT INTO playlists.details
                        (spotify_id, name, image, track_count, external_url, owner_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (spotify_id) DO UPDATE SET
                        name = EXCLUDED.name, image = EXCLUDED.image,
                        track_count = EXCLUDED.track_count, updated_at = now()
                    RETURNING playlist_id
                    """,
                    (
                        pl["id"],
                        pl["name"],
                        pl.get("image"),
                        pl.get("tracks", 0),
                        pl["external_url"],
                        uid,
                    ),
                )
                pid = cur.fetchone()["playlist_id"]
                cur.execute(
                    """
                    INSERT INTO users.saved_playlists (user_id, playlist_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (uid, pid),
                )
                count += 1
            conn.commit()
    return count


def remove_saved_playlists(user_spotify_id: str, playlist_spotify_ids: list[str]) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            uid = _require_user_pk(cur, user_spotify_id)
            # Remove from featured first (FK constraint)
            cur.execute(
                """
                DELETE FROM users.featured_playlists
                WHERE user_id = %s AND playlist_id IN (
                    SELECT playlist_id FROM playlists.details WHERE spotify_id = ANY(%s)
                )
                """,
                (uid, playlist_spotify_ids),
            )
            cur.execute(
                """
                DELETE FROM users.saved_playlists
                WHERE user_id = %s AND playlist_id IN (
                    SELECT playlist_id FROM playlists.details WHERE spotify_id = ANY(%s)
                )
                """,
                (uid, playlist_spotify_ids),
            )
            count = cur.rowcount
            conn.commit()
    return count


def get_saved_playlists(spotify_id: str) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.spotify_id AS id, d.name, d.image,
                       d.track_count AS tracks, d.external_url
                FROM users.saved_playlists sp
                JOIN playlists.details d ON sp.playlist_id = d.playlist_id
                JOIN users.profiles u ON sp.user_id = u.user_id
                WHERE u.spotify_id = %s
                ORDER BY sp.added_at
                """,
                (spotify_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def get_featured_playlists(spotify_id: str) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.spotify_id AS id, d.name, d.image,
                       d.track_count AS tracks, d.external_url
                FROM users.featured_playlists fp
                JOIN playlists.details d ON fp.playlist_id = d.playlist_id
                JOIN users.profiles u ON fp.user_id = u.user_id
                WHERE u.spotify_id = %s
                ORDER BY fp.position
                """,
                (spotify_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def update_featured_playlists(user_spotify_id: str, playlist_spotify_ids: list[str]) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            uid = _require_user_pk(cur, user_spotify_id)
            cur.execute("DELETE FROM users.featured_playlists WHERE user_id = %s", (uid,))
            count = 0
            for pos, pl_sid in enumerate(playlist_spotify_ids):
                cur.execute(
                    """
                    INSERT INTO users.featured_playlists (user_id, playlist_id, position)
                    SELECT %s, sp.playlist_id, %s
                    FROM users.saved_playlists sp
                    JOIN playlists.details d ON sp.playlist_id = d.playlist_id
                    WHERE sp.user_id = %s AND d.spotify_id = %s
                    """,
                    (uid, pos, uid, pl_sid),
                )
                count += cur.rowcount
            conn.commit()
    return count


def get_synced_playlists(spotify_id: str) -> list[dict]:
    """Get all playlists owned by a user (from admin sync)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.spotify_id AS id, d.name, d.image,
                       d.track_count AS tracks, d.external_url
                FROM playlists.details d
                JOIN users.profiles u ON d.owner_id = u.user_id
                WHERE u.spotify_id = %s
                ORDER BY d.updated_at DESC
                """,
                (spotify_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def sync_user_playlists(user_spotify_id: str, playlists: list[dict]) -> int:
    """Admin sync: upsert all playlists for a user into playlists.details."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            uid = _require_user_pk(cur, user_spotify_id)
            for pl in playlists:
                cur.execute(
                    """
                    INSERT INTO playlists.details
                        (spotify_id, name, image, track_count, external_url, owner_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (spotify_id) DO UPDATE SET
                        name = EXCLUDED.name, image = EXCLUDED.image,
                        track_count = EXCLUDED.track_count,
                        external_url = EXCLUDED.external_url,
                        owner_id = EXCLUDED.owner_id,
                        updated_at = now()
                    """,
                    (
                        pl["id"],
                        pl["name"],
                        pl.get("image"),
                        pl.get("tracks", 0),
                        pl["external_url"],
                        uid,
                    ),
                )
            conn.commit()
    return len(playlists)


# ── Playback ─────────────────────────────────────────────────


def get_last_played(spotify_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.spotify_id AS id, t.name, t.album, t.album_art_url,
                       t.external_url, pb.played_at,
                       ap.name AS artist, ap.spotify_id AS artist_spotify_id
                FROM users.playback pb
                JOIN artists.tracks t ON pb.track_id = t.track_id
                LEFT JOIN artists.track_credits tc
                    ON tc.track_id = t.track_id AND tc.position = 0
                LEFT JOIN artists.profiles ap ON tc.artist_id = ap.artist_id
                JOIN users.profiles u ON pb.user_id = u.user_id
                WHERE u.spotify_id = %s
                """,
                (spotify_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            # Fetch genres for the primary artist
            genres = []
            if row["artist_spotify_id"]:
                cur.execute(
                    """
                    SELECT g.name
                    FROM artists.genre_map gm
                    JOIN artists.genres g ON gm.genre_id = g.genre_id
                    JOIN artists.profiles ap ON gm.artist_id = ap.artist_id
                    WHERE ap.spotify_id = %s
                    """,
                    (row["artist_spotify_id"],),
                )
                genres = [r["name"] for r in cur.fetchall()]

            return {
                "id": row["id"],
                "name": row["name"],
                "artist": row["artist"],
                "album": row["album"],
                "album_art_url": row["album_art_url"],
                "external_url": row["external_url"],
                "genres": genres,
                "timestamp": row["played_at"].isoformat() if row["played_at"] else None,
            }


def upsert_playback(user_spotify_id: str, track_data: dict) -> None:
    """Store a played track. track_data comes from build_track_data()."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            uid = _require_user_pk(cur, user_spotify_id)

            # Upsert track
            cur.execute(
                """
                INSERT INTO artists.tracks
                    (spotify_id, name, album, album_art_url, external_url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (spotify_id) DO UPDATE SET
                    name = EXCLUDED.name, album = EXCLUDED.album,
                    album_art_url = EXCLUDED.album_art_url, updated_at = now()
                RETURNING track_id
                """,
                (
                    track_data["id"],
                    track_data["name"],
                    track_data["album"],
                    track_data.get("album_art_url"),
                    track_data["external_url"],
                ),
            )
            track_id = cur.fetchone()["track_id"]

            # Upsert artist if we have their spotify ID
            if track_data.get("artist_id"):
                cur.execute(
                    """
                    INSERT INTO artists.profiles (spotify_id, name)
                    VALUES (%s, %s)
                    ON CONFLICT (spotify_id) DO UPDATE SET
                        name = EXCLUDED.name, updated_at = now()
                    RETURNING artist_id
                    """,
                    (track_data["artist_id"], track_data["artist"]),
                )
                artist_id = cur.fetchone()["artist_id"]

                # Link track to artist
                cur.execute(
                    """
                    INSERT INTO artists.track_credits (track_id, artist_id, position)
                    VALUES (%s, %s, 0)
                    ON CONFLICT DO NOTHING
                    """,
                    (track_id, artist_id),
                )

                # Store artist genres
                for genre_name in track_data.get("genres", []):
                    cur.execute(
                        """
                        INSERT INTO artists.genres (name) VALUES (%s)
                        ON CONFLICT (name) DO NOTHING
                        """,
                        (genre_name,),
                    )
                    cur.execute(
                        "SELECT genre_id FROM artists.genres WHERE name = %s",
                        (genre_name,),
                    )
                    genre_id = cur.fetchone()["genre_id"]
                    cur.execute(
                        """
                        INSERT INTO artists.genre_map (artist_id, genre_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (artist_id, genre_id),
                    )

            # Upsert playback
            cur.execute(
                """
                INSERT INTO users.playback (user_id, track_id, played_at)
                VALUES (%s, %s, now())
                ON CONFLICT (user_id) DO UPDATE SET
                    track_id = EXCLUDED.track_id, played_at = now()
                """,
                (uid, track_id),
            )
            conn.commit()


# ── Genres ───────────────────────────────────────────────────


def get_genre_analysis(spotify_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            uid = _user_pk(cur, spotify_id)
            if uid is None:
                return None

            cur.execute(
                "SELECT genre_last_updated FROM users.profiles WHERE user_id = %s",
                (uid,),
            )
            profile = cur.fetchone()
            if not profile or not profile["genre_last_updated"]:
                return None

            # Sub-genre stats
            cur.execute(
                """
                SELECT g.name, gs.portion, mg.name AS parent_genre, mg.gradient
                FROM users.genre_stats gs
                JOIN artists.genres g ON gs.genre_id = g.genre_id
                LEFT JOIN artists.meta_genres mg ON g.meta_genre_id = mg.meta_genre_id
                WHERE gs.user_id = %s
                ORDER BY gs.rank
                """,
                (uid,),
            )
            sub_genres = {}
            for row in cur.fetchall():
                sub_genres[row["name"]] = {
                    "portion": float(row["portion"]),
                    "parent_genre": row["parent_genre"] or "other",
                    "gradient": row["gradient"] or "",
                }

            # Meta-genre stats
            cur.execute(
                """
                SELECT mg.name, mgs.portion, mg.gradient
                FROM users.meta_genre_stats mgs
                JOIN artists.meta_genres mg ON mgs.meta_genre_id = mg.meta_genre_id
                WHERE mgs.user_id = %s
                ORDER BY mgs.rank
                """,
                (uid,),
            )
            meta_genres = {}
            for row in cur.fetchall():
                meta_genres[row["name"]] = {
                    "portion": float(row["portion"]),
                    "gradient": row["gradient"] or "",
                }

            # Top subgenre
            cur.execute(
                """
                SELECT g.name AS sub_genre, mg.name AS parent_genre, mg.gradient
                FROM users.profiles p
                JOIN artists.genres g ON p.top_genre_id = g.genre_id
                LEFT JOIN artists.meta_genres mg ON g.meta_genre_id = mg.meta_genre_id
                WHERE p.user_id = %s
                """,
                (uid,),
            )
            top_row = cur.fetchone()
            top_subgenre = None
            if top_row:
                top_subgenre = {
                    "sub_genre": top_row["sub_genre"],
                    "parent_genre": top_row["parent_genre"] or "other",
                    "gradient": top_row["gradient"] or "",
                }

            return {
                "sub_genres": sub_genres,
                "meta_genres": meta_genres,
                "top_subgenre": top_subgenre,
            }


def save_genre_analysis(
    spotify_id: str,
    sub_genres: dict,
    meta_genres: dict,
    top_subgenre: dict | None,
) -> None:
    """Persist computed genre analysis to the normalized tables."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            uid = _require_user_pk(cur, spotify_id)

            # Clear existing stats
            cur.execute("DELETE FROM users.genre_stats WHERE user_id = %s", (uid,))
            cur.execute("DELETE FROM users.meta_genre_stats WHERE user_id = %s", (uid,))

            # Upsert meta genres and save stats
            for rank, (name, data) in enumerate(meta_genres.items(), 1):
                cur.execute(
                    """
                    INSERT INTO artists.meta_genres (name, gradient)
                    VALUES (%s, %s)
                    ON CONFLICT (name) DO UPDATE SET gradient = EXCLUDED.gradient
                    RETURNING meta_genre_id
                    """,
                    (name, data["gradient"]),
                )
                mg_id = cur.fetchone()["meta_genre_id"]
                cur.execute(
                    """
                    INSERT INTO users.meta_genre_stats (user_id, meta_genre_id, portion, rank)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (uid, mg_id, data["portion"], rank),
                )

            # Upsert genres and save sub-genre stats
            for rank, (name, data) in enumerate(sub_genres.items(), 1):
                parent = data["parent_genre"]
                # Resolve parent meta genre
                cur.execute(
                    "SELECT meta_genre_id FROM artists.meta_genres WHERE name = %s",
                    (parent,),
                )
                mg_row = cur.fetchone()
                mg_id = mg_row["meta_genre_id"] if mg_row else None

                cur.execute(
                    """
                    INSERT INTO artists.genres (name, meta_genre_id)
                    VALUES (%s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        meta_genre_id = COALESCE(EXCLUDED.meta_genre_id, artists.genres.meta_genre_id)
                    RETURNING genre_id
                    """,
                    (name, mg_id),
                )
                genre_id = cur.fetchone()["genre_id"]
                cur.execute(
                    """
                    INSERT INTO users.genre_stats (user_id, genre_id, portion, rank)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (uid, genre_id, data["portion"], rank),
                )

            # Set top genre on profile
            if top_subgenre and top_subgenre.get("sub_genre"):
                cur.execute(
                    "SELECT genre_id FROM artists.genres WHERE name = %s",
                    (top_subgenre["sub_genre"],),
                )
                g_row = cur.fetchone()
                if g_row:
                    cur.execute(
                        """
                        UPDATE users.profiles
                        SET top_genre_id = %s, genre_last_updated = now()
                        WHERE user_id = %s
                        """,
                        (g_row["genre_id"], uid),
                    )
                else:
                    cur.execute(
                        "UPDATE users.profiles SET genre_last_updated = now() WHERE user_id = %s",
                        (uid,),
                    )
            else:
                cur.execute(
                    "UPDATE users.profiles SET genre_last_updated = now() WHERE user_id = %s",
                    (uid,),
                )

            conn.commit()


def clear_genre_analysis(spotify_id: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            uid = _user_pk(cur, spotify_id)
            if uid is None:
                return
            cur.execute("DELETE FROM users.genre_stats WHERE user_id = %s", (uid,))
            cur.execute("DELETE FROM users.meta_genre_stats WHERE user_id = %s", (uid,))
            cur.execute(
                """
                UPDATE users.profiles
                SET genre_last_updated = NULL, top_genre_id = NULL
                WHERE user_id = %s
                """,
                (uid,),
            )
            conn.commit()


# ── Admin helpers ────────────────────────────────────────────


def get_all_users_with_tokens() -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.spotify_id, t.access_token
                FROM users.profiles p
                JOIN users.tokens t ON p.user_id = t.user_id
                """,
            )
            return [dict(row) for row in cur.fetchall()]


def backfill_playlist_metadata(user_spotify_id: str, playlists: list[dict]) -> None:
    """Admin: update playlist metadata for a user's saved playlists."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            for pl in playlists:
                cur.execute(
                    """
                    UPDATE playlists.details
                    SET track_count = %s, external_url = %s, updated_at = now()
                    WHERE spotify_id = %s
                    """,
                    (pl.get("tracks", 0), pl["external_url"], pl["id"]),
                )
            conn.commit()
