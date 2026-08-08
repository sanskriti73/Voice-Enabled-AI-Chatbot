import pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 170)  # Speed of speech
def speak(text):
    engine.say(text)
    engine.runAndWait()