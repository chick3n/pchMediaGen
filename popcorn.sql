CREATE TABLE "tv" ("tv_id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL , "tv_name" VARCHAR, "update" DATETIME, "last_update" DATETIME);
CREATE TABLE "tv_episode" ("tvepisode_id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL , "episode_name" VARCHAR, "episode_number" VARCHAR, "episode_description" VARCHAR, "raw_file_name" VARCHAR, "updated_on" DATETIME, "last_update_html" DATETIME);
CREATE TABLE "tv_season" ("tvseason_id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL , "season_name" VARCHAR, "updated_on" , "last_update" , "tv_id" INTEGER NOT NULL );
