import socket
import time
import pygame.midi as midi
from midi import NoteData, NoteHistory

class Sender:
	def __init__(self, ip, port, M_SIZE=1024):
		self.ip = ip
		self.port = port
		self.M_Size = M_SIZE

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.history = NoteHistory()

	def send_note(self, note):
		message = f"{note.status},{note.pitch},{note.velocity},{time.perf_counter()}"
		send_mes = self.socket.sendto(message.encode("utf-8"), (self.ip, self.port))

class MidiInput:
	def __init__(self, device_id:int):
		self.device = midi.Input(device_id)

	def get_note(self):
		raw = self.device.read(1)[0][0]
		status = raw[0]
		pitch = raw[1]
		velocity = raw[2]
		timestamp = time.perf_counter()
		return NoteData(status, pitch, velocity, timestamp)

	def poll(self):
		return self.device.poll()

	@staticmethod
	def from_cli():
		for i in range(midi.get_count()):
			device_info = midi.get_device_info(i)

			if not device_info:
				print("NO DEVICE")
				return
			if device_info[2] == 0:
				continue

			print(f'{i}: {device_info[1].decode("utf-8")}\n')
		device_id = int(input("Choose device:"))
		return MidiInput(device_id)

if __name__ == "__main__":
	ip = '127.0.0.1'
	port = 8890
	sender = Sender(ip, port)
	midi.init()
	in_device = MidiInput.from_cli()

	while True:
		if in_device.poll():
			note = in_device.get_note()

			note._print()
			sender.send_note(note)