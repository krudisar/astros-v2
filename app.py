from flask import Flask, render_template
import os
import requests
import requests_cache
import json
import datetime, time
import socket
from pymongo import MongoClient
import pymongo
from bson import json_util

import wavefront_api_client

# ------ WAVEFRONT INTEGRATION -------

# Configure API key authorization: api_key
wavefrontConfiguration = wavefront_api_client.Configuration()
wavefrontConfiguration.host = 'https://vmware.wavefront.com'
wavefrontConfiguration.api_key['X-AUTH-TOKEN'] = '7dd79888-59fb-42f0-84a7-2a83545de7f0'

wavefrontApiInstance = wavefront_api_client.DirectIngestionApi(wavefront_api_client.ApiClient(wavefrontConfiguration))
wavefrontDataFormat = 'wavefront' 
wavefrontMetricSourceName_AstroApiResponse = 'kr.astro.external.api.response'

wavefrontMetricName_AstroApiResponse = 'kr.astro.api'
wavefrontMetricName_GoogleApiResponse = 'kr.google.api'

def wavefrontDirectSenderSingleMetric(wavefrontMetricName, wavefrontMetricSourceName, metricValue):
	body = wavefrontMetricName + ' ' + str(metricValue) + ' source=' + wavefrontMetricSourceName
	wavefrontApiInstance.report(f=wavefrontDataFormat, body=body)
	return body

# ------------------------------------

# ------ local imports
from package.search_functions import get_image_url

app = Flask(__name__)

# GLOBALS =================
x = []
url_web_service = 'http://api.open-notify.org/astros.json'
# =========================


# OLD - mongodb_server_url = "mongodb://127.0.0.1:27017"
mongodb_server_url = "mongodb://mongodb:27017"

_MONGODB_SERVER_READY_ = False
_OPTIMIZED_PHOTOS_RETRIEVAL_ = False
db = None

print("")
# ----- ENABLE REST API RESPONSE CACHING -------

if (int(os.environ.get('CACHE_API_REQUESTS')) != 0):
	print("API Request Caching Enabled ...")
	requests_cache.install_cache(cache_name='api_cache', backend='memory', expire_after=1800)
else:
	print("API Request Caching Disabled ...")

# ----------------------------------------------

if (int(os.environ.get('CACHE_IMAGES_IN_DB')) != 0):
	print("Image Caching In Database Enabled ... ")
	_OPTIMIZED_PHOTOS_RETRIEVAL_ = True
else:
	print("Image Caching In Database Disabled ... ")

# ----------------------------------------------------------------

class Astronaut:
    def __init__(self, name, craft, photo_url):
        self.name = name
        self.craft = craft
        self.photo_url = photo_url
        
    # return dictionary json representation of thuis class
    def to_document(self):
            return dict(
                name = self.name,
                craft = self.craft,
                photo_url = self.photo_url,
            )

    @classmethod
    def from_document(cls, doc):
            return cls(
                name = doc['name'],
                craft = doc['craft'],
                photo_url = doc['photo_url'],
            )
    def get(self):
        return to_document()

# ----------------------------------------------------------------

# populate name & url structure from webservice response
def processAstros(json_object):
	global x
	
	x=[]
	for item in json_object['people']:
		# check if item['name'] is in MongoDB
		# if yes then pull data and create object type Astronauts
		# if not then request Google Search

		search_string = {'name' : item["name"]}

		record_from_db = astronauts.find(search_string)
		
		if (_OPTIMIZED_PHOTOS_RETRIEVAL_ and (record_from_db.count() > 0)):
			
			astro = Astronaut(record_from_db[0]["name"], record_from_db[0]["craft"], record_from_db[0]["photo_url"])
			x.append(astro)

		else:

			item["photo_url"] = get_image_url(item['name'])
			x.append(item)

			astro = Astronaut(item["name"], item["craft"], item['photo_url'])
			result = astronauts.insert_one(astro.to_document())

	return x

# --------------------------------------------------------------------
@app.route('/api/get', methods=['GET'])
def get_none():
	#global client 
	global astronauts

	if _MONGODB_SERVER_READY_:
		res = astronauts.find({},{"name":1, "craft":1, "photo_url":1, "_id":0})
		dump = json.dumps([doc for doc in res], sort_keys=False, indent=4, default=json_util.default)
		return dump
	else:
		return "{'response': 'NO_DATA_AVAILABLE'}"


# --------------------------------------------------------------------
@app.route('/')
def hello_world():
	r = requests.get(url_web_service)
	d = r.json()

	# get current date & time
	now = datetime.datetime.now()

	return render_template("index.html", current_date = now.strftime("%Y-%m-%d %H:%M:%S"), hostname = socket.gethostname())


# --------------------------------------------------------------------
@app.route("/test")
def test():

	# -------
	start_time = time.time()
	# -------

	# get json data from external REST API Endpoint
	r = requests.get(url_web_service)
	d = r.json()

	# ------- WAVEFRONT ACTION => Inject Data ---------
	wavefrontDirectSenderSingleMetric(wavefrontMetricName_AstroApiResponse, 
		wavefrontMetricSourceName_AstroApiResponse, 
		r.elapsed.total_seconds())
	# -------------------------------------------------


	# -------
	start_time = time.time()
	# -------

	# populate name & url structure from webservice response, where x is a global array
	processAstros(d)

	# ------- WAVEFRONT ACTION => Inject Data ---------
	wavefrontDirectSenderSingleMetric(wavefrontMetricName_GoogleApiResponse, 
		wavefrontMetricSourceName_AstroApiResponse, 
		time.time() - start_time)
	# -------------------------------------------------

	return render_template("people.html", dd=x)	

# --------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
  return 'custom 404'
  #return render_template('path_folder/404.html'), 404


# --------------------------------------------------------------------
if __name__ == '__main__':
	client = MongoClient(mongodb_server_url) 

	# Send a query to the server to see if the connection is working.
	try:
	    client.server_info()
	    _MONGODB_SERVER_READY_ = True

	    # select our project's database  
	    db = client.kr_mongodb    
	    
	    # delete the whole collection to start with no data
	    db.a.delete_many({})

	    # create a new collection 'astros'
	    astronauts = db.astros

	    print("Successfully connected to MongoDB Server !!! - Starting servicing clients ..." + "\n")
	except pymongo.errors.ServerSelectionTimeoutError as e:
	    print("Unable to connect to MONGODB server !!! - Exiting ...")
	    client = None
	    exit(1)

app.run(debug=True,host='0.0.0.0')

