import pygame
import time
import math
from utils import scale_image, blit_rotate_center, blit_text_center, contains
pygame.font.init()
from wavefront import wave_front, normalize_wavefront
from matplotlib import pyplot as plt
import numpy as np
from collections import deque

GRASS = scale_image(pygame.image.load("imgs/grass.jpg"), 2.5)
TRACK = scale_image(pygame.image.load("imgs/track.png"), 0.9)

TRACK_BORDER = scale_image(pygame.image.load("imgs/track-border.png"), 0.9)
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)

WAVEFRONT_TRACK_BORDER = scale_image(pygame.image.load("imgs/wavefront-track.png"), 0.9)
WAVEFRONT_TRACK_BORDER_MASK = pygame.mask.from_surface(WAVEFRONT_TRACK_BORDER)

FINISH = pygame.image.load("imgs/finish.png")
FINISH_MASK = pygame.mask.from_surface(FINISH)

FINISH_POSITION = (130, 250)

RED_CAR = scale_image(pygame.image.load("imgs/red-car.png"), 0.35)
GREEN_CAR = scale_image(pygame.image.load("imgs/green-car.png"), 0.40)

CAR_WIDTH, CAR_HEIGHT = RED_CAR.get_width(), RED_CAR.get_height()

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racing Game!")

MAIN_FONT = pygame.font.SysFont("comicsans", 44)

WAVEFRONT_INITIAL_POSITION = (200, 250)

MAX_HISTORY_POSITIONS = 100

beam_surface = pygame.Surface(WIN.get_rect().center, pygame.SRCALPHA)

mask = pygame.mask.from_surface(WAVEFRONT_TRACK_BORDER)
mask_fx = pygame.mask.from_surface(pygame.transform.flip(WAVEFRONT_TRACK_BORDER, True, False))
mask_fy = pygame.mask.from_surface(pygame.transform.flip(WAVEFRONT_TRACK_BORDER, False, True))
mask_fx_fy = pygame.mask.from_surface(pygame.transform.flip(WAVEFRONT_TRACK_BORDER, True, True))
flipped_masks = [[mask, mask_fy], [mask_fx, mask_fx_fy]]

FPS = 60
PATH = [(175, 119), (110, 70), (56, 133), (70, 481), (318, 731), (404, 680), (418, 521), (507, 475), (600, 551), (613, 715), (736, 713),
		(734, 399), (611, 357), (409, 343), (433, 257), (697, 258), (738, 123), (581, 71), (303, 78), (275, 377), (176, 388), (178, 260)]


class AbstractCar:
	def __init__(self, max_vel, rotation_vel):
		self.img = self.IMG
		self.max_vel = max_vel
		self.vel = 0
		self.rotation_vel = rotation_vel
		self.angle = 0
		self.x, self.y = self.START_POS
		self.acceleration = 0.1

	def rotate(self, left=False, right=False):
		if left:
			self.angle += self.rotation_vel
		elif right:
			self.angle -= self.rotation_vel

	def draw(self, win):
		blit_rotate_center(win, self.img, (self.x, self.y), self.angle)

	def move_forward(self):
		self.vel = min(self.vel + self.acceleration, self.max_vel)
		self.move()

	def move_backward(self):
		self.vel = max(self.vel - self.acceleration, -self.max_vel/2)
		self.move()

	def move(self):
		radians = math.radians(self.angle)
		vertical = math.cos(radians) * self.vel
		horizontal = math.sin(radians) * self.vel 

		self.y -= vertical
		self.x -= horizontal

	def collide(self, mask, x=0, y=0):
		car_mask = pygame.mask.from_surface(self.img)
		offset = (int(self.x - x), int(self.y - y))
		poi = mask.overlap(car_mask, offset)
		return poi

	def reset(self):
		self.x, self.y = self.START_POS
		self.angle = 0
		self.vel = 0

