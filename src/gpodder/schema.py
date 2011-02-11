# -*- coding: utf-8 -*-
#
# gPodder - A media aggregator and podcast client
# Copyright (c) 2005-2010 Thomas Perl and the gPodder Team
#
# gPodder is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# gPodder is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# gpodder.schema - Database schema update and migration facility
# Thomas Perl <thp@gpodder.org>; 2011-02-01


def initialize_database(db):
    # Create table for podcasts
    db.execute("""
    CREATE TABLE podcast (
        id INTEGER PRIMARY KEY NOT NULL,
        title TEXT NOT NULL DEFAULT '',
        url TEXT NOT NULL DEFAULT '',
        link TEXT NOT NULL DEFAULT '',
        description TEXT NOT NULL DEFAULT '',
        cover_url TEXT NULL DEFAULT NULL,
        published INTEGER NOT NULL DEFAULT 0,
        auth_username TEXT NULL DEFAULT NULL,
        auth_password TEXT NULL DEFAULT NULL,
        http_last_modified TEXT NULL DEFAULT NULL,
        http_etag TEXT NULL DEFAULT NULL,
        auto_archive_episodes INTEGER NOT NULL DEFAULT 0,
        download_folder TEXT NOT NULL DEFAULT '',
        pause_subscription INTEGER NOT NULL DEFAULT 0
    )
    """)

    INDEX_SQL = """
    CREATE UNIQUE INDEX idx_podcast_url ON podcast (url)
    CREATE UNIQUE INDEX idx_podcast_download_folder ON podcast (download_folder)
    """

    for sql in INDEX_SQL.strip().split('\n'):
        db.execute(sql)

    # Create table for episodes
    db.execute("""
    CREATE TABLE episode (
        id INTEGER PRIMARY KEY NOT NULL,
        podcast_id INTEGER NOT NULL,
        title TEXT NOT NULL DEFAULT '',
        description TEXT NOT NULL DEFAULT '',
        url TEXT NOT NULL,
        published INTEGER NOT NULL DEFAULT 0,
        guid TEXT NOT NULL,
        link TEXT NOT NULL DEFAULT '',
        file_size INTEGER NOT NULL DEFAULT 0,
        mime_type TEXT NOT NULL DEFAULT 'application/octet-stream',
        state INTEGER NOT NULL DEFAULT 0,
        is_new INTEGER NOT NULL DEFAULT 0,
        archive INTEGER NOT NULL DEFAULT 0,
        download_filename TEXT NULL DEFAULT NULL,
        total_time INTEGER NOT NULL DEFAULT 0,
        current_position INTEGER NOT NULL DEFAULT 0,
        current_position_updated INTEGER NOT NULL DEFAULT 0,
        last_playback INTEGER NOT NULL DEFAULT 0
    )
    """)

    INDEX_SQL = """
    CREATE INDEX idx_episode_podcast_id ON episode (podcast_id)
    CREATE UNIQUE INDEX idx_episode_download_filename ON episode (download_filename)
    CREATE UNIQUE INDEX idx_episode_guid ON episode (podcast_id, guid)
    CREATE INDEX idx_episode_state ON episode (state)
    CREATE INDEX idx_episode_is_new ON episode (is_new)
    CREATE INDEX idx_episode_archive ON episode (archive)
    CREATE INDEX idx_episode_published ON episode (published)
    """

    for sql in INDEX_SQL.strip().split('\n'):
        db.execute(sql)

    # Create table for version info / metadata + insert initial data
    db.execute("""CREATE TABLE version (version integer)""")
    db.execute("""INSERT INTO version (version) VALUES (1)""")
    db.commit()


def upgrade(db):
    if not list(db.execute('PRAGMA table_info(version)')):
        initialize_database(db)
        return

    result = db.execute('SELECT version FROM version').fetchone()
    if result[0] != 1:
        raise Exception('Database schema version unknown')


def convert_gpodder2_db(old_db, new_db):
    """Convert gPodder 2.x databases to the new format

    Both arguments should be SQLite3 connections to the
    corresponding databases.
    """

    # Copy data for podcasts
    old_cur = old_db.cursor()
    columns = [x[1] for x in old_cur.execute('PRAGMA table_info(channels)')]
    for row in old_cur.execute('SELECT * FROM channels'):
        row = dict(zip(columns, row))
        values = (
                row['id'],
                row['override_title'] or row['title'],
                row['url'],
                row['link'],
                row['description'],
                row['image'],
                row['pubDate'],
                row['username'] or None,
                row['password'] or None,
                row['last_modified'] or None,
                row['etag'] or None,
                row['channel_is_locked'],
                row['foldername'],
                not row['feed_update_enabled'],
        )
        new_db.execute("""
        INSERT INTO podcast VALUES (%s)
        """ % ', '.join('?'*len(values)), values)
    old_cur.close()

    # Copy data for episodes
    old_cur = old_db.cursor()
    columns = [x[1] for x in old_cur.execute('PRAGMA table_info(episodes)')]
    for row in old_cur.execute('SELECT * FROM episodes'):
        row = dict(zip(columns, row))
        values = (
                row['id'],
                row['channel_id'],
                row['title'],
                row['description'],
                row['url'],
                row['pubDate'],
                row['guid'],
                row['link'],
                row['length'],
                row['mimetype'],
                row['state'],
                not row['played'],
                row['locked'],
                row['filename'],
                row['total_time'],
                row['current_position'],
                row['current_position_updated'],
                0,
        )
        new_db.execute("""
        INSERT INTO episode VALUES (%s)
        """ % ', '.join('?'*len(values)), values)
    old_cur.close()

