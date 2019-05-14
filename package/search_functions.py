from google_images_download import google_images_download   #importing the library
import string
import json
import sys

def get_image_url(search_string):

	orig_stdout = sys.stdout
	f = open('URLS.txt', 'w')
	sys.stdout = f

	response = google_images_download.googleimagesdownload() 

	arguments = "{\"keywords\":\"" + search_string + " astronaut\",\"limit\":1,\"print_urls\":\"True\",\"Size\":\"<100KB\"}"
	
	paths = response.download(json.loads(arguments))   #passing the arguments to the function

	sys.stdout = orig_stdout
	f.close()

	with open('URLS.txt') as f:
	    content = f.readlines()
	f.close()

	urls = []
	for j in range(len(content)):
		if content[j][:9] == 'Completed':
			urls.append(content[j-1][11:-1])  

	return urls[0]


	