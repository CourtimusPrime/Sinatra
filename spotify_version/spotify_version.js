// Authorization token that must have been created previously. See : https://developer.spotify.com/documentation/web-api/concepts/authorization
const token = 'BQAgu28vzvSK9hd02Wer2fXRzrpjBACgfhA_1lDGnHX2XbtjvBcT4dsG5jiRITcSDKzWVgWa1x7oWSrsMLM-MZDhhbXCmRdv8N6QQEEHUWRR2791nDUyTmfllfn1tIL5KY3IvpVo_gNz6xWvzL-9gvqYlEKjvYyaqnjoxYFaUiFApWMUA7BiV8adMs7T_sLLoc6FARJjMtsX6cjItZu6RBWhOJo4h1EXEiLQwaEhUqP3Xu79KqoJ7XQq-v7LMChCUMKEa4g1FCz8ZcZI6veWTaFjejLIls5xV0sn';

async function fetchWebApi(endpoint, method, body) {
  const res = await fetch(`https://api.spotify.com/${endpoint}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    method,
    body: JSON.stringify(body)
  });
  return await res.json();
}

async function getTopTracks() {
  // Endpoint reference : https://developer.spotify.com/documentation/web-api/reference/get-users-top-artists-and-tracks
  return (await fetchWebApi(
    'v1/me/top/tracks?time_range=long_term&limit=5', 'GET'
  )).items;
}

async function main() {
  const topTracks = await getTopTracks();
  const trackList = topTracks?.map(
    ({ name, artists }) =>
      `${name} by ${artists.map(artist => artist.name).join(', ')}`
  );

  // Send the track list to the HTML page
  const trackListElement = document.getElementById('track-list');
  trackListElement.innerHTML = trackList.map(track => `<li>${track}</li>`).join('');
}

main().catch(console.error);