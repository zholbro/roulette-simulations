from collections import Counter
import random
import threading
import string
import sys
import time
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np

jumpCounter = Counter()
jumpData = []

class RouletteNode:
	def __init__(self, isRoot, k):
		self.counter = Counter({'InternalCounter': 0, 'ExternalCounter': 0})
		self.isRoot = isRoot
		self.parents = []
		self.children = []
		self.k = k
		self.id = ''.join(random.choice(string.ascii_uppercase) for _ in range(2))
		# print(self.id)

	# this scheduling scheme tends to result in an overlay radius of n/k
	def rouletteJoin(self, partner, k):
		if self is partner or len(self.parents) >= self.k or partner in self.parents or self in partner.children:
			return
		# partner is complete with children
		if len(partner.children) >= partner.k:
			for i in partner.children:
				self.rouletteJoin(i, 1)
		if k == 1:
			if len(partner.children) >= partner.k:
				self.rouletteJoin(random.choice(partner.children), 1)
			elif not partner.isRoot:
				partner.children.append(self)
				self.parents.append(partner)
		elif not partner.isRoot:
			for i in partner.children:
				self.rouletteJoin(i, 1)
			self.parents.append(partner)
			partner.children.append(self)

		# if self is partner or len(self.parents) >= k:
		# 	return
		# if len(partner.children) >= partner.k:
		# 	# for i in range (0, k-1):
		# 	# 	rouletteJoin(self, partner.children[i], 1)
		# 	for i in partner.children:
		# 		print('giving ' + self.id + ' to ' + i.id)
		# 		self.rouletteJoin(i, 1)
		# if k == 1:
		# 	if len(partner.children) >= partner.k:
		# 		i = random.randint(0, len(partner.children) - 1)
		# 		self.rouletteJoin(partner.children[i], k)
		# 	else:
		# 		self.parents.append(partner)
		# 		partner.children.append(self)
		# else:
		# 	self.parents.append(partner)
		# 	partner.children.append(self)
		# 	# for i in range (0, partner.children.length - 1):
		# 	# 	rouletteJoin(self, partner.children[i], 1)
		# 	for i in partner.children:
		# 		self.rouletteJoin(i, 1)

	def transmit(self):
		threading.Timer(1/30, self.transmit).start()
		self.counter['InternalCounter'] += 1
		self.counter['ExternalCounter'] += 1
		# for i in range(0, self.children.length - 1):
		if len(self.children) > 0:
			for i in self.children:
				failure = random.uniform(1, 100)
				# modelling TCP failure at about 5%
				if failure > 5:
					# self.children[i].counter['ExternalCounter'] = self.counter['InternalCounter']
					i.counter['ExternalCounter'] = self.counter['InternalCounter']
				# else:
					# print('PACKET LOSS FROM ' + self.id + ' TO ' + i.id)

	def retransmit(self):
		threading.Timer(1/30, self.retransmit).start()
		internal = self.counter['InternalCounter']
		ext = self.counter['ExternalCounter']

		if ext > internal and self.children > 0:
			# print('node ' + self.id + ' going from frame ' + str(internal) + ' to ' + str(ext))
			if (ext - internal) > 1:
				# print('Jump by ' + str(ext-internal) + 'frames')
				jumpData.append(ext - internal)
				jumpCounter[str(ext-internal)] += 1
				# print 'JUMP IN FRAMES FROM ' + str(internal) + ' TO ' + str(ext)
			# if (ext - internal) > 10:
				# print('SEVERE PACKET DROPPED FOR NODE ' + self.id)
			#time for rebroadcast
			self.counter['InternalCounter'] = ext
			# for i in range(0, self.children.length - 1):
			# 	failure = random.uniform(0, 100)
			# 	if failure > 5:
			# 		self.children[i].counter['ExternalCounter'] = internal
			for i in self.children:
				failure = random.uniform(1,100)
				#this shit here is where some race conditions are about to happen probably
				if failure > 5 and i.counter['ExternalCounter'] < ext:
					# increase of the counter needs to be monotonic
					i.counter['ExternalCounter'] = ext
		# print(self.id + ' is at ' + str(ext))

	def overlayRadiusMeasure(self, partner, radius):
		if partner.isRoot:
			return radius
		else:
			return self.overlayRadiusMeasure(random.choice(partner.parents), radius + 1)

def waiting():
	threading.Timer(1, waiting).start()
	print('waiting for failure')

def main():
	# bootstrapping is nothing
	root = RouletteNode(True, 2)
	a = RouletteNode(False, 2)
	b = RouletteNode(False, 2)
	root.children.extend([a, b])
	a.parents.append(root)
	b.parents.append(root)
	c = RouletteNode(False, 2)
	c.parents.append(a)
	d = RouletteNode(False, 2)
	d.parents.extend([a,b])
	e = RouletteNode(False, 2)
	e.parents.append(b)
	a.children.extend([c, d])
	b.children.extend([d, e])
	print('Root id is ' + root.id)
	print('c\'s grandparent is ' + c.parents[0].parents[0].id)
	print('d\'s parents are: ')
	for i in d.parents:
		print(i.id)
	x = RouletteNode(False, 2)
	x.rouletteJoin(root, x.k)
	a.retransmit()
	b.retransmit()
	c.retransmit()
	d.retransmit()
	e.retransmit()
	root.transmit()

	for i in range(1, 20):
		newNode = RouletteNode(False, 2)
		newNode.rouletteJoin(root, newNode.k)
		newNode.retransmit()

	print('gimme a bit')
	time.sleep(30)
	print(jumpCounter)
	h = sorted(jumpData)
	fit = stats.norm.pdf(h, np.mean(h), np.std(h))
	# plt.plot(h, fit, '-o')
	# plt.hist(h, normed=True)
	# plt.show()
	# sys.exit()
	plt.hist(jumpData, bins='auto')
	plt.title('Distribution of frame misses in Roulette With Unreliable Network and Reliable Nodes, n = 20, p = 0.05')
	plt.show()

if __name__ == "__main__":
	main()