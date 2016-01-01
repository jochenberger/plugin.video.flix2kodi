﻿from __future__ import unicode_literals

import traceback
import xbmc
import xbmcgui

from resources import delete
from resources import general
from resources import library
from resources import list
from resources import login
from resources import play
from resources import profiles
from resources import queue
from resources import search
from resources.utility import generic_utility

# utility.log('\n\nStart of plugin')

while (generic_utility.get_setting('username') or generic_utility.get_setting('password')) == '':
    generic_utility.open_setting()

generic_utility.prepare_folders()

parameters = generic_utility.parameters_to_dictionary(sys.argv[2])
name = generic_utility.get_parameter(parameters, 'name')
url = generic_utility.get_parameter(parameters, 'url')
mode = generic_utility.get_parameter(parameters, 'mode')
thumb = generic_utility.get_parameter(parameters, 'thumb')
video_type = generic_utility.get_parameter(parameters, 'type')
season = generic_utility.get_parameter(parameters, 'season')
series_id = generic_utility.get_parameter(parameters, 'series_id')
page = generic_utility.get_parameter(parameters, 'page')
run_as_widget = generic_utility.get_parameter(parameters, 'widget') == 'true'

def handle_request():
    if mode == 'main':
        general.main(video_type)
    elif mode == 'list_videos':
        list.videos(url, video_type, page, run_as_widget)
    elif mode == 'list_seasons':
        list.seasons(name, url, thumb)
    elif mode == 'list_episodes':
        list.episodes(series_id, url)
    elif mode == 'list_genres':
        list.genres(video_type)
    elif mode == 'list_viewing_activity':
        list.viewing_activity(video_type, run_as_widget)
    elif mode == 'add_to_queue':
        queue.add(url)
    elif mode == 'remove_from_queue':
        queue.remove(url)
    elif mode == 'add_movie_to_library':
        library.movie(url, name)
    elif mode == 'add_series_to_library':
        library.series(series_id, name, url)
    elif mode == 'play_trailer':
        play.trailer(url, video_type)
    elif mode == 'update_displayed_profile':
        profiles.update_displayed()
    elif mode == 'search':
        search.netflix(video_type)
    elif mode == 'delete_cookies':
        delete.cookies()
    elif mode == 'delete_cache':
        delete.cache()
    elif mode == 'reset_addon':
        delete.addon()
    elif mode == 'play_video':
        #    utility.log('play_video: '+url)
        play.video(url);
    elif mode == 'play_video_main':
        #    utility.log('play_video_main: '+url)
        play.video(url);
    elif mode == 'relogin':
        login.login()
    else:
        general.index()


try:
    handle_request()
except:
    generic_utility.log('parameters: ' + sys.argv[2])
    generic_utility.log(traceback.format_exc(), xbmc.LOGERROR)
    dialog = xbmcgui.Dialog()
    do_fresh_login = dialog.yesno('Sorry', 'Flix2Kodi crashed.', 'Try to refresh your login?')
    if do_fresh_login:
        if login.login()==True:
            generic_utility.notification('Login refreshed. please try again.')
