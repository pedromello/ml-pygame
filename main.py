import pygame
import time
import math
from utils import scale_image, blit_rotate_center, blit_text_center, contains
pygame.font.init()
from agent import Agent

GRASS = scale_image(pygame.image.load("imgs/grass.jpg"), 2.5)
TRACK = scale_image(pygame.image.load("imgs/track.png"), 0.9)

TRACK_BORDER = scale_image(pygame.image.load("imgs/track-border.png"), 0.9)
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)

FINISH = pygame.image.load("imgs/finish.png")
FINISH_MASK = pygame.mask.from_surface(FINISH)
# FINISH_POSITION = (130, 250)
FINISH_POSITION = (130, 250)

RED_CAR = scale_image(pygame.image.load("imgs/red-car.png"), 0.40)
GREEN_CAR = scale_image(pygame.image.load("imgs/green-car.png"), 0.40)

CAR_WIDTH, CAR_HEIGHT = RED_CAR.get_width(), RED_CAR.get_height()

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racing Game!")

MAIN_FONT = pygame.font.SysFont("comicsans", 44)

FPS = 60
PATH = [(175, 119), (110, 70), (56, 133), (70, 481), (318, 731), (404, 680), (418, 521), (507, 475), (600, 551), (613, 715), (736, 713),
		(734, 399), (611, 357), (409, 343), (433, 257), (697, 258), (738, 123), (581, 71), (303, 78), (275, 377), (176, 388), (178, 260)]


class GameInfo:
	LEVELS = 10

	def __init__(self, level=1):
		self.level = level
		self.started = False
		self.level_start_time = 0

	def next_level(self):
		self.level += 1
		self.started = False

	def reset(self):
		self.level = 1
		self.started = False
		self.level_start_time = 0

	def game_finished(self):
		return self.level > self.LEVELS

	def start_level(self):
		self.started = True
		self.level_start_time = time.time()

	def get_level_time(self):
		if not self.started:
			return 0
		return round(time.time() - self.level_start_time)


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
	global last_reward

	def __init__(self, max_vel, rotation_vel):
		super().__init__(max_vel, rotation_vel)
		self.sensors = [SensorBullet(self, 25, 12, (0, 0, 255)), SensorBullet(self, 10, 12, (0, 0, 255)), SensorBullet(self, 0, 12, (0, 255, 0)), SensorBullet(self, -10, 12, (0, 0, 255)), SensorBullet(self, -25, 12, (0, 0, 255))]
		# self.distance = ComputerCar.

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
		#print(contains(self.sensors, lambda x: x.hit))

		for bullet in self.sensors:
			if not bullet.fired:
				bullet.fire(self)

		for bullet in self.sensors:
			bullet.move()
	
	def get_distance_array(self):
		return [bullet.get_distance_from_poi(self) for bullet in self.sensors]

	def move_forward(self):
		self.vel = min(self.vel + self.acceleration, self.max_vel)
		if self.vel >= 2:
			last_reward = 5
		self.move()

	# def final_distance(self):
	# 	res = math.sqrt((self.x - FINISH_POSITION[0])**2 + (self.y - FINISH_POSITION[1])**2)
	# 	return res

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

# class Reward():
#     def __init__(self):
#         self.last_reward = 0

#     def set_last_reward(self, reward):
#         self.last_reward = reward

#     def get_last_reward(self):
#         return self.last_reward

def draw(win, images, player_car, computer_car, game_info):
	for img, pos in images:
		win.blit(img, pos)

	level_text = MAIN_FONT.render(
		f"Level {game_info.level}", 1, (255, 255, 255))
	win.blit(level_text, (10, HEIGHT - level_text.get_height() - 70))

	time_text = MAIN_FONT.render(
		f"Time: {game_info.get_level_time()}s", 1, (255, 255, 255))
	win.blit(time_text, (10, HEIGHT - time_text.get_height() - 40))

	vel_text = MAIN_FONT.render(
		f"Vel: {round(player_car.vel, 1)}px/s", 1, (255, 255, 255))
	win.blit(vel_text, (10, HEIGHT - vel_text.get_height() - 10))

	player_car.draw(win)
	computer_car.draw(win)

	for bullet in player_car.sensors:
		bullet.draw(win)

	pygame.display.update()

