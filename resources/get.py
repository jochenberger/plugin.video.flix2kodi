from __future__ import unicode_literals

import json
import time
import xbmc
import xbmcvfs

import login
import search
from resources import connect
from resources.utility import generic_utility


def videos_matches(video_type, page, url):
    post_data = ''
    if not xbmcvfs.exists(generic_utility.cookies_file()):
        login.login()

    items_per_page = int(generic_utility.get_setting('items_per_page'))
    off_from = page * items_per_page
    off_to = off_from + items_per_page - 2

    if 'genre' in url:
        post_data = generic_utility.genre % (url.split('?')[1], off_from, off_to, generic_utility.get_setting('authorization_url'))
    elif 'list?' in url:
        data = url.split('?')[1]
        if('mylist' in data):
            list_id = data.split('&')[0]
        else:
            list_id = data
        post_data = generic_utility.list_paths % (list_id, off_from, off_to, generic_utility.get_setting('authorization_url'))

    target_url = generic_utility.evaluator()
    response = connect.load_netflix_site(target_url, post=post_data)
#    utility.log('response: '+response)
    video_ids = extract_other_video_ids(response, video_type)
    return video_ids


def search_matches(search_string, video_type):
    if not xbmcvfs.exists(generic_utility.cookies_file()):
        login.login()
    content = search_results(search_string)
    return extract_other_video_ids(content, video_type)


def extract_other_video_ids(content, video_type):
    video_ids = []
    jsondata = json.loads(content)
    if 'videos' in jsondata['value']:
        videos = jsondata['value']['videos']
        video_ids = filter_videos_by_type(videos, video_type)
    return video_ids


def viewing_activity_matches(video_type):
    if not xbmcvfs.exists(generic_utility.cookies_file()):
        login.login()
    content = viewing_activity_info()
    matches = json.loads(content)['viewedItems']

    metadata = []
#    utility.log('activity: '+unicode(matches))
    for match in matches:
#        utility.log(match)

        if 'seriesTitle' in match:
            metadata_type = 'tv'
            series_title = match['seriesTitle']
        else:
            metadata_type = 'movie'
            series_title = None

        if video_type == metadata_type:
            metadata.append({'id':unicode(match['movieID']), 'title':get_viewing_activity_title(match), 'series_title':series_title})

    return metadata


def filter_videos_by_type(videos, video_type):
    for video in videos.keys():
        metatdata_type = get_metadata_type_my_list(videos, video)
        if video_type != metatdata_type:
            del videos[video]
    return videos

def get_metadata_type_my_list(videos, video):
    type = 'unknown'
    if 'summary' in videos[video]:
        summary = videos[video]['summary']
        if 'type' in summary:
            type = summary['type']

    if 'movie' == type:
        metadata_type = 'movie'
    elif 'unknown' == type:
        metadata_type = 'unknown'
    else:
        metadata_type = 'tv'

    return metadata_type

def get_viewing_activity_title(item):
    date = item['dateStr']
    try:
        series_id = item['series']
        series_title = item['seriesTitle']
        title = item['title']
        title = series_title + ' ' + title
    except Exception:
        title = item['title']
    title = date + ' - ' + title
    return title

def seasons_data(series_id):
    seasons = []
    content = series_info(series_id)
#    utility.log(str(content))
    content = json.loads(content)['video']['seasons']
    for item in content:
        season = item['title'], item['seq']
        seasons.append(season)
    return seasons

def season_title(series_id, seq):
    title = None
    datas = seasons_data(series_id)
    for data in datas:
        if data[1] == seq:
            title = data[0]
            break;
    return title


def episodes_data(season, series_id):
    episodes = []

    content = series_info(series_id)
    content = json.loads(content)['video']['seasons']
    for test in content:
        episode_season = unicode(test['seq'])
        if episode_season == season:
            for item in test['episodes']:
                playcount = 0
                episode_id = item['episodeId']
                episode_nr = item['seq']
                episode_title = (unicode(episode_nr) + '. ' + item['title'])
                duration = item['runtime']
                offset = item['bookmark']['offset']
                if (duration > 0 and float(offset) / float(duration)) >= 0.9:
                    playcount = 1
                description = item['synopsis']
                try:
                    thumb = item['stills'][0]['url']
                except:
                    thumb = generic_utility.addon_fanart()

                episode = series_id, episode_id, episode_title, description, episode_nr, season, duration, thumb, playcount
                episodes.append(episode)
    return episodes



def genre_data(video_type):
    match = []
    if not xbmcvfs.exists(generic_utility.cookies_file()):
        login.login()

    content = genre_info(video_type)

    matches = json.loads(content)['value']['genres']
    for item in matches:
        try:
            match.append((unicode(matches[item]['id']), matches[item]['menuName']))
        except Exception:
            try:
                match.append((unicode(matches[item]['summary']['id']), matches[item]['summary']['menuName']))
            except Exception:
                pass
    return match