class SensorBullet:
	def __init__(self, car, base_angle, vel, color):
		self.x = car.x + CAR_WIDTH/2
		self.y = car.y + CAR_HEIGHT/2
		self.angle = car.angle
		self.base_angle = base_angle
		self.vel = vel
		self.color = color
		self.img = pygame.Surface((4, 4))
		self.fired = False
		self.hit = False
		self.last_poi = None

	def draw(self, win):
		pygame.draw.circle(win, self.color, (self.x, self.y), 2)

	def fire(self, car):
		self.angle = car.angle + self.base_angle
		self.x = car.x + CAR_WIDTH/2
		self.y = car.y + CAR_HEIGHT/2
		self.fired = True
		self.hit = False

	def move(self):
		if(self.fired):
			radians = math.radians(self.angle)
			vertical = math.cos(radians) * self.vel
			horizontal = math.sin(radians) * self.vel

			self.y -= vertical
			self.x -= horizontal

	def collide(self, x=0, y=0):
		bullet_mask = pygame.mask.from_surface(self.img)
		offset = (int(self.x - x), int(self.y - y))
		poi = TRACK_BORDER_MASK.overlap(bullet_mask, offset)
		if poi:
			self.fired = False
			self.hit = True
			self.last_poi = poi
		return poi

	def draw_line(self, win, car):
		if self.hit:
			pygame.draw.line(win, self.color, (car.x + CAR_WIDTH/2, car.y + CAR_HEIGHT/2), (self.x, self.y), 1)
			pygame.display.update()

	def get_distance_from_poi(self, car):
		if self.last_poi is None:
			return -1
		return math.sqrt((car.x + CAR_WIDTH/2 - self.last_poi[0])**2 + (car.y + CAR_HEIGHT/2 - self.last_poi[1])**2)
		
class PlayerCar(AbstractCar):
	IMG = RED_CAR
	START_POS = (180, 200)

	def __init__(self, max_vel, rotation_vel):
		super().__init__(max_vel, rotation_vel)
		self.sensors = [SensorBullet(self, 25, 12, (100, 0, 255)), SensorBullet(self, 10, 12, (200, 0, 255)), SensorBullet(self, 0, 12, (0, 255, 0)), SensorBullet(self, -10, 12, (0, 0, 255)), SensorBullet(self, -25, 12, (0, 0, 255))]
		self.last_wavefront_value = 0
		self.current_wavefront_value = 0
		self.last_vel_value = 0
		self.distance_array = [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]

	def reduce_speed(self):
		self.vel = max(self.vel - self.acceleration / 2, 0)
		self.move()

	def bounce(self):
		self.vel = -self.vel
		self.move()

	def fireSensors(self): 
		for bullet in self.sensors:
			bullet.fire(self)
	
	def sensorControl(self):

		for bullet in self.sensors:
			if not bullet.fired:
				bullet.fire(self)

		for bullet in self.sensors:
			bullet.move()
	
	def get_distance_array(self):
		return self.distance_array

	def move_forward(self):
		self.last_vel_value = self.vel
		self.vel = min(self.vel + self.acceleration, self.max_vel)
		self.move()
	
	def draw_beam(self, surface, base_angle, angle, pos):
		c = math.cos(math.radians(angle - base_angle))
		s = math.sin(math.radians(angle - base_angle))

		flip_x = c < 0
		flip_y = s < 0
		filpped_mask = flipped_masks[flip_x][flip_y]
		
		# compute beam final point
		x_dest = surface.get_width() * abs(c)
		y_dest = surface.get_height() * abs(s)

		beam_surface.fill((0, 0, 0, 0))

		# draw a single beam to the beam surface based on computed final point
		pygame.draw.line(beam_surface, (0, 0, 255), (0, 0), (x_dest, y_dest))
		beam_mask = pygame.mask.from_surface(beam_surface)

		# find overlap between "global mask" and current beam mask
		offset_x = surface.get_width()-1 - pos[0] if flip_x else pos[0]
		offset_y = surface.get_height()-1 - pos[1] if flip_y else pos[1]
		hit = filpped_mask.overlap(beam_mask, (offset_x, offset_y))
		if hit is not None and (hit[0] != pos[0] or hit[1] != pos[1]):
			hx = surface.get_width()-1 - hit[0] if flip_x else hit[0]
			hy = surface.get_height()-1 - hit[1] if flip_y else hit[1]
			hit_pos = (hx, hy)

			pygame.draw.line(surface, (0, 0, 255), pos, hit_pos)
			pygame.draw.circle(surface, (0, 255, 0), hit_pos, 3)

			# return the distance between the car and the hit point
			return math.sqrt((pos[0] + CAR_WIDTH/2 - hit_pos[0])**2 + (pos[1] + CAR_HEIGHT/2 - hit_pos[1])**2)
		return -1


