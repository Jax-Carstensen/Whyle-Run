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

class Event:
	def __init__(self, name, position, radius, trigger_key):
		self.name = name
		self.position = position
		self.radius = radius
		self.trigger_key = trigger_key

class Image:
	def __init__(self, src, draw_width=64, draw_height=64):
		self.src = src
		self.image = pygame.image.load(self.src).convert_alpha()
		self.rescale(Vector2(draw_width, draw_height))
		self.image_rect = self.image.get_rect()

	def rescale(self, new_dimensions):
		if self.image.get_width() != self.image.get_height():
			x = new_dimensions.x
			y = x
			new_dimensions = Vector2(int(new_dimensions.x), int(round(new_dimensions.x / self.image.get_width() * self.image.get_height())))
		self.image = pygame.transform.scale(self.image, (new_dimensions.x, new_dimensions.y)).convert_alpha()
		self.dimensions = Vector2(self.image.get_width(), self.image.get_height())

	def draw(self, screen, position):
		screen.blit(self.image, (position.x, position.y))

class Button:
	def __init__(self, text, onclick=None, gui_type="button"):
		self.text = text
		self.dimensions = Vector2()
		self.position = Vector2()
		self.color = (255, 0, 0)
		self.onclick = onclick
		self.gui_type = gui_type

	def click(self):
		if self.onclick != None:
			self.onclick()

class Input(Button):
	def __init__(self, text, name=""):
		super().__init__(text, False, "input")
		self.name = name

class KeyBind:
	def __init__(self, name, text, key, value, action):
		self.text = text
		self.key = key
		self.value = value
		self.name = name
		self.action = action

	def get_text(self):
		return f"({self.key.upper()}) {self.text}: {self.value}"

	def activate(self):
		self.action()

class Option(Button):
	def __init__(self, name, options, on_change):
		super().__init__(options[0], False, "option")
		self.name = name
		self.options = options
		self.current_option_index = 0
		self.on_change = on_change

	def add_option(self, option):
		self.options.append(option)

	def next_option(self):
		self.current_option_index += 1
		if self.current_option_index >= len(self.options):
			self.current_option_index = 0
		self.text = self.options[self.current_option_index]
		self.on_change()

	def previous_option(self):
		self.current_option_index -= 1
		if self.current_option_index < 0:
			self.current_option_index = len(self.options) - 1
		self.text = self.options[self.current_option_index]
		self.on_change()

class Setting:
	def __init__(self, name, screen_height, screen_width, extra_width):
		self.name = name
		self.inputs = []
		self.buttons = []
		self.switches = []
		self.items = []
		self.options = []
		self.keybinds = []
		self.screen_height = screen_height
		self.screen_width = screen_width
		self.current_y = -0.03
		self.extra_width = extra_width

	def add_button(self, button):
		self.current_y += 0.09
		button.position = Vector2(self.screen_width + self.extra_width * 0.5, self.current_y * self.screen_height)
		button.color = (16, 16, 16)
		button.dimensions = Vector2(self.screen_width * 0.2, self.screen_height * 0.075)
		self.buttons.append(button)

	def add_input(self, inp):
		self.current_y += 0.12
		inp.position = Vector2(self.screen_width + self.extra_width * 0.5, self.current_y * self.screen_height)
		inp.color = (16, 16, 16)
		inp.dimensions = Vector2(self.screen_width * 0.2, self.screen_height * 0.075)
		self.inputs.append(inp)

	def add_keybind(self, keybind):
		self.current_y += 0.06
		keybind.position = Vector2(self.screen_width + self.extra_width * 0.5, self.current_y * self.screen_height)
		self.keybinds.append(keybind)

	def add_option(self, option):
		self.current_y += 0.12
		option.position = Vector2(self.screen_width + self.extra_width * 0.5, self.current_y * self.screen_height)
		option.dimensions = Vector2(self.screen_width * 0.2, self.screen_height * 0.075)
		option.color = (16, 16, 16)
		self.options.append(option)

	def get_keybind(self, name):
		for keybind in self.keybinds:
			if keybind.name == name:
				return keybind

class Layer:
	def __init__(self, name, layer_index):
		self.name = name
		self.layer_index = layer_index
		self.blocks = []
	def add_block(self, block):
		self.blocks.append(block)


