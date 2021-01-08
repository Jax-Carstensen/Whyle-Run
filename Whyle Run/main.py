from subprocess import run
from sys import executable
from pkg_resources import working_set
from time import time
import json
from os import listdir
from os.path import isfile, join


print("Loading libraries. . . Please wait")

required = {'pygame'}
installed = {pkg.key for pkg in working_set}
missing = required - installed
if missing:
	run([executable, "-m", "pip", "-q", "install", "pygame"])
else:
	print("Pygame is already installed")

import pygame

class Vector2:
	def __init__(self, x=0, y=0):
		self.x = x
		self.y = y

class Block:
	def __init__(self, name, position, collidable=True):
		self.name = name
		self.position = position
		self.collidable = collidable

class Image:
	def __init__(self, src, draw_width=64, draw_height=64):
		self.src = src
		self.image = pygame.image.load(self.src).convert_alpha()
		self.rescale(Vector2(draw_width, draw_height))
		self.image_rect = self.image.get_rect()
		self.dimensions = Vector2(self.image.get_width(), self.image.get_height())

	def rescale(self, new_dimensions):
		if self.image.get_width() != self.image.get_height():
			x = new_dimensions.x
			y = x
			new_dimensions = Vector2(int(new_dimensions.x), int(round(new_dimensions.x / self.image.get_width() * self.image.get_height())))
		self.image = pygame.transform.scale(self.image, (new_dimensions.x, new_dimensions.y)).convert_alpha()
		self.dimensions = Vector2(self.image.get_width(), self.image.get_height())

	def draw(self, screen, position, flip=False):
		if flip:
			screen.blit(pygame.transform.flip(self.image, True, False), (position.x, position.y))
		else:
			screen.blit(self.image, (position.x, position.y))

class Layer:
	def __init__(self, name, layer_index):
		self.name = name
		self.layer_index = layer_index
		self.blocks = []
	def add_block(self, block):
		self.blocks.append(block)

class Component:
	def __init__(self, name):
		self.name = name

class Rigidbody(Component):
	def __init__(self, mass=360, velocity=Vector2()):
		super().__init__("rigidbody")
		self.mass = mass
		self.velocity = velocity
		self.grounded = False

class Animation:
	def __init__(self, name="", frames=[]):
		self.name = name
		self.frames = frames

class Animator(Component):
	def __init__(self, animations=[], frame_time=0.25):
		super().__init__("animator")
		self.animations = animations
		self.frame_time = frame_time
		self.last_frame = time()
		self.frame_index = 0
		self.animation = self.animations[1]

	def next_frame(self):
		self.frame_index += 1
		if self.frame_index >= len(self.animation.frames):
			self.frame_index = 0

	def set_animation(self, name):
		for animation in self.animations:
			if animation.name == name:
				if name != self.animation.name:
					self.last_frame = time()
					self.animation = animation
					self.frame_index = 0

	def update(self):
		if time() - self.last_frame >= self.frame_time:
			self.next_frame()
			self.last_frame = time()

	def get_frame(self):
		return self.animation.frames[self.frame_index]

class GameObject:
	def __init__(self, name, position, image_name):
		self.name = name
		self.position = position
		self.image_name = image_name
		self.dimensions = Vector2(20, 32)
		self.components = []
		self.flip = False

	def add_component(self, component):
		self.components.append(component)

	def get_component(self, component_name):
		for component in self.components:
			if component.name == component_name:
				return component
		return False

