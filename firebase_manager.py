from firebase_admin import credentials, initialize_app, storage


def init():
	# Init firebase with your credentials
	cred = credentials.Certificate("virtual-presence-app-2a440e2cacfc.json")
	initialize_app(cred, {'storageBucket': 'virtual-presence-app.appspot.com'})


def upload_file(fileName, dstFile):
	bucket = storage.bucket()
	blob = bucket.blob(dstFile)
	blob.upload_from_filename(fileName)
	blob.make_public()
	return blob.public_url

def download_file(cloud_file_name, to_file):
	bucket = storage.bucket()
	blob = bucket.blob(cloud_file_name)
	blob.download_to_filename(to_file)	

#init()
#download_file("img.jpeg","image.jpeg")
#res = upload_file("image.jpeg","test.jpeg")
#print("your file url {}".format(res))
