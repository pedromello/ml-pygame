import torch
import random
import numpy as np
from collections import deque
from game import GameInfo
from model import Linear_QNet, QTrainer
from helper import plot
import sys

MAX_MEMORY = 200_000
BATCH_SIZE = 2000
LR = 0.5

class Agent:

    def __init__(self):
        self.n_games = 0
        # Esse 5 é 0.05
        self.initial_epsilon = 20
        self.final_epsilon = 5
        self.epsilon = self.initial_epsilon # randomness
        self.gamma = 0.95 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY) # popleft()
        self.model = Linear_QNet(13, 6, 3)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        #for state, action, reward, nexrt_state, done in mini_sample:
        #    self.trainer.train_step(state, action, reward, next_state, done)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random moves: tradeoff exploration / exploitation
        self.epsilon = max(self.final_epsilon, self.epsilon - self.n_games * 0.01)
        final_move = [0,0,0]
        if random.randint(0, 100) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, device="cuda", dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            
            final_move[move] = 1

        return final_move


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = GameInfo()
    while True:
        # get old state
        state_old = game.get_state()

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.play_step(final_move)
        state_new = game.get_state()

        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            name_from_terminal = ""
            if len(sys.argv) > 1:
                name_from_terminal = sys.argv[1]
            # train long memory, plot result
            car_position = (game.player_car.x, game.player_car.y)
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                game.new_best_position(car_position)
                agent.model.save('model_' + name_from_terminal + '.pth')

            #print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            
            plot(plot_scores, plot_mean_scores, name_from_terminal)


if __name__ == '__main__':
    train()