from flask import Flask, render_template_string, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

recent_songs = []
saved_songs = []
home_recommendations = []

def fetch_home_recommendations():
    global home_recommendations
    if home_recommendations:
        return home_recommendations
    try:
        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': ['ios', 'android']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info("ytsearch10:top global hits popular songs audio", download=False)
            results = []
            for entry in info.get('entries', []):
                url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                title = entry.get('title')
                thumbnail = entry.get('thumbnail') or f"https://i.ytimg.com/vi/{entry.get('id')}/hqdefault.jpg"
                channel = entry.get('uploader') or entry.get('channel') or "YouTube"
                results.append({"title": title, "url": url, "thumbnail": thumbnail, "channel": channel})
            home_recommendations = results
    except Exception as e:
        print("Home Error:", str(e))
    return home_recommendations

UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Echoo Music Pro</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", sans-serif; }
        body { background-color: #040406; color: #fff; display: flex; flex-direction: column; align-items: center; min-height: 100vh; padding-bottom: 140px; overflow-x: hidden; }
        .top-header { width: 100%; max-width: 420px; padding: 24px 20px 12px 20px; display: flex; justify-content: space-between; align-items: center; }
        .app-brand { font-size: 26px; font-weight: 800; letter-spacing: -0.5px; background: linear-gradient(135deg, #ff2a5f, #ff7e5f); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .search-icon-btn { background: rgba(255, 255, 255, 0.06); backdrop-filter: blur(25px); border: 1px solid rgba(255,255,255,0.1); width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #ff2a5f; cursor: pointer; transition: 0.2s; }
        .search-icon-btn:active { transform: scale(0.92); }
        .chips-container { width: 100%; max-width: 420px; padding: 0 20px; display: flex; gap: 10px; margin-bottom: 18px; overflow-x: auto; scrollbar-width: none; }
        .chips-container::-webkit-scrollbar { display: none; }
        .chip { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.08); padding: 8px 18px; border-radius: 22px; font-size: 13px; font-weight: 600; color: #98989f; cursor: pointer; white-space: nowrap; transition: 0.2s; }
        .chip.active { background: linear-gradient(135deg, #ff2a5f, #ff5e62); color: #fff; border-color: transparent; box-shadow: 0 4px 20px rgba(255,42,95,0.4); }
        .featured-box { width: calc(100% - 40px); max-width: 380px; height: 135px; background: linear-gradient(135deg, #18181c, #26262c); border-radius: 26px; padding: 20px; display: flex; flex-direction: column; justify-content: space-between; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 12px 35px rgba(0,0,0,0.6); margin: 0 auto 22px auto; position: relative; overflow: hidden; }
        .feat-title { font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 4px; }
        .feat-desc { font-size: 12px; color: #98989f; line-height: 1.4; }
        .feat-btn { background: #ff2a5f; color: white; border: none; padding: 7px 16px; border-radius: 14px; font-size: 11px; font-weight: 700; width: fit-content; cursor: pointer; box-shadow: 0 4px 12px rgba(255,42,95,0.3); }
        .section-header { width: 100%; max-width: 420px; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .section-title { font-size: 18px; font-weight: 700; color: #fff; letter-spacing: -0.3px; }
        .content-area { width: 100%; max-width: 420px; padding: 0 20px; display: flex; flex-direction: column; gap: 10px; }
        .song-card { display: flex; align-items: center; background: rgba(255, 255, 255, 0.04); backdrop-filter: blur(20px); border-radius: 18px; padding: 9px 12px; gap: 12px; cursor: pointer; border: 1px solid rgba(255,255,255,0.05); transition: 0.2s; }
        .song-card:active { background: rgba(255, 255, 255, 0.08); transform: scale(0.98); }
        .song-card img { width: 52px; height: 52px; border-radius: 14px; object-fit: cover; }
        .song-info { flex: 1; overflow: hidden; }
        .song-title { font-size: 14px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; color: #f5f5f7; }
        .song-artist { font-size: 12px; color: #98989f; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .mini-player { display: none; position: fixed; bottom: 95px; left: 50%; transform: translateX(-50%); width: calc(100% - 30px); max-width: 390px; height: 62px; background: rgba(24, 24, 28, 0.92); backdrop-filter: blur(30px); border-radius: 22px; border: 1px solid rgba(255,42,95,0.3); z-index: 999; align-items: center; padding: 0 14px; gap: 12px; box-shadow: 0 12px 35px rgba(0,0,0,0.7); }
        .mini-player.active { display: flex; }
        .mini-img { width: 44px; height: 44px; border-radius: 12px; object-fit: cover; }
        .mini-meta { flex: 1; overflow: hidden; cursor: pointer; }
        .mini-title { font-size: 13px; font-weight: 600; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .mini-artist { font-size: 11px; color: #98989f; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .mini-play-btn { background: #ff2a5f; border: none; width: 38px; height: 38px; border-radius: 50%; color: white; display: flex; align-items: center; justify-content: center; font-size: 14px; cursor: pointer; box-shadow: 0 4px 12px rgba(255,42,95,0.4); }
        .floating-nav { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); width: calc(100% - 30px); max-width: 390px; height: 66px; background: rgba(22, 22, 26, 0.88); backdrop-filter: blur(35px); border-radius: 36px; border: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-around; align-items: center; z-index: 1000; padding: 0 8px; box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
        .nav-item { color: #98989f; background: none; border: none; font-size: 13px; font-weight: 600; cursor: pointer; padding: 8px 16px; border-radius: 24px; transition: 0.2s; }
        .nav-item.active { background: #ff2a5f; color: #fff; box-shadow: 0 4px 18px rgba(255,42,95,0.4); }
        .player-view { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(8, 8, 10, 0.97); backdrop-filter: blur(40px); z-index: 2000; flex-direction: column; justify-content: space-between; padding: 45px 22px; }
        .player-view.active { display: flex; }
        .player-top { display: flex; justify-content: space-between; align-items: center; width: 100%; }
        .player-btn-action { color: #ff2a5f; background: rgba(255,42,95,0.1); border: 1px solid rgba(255,42,95,0.25); padding: 7px 16px; border-radius: 20px; font-size: 13px; font-weight: 600; cursor: pointer; }
        .artwork-box { width: 270px; height: 270px; margin: 0 auto; border-radius: 28px; overflow: hidden; background: #18181c; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
        .artwork-box img { width: 100%; height: 100%; object-fit: cover; }
        .player-meta { width: 100%; padding: 0 5px; }
        .m-title { font-size: 19px; font-weight: 700; color: #fff; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .m-artist { font-size: 14px; color: #98989f; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        audio { width: 100%; height: 44px; border-radius: 22px; outline: none; }
        .related-box { max-height: 140px; overflow-y: auto; width: 100%; display: flex; flex-direction: column; gap: 8px; scrollbar-width: none; }
        .search-modal { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(6, 6, 8, 0.96); backdrop-filter: blur(35px); z-index: 1500; flex-direction: column; padding: 25px 20px; }
        .search-modal.active { display: flex; }
        .search-bar-row { display: flex; gap: 10px; width: 100%; margin-bottom: 20px; }
        .search-input-box { flex: 1; background: rgba(255, 255, 255, 0.07); border: 1px solid rgba(255,255,255,0.12); border-radius: 26px; padding: 12px 20px; color: white; outline: none; font-size: 15px; }
        .close-search { background: none; border: none; color: #ff2a5f; font-weight: 600; font-size: 15px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="top-header">
        <div class="app-brand">Echoo</div>
        <div class="search-icon-btn" onclick="openSearchModal()">🔍</div>
    </div>
    <div class="chips-container">
        <div class="chip active" onclick="filterCategory('All', this)">All</div>
        <div class="chip" onclick="filterCategory('Trending', this)">Trending</div>
        <div class="chip" onclick="filterCategory('Bollywood', this)">Bollywood</div>
        <div class="chip" onclick="filterCategory('Lo-Fi', this)">Lo-Fi</div>
        <div class="chip" onclick="filterCategory('Remix', this)">Remix</div>
    </div>
    <div class="featured-box">
        <div>
            <div class="feat-title">Music for Your Mood</div>
            <div class="feat-desc">Soundtracks that match your vibe. Fast & smooth playback.</div>
        </div>
        <button class="feat-btn" onclick="loadRecommended()">Explore Beats</button>
    </div>
    <div class="section-header">
        <div class="section-title" id="sec-title">Recommended For You</div>
    </div>
    <div class="content-area" id="main-content-area"></div>
    <div class="mini-player" id="miniPlayer">
        <img class="mini-img" id="mini-img" src="" alt="Art">
        <div class="mini-meta" onclick="openPlayer()">
            <div class="mini-title" id="mini-title">Title</div>
            <div class="mini-artist" id="mini-artist">Artist</div>
        </div>
        <button class="mini-play-btn" id="miniPlayBtn" onclick="togglePlayPause()">❚❚</button>
    </div>
    <div class="floating-nav">
        <button class="nav-item active" onclick="switchTab('home', this)">Home</button>
        <button class="nav-item" onclick="switchTab('recent', this)">Recent</button>
        <button class="nav-item" onclick="switchTab('saved', this)">Saved</button>
        <button class="nav-item" onclick="openPlayer()">Player</button>
    </div>
    <div class="player-view" id="playerOverlay">
        <div class="player-top">
            <button class="player-btn-action" onclick="closePlayer()">Minimize</button>
            <span style="font-size: 12px; font-weight: 600; color: #98989f; letter-spacing: 1px;">NOW PLAYING</span>
            <button class="player-btn-action" onclick="saveCurrentSong()">Save</button>
        </div>
        <div class="artwork-box"><img id="player-img" src="" alt="Art"></div>
        <div class="player-meta">
            <div class="m-title" id="player-title">Song Title</div>
            <div class="m-artist" id="player-artist">Artist Name</div>
        </div>
        <audio id="audioElement" controls autoplay onended="playNextRelated()" onplay="updatePlayState(true)" onpause="updatePlayState(false)"></audio>
        <div style="font-size: 14px; font-weight: 700; color: #fff;">Up Next</div>
        <div class="related-box" id="related-list"></div>
    </div>
    <div class="search-modal" id="searchModal">
        <div class="search-bar-row">
            <input type="text" id="query-input" class="search-input-box" placeholder="Search songs, artists..." onkeypress="handleSearchKey(event)">
            <button class="close-search" onclick="closeSearchModal()">Cancel</button>
        </div>
        <div class="section-header" style="padding: 0; margin-bottom: 10px;">
            <div class="section-title" style="font-size: 15px;">Search Results</div>
        </div>
        <div class="content-area" id="search-results-area" style="max-width: 100%; padding: 0; overflow-y: auto; max-height: calc(100vh - 120px);"></div>
    </div>
    <script>
        let currentSongData = null;
        let relatedQueue = [];
        window.onload = function() { loadRecommended(); };
        function loadRecommended() {
            document.getElementById('sec-title').innerText = "Recommended For You";
            let area = document.getElementById('main-content-area');
            area.innerHTML = '<div style="color: #98989f; text-align: center; padding: 40px; font-size: 13px;">Loading beats...</div>';
            fetch('/get-home').then(res => res.json()).then(data => { renderSongList(data, area); });
        }
        function filterCategory(cat, element) {
            document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
            element.classList.add('active');
            let query = "top global hits";
            if(cat === 'Trending') query = "trending viral music 2026";
            if(cat === 'Bollywood') query = "latest bollywood hits";
            if(cat === 'Lo-Fi') query = "lofi chill beats";
            if(cat === 'Remix') query = "bass boosted remix songs";
            let area = document.getElementById('main-content-area');
            document.getElementById('sec-title').innerText = cat + " Selection";
            area.innerHTML = '<div style="color: #98989f; text-align: center; padding: 40px; font-size: 13px;">Loading...</div>';
            fetch('/search', { method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'query=' + encodeURIComponent(query) }).then(res => res.json()).then(data => { renderSongList(data, area); });
        }
        function switchTab(tabName, btnElement) {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            btnElement.classList.add('active');
            let area = document.getElementById('main-content-area');
            let title = document.getElementById('sec-title');
            if(tabName === 'home') { loadRecommended(); }
            else if(tabName === 'recent') { title.innerText = "Listening History"; fetch('/get-recent').then(res => res.json()).then(data => renderSongList(data, area)); }
            else if(tabName === 'saved') { title.innerText = "Liked Songs"; fetch('/get-saved').then(res => res.json()).then(data => renderSongList(data, area)); }
        }
        function openSearchModal() { document.getElementById('searchModal').classList.add('active'); document.getElementById('query-input').focus(); }
        function closeSearchModal() { document.getElementById('searchModal').classList.remove('active'); }
        function handleSearchKey(e) { if(e.key === 'Enter') performSearch(); }
        function performSearch() {
            let q = document.getElementById('query-input').value.trim();
            if(!q) return;
            let area = document.getElementById('search-results-area');
            area.innerHTML = '<div style="color: #98989f; text-align: center; padding: 40px; font-size: 13px;">Searching...</div>';
            fetch('/search', { method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'query=' + encodeURIComponent(q) }).then(res => res.json()).then(data => { renderSongList(data, area); });
        }
        function renderSongList(items, container) {
            container.innerHTML = '';
            if(!items || items.length === 0) { container.innerHTML = '<div style="color: #98989f; text-align: center; padding: 40px; font-size: 13px;">No songs found.</div>'; return; }
            items.forEach((item) => {
                let card = document.createElement('div');
                card.className = 'song-card';
                card.innerHTML = `<img src="${item.thumbnail}" alt="Art"><div class="song-info"><div class="song-title">${item.title}</div><div class="song-artist">${item.channel}</div></div>`;
                card.onclick = () => { playSong(item.url); closeSearchModal(); };
                container.appendChild(card);
            });
        }
        function playSong(url) {
            fetch('/play?url=' + encodeURIComponent(url)).then(res => res.json()).then(data => {
                if(data.error) { alert("Error playing song. Try another track."); return; }
                currentSongData = data;
                document.getElementById('player-title').innerText = data.title;
                document.getElementById('player-artist').innerText = data.channel;
                document.getElementById('player-img').src = data.thumbnail;
                document.getElementById('mini-title').innerText = data.title;
                document.getElementById('mini-artist').innerText = data.channel;
                document.getElementById('mini-img').src = data.thumbnail;
                let audio = document.getElementById('audioElement');
                audio.src = data.url;
                audio.play();
                document.getElementById('miniPlayer').classList.add('active');
                loadRelated(data.title);
            }).catch(err => { alert("Network error playing song."); });
        }
        function loadRelated(query) {
            fetch('/search', { method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'query=' + encodeURIComponent(query + " remix live") }).then(res => res.json()).then(data => {
                relatedQueue = data;
                let relList = document.getElementById('related-list');
                relList.innerHTML = '';
                data.forEach(item => {
                    let rCard = document.createElement('div');
                    rCard.className = 'song-card';
                    rCard.style.padding = '6px 10px';
                    rCard.innerHTML = `<img src="${item.thumbnail}" style="width: 36px; height: 36px;" alt="Art"><div class="song-info"><div class="song-title" style="font-size: 13px;">${item.title}</div></div>`;
                    rCard.onclick = () => playSong(item.url);
                    relList.appendChild(rCard);
                });
            });
        }
        function playNextRelated() { if(relatedQueue.length > 0) { let nextSong = relatedQueue.shift(); playSong(nextSong.url); } }
        function togglePlayPause() { let audio = document.getElementById('audioElement'); if(audio.paused) { audio.play(); } else { audio.pause(); } }
        function updatePlayState(isPlaying) { let btn = document.getElementById('miniPlayBtn'); btn.innerText = isPlaying ? '❚❚' : '▶'; }
        function saveCurrentSong() {
            if(!currentSongData) return;
            fetch('/save-song', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(currentSongData) }).then(res => res.json()).then(msg => { alert("Song saved to Liked list!"); });
        }
        function openPlayer() { if(!currentSongData) return; document.getElementById('playerOverlay').classList.add('active'); }
        function closePlayer() { document.getElementById('playerOverlay').classList.remove('active'); }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(UI_TEMPLATE)

@app.route('/get-home')
def get_home():
    return jsonify(fetch_home_recommendations())

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    results = []
    try:
        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': ['ios', 'android']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch6:{query}", download=False)
            for entry in info.get('entries', []):
                url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                title = entry.get('title')
                thumbnail = entry.get('thumbnail') or f"https://i.ytimg.com/vi/{entry.get('id')}/hqdefault.jpg"
                channel = entry.get('uploader') or entry.get('channel') or "YouTube"
                results.append({"title": title, "url": url, "thumbnail": thumbnail, "channel": channel})
    except Exception as e:
        print("Search Error:", str(e))
    return jsonify(results)

@app.route('/play')
def play():
    video_url = request.args.get('url')
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extractor_args': {'youtube': {'player_client': ['ios', 'android']}},
            'socket_timeout': 10
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            song_data = {
                "title": info.get('title'),
                "url": info.get('url'),
                "thumbnail": info.get('thumbnail'),
                "channel": info.get('uploader') or info.get('channel') or "YouTube"
            }
            if song_data not in recent_songs:
                recent_songs.insert(0, song_data)
                if len(recent_songs) > 15: recent_songs.pop()
            return jsonify(song_data)
    except Exception as e:
        print("Play Error:", str(e))
        return jsonify({"error": str(e)})

@app.route('/get-recent')
def get_recent():
    return jsonify(recent_songs)

@app.route('/get-saved')
def get_saved():
    return jsonify(saved_songs)

@app.route('/save-song', methods=['POST'])
def save_song():
    song = request.json
    if song and song not in saved_songs:
        saved_songs.insert(0, song)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
