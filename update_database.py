import sqlite3 as lite
import constants
import re
import tvdb_api
import tvdb_exceptions as te
import datetime
import urllib
import os
import PIL
from PIL import Image
import tmdb
import difflib
from logger import logger
import globals

def updateDB(conn, cur, type):
    if conn is None:
        return None
    if cur is None:
        cur = conn.cursor()

    added = []

    if type == constants.__TYPE_TV:
        logger.info('MEDIA_INFO', 'TV MEDIA_INFO BEGIN')
        added = beginTVParse(cur)
        logger.info('MEDIA_INFO', 'TV MEDIA_INFO END')

        logger.info('FANART', 'TV FANART BEGIN')
        updateFanartTV(cur)
        logger.info('FANART', 'TV FANART END')
    elif type == constants.__TYPE_MOVIE:
        logger.info('MEDIA_INFO', 'MOVIE MEDIA_INFO BEGIN')
        added = beginMovieParse(cur)
        logger.info('MEDIA_INFO', 'MOVIE MEDIA_INFO END')

        logger.info('FANART', 'MOVIE FANART BEGIN')
        updateFanartMovie(cur, conn)
        logger.info('FANART', 'MOVIE FANART END')

    conn.commit()
    return added

def updateFanartMovie(cur, conn): #posters only for now
    cur.execute("select id, tmdbid, title from movie where poster is null and mediaupdated is null and tmdbid is not null")
    movies = cur.fetchall()

    tmdb.configure('1c6f8a30ad219e30992ea75911f8f9d5')

    for movie in movies:
        #check if already exists due to crashing and no DB commits happening during this whole process. Not a good idea.
        #fix later
        if os.path.isfile(globals.local_script_path + 'Views/images/movie/' + movie[1] + '_poster.jpg'):
            cur.execute("UPDATE movie SET poster = ?, mediaupdated = date('now') WHERE id = ?", (movie[1] + '_poster.jpg', movie[0],))
            conn.commit()
            continue
        elif os.path.isfile(globals.local_script_path + 'Views/images/movie/' + movie[1] + '_poster.png'):
            cur.execute("UPDATE movie SET poster = ?, mediaupdated = date('now') WHERE id = ?", (movie[1] + '_poster.png', movie[0],))
            conn.commit()
            continue

        minfo = tmdb.Movie(movie[1])

        if not minfo:
            logger.warn('updateFanartMovie', 'TMDB returned no results for \"%s\" [%s]', movie[2], movie[0])
            cur.execute("UPDATE movie SET mediaupdated = date('now') WHERE id = ?", (movie[0],))
            conn.commit()
            continue

        poster = None
        try:
            poster = minfo.get_poster()
        except:
            logger.error('updateFanartMovie', 'update_database.py', 'TMDB crashed retrieving poster for \"%s\" [%s]', movie[2], movie[0])
            cur.execute("UPDATE movie SET mediaupdated = date('now') WHERE id = ?", (movie[0],))
            conn.commit()
            continue

        if not poster:
            logger.info('updateFanartMovie', 'TMDB has no poster for \"%s\" [%s]', movie[2], movie[0])
            cur.execute("UPDATE movie SET mediaupdated = date('now') WHERE id = ?", (movie[0],))
            conn.commit()
            continue

        url = poster
        ext = os.path.splitext(url)[1]
        poster_file_name = movie[1] + '_poster' + ext

        try:
            urllib.urlretrieve(url, globals.local_script_path + 'Views/images/movie/' + poster_file_name)
        except Exception, e:
            logger.error('updateFanartMovie', 'update_database.py', str(e))
            continue

        # no need to resize any more since not running on PCH but through phone/tablet browser
        #try:
        #    img = Image.open(globals.local_script_path + 'Views/images/movie/' + poster_file_name)
        #    img = img.resize((228, 342), PIL.Image.ANTIALIAS)
        #    img.save(globals.local_script_path + 'Views/images/movie/' + poster_file_name)
        #except Exception, e:
        #    if os.path.isfile(globals.local_script_path + 'VIews/images/movie/' + poster_file_name):
        #        os.remove(globals.local_script_path + 'Views/images/movie' + poster_file_name)
        #        # remove file if partially created.
        #    logger.error('updateFanartMovie', 'update_database.py',
        #                 'PIL crashed on image resize for poster \"%s\" [%s]',
        #                 movie[2], movie[0])
        #    logger.error('updateFanartMovie', 'update_database.py', str(e))

        cur.execute("UPDATE movie SET poster = ?, mediaupdated = date('now') WHERE id = ?",
                    (poster_file_name, movie[0],))
        conn.commit()
        logger.info('FANART', 'TMDB returned poster %s which has been added for \"%s\"', poster_file_name, movie[2])


