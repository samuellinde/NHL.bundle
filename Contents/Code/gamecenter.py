from core import *

### Gamecenter ###

def GCLogin():
    handler = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    urllib2.install_opener(handler)
    u = Prefs['gc_username']
    p = Prefs['gc_password']
    params = urllib.urlencode({"username": u, "password": p})
    f = handler.open("https://gamecenter.nhl.com/nhlgc/secure/login", params)
    headers = f.info().headers
    data = f.read()
    loginresult = XML.ElementFromString(data).find("./code").text
    f.close()
    return (handler, headers, loginresult)


def GCArchives(handler, params, servlet="archives"):
    # Returns XML for GC archives
    params = urllib.urlencode(dict({"isFlex": "true"}.items() + params.items())) # Add params to the "isFlex"
    f = handler.open("http://gamecenter.nhl.com/nhlgc/servlets/%s" % servlet, params)
    data = f.read()
    f.close()
    return data

def GCMainMenu(sender):
    if (Prefs["gc_username"] and Prefs["gc_password"]):
        dir = MediaContainer(viewGroup="List")
        dir.Append(Function(DirectoryItem(GCMenu, title="Live games", thumb=R(NHL), art=R(ART)), channel="live"))
        dir.Append(Function(DirectoryItem(GCMenu, title="Archive", thumb=R(NHL), art=R(ART)), channel="archive"))
        # dir.Append(Function(DirectoryItem(GCMenu, title="Upcoming", thumb=R(NHL), art=R(ART))))
        return dir
    else:
        return MessageContainer("No username or password entered", "Please enter your Gamecenter credentials in the preferences.")

def GCMenu(sender, channel=None, season=None, season_start=None, season_end=None, month=None, date=None, team=None, condensed=False):    
    handler, headers, loginresult = GCLogin() # Login
    
    if (loginresult == "loginfailed"):
        return MessageContainer("Login failed", "Please check your Gamecenter credentials in the preferences")
    
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
            dir.Append(Function(WebVideoItem(PlayGC, title=gametitle, subtitle=gamedate), url=url))    
    return dir

def PlayGC(sender, url=None):
    handler, headers, loginresult = GCLogin() # Login
    if (loginresult == "loginfailed"):
        return MessageContainer("Login failed", "Please check your Gamecenter credentials in the preferences")
    if (Prefs["enable_hd"]):
        quality = "_hd"
    else:
        quality = "_sd"
    url = url.replace(".mp4", "%s.mp4" % quality) # Add quality to path
    # Create cookie string
    cookies = []
    for h in headers:
        if h[0:10] == "Set-Cookie":
            cookies.append(h[12:-2])
    cookie_string = ', '.join(cookies)
    url = DecryptGC(url, cookie_string) # Pass params to GC helper
    split_url = re.split('/mp4', url)
    url = split_url[0]
    clip = "mp4%s" % split_url[1]
    if (Prefs["enable_hd"]):
        return Redirect(RTMPVideoItem(url, clip=clip, width=960, height=540))
    else:
        return Redirect(RTMPVideoItem(url, clip=clip, width=640, height=360))

def DecryptGC(url, cookies):
    return Helper.Run('decrypt_gc', url, cookies) 