def video_info(video_id, lock = None, ignore_cache = False):
    content = ''
    cache_file = xbmc.translatePath(generic_utility.cache_dir() + video_id + '.cache')
    if not ignore_cache and xbmcvfs.exists(cache_file):
        file_handler = xbmcvfs.File(cache_file, 'rb')
        content = generic_utility.decode(file_handler.read())
        file_handler.close()
    if not content:
        post_data = generic_utility.video_info % (video_id, video_id, video_id, video_id,
                                                  generic_utility.get_setting('authorization_url'))
        content = connect.load_netflix_site(generic_utility.evaluator(), post=post_data, lock = lock)
        file_handler = xbmcvfs.File(cache_file, 'wb')
        file_handler.write(generic_utility.encode(content))
        file_handler.close()
    return content


def series_info(series_id):
    content = ''
    cache_file = xbmc.translatePath(generic_utility.cache_dir() + series_id + '_episodes.cache')
    if xbmcvfs.exists(cache_file) and (time.time() - xbmcvfs.Stat(cache_file).st_mtime() < 60 * 5):
        file_handler = xbmcvfs.File(cache_file, 'rb')
        content = generic_utility.decode(file_handler.read())
        file_handler.close()
    if not content:
        url = generic_utility.series_url % (generic_utility.get_setting('api_url'), series_id)
        content = connect.load_netflix_site(url)
        file_handler = xbmcvfs.File(cache_file, 'wb')
        file_handler.write(generic_utility.encode(content))
        file_handler.close()
    return content


def cover_and_fanart(video_type, video_id, title, year):
    content = search.tmdb(video_type, title, year)
    if content['total_results'] > 0:
        content = content['results'][0]

        poster_path = content['poster_path']
        if poster_path:
            cover_url = generic_utility.picture_url + poster_path
            cover(video_id, cover_url)

        backdrop_path = content['backdrop_path']
        if backdrop_path:
            fanart_url = generic_utility.picture_url + backdrop_path
            fanart(video_id, fanart_url)


def fanart(video_id, fanart_url):
    filename = video_id + '.jpg'
    fanart_file = xbmc.translatePath(generic_utility.fanart_cache_dir() + filename)
    try:
        content_jpg = connect.load_other_site(fanart_url)
        file_handler = open(fanart_file, 'wb')
        file_handler.write(content_jpg)
        file_handler.close()
    except Exception:
        pass


def cover(video_id, cover_url):
    filename = video_id + '.jpg'
    filename_none = video_id + '.none'

    cover_file = xbmc.translatePath(generic_utility.cover_cache_dir() + filename)
    cover_file_none = xbmc.translatePath(generic_utility.cover_cache_dir() + filename_none)

    try:
        content_jpg = connect.load_other_site(cover_url)
        file_handler = open(cover_file, 'wb')
        file_handler.write(content_jpg)
        file_handler.close()
    except Exception:
        file_handler = open(cover_file_none, 'wb')
        file_handler.write('')
        file_handler.close()
        pass


def trailer(video_type, title):
    content = search.tmdb(video_type, title)
    if content['total_results'] > 0:
        content = content['results'][0]
        tmdb_id = content['id']
        content = search.trailer(video_type, tmdb_id)
    else:
        generic_utility.notification(generic_utility.get_string(30305))
        content = None
    return content


def genre_info(video_type):
    post_data = ''
    if video_type == 'tv':
        post_data = generic_utility.series_genre % generic_utility.get_setting('authorization_url')
    elif video_type == 'movie':
        post_data = generic_utility.movie_genre % generic_utility.get_setting('authorization_url')
    else:
        pass
    content = connect.load_netflix_site(generic_utility.evaluator(), post=post_data)
    return content


def search_results(search_string):
    post_data = '{"paths":[["search","%s",{"from":0,"to":48},["summary","title"]],["search","%s",["id","length",' \
                '"name","trackIds","requestId"]]],"authURL":"%s"}' % (search_string, search_string,
                                                                      generic_utility.get_setting('authorization_url'))
    content = connect.load_netflix_site(generic_utility.evaluator(), post=post_data)
    return content


def viewing_activity_info():
    content = connect.load_netflix_site(generic_utility.activity_url % (generic_utility.get_setting('api_url'),
                                                                        generic_utility.get_setting(
                                                                                   'authorization_url')))
    return content

def video_playback_info(video_ids):
    ids_str = ''
    for video_id in video_ids:
        ids_str+='"'+video_id+'",'
    ids_str = ids_str[:-1]
    post_data = generic_utility.video_playback_info % (ids_str, generic_utility.get_setting('authorization_url'))
    content = connect.load_netflix_site(generic_utility.evaluator(), post=post_data)
    return content