def move_player(player_car, action):
	global last_reward
	# keys = pygame.key.get_pressed()
	keys = action
	# print('aqui porra', keys.item())
	moved = False

	#Trocar só a condição
	if keys == 2:
		last_reward = 0.3
		player_car.rotate(left=True)
	if keys == 3:
		last_reward = 0.3
		player_car.rotate(right=True)
	if keys == 0:
		last_reward = -0.1
		moved = True
		player_car.move_forward()
	if keys == 1:
		last_reward = -0.5
		moved = True
		player_car.move_backward()

	if not moved:
		player_car.reduce_speed()


def handle_collision(player_car, computer_car, game_info):
	global last_reward
	if player_car.collide(TRACK_BORDER_MASK) != None:
		last_reward = -20
		player_car.bounce()

	for bullet in player_car.sensors:
		if bullet.collide() != None:
			bullet.draw_line(WIN, player_car)

	computer_finish_poi_collide = computer_car.collide(FINISH_MASK, *FINISH_POSITION)
	if computer_finish_poi_collide != None:
		blit_text_center(WIN, MAIN_FONT, "You lost!")
		pygame.display.update()
		pygame.time.wait(5000)
		game_info.reset()
		player_car.reset()
		computer_car.reset()
		print("saving brain...")
		agent.save()

	player_finish_poi_collide = player_car.collide(FINISH_MASK, *FINISH_POSITION)
	if player_finish_poi_collide != None:
		if player_finish_poi_collide[1] == 0:
			last_reward = -50
			player_car.bounce()
		else:
			last_reward = 100
			game_info.next_level()
			player_car.reset()
			computer_car.next_level(game_info.level)
			print("saving brain...")
			agent.save()

# def sum_last100_rewards

run = True
clock = pygame.time.Clock()
images = [(GRASS, (0, 0)), (TRACK, (0, 0)),
		  (FINISH, FINISH_POSITION), (TRACK_BORDER, (0, 0))]
player_car = PlayerCar(2.5, 4)
computer_car = ComputerCar(2, 4, PATH)
game_info = GameInfo()
agent = Agent(6, 4, 0.9)
last_reward = 0
# sum_last100_rewards = 0
# best_sum = 0
scores = []
#Acoes: 0 -> W, 1 -> S, 2 -> A, 3 -> D
action_decision = [0, 1, 2, 3]
print("loading last saved brain...")
agent.load()

while run:
	clock.tick(FPS)

	draw(WIN, images, player_car, computer_car, game_info)

	while not game_info.started:
		# blit_text_center(WIN, MAIN_FONT, f"Press any key to start level {game_info.level}!")
		# pygame.display.update()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				last_reward = -4
				print("saving brain...")
				agent.save()
				pygame.quit()
				break

			# if event.type == pygame.KEYDOWN:
			game_info.start_level()

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			last_reward = -4
			print("saving brain...")
			agent.save()
			run = False
			break

	#Adicionar os sensores e verificar se há a necessidade da orientação
	last_signal = [*player_car.get_distance_array(), player_car.vel] # esse é o vetor de entrada, composto por três sinais dos sensores mais a orientação positiva e negativa
	action = agent.update(last_reward, last_signal) # a rede neural vai indicar a próxima ação
	scores.append(agent.score())
	move_player(player_car, action_decision[action])
	computer_car.move()

	handle_collision(player_car, computer_car, game_info)
	player_car.sensorControl()

	print('last_reward', last_reward)
	# print(player_car.get_distance_array())

	if game_info.game_finished():
		blit_text_center(WIN, MAIN_FONT, "You won the game!")
		pygame.time.wait(20)
		last_reward = -4
		print("saving brain...")
		agent.save()
		game_info.reset()
		player_car.reset()
		computer_car.reset()


pygame.quit()
