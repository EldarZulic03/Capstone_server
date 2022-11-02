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

import pyaudio
import cv2

import people_manager as pm
import wav2lip_wrapper as w2l
import voice_cloning_wrapper as vcl
import firebase_manager as fbm

#TODO: do this cleaner
def process_responses(responses):
	#trim last ; off and split
	question_answers = responses[:-1].split(';')
	res = {}
	for qa in question_answers:
		qa = qa.split(':')
		res[qa[0]] = qa[1]
	return res

#TODO: need to talk to chatbot api to get these
def get_sentences(patient, loved_one):
	return ["this is a test sentence", "this is another test sentence", "this is the last test sentence"]

#TODO: upload to firebase
def gen_snippets(patient, loved_one):
	base_path = "people_data/patient_data/{}/{}/".format(patient, loved_one)
	face = base_path + "face.jpg"
	voice = base_path + "voice.wav"
	snippets = base_path + "snippets/"
	sentences = get_sentences(patient, loved_one)
	vc = vcl.VoiceChanger()
	vc.load_and_set_new_model(voice,"{}_{}".format(patient,loved_one))
	#create .wavs for sentences
	for sentence in sentences:
		words = sentence.lower()
		words = words.split()
		fname = ''
		for word in words:
			fname += word
		vc.synthesize_sentence(sentence,snippets+"audio/"+fname+".wav")
	#sync the audio created above to the face image
	for filename in os.listdir(snippets+"audio"):
		vid_name = filename.split('.')[0] + '.mp4'
		f = os.path.join(snippets+"audio", filename)
		ls = w2l.LipSyncer(f, face, snippets + 'video/' + vid_name)
		ls.gen()	
	#upload all the snippets to the cloud
	for filename in os.listdir(snippets+"video"):
		dst_file = "{}/{}/{}".format(patient, loved_one, filename)
		url = fbm.upload_file(os.path.join(snippets,"video",filename),dst_file)
		print(url)

#create main app
app = Flask(__name__)
api = Api(app)

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5

audio1 = pyaudio.PyAudio()

#camera = cv2.VideoCapture(0)

#can use this to stream in the AI's deepfake output
#how to send over sound?
def gen_frames():
	image_paths = ['./Resources/Images/fly_dog.jpg', './Resources/Images/jump_dog.jpg']
	i = 0
	while True:
		# success, frame = camera.read() 
		frame = cv2.imread(image_paths[i])
		success = True
		i += 1
		if i >= 2:
			i = 0

		if not success:
			break
		else:
			ret, buffer = cv2.imencode('.jpg', frame)
			frame = buffer.tobytes()
			#concatenates frames one by one
			yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def genHeader(sampleRate, bitsPerSample, channels):
    datasize = 2000*10**6
    o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                              # (4byte) File type
    o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
    o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
    return o

@app.route('/audio')
def audio():
    # start Recording
    def sound():

        CHUNK = 1024
        sampleRate = 44100
        bitsPerSample = 16
        channels = 2
        wav_header = genHeader(sampleRate, bitsPerSample, channels)

        stream = audio1.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,input_device_index=1,
                        frames_per_buffer=CHUNK)
        print("recording...")
        #frames = []
        first_run = True
        while True:
           if first_run:
               data = wav_header + stream.read(CHUNK)
               first_run = False
           else:
               data = stream.read(CHUNK)
           yield(data)

    return Response(sound())

@app.route("/wav")
def streamwav():
    def generate():
        with open("./Resources/Songs/out_loud.wav", "rb") as fwav:
            data = fwav.read(1024)
            while data:
                yield data
                data = fwav.read(1024)
    return Response(generate(), mimetype="audio/x-wav")

@app.route('/')
def index():
    return render_template('index.html')

#streaming support
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload_image/<p_idx>/<lo_idx>', methods=['POST'])
def upload_image(p_idx, lo_idx):
	print('Got an image')
	image_64_encoded = request.form['image']
	image_64_encoded = image_64_encoded.replace(" ","+")
	#print(image_64_encoded)
	#print(len(image_64_encoded))
	#image_64_encoded += "=" * ((4 - (len(image_64_encoded) % 4))) #ugh
	#print(len(image_64_encoded))
	image_64_decode = base64.b64decode(image_64_encoded) 
	image_result = open('people_data/patient_data/' + p_idx + '/' + lo_idx + '/face.jpeg', 'wb') # create a writable image and write the decoding result
	image_result.write(image_64_decode)
	image_result.close()
	return {"status" : "succeeded"}

@app.route('/upload_audio/<p_idx>/<lo_idx>', methods=['POST','GET'])
def upload_audio(p_idx, lo_idx):
	print('Got audio from loved one, not doing anything with it')
    #TODO: this cant be on by default...
	return {"status" : "succeeded"}
	mp3_64_encoded = request.form['loved_one.mp3']
	image_result = open('loved_one.mpeg', 'wb') # create a writable image and write the decoding result
	image_result.write(mp3_64_encoded)
	image_result.close()
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
		return pm.add_loved_one(int(data['p_idx']),data['name'], data['gender'], data['DOB'], responses)
	elif request.method == 'DELETE':
		pm.delete_loved_one(int(data['p_idx']),int(data['lo_idx']))
		return {}

if __name__ == "__main__":
	pm.init()
	fbm.init()
	app.run(debug=True)
