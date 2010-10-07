import re, time, urllib, urllib2, cookielib, string
from core import *
from nhl import *
from gamecenter import *
from espn import *

def Start():
    Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, L('VideoTitle'), ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(NHL)
    DirectoryItem.art = R(ART)

    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (iPad; U; CPU OS 3_2_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B500 Safari/531.21.10'

def ValidatePrefs():
    
    u = Prefs['gc_username']
    p = Prefs['gc_password']
    ## do some checks and return a
    ## message container
    if( u and p ):
        Log("username = %s"%u)
    else:
        return MessageContainer(
            "Error",
            "You need to provide a valid username and password. Please buy a subscription."
        )

def VideoMainMenu():    
    dir = MediaContainer(viewGroup="List")

    dir.Append(Function(DirectoryItem(NHLMenu, title="NHL.com", thumb=R(NHL), art=R(ART))))
    if (Prefs['gc_enabled']):
        dir.Append(Function(DirectoryItem(GCMainMenu, title="NHL Gamecenter Live", thumb=R(NHL), art=R(ART))))
    if (Prefs['espn_enabled']):
        dir.Append(Function(DirectoryItem(ESPNMenu, title="ESPN360", thumb=R(NHL), art=R(ART))))
    dir.Append(PrefsItem(title="Preferences"))
        
    return dir