class ComputerCar(AbstractCar):
	IMG = GREEN_CAR
	START_POS = (150, 200)

	def __init__(self, max_vel, rotation_vel, path=[]):
		super().__init__(max_vel, rotation_vel)
		self.path = path
		self.current_point = 0
		self.vel = max_vel

	def draw_points(self, win):
		for point in self.path:
			pygame.draw.circle(win, (255, 0, 0), point, 5)

	def draw(self, win):
		super().draw(win)
		# self.draw_points(win)

	def calculate_angle(self):
		target_x, target_y = self.path[self.current_point]
		x_diff = target_x - self.x
		y_diff = target_y - self.y

		if y_diff == 0:
			desired_radian_angle = math.pi / 2
		else:
			desired_radian_angle = math.atan(x_diff / y_diff)

		if target_y > self.y:
			desired_radian_angle += math.pi

		difference_in_angle = self.angle - math.degrees(desired_radian_angle)
		if difference_in_angle >= 180:
			difference_in_angle -= 360

		if difference_in_angle > 0:
			self.angle -= min(self.rotation_vel, abs(difference_in_angle))
		else:
			self.angle += min(self.rotation_vel, abs(difference_in_angle))

	def update_path_point(self):
		target = self.path[self.current_point]
		rect = pygame.Rect(
			self.x, self.y, self.img.get_width(), self.img.get_height())
		if rect.collidepoint(*target):
			self.current_point += 1

	def move(self):
		if self.current_point >= len(self.path):
			return

		self.calculate_angle()
		self.update_path_point()
		super().move()

	def next_level(self, level):
		self.reset()
		self.vel = self.max_vel + (level - 1) * 0.2
		self.current_point = 0

