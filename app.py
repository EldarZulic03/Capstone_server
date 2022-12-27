import sys
sys.path.append("wav2lip")
sys.path.append("voice_cloning")
from flask_restful import Api, Resource, reqparse
import numpy as np 
import select
import subprocess
import base64
import json
import os
from flask import Flask, render_template, request, session, redirect, Response
from flask_session import Session
import shutil
import cv2
import pickle5 as pickle
import people_manager as pm
import wav2lip_wrapper as w2l
import voice_cloning_wrapper as vcl
import firebase_manager as fbm
import chatbot as cb
from pydub import AudioSegment
from multiprocessing import Process

NUM_PROCESSES = 4
models = {}
patient_responses_dict = {}
loved_one_responses_dict = {}

#TODO: do this cleaner
#because dictionary entries have commas in them we get the as a string like:
# "key:val;key:val;"
def process_responses(responses):
	#trim last ; off and split
	question_answers = responses[:-1].split(';')
	res = {}
	for qa in question_answers:
		qa = qa.split(':')
		res[qa[0]] = qa[1]
	return res

#lowercase and remove spaces in filename 
def get_fname_for_sentence(sentence):
	words = sentence.lower()
	fname = ''
	for letter in words:
		if not letter.isalpha():
			continue
		else:
			fname += letter
	return fname

def upload_snippets(patient, loved_one):
	base_path = "people_data/patient_data/{}/{}/".format(patient, loved_one)
	face = base_path + "face.jpeg"
	voice = base_path + "voice.wav"
	snippets = base_path + "snippets/"
	
	#upload all the snippets to the cloud
	for filename in os.listdir(snippets+"video"):
		dst_file = "{}/{}/{}".format(patient, loved_one, filename)
		url = fbm.upload_file(os.path.join(snippets,"video",filename),dst_file)
		print(url)


#TODO: upload to firebase
def gen_snippets(patient, loved_one, sentences):
	print("Generating Snippets")
	base_path = "people_data/patient_data/{}/{}/".format(patient, loved_one)
	face = base_path + "face.jpeg"
	voice = base_path + "voice.wav"
	snippets = base_path + "snippets/"
	vc = vcl.VoiceChanger()
	vc.load_and_set_new_model(voice,"{}_{}".format(patient,loved_one))
	#create .wavs for sentences
	for sentence in sentences:
		fname = get_fname_for_sentence(sentence)
		vc.synthesize_sentence(sentence,snippets+"audio/"+fname+".wav")
	#sync the audio created above to the face image
	for filename in os.listdir(snippets+"audio"):
		vid_name = filename.split('.')[0] + '.mp4'
		f = os.path.join(snippets+"audio", filename)
		ls = w2l.LipSyncer(f, face, snippets + 'video/' + vid_name)
		ls.gen()	


#Train the models
#TODO: eventaully we cant keep using placeholder data
def train_models(patient,loved_one):
	#temporarily use placeholder data until audio upload is working...
	shutil.copyfile('test_data/trump.jpeg', 'people_data/patient_data/{}/{}/face.jpeg'.format(patient,loved_one))	
	shutil.copyfile('test_data/trump.wav', 'people_data/patient_data/{}/{}/voice.wav'.format(patient,loved_one))

	loved_one_responses = {} 
	patient_responses = {}
	with open('people_data/patient_data/{}/responses'.format(patient), 'rb') as handle:
		patient_responses = pickle.load(handle)	
	with open('people_data/patient_data/{}/{}/responses'.format(patient,loved_one), 'rb') as handle:
		loved_one_responses = pickle.load(handle)
	#merge them
	print(patient_responses)
	print(loved_one_responses)
	responses = cb.get_possible_responses(patient_responses, loved_one_responses)
	
	print(responses)
	
	processes = []
	num_responses = len(responses)
	responses_per_process = int(num_responses / 4)
	start_idx = 0
	end_idx = responses_per_process
	for i in range(NUM_PROCESSES):
		#in case its not divisible by NUM_PROCESSES evenly
		if i == NUM_PROCESSES - 1:
			end_idx = num_responses

		print("Assigning {}:{} to process {}".format(start_idx,end_idx,i))
		p_responses = responses[start_idx : end_idx]
		p = Process(target=gen_snippets, args=(patient, loved_one, p_responses))
		p.start()
		processes.append(p)
		start_idx = end_idx
		end_idx += responses_per_process

	
	for p in processes:
		p.join()
	


	#upload all the snippets to the cloud, sometimes this fails so retry
	try:
		upload_snippets(patient, loved_one)
	except:
		print("Snippet upload failed, trying again")	
		upload_snippets(patient, loved_one)