class Game:
	def __init__(self):
		self.fps_cap = 60
		self.times = []
		self.tested_resolution = 0
		self.delta_time = 0
		self.images = {}
		self.square_width = 32
		self.square_height = int(round(self.square_width / 1.777))
		self.mouse_down = False
		self.blocks = []
		self.block_types = {}
		self.buttons = []
		self.inputs = []
		self.keybinds = []
		self.settings = []
		self.options = []
		self.events = []
		self.typing = False
		self.typing_index = -1
		self.shifting = False
		self.collidable = True
		self.setting = []
		self.block_name = ""
		self.removing = False
		self.show_grid = True
		self.show_event_radius = True
		self.fill = False
		self.filling = False
		self.fill_start = Vector2()
		self.optioning = False
		self.layers = []
		self.current_layer_index = 0
		self.layer_ind = 0
		self.keys = {"w":False,"a":False,"s":False,"d":False}
		self.offset = Vector2()
		self.font_size = 25

	def draw_text(self, text="", position=Vector2(), color=(0,0,0), center=False, text_shadow=True):
		if center:
			w, h = self.font.size(text)
			position = Vector2(position.x - w * 0.5, position.y - h * 0.5)
		if text_shadow:
			text_surface = self.font.render(text, True, (0,0,0))
			self.screen.blit(text_surface, (position.x + 2, position.y + 2))
		text_surface = self.font.render(text, True, color)
		self.screen.blit(text_surface, (position.x, position.y))

	def load_images(self):
		files = [f for f in listdir("./images/") if isfile(join("./images/", f))]
		for file in files:
			if ".png" in file:
				self.block_types[file.split(".")[0]] = Image(f"./images/{file}", self.square_size, self.square_size)
		self.block_types["principal"].rescale(Vector2(self.square_size * 1.25, 32))

	def add_layer(self, layer_name):
		self.layers.append(Layer(layer_name, self.layer_ind))
		self.layer_ind += 1

	def set_settings(self, setting_name):
		self.typing = False
		self.optioning = False
		for setting in self.settings:
			if setting.name == setting_name:
				self.setting = setting
				self.inputs = setting.inputs
				self.buttons = setting.buttons
				self.keybinds = setting.keybinds
				self.options = setting.options
				return

	def load_events(self):
		self.set_settings("add event")

	def load_scene_management(self):
		self.set_settings("scene manager")

	def back(self):
		self.set_settings("main")

	def get_setting(self):
		return self.setting.name

	# The way this is implemented, you HAVE to add layers in order in the start function
	def change_layer(self):
		self.current_layer_index = self.get_option("layer").current_option_index

	def start(self):
		pygame.init()
		self.clock = pygame.time.Clock()
		self.screen_height = int(pygame.display.Info().current_h * 0.75)
		if pygame.display.Info().current_h == 1440:
			self.font_size = 30
		elif pygame.display.Info().current_h == 1080:
			self.font_size = 25
		self.font = pygame.font.SysFont("Arial", self.font_size)
		self.screen_width = int(pygame.display.Info().current_w * 0.75)
		self.extra_width = int(pygame.display.Info().current_w * 0.2)
		self.square_size = int(round(self.screen_width / self.square_width))
		self.screen = pygame.display.set_mode((self.screen_width + self.extra_width, self.screen_height))
		self.add_layer("base")
		self.add_layer("decorations")
		main_screen = Setting("main", self.screen_height, self.screen_width, self.extra_width)
		main_screen.add_button(Button("Scene Management", self.load_scene_management))
		main_screen.add_button(Button("Add Event", self.load_events))
		main_screen.add_button(Button("Add Prefab", self.add_prefab))
		main_screen.add_input(Input("grass", "block name"))
		names = []
		for layer in self.layers:
			names.append(layer.name)
		main_screen.add_option(Option("layer", names, self.change_layer))
		main_screen.add_keybind(KeyBind("collidable", "Collidable", "C", self.collidable, self.toggle_collision))
		main_screen.add_keybind(KeyBind("removing", "Remove", "R", self.removing, self.toggle_removing))
		main_screen.add_keybind(KeyBind("show grid", "Show Grid", "G", self.show_grid, self.toggle_grid))
		main_screen.add_keybind(KeyBind("fill", "Fill Scene", "F", self.fill, self.toggle_fill))
		self.settings.append(main_screen)
		scene_manager = Setting("scene manager", self.screen_height, self.screen_width, self.extra_width)
		scene_manager.add_button(Button("Back", self.back))
		scene_manager.add_input(Input("level1", "level name"))
		scene_manager.add_button(Button("Load Scene", self.load))
		scene_manager.add_button(Button("Save Scene", self.save))
		self.settings.append(scene_manager)
		add_event = Setting("add event", self.screen_height, self.screen_width, self.extra_width)
		add_event.add_button(Button("Back", self.back))
		add_event.add_input(Input("event name", "event name"))
		add_event.add_input(Input("2", "event radius"))
		add_event.add_input(Input("E", "trigger key"))

		add_event.add_keybind(KeyBind("show radius", "Show Event Radius", "R", self.show_event_radius, self.toggle_event_radius))
		self.settings.append(add_event)
		self.set_settings("main")
		self.load_images()
		exit_loop = False
		while True:
			self.manage_time()
			self.screen.fill((32,32,32))
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					exit_loop = True
					break
				else:
					self.manage_event(event)
			if exit_loop:
				break

			if self.show_grid:
				for x in range(self.square_width):
					for y in range(self.square_height):
						pygame.draw.rect(self.screen, (255, 0, 0), (x*self.square_size,y*self.square_size,self.square_size,self.square_size), 3)
			mouse_position = pygame.mouse.get_pos()
			x = int(mouse_position[0] / self.square_size) * self.square_size
			y = int(mouse_position[1] / self.square_size) * self.square_size
			for layer in self.layers:
				for block in layer.blocks:
					if self.square_width > (block.position.x - self.offset.x):
						self.block_types[block.name].draw(self.screen, Vector2((block.position.x - self.offset.x) * self.square_size, (block.position.y - self.offset.y) * self.square_size))
			for event in self.events:
				self.block_types["event"].draw(self.screen, Vector2(event.position.x * self.square_size, event.position.y * self.square_size))
				if self.show_event_radius:
					size = float(event.radius)
					pygame.draw.circle(self.screen, (0, 0, 255), (event.position.x * self.square_size + self.square_size * 0.5, event.position.y * self.square_size + self.square_size * 0.5), self.square_size * size, width=2)
			if self.get_setting() == "main":
				self.block_name = self.get_input("block name").text
			if mouse_position[0] < self.screen_width:
				if self.get_setting() != "add event":
					if self.block_name in self.block_types:
						if not self.removing:
							self.block_types[self.block_name].draw(self.screen, Vector2(x, y))
							if self.filling:
								start_x = self.fill_start.x
								end_x = int(mouse_position[0] / self.square_size)
								start_y = self.fill_start.y
								end_y = int(mouse_position[1] / self.square_size)
								if start_x > end_x:
									new_var = start_x
									start_x = end_x
									end_x = new_var
								if start_y > end_y:
									new_var = start_y
									start_y = end_y
									end_y = new_var
								for x in range(start_x, end_x + 1):
									for y in range(start_y, end_y + 1):
										self.block_types[self.block_name].draw(self.screen, Vector2(x * self.square_size, y * self.square_size))
						if self.mouse_down:
							x = int(mouse_position[0] / self.square_size) + self.offset.x
							y = int(mouse_position[1] / self.square_size) + self.offset.y
							if not self.fill:
								if self.removing:
									if not self.remove_event(x, y):
										self.remove_block(x, y)
								else:
									self.set_block(x, y)
							else:
								if not self.filling or (self.fill_start.x == x and self.fill_start.y == y):
									self.fill_start = Vector2(x, y)
									self.filling = True
								else:
									self.filling = False
									start_x = self.fill_start.x
									end_x = int(mouse_position[0] / self.square_size)
									start_y = self.fill_start.y
									end_y = int(mouse_position[1] / self.square_size)
									if start_x > end_x:
										new_var = start_x
										start_x = end_x
										end_x = new_var
									if start_y > end_y:
										new_var = start_y
										start_y = end_y
										end_y = new_var
									for x in range(start_x, end_x + 1):
										for y in range(start_y, end_y + 1):
											if self.removing:
												self.remove_block(x, y)
											else:
												self.set_block(x, y)
												#self.block_types[self.block_name].draw(self.screen, Vector2(x * self.square_size, y * self.square_size))
				else:
					self.block_types["event"].draw(self.screen, Vector2(x, y))
					if self.show_event_radius:
						size = float(self.get_input("event radius").text)
						pygame.draw.circle(self.screen, (0, 0, 255), (x + self.square_size * 0.5, y + self.square_size * 0.5), self.square_size * size, width=2)
					found = False
					x = int(mouse_position[0] / self.square_size)
					y = int(mouse_position[1] / self.square_size)
					if self.mouse_down:
						for event in self.events:
							if event.position.x == x and event.position.y == y:
								found = True
								break
						if not found:
							self.events.append(Event(self.get_input("event name").text, Vector2(x,y), self.get_input("event radius").text, self.get_input("trigger key").text))
			for button in self.buttons:
				if self.mouse_down:
					if box_collides(Vector2(mouse_position[0], mouse_position[1]), Vector2(button.position.x - button.dimensions.x * 0.5, button.position.y - button.dimensions.y * 0.5), Vector2(1,1), button.dimensions):
						button.click()
						self.mouse_down = False
				self.draw_button(button)
			collision = False
			for inp in self.inputs:
				if self.mouse_down:
					if box_collides(Vector2(mouse_position[0], mouse_position[1]), Vector2(inp.position.x - inp.dimensions.x * 0.5, inp.position.y - inp.dimensions.y * 0.5), Vector2(1,1), inp.dimensions):
						self.typing = True
						self.optioning = False
						self.typing_index = self.inputs.index(inp)
						collision = True
				self.draw_button(inp)
			for option in self.options:
				if self.mouse_down:
					if box_collides(Vector2(mouse_position[0], mouse_position[1]), Vector2(option.position.x - option.dimensions.x * 0.5, option.position.y - option.dimensions.y * 0.5), Vector2(1,1), option.dimensions):
						self.option_index = self.options.index(option)
						self.optioning = True
						self.typing = False
						collision = True
				self.draw_button(option)
			for keybind in self.keybinds:
				self.draw_text(keybind.get_text(), keybind.position,(255,255,255),True,True)
			if self.mouse_down and not collision:
				self.typing = False
				self.optioning = False
			self.draw_text(f"FPS: {len(self.times)}", Vector2(0, 0), (45, 255, 0))
			pygame.display.flip()
			self.clock.tick(self.fps_cap)

	def find_block(self, position):
		for block in self.layers[self.current_layer_index].blocks:
			if block.position.x == position.x and block.position.y == position.y:
				return block
		return False

	def get_input(self, name):
		for inp in self.inputs:
			if inp.name == name:
				return inp
		return False

	def get_option(self, name):
		for option in self.options:
			if option.name == name:
				return option
		return False

	def add_prefab(self):
		print("Lets you add players, npcs, and other pre-made non-static items.")

	def load(self):
		file_location = f"./levels/{self.get_input('level name').text}.json"
		self.events = []
		with open(file_location, "r") as file:
			dictionary = json.load(file)
			i = 0
			for layer in dictionary["layers"]:
				self.layers[i].blocks = []
				for block in layer:
					self.layers[i].add_block(Block(block["name"],Vector2(block["position"]["x"], block["position"]["y"]),block["collidable"]))
				i += 1
			for event in dictionary["events"]:
				self.events.append(Event(event["name"],Vector2(event["position"]["x"], event["position"]["y"]),event["radius"],event["trigger key"]))

	def save(self):
		file_location = f"./levels/{self.get_input('level name').text}.json"
		json_file = {}
		json_file["blocks"] = []
		json_file["events"] = []
		json_file["player position"] = {
			"x": 0,
			"y": 0
		}
		json_file["layers"] = []
		for layer in self.layers:
			json_file["layers"].append([])
			for block in layer.blocks:
				json_file["layers"][len(json_file["layers"]) - 1].append({
					"name": block.name,
					"position": {
						"x": block.position.x,
						"y": block.position.y
					},
					"collidable": block.collidable
				})
		for event in self.events:
			json_file["events"].append({
				"name": event.name,
				"position": {
					"x": event.position.x,
					"y": event.position.y
				},
				"trigger key": event.trigger_key,
				"radius": event.radius
			})
		with open(file_location, "w") as file:
			json.dump(json_file, file, indent=4) 

	def draw_button(self, button):
		x = button.position.x - button.dimensions.x * 0.5
		y = button.position.y - button.dimensions.y * 0.5
		pygame.draw.rect(self.screen, (0,0,0), (x+4, y+4, button.dimensions.x, button.dimensions.y))
		pygame.draw.rect(self.screen, button.color, (x, y, button.dimensions.x, button.dimensions.y))
		self.draw_text(button.text, Vector2(button.position.x, button.position.y), (255, 255, 255), True, True)
		if button.gui_type != "button":
			self.draw_text(button.name.title() + ":", Vector2(x, button.position.y - self.screen_height * 0.07), (255, 255, 255), False, True)
		if button.gui_type == "option":
			self.draw_text("<", Vector2(button.position.x - self.screen_width * 0.075, button.position.y), (255, 255, 255), True, True)
			self.draw_text(">", Vector2(button.position.x + self.screen_width * 0.075, button.position.y), (255, 255, 255), True, True)

	def set_block(self, x, y, name=""):
		if name == "":
			name = self.block_name
		found = False
		if self.find_block(Vector2(x, y)) != False:
			b = self.find_block(Vector2(x, y))
			b.name = name
			b.collidable = self.collidable
		else:
			self.layers[self.current_layer_index].add_block(Block(name,Vector2(x,y),self.collidable))
		if name == "grass" and y > 0:
			if self.find_block(Vector2(x,y-1)) != False:
				self.find_block(Vector2(x, y)).name = "dirt"
		if self.find_block(Vector2(x, y+1)) != False and self.find_block(Vector2(x, y+1)).name == "grass":
			self.set_block(x, y+1, "dirt")

	def remove_block(self, x, y):
		if self.find_block(Vector2(x, y)) != False:
			self.layers[self.current_layer_index].blocks.remove(self.find_block(Vector2(x, y)))

	def remove_event(self, x, y):
		for event in self.events:
			if event.position.x == x and event.position.y == y:
				self.events.remove(event)
				return True
		return False

	def manage_time(self):
		if len(self.times) > 0:
			self.delta_time = time() - self.times[len(self.times) - 1]
		self.times.append(time())
		while(time() - self.times[0] > 1):
			self.times.pop(0)

	def toggle_collision(self):
		self.collidable = not self.collidable
		self.setting.get_keybind("collidable").value = self.collidable

	def toggle_removing(self):
		self.removing = not self.removing
		self.setting.get_keybind("removing").value = self.removing

	def toggle_grid(self):
		self.show_grid = not self.show_grid
		self.setting.get_keybind("show grid").value = self.show_grid

	def toggle_event_radius(self):
		self.show_event_radius = not self.show_event_radius
		self.setting.get_keybind("show radius").value = self.show_event_radius

	def toggle_fill(self):
		self.fill = not self.fill
		self.setting.get_keybind("fill").value = self.fill
		self.filling = False

	def manage_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN:
			self.mouse_down = True
		elif event.type == pygame.MOUSEBUTTONUP:
			self.mouse_down = False
		elif event.type == pygame.KEYDOWN:
			if self.typing:
				character = pygame.key.name(event.key)
				if character == "backspace":
					self.inputs[self.typing_index].text = self.inputs[self.typing_index].text[:-1]
				if "shift" in character:
					self.shifting = True
				if len(character) == 1 and (character.isalpha() or character == "/" or character == "\\" or character.isdigit() or character == "." or character == " "):
					if self.shifting:
						character = character.upper()
					self.inputs[self.typing_index].text += character
			elif self.optioning:
				character = pygame.key.name(event.key)
				if character == "right":
					self.options[self.option_index].next_option()
				elif character == "left":
					self.options[self.option_index].previous_option()
			else:
				character = pygame.key.name(event.key)
				if character == "w" or character == "a" or character == "s" or character == "d":
					if character == "w":
						self.offset.y -= 1
					elif character == "a":
						self.offset.x -= 1
					elif character == "s":
						self.offset.y += 1
					elif character == "d":
						self.offset.x += 1
				for keybind in self.keybinds:
					if keybind.key.lower() == character.lower():
						keybind.activate()
			if event.key == pygame.K_b:
				self.tool = "brush"
			elif event.key == pygame.K_g:
				self.tool = "bucket"
		elif event.type == pygame.KEYUP:
			character = pygame.key.name(event.key)
			if "shift" in character:
				self.shifting = False

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