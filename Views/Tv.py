import cherrypy
from mako.template import Template
from mako.lookup import TemplateLookup

from datetime import datetime, timedelta

from logger import logger
from Filter import Filter

lookup = TemplateLookup(directories=['templates'],
    input_encoding='utf-8',
    output_encoding='utf-8',
    default_filters=['decode.utf8'],
    encoding_errors='replace')

from math import ceil, floor
class Tv(object):
    def __init__(self, content):
        self.content = content

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect('/tv/show')

    def kill(self):
        self.content.close()

    @cherrypy.expose
    def added(self, page = 0, f=None):
        try:
            page = int(page)
        except:
            page = 0
        limit = 17

        filters = ()
        if f is not None:
            pFilter = Filter.ParseFilter(f)
            if pFilter is not None:
                filters += pFilter,

        episodes=self.content.get_latest_tv_html(page, limit, filters)
        total = self.content.get_total_items("episode e", "e.id", [ " inner join show s on s.id = e.show "], Filter("tv", {"episode": "e", "show": "s"}, filters))
        pPage = self.content.get_prev_page(page, limit, "episode", total)
        nPage = self.content.get_next_page(page, limit, "episode", total)
        filterLetters = self.content.get_available_letters("episode e", "s.title", [ " inner join show s on s.id = e.show "], None)
        tmpl = lookup.get_template("tv/added.html")

        return tmpl.render(episodes = episodes
            , prevPage = pPage
            , nextPage = nPage
            , totalPages = int(ceil(total/limit))
            , page = page
            , selected = Filter.getFilterValue(Filter.FILTER_LETTER, filters)
            , filterUrl = "f=" + (f if f is not None else '')
            , filterLetters = filterLetters)

    @cherrypy.expose
    def show(self, page=0, f = None):
        limit = 17
        try:
            page = int(page)
        except:
            page = 0

        filters = ()
        if f is not None:
            pFilter = Filter.ParseFilter(f)
            if pFilter is not None:
                filters += pFilter,

        content = self.content.get_tv_shows_html(page, limit, filters)

        total = self.content.get_total_items("show s", "s.id", None, Filter("tv", {"episode": "e", "show": "s"}, filters))
        prev = self.content.get_prev_page(page, limit, "episode", total)
        next = self.content.get_next_page(page, limit, "episode", total)
        content["total"] = int(ceil(total/limit))
        filterLetters = self.content.get_available_letters("show s", "s.title", None, None)

        tmpl = lookup.get_template("tv/show.html")
        return tmpl.render(content = content
            , prev = prev
            , next = next
            , selected = Filter.getFilterValue(Filter.FILTER_LETTER_EPISODE, filters)
            , filterUrl = "f=" + (f if f is not None else '')
            , filterLetters = filterLetters)

    @cherrypy.expose
    def season(self, id, page=0):
        limit = 17
        try:
            page = int(page)
        except:
            page = 0

        content = self.content.get_tv_season_html(id, page, limit)
        show = self.content.get_tv_show(id)
        total = len(show['show']['seasons'])
        prev = self.content.get_prev_page(page, limit, "episode", total)
        next = self.content.get_next_page(page, limit, "episode", total)
        show["page"] = page
        show["total"] = int(ceil(total / limit))

        tmpl = lookup.get_template("tv/season.html")
        return tmpl.render(content = content, show = show, prev = prev, next = next, total = total)

    @cherrypy.expose
    def episode(self, show = None, season = None, id = None, page=0, play='false', f = None, date = None):
        limit = 17
        try:
            page = int(page)
        except:
            page = 0

        if (show is None or season is None) and id is None:
            logger.error('episode', 'Tv.py', 'Call made to episode with no SHOW and SEASON and EPISODE')
            raise cherrypy.HTTPRedirect('/tv/show')
        elif (show is None or season is None) and id is not None:
            foundShowAndSeason = self.content.get_tv_show_and_season(id)
            if foundShowAndSeason and len(foundShowAndSeason) > 1:
                show = foundShowAndSeason[0]
                season = foundShowAndSeason[1]
            else:
                logger.error('episode', 'Tv.py', 'Call made to episode with no SHOW or SEASON, and could not find them with EPISODE %s', id)
                raise cherrypy.HTTPRedirect('/tv/show')

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
                        logger.warn('episode', 'Play request time < now - 60 (%s < %s).', str(callingDate), str(currentDate))
                except:
                    id = None
                    play = 'false'
                    logger.error('episode', 'Tv.py', 'Error converting UTC Javascript date for %s.', date)

        if id is not None:
            self.content.update_media_watched("tv",id)

        filter = ((Filter.FILTER_SHOWID, show), (Filter.FILTER_SEASON, season))
        if f is not None:
            pFilter = Filter.ParseFilter(f)
            if pFilter is not None:
                filter += pFilter,
                filter = Filter.ModifyFilter(Filter.FILTER_LETTER, filter, Filter.FILTER_LETTER_EPISODE, None) # we compare against episode here not show

        show = self.content.get_tv_show(show)
        episodes = self.content.get_tv_series_html(show, season, page, limit, filter)

        total = self.content.get_total_items("episode e", "e.id", [" inner join show s on s.id = e.show "], Filter("tv", {"episode": "e", "show": "s"}, filter))
        pPage = self.content.get_prev_page(page, limit, "episode", total)
        nPage = self.content.get_next_page(page, limit, "episode", total)

        tmpl = lookup.get_template("tv/episode.html")
        return tmpl.render(id = id
            , show = show["show"]
            , episodes = episodes
            , season = season
            , prevPage = pPage
            , nextPage = nPage
            , totalPages = int(ceil(total/limit))
            , page = page
            , play = play
            , selected = Filter.getFilterValue(Filter.FILTER_LETTER_EPISODE, filter)
            , urlPrefix = "?show={}&season={}&play=false&page=0&".format(show["show"]["id"], season)
            , filterUrl = "f=" + (f if f is not None else '')
            , filterLetters = set())


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
        total = self.content.get_total_items("episode e", "e.id", [" inner join show s on s.id = e.show "], Filter("tv", {"episode": "e", "show": "s"}, filter))
        pPage = self.content.get_prev_page(page, limit, "episode", total)
        nPage = self.content.get_next_page(page, limit, "episode", total)
        filterLetters = self.content.get_available_letters("episode e", "s.title", [ " inner join show s on s.id = e.show "], None)

        tmpl = lookup.get_template("tv/watchme.html")
        return tmpl.render(episodes=episodes
            , prevPage = pPage
            , nextPage = nPage
            , totalPages = int(ceil(total/limit))
            , page = page
            , selected = Filter.getFilterValue(Filter.FILTER_LETTER_EPISODE, filter)
            , filterUrl = "f=" + (f if f is not None else '')
            , filterLetters = filterLetters)