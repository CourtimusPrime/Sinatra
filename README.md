
# 🎸 Sinatra

Sinatra is a cross-platform music app used for sharing music tastes and the aux. Create a custom link-in-bio to a unique music profile for listing your favourite tracks and playlists and compare your music taste with dynamic charts. Share the aux across different music apps, get tips from your own lists, and enable vibe-checks to maintain a consistent queue.


## Key Features

- **🚀 Click-and-Play Anywhere:** Share a link Light/dark mode toggle
- **🤝 One Queue to Rule Them All:** Friends on Spotify, Tidal, Apple? Everyone controls the same party playlist.
- **🤩 Public Music Profile:** Drop a link-in-bio that shows your latest tracks and prized playlists.
- **💞 Sharing the Love:** See your own ❤️ marks inside anyone's playlist at a glance.
- **📊 Charts that Slap:** Compare dynamic charts of streamed minutes, top tracks, genres, and more.

- **📚 Any-App Login(s):** Sign in with one platform, or all of them, to keep everything in sync.


## Installation

**_Step #1:_ Clone the Repo**
```bash
    git clone https://github.com/CourtimusPrime/Sinatra
    cd Sinatra
```
**_Step #2:_ Set up a Python environment**

Ensure Python 3.13 or higher is installed. Create and activate a virtual environment:

```bash
    python3 -m venv venv
    source venv/bin/activate  # On Mac/Linux
```
**_Step #3:_ Install Dependencies**

Install the required Python packages
```bash
    pip install --upgrade pip
    pip install -r requirements.txt
```
**_Step #4:_ Set up Environment Variables**

Create a `.env` file in the root directory with the following variables:
| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `SPOTIFY_CLIENT_ID` | `string` | **Required** for Spotify API (get from Dashboard).|
| `SPOTIFY_SECRET_ID` | `string` | **Required** for Spotify API. |
| `SPOTIPY_REDIRECT_URI` | `url` | **Required** for Spotify API callbacks. |
| `MONGODB_URI` | `url` | **Required** for MongoDB (get from Atlas). |
| `TIDAL_ID` | `string` | **Required** for Tidal API (get from Dashboard). |
| `TIDAL_REDIRECT_URI` | `url` | **Required** for Tidal API callbacks. |

**_Step #5:_ Run the Application**

Start the FastAPI server using `uvicorn`:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

The app will be accessible at `http://localhost:8000`.

**_Step #6:_ Access the Frontend**

Open the following URLs in a browser:
- **Home Page:** `http://localhost:8000`
- **Login Page:** `http://localhost:8000/login-page`
- **Onboarding Page:** `http://localhost:8000/onboard`

**_Step #7:_ Run Tests (optional)**

Verify the setup by running the pytests:
```bash
pytest backend/tests --disable-warnings
```
## Authors

- [@CourtimusPrime](https://github.com/CourtimusPrime)
- [@AmBornstein](https://github.com/ambornstein)

## Feedback

If you have any feedback, please reach out to us at dashdale02@gmail.com

