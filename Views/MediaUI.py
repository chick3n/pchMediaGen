import cherrypy
from mako.template import Template
from mako.lookup import TemplateLookup
import os
import threading
import logging
import datetime
from logger import logger
import json

#web
import Tv
import Movie

#data
import Content

LOCAL = os.path.dirname(os.path.realpath(__file__))

os.chdir(LOCAL)

lookup = TemplateLookup(directories=['templates'],
                        input_encoding='utf-8',
                        output_encoding='utf-8',
                        default_filters=['decode.utf8'],
                        encoding_errors='replace')


class MediaUI(object):
    content = Content.Content()

    def __init__(self):
        logging.basicConfig(filename='logs/session.log', level=logging.DEBUG
            , format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    @cherrypy.expose
    def index(self, page=0, sort='date', dir='desc', filter='all', search=None):

        try:
            current_page = int(page)
        except:
            current_page = 0

        #nextPage
        next_page = "?page=%s&sort=%s&dir=%s&filter=%s" % (str(current_page + 1),
                                                           'date' if str(sort) == 'date' else 'title',
                                                           'desc' if str(dir) == 'desc' else 'asc',
                                                           str(filter))

        #filters movie or tv or all
        movie_checked = ''

        if search is not None and search.__len__() > 0:
            next_page += "&search=" + search
        else:
            search = None

        if filter == 'movies':
            media_content = self.content.get_all_movie_content(page=current_page, order=sort, direction=dir, limit=50,
                                                               search=search)
            movie_checked = "checked='checked'"
        elif filter == 'tv':
            return self.tv(None, None, page, sort, dir, search)
        else:
            media_content = self.content.get_all_media_content(page=current_page, order=sort, direction=dir, limit=50,
                                                               search=search)

        tmpl = lookup.get_template("index.html")
        return tmpl.render(media=media_content,
                           nextPage=next_page,
                           searchContent=search,
                           movie_checked=movie_checked,
                           tv_checked='')

    @cherrypy.expose
    def movies(self, page=0, sort='date', dir='desc', search=''):
        return self.index(page, sort, dir, 'movies', search)

    @cherrypy.expose
    def tv(self, show=None, season=None, page=0, sort='date', dir='asc', search=''):
        try:
            current_page = int(page)
        except:
            current_page = 0

        try:
            current_show = int(show)
        except:
            current_show = None

        try:
            current_season = int(season)
        except:
            current_season = None

        tmpl = lookup.get_template("index.html")
        if current_show is not None and current_season is not None:
            # list of episodes for show
            media_content = self.content.get_episodes(current_show, current_season, page=current_page, direction=dir,
                                                      search=search)
            #nextPage
            next_page = "/tv?show=%s&season=%s&page=%s&sort=%s&dir=%s" % (str(current_show), str(current_season),
                                                                          str(current_page + 1),
                                                                          'date' if str(sort) == 'date' else 'title',
                                                                          'desc' if str(dir) == 'desc' else 'asc')
        else:
            media_content = self.content.get_all_tv_content(page=current_page, direction=dir, search=search)

            #nextPage
            next_page = "/tv?page=%s&sort=%s&dir=%s" % (str(current_page + 1),
                                                        'date' if str(sort) == 'date' else 'title',
                                                        'desc' if str(dir) == 'desc' else 'asc')

        if search is not None and search.__len__() > 0:
            next_page += "&search=" + search

        return tmpl.render(media=media_content, nextPage=next_page, searchContent=search,
                           movie_checked='', tv_checked="checked='checked'")

    @cherrypy.expose
    def media(self, type, id):
        data = {'status': 0}

        if type is None:
            return

        if type in ('movie', 'tv', 'anime',):
            tmpl = lookup.get_template("mediaDetails.html")
        elif type in ('show',):
            tmpl = lookup.get_template("seasons.html")
        else:
            return

        try:
            media_id = int(id)
        except Exception:
            return tmpl.render(media=data)

        data_content = None
        if str(type) == 'movie':
            data_content = self.content.get_movie(media_id)
        elif str(type) == 'tv':
            data_content = self.content.get_tv(media_id)
        elif str(type) == 'show':
            data_content = self.content.get_tv_seasons(media_id)
            data_content['last_added_episodes'] = self.content.get_episode_latest(show=media_id, limit=10)

        if data_content is not None:
            data.update(data_content)
            data['status'] = 1

        return tmpl.render(media=data)

    def stop(self):
        self.content.close()
        #close db


root = MediaUI()


def startService(new=True, redirect=False):
    cherrypy.config.update(config=os.path.join(LOCAL, 'config.conf'))
    cherrypy.tree.mount(root, '/', config=os.path.join(LOCAL, 'config.conf'))

    if hasattr(cherrypy.engine, "signal_handler"):
        cherrypy.engine.signal_handler.subscribe()
    if hasattr(cherrypy.engine, "console_control_handler"):
        cherrypy.engine.console_control_handler.subscribe()

    cherrypy.engine.subscribe('exit', root.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()


def stopService(kill=False, restart=False):
    cherrypy.engine.stop()

    if kill:
        killService();
        root.stop()
    elif restart:
        startService(redirect=True)


def killService():
    os.exit(0)


if __name__ == '__main__':
    startService(new=True, redirect=True)

