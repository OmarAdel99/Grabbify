import sys
import yt_dlp
from youtubesearchpython import VideosSearch
import threading
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pathlib
import time
from os import path, walk
import PySimpleGUI as sg
import difflib


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)


def my_hook(d):
    # global progress_count
    if d['status'] == 'finished':
        pass
        # print('Done downloading, now converting ...')
        # progress_count += 1


# Global Variables
if __name__ == "__main__":
    progress_count = 0
    download_path = ''
    playlist_id = ''
    track_list_total = 0
    PLAYLIST_ID = ""
    auth_manager = SpotifyClientCredentials('689e459b019f468b9180e15f4428b548', '8e338ee6300946edbd7e3d520b2dda58')
    threads = list()
    terminate_flag = False
    complete_flag = False
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3'
        }],
        'prefer_ffmpeg': "true",
        'ffmpeg_location': 'C:/ProgramData/chocolatey/bin',
        'outtmpl': '',
        'nooverwrites': "true",
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
        'quiet': False,
        'ignoreerrors': True,
        'cookies': './cookies.txt'
    }

    # Client Credentials Flow
    sp = spotipy.Spotify(auth_manager=auth_manager)

    sg.theme('Light Teal')
    download_btn = [[sg.Button("Download", size=(12, 2), pad=(55, 20))]]
    cancel_btn = [[sg.Button("Cancel", size=(7, 2))]]
    layout = [[sg.T("Playlist URL :")],
              [sg.Input('', focus=True, visible=False)],
              # open.spotify.com/playlist/35xI4hSJ8MdO1xkXwsd56a
              [sg.Input('open.spotify.com/playlist/7asNokJeuqHQMjvd0rOuhk', key='-ID-', size=36, pad=(5, (2, 12)),
                        tooltip='Copy playlist url from spotify', focus=False)],
              [sg.T('Download Location :')],
              [sg.Input('C:/Users/USER/Music', key='-LOC-', tooltip='A folder will be created in the chosen directory',
                        size=36)],
              [sg.FolderBrowse(target='-LOC-', pad=(5, (4, 12)))],
              [sg.Column(download_btn),
               sg.Column(cancel_btn)],
              [sg.T('', key='-NAME-', expand_x=True)],
              [sg.ProgressBar(size=(36, 20), max_value=100, style='clam', key='-BAR-', visible=False, pad=10,
                              border_width=3)],
              [sg.T('', key='-PROGTXT-', size=(36, 2))]]
    window = sg.Window(title="Grabbify", layout=layout, margins=(40, 30), font='Cambria 14', finalize=True)
    window['-ID-'].bind('<Button-1>', '+SELECT+')
    window['-ID-'].bind('<FocusIn>', '+FOCUS IN+')
    window['-LOC-'].bind('<Button-1>', '+SELECT+')
    window['-LOC-'].bind('<FocusIn>', '+FOCUS IN+')


def clear_default(key):
    window[key].update('')
    return


def get_playlist_tracks():
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
            artist = artists[0].get("name") + ' '
        trackName = (('{:04d}'.format(count)), artist, myTrack.get("track").get("name"))
        count += 1
        track_list.append(trackName)
    global track_list_total
    track_list_total = len(track_list)
    print('track_list_total ::' + str(track_list_total))
    #    with open((download_path + "_" + 'track list.txt'), "w", encoding="utf-8") as log:
    #        for track in track_list:
    #            log.write((str(track) + "\n"))
    #        log.close()
    return track_list


def playlist_download(track_list, thread_no, total_threads):
    global progress_count
    start = int(thread_no * ((int(track_list_total) / total_threads) + 1))
    end = int((thread_no + 1) * ((int(track_list_total) / total_threads) + 1))
    if thread_no == total_threads - 1:
        end = int(track_list_total)
    for track in track_list[start: end]:
        if terminate_flag:
            break
        track_name = track[1] + ' - ' + track[2] + ' Official Lyric'
        if dupe_check(track_name):
            result = track_search(track_name)
            if len(result.get("result")):
                url = result.get("result")[0].get("link")
                track_download(track_name, track[0], url)
            else:
                print("Error: search not found")
        progress_count += 1
    print(progress_count)
    return


def track_search(track):
    videosSearch = VideosSearch(track, limit=1)
    return videosSearch.result()


def dupe_check(track_name):
    if path.exists(download_path + "_" + playlist_id + ".txt"):
        with open((download_path + "_" + playlist_id + ".txt"), "r", encoding="utf-8") as download_log:
            for track in download_log:
                ratio = difflib.SequenceMatcher(None, track, track_name).ratio()
                if ratio > 0.85:
                    # print("Dupe!" + str(ratio) + "\n")
                    return 0
    print('New~ : ' + track_name + '\n')
    return 1


def track_download(track_name, track_no, url):
    ydl_opts['outtmpl'] = download_path + track_no + ' %(title)s.%(ext)s'
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            log = ydl.download([url])
            if log:
                print(log)
            with open((download_path + "_" + playlist_id + ".txt"), "a", encoding="utf-8") as download_log:
                download_log.write((track_name + "\n"))
                download_log.close()
        except:
            print("Error! Retrying...")
            time.sleep(5)
            ydl.download([url])
            with open((download_path + "_" + playlist_id + ".txt"), "a", encoding="utf-8") as download_log:
                download_log.write((track_name + "\n"))
                download_log.close()


def thread_factory(track_list):
    x = 6
    for y in range(x):
        print("Thread #{} Starting ~".format(y))
        my_thread = threading.Thread(target=playlist_download, args=(track_list, y, x),
                                     name=('Download_Worker-' + str(y)))
        threads.append(my_thread)
        my_thread.start()


