import socket
from threading import Timer
from mingus.midi import fluidsynth
from ping3 import ping
from .midi import NoteData, NoteHistory

class Reciever:
	def __init__(self, ip, port, M_SIZE=1024):
		self.M_Size = M_SIZE
		self.ip = ip
		self.port = port

		# init lists, variables
		self.ping_history = []
		self.note_history = NoteHistory()

		# init socket
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.bind((self.ip, self.port))

	def recieve(self):
		print("getting signal")
		message, addr = self.socket.recvfrom(self.M_Size)
		raw = message.decode("utf-8").split(",")

		note = NoteData(raw[0], raw[1], raw[2], raw[3])
		self.note_history.add(note, float(raw[3]))

		note._print()
		return note

def ping_log(ip, note_hist):
	print("calc_bpm")
	cur_bpm = note_hist.get_bpm(20)
	print(f"latency: {ping(ip)}, bpm: {60/cur_bpm if not cur_bpm == 0 else 1}")

class repeater(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

if __name__ == "__main__":
	ip = "127.0.0.1"
	port = 8890
	reciever = Reciever(ip, port)
	fluidsynth.init("C:/soundfont/FluidR3_GM.sf2")

	pinger = repeater(2, ping_log)
	pinger.start()

	try: 
		while True:
			note = reciever.recieve()
			fluidsynth.play_Note(note.pitch, 0, note.velocity)
	except KeyboardInterrupt:
		reciever.socket.close()
		pinger.cancel()
		print("BYE")
		exit()