class GameInfo:
	LEVELS = 10

	def __init__(self, level=1):
		self.level = level
		self.started = False
		self.level_start_time = 0
		
		self.images = [(GRASS, (0, 0)), (TRACK, (0, 0)),
				(FINISH, FINISH_POSITION), (TRACK_BORDER, (0, 0))]
		self.player_car = PlayerCar(2.5, 4)

		self.wavefront_result_matrix = wave_front((WIDTH, HEIGHT), WAVEFRONT_INITIAL_POSITION, WAVEFRONT_TRACK_BORDER_MASK)
		self.normalized_result_matrix = normalize_wavefront(self.wavefront_result_matrix)
		self.wavefront_image = self.create_wavefront_image()

		self.reward = 0
		self.done = False
		self.score = 0

		self.old_distance = 0
		self.new_distance = 0

		self.clock = pygame.time.Clock()
		self.reset()

		self.iterations = 0
		self.MAX_ITERATIONS = 60*30

		self.best_position = (0,0)

		self.historic_positions = deque(maxlen=MAX_HISTORY_POSITIONS)

	def create_wavefront_image(self):
		img = pygame.Surface((WIDTH, HEIGHT)).convert_alpha()
		
		for x in range(WIDTH):
			for y in range(HEIGHT):
				if(self.normalized_result_matrix[x][y].value == 0):
					img.set_at((x, y), (0, 0, 0, 0))
				else:
					img.set_at((x, y), (0, 0, self.normalized_result_matrix[x][y].value, 150))
		return img

	def render_wavefront(self, win):
		for i in range(len(self.normalized_result_matrix)):
			for j in range(len(self.normalized_result_matrix[i])):
					pygame.draw.rect(win, (self.normalized_result_matrix[j][i].value, 0, 0), (j, i, 1, 1))

	def add_to_historic_positions(self, position):
		self.historic_positions.append(position)

	def draw_historic_positions(self, win):
		i = 0
		length = len(self.historic_positions)
		for i in range(length):
			pygame.draw.circle(win, (255 - (length - i)*10, 255 - (length - i)*10, 0), self.historic_positions[i], 5)
			i += 1
	
	def new_best_position(self, position):
		self.best_position = (position[0] + CAR_WIDTH/2, position[1] + CAR_HEIGHT/2)

	def next_level(self):
		self.level += 1
		self.started = False

	def reset(self):
		self.level = 1
		self.started = False
		self.level_start_time = 0
		self.iterations = 0

		self.player_car.reset()
		self.start_level()

	def start_level(self):
		self.started = True
		self.level_start_time = time.time()

	def get_level_time(self):
		if not self.started:
			return 0
		return round(time.time() - self.level_start_time)
	
	def get_state(self):
		# esse é o vetor de entrada, composto por três sinais dos sensores mais a orientação positiva e negativa
		return [*self.player_car.get_distance_array(), self.player_car.vel] 

	def loop_check(self):
		if(self.player_car.vel <= 0.5):
			self.iterations += 1
			if(self.iterations > 60*10):
				print(self.iterations)
		else:
			self.iterations = 0
		if(self.iterations >= self.MAX_ITERATIONS):
			self.reward = -100
			self.done = True

	def play_step(self, action):
		self.done = False
		self.draw(WIN, self.images, self.player_car)
		self.clock.tick(60)

		self.move_player(self.player_car, action)

		self.old_distance = self.new_distance
		self.new_distance = self.wavefront_result_matrix[int(self.player_car.x + CAR_WIDTH/2)][int(self.player_car.y + CAR_HEIGHT/2)].value

		self.handle_collision(self.player_car)

		self.loop_check()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.done = True
				break

		return self.reward, self.done, self.score

	def draw(self, win, images, player_car):

		images.append((self.wavefront_image, (0, 0)))

		for img, pos in images:
			win.blit(img, pos)

		self.draw_historic_positions(WIN)

		i = 0
		for angle in range(0, 359, 30):
			distance = self.player_car.draw_beam(WIN, self.player_car.angle, angle, (self.player_car.x + CAR_WIDTH/2, self.player_car.y + CAR_HEIGHT/2))
			self.player_car.distance_array[i] = distance
			i += 1
		player_car.draw(win)

		# DRAW A  POINT
		if self.best_position != (0,0):
			pygame.draw.circle(win, (255, 0, 0), self.best_position, 5)

		pygame.display.update()

	def move_player(self, player_car, action):
		moved = False

		# W A S D
		#[0,0,0,0]

		if np.array_equal(action, [1, 0, 0, 0]):
			player_car.move_forward()
			moved = True
		if np.array_equal(action, [0, 0, 1, 0]):
			player_car.move_backward()
			moved = True
		
		if np.array_equal(action, [0, 1, 0, 0]):
			player_car.rotate(left=True)
		elif np.array_equal(action, [0, 0, 0, 1]):
			player_car.rotate(right=True)

		if not moved:
			player_car.reduce_speed()

	def handle_collision(self, player_car):

		wavefront_value = self.wavefront_result_matrix[int(self.player_car.x + CAR_WIDTH/2)][int(self.player_car.y + CAR_HEIGHT/2)].value

		self.score = wavefront_value
		
		if player_car.collide(TRACK_BORDER_MASK) != None:
			self.reward = -100
			self.done = True
			self.add_to_historic_positions((int(self.player_car.x + CAR_WIDTH/2), int(self.player_car.y + CAR_HEIGHT/2)))
		else :
			self.reward = (self.new_distance - self.old_distance) * 3

		for bullet in player_car.sensors:
			if bullet.collide() != None:
				bullet.draw_line(WIN, player_car)

		player_finish_poi_collide = player_car.collide(FINISH_MASK, *FINISH_POSITION)
		if player_finish_poi_collide != None:
			if player_finish_poi_collide[1] == 0:
				self.reward = -100
				player_car.bounce()
			else:
				self.reward = 10000
				self.done = True
				self.add_to_historic_positions((int(self.player_car.x + CAR_WIDTH/2), int(self.player_car.y + CAR_HEIGHT/2)))
		
			

