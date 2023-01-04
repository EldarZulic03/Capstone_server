import pickle5 as pickle
import os
import shutil

#key: patient id
#value: person object
patients = {}

#key: patient id
#value: dict of loved one id -> loved one person
loved_ones = {}

#current patient uuid
patient_uuid = 1

#tracks current uuid for loved ones for each patient
#key is patient id, value is current id for loved one
patient_loved_one_uuid = 1

def save_to_disk(data, filename):
	with open('people_data/' + filename, 'wb') as handle:
		pickle.dump(data, handle)	

#get all patients
def get_all_patients():
	global patients
	return {"patients": [{"p_idx" : str(p), "name" : patients[p]["name"], "gender" : patients[p]["gender"], "DOB" : patients[p]["dob"]} for p in patients]}

#get all loved ones for a given patient
def get_all_loved_ones():
	global loved_ones
	res = []
	for p in loved_ones:
		loved_one_list = loved_ones[p]
		for loved_one in loved_one_list:
			lo = loved_one_list[loved_one]
			res.append({"p_idx":str(p),"lo_idx" : str(loved_one), "name" : lo["name"], "gender" : lo["gender"], "DOB" : lo["dob"]})		
	return {"loved_ones" : res}

#get a loved one
def get_loved_one(p_idx, lo_idx):
	#TODO: error handling here
	if p_idx in loved_ones:
		patient_loved_ones = loved_ones[p_idx]
		if lo_idx in patient_loved_ones:
			return patient_loved_ones[lo_idx]
		else:
			return ''
	else:
		return ''

#get a patient
def get_patient(idx):
	global patients
	if idx in patients:
		return patients[idx]
	#TODO: error handling here
	return ''

#delete a loved one
def delete_loved_one(p_idx, lo_idx):
	global loved_ones
	if p_idx in loved_ones:
		if lo_idx in loved_ones[p_idx]:
			loved_ones[p_idx].pop(lo_idx)
			save_to_disk(loved_ones,'loved_ones')
			shutil.rmtree('people_data/patient_data/'+str(p_idx)+'/'+str(lo_idx))
		else:
			return ''
	else:
		#TODO: error handling
		return ''

#delete a patient
def delete_patient(p_idx):
	global patients
	global loved_ones
	global patient_loved_one_uuid
	if p_idx in patients:
		patients.pop(p_idx)
		loved_ones.pop(p_idx)
		#patient_loved_one_uuid.pop(p_idx)
		save_to_disk(patients,'patients')
		save_to_disk(loved_ones,'loved_ones')
		#save_to_disk(patient_loved_one_uuid,'patient_loved_one_uuid')
		shutil.rmtree('people_data/patient_data/'+str(p_idx))
	else:
		return ''
#add loved one
def add_loved_one(p_idx, name, gender, dob, responses):
	loved_one = {"name":name,"gender":gender,"dob":dob}
	global patients
	global patient_loved_one_uuid
	global loved_ones
	if p_idx in patients:
		curr_idx = patient_loved_one_uuid
		patient_loved_one_uuid += 1
		loved_ones[p_idx][curr_idx] = loved_one
		save_to_disk(patient_loved_one_uuid,'patient_loved_one_uuid')
		save_to_disk(loved_ones,'loved_ones')
		os.mkdir('people_data/patient_data/' + str(p_idx) + '/' + str(curr_idx))
		os.mkdir('people_data/patient_data/' + str(p_idx) + '/' + str(curr_idx) + '/snippets')
		os.mkdir('people_data/patient_data/' + str(p_idx) + '/' + str(curr_idx) + '/snippets/audio')
		os.mkdir('people_data/patient_data/' + str(p_idx) + '/' + str(curr_idx) + '/snippets/video')	
		save_to_disk(responses, 'patient_data/{}/{}/responses'.format(p_idx,curr_idx))
		return {"patient_id" : str(p_idx), "id" : str(curr_idx), "name" : name, "gender" : gender, "DOB" : dob}
	else:
		print('Tried to add loved one for invalid patient')
		return {}

#add a patient
def add_patient(name, gender, dob, responses):
	patient = {"name":name,"gender":gender,"dob":dob}
	global patient_uuid
	global patients
	global loved_ones
	global patient_loved_one_uuid
	patients[patient_uuid] = patient
	loved_ones[patient_uuid] = {}
	#patient_loved_one_uuid[patient_uuid] = 1
	os.mkdir('people_data/patient_data/' + str(patient_uuid))
	patient_uuid += 1
	#save_to_disk(patient_loved_one_uuid,'patient_loved_one_uuid')
	save_to_disk(loved_ones,'loved_ones')
	save_to_disk(patients,'patients')
	save_to_disk(patient_uuid,'patient_uuid')
	save_to_disk(responses, 'patient_data/{}/responses'.format(patient_uuid - 1))
	return {"id" : str(patient_uuid - 1), "name" : name, "gender" : gender, "DOB" : dob}

#read existing data from disk, other wise initialize
def init():
	print("Initializing people manager")
	global patients
	global loved_ones
	global patient_uuid
	global patient_loved_one_uuid
	
	if os.path.exists('people_data') == False:
		os.mkdir('people_data')

	if os.path.exists('people_data/patient_data') == False:
		os.mkdir('people_data/patient_data')

	if os.path.exists('people_data/patients'):
		with open('people_data/patients', 'rb') as handle:
			patients = pickle.load(handle)
	
	if os.path.exists('people_data/loved_ones'):
		with open('people_data/loved_ones', 'rb') as handle:
			loved_ones = pickle.load(handle)

	if os.path.exists('people_data/patient_uuid'):
		with open('people_data/patient_uuid', 'rb') as handle:
			patient_uuid = pickle.load(handle)

	if os.path.exists('people_data/patient_loved_one_uuid'):
		with open('people_data/patient_loved_one_uuid', 'rb') as handle:
			patient_loved_one_uuid = pickle.load(handle)

	#for p in patients:
	#	print("Found patient {}:{} on init".format(p,patients[p].name))

def dump_all():
	print("###DUMP###")
	print(patients)
	print(loved_ones)
	print(patient_uuid)
	print(patient_loved_one_uuid)

print("Test")
#get_all_patients()
#init()
'''
dump_all()
add_patient("Steve James","male","11/08/2000")
dump_all()
add_patient("Bob John","male","8/09/2003")
dump_all()
delete_patient(1)
add_loved_one(2,"Bill","male","6/6/2003")
add_loved_one(2,"Jack","male","6/7/1999")
dump_all()
delete_loved_one(2,1)
dump_all()'''
