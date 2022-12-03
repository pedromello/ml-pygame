import pygame
import time
import math
from utils import scale_image, blit_rotate_center, blit_text_center, contains
pygame.font.init()
from wavefront import wave_front
from matplotlib import pyplot as plt
import numpy as np

GRASS = scale_image(pygame.image.load("imgs/grass.jpg"), 2.5)
TRACK = scale_image(pygame.image.load("imgs/track.png"), 0.9)

TRACK_BORDER = scale_image(pygame.image.load("imgs/track-border.png"), 0.9)
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)

WAVEFRONT_TRACK_BORDER = scale_image(pygame.image.load("imgs/wavefront-track.png"), 0.9)
WAVEFRONT_TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)

FINISH = pygame.image.load("imgs/finish.png")
FINISH_MASK = pygame.mask.from_surface(FINISH)

FINISH_POSITION = (130, 250)

RED_CAR = scale_image(pygame.image.load("imgs/red-car.png"), 0.40)
GREEN_CAR = scale_image(pygame.image.load("imgs/green-car.png"), 0.40)

CAR_WIDTH, CAR_HEIGHT = RED_CAR.get_width(), RED_CAR.get_height()

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racing Game!")

MAIN_FONT = pygame.font.SysFont("comicsans", 44)

WAVEFRONT_INITIAL_POSITION = (200, 250)

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
		return math.sqrt((car.x - self.last_poi[0])**2 + (car.y - self.last_poi[1])**2)
		
class PlayerCar(AbstractCar):
	IMG = RED_CAR
	START_POS = (180, 200)

	def __init__(self, max_vel, rotation_vel):
		super().__init__(max_vel, rotation_vel)
		self.sensors = [SensorBullet(self, 25, 12, (100, 0, 255)), SensorBullet(self, 10, 12, (200, 0, 255)), SensorBullet(self, 0, 12, (0, 255, 0)), SensorBullet(self, -10, 12, (0, 0, 255)), SensorBullet(self, -25, 12, (0, 0, 255))]
		self.last_wavefront_value = 0
		self.current_wavefront_value = 0
		self.last_vel_value = 0

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
		return [bullet.get_distance_from_poi(self) for bullet in self.sensors]

	def move_forward(self):
		self.last_vel_value = self.vel
		self.vel = min(self.vel + self.acceleration, self.max_vel)
		self.move()

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

		self.reward = 0
		self.done = False
		self.score = 0

		self.old_distance = 0
		self.new_distance = 0

		self.clock = pygame.time.Clock()
		self.reset()

		self.iterations = 0
		self.MAX_ITERATIONS = 60*30
	

	def next_level(self):
		self.level += 1
		self.started = False

	def reset(self):
		self.level = 1
		self.started = False
		self.level_start_time = 0

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
		return [*self.player_car.get_distance_array(), self.player_car.vel, self.player_car.angle] 

	def loop_check(self):
		if(self.player_car.vel <= 0.5):
			self.iterations += 1
			if(self.iterations > 60*10):
				print(self.iterations)
		else:
			self.iterations = 0
		if(self.iterations >= self.MAX_ITERATIONS):
			self.done = True

	def play_step(self, action):
		self.done = False
		self.draw(WIN, self.images, self.player_car)
		self.clock.tick(60)

		self.move_player(self.player_car, action)

		self.old_distance = self.new_distance
		self.new_distance = self.wavefront_result_matrix[int(self.player_car.x + CAR_WIDTH/2)][int(self.player_car.y + CAR_HEIGHT/2)].value

		self.handle_collision(self.player_car)
		self.player_car.sensorControl()

		self.loop_check()

		return self.reward, self.done, self.score

	def draw(self, win, images, player_car):
		for img, pos in images:
			win.blit(img, pos)

		player_car.draw(win)

		for bullet in player_car.sensors:
			bullet.draw(win)

		# DRAW A  POINT
		pygame.draw.circle(win, (255, 0, 0), WAVEFRONT_INITIAL_POSITION, 5)

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
		else :
			self.reward = self.new_distance - self.old_distance

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

