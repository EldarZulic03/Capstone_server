from firebase_admin import credentials, initialize_app, storage


def init():
	# Init firebase with your credentials
	cred = credentials.Certificate("test-873a0-5403e52fd2d9.json")
	initialize_app(cred, {'storageBucket': 'test-873a0.appspot.com'})


def upload_file(fileName, dstFile):
	bucket = storage.bucket()
	blob = bucket.blob(dstFile)
	blob.upload_from_filename(fileName)
	blob.make_public()
	return blob.public_url

#init()
#res = upload_file("img.jpeg","0/0/test.jpeg")
#print("your file url {}".format(res))
