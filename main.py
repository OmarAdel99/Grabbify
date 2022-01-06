from flask import Flask, request, render_template
import youtube_dl
from youtubesearchpython import VideosSearch
import threading
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pathlib
import time
from os import path


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    # global progress_count
    if d['status'] == 'finished':
        pass
        # print('Done downloading, now converting ...')
        # progress_count += 1


# Global Variables
progress_count = 0
download_path = ''
playlist_id = ''
track_list_total = 0
PLAYLIST_ID = ""
app = Flask(__name__)
auth_manager = SpotifyClientCredentials('689e459b019f468b9180e15f4428b548', '8e338ee6300946edbd7e3d520b2dda58')
threads = list()
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3'
    }],
    'outtmpl': '',
    'nooverwrites': "true",
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}

# Client Credentials Flow
sp = spotipy.Spotify(auth_manager=auth_manager)


def get_playlist_tracks(playlist_id):
    count = 0
    results = sp.playlist_items(playlist_id, additional_types={'track'})
    my_tracks = results['items']
    track_list = []
    while results['next']:
        results = sp.next(results)
        my_tracks.extend(results['items'])
    for myTrack in my_tracks:
        artist = ''
        artists = myTrack.get("track").get("artists")
        if len(artists) > 1:
            for x in range(0, 1):
                artist += artist + artists[x].get("name") + ' '
        else:
            artist = artists[0].get("name")
        trackName = (('{:04d}'.format(count)), artist, myTrack.get("track").get("name"))
        count += 1
        track_list.append(trackName)
    global track_list_total
    track_list_total = len(track_list)
    return track_list


def playlist_download(track_list, thread_no, total_threads):
    global progress_count
    start = int(thread_no * (int(track_list_total) / total_threads))
    end = int((thread_no + 1) * (int(track_list_total) / total_threads))
    for track in track_list[start: end]:
        track_name = track[1] + ' - ' + track[2]
        result = track_search(track_name)
        print(result.get("result")[0].get("title"))
        url = result.get("result")[0].get("link")
        progress_count += 1
        track_download(track_name, track[0], url)


def track_search(track):
    videosSearch = VideosSearch(track, limit=1)
    return videosSearch.result()


def track_download(track_name, track_no, url):
    ydl_opts['outtmpl'] = download_path + '/' + track_no + ' %(title)s.%(ext)s'
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            with open((download_path + "/_" + playlist_id + ".txt"), "a", encoding="utf-8") as download_log:
                download_log.write((track_name + "\n"))
                download_log.close()
        except:
            print("Error! Retrying...")
            time.sleep(5)
            ydl.download([url])
            with open((download_path + "/_" + playlist_id + ".txt"), "a", encoding="utf-8") as download_log:
                download_log.write((track_name + "\n"))
                download_log.close()


def thread_factory(track_list):
    x = 10
    for y in range(x):
        print("Thread #{} Starting ~".format(y + 1))
        my_thread = threading.Thread(target=playlist_download, args=(track_list, y, x),
                                     name=('Download Worker - ' + str(y)))
        threads.append(my_thread)
        my_thread.start()


def check_task_progress(progress):
    progress = (progress / track_list_total) * 100
    if progress >= 100:
        return True
    else:
        return False


@app.route('/progress')
def get_progress_html():
    if track_list_total == 0:
        # return render_template('index.html', prog=-1)
        return "0"
    progress = (progress_count / track_list_total) * 100
    if progress >= 100:
        return "100"
    else:
        return str(int(progress))


def progress_thread():
    global progress_count
    while True:
        if check_task_progress(progress_count):
            for my_thread in threads:
                if my_thread.is_alive():
                    print("Active thread: " + my_thread.getName())
                    print("Not all threads done")
                    time.sleep(10)
                    continue
                else:
                    threads.remove(my_thread)
        if not len(threads):
            progress_count = 0
            with app.app_context(), app.test_request_context():
                return render_template('index.html', msg="Download complete!")
        else:
            print("Task active")
            time.sleep(10)


def run_app():
    app.run(host="127.0.0.1", port=8080, debug=False)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/index.html", methods=['GET', 'POST'])
def get_playlist_form():
    global download_path
    global playlist_id
    playlist_id = request.form.get('playlist_id', '')
    playlist_name = (sp.playlist(playlist_id, fields="name"))['name']
    download_path = request.form.get('download_path', '') + '/' + playlist_name + '/'
    try:
        pathlib.Path(download_path).mkdir(parents=True, exist_ok=True)
    except:
        pass
    ydl_opts['download_archive'] = download_path + '_' + playlist_name + ' -' + playlist_id + '.txt'
    if len(playlist_id) == 22:
        if path.exists(download_path):
            try:
                track_list = get_playlist_tracks(playlist_id)
            except:
                with app.app_context(), app.test_request_context():
                    return render_template('index.html', msg="Error! Incorrect playlist ID.")
            thread_factory(track_list)
            prg_thread = threading.Thread(target=progress_thread, name='Progress Thread')
            prg_thread.start()
            return render_template('index.html', playlist_id=playlist_id, download_path=download_path)
        else:
            with app.app_context(), app.test_request_context():
                return render_template('index.html', msg="Error! Incorrect download location.")
    else:
        with app.app_context(), app.test_request_context():
            return render_template('index.html', msg="Error! Incorrect playlist ID.")


@app.route("/blog.html")
def get_blog():
    return render_template('blog.html')


if __name__ == "__main__":
    run_thread = threading.Thread(target=run_app, name='Run App')
    run_thread.start()
