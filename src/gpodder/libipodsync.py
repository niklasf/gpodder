
#
# gPodder
# Copyright (c) 2005-2006 Thomas Perl <thp@perli.net>
# Released under the GNU General Public License (GPL)
#

#
#  libipodsync.py -- sync localdb contents with ipod playlist
#  thomas perl <thp@perli.net>   20060405
#
#


# variable tells if ipod functions are to be enabled
enable_ipod_functions = True


try:
    import gpod
    import eyeD3
except:
    enable_ipod_functions = False

import os
import sys

import libgpodder
import liblocaldb
import libpodcasts


# do we provide iPod functions to the user?
def ipod_supported():
    global enable_ipod_functions
    return enable_ipod_functions


class gPodder_iPodSync(object):
    itdb = None
    ipod_mount = '' # mountpoint for ipod
    playlist_name = 'gpodder'
    pl_master = None
    pl_gpodder = None
    
    def __init__( self, ipod_mount = '/media/ipod/'):
        if not ipod_supported():
            if libgpodder.isDebugging():
                print '(ipodsync) iPod functions not supported. (libgpod + eyed3 needed)'
        self.ipod_mount = ipod_mount

    def open( self):
        if not ipod_supported():
            return False
        if self.itdb == None:
            self.itdb = gpod.itdb_parse( self.ipod_mount, None)
            self.itdb.mountpoint = self.ipod_mount
            self.pl_master = gpod.sw_get_playlists( self.itdb)[0]
            self.pl_gpodder = self.get_gpodder_playlist()

    def close( self, write_update = True):
        if not ipod_supported():
            return False
        if write_update:
            gpod.itdb_write( self.itdb, None)
        self.itdb = None

    def remove_from_ipod( self, track):
        if not ipod_supported():
            return False
        if libgpodder.isDebugging():
           print '(ipodsync) REMOVING FROM IPOD!! track: %s' % track.title
        fname = gpod.itdb_filename_on_ipod( track)
        gpod.itdb_playlist_remove_track( self.pl_master, track)
        gpod.itdb_playlist_remove_track( self.pl_gpodder, track)
        gpod.itdb_track_unlink( track)
        os.unlink( fname)
    
    def get_gpodder_playlist( self):
        if not ipod_supported():
            return False
        for playlist in gpod.sw_get_playlists( self.itdb):
            if playlist.name == 'gpodder':
                if libgpodder.isDebugging():
                    print "(ipodsync) found old gpodder playlist"
                return playlist
        
        # if we arrive here: gpodder playlist not found!
        if libgpodder.isDebugging():
            print "creating new playlist"
        new_playlist = gpod.itdb_playlist_new( 'gpodder', False)
        gpod.itdb_playlist_add( self.itdb, new_playlist, -1)
        return new_playlist

    def dump( self):
        if not ipod_supported():
            return False
        for track in gpod.sw_get_playlist_tracks( self.pl_gpodder):
            print gpod.itdb_filename_on_ipod( track)

    def clean_playlist( self):
        if not ipod_supported():
            return False
        for track in gpod.sw_get_playlist_tracks( self.pl_gpodder):
            if libgpodder.isDebugging():
                print '(ipodsync) trying to remove track %s' % track.title
            self.remove_from_ipod( track)

    def copy_channel_to_ipod( self, channel):
        if not ipod_supported():
            return False
        for episode in channel.items:
            if channel.isDownloaded( episode):
                self.add_episode_from_channel( channel, episode)

    def set_podcast_flags( self, track):
        if not ipod_supported():
            return False
        # try to modify track to be more podcast-ish
        #track.flag1 = 0x02
        #track.flag3 = 0x01
        #track.flag4 = 0x02
        pass

    def add_episode_from_channel( self, channel, episode):
        if not ipod_supported():
            return False
        if libgpodder.isDebugging():
            print '(ipodsync) Adding item: %s from %s' % (episode.title, channel.title)
        local_filename = str(channel.getPodcastFilename( episode.url))
        try:
            eyed3_info = eyeD3.Mp3AudioFile( local_filename)
            track_length = eyed3_info.getPlayTime() * 1000 # in milliseconds
        except:
            if libgpodder.isDebugging():
                print '(ipodsync) Warning: cannot get length for %s, will use zero-length' % episode.title
            track_length = 0 # hmm.. better do something else?!
        
        track = gpod.itdb_track_new()
        self.set_podcast_flags( track)
        track.title = str(episode.title)
        track.artist = str(channel.title)
        track.album = 'gPodder podcast'
        track.tracklen = track_length
        track.filetype = 'mp3' # huh?! harcoded?! well, well :)
        track.description = str(episode.description)
        
        gpod.itdb_track_add( self.itdb, track, -1)
        gpod.itdb_playlist_add_track( self.pl_master, track, -1)
        gpod.itdb_playlist_add_track( self.pl_gpodder, track, -1)

        if gpod.itdb_cp_track_to_ipod( track, local_filename, None) != 1:
            if libgpodder.isDebugging():
                print '(ipodsync) could not add track: %s' % episode.title
        else:
            if libgpodder.isDebugging():
                print '(ipodsync) success for %s :)' % episode.title


