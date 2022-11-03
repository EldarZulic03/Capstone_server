# Capstone
Capstone Repo

You need to download the synthesizer.pt and store it under voice_cloning/saved_models/default/synthesizer.pt. Can download from here: https://drive.google.com/file/d/1YAoaMeMSb68xp-iOf9CRliAGK2iCncPP/view?usp=sharing


Start server using: python -m flask run

Then go to: 127.0.0.1:5000 (or whichever host you specify using --host to see what the server displays)

to be able to use the deepfake you need to run ""brew install ffmpeg" and pip install -r requirements.txt

If on an M1 mac and pyaudio is causing trouble this might be useful: https://qiita.com/yukilab/items/d50a10f1d46c44ae0757

####Understanding the different modules####

---app.py---

This is the main server code. This is how you want to run the server, "python app.py". Currently at the top of the file theres some experimental streaming stuff, and some stuff related to generating deep fake snippets that needs to be moved out as we integrate the chatbot and call features, you can ignore this for now.

The relevant functions will be anything with the @app.route decorator. These are our endpoints, the code should be simple to understand here because they defer to our other modules.

---people_manager.py---

This module manages the loved ones and patient data and sets up our local file system. init() loads the data from disk when the server is run, it supports adding, deleting etc for loved ones and patients. It also sets up the local filesystem to manage these people, for more details look at the next section on data management.

---voice_cloning_wrapper.py---

Like the name suggests, this is a wrapper on the open source voice cloning code, the main class is called VoiceChanger because I miss named it and need to change it... but besides that it abstracts a lot of the complexity of the code away and allows use to create and set models using voice.wav, and synthesize sentences using models.

---wav2lip_wrapper.py---

This is the wrapper for the lip syncing deepfake code. We use it to pass the resulting synthesized audio and the image to create the deepfake snippet.

---firebase_manager.py---

We use local storage for ML training, and firebase to host our snippets, so this is our interface to firebase. Currently used just to upload blobs for the snippets, but we may use it to download training audio since sending from front->backend directly is causing issues, so watch out for that.


---chatbot.py---
place holder module that provides the same interface the final chatbot should. Used to abstract chatbot training and prediction for the main server code.

Understanding the data management, filesystem and firebase storage:

people_data directory is created by people_manager on init. This is where we store all the data for people. people_data will contain pickle files for people_manager to store the patient,loved one info (name, id , current uuid count etc) to disk. It also contains patient_data dir which has patient data...

people_data/patient_data directory has one directory for each patient, with the dirname being the patient id. simple enough.

people_data/patient_data/patient_id contains one dir for each loved one, with the name being the loved ones id.

people_data/patient_data/patient_id/loved_one_id this directory should have face.jpeg and voice.wav which is loved on training data. Then it should have snippets dir. snippets/audio stores sentences we synthesize. snippets/video has the deepfake snippets we upload to firebase.

we use firebase to upload these snippets. In the firebase storage we upload deepfake of sentence <sentence_words> for patient p_id and loved one lo_id to p_id/lo_id/<sentence_words>