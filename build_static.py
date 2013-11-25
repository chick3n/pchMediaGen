#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      VincentLab
#
# Created:     29/01/2013
# Copyright:   (c) VincentLab 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import ConfigParser
import os
import constants
import build_database as db
import sys
import logging
from logger import logger
from pushnotify import exceptions
from pushnotify import nma

# globals
movie_locations = []
tv_locations = []
notifymyandroid_keys = []

# load settings
def parseSettings():
    global movie_locations, tv_locations

    tmpConfig = ConfigParser.ConfigParser()
    tmpConfig.read(constants.__CONFIG_FILENAME)

    try:
        for option in tmpConfig.options(constants.__CONFIG_TV):
            tv_locations.append(tmpConfig.get(constants.__CONFIG_TV, option))
    except:
        logger.warn('parseSettings', 'no tv locations provided.')
        pass

    try:
        for option in tmpConfig.options(constants.__CONFIG_MOVIES):
            movie_locations.append(tmpConfig.get(constants.__CONFIG_MOVIES, option))
    except:
        logger.warn('parseSettings', 'no movie locations provided.')
        pass

    try:
        for option in tmpConfig.options(constants.__CONFIG_NOTIFYMYANDROID_KEYS):
            notifymyandroid_keys.append(tmpConfig.get(constants.__CONFIG_NOTIFYMYANDROID_KEYS, option))
    except:
        logger.warn('parseSettings', 'no Notify My Android keys.')
        pass

    return

def validateLocation(loc):
    return os.path.isdir(loc)

def bootstrap():
    #filemode='w' #new file every launch
    logging.basicConfig(level=logging.DEBUG
        , format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


def main(checkTv=False, checkMovie=False, checkTvFanart=False, checkMovieFanart=False):
    bootstrap()

    logger.info('main', 'Starting indexer')

    parseSettings() #grab settings

    if tv_locations is not None and len(tv_locations) > 0:
        for x in range(0, len(tv_locations)):
            if not validateLocation(tv_locations[x]):
                tv_locations.pop(x)

    if movie_locations is not None and len(movie_locations) > 0:
        for x in range(0, len(movie_locations)):
            if not validateLocation(movie_locations[x]):
                movie_locations.pop(x)

    has_a_location = len(tv_locations) + len(movie_locations)

    if has_a_location == 0:
        logger.error('main', 'build_static.py', 'There are no paths to index against.')
        exit()

    #settings parse complete

    #build/update database
    movies = []
    shows = []

    if checkTv:
        shows = db.buildDatabase(tv_locations, constants.__TYPE_TV)
    if checkMovie:
        movies = db.buildDatabase(movie_locations, constants.__TYPE_MOVIE)

    #send push notifications
    if False and notifymyandroid_keys is not None and len(notifymyandroid_keys) > 0:
        client = nma.Client(notifymyandroid_keys)
        if movies is not None and len(movies) > 0:
            client.notify('MediaPCH',
                          'Movies Added',
                          "<br>".join(movies),
                          kwargs={'content-type': 'text/html'})
        if shows is not None and len(shows) > 0:
            client.notify('MediaPCH',
                          'Shows Added',
                          "<br>".join(shows),
                          kwargs={'content-type': 'text/html'})

    logger.info('main', 'Finished indexing')


if __name__ == '__main__':
    params = {"tv": False, "movie": False, "tvFanart": False, "movieFanart": False}
    helpMode = False

    if len(sys.argv) > 1:
        for argv in sys.argv[1:]:
            if argv[0] == '-':
                for p in argv[1:]:
                    if p == 't': params["tv"] = True
                    elif p == 'm': params["movie"] = True
                    elif p == 'T': params["tvFanart"] = True
                    elif p == 'M': params["movieFanart"] = True
            elif argv[0] == '?':
                helpMode = True
            else:
                print "unknown arg: {}".format(argv)



    if not helpMode:
        main(params["tv"]
            , params["movie"]
            , params["tvFanart"]
            , params["movieFanart"])
    else:
        print """
                ex: python build_static.py -tmTM
                t = index tv
                m = index movies
                T = scan for fanart for tv
                M = scan for fanart for Movies
                """

