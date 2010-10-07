from core import *

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