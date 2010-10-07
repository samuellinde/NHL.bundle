from core import *

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