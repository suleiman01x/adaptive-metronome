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

	def get_bpm(self, range: int):
		'''Calculates BPM from Beat Induction algorithm
		Ref: Simon Dixon, Emilios Cambouropoulos, 2000, "Beat Tracking with Musical Knowledge"
		Emilios Cambouropoulos, 2000, From MIDI to Traditional Musical Notation'''
		if len(self.notes()) < 2:
			return 0

		notes = self.notes()[-range:]
		all_intervals = Cluster.from_notes(notes)
		clusters = split_cluster(all_intervals)

		max_cluster = clusters[0]
		for c in clusters:
			if c.sum_strength() > max_cluster.sum_strength():
				max_cluster = c

		return max_cluster.avg()

class Interval:
	def __init__(self, note1: Note, note2: Note):
		self.note1 = note1
		self.note2 = note2
		self.time = note2.timestamp - note1.timestamp

	def bpm(self):
		return 60 / self.time

	def strength(self):
		if not self.note1:
			return 0
		return self.note1.strength() + self.note2.strength()

class Cluster:
	def __init__(self, intervals = []):
		self.intervals = intervals

	def avg(self):
		return mean([d.time for d in self.intervals])

	def add(self, interval):
		self.intervals.append(interval)

	def sum_strength(self):
		strength = 0
		for interval in self.intervals:
			strength += interval.strength()
		return strength

	def is_near(self, interval_time, range):
		return abs(self.avg() - interval_time) <= range

	@staticmethod
	def join(clust1, clust2):
		all = clust1.intervals + clust2.intervals
		return Cluster(all)

	@staticmethod
	def from_notes(notes=[]):
		intervals = []
		for a in notes:
			for b in notes:
				if a.timestamp >= b.timestamp:
					continue
				intervals.append(Interval(a, b))
		return Cluster(intervals)

def split_cluster(cluster):
	clusters = [Cluster([Interval(Note(0,0,0,0), Note(0,0,0,0))])]
	for i in cluster.intervals:
		if i.time <= 0.025 or i.time >= 2.5:
			continue

		for c in clusters:
			if c.is_near(i.time, 0.025):
				c.add(i)
				break
		else:
			clusters.append(Cluster([i]))

	return clusters

def clamp(n: int, min_v: int, max_v: int):
	'''Limits n to a range(min, max)'''
	v = max(min(max_v, n), min_v)
	return v
