import sqlite3 as lite
import db
import re
from datetime import date, timedelta, datetime
from math import ceil, floor
import cgi
from Filter import Filter

class Content(object):
    def __init__(self):
        super(Content,self).__init__()
        self.db = "../media.sqlite"
        self.sql = db.MultiThreadOK(self.db)

    def close(self):
        self.sql.kill()

    def convert_runtime_seconds(self, seconds):
        if seconds is None:
            return "-"

        hours, minutes = divmod(int(seconds), 60)

        return "%s hour and %s minutes" % (hours, minutes)

    def strip_year_from_date(self, date):
        if date is None:
            return ""

        return re.match('([0-9]{4})', date).group()

    def convert_date_to_dayssince(self, added):
        if added is None:
            return ""

        if isinstance(added, str) or isinstance(added, unicode):
            try:
                if "." in added:
                    added = datetime.strptime(added, '%Y-%m-%d %H:%M:%S.%f')
                else:
                    added = datetime.strptime(added, '%Y-%m-%d %H:%M:%S')
            except:
                return "?"

        delta = datetime.today() - added
        if delta.days > 365:
            return "%s y" % int(floor(delta.days / 365))
        elif delta.days > 30:
            return "%s m" % int(floor(delta.days / 30))

        return "%s d" % delta.days

    def convert_watched_to_dayssince(self, watched):
        if watched is None:
            return ""

        if isinstance(watched, str) or isinstance(watched, unicode):
            try:
                if "." in watched:
                    watched = datetime.strptime(watched, '%Y-%m-%d %H:%M:%S.%f')
                else:
                    watched = datetime.strptime(watched, '%Y-%m-%d %H:%M:%S')
            except:
                return "?"

        delta = datetime.now() - watched
        if delta.days > 365:
            return "%s y" % int(floor(delta.days / 365))
        elif delta.days > 30:
            return "%s m" % int(floor(delta.days / 30))

        return "%s d" % delta.days

    def get_available_letters(self, _from, _select, _joins = None, _filters = None, _groups = None, _limits = None):
        sql = "select %s from %s" % (_select, _from)

        if _joins is not None:
            sql += " ".join(_joins)

        if _filters is not None:
            sql += _filters.genFilter()

        results = self.sql.select(sql)

        letters = set()
        for result in results:
            if result[0] is None:
                continue
            if result[0][0].isalpha():
                letters.add(result[0][0].upper())
            else: letters.add('#')

        return sorted(letters)

    def get_total_items(self, _from, _select, _joins = None, _filters = None, _groups = None, _limits = None):
        sql = "select count(%s) from %s" % (_select, _from)

        if _joins is not None:
            sql += " ".join(_joins)

        if _filters is not None:
            sql += _filters.genFilter()

        results = self.sql.select(sql)

        total = 0
        for result in results:
            total = result[0]
            break

        return total

    def get_next_page(self, page, limit, column, total = None):
        if page >= 0 and ((page + 1)*limit) <= total:
            return page+1

        return 0

    def get_prev_page(self, page, limit, column, total = None):
        if (page - 1) >= 0 and ((page - 1) * limit) <= total:
            return page - 1

        return int(ceil(total / limit))


    def get_latest_tv_html(self, page = 0, limit = 5, filter = None):
        episodes = self.get_latest_tv(page, limit, filter)

        html = []

        for episode in episodes:
            show = episode["show"]
            if episode["episode"] is not None and int(episode["episode"]) < 10:
                episode["episode"] = "0" + str(episode["episode"])
            title = episode["file_name"] if episode["title"] is None else "%s. %s" % (episode["episode"], episode["title"])
            desc = episode["desc"] if not episode["desc"] is None else ""
            path = "file:///opt/sybhttpd/localhost.drives/NETWORK_SHARE/mediaui/Tv/%s" % (episode["full_path"])
            fanart = episode["fanart"] if not episode["fanart"] is None else "tv_fanart.png"
            season = episode["season"]
            added = self.convert_date_to_dayssince(episode["added"])
            showsmall = "".join(item[0].upper() for item in show.split())
            fullshow = episode["show"]

            watchedicon = "/images/unwatched.png" if episode["watched"] is None else "/images/watched.png"
            watcheddate = self.convert_watched_to_dayssince(episode["watched"])

            fulltitle = title

            if desc.__len__() > 300:
                desc = desc[:300] + "..."

            if title.__len__() > 30:
                title = title[:30] + "..."

            if show.__len__() > 10:
                show = show[:10] + "..."

            html.append((show
                         , title
                         , path
                         , desc
                         , fanart
                         , season
                         , added
                         , showsmall
                         , fullshow
                         , watchedicon
                         , watcheddate
                         , episode["id"]
                         , fulltitle
                ))

        return html

    def get_latest_tv_added(self, limit = 5):
        pass

    def get_latest_tv(self, page = 0, limit = 5, _filter = None):
        sql = """
            select s.title, e.season, e.episode, e.title, e.full_path, e.file_name, e.description, e.added
            ,s.fanart, s.banner, s.poster, datetime(e.watched, 'localtime'), e.id
            from episode e
            inner join show s on s.id = e.show
            """

        if _filter is not None:
            f = Filter("tv", {"episode": "e", "show": "s"})
            sql += f.genFilter(_filter)

        sql += """
            order by added desc
            limit ?, ?"""

        episodes = self.sql.select(sql,(page*limit,limit,))
        content = []

        for episode in episodes:
            content.append(
                {"show": episode[0]
                    , "season": episode[1]
                    , "episode": episode[2]
                    , "title": episode[3]
                    , "full_path": episode[4]
                    , "file_name": episode[5]
                    , "desc": episode[6]
                    , "added": episode[7]
                    , "fanart": episode[8]
                    , "banner": episode[9]
                    , "poster": episode[10]
                    , "watched": episode[11]
                    , "id": episode[12]
                }
            )

        return content


    def update_media_watched(self, type, id):
        sql = ""
        if type == "tv":
            sql = """
            UPDATE episode SET watched = datetime('now') WHERE id = ?
            """
        elif type == "movie":
            sql = """
            UPDATE movie SET watched = datetime('now') WHERE id = ?
            """
        else:
            return

        self.sql.execute(sql,(id,))
        self.sql.execute("COMMIT")

        return


    def get_tv_html(self, id):
        sql = """
            SELECT s.title, e.season, e.episode, e.title, e.full_path, e.file_name, e.description, e.added
            ,s.fanart, s.banner, s.poster, datetime(e.watched, 'localtime'), e.id, e.show
            from episode e
            inner join show s on s.id = e.show
            WHERE e.id = ?"""

        content = self.sql.select(sql, (id,))

        episode = {}
        for item in content:
            episode["show"] = item[0]
            episode["showmall"] = "".join(item[0].upper() for item in item[0].split())
            episode["season"] = item[1]
            episode["episode"] = item[2]
            if episode["episode"] is not None and int(episode["episode"]) < 10:
                episode["episode"] = "0" + str(episode["episode"])

            episode["file_name"] = item[5]
            episode["title"] = episode["file_name"] if item[3] is None else "%s. %s" % (episode["episode"], item[3])
            episode["desc"] = item[6] if not item[6] is None else ""
            episode["path"] = "file:///opt/sybhttpd/localhost.drives/NETWORK_SHARE/mediaui/Tv/%s" % (item[4])
            episode["fanart"] = item[8] if not item[8] is None else "tv_fanart.png"
            episode["added"] = self.convert_date_to_dayssince(item[7])
            episode["banner"] = item[9]
            episode["poster"] = item[10]
            episode["watchedicon"] = "/images/unwatched.png" if item[11] is None else "/images/watched.png"
            episode["watcheddate"] = self.convert_watched_to_dayssince(item[11])
            episode["id"] = item[12]
            episode["showid"] = item[13]
            episode["fulltitle"] = episode["title"]
            break

        if episode["desc"].__len__() > 300:
            episode["desc"] = episode["desc"][:300] + "..."

        if episode["title"].__len__() > 30:
            episode["title"] = episode["title"][:30] + "..."


        return episode

    def get_tv_series_html(self, show, season = None, page = 0, limit = 5, filter = None):
        episodes = self.get_tv_series(show, season, page, limit, filter)

        html = []

        for episode in episodes:
            show = episode["show"]
            if episode["episode"] is not None and int(episode["episode"]) < 10:
                episode["episode"] = "0" + str(episode["episode"])
            title = episode["file_name"] if episode["title"] is None else "%s. %s" % (episode["episode"], episode["title"])
            desc = episode["desc"] if not episode["desc"] is None else ""
            path = "file:///opt/sybhttpd/localhost.drives/NETWORK_SHARE/mediaui/Tv/%s" % (episode["full_path"])
            fanart = episode["fanart"] if not episode["fanart"] is None else "tv_fanart.png"
            season = episode["season"]
            added = self.convert_date_to_dayssince(episode["added"])
            showsmall = "".join(item[0].upper() for item in show.split())
            fullshow = episode["show"]

            watchedicon = "/images/unwatched.png" if episode["watched"] is None else "/images/watched.png"
            watcheddate = self.convert_watched_to_dayssince(episode["watched"])

            fulltitle = title

            if desc.__len__() > 300:
                desc = desc[:300] + "..."

            if title.__len__() > 30:
                title = title[:30] + "..."

            if show.__len__() > 10:
                show = show[:10] + "..."

            html.append((show
                         , title
                         , path
                         , desc
                         , fanart
                         , season
                         , added
                         , showsmall
                         , fullshow
                         , watchedicon
                         , watcheddate
                         , episode["id"]
                         , fulltitle
                ))

        return html

    def get_tv_series(self, show, season = None, page = 0, limit = 5, filter = None):
        sql = """
                select s.title, e.season, e.episode, e.title, e.full_path, e.file_name, e.description, e.added
                ,s.fanart, s.banner, s.poster, datetime(e.watched, 'localtime'), e.id
                from episode e
                inner join show s on s.id = e.show
                """

        if filter is not None:
            _f = Filter("tv", {"episode": "e", "show": "s"})
            sql += _f.genFilter(filter)

        sql += " order by e.episode asc limit ?, ?"

        episodes = self.sql.select(sql,((page * limit), limit,))
        content = []

        for episode in episodes:
            content.append(
                {"show": episode[0]
                    , "season": episode[1]
                    , "episode": episode[2]
                    , "title": episode[3]
                    , "full_path": episode[4]
                    , "file_name": episode[5]
                    , "desc": episode[6]
                    , "added": episode[7]
                    , "fanart": episode[8]
                    , "banner": episode[9]
                    , "poster": episode[10]
                    , "watched": episode[11]
                    , "id": episode[12]
                }
            )

        return content

    def get_tv_shows_html(self, page = 0, limit = 5, f = None):
        sql = """
                SELECT s.title, s.fanart
                , (select count(e.id) from episode e where e.show = s.id)
                , (select group_concat(distinct e2.season) from episode e2 where e2.show = s.id)
                , s.id
                , (select MAX(e3.added) from episode e3 where e3.show = s.id order by e3.added DESC)
                FROM show s
              """

        if f is not None:
            _f = Filter("tv", {"episode": None, "show": "s"})
            sql += _f.genFilter(f)

        sql += " ORDER BY s.title ASC LIMIT ?, ?"

        results = self.sql.select(sql, (page*limit, limit,))

        content = {
            "shows": []
            , "total": 0
            , "page": page
        }

        for result in results:
            content["shows"].append(
                {
                    "fulltitle": result[0] #title
                    , "fanart": result[1] if result[1] is not None else "tv_fanart.png" #fanart
                    , "epscount": result[2] #episode count
                    , "shorttitle": result[0][:30]
                    , "seasons": sorted(result[3].split(","), key=int) if result[3] is not None else ""
                    , "id": result[4]
                    , "lastadded": self.convert_date_to_dayssince(result[5])
                }
            )

        return content

    def get_tv_season_html(self, id, page=0, limit=5):
        sql = """
                select e.season
                 , (select count(e2.id) from episode e2 where e2.season = e.season and e2.show = e.show)
                 , (select MAX(e3.added) from episode e3 where e3.show = e.show and e3.season = e.season order by e3.added DESC)
                from episode e
                where e.show = ? and e.season is not null
                group by e.season
                order by e.season asc
                limit ?, ?
            """
        sql2 = "select count(e.id) from episode e where e.show = ? and e.season is null"

        results = self.sql.select(sql, (id, page*limit, limit,))

        content = []
        for result in results:
            content.append((result[0], result[1], self.convert_date_to_dayssince(result[2])))

        results = self.sql.select(sql2, (id,))

        for result in results:
            if result[0] > 0:
                content.append((-1, result[0], ''))
            break

        return content

    def get_tv_show_and_season(self, eps):
        sql = """
                SELECT s.id, e.season FROM episode e
                INNER JOIN show s on s.id = e.show
                WHERE e.id = ?
                LIMIT 1
            """
        results = self.sql.select(sql, (eps,))
        content = ()
        for result in results:
            content = (result[0], result[1],)

        return content

    def get_tv_show(self, id):
        sql = """
                    SELECT s.title, s.fanart
                    , (select count(e.id) from episode e where e.show = s.id)
                    , (select group_concat(distinct e2.season) from episode e2 where e2.show = s.id)
                    , s.id
                    , (select MAX(e3.added) from episode e3 where e3.show = s.id order by e3.added DESC)
                    FROM show s
                    WHERE s.id = ?
                """

        results = self.sql.select(sql, (id,))

        content = {
            "show": {}
            , "total": 0
            , "page": 0
        }

        for result in results:
            content["show"] = {
                    "fulltitle": result[0] #title
                    , "fanart": result[1] if result[1] is not None else "tv_fanart.png" #fanart
                    , "epscount": result[2] #episode count
                    , "shorttitle": result[0][:30]
                    , "seasons": sorted(result[3].split(","), key=int)
                    , "id": result[4]
                    , "lastadded": self.convert_date_to_dayssince(result[5])
                }

        return content

    def get_movies(self, page = 0, limit = 5, filter = None, order = 'm.title ASC'):
        sql = "select m.title, m.description, m.airdate, m.full_path, m.parent_dir, m.added, m.id, datetime(m.watched, 'localtime'), m.runtime, m.poster from movie m"

        if filter is not None:
            _f = Filter("movie", {"movie": "m"})
            sql += _f.genFilter(filter)

        sql += " ORDER BY %s LIMIT ?, ?" % order

        movies = self.sql.select(sql, (page * limit, limit,))

        html = []
        for movie in movies:
            content = {}
            content["id"] = movie[6]
            content["title"] = movie[0] if movie[0] is not None else movie[4]
            content["desc"] = movie[1] if not movie[1] is None else ""
            content["path"] = "file:///opt/sybhttpd/localhost.drives/NETWORK_SHARE/mediaui/Movies/%s" % (movie[3])
            content["fanart"] = movie[9] if movie[9] is not None else "movie_fanart.png"
            content["added"] = self.convert_date_to_dayssince(movie[5])
            content["watchedicon"] = "/images/unwatched.png" if movie[7] is None else "/images/watched.png"
            content["watcheddate"] = self.convert_watched_to_dayssince(movie[7])
            content["fulltitle"] = content["title"]
            content["runtime"] = self.convert_runtime_seconds(movie[8])
            content["year"] = self.strip_year_from_date(movie[2])

            if content["desc"].__len__() > 300:
                content["desc"] = content["desc"][:300] + "..."

            if content["title"].__len__() > 30:
                content["title"] = content["title"][:30] + "..."

            html.append(content)

        return html