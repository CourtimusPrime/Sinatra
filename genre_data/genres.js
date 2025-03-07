async function updateGenreCounts(csvFilePath) {
    // Fetch top 100 tracks
    const response = await fetch(`http://localhost:3000/me/top/tracks?time_range=short_term&limit=100`);
    const topTracks = await response.json();

    const artistIds = new Set();
    
    // Extract unique artist IDs from the top 100 tracks
    topTracks.forEach(track => {
        track.artists.forEach(artist => artistIds.add(artist.id));
    });

    // Convert the Set into an array and fetch artist details
    const artistIdArray = Array.from(artistIds);
    const artistResponse = await fetch(`http://localhost:3000/artists?ids=${artistIdArray.join(',')}`);
    const artistData = await artistResponse.json();

    // Count genres in the top 100 tracks
    const genreCounts = {};
    artistData.artists.forEach(artist => {
        artist.genres.forEach(genre => {
            genreCounts[genre] = (genreCounts[genre] || 0) + 1;
        });
    });

    // Send genreCounts to Python for updating CSV and visualization
    await fetch('/update_csv_and_visualize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(genreCounts)
    });
}

// Trigger function when page loads (or manually call updateGenreCounts)
updateGenreCounts("genres_mar6_noval.csv");