import argparse
import os
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import torch

from voice_cloning.encoder import inference as encoder
from encoder.params_model import model_embedding_size as speaker_embedding_size
from voice_cloning.synthesizer.inference import Synthesizer
from voice_cloning.utils.argutils import print_args
from voice_cloning.utils.default_models import ensure_default_models
from voice_cloning.vocoder import inference as vocoder



class VoiceChanger:
    
    def __init__(self):
        self.enc_model_fpath = Path("voice_cloning/saved_models/default/encoder.pt")
        self.syn_model_fpath = Path("voice_cloning/saved_models/default/synthesizer.pt")
        self.voc_model_fpath = Path("voice_cloning/saved_models/default/vocoder.pt")
        self.models = {}
        self.embed = None    

        if torch.cuda.is_available():
            device_id = torch.cuda.current_device()
            gpu_properties = torch.cuda.get_device_properties(device_id)
            ## Print some environment information (for debugging purposes)
            print("Found %d GPUs available. Using GPU %d (%s) of compute capability %d.%d with "
                "%.1fGb total memory.\n" %
                (torch.cuda.device_count(),
                device_id,
                gpu_properties.name,
                gpu_properties.major,
                gpu_properties.minor,
                gpu_properties.total_memory / 1e9))
        else:
            print("Using CPU for inference.\n")

        ## Load the models one by one.
        print("Preparing the encoder, the synthesizer and the vocoder...")
        ensure_default_models(Path("voice_cloning/saved_models"))
        encoder.load_model(self.enc_model_fpath)
        self.synthesizer = Synthesizer(self.syn_model_fpath)
        vocoder.load_model(self.voc_model_fpath)


        ## Run a test
        print("Testing your configuration with small inputs.")
        # Forward an audio waveform of zeroes that lasts 1 second. Notice how we can get the encoder's
        # sampling rate, which may differ.
        # If you're unfamiliar with digital audio, know that it is encoded as an array of floats
        # (or sometimes integers, but mostly floats in this projects) ranging from -1 to 1.
        # The sampling rate is the number of values (samples) recorded per second, it is set to
        # 16000 for the encoder. Creating an array of length <sampling_rate> will always correspond
        # to an audio of 1 second.
        print("\tTesting the encoder...")
        encoder.embed_utterance(np.zeros(encoder.sampling_rate))

        # Create a dummy embedding. You would normally use the embedding that encoder.embed_utterance
        # returns, but here we're going to make one ourselves just for the sake of showing that it's
        # possible.
        embed = np.random.rand(speaker_embedding_size)
        # Embeddings are L2-normalized (this isn't important here, but if you want to make your own
        # embeddings it will be).
        embed /= np.linalg.norm(embed)
        # The synthesizer can handle multiple inputs with batching. Let's create another embedding to
        # illustrate that
        embeds = [embed, np.zeros(speaker_embedding_size)]
        texts = ["test 1", "test 2"]
        print("\tTesting the synthesizer... (loading the model will output a lot of text)")
        mels = self.synthesizer.synthesize_spectrograms(texts, embeds)

        # The vocoder synthesizes one waveform at a time, but it's more efficient for long ones. We
        # can concatenate the mel spectrograms to a single one.
        mel = np.concatenate(mels, axis=1)
        # The vocoder can take a callback function to display the generation. More on that later. For
        # now we'll simply hide it like this:
        no_action = lambda *args: None
        print("\tTesting the vocoder...")
        # For the sake of making this test short, we'll pass a short target length. The target length
        # is the length of the wav segments that are processed in parallel. E.g. for audio sampled
        # at 16000 Hertz, a target length of 8000 means that the target audio will be cut in chunks of
        # 0.5 seconds which will all be generated together. The parameters here are absurdly short, and
        # that has a detrimental effect on the quality of the audio. The default parameters are
        # recommended in general.
        vocoder.infer_waveform(mel, target=200, overlap=50, progress_callback=no_action)

        print("All test passed! You can now synthesize speech.\n\n")


    #load a sample from a path and create the embed model for it
    #TODO save models to db with unique id instead of with name in memory
    def load_and_set_new_model(self, file_path, name):
        in_fpath = Path(file_path.replace("\"","").replace("\'","")) 
        preprocessed_wav = encoder.preprocess_wav(in_fpath)
        original_wav, sampling_rate = librosa.load(str(in_fpath))
        print("Loaded File successfuly")
        embed = encoder.embed_utterance(preprocessed_wav)
        print("Created the embeding and saved it under {}".format(name))
        self.models[name] = embed
        self.embed = embed

    #create audio for a given sentence with the current embed    
    def synthesize_sentence(self, text, file_name = "voice_cloning/demo_output.wav"):
        if self.embed is None:
            return

        texts = [text]
        embeds = [self.embed]

        specs = self.synthesizer.synthesize_spectrograms(texts, embeds)
        spec = specs[0]
        print("Created the mel spectrogram")

        generated_wav = vocoder.infer_waveform(spec)
        generated_wav = np.pad(generated_wav, (0, self.synthesizer.sample_rate), mode="constant")
        generated_wav = encoder.preprocess_wav(generated_wav)

        import sounddevice as sd
        try:
            sd.stop()
            sd.play(generated_wav, self.synthesizer.sample_rate)
        except sd.PortAudioError as e:
            print("\nCaught exception: %s" % repr(e))
        except:
            raise
        sf.write(file_name, generated_wav.astype(np.float32), self.synthesizer.sample_rate)
        print("Saved output as {}".format(file_name))


    def set_current_model(self, name):
        if name not in self.models:
            return

        print("Setting current model to {}".format(name))
        self.embed = self.models[name]

"""
if __name__ == '__main__':
    print("Hello World")
    vc = VoiceChanger()
    vc.load_and_set_new_model("../test/trump.wav","trump")
    vc.load_and_set_new_model("../test/sponge.wav","spongebob")
    vc.set_current_model("trump")
    vc.synthesize_sentence("this is a test sentence to see if the wrapper is working", "trump_test.wav")
    vc.set_current_model("spongebob")
    vc.synthesize_sentence("this is a test sentence to see if the wrapper is working","sponge_test.wav")
"""
