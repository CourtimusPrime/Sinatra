// Authorization token that must have been created previously. See : https://developer.spotify.com/documentation/web-api/concepts/authorization
const token = 'BQDqP8QjmOHWD1uM--VdvOv9Rly-uTXwGPsj4XiTn9PSSQZjx1atv8SMaGqBOjCFpGogkcLfe41y3orxPlIS6jKeeGdDza3Q09KTcAj5h58aGscim1EoP8FVRTWQHfcxQCoYyX8242BbH36XhLwOekmYet1yVgNBjfIVip6Q5dx4ldujhewXpOcPgJKVgJp0qO7tAS7AUL4yyJ_8QFSIuEAUH8vYv2KVMyDcPufdymlFu1KtC1alDAsWFpWjrhHLYsl1bj_3s8ooxfSn2UyWiDwHuXtfrjDn6Mm-';

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
    ({ name, artists, album }) =>
      `<li>
        <img src="${album.images[0].url}" alt="${name} album cover" width="50" height="50">
        ${name} by ${artists.map(artist => artist.name).join(', ')}
      </li>`
  );

  // Send the track list to the HTML page
  const trackListElement = document.getElementById('track-list');
  trackListElement.innerHTML = trackList.join('');
}

main().catch(console.error);