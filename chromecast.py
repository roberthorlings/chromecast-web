#!/usr/bin/python

import pychromecast
import web
import json
import time

#
# Variables to set. 
#

# IP address of the chromecast to control
chromecast_ip = "192.168.178.32"

# Prefix for all URLs to be handled. E.g. if the application runs on http://localhost/chromecast, 
# the prefix should be "/chromecast"
url_prefix = "/chromecast"

# Timeout to wait for the status (ms)
status_timeout = 8000

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

	cast = pychromecast.Chromecast(host=chromecast_ip)

	# We can only use the controller when a status has been retrieved
	# For that reason, we wait for that event 
	status_handler = StatusHandler(cast)
	cast.socket_client.receiver_controller.register_status_listener(status_handler)
	cast.media_controller.register_status_listener(status_handler)
	
	# Wait for the status, although not forever
	starttime = time.time() * 1000
	wait_until = starttime + status_timeout
	while ( time.time() * 1000 ) < wait_until and not ( status_handler.cast_status and status_handler.media_status ):
		pass
	
	return cast

# 
# Web.py part to initialize the application
#

urls = (
    url_prefix + '/status', 'status',
    url_prefix + '/fullstatus', 'full_status',
    url_prefix + '/mediastatus', 'media_status',
    
    url_prefix + '/play', 'play',
    url_prefix + '/pause', 'pause',
    url_prefix + '/stop', 'stop',
    
    url_prefix + '/skip', 'skip',
    
    url_prefix + '/volume', 'volume',
    url_prefix + '/mute', 'mute',
    url_prefix + '/unmute', 'unmute'
)

class status:
    def GET(self):
    	try:
            cast = get_cast_with_status(chromecast_ip)
        except pychromecast.error.ChromecastConnectionError:
            return web.notfound("Chromecast not found at IP " + chromecast_ip)
        
        if( cast.status ):    
            return json.dumps(cast.status.__dict__)
        else:
            return ""
            

class media_status:
    def GET(self):
    	try:
            cast = get_cast_with_status(chromecast_ip)
        except pychromecast.error.ChromecastConnectionError:
            return web.notfound("Chromecast not found at IP " + chromecast_ip)
        
        if( cast.media_controller and cast.media_controller.status ):    
            return json.dumps(cast.media_controller.status.__dict__)
        else:
            return ""

class full_status:
    def GET(self):
        try:
            cast = get_cast_with_status(chromecast_ip)
        except pychromecast.error.ChromecastConnectionError:
            return web.notfound("Chromecast not found at IP " + chromecast_ip)

        return json.dumps({ 
        	'cast': cast.status.__dict__ if cast.status else {}, 
        	'media': cast.media_controller.status.__dict__ if cast.media_controller else {}
        })

class play:
    def POST(self):
    	try:
            cast = pychromecast.Chromecast(host=chromecast_ip)
        except pychromecast.error.ChromecastConnectionError:
            return web.notfound("Chromecast not found at IP " + chromecast_ip)
    	
        cast.media_controller.play()
        return ""

class pause:
    def POST(self):
    	try:
            cast = get_cast_with_status(chromecast_ip)
        except pychromecast.error.ChromecastConnectionError:
            return web.notfound("Chromecast not found at IP " + chromecast_ip)
    	
    	if cast.is_idle: 
    		return web.BadRequest("Cast is currently idle")

    	if not cast.media_controller.status.supports_pause: 
    		return web.BadRequest("Current media doesn't support pause")
    
        cast.media_controller.pause()
        return ""

class stop:
    def POST(self):
    	try:
            cast = pychromecast.Chromecast(host=chromecast_ip)
        except pychromecast.error.ChromecastConnectionError:
            return web.notfound("Chromecast not found at IP " + chromecast_ip)
    	
        cast.media_controller.stop()
        return ""

class skip:
    def POST(self):
    	try:
            cast = get_cast_with_status(chromecast_ip)
        except pychromecast.error.ChromecastConnectionError:
            return web.notfound("Chromecast not found at IP " + chromecast_ip)
    	
    	if cast.is_idle: 
    		return web.BadRequest("Cast is currently idle")

    	if not cast.media_controller.status.supports_seek: 
    		return web.BadRequest("Current media doesn't support skipping")
    
        cast.media_controller.skip()
        return ""

class volume:
    def POST(self):
    	# Volume is given as 0 - 100, but is transformed into 0..1
    	user_data = web.input()
    	volume = int(user_data.volume)
    	
    	if(volume < 0 or volume > 100):
    		return web.BadRequest("Invalid volume. Valid range is between 0 and 100")
    		
    	try:
            cast = pychromecast.Chromecast(host=chromecast_ip)
        except pychromecast.error.ChromecastConnectionError:
            return web.notfound("Chromecast not found at IP " + chromecast_ip)
            
        cast.set_volume( volume / 100.0 )
        return ""

class mute:
    def POST(self):
    	try:
            cast = pychromecast.Chromecast(host=chromecast_ip)
        except pychromecast.error.ChromecastConnectionError:
            return web.notfound("Chromecast not found at IP " + chromecast_ip)
        
        return ""

class unmute:
    def POST(self):
    	try:
            cast = pychromecast.Chromecast(host=chromecast_ip)
        except pychromecast.error.ChromecastConnectionError:
            return web.notfound("Chromecast not found at IP " + chromecast_ip)
        return ""

def common_headers():
    web.header('Content-type', "application/json")
    web.header('Access-Control-Allow-Origin', "*")

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(common_headers))
    app.run()

