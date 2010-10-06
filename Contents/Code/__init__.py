import re, time, urllib, urllib2, cookielib, string

####################################################################################################
VIDEO_PREFIX = "/video/nhl"

NAME = L('Title')

ART           = 'art-default.jpg'
ICON          = 'icon-default.png'
NHL           = 'nhl.png'
####################################################################################################

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
            "You need to provide a valid username and password. Please buy a sub."
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
    

### NHL.com ###

def NHLMenu(sender):
    dir = MediaContainer(viewGroup="List")
    
    html = HTML.ElementFromURL('http://video.nhl.com/videocenter', errors='ignore')
    teams = html.xpath(".//tr[@id='trTopBanner']//option[@value!='']")
    for team in teams:
        if (team.get('value') == "video"):
            subdomain = "video"
            thumb=R(NHL)
            art=R(ART)
        else:
            team_name = team.get('value')
            subdomain = "video.%s" % team_name
            thumb=R('%s.png' % team_name)
            art=R('%s_art.jpg' % team_name)
        name = team.text
        url = "http://%s.nhl.com/videocenter" % subdomain
        dir.Append(Function(DirectoryItem(ChannelMenu, title=name, thumb=thumb), team_url=url, thumb2=thumb, art2=art))
        
    return dir


def ChannelMenu(sender, team_url=None, thumb2=NHL, art2=ART):
    
    dir = MediaContainer(viewGroup="InfoList", title2=sender.itemTitle)
    VideoItem.art = art2
    VideoItem.thumb = thumb2
    DirectoryItem.art = art2
    DirectoryItem.thumb = thumb2
    
    html = HTML.ElementFromURL(team_url, errors='ignore')
    channels_html = html.find(".//table[@id='tblMenu']")
    
    channels = channels_html.findall(".//td[@class='menuitem']")
    
    for channel in channels:
        menuid = channel.get('menuid')
        menutype = channel.get('menutype')
        title_row = channel.find("./table/tr")
        subtitle_row = title_row.getnext()
        title = title_row.find("./td").text
        subtitle = subtitle_row.find("./td").text
        dir.Append(Function(DirectoryItem(ChannelVideos, title=title, summary=subtitle), menuid=menuid, menutype=menutype, team_url=team_url))
    
    return dir


def ChannelVideos(sender, menuid=0, menutype=0, team_url=None):
    tables = []
    games = []
    liveevents = []
    podcasts = []
    dir = MediaContainer(viewGroup="InfoList", title1=sender.title2, title2=sender.itemTitle)
    if (menutype == "0"): # Categories
        html = HTML.ElementFromURL('%s/servlets/browse?ispaging=false&cid=%s&component=_browse&menuChannelIndex=0&menuChannelId=%s&ps=36&pn=1&pm=0&ptrs=3&large=true' % (team_url, menuid, menuid), errors='ignore')
        tables = html.findall(".//table[@title]")
    elif (menutype == "1"): # Channels
        html = HTML.ElementFromURL('%s/servlets/guide?ispaging=false&cid=%s&menuChannelIndex=5&menuChannelId=%s&ps=7&channeldays=7&pn=1&pm=0&ptrs=3&large=true' % (team_url, menuid, menuid), errors='ignore')
        tables = html.findall(".//table[@title]")
    # elif (menutype == "3"): # Game Day // None yet
    elif (menutype == "4"): # Live Events // NHL/Press Room
        html = HTML.ElementFromURL('http://video.nhl.com/videocenter/servlets/liveevents?autoRefreshing=true&catId=%s&large=true&menuChannelId=%s&menuChannelIndex=9&ptrs=3' % (menuid, menuid), errors='ignore')
        liveevents = html.findall(".//table[@title]")
    elif (menutype == "5"): # Podcasts // NHL/Podcast Central
        xml = XML.ElementFromURL('http://video.nhl.com/videocenter/servlets/podcasts?large=true&menuChannelId=%s&menuChannelIndex=15&ptrs=3' % menuid)
        podcasts = xml.findall("podcast")
    elif (menutype == "100"): # Game Highlights
        dir = MediaContainer(viewGroup="List", title1=sender.title2, title2=sender.itemTitle)
        xml = XML.ElementFromURL('%s/highlights?xml=0' % team_url)
        games = xml.findall("./game")
    
    for podcast in podcasts:
        title = podcast.find("title").text
        summary = podcast.find("description").text
        url = podcast.find("link").text
        dir.Append(TrackItem(url, title=title, summary=summary))
    
    for game in games:
        title = "%s: %s at %s, %s - %s" % (game.find("game-date").text , game.find("away-team/name").text, game.find("home-team/name").text, game.find("away-team/goals").text, game.find("home-team/goals").text)
        url = game.find("alt-video-clip").text
        dir.Append(VideoItem(key=url, title=title))
    
    for event in liveevents:
        is_live = True if event.get("islive") == "true" else False
        try:
            data = re.search(r"(rtmp[^']+)','([^']+)'", event.get('onclick'))
            is_rtmp = True
            url = data.group(1)
        except AttributeError, e:
            data = re.search(r"(http[^']+)','([^']+)'", event.get('onclick'))
            is_rtmp = False
            url = data.group(1)
        title = data.group(2)
        summary = event.get("title")
        if (is_live == True):
            dir.Append(Function(WebVideoItem(PlayRTMP, title=title, summary=summary), url=url, team_url=team_url))
        else:
            dir.Append(Function(DirectoryItem(PlayNotLive, title, summary=summary)))
    
    for table in tables:
        img = table.find(".//img").get('src')
        data = re.search(r"(http[^']+)','([^']+)',[^,]+,[^,]+, '([^']+)", table.get('onclick'))
        try:
            title = data.group(2)
        except AttributeError, e:
            data = re.search(r"(http[^']+)','([^']+)'", table.get('onclick'))
            title = data.group(2)
        date = table.find(".//div[@divtype='prog_name']").getnext().text.strip()
        subtitle = data.group(3) if date == "" else date
        url = data.group(1)
        is_flv = re.search(r"\.flv", url)
        is_audio = re.search(r"\.mp3", url)
        if (is_flv == None):
            url = re.sub(r"/s/", "/u/", url)
            url = re.sub(r"\.mp4", "_sd.mp4", url)
            dir.Append(VideoItem(key=url, title=title, subtitle=subtitle, summary=table.get('title'), thumb=img))
        else:
            if (is_audio == None):
                dir.Append(Function(VideoItem(PlayVideo, title=title, subtitle=subtitle, summary=table.get('title'), thumb=img), url=url, team_url=team_url))
            else:
                dir.Append(Function(TrackItem(PlayAudio, title=title, artist="NHL", album=subtitle, thumb=img), url=url, team_url=team_url))
    return dir


