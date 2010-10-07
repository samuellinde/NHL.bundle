####################################################################################################
VIDEO_PREFIX = "/video/nhl"
NAME         = L('Title')
ART          = 'art-default.jpg'
ICON         = 'icon-default.png'
NHL          = 'nhl.png'
####################################################################################################

def Decrypt(url, service="nhl", url_type="fvod"):
    return Helper.Run('decrypt', url, service, url_type)
    
def PopupMessage(sender,line1,line2):
    return MessageContainer(line1,line2)