from firebase_admin import credentials, initialize_app, storage, firestore

db = []
def init():
	# Init firebase with your credentials
	cred = credentials.Certificate("virtual-presence-app-2a440e2cacfc.json")
	initialize_app(cred, {'storageBucket': 'virtual-presence-app.appspot.com'})
	global db
	db = firestore.client()

def reset_counters():
	tmp = {'idx' : 1}
	db.collection('indices').document('p_index').set(tmp)
	db.collection('indices').document('lo_index').set(tmp)


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

#TODO: Need to synchronize here across servers
def get_counter_and_increment(index_doc):
	ref = db.collection('indices').document(index_doc)
	val = dict_ref = ref.get().to_dict()['idx']
	ref.update({'idx' : firestore.Increment(1)})
	return val

def add_patient(name, gender, dob, responses):
	p_idx = get_counter_and_increment('p_index')
	entry = {'name' : name, 'gender' : gender, 'dob' : dob, 'loved_ones' : {}, 'responses' : responses}
	db.collection('patients').document(str(p_idx)).set(entry)
	return p_idx

def get_patient(p_idx):
	return db.collection('patients').document(str(p_idx)).get().to_dict()

def get_loved_one(p_idx, lo_idx):
	return db.collection('patients').document(str(p_idx)).get().to_dict()['loved_ones'][str(lo_idx)]

def add_loved_one(p_idx, name, gender, dob, responses):
	lo_idx = get_counter_and_increment('lo_index')
	entry = {'name' : name, 'gender' : gender, 'dob' : dob, 'responses' : responses}
	patient_doc = db.collection('patients').document(str(p_idx))
	patient_doc.update({'loved_ones.{}'.format(lo_idx) : entry})
	return lo_idx

def delete_loved_one(p_idx,lo_idx):
	patient_doc = db.collection('patients').document(str(p_idx))
	patient_doc.update({'loved_ones.{}'.format(lo_idx) : firestore.DELETE_FIELD})

def delete_patient(p_idx):
	db.collection('patients').document(str(p_idx)).delete()	

def get_all_patients():
	patients = db.collection('patients').stream()
	res = []
	for patient in patients:
		p_dict = patient.to_dict()
		p = {"p_idx": str(patient.id), "name" : p_dict["name"], "gender" : p_dict["gender"], "DOB" : p_dict["dob"]}
		res.append(p)
	return {"patients" : res}

def get_all_loved_ones():
	patients = db.collection('patients').stream()
	res = []
	for patient in patients:
		p_dict = patient.to_dict()
		loved_ones = p_dict['loved_ones']
		for loved_one in loved_ones:
			lo = {"p_idx": str(patient.id), "lo_idx" : str(loved_one),"name" : loved_ones[loved_one]["name"], "gender" : loved_ones[loved_one]["gender"], "DOB" : loved_ones[loved_one]["dob"]}
			res.append(lo)
	return {"loved_ones" : res}

def test():
	print(get_all_patients())
	print(get_all_loved_ones())
	#reset_counters()
	#delete_patient(1)
	#print(get_loved_one(1,3))
	#delete_loved_one(1,5)
	#add_patient('Tim','Male','2022/11/11', {'hobbies' : 'running', 'city' : 'ajax'})
	#add_patient('Jim','Male','2022/8/7', {'hobbies' : 'eating', 'city' : 'pickering'})
	#add_loved_one(1,'Rob','Male','2022/8/7', {'hobbies' : 'jumping', 'city' : 'oshawa'})
	#add_loved_one(2,'Bob','Male','2022/8/7', {'hobbies' : 'jumping', 'city' : 'oshawa'})
	#add_loved_one(1,'Rick','Male','2022/8/7', {'hobbies' : 'jumping', 'city' : 'oshawa'})
	#add_loved_one(1,'Thomas','Male','2022/8/7', {'hobbies' : 'eating', 'city' : 'pickering'})
	#for i in range(5):
	#	print(get_counter_and_increment('lo_index'))

	#db = firestore.client()  # this connects to our Firestore database
	#collection = db.collection('places')  # opens 'places' collection
	#doc = collection.document('rome')  # specifies the 'rome' document

	#download_file("img.jpeg","image.jpeg")
	#res = upload_file("image.jpeg","test.jpeg")
	#print("your file url {}".format(res))

#test()
