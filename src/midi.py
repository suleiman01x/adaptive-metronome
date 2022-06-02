import time
from statistics import mean
import itertools

# Global Variables
NOTE_OFF = 0
NOTE_ON = 1
CONTROL = 2

class NoteData:
	def __init__(self, status=127, pitch=1, velocity=127, timestamp=.0):
		self.status = int(status)
		self.pitch = int(pitch)
		self.velocity = int(velocity)
		self.timestamp = float(timestamp)

	def message(self):
		'''0: note off
		1: note on
		2: control'''
		if self.velocity == 0:
			return NOTE_OFF
		if 128 <= self.status < 144:
			return NOTE_OFF
		if self.status > 159:
			return CONTROL
		return NOTE_ON

	def _print(self):
		print(f"Status: {self.status}, Pitch: {self.pitch}, Velocity: {self.velocity}")

	def encode(self):
		data = [self.status, self.pitch, self.velocity]
		return bytes(data)

	@staticmethod
	def decode(data: bytes):
		arr = bytearray(data)
		return NoteData(arr[0], arr[1], arr[2])

class Note(NoteData):
	def __init__(self, pitch: int, velocity: int, timestamp: float, duration: float):
		NoteData.__init__(self, 144, pitch, velocity, timestamp)
		self.duration = duration

	def strength(self):
		v = clamp(self.velocity, 30, 90)
		p = clamp(self.pitch, 30, 90)
		d = self.duration * 1000
		return (v/p)*d

class NoteHistory:
	def __init__(self):
		'''NoteHistory.history: history of all signals (control, noteon, noteoff)
		NoteHistory.notes: history of only musical notes with duration information'''
		self.history = []

	def add(self, note: NoteData, time: float):
		note.timestamp = time
		self.history.append(note)

	def message_hist(self, message_type: int):
		'''Returns list of all MIDI messages with message type: message_type
		0: note off
		1: note on
		2: control'''
		events  = []
		for note in self.history:
			if note.message() == message_type:
				events.append(note)
		return events

	def notes(self):
		'''Returns list of Note() objects representing all completed notes (notes with note off signals).'''
		on_list = self.message_hist(NOTE_ON)
		off_list = self.message_hist(NOTE_OFF)
		note_hist = []
		# for each note on message, find the next note off message of same pitch value
		for noteon in on_list:
			for noteoff in off_list:
				# skip if note on is after note off
				if noteon.timestamp > noteoff.timestamp:
					continue

				# same pitch
				if noteon.pitch == noteoff.pitch:
					dur = noteoff.timestamp - noteon.timestamp

					note = Note(noteon.pitch, noteon.velocity, noteon.timestamp, dur)
					note_hist.append(note)
					break
		return note_hist

	def get_bpm(self, range: int, delta=.025):
		'''Calculates BPM from Beat Induction algorithm
		Ref: Simon Dixon, Emilios Cambouropoulos, 2000, "Beat Tracking with Musical Knowledge"
		Emilios Cambouropoulos, 2000, From MIDI to Traditional Musical Notation'''
		if len(self.notes()) < 2:
			return 0

		hist = self.notes()[-range:]
		clusters = []

		# IOI clustering
		intervals = itertools.permutations(hist)

		for group in intervals:
			a = group[0]
			b = group[1]

			if a.timestamp > b.timestamp:
				continue

			interval = b.timestamp - a.timestamp
			if not 0.025 < interval < 2.5:
				#print(f"too short{interval}")
				continue

			#print(interval)

			if len(clusters) == 0:
				clusters.append([Interval(a, b)])
				continue

			nearest_clust =  []
			index = 0
			for clust in clusters:
				if len(nearest_clust) == 0:
					nearest_clust = clust
					index = clusters.index(clust)
					continue

				diff = abs(Interval.avg_intervals(clust) - interval)
				if diff < Interval.avg_intervals(nearest_clust):
					nearest_clust = clust
					index = clusters.index(clust)

			if len(nearest_clust) == 0:
				continue

			#print(f"nearest: {Interval.avg_intervals(nearest_clust)}")
			if abs(Interval.avg_intervals(nearest_clust) - interval) < delta:
				clusters[index].append(Interval(a, b))
			else:
				clusters.append([Interval(a, b)])

		largest_strength = clusters[0]
		for clust in clusters:
			if Interval.sum_strength(clust) > Interval.sum_strength(largest_strength):
				largest_strength = clust

		return Interval.avg_intervals(largest_strength)

class Interval:
	def __init__(self, note1: Note, note2: Note):
		self.note1 = note1
		self.note2 = note2
		self.time = note2.timestamp - note1.timestamp

	def bpm(self):
		return 60 / self.time

	def strength(self):
		return self.note1.strength() + self.note2.strength()

	@staticmethod
	def avg_intervals(list):
		return mean([d.time for d in list])

	def avgint_diff(list1, list2):
		return abs(Interval.avg_intervals(list1) - Interval.avg_intervals(list2))

	def sum_strength(list):
		strength = 0
		for note in list:
			strength += note.strength()
		return strength

def clamp(n: int, min_v: int, max_v: int):
	'''Limits n to a range(min, max)'''
	v = max(min(max_v, n), min_v)
	return v

if __name__ == "__main__":
	testnotes = [
		NoteData(pitch=3),
		NoteData(status=128, pitch=3),
		NoteData(pitch=2),
		NoteData(status=128, pitch=2),
		NoteData(pitch=5),
		NoteData(status=128, pitch=5),
		NoteData(pitch=3),
		NoteData(status=128, pitch=3),
	]

	hist =  NoteHistory()

	for note in testnotes:
		hist.add(note, time.perf_counter())
		time.sleep(.1)

	for note in hist.notes():
		print(f'Pitch: {note.pitch}, Duration: {note.duration}, Strength: {note.strength()}')
	print(60 / hist.get_bpm(20))