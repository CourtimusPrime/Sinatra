// Authorization token that must have been created previously. See : https://developer.spotify.com/documentation/web-api/concepts/authorization
const token = 'BQDw-O5Mu6a1nObq_wgZNF8GyTgESoEO_80rcmvEtjLeZzj0xUuYBoxIAyjzra6rBinztQWkQ9f0zbApeKcVA-KFW49l8aIrEwTVL9MTYfebHAUg3hrO5IgNFDwBgE4Rk9vWmngm7Nx3o9ZDKge5aSQLL1kU7PWOzTKS0Iwj580mNr8QoA-cgiiJ1Mp7szhprPAfhJq7CUzBuCssRWEwDQcx4AZg-XEOSflk7Ahvu3WhQEC9iJ4u3FX5B99hy0GuXQQf6VeQ2SgpNqbsJasMnCZzQkedcWWUwdsU';
async function fetchWebApi(endpoint, method, body) {
  const res = await fetch(`https://api.spotify.com/${endpoint}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    method,
    body:JSON.stringify(body)
  });
  return await res.json();
}

async function getTopTracks(){
  // Endpoint reference : https://developer.spotify.com/documentation/web-api/reference/get-users-top-artists-and-tracks
  return (await fetchWebApi(
    'v1/me/top/tracks?time_range=long_term&limit=5', 'GET'
  )).items;
}

const topTracks = await getTopTracks();
console.log(
  topTracks?.map(
    ({name, artists}) =>
      `${name} by ${artists.map(artist => artist.name).join(', ')}`
  )
);