class Game:
	def __init__(self):
		self.fps_cap = 165
		self.times = []
		self.player = GameObject("Player", Vector2(), "whyle")
		walk = Animation("whyle walk", ["whyle","whyle1","whyle","whyle2"])
		idle = Animation("whyle idle", ["whyle"])
		jump = Animation("whyle jump", ["whyle_jump"])
		self.player.add_component(Rigidbody())
		self.player.add_component(Animator([idle, walk, jump]))
		self.tested_resolution = 0
		self.delta_time = 0
		self.block_types = {}
		self.blocks = []
		self.square_width = 32
		self.square_height = int(round(self.square_width / 1.777))
		self.level_background_color = (135, 206, 235)
		self.keys = {}
		self.game_objects = []
		self.resize_names = ["whyle", "whyle1", "whyle2", "whyle_jump"]
		self.loading = False
		self.unloading = False
		self.load_time = 1
		self.to_load = ""
		self.loaded = False
		self.layers = []

	def to_tuple(self, vector):
		return (vector.x, vector.y)

	def add_game_object(self, game_object):
		self.game_objects.append(game_object)

	def add_vector(self, vector, vector1):
		return Vector(vector.x + vector1.x, vector.y + vector1.y)

	def draw_text(self, text="", position=Vector2(), color=(0,0,0), center=False, text_shadow=True):
		text_surface = self.font.render(text, True, color)
		self.screen.blit(text_surface, self.to_tuple(position))

	def load_images(self):
		files = [f for f in listdir("./images/") if isfile(join("./images/", f))]
		for file in files:
			if ".png" in file:
				self.block_types[file.split(".")[0]] = Image(f"./images/{file}", self.square_size, self.square_size)

		for name in self.resize_names:
			self.block_types[name].rescale(Vector2(self.square_size * 1.25, 32))
			#self.block_types[name].rescale(Vector2(self.square_size * 2.85, 32))

	def start(self):
		pygame.init()
		self.add_game_object(self.player)
		self.font = pygame.font.SysFont("Arial", 30)
		self.clock = pygame.time.Clock()
		self.screen_height = int(pygame.display.Info().current_h * 0.75)
		self.screen_width = int(pygame.display.Info().current_w * 0.75)
		self.flags = pygame.DOUBLEBUF | pygame.RESIZABLE
		self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), self.flags)
		self.square_size = int(round(self.screen_width / self.square_width))
		self.player.get_component("rigidbody").mass = self.screen_height
		self.load_images()
		self.load("level1", False)
		self.player.dimensions = Vector2(int(self.square_size * 0.666), self.square_size)
		exit_loop = False
		self.player.dimensions = self.block_types["whyle"].dimensions
		while True:
			self.manage_time()
			if not self.loaded:
				self.screen.fill(self.level_background_color)
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					exit_loop = True
					break
				else:
					self.manage_event(event)
			if exit_loop:
				break

			for layer in self.layers:
				for block in layer.blocks:
					self.block_types[block.name].draw(self.screen, Vector2(block.position.x * self.square_size, block.position.y * self.square_size))

			if self.loaded:
				self.loaded = False
			if self.loading:
				if time() - self.start_load_time > self.load_time:
					self.loading = False
				for game_object in self.game_objects:
					self.update_components(game_object)
					self.block_types[game_object.image_name].draw(self.screen, game_object.position, game_object.flip)

				s = pygame.Surface((self.screen_width,self.screen_height))
				s.set_alpha(256 - ((time() - self.start_load_time) / self.load_time) * 256)
				s.fill((0,0,0))
				self.screen.blit(s, (0,0))

				pygame.display.flip()
				continue
			elif self.unloading:
				if time() - self.start_load_time > self.load_time:
					self.unloading = False
					self.loaded = True
					self.load(self.to_load, False)
				s = pygame.Surface((self.screen_width,self.screen_height))
				s.set_alpha(((time() - self.start_load_time) / self.load_time) * 256)
				s.fill((0,0,0))
				self.screen.blit(s, (0,0))
				pygame.display.flip()
				continue

			rigidbody = self.player.get_component("rigidbody")
			animator = self.player.get_component("animator")
			x_movement = 0
			if self.key_down("a"):
				self.player.flip = True
				x_movement -= 1
			if self.key_down("d"):
				self.player.flip = False
				x_movement += 1
			if x_movement != 0 and rigidbody.grounded:
				animator.set_animation("whyle walk")
			elif not rigidbody.grounded:
				animator.set_animation("whyle jump")
			else:
				animator.set_animation("whyle idle")
			add_x = x_movement * rigidbody.mass * 0.1 * self.delta_time
			rigidbody.velocity.x = add_x
			if self.key_down("w") and rigidbody.grounded:
				rigidbody.velocity.y = -self.square_size * 10
			for game_object in self.game_objects:
				self.update_components(game_object)
				self.block_types[game_object.image_name].draw(self.screen, game_object.position, game_object.flip)

			self.draw_text(f"FPS: {len(self.times)}", Vector2(0, 0), (45, 255, 0))
			pygame.display.flip()
			#self.clock.tick(self.fps_cap)

	def update_components(self, game_object):
		if game_object.get_component("rigidbody"):
			rb = game_object.get_component("rigidbody")
			rb.velocity.y += rb.mass * self.delta_time
			rb.grounded = False
			game_object.position.y += rb.velocity.y * self.delta_time
			for layer in self.layers:
				for block in layer.blocks:
					if block.collidable:
						if box_collides(Vector2(block.position.x * self.square_size, block.position.y * self.square_size), self.player.position, Vector2(self.square_size, self.square_size), game_object.dimensions):
							game_object.position.y = block.position.y * self.square_size - game_object.dimensions.y
							rb.velocity.y = 0
							rb.grounded = True
						if box_collides(Vector2(block.position.x * self.square_size, block.position.y * self.square_size + 0.1), Vector2(self.player.position.x + rb.velocity.x, self.player.position.y), Vector2(self.square_size, self.square_size), self.player.dimensions):
							if not box_collides(Vector2(block.position.x * self.square_size, block.position.y * self.square_size), self.player.position, Vector2(self.square_size, self.square_size), self.player.dimensions):
								if rb.velocity.x > 0:
									game_object.position.x = block.position.x * self.square_size - self.player.dimensions.x - 0.01
								else:
									game_object.position.x = block.position.x * self.square_size + self.square_size
								rb.velocity.x = 0
			game_object.position.x += rb.velocity.x
		if game_object.get_component("animator"):
			anim = game_object.get_component("animator")
			anim.update()
			game_object.image_name = anim.get_frame()



	def key_down(self, key):
		if key in self.keys:
			if self.keys[key]:
				return True
		return False

	def load(self, level_name, fade=True):
		if fade:
			self.loading = False
			self.unloading = True
			self.to_load = level_name
			self.start_load_time = time()
			return
		self.delta_time = 0
		self.player.position.y = 0
		self.player.position.x = 0
		self.loading = True
		self.start_load_time = time()
		file_location = f"./levels/{level_name}.json"
		with open(file_location, "r") as file:
			dictionary = json.load(file)
			i = 0
			for layer in dictionary["layers"]:
				if len(self.layers) <= i:
					self.layers.append(Layer("",1))
				self.layers[i].blocks = []
				for block in layer:
					self.layers[i].add_block(Block(block["name"],Vector2(block["position"]["x"], block["position"]["y"]),block["collidable"]))
				i += 1
			for event in dictionary["events"]:
				self.events.append(Event(event["name"],Vector2(event["position"]["x"], event["position"]["y"]),event["radius"],event["trigger key"]))

		# file_location = f"./levels/{level_name}.json"
		# with open(file_location, "r") as file:
		# 	dictionary = json.load(file)
		# 	self.blocks = []
		# 	for block in dictionary["blocks"]:
		# 		self.blocks.append(Block(block["name"],Vector2(block["position"]["x"], block["position"]["y"]),block["collidable"]))

	def manage_time(self):
		if not self.loading:
			if len(self.times) > 0:
				self.delta_time = time() - self.times[len(self.times) - 1]
		self.times.append(time())
		while(time() - self.times[0] > 1):
			self.times.pop(0)

	def manage_event(self, event):
		if event.type == pygame.VIDEORESIZE:
			w = self.screen.get_width()
			h = self.screen.get_height()
			print("Resizing")
		elif event.type == pygame.KEYDOWN:
			character = pygame.key.name(event.key)
			if character.isalpha():
				self.keys[character] = True
		elif event.type == pygame.KEYUP:
			character = pygame.key.name(event.key)
			if character.isalpha():
				self.keys[character] = False

	def scale(self, value):
		return value

def collides(x, y, r, b, x2, y2, r2, b2):
	return not (r <= x2 or x > r2 or b <= y2 or y > b2);

# Returns True if 2 boxes collide
def box_collides(pos, pos2, size1, size2):
	return collides(pos.x, pos.y,
		pos.x + size1.x, pos.y + size1.y,
		pos2.x, pos2.y,
		pos2.x + size2.x, pos2.y + size2.y);

game = Game()
game.start()