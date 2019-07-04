import requests
import json
import os
import threading
import time
import Util
import ProxiesDataBase
import codecs

root_addr = "http://localhost:3000"

## Get all playlists info
def getPlaylists():

    hot_playlists_api = root_addr + "/top/playlist"
    hot_playlists = (requests.get(url = hot_playlists_api).json())['playlists']
    playlists = []

    for i in range(len(hot_playlists)):
        playlists.append({'name' : hot_playlists[i]['name'], 'id' : hot_playlists[i]['id']})

    return playlists

## Get single playlist
def getPlaylistDetail(playlist_id, proxy):

    songs = []
    playlist_detail_api = root_addr + "/playlist/detail"

    res = requests.get(url = playlist_detail_api, params = {'id' : playlist_id, 'proxy' : proxy}).json()
    data = res['playlist']
    
    for j in range(len(data['tracks'])):
        songs.append({'song_name' : data['tracks'][j]['name'], 'song_id' : data['tracks'][j]['id']})

    return songs

## Get comment given song id
def getComment(id, proxy):

    comments = []
    comment_api = root_addr + "/comment/hot"
    res = requests.get(url = comment_api, params = {'id' : id, 'type' : 0, 'proxy' : proxy}).json()
    success = 'hotComments' in res
    if success:
        hot_comments = res['hotComments']
    else:
        hot_comments = {}
    
    for i in range(len(hot_comments)):
        content = "IP 被封"
        if success:
            content = hot_comments[i]['content']

        comments.append({'user' : hot_comments[i]['user']['nickname'], 'content' : content})

    return comments

## Update proxy every 10 minutes
def refreshProxies():
    Util.Refresh()
    threading.Timer(10 * 60, refreshProxies).start()

## Validate if given proxy can work as expected
def validateProxy(proxy):

    try:
        hot_playlists_api = root_addr + "/top/playlist"
        hot_playlists = requests.get(url = hot_playlists_api, params = {'proxy' : proxy}).json()
    except Exception as e:
        print("Catched Exception: " + e)
        return False

    try:
        playlist_detail_api = root_addr + "/playlist/detail"
        songs = requests.get(url = playlist_detail_api, params = {'id' : 24381616, 'proxy' : proxy}).json()
    except Exception as e:
        print("Catched Exception: " + e)
        return False

    try:
        comment_api = root_addr + "/comment/hot"
        comments = requests.get(url = comment_api, params = {'id' : 186016, 'type' : 0, 'proxy' : proxy}).json()
    except Exception as e:
        print("Catched Exception: " + e)
        return False

    if 'msg' in hot_playlists or 'msg' in comments or 'msg' in songs:
        return False
    else:
        print(proxy)
        return True

## Get current proxy
def getProxyForList():
    
    proxy = (Util.Get())['http']  
    while (not validateProxy(proxy)):
        proxy = (Util.Get())['http']
    
    return proxy


def main():

    # Initialize proxy database
    ProxiesDataBase.InitDB()
    # Proxy setup
    refreshProxies()
    # Get all playlists
    playlists = getPlaylists()

    all_playlists_names = []

    with open('all_comments.json', encoding='utf-8') as f:
        data = json.load(f)

    for i in range(len(data)):
        all_playlists_names.append(data[i][0])

    # Save comments to json file
    for i in range(len(playlists)):
        
        playlist_name = playlists[i]['name']
        playlist_id = playlists[i]['id']

        if playlist_name in all_playlists_names:
            continue
        else:
            try: 
                proxy = getProxyForList()
                songs = getPlaylistDetail(playlist_id, proxy)
                songs_comments = [playlist_name]

                for j in range(len(songs)):
                    song_name = songs[j]['song_name']
                    song_id = songs[j]['song_id']
                    songs_comments.append({'song' : song_name, 'comments' : getComment(song_id, proxy)})
            
                all_playlists_names.append(playlist_name)

                fp = codecs.open('all_comments.json', 'a+', 'utf-8')
                fp.write(json.dumps(songs_comments, ensure_ascii=False))
                fp.close()
            except Exception as e:
                print("Catched Exception: " + e)
                continue

    print("All comments has been crawled.\nFinalizing sequence.")
    os._exit(0)


if __name__== "__main__":
    main()