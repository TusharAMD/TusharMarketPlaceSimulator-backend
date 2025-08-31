import speech_recognition as sr
import time

recognizer = sr.Recognizer()


start  = time.time()
with sr.AudioFile("uploads/recording.wav") as source:
    audio_data = recognizer.record(source)
    text = recognizer.recognize_google(audio_data)
    print(text) 
print(time.time()-start)

print("=====")

import whisper
model = whisper.load_model("tiny")

start  = time.time()
result = model.transcribe("uploads/recording.wav")
print(time.time()-start)

print(result["text"])