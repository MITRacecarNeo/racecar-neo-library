"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: racecar_games.py
File Description: Contains Flappy Bird and Space Invaders class, which can be played on the dot matrix display
"""

import numpy as np
import random

########################################################################################
# General Display
########################################################################################

lost = [
    [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0],
    [1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1]
]

win = [
    [1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0],
    [1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0]
]

########################################################################################
# Flappy Bird
########################################################################################
class Flappy:
    def __init__(self):
        self.time = 0
        self.run = True
        self.matrix = np.zeros((8, 24))
        self.birdX = 0
        self.birdY = 3
        self.bottom_pillarX = 8
        self.bottom_pillarY = 8
        self.bottom_pillarHeight = random.randint(1, 6)
        self.top_pillarX = 15
        self.top_pillarY = 0
        self.top_pillarHeight = random.randint(1, 6)
        self.score = 0
        self.matrix[self.birdY][self.birdX] = 1
        self.matrix[self.bottom_pillarY - self.bottom_pillarHeight:self.bottom_pillarY, self.bottom_pillarX] = 1
        self.matrix[self.top_pillarY:self.top_pillarHeight, self.top_pillarX] = 1

    def update(self, delta_time, press):
        self.time += delta_time

        if press and self.birdY > 1:
            self.birdY -= 2
        elif self.bottom_pillarX >= 0 and self.bottom_pillarX <= self.top_pillarX and self.birdY > self.bottom_pillarY - self.bottom_pillarHeight and self.birdY > 0:
            self.birdY -= 2

        if self.run and self.time > 0.2:
            self.time = 0

            if self.bottom_pillarX > 0:
                self.bottom_pillarX -= 1
            else:
                self.score += 1
                self.bottom_pillarX = 15
                self.bottom_pillarHeight = random.randint(1, 6)

            if self.top_pillarX > 0:
                self.top_pillarX -= 1
            else:
                self.score += 1
                self.top_pillarX = 15
                self.top_pillarHeight = random.randint(1, 6)

            if self.birdY < 7:
                self.birdY += 1

            self.matrix = np.zeros((8, 24))
            self.matrix[self.birdY][self.birdX] = 1
            self.matrix[self.bottom_pillarY - self.bottom_pillarHeight:self.bottom_pillarY, self.bottom_pillarX] = 1
            self.matrix[self.top_pillarY:self.top_pillarHeight, self.top_pillarX] = 1
            self.matrix[0:int(self.score / 8), 16:] = 1

            if self.score % 8 != 0:
                self.matrix[int(self.score / 8), 16:16 + (self.score % 8)] = 1

            if self.birdX == self.top_pillarX and self.birdY < self.top_pillarHeight:
                self.run = False

            if self.birdX == self.bottom_pillarX and self.birdY > self.bottom_pillarY - self.bottom_pillarHeight:
                self.run = False

            if self.score == 64:
                self.run = False

        elif not self.run and self.score == 64:
            self.matrix = win

        elif not self.run:
            self.matrix = lost

        else:
            pass

    def get_flappy(self):
        return self.matrix

    def get_run(self):
        return self.run

########################################################################################
# Space Invaders
########################################################################################

class Space:
    def __init__(self):
        self.time = 0
        self.run = True
        self.shot = False
        self.vic = False
        self.matrix = np.zeros(shape=(8, 24))
        self.player_x = 11
        self.player_y = 7
        self.bullet_x = 11
        self.bullet_y = 7
        self.invaders = [[0, 0], [2, 0], [4, 0], [6, 0], [8, 0], [10, 0], [12, 0], [14, 0], [16, 0], [18, 0], [20, 0], [22, 0]]
    
    def update(self, delta_time, left_press, right_press, bottom_press):

        self.time += delta_time

        if bottom_press:
            self.shot = True
            self.bullet_x = self.player_x
        
        if left_press and self.player_x > 0:
            self.player_x -= 1
        
        if right_press and self.player_x < 23:
            self.player_x += 1

        if self.time > 0.2:
            self.time = 0

            if self.run:
                if self.shot:
                    if self.bullet_y - 1 < 0:
                        self.shot = False
                        self.bullet_x = self.player_x
                        self.bullet_y = self.player_y
                    else:
                        self.bullet_y -= 1

                self.matrix = np.zeros(shape=(8, 24))

                i = 0
                while i < len(self.invaders):
                    if self.invaders[i][0] - 1 < 0:
                        self.invaders[i] = [23, self.invaders[i][1] + 1]
                    else:
                        self.invaders[i] = [self.invaders[i][0] - 1, self.invaders[i][1]]
                    if self.invaders[i][1] > 7:
                        self.run = False
                        break
                    elif self.invaders[i][0] == self.bullet_x and self.invaders[i][1] == self.bullet_y and self.shot:
                        del self.invaders[i]
                        self.shot = False
                        self.bullet_x = self.player_x
                        self.bullet_y = self.player_y
                        continue
                    else:
                        self.matrix[self.invaders[i][1], self.invaders[i][0]] = 1

                    i += 1

                if len(self.invaders) == 0:
                    self.vic = True

                self.matrix[self.player_y, self.player_x] = 1

                if self.shot:
                    self.matrix[self.bullet_y, self.bullet_x] = 1

            if not self.run and not self.vic:
                self.matrix = lost

            elif self.vic:
                self.matrix = win
    
    def get_space(self):
        return self.matrix