def updateFanartTV(cur):
    cur.execute("select title, fanart, id from show where fanart is null and updated is null")
    shows = cur.fetchall()

    tvdb = tvdb_api.Tvdb(banners=True)

    for show in shows:
        banners = None

        try:
            banners = tvdb[show[0]]['_banners']
        except:
            logger.warn('updateFanartTv', 'TVDB returned no result for \"%s\"', show[0])
            #update the database so we dont see this again for the same movie each iteration
            cur.execute("update show set updated = date('now') WHERE id = ?", (show[2],))
            continue

        if 'fanart' not in banners.keys():
            continue

        fanart = None
        key = None

        #determine first size choice
        if '1920x1080' in banners['fanart']: key = '1920x1080'
        elif '1280x720' in banners['fanart']: key = '1280x720'
        else:
            logger.warn('updateFanartTv', 'TVDB returned no fanart results for accepted sizes {%s}', '1920x1080, 1280x720')
            #update the database so we dont see this again for the same movie each iteration
            cur.execute("update show set updated = date('now') WHERE id = ?", (show[2],))
            continue #change this to just choose next best

        fanart = None
        fanart_rating = -1.0
        for art in banners['fanart'][key].iteritems():
            keys = art[1].keys()

            if not 'rating' in keys or not 'language' in keys:
                continue #no rating or language options available.
            if art[1]['language'] != 'en': continue #english only art
            if float(art[1]['rating']) > fanart_rating:
                fanart = art[1]

        #download fanart
        if fanart is not None:
            url = fanart['_bannerpath']
            ext = os.path.splitext(url)[1]
            fanart_file_name = str(show[2]) + '_fanart' + ext
            #f.open(show[0].lower().replace(' ', '') + '_fanart')
            #f.write(urllib.urlopen(url).read())
            #f.close()

            urllib.urlretrieve(url, globals.local_script_path + 'Views/images/tv/' + fanart_file_name)

            # no need to resize any more since not running on PCH but through phone/tablet browser
            #img = Image.open(globals.local_script_path + 'Views/images/tv/' + fanart_file_name)
            #img = img.resize((608,340), PIL.Image.ANTIALIAS)
            #img.save(globals.local_script_path + 'Views/images/tv/' + fanart_file_name)
            cur.execute("UPDATE show SET fanart = ? WHERE id = ?", (fanart_file_name, show[2],))
            logger.info('FANART', 'TVDB returned fanart %s which has been added for \"%s\"', fanart_file_name, show[0])
        else:
            cur.execute("update show set updated = date('now') WHERE id = ?", (show[2],))
            logger.info('FANART', 'TVDB returned no fanart for \"%s\"', show[0])