def PlayNotLive(sender):
    return MessageContainer("Stream is not live yet", "Please check back later.")
    
def PlayRTMP(sender, url=None, team_url=None):
    encrypted_url = Decrypt(url)
    split_url = re.split('/cdncon/', encrypted_url)
    url = "%s/cdncon" % split_url[0]
    clip =  split_url[1]
    return Redirect(RTMPVideoItem(url, clip=clip, width=640, height=360, live=True))

def PlayVideo(sender, url=None, team_url=None):
    url = re.sub(r"\.flv", "_sd.flv", url)
    return Decrypt(url)

def PlayAudio(sender, url=None, team_url=None):
    url = re.sub(r"\.flv", "_sd.flv", url)
    return Decrypt(url, "nhl", "audio")


### Gamecenter ###

def GCLogin():
    handler = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    urllib2.install_opener(handler)
    u = Prefs['gc_username']
    p = Prefs['gc_password']
    params = urllib.urlencode({"username": u, "password": p})
    f = handler.open("https://gamecenter.nhl.com/nhlgc/secure/login", params)
    data = f.read()
    f.close()
    return handler


def GCArchives(handler, params, servlet="archives"):
    # Returns XML for GC archives
    params = urllib.urlencode(dict({"isFlex": "true"}.items() + params.items())) # Add params to the "isFlex"
    f = handler.open("http://gamecenter.nhl.com/nhlgc/servlets/%s" % servlet, params)
    data = f.read()
    f.close()
    return data

def GCMainMenu(sender):
    dir = MediaContainer(viewGroup="List")
    dir.Append(Function(DirectoryItem(GCMenu, title="Live games", thumb=R(NHL), art=R(ART)), channel="live"))
    dir.Append(Function(DirectoryItem(GCMenu, title="Archive", thumb=R(NHL), art=R(ART)), channel="archive"))
    # dir.Append(Function(DirectoryItem(GCMenu, title="Upcoming", thumb=R(NHL), art=R(ART))))
    return dir

