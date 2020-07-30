import pyaudio
from cryptography.fernet import Fernet

chunk_size = 1024 
audio_format = pyaudio.paInt16
channels = 1
rate = 44000

key = Fernet.generate_key()
encrypter = Fernet(key)

# initialise microphone recording
p = pyaudio.PyAudio()
playing_stream = p.open(format=audio_format, channels=channels, rate=rate, output=True, frames_per_buffer=chunk_size)
recording_stream = p.open(format=audio_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk_size)

data = recording_stream.read(chunk_size)

while data != "":
    data = recording_stream.read(chunk_size)
    data = encrypter.encrypt(data)
    data = encrypter.decrypt(data)
    playing_stream.write(data)