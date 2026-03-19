# models/playlists.py

from pydantic import BaseModel


class PlaylistSummary(BaseModel):
    id: str
    name: str
    image: str
    tracks: int


class PlaylistToSave(BaseModel):
    id: str


class PlaylistID(BaseModel):
    id: str


class SaveAllPlaylistsRequest(BaseModel):
    user_id: str
    playlists: list[PlaylistToSave]


class FeaturedPlaylistsUpdateRequest(BaseModel):
    user_id: str
    playlist_ids: list[str]
