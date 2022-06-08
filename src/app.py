from threading import Thread
import time
from ping3 import ping
from .midi import NoteHistory
from .sender import MidiInput, Sender
import pygame.midi as midi
from .receiver import Reciever
from mingus.midi import fluidsynth

# TODO: find a way to share note_hist without global variables
note_hist = NoteHistory()
is_on = 1

class App:
	def __init__(self):
		self.ip = str(input("IP Adress:"))
		self.port = int(input("Port: "))
		self.midi_device = MidiInput.from_cli()

		t1 = Thread(target=self.sender)
		t2 = Thread(target=self.reciever)
		t3 = Thread(target=self.pinger)
		t1.start()
		t2.start()
		t3.start()
		t1.join()
		t2.join()
		t3.join()

	def sender(self):
		s = Sender(self.ip, self.port)

		global is_on
		try:
			while is_on == 1:
				if self.midi_device.poll():
					note = self.midi_device.get_note()

					note._print()
					s.send_note(note)
		except KeyboardInterrupt:
			is_on = 0
			s.socket.close()

	def reciever(self):
		r = Reciever(self.ip, self.port)
		fluidsynth.init("./soundfont/FluidR3_GM.sf2")

		global is_on
		while is_on == 1:
			note = r.recieve()
			fluidsynth.play_Note(note.pitch, 0, note.velocity)
			note_hist.add(note, time.perf_counter())
		r.socket.close()

	def pinger(self):
		global is_on
		while is_on == 1:
			print("calc_bpm")
			global note_hist
			cur_bpm = note_hist.get_bpm(20)
			latency = ping(self.ip)
			print(f"latency: {latency}, bpm: {60/cur_bpm if not cur_bpm == 0 else 1}")
			time.sleep(2)