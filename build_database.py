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

import sqlite3 as lite
import os
import constants
import fnmatch
import re
import update_database as ud
import datetime
from logger import logger

conn = None
cur = None

def buildDatabase(locations, type):
    global conn, cur

    if len(locations) <= 0:
        return

    initalizeDB()

    if conn is None or cur is None:
        logger.error('buildDatabase', 'build_database.py', 'Connection to database not established. Exiting.')
        return

    populateDB(locations, type)
    ud.updateDB(conn, cur, type)

    #clean up
    if(conn is not None):
        conn.commit()
        conn.close()

    return

def initalizeDB():
    global conn, cur

    if(not os.path.isfile(constants.__DATABASE_FILENAME)):
        conn = lite.connect(constants.__DATABASE_FILENAME)
        cur = conn.cursor()
        cur.executescript(constants.__DATABASE_CREATE())
        conn.commit()
    else:
        conn = lite.connect(constants.__DATABASE_FILENAME)
        cur = conn.cursor()

    return

def renameAllFiles(locations):
    if len(locations) <= 0:
        return

    initalizeDB()

    if conn is None or cur is None:
        logger.error('renameAllFiles', 'build_database.py', 'Connection to database not established. Exiting.')
        return

    files = []
    cur.execute("select full_path from episode")
    media_info = cur.fetchall()

    for media in media_info:
        files.append(media[0])

    renameFiles(files, locations)

    return

def renameFiles(files, locations):

    location = locations[0].replace('/', os.path.sep)

    for file in files:
        try:
            cur.execute("select season, episode, title, id, file_name from episode where full_path = ? AND episode is not null AND title is not null", (file,))
            media_info = cur.fetchone()

            if media_info is not None:
                if media_info[1] > 0 and media_info[2].__len__() > 0:
                    root, ext = os.path.splitext(file)
                    new_file = str(media_info[1]).zfill(2) + ' - ' + media_info[2] + ext
                    #logger.info('Rename', 'Change filename: ' + file + ' to ' + new_file)
                    if new_file != media_info[4]:
                        new_path = file.replace(media_info[4], new_file)
                        os.rename(os.path.join(location, file), os.path.join(location, new_path))
                        #rename succesfull, update database to reference new name

                        cur.execute("update episode set file_name = ?, full_path = ? where id = ?", (new_file, new_path, media_info[3]))
        except Exception:
            continue

    conn.commit()

    return

def populateDB(locations, type):
    added = []

    if(type == constants.__TYPE_TV):
        added = populateDBTV(locations, type)
        renameFiles(added, locations)

    if(type == constants.__TYPE_MOVIE):
        added = populateDBMovie(locations, type)

    return added

#Movie: Root = Movie List > Movie
def populateDBMovie(locations, type):
    global conn
    includes = ['*.mkv', '*.avi', '*.mp4']
    excludes = ['*sample*']

    includes = r'|'.join([fnmatch.translate(x) for x in includes])
    excludes = r'|'.join([fnmatch.translate(x) for x in excludes])

    level = 0

    files_added = []

    logger.info('Movies', 'Scanning Movies Started')
    for location in locations:
        location = location.replace('/', os.path.sep)
        insertList = []
        for dirname in os.listdir(location):
            try:
                cur.execute("select count(movie.id) from movie where parent_dir = ?", (dirname,))
                if cur.fetchone()[0] == 1:
                    continue
                for path, dirs, filenames in os.walk(os.path.join(location, dirname)):

                    if path.replace(location, "").count(os.path.sep) > level:
                        del dirs[:]

                    filenames = [f for f in filenames if re.match(includes, f.lower())]
                    filenames = [f for f in filenames if not re.match(excludes, f.lower())]

                    no_root_path = path.replace(location, "")

                    for filename in filenames:
                        full_path = os.path.join(path, filename)
                        blank_path = os.path.join(no_root_path, filename)
                        #check if fullpath + filename exists, than ignore otherwise
                        cur.execute("select count(movie.id) from movie where full_path = ?", (blank_path,))
                        if cur.fetchone()[0] == 1:
                            continue

                        folder = None
                        folderList = path.rsplit(os.path.sep, 1)
                        if len(folderList) > 1:
                            folder = folderList[1]

                        added = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                        #look for nfo first

                        insertList.append((blank_path
                                           , filename
                                           , dirname
                                           , folder
                                           , added
                            ))
                        files_added.append(blank_path)
            except Exception:
                continue

        if len(insertList) > 0:
            logger.info('Movies', "Indexed Movies:\n%s", ','.join([x[2] for x in insertList]))
            cur.executemany('insert into movie (full_path, file_name, parent_dir, sub_dir, added) VALUES (?,?,?,?, ?)'
                , insertList)
            conn.commit()
    return files_added


# TV: Root = Show List > Season/Year > Episode || Episode
def populateDBTV(locations, type):
    global conn
    includes = ['*.mkv', '*.avi', '*.mp4']
    excludes = ['*sample*']

    includes = r'|'.join([fnmatch.translate(x) for x in includes])
    excludes = r'|'.join([fnmatch.translate(x) for x in excludes])

    #get list of tv shows
    level = 1 #how deep to go
    #locations = []
    files_added = []

    for location in locations:
        location = location.replace('/', os.path.sep)
        for dirname in os.listdir(location):
            skippedDir = False
            insertList = []
            for path, dirs, filenames in os.walk(os.path.join(location, dirname)):
                #ignore check
                if '.ignore' in filenames:
                    skippedDir = True
                    break

                if path.replace(location, "").count(os.path.sep) > level:
                    del dirs[:]

                filenames = [f for f in filenames if re.match(includes, f.lower())]
                filenames = [f for f in filenames if not re.match(excludes, f.lower())]

                no_root_path = path.replace(location, "")

                for filename in filenames:
                    full_path = os.path.join(path, filename).decode('utf-8')
                    blank_path = os.path.join(no_root_path, filename).decode('utf-8')
                    #check if fullpath + filename exists, than ignore otherwise
                    cur.execute("select count(episode.id) from episode where full_path = ?", (blank_path,))
                    if cur.fetchone()[0] == 1:
                        continue

                    folder = None
                    folderList = path.rsplit(os.path.sep, 1)
                    if len(folderList) > 1:
                        folder = folderList[1]

                    added = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                    #look for nfo first

                    #determine episode, season, title, insert into DB
                    insertList.append((blank_path
                                       , filename
                                       , dirname
                                       , folder
                                       , added
                                    ))
                    files_added.append(blank_path)

            if len(insertList) > 0:
                logger.info('TV', 'Indexing \"%s\" - Found %s releases', dirname, len(insertList))
                cur.executemany('insert into episode (full_path, file_name, parent_dir, sub_dir, added) VALUES (?,?,?,?, ?)'
                    , insertList)
                conn.commit()
            elif skippedDir:
                logger.info('TV', 'Skipping \"%s\" - Found ignore', dirname)
            else:
                logger.info('TV', 'Indexing \"%s\" - Found 0 releases', dirname)
    return files_added