def beginMovieParse(cur):
    updateList = []
    returnList = []

    updateCount = 100
    updated = datetime.datetime.now().strftime("%Y-%m-%d")
    filterWords = r"(.*)proper|sample|repack|extended(\scut)?|dual audio|unrated|rerip|limited|\bdc\b|uncut"

    pass1 = re.compile(r'(?i)(.*?)(?=[0-9]{4}(?!p))\(?([0-9]{4})\)?')
    pass2 = re.compile(r'(?i)(.*?)(?=[0-9]{3,})(?!p)')

    cur.execute('select id, file_name, parent_dir, sub_dir from movie where updated is NULL')
    movie_list = cur.fetchall()

    tmdb.configure('1c6f8a30ad219e30992ea75911f8f9d5')

    for row in movie_list:
        filename = row[1]
        parentdir = row[2]
        id = row[0]

        results = None
        data = {'id': id, 'title': None, 'year': None, 'desc': None, 'year': None, 'aired': None, 'updated': updated
                , "runtime": None, "imdb": None, "tmdb": None}
        searchTitle = None
        searchYear = None

        #first pass
        results = pass1.search(parentdir)
        if results:
            searchTitle = results.group(1)
            searchYear = results.group(2)
        else:
            results = pass2.search(parentdir)
            if results:
                searchTitle = results.group(1)
                searchYear = None

        if searchTitle is not None:
            searchTitle = searchTitle.lower().replace('.', ' ')
            searchTitle = re.sub(filterWords, '', searchTitle, 1, flags=re.IGNORECASE) #reverse removal
            searchTitle = searchTitle.strip()

            movies = tmdb.Movies(searchTitle, limit = True)

            movieResult = None
            if movies:
                for  movie in movies:
                    if movie.get_title().lower() == searchTitle:
                        if searchYear and movie.get_release_date() is not None:
                            movieYear = re.match('[0-9]{4}', movie.get_release_date()).group()
                            if movieYear != searchYear:
                                continue
                        movieResult = movie
                        break

                if not movieResult: #diff search
                    l = [x.get_title() for x in movies]
                    d = difflib.get_close_matches(searchTitle, l, 1, 0)
                    if len(d) > 0:
                        for movie in movies:
                            if movie.get_title() == d[0]:
                                movieResult = movie
                                break

                if not movieResult: #just pick first result if exists
                    if movies.get_total_results() > 0:
                        movieResult = movies.__iter__().next()


                if movieResult:
                    data["title"]= movieResult.get_title()
                    data["year"] = movieResult.get_release_date()
                    data["aired"] = movieResult.get_release_date()
                    data["tmdb"] = movieResult.get_id()
                    data["imdb"]= movieResult.get_imdb_id()
                    data["desc"] = movieResult.get_overview()
                    data["runtime"] = movieResult.get_runtime()

                    if data["desc"] and len(data["desc"]) > 0:
                        data["desc"] = data["desc"].replace('\n', '')

                    updateList.append((
                        data["title"]
                        , data["year"]
                        , data["aired"]
                        , data["tmdb"]
                        , data["imdb"]
                        , data["desc"]
                        , data["runtime"]
                        , data["id"]
                    ))

                    returnList.append(data["title"])

                    logger.info('MEDIA_INFO', 'TMDB scrapped data for \"%s\" @ \"%s\".'
                        , data['title']
                        , parentdir)
                else:
                    logger.warn('MEDIA_INFO', 'TMDB found no matching results for \"%s\".\nTMDB was sent %s and returned a list of %s'
                        , parentdir
                        , searchTitle
                        , ','.join([x.get_title() for x in movies]))
                    #update the database so we dont see this again for the same movie each iteration
                    cur.execute("update movie set updated = date('now') WHERE id = ?", (data['id'],))

                    returnList.append(parentdir)
            else:
                logger.warn('MEDIA_INFO', 'TMDB returned a null object for \"%s\". RAW = %s', searchTitle, parentdir)
                #update the database so we dont see this again for the same movie each iteration
                cur.execute("update movie set updated = date('now') WHERE id = ?", (data['id'],))
                returnList.append(parentdir)
        else:
            logger.error('beginMovieParse', 'update_database.py', 'We were unable to parse a title out of \"%s\"', parentdir)
            #update the database so we dont see this again for the same movie each iteration
            cur.execute("update movie set updated = date('now') WHERE id = ?", (data['id'],))
            returnList.append(parentdir)

        if len(updateList) > 40:
            cur.executemany("update movie set title = ?, year = ?, airdate = ?, tmdbid = ?, imdbid = ?, description = ?, runtime = ?, updated = date('now') WHERE id = ?", updateList)
            updateList = []

    if len(updateList) > 0:
        cur.executemany("update movie set title = ?, year = ?, airdate = ?, tmdbid = ?, imdbid = ?, description = ?, runtime = ?, updated = date('now') WHERE id = ?", updateList)

    return returnList