def thread_log(thread_no, track_name, track_no):
    with open((download_path + "/_Thread#" + str(thread_no) + ".txt"), "a", encoding="utf-8") as download_log:
        download_log.write((str(track_no) + ' - ' + track_name + "\n"))
        download_log.close()


def progress_thread():
    global progress_count
    global complete_flag
    while True:
        if terminate_flag:
            break
        prog = get_progress()
        if 0 <= prog < 100:
            window['-BAR-'].update_bar(prog)
            window['-PROGTXT-'].update('Downloading tracks...  ' + str(prog) + '%')
            time.sleep(0.02)
        elif prog >= 100:
            window['-BAR-'].update_bar(100)
            window['-PROGTXT-'].update("Download complete!")
            for my_thread in threads:
                while my_thread.is_alive():
                    print("Active thread: " + my_thread.getName())
                    time.sleep(5)
                my_thread.join()
                threads.remove(my_thread)
            progress_count = 0
            complete_flag = True
            print('Prog_thread Break')
            break


def get_progress():
    if track_list_total == 0:
        return 0
    else:
        progress = (progress_count / track_list_total) * 100
        if progress >= 100:
            return 100
        else:
            return int(progress)


def scan():
    filenames = next(walk(download_path), (None, None, []))[2]  # [] if no file
    # Check for duplicates
    dupes = []
    missing = []
    for i, j in enumerate(filenames[:-1]):
        if i:
            if j[:4].isdigit():
                if int(j[:4]) == int(filenames[i - 1][:4]) + 1:
                    continue
                elif j[:4] == filenames[i - 1][:4]:
                    dupes.append(j)
                    dupes.append(filenames[i - 1])
                    continue
                else:
                    missing_dict = {
                        "missing": int(filenames[i - 1][:4]) + 1,
                        "next": j
                    }
                    missing.append(missing_dict)
    file = open((download_path + "_Duplicates.txt"), "w", encoding="utf-8")
    file.write('DUPLICATES\n')
    for name in dupes:
        file.write(name + '\n')
    file.write('\n\n\n____________________________________\nMISSING\n')
    file.write('  Missing    --  Next\n')
    for name in missing:
        file.write('    ' + str(name['missing']) + '       --  ' + str(name['next']) + '\n')


def main():
    global download_path
    global playlist_id
    global terminate_flag
    global progress_count
    global complete_flag
    playlist_name = 'Default'
    while True:
        event, values = window.read()
        key = (event.rsplit('+'))[0]
        if event in (sg.WIN_CLOSED, 'Exit', 'Cancel'):
            terminate_flag = True
            window.close()
            sys.exit()
            break
        if complete_flag:
            break
        if event.__contains__("+FOCUS IN+"):
            if values[key] == 'Ex: 35xI4hSJ8MdO1xkXwsd56a':
                window[key].update('')
            else:
                window[key].update(select=True)
        if event.__contains__("+SELECT+"):
            # Mouse Btn1 click
            if values[key] == 'Ex: 35xI4hSJ8MdO1xkXwsd56a':
                window[key].update('')
        if event == 'Download':
            playlist_id = values['-ID-']
            if playlist_id.__contains__('spotify'):
                playlist_id = playlist_id.split('/')
                x = 0
                for p in playlist_id:
                    if p == 'playlist':
                        playlist_id = (playlist_id[x + 1])[:22]
                    x += 1
            try:
                playlist_name = (sp.playlist(playlist_id, fields="name"))['name']
                playlist_name_alnum = ""
                for char in playlist_name:
                    if char.isalnum() or char == ' ':
                        playlist_name_alnum += char
            except:
                sg.popup(font='Cambria 16', no_titlebar=True, background_color='#424242',
                         button_color=('#FFCDD2', '#D50000'), line_width=40,
                         custom_text='Error retrieving playlist.')
            if len(playlist_id) == 22:
                if values['-LOC-']:
                    download_path = values['-LOC-'] + '/' + playlist_name_alnum + '/'
                    try:
                        pathlib.Path(download_path).mkdir(parents=True, exist_ok=True)
                        if path.exists(download_path):
                            ydl_opts[
                                'download_archive'] = download_path + '_' + playlist_name_alnum + ' -' + playlist_id + '.txt'
                        else:
                            sg.popup(font='Cambria 16', no_titlebar=True, background_color='#424242',
                                     button_color=('#FFCDD2', '#D50000'), line_width=40,
                                     custom_text='Error! Download location incorrect.')
                            return
                    except:
                        sg.popup(font='Cambria 16', no_titlebar=True, background_color='#424242',
                                 button_color=('#FFCDD2', '#D50000'), line_width=40,
                                 custom_text='Error! Download location incorrect.')
                        return
                    try:
                        track_list = get_playlist_tracks()
                    except:
                        sg.popup(font='Cambria 16', no_titlebar=True, background_color='#424242',
                                 button_color=('#FFCDD2', '#D50000'), line_width=40,
                                 custom_text='Error retrieving track list.')
                        return
                    progress_count = 0
                    thread_factory(track_list)
                    prg_thread = threading.Thread(target=progress_thread, name='Progress_thread')
                    prg_thread.start()
                    window['-NAME-'].update(playlist_name)
                    window['-BAR-'].update(visible=True)
                    window['-PROGTXT-'].update('Downloading tracks...  ')
            else:
                sg.popup(font='Cambria 16', no_titlebar=True, background_color='#424242',
                         button_color=('#FFCDD2', '#D50000'), line_width=40,
                         custom_text='Error! Incorrect playlist ID.')
    print('prg_thread.join()')
    prg_thread.join()
    for thread in threads:
        thread.join()
    scan()
    complete_flag = False


if __name__ == "__main__":
    while True:
        main()
