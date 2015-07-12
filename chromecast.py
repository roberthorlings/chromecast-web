import pychromecast
import web
import json

# Variables to set. 
chromecast_ip = "192.168.178.23"

"""
Handles status updates 
"""
class StatusHandler(object):
    def __init__(self, cast):
        """
        Initialize the handler

        cast:              the chromecast object to work with
        """
        self.cast = cast
        self.cast_status = False
        self.media_status = False

    def new_cast_status(self, status):
        self.cast_status = True
        
    def new_media_status(self,status):
    	self.media_status = True

"""
Returns a chromecast object filled with the status
"""
def get_cast_with_status(chromecast_ip):
	#cast = pychromecast.get_chromecast(friendly_name=chromecast_friendly_name)
	cast = pychromecast.Chromecast(host=chromecast_ip)
	
	# We can only use the controller when a status has been retrieved
	# For that reason, we wait for that event 
	status_handler = StatusHandler(cast)
	cast.socket_client.receiver_controller.register_status_listener(status_handler)
	cast.media_controller.register_status_listener(status_handler)
	
	while not ( status_handler.cast_status and status_handler.media_status ):
		pass
		
	return cast

# 
# Web.py part to initialize the application
#

urls = (
    '/status', 'status',
    '/mediastatus', 'media_status',
    
    '/play', 'play',
    '/pause', 'pause',
    '/stop', 'stop',
    
    '/skip', 'skip',
    
    '/volume/(\d+)', 'volume',
    '/mute', 'mute',
    '/unmute', 'unmute'
)

class status:
    def GET(self):
    	web.header("Content-Type", "application/json")
        return json.dumps(get_cast_with_status(chromecast_ip).status.__dict__)

class media_status:
    def GET(self):
    	web.header("Content-Type", "application/json")
        return json.dumps(get_cast_with_status(chromecast_ip).media_controller.status.__dict__)

class play:
    def POST(self):
    	cast = get_cast_with_status(chromecast_ip)
    	
    	if cast.is_idle(): 
    		return web.BadRequest("Cast is currently idle")
    		
        cast.media_controller.play()
        return ""

class pause:
    def POST(self):
    	cast = get_cast_with_status(chromecast_ip)
    	
    	if cast.is_idle(): 
    		return web.BadRequest("Cast is currently idle")

    	if not cast.media_controller.status.supports_pause(): 
    		return web.BadRequest("Current media doesn't support pause")
    
        cast.media_controller.pause()
        return ""

class stop:
    def POST(self):
    	cast = get_cast_with_status(chromecast_ip)
    	
    	if cast.is_idle(): 
    		return web.BadRequest("Cast is currently idle")
    		
        cast.media_controller.stop()
        return ""

class skip:
    def POST(self):
    	cast = get_cast_with_status(chromecast_ip)
    	
    	if cast.is_idle(): 
    		return web.BadRequest("Cast is currently idle")

    	if not cast.media_controller.status.supports_seek(): 
    		return web.BadRequest("Current media doesn't support skipping")
    
        cast.media_controller.skip()
        return ""

class volume:
    def POST(self, givenVolume):
    	# Volume is given as 0 - 100, but is transformed into 0..1
    	volume = int(givenVolume)
    	
    	if(volume < 0 or volume > 100):
    		return web.BadRequest("Invalid volume. Valid range is between 0 and 100")
    		
        get_cast_with_status(chromecast_ip).set_volume( volume / 100.0 )
        return ""

class mute:
    def POST(self):
        get_cast_with_status(chromecast_ip).set_volume_muted(True)
        return ""

class unmute:
    def POST(self):
        get_cast_with_status(chromecast_ip).set_volume_muted(False)
        return ""

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()