def GCMenu(sender, channel=None, season=None, season_start=None, season_end=None, month=None, date=None, team=None, condensed=False):    
    handler = GCLogin() # Login
    
    # GC Archive – Shows seasons
    if (channel == "archive"):
        dir = MediaContainer(viewGroup="List")
        data = GCArchives(handler, {"date": "true"}, "allarchives")
        seasons = XML.ElementFromString(data.strip())
        for season in seasons:
            not_empty = season.xpath("./*[1]") # Won't display season that hasn't started yet
            if not_empty:
                season_start = Datetime.ParseDate(season.xpath("./*[1]")[0].text)
                season_end = Datetime.ParseDate(season.xpath("./*[last()]")[0].text)
                dir.Append(Function(DirectoryItem(GCMenu, title=season.get("id")), channel="season", season=season.get("id"), season_start=season_start, season_end=season_end))
    
    # GC Archive - Shows months
    if (channel == "season"):
        dir = MediaContainer(viewGroup="List")
        start_int = season_start.month
        end_int = season_end.month
        if (start_int > end_int):
            for month in range(start_int, 13):
                month_obj = Datetime.ParseDate("%s-%s-1" % (season_start.year, month))
                month_str = month_obj.strftime("%B")
                dir.Append(Function(DirectoryItem(GCMenu, title=month_str), channel="month", season=season, month=month))
            for month in range(1, end_int + 1):
                month_obj = Datetime.ParseDate("%s-%s-1" % (season_end.year, month))
                month_str = month_obj.strftime("%B")
                dir.Append(Function(DirectoryItem(GCMenu, title=month_str), channel="month", season=season, month=month))
    
    # GC Archive - Shows games for a specific month
    if (channel == "month"):
        dir = MediaContainer(viewGroup="InfoList")
        data = GCArchives(handler, {"season": season, "month": month})
        games = XML.ElementFromString(data.strip()).find("games")
        for game in games:
            gametitle = "%s vs. %s" % (game.find("./awayTeam").text, game.find("./homeTeam").text)
            gamedate = Datetime.ParseDate(game.find("./date").text)
            url = game.find(".//publishPoint").text
            Log(url)
            dir.Append(Function(WebVideoItem(PlayGC, title=gametitle, subtitle=gamedate), url=url))    
    return dir

def PopupMessage(sender,line1,line2):
    return MessageContainer(line1,line2)

def PlayGC(sender, url=None):
    handler = GCLogin() # Login
    if (Prefs["enable_hd"]):
        quality = "_hd"
    else:
        quality = "_sd"
    url = url.replace(".mp4", "%s.mp4" % quality) # Add quality to path
    params = urllib.urlencode({"type": "fvod", "isFlex": "true", "path": url})
    
    f = handler.open("http://gamecenter.nhl.com/nhlgc/servlets/encryptvideopath", params)
    data = f.read()
    f.close()
    url = XML.ElementFromString(data).find("./path").text
    # Split RTMP url & clip parameters
    split_url = re.split('/mp4', url)
    url = split_url[0]
    clip = "mp4%s" % split_url[1]
    if (Prefs["enable_hd"]):
        return Redirect(RTMPVideoItem(url, clip=clip, width=960, height=540))
    else:
        return Redirect(RTMPVideoItem(url, clip=clip, width=640, height=360))

### ESPN ###

def ESPNMenu(sender):
    dir = MediaContainer(viewGroup="List")
    dir.Append(Function(DirectoryItem(ESPNChannel, title="On today", thumb=R(NHL), art=R(ART)), channel="today"))
    dir.Append(Function(DirectoryItem(ESPNChannel, title="Archive", thumb=R(NHL), art=R(ART)), channel="archives"))
    dir.Append(Function(DirectoryItem(ESPNChannel, title="Upcoming", thumb=R(NHL), art=R(ART)), channel="upcoming"))
    return dir

def ESPNChannel(sender, channel=None):
    game_data = HTTP.Request("http://www.espnplayer.com/espnplayer/servlets/games", values = {"isFlex": "true", "product": "NHL_CENTER_ICE"}).content
    game_xml = XML.ElementFromString(game_data.strip())
    games_list = game_xml.find(".//%s" % channel)

    games = games_list.findall(".//game")

    dir = MediaContainer(viewGroup="InfoList")

    for game in games:
        name = game.find("./name").text

        url = game.find(".//publishPoint").text
        dir.Append(Function(WebVideoItem(PlayESPN, title=name, subtitle=game.find("./gameTime").text), url=url))

    return dir
    
def PlayESPN(sender, url=None):
    url = Decrypt(url, "espn")
    new_url = re.sub(r"\?e=", "_sd?e=", url)
    split_url = re.split('/mp4', new_url)
    url = split_url[0]
    clip = "mp4%s" % split_url[1]
    return Redirect(RTMPVideoItem(url, clip=clip, width=640, height=360))

def Decrypt(url, service="nhl", url_type="fvod"):
    return Helper.Run('decrypt', url, service, url_type) 
