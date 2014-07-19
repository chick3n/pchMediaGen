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

__DATABASE_FILENAME = "media.sqlite"

__CONFIG_FILENAME = "settings.ini"
__CONFIG_MOVIES = "MOVIES"
__CONFIG_TV = "TV"
__CONFIG_NOTIFYMYANDROID_KEYS = "NOTIFYMYANDROID"

def __DATABASE_CREATE():
    return '''CREATE TABLE "episode" ("id" INTEGER PRIMARY KEY  NOT NULL ,"show" TEXT,"season" INTEGER,"episode" INTEGER,"title" TEXT,"description" TEXT,"airdate" DATETIME,"full_path" TEXT NOT NULL ,"file_name" TEXT NOT NULL ,"added" DATETIME DEFAULT (CURRENT_TIMESTAMP) ,"updated" DATETIME DEFAULT (NULL) ,"parent_dir" TEXT,"sub_dir" TEXT,"year" INTEGER,"fanart" TEXT,"poster" TEXT,"banner" TEXT);
                CREATE TABLE "show" ("id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL , "title" TEXT NOT NULL );
            '''


__TYPE_TV = "TV"
__TYPE_MOVIE = "MOVIE"