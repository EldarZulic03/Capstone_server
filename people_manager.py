import pickle5 as pickle
import os
import shutil
import firebase_manager as fbm

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
	return fbm.get_all_patients()
	
#get all loved ones for a given patient
def get_all_loved_ones():
	return fbm.get_all_loved_ones()

#get a loved one
def get_loved_one(p_idx, lo_idx):
	#TODO: error handling here
	return fbm.get_loved_one(p_idx,lo_idx)

#get a patient
def get_patient(idx):
	#TODO: error handling here
	return fbm.get_patient(idx)

#delete a loved one
def delete_loved_one(p_idx, lo_idx):
	#TODO: error handling
	fbm.delete_loved_one(p_idx, lo_idx)
	
#delete a patient
def delete_patient(p_idx):
	#TODO: error handling
	fbm.delete_patient(p_idx)

#add loved one
def add_loved_one(p_idx, name, gender, dob, responses):
	curr_idx = fbm.add_loved_one(p_idx, name, gender, dob, responses)
	if not os.path.exists('people_data/patient_data/' + str(p_idx)):
		os.mkdir('people_data/patient_data/' + str(p_idx))	
	os.mkdir('people_data/patient_data/' + str(p_idx) + '/' + str(curr_idx))
	os.mkdir('people_data/patient_data/' + str(p_idx) + '/' + str(curr_idx) + '/snippets')
	os.mkdir('people_data/patient_data/' + str(p_idx) + '/' + str(curr_idx) + '/snippets/audio')
	os.mkdir('people_data/patient_data/' + str(p_idx) + '/' + str(curr_idx) + '/snippets/video')	
	save_to_disk(responses, 'patient_data/{}/{}/responses'.format(p_idx,curr_idx))
	return {"patient_id" : str(p_idx), "id" : str(curr_idx), "name" : name, "gender" : gender, "DOB" : dob}

#add a patient
def add_patient(name, gender, dob, responses):
	p_idx = fbm.add_patient(name, gender, dob, responses)
	os.mkdir('people_data/patient_data/' + str(p_idx))
	save_to_disk(responses, 'patient_data/{}/responses'.format(p_idx))
	return {"id" : str(p_idx), "name" : name, "gender" : gender, "DOB" : dob}

#read existing data from disk, other wise initialize
def init():
	print("Initializing people manager")
	if not os.path.exists('people_data'):
		os.mkdir('people_data')

	if not os.path.exists('people_data/patient_data'):
		os.mkdir('people_data/patient_data')

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
