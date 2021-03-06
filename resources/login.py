from __future__ import unicode_literals

import re
import xbmc
import xbmcgui

import connect
import profiles
from resources.utility import generic_utility





def login():
    login_progress = xbmcgui.DialogProgress()
    login_progress.create('Netflix', generic_utility.get_string(30200) + '...')
    generic_utility.progress_window(login_progress, 25, generic_utility.get_string(30201))
    content = connect.load_netflix_site(generic_utility.main_url + 'Login', new_session=True)
    if not 'Sorry, Netflix ' in content:
        match = re.compile('name="authURL" value="(.+?)"', re.DOTALL| re.UNICODE).findall(content)
#        utility.log('Setting authorization url: ' + match[0])
        generic_utility.set_setting('authorization_url', match[0])
        match = re.compile('locale: "(.+?)"', re.DOTALL|re.UNICODE).findall(content)
        generic_utility.set_setting('language', match[0])
        post_data = {'authURL': generic_utility.get_setting('authorization_url'), 'email': generic_utility.get_setting('username'),
                     'password': generic_utility.get_setting('password'), 'RememberMe': 'on'}
        generic_utility.progress_window(login_progress, 50, generic_utility.get_string(30202))
        content = connect.load_netflix_site(
            generic_utility.main_url + 'Login?locale=' + generic_utility.get_setting('language'),
            post=post_data)
#        utility.log(content)

        if 'id="page-LOGIN"' in content:
            generic_utility.notification(generic_utility.get_string(30303))
            return False
        match = re.compile('"apiUrl":"(.+?)",', re.UNICODE).findall(content)
        generic_utility.set_setting('api_url', match[0])

        connect.set_chrome_netflix_cookies()

        generic_utility.progress_window(login_progress, 75, generic_utility.get_string(30203))

        profile_selection()

        if login_progress:
            if not generic_utility.progress_window(login_progress, 100, generic_utility.get_string(30204)):
                return False
            xbmc.sleep(500)
            login_progress.close()
        return True
    else:
        generic_utility.notification(generic_utility.get_string(30300))
        if login_progress:
            login_progress.close()
        return False


def profile_selection():
    if not (
        generic_utility.get_setting('selected_profile') or (generic_utility.get_setting('single_profile') == 'true')):
        profiles.choose()
    elif not (generic_utility.get_setting('single_profile') == 'true') and (
        generic_utility.get_setting('show_profiles') == 'true'):
        profiles.choose()
    elif not ((generic_utility.get_setting('single_profile') and generic_utility.get_setting('show_profiles')) == 'true'):
        profiles.load()

