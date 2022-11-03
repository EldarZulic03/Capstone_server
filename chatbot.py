#TODO: get rid of this, its just a plae holder
import random

class chatbot:
	def __init__(self,dic):
		self.dic = dic
		self.responses = ["Hello there friend", "How are you doing", "Mhm", "Okay", "Do you know where you are"]
	
	def get_responses(self):
		return self.responses



def train_model(questions):
	cb = chatbot(questions)
	responses = cb.get_responses()
	return cb, responses

def generate_response(cb, user_input):
	idx = random.randint(0,4)
	return cb.get_responses[idx]
	
