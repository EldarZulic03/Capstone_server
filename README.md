# Capstone
Capstone Repo

#####SETUP######

You need to download the synthesizer.pt and store it under   voice_cloning/saved_models/default/synthesizer.pt. Can download from here: https://drive.google.com/file/d/1YAoaMeMSb68xp-iOf9CRliAGK2iCncPP/view?usp=sharing


You need to download wav2lip_gan.pth and put it under wav2lip/checkpoints/wav2lip_gan.pth you can download it from here: https://drive.google.com/file/d/1XdUcCD2onItOG5JEJztiyTS_7p8OVkPA/view?usp=sharing

pip install all the libraries in required_modules

to be able to use the deepfake you need to run ""brew install ffmpeg" and pip install -r requirements.txt. You may have to pip or brew install the packages in requirements.txt one by one if you find some trouble


Start server using: python3 app.py

Then go to: 127.0.0.1:5000 (or whichever host you specify using --host to see what the server displays)
you can change the app.run line in app.py to app.run(debug=True,host="0.0.0.0",port=7000) might have to play around with the port value to find something available. That should make it available on all interfaces of your device. Then you can do ifconfig and check en0 or whatever your devices wifi interface is called for the ipv4 address and replace the ip/port in the front end with the ip you see from the command and the port you chose

email hmkhan2000@gmail.com for access to the Firebase project for debugging. Relevant credentials to make use of the storage exist in the project directory already.

If on an M1 mac and pyaudio is causing trouble this might be useful: https://qiita.com/yukilab/items/d50a10f1d46c44ae0757

####Understanding the different modules####

---app.py---

This is the main server code. This is how you want to run the server, "python app.py". Currently at the top of the file theres some experimental streaming stuff, and some stuff related to generating deep fake snippets that needs to be moved out as we integrate the chatbot and call features, you can ignore this for now.

The relevant functions will be anything with the @app.route decorator. These are our endpoints, the code should be simple to understand here because they defer to our other modules.

---people_manager.py---

This module manages the loved ones and patient data and sets up our local file system. 

---voice_cloning_wrapper.py---

Like the name suggests, this is a wrapper on the open source voice cloning code, the main class is called VoiceChanger because I miss named it and need to change it... but besides that it abstracts a lot of the complexity of the code away and allows use to create and set models using voice.wav, and synthesize sentences using models.

---wav2lip_wrapper.py---

This is the wrapper for the lip syncing deepfake code. We use it to pass the resulting synthesized audio and the image to create the deepfake snippet.

---firebase_manager.py---

We use local storage for ML training, and firebase to host our snippets, so this is our interface to firebase. FireStore has the personal information that gets used to populate chatbot responses. Its also how we keep track of patients and loved ones. All this management happens through this API


---chatbot.py---
has the chatbot which provides responses which get populated after the fact with personal information. To add new intents, modify intents.json

#####Understanding the data management, filesystem and firebase storage#####

people_data directory is created by people_manager on init. This is where we store all the data for people. people_data will It contains patient_data dir which has patient data...

The personal information gets stored in FiresStore, this is how we keep track of patients and loved-ones.
The blobs get stored in Firebase Storage

people_data/patient_data directory has one directory for each patient, with the dirname being the patient id. simple enough.

people_data/patient_data/patient_id contains one dir for each loved one, with the name being the loved ones id.

people_data/patient_data/patient_id/loved_one_id this directory should have face.mp4 and voice.wav which is loved on training data. Then it should have snippets dir. snippets/audio stores sentences we synthesize. snippets/video has the deepfake snippets we upload to firebase.

we use firebase to upload these snippets. In the firebase storage we upload deepfake of sentence <sentence_words> for patient p_id and loved one lo_id to p_id/lo_id/<sentence_words>