#create main app
app = Flask(__name__)
api = Api(app)

@app.route('/training_data', methods=['POST'])
def training_data():
	data = request.get_json()
	print(data)
	p_idx = data['p_idx']
	lo_idx = data['lo_idx']
	base_dir = 'people_data/patient_data/{}/{}/'.format(p_idx,lo_idx)
	fbm.download_file("training_data/face.jpeg",base_dir + "face.jpeg")
	fbm.download_file("training_data/voice.m4a",base_dir + "voice.m4a")
	m4a_file = base_dir + 'voice.m4a'
	wav_filename = base_dir + "voice.wav"
	track = AudioSegment.from_file(m4a_file,  format= 'm4a')
	file_handle = track.export(wav_filename, format='wav')
	train_models(p_idx, lo_idx)
	return {"status" : "succeeded"}

@app.route('/all_patients', methods=['GET'])
def all_patients():
	if request.method == 'GET':
		return pm.get_all_patients()

@app.route('/all_loved_ones/', methods=['GET'])
def all_loved_ones():
	if request.method == 'GET':
		return pm.get_all_loved_ones()

@app.route('/patients', methods=['POST','DELETE'])
def manage_patient():
	data = request.get_json()
	print(data) 
	if request.method == 'POST':
		responses = process_responses(data['responses'])
		responses['name'] = data['name']
		responses['gender'] = data['gender']
		responses['date_of_birth'] = data['DOB']
		print(responses)
		return pm.add_patient(data['name'], data['gender'], data['DOB'], responses)
	elif request.method == 'DELETE':
		pm.delete_patient(int(data['p_idx']))
		return {}

@app.route('/loved_ones', methods=['POST','DELETE'])
def manage_loved_one():
	data = request.get_json()
	print(data)
	if request.method == 'POST':
		responses = process_responses(data['responses'])
		responses['name'] = data['name']
		responses['gender'] = data['gender']
		responses['date_of_birth'] = data['DOB']
		print(responses)
		return pm.add_loved_one(int(data['p_idx']),data['name'], data['gender'], data['DOB'], responses)
	elif request.method == 'DELETE':
		pm.delete_loved_one(int(data['p_idx']),int(data['lo_idx']))
		return {}

@app.route('/responses', methods=['POST'])
def get_response():
	data = request.get_json()
	print(data)
	if request.method == 'POST':
		loved_one = data['lo_idx']
		user_input = data['input']
		patient = data['p_idx']

		#load the responses in memory since there will be heavy reuse
		if patient not in patient_responses_dict:
			with open('people_data/patient_data/{}/responses'.format(patient), 'rb') as handle:
				patient_responses = pickle.load(handle)
				patient_responses_dict[patient] = patient_responses
		if loved_one not in loved_one_responses_dict:
			with open('people_data/patient_data/{}/{}/responses'.format(patient,loved_one), 'rb') as handle:
				loved_one_responses = pickle.load(handle)
				loved_one_responses_dict[loved_one] = loved_one_responses
		
		loved_one_responses = loved_one_responses_dict[loved_one] 
		patient_responses = patient_responses_dict[patient]
		response = cb.generate_response(models['chatbot'], user_input, patient_responses, loved_one_responses)
		return {"response" : get_fname_for_sentence(response) + '.mp4'}

if __name__ == "__main__":
	pm.init()
	fbm.init()
	models['chatbot'] = cb.train_model()
	app.run(debug=True)