def beginTVParse(cur):
    updateList = []
    return_list = []
    updateCount = 100
    tvdb = None
    updated = datetime.datetime.now().strftime("%Y-%m-%d")
    current_show = None
    tvdb_show = None

    pass1 = re.compile(r'(?ix)(?:s|season|\.|\s)(?P<season>\d{1,2})?(?:e|x|episode\s|^|\s)(?P<episode>\d{2})')
    pass2 = re.compile(r'(?i)([0-9]{3,})')
    season = re.compile('season\s?([0-9]+)', re.I)
    year = re.compile('^[0-9]{4}$')

    cur.execute("select id, title from show")
    show_list = cur.fetchall()

    cur.execute('select id, file_name, parent_dir, sub_dir from episode where updated is NULL order by parent_dir ASC')
    nullRows = cur.fetchall()
    for row in nullRows:
        #get values necessary
        filename = row[1]
        parentdir = row[2]
        subdir = row[3]
        id = row[0]

        results = None
        data = {'id': id, 'eps': None, 'season': None, 'title': None, 'desc': None, 'year': None, 'aired': None, 'show': None, 'updated': updated}

        #first pass
        results = pass1.search(filename)
        if results:
            data['eps'] = results.group('episode')
            data['season'] = results.group('season')

        if data['eps'] is None:
            results = pass2.findall(filename)
            if results and len(results[-1]) >= 3:
                seq = results[-1]
                seqlen = seq.__len__()
                skip = 1 if seqlen%2 else 2 #if even skip 2 otherwise skip 1
                data['season'] = seq[0:skip]
                data['eps'] = seq[skip:skip+2] # only get the first episode, even if a joined one

        if data['season'] is None:
            results = season.match(subdir)
            if results is not None:
                data['season'] = results.group(1)

        #TVDB:
        if data['season'] is not None and data['eps'] is not None:
            if tvdb is None: tvdb = tvdb_api.Tvdb()

            if current_show != parentdir:
                tvdb_show = None
                cur.execute("select count(id) from episode where parent_dir=? and updated is null", (parentdir,))
                if cur.fetchone()[0] >= 10: #bulk update
                    current_show = parentdir
                    try:
                        tvdb_show = tvdb[parentdir]
                    except te.tvdb_error:
                        tvdb_show = []
                        data['updated'] = None
                    except te.tvdb_userabort:
                        tvdb_show = []
                        data['updated'] = None
                    except:
                        pass

            episode = None
            if tvdb_show is not None:
                try:
                    episode = tvdb_show[int(data['season'])][int(data['eps'])]
                except:
                    logger.warn('MEDIA_INFO', 'TVDB had no data in bulk find for \"%s\" s%se%s', parentdir, data['season'], data['eps'])
                pass
            else:
                try:
                    episode = tvdb[parentdir][int(data['season'])][int(data['eps'])]
                except te.tvdb_error:
                    data['updated'] = None
                    logger.warn('MEDIA_INFO', 'TVDB had no data in single find for \"%s\" s%se%s', parentdir, data['season'], data['eps'])
                except te.tvdb_userabort:
                    data['updated'] = None
                    logger.warn('MEDIA_INFO', 'TVDB was user aborted for \"%s\" s%se%s', parentdir, data['season'], data['eps'])
                except:
                    logger.warn('MEDIA_INFO', 'TVDB had no data in single find for \"%s\" s%se%s', parentdir, data['season'], data['eps'])

            if episode is not None:
                data['desc'] = episode['overview']
                data['title'] = episode['episodename']
                data['aired'] = episode['firstaired']

                if data['desc'] and len(data['desc']) > 0:
                    data['desc'] = data['desc'].replace('\n', '')

                logger.info('MEDIA_INFO', 'TVDB scrapped data for %s.s%se%s', parentdir, data['season'], data['eps'])
            else:
                logger.warn('MEDIA_INFO', 'TVDB returned no results for \"%s\" s%se%s', parentdir, data['season'], data['eps'])
        else:
            logger.error('beginTVParse', 'update_database.py', 'Unable to parse \"%s\" for season or episode.', filename)

        #get show id
        show_id = [sid[0] for sid in show_list if sid[1] == parentdir.title()]
        if len(show_id) == 0:
            cur.execute("INSERT INTO show (title) VALUES (?)", (parentdir.title(), ))
            data['show'] = cur.lastrowid
            show_list.append((data['show'], parentdir.title()))
        else:
            data['show'] = show_id[0]

        updateList.append((data['show'], data['eps'], data['season'], data['title'], data['desc']
                          , data['aired'], data['year'], data['updated'], data['id']))

        return_list.append("{0} {1}x{2} - {3}".format(parentdir.title(),
                                                      data['season'],
                                                      data['eps'],
                                                      data['title'].encode('utf-8') if not None else filename))

        #update db
        if len(updateList) >= updateCount:
            cur.executemany("UPDATE episode SET show=?,episode=?,season=?,title=?,description=?,airdate=?,year=?,updated=? WHERE id=?", updateList)
            updateList = []

    if len(updateList) > 0: #remaining
        cur.executemany("UPDATE episode SET show=?,episode=?,season=?,title=?,description=?,airdate=?,year=?,updated=? WHERE id=?", updateList)

    return return_list
