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

# globals
movie_locations = []
tv_locations = []

# load settings
def parseSettings():
    global movie_locations, tv_locations

    tmpConfig = ConfigParser.ConfigParser()
    tmpConfig.read(constants.__CONFIG_FILENAME)

    try:
        for option in tmpConfig.options(constants.__CONFIG_TV):
            tv_locations.append(tmpConfig.get(constants.__CONFIG_TV, option))
    except Exception, e:
        logger.warn('parseSettings', 'no tv locations provided. ' + str(e))
        pass

    try:
        for option in tmpConfig.options(constants.__CONFIG_MOVIES):
            movie_locations.append(tmpConfig.get(constants.__CONFIG_MOVIES, option))
    except Exception, e:
        logger.warn('parseSettings', 'no movie locations provided. ' + str(e))
        pass

    return

def validateLocation(loc):
    return os.path.isdir(loc)

def bootstrap():
    #filemode='w' #new file every launch
    logging.basicConfig(level=logging.DEBUG
        , format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


def main(checkTv=False, checkMovie=False, checkTvFanart=False, checkMovieFanart=False, renameAllFiles=False):
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
    if checkTv:
        db.buildDatabase(tv_locations, constants.__TYPE_TV)
        renameAllFiles = False

    if checkMovie:
        db.buildDatabase(movie_locations, constants.__TYPE_MOVIE)
        renameAllFiles = False

    if renameAllFiles: db.renameAllFiles(tv_locations)

    logger.info('main', 'Finished indexing')


if __name__ == '__main__':
    params = {"tv": False, "movie": False, "tvFanart": False, "movieFanart": False, "renameFiles": False}
    helpMode = False

    if len(sys.argv) > 1:
        for argv in sys.argv[1:]:
            if argv[0] == '-':
                for p in argv[1:]:
                    if p == 't': params["tv"] = True
                    elif p == 'm': params["movie"] = True
                    elif p == 'T': params["tvFanart"] = True
                    elif p == 'M': params["movieFanart"] = True
                    elif p == 'R': params["renameFiles"] = True
            elif argv[0] == '?':
                helpMode = True
            else:
                print "unknown arg: {}".format(argv)



    if not helpMode:
        main(params["tv"]
            , params["movie"]
            , params["tvFanart"]
            , params["movieFanart"]
            , params["renameFiles"])
    else:
        print """
                ex: python build_static.py -tmTM
                t = index tv
                m = index movies
                T = scan for fanart for tv
                M = scan for fanart for Movies
                R = rename ALL tv files to match title, cannot be used with other options
                """

