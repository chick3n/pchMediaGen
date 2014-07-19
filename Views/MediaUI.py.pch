import cherrypy
from mako.template import Template
from mako.lookup import TemplateLookup
import os
import threading
import logging
import datetime
from logger import logger

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
        self.tv = Tv.Tv(content=self.content)
        self.movies = Movie.Movie(content=self.content)
        logging.basicConfig(filename='logs/session.log', level=logging.DEBUG
            , format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    @cherrypy.expose
    def index(self, refresh = None):
        if refresh:
            logger.info('index', 'Refresh called, relinking DB thread.')
            self.content.close()
            self.content = Content.Content()
            self.tv.content = self.content
            self.movies.content = self.content
        tmpl = lookup.get_template("index.htm")
        return tmpl.render(episodes=self.content.get_latest_tv_html(0, 5)
            , movies=self.content.get_movies(0, 5, None, 'm.added DESC'))

    @cherrypy.expose
    def rebootPy(self):
        threading.Timer(1, lambda: stopService(restart=True)).start()
        return Template(filename='templates/exit.html').render(
            msg="Restarting the web service. <br>Refresh will start in <div id='countdown'>30 seconds.</div>"
            , redirect='/index')


    @cherrypy.expose
    def shutdownPy(self):
        threading.Timer(3, lambda: stopService(kill=True)).start()
        return Template(filename='templates/exit.html').render(msg="Shutting down web service.")

    def stop(self):
        self.content.close() #close db

root = MediaUI()

def startService(new=True, redirect=False):
    cherrypy.config.update(config=os.path.join(LOCAL,'config.conf'))
    cherrypy.tree.mount(root, '/', config=os.path.join(LOCAL,'config.conf'))

    if hasattr(cherrypy.engine, "signal_handler"):
        cherrypy.engine.signal_handler.subscribe()
    if hasattr(cherrypy.engine, "console_control_handler"):
        cherrypy.engine.console_control_handler.subscribe()

    cherrypy.engine.subscribe('exit',  root.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()

def stopService(kill=False, restart=False):
    cherrypy.engine.stop()

    if kill: killService(); root.stop()
    elif restart: startService(redirect=True)

def killService():
    os.exit(0)


if __name__ == '__main__':
    startService(new=True, redirect=True)

