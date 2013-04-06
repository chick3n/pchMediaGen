import cherrypy
from mako.lookup import TemplateLookup
from logger import logger

from datetime import datetime, timedelta

from Filter import Filter

lookup = TemplateLookup(directories=['templates'],
    input_encoding='utf-8',
    output_encoding='utf-8',
    default_filters=['decode.utf8'],
    encoding_errors='replace')

from math import ceil
class Movie(object):
    def __init__(self, content):
        self.content = content

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect('/movies/movie')

    def kill(self):
        self.content.close()

    @cherrypy.expose
    def added(self, id = None, page=0, play='false', f = None, date = None, dir = None):
        try:
            page = int(page)
        except:
            page = 0
        limit = 17

        if play == 'true' and id is not None:
            if date is None:
                id = None
                play = 'false'
            else:
                try:
                    callingDate = datetime.strptime(date, "%a %b %d %H:%M:%S %Y %Z")
                    currentDate = datetime.utcnow() - timedelta(seconds = 60)
                    # Sat Feb 23 19:35:57 2013 GMT popcorn hour example call
                    #callingDate = datetime.utcfromtimestamp(date)
                    if callingDate < currentDate:
                        id = None
                        play = 'false'
                        logger.warn('added', 'Play request time < now - 60 (%s < %s).', str(callingDate), str(currentDate))
                except:
                    id = None
                    play = 'false'
                    logger.error('added', 'Movie.py', 'Error converting UTC Javascript date for %s.', date)

        if id is not None:
            self.content.update_media_watched("movie",id)

        filters = ()
        if f is not None:
            pFilter = Filter.ParseFilter(f)
            if pFilter is not None:
                filters += pFilter,

        movies=self.content.get_movies(page, limit, filters, 'm.added DESC')
        total = self.content.get_total_items("movie m", "m.id", None, Filter("movie", {"movie": "m"}, filters))
        pPage = self.content.get_prev_page(page, limit, "movie", total)
        nPage = self.content.get_next_page(page, limit, "movie", total)
        filterLetters = self.content.get_available_letters("movie m", "m.file_name", None, None)
        tmpl = lookup.get_template("movies/movies.html")

        startOn = 'moviename_0'
        if id is not None and play == 'true':
            startOn = 'movieid_' + id
        elif dir is not None:
            startOn = 'moviename_' + str(len(movies)-1)

        return tmpl.render(movies = movies
            , prevPage = pPage
            , nextPage = nPage
            , totalPages = int(ceil(total/limit))
            , page = page
            , play = play
            , selected = Filter.getFilterValue(Filter.FILTER_LETTER, filters)
            , filterUrl = "f=" + (f if f is not None else '')
            , filterLetters = filterLetters
            , pageName = 'added'
            , id = id
            , startOn = startOn)

    @cherrypy.expose
    def movie(self, id = None, page=0, play='false', f = None, date = None, dir = None):
        limit = 17
        try:
            page = int(page)
        except:
            page = 0

        if play == 'true' and id is not None:
            if date is None:
                id = None
                play = 'false'
            else:
                try:
                    callingDate = datetime.strptime(date, "%a %b %d %H:%M:%S %Y %Z")
                    currentDate = datetime.utcnow() - timedelta(seconds = 60)
                    # Sat Feb 23 19:35:57 2013 GMT popcorn hour example call
                    #callingDate = datetime.utcfromtimestamp(date)
                    if callingDate < currentDate:
                        id = None
                        play = 'false'
                        logger.warn('movie', 'Play request time < now - 60 (%s < %s).', str(callingDate), str(currentDate))
                except:
                    id = None
                    play = 'false'
                    logger.error('movie', 'Movie.py', 'Error converting UTC Javascript date for %s.', date)

        if id is not None:
            self.content.update_media_watched("movie",id)

        filter = ()
        if f is not None:
            pFilter = Filter.ParseFilter(f)
            if pFilter is not None:
                filter += pFilter,

        movies = self.content.get_movies(page, limit, filter, 'm.parent_dir ASC')
        total = self.content.get_total_items("movie m", "m.id", None, Filter("movie", {"movie": "m"}, filter))
        pPage = self.content.get_prev_page(page, limit, "movie", total)
        nPage = self.content.get_next_page(page, limit, "movie", total)
        filterLetters = self.content.get_available_letters("movie m", "m.file_name", None, None)

        startOn = 'moviename_0'
        if id is not None and play == 'true':
            startOn = 'movieid_' + id
        elif dir is not None:
            startOn = 'moviename_' + str(len(movies)-1)


        tmpl = lookup.get_template("movies/movies.html")
        return tmpl.render(movies = movies
            , prevPage = pPage
            , nextPage = nPage
            , totalPages = int(ceil(total/limit))
            , page = page
            , selected = Filter.getFilterValue(Filter.FILTER_LETTER, filter)
            , filterUrl = "f=" + (f if f is not None else '')
            , filterLetters = filterLetters
            , play = play
            , pageName = 'movie'
            , id = id
            , startOn = startOn)

    @cherrypy.expose
    def watchme(self, page=0, f=None):
        try:
            page = int(page)
        except:
            page = 0
        limit = 17
        filter = ((Filter.FILTER_NOTSEEN, ),)
        if f is not None:
            pFilter = Filter.ParseFilter(f)
            if pFilter is not None:
                filter += pFilter,

        episodes=self.content.get_latest_tv_html(page, limit, filter)
        total = self.content.get_total_items("episode e", "e.id", [" inner join show s on s.id = e.show "], filter)
        pPage = self.content.get_prev_page(page, limit, "episode", total)
        nPage = self.content.get_next_page(page, limit, "episode", total)
        filterLetters = self.content.get_available_letters("episode e", "s.title", [ " inner join show s on s.id = e.show "], filter)

        tmpl = lookup.get_template("tv/watchme.html")
        return tmpl.render(episodes=episodes
            , prevPage = pPage
            , nextPage = nPage
            , totalPages = int(ceil(total/limit))
            , page = page
            , selected = Filter.getFilterValue(Filter.FILTER_LETTER_EPISODE, filter)
            , filterUrl = "f=" + (f if f is not None else '')
            , filterLetters = filterLetters)