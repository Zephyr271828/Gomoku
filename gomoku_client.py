import json
import socket
import sys
import threading
import time

import pygame
from pygame.locals import *

HOST = "xuyufengdeMacBook-Pro.local"
PORT = 12345

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (252, 204, 116)

N = 18
SPACE = 1
STONE_RADIUS = 10
BLOCK_SIZE = 36
FONT_SIZE = 32
MARGIN = 24
SCREEN_WIDTH = N * BLOCK_SIZE + (N + 1) * SPACE + 2 * MARGIN
SCREEN_HEIGHT = SCREEN_WIDTH

locs = []
for i in range(N + 1):
    tmp = []
    for j in range(N + 1):
        tmp.append((MARGIN + SPACE + j * (SPACE + BLOCK_SIZE), MARGIN + SPACE + i * (SPACE + BLOCK_SIZE)))
    locs.append(tmp)

board = [[None for i in range(N + 1)] for j in range(N + 1)]

class Stone:

    def __init__(self, loc, color):
        self.loc = loc
        self.color = color
        self.r = STONE_RADIUS

stones = []

class Client:

    def __init__(self, host = "", port = 12345):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.name = input("Enter your name: ")
        self.socket.send(json.dumps({"action" : "log_in", "name" : self.name}).encode("utf-8"))
        #self.running = False
        self.playing = False
        self.win = None
        threading.Thread(target = self.recv).start()

    def recv(self):
        while True:
            
            raw_data = self.socket.recv(1024).decode("utf-8")

            i = 0
            while i < len(raw_data):
                j = raw_data.find('}', i)
                data = json.loads(raw_data[i:j + 1])
                i = j + 1   

                if data["action"] == "welcome":
                    print("Welcome,", self.name)

                if data["action"] == "wait":
                    print("Waiting for another player...")

                if data["action"] == "game":
                    print("Game starts!")

                    self.color = BLACK if data["id"] == 0 else WHITE
                    self.active = True if data["id"] == 0 else False

                    time.sleep(1)
                    #self.running = True
                    self.playing = True

                if data["action"] == "play":
                    stone = Stone(locs[data["ij"][0]][data["ij"][1]], data["color"])
                    stones.append(stone)
                    board[data["ij"][0]][data["ij"][1]] = "Black" if data["color"] == BLACK else "White"
                    self.active = True

                if data["action"] == "end_game":
                    client.win = False
                    client.playing = False

                if data["action"] == "quit":
                    self.playing = False
                    #self.running = False
                    #print("Your opponent has left the game")
                    #print("Waiting for another player...")

def detect(i, j, dr, s):
    def helper(i, j, dr, s):
        if i < 0 or i > N or j < 0 or j > N:
            return 0
        if board[i][j] != s:
            return 0
        return 1 + helper(i + dr[1], j + dr[0], dr, s)
    return helper(i, j, dr, s) + helper(i, j, (-dr[0], -dr[1]), s) - 1

client = Client(HOST, PORT)

while not client.playing:
    pass

pygame.init()

pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

try:
    pygame.mixer.music.load("go/白纻.mp3")
except:
    pygame.mixer.music.load("白纻.mp3")
    pygame.mixer.music.play(loops = -1)

while client.playing:

    screen.fill(YELLOW)

    L = SCREEN_WIDTH - 2 * MARGIN
    surf1 = pygame.Surface((L, L))
    surf1.fill(BLACK)
    screen.blit(surf1, (MARGIN, MARGIN))

    surf2 = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
    surf2.fill(YELLOW)
    for i in range(N):
        for j in range(N):
            screen.blit(surf2, locs[i][j])
        
    for i in [3, 9, 15]:
        for j in [3, 9, 15]:
            pygame.draw.circle(screen, BLACK, locs[i][j], 4)

    for stone in stones:
        pygame.draw.circle(screen, stone.color, stone.loc, stone.r)

    for event in pygame.event.get():
        if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
            client.socket.send(json.dumps({"action" : "quit"}).encode("utf-8"))
            client.playing = False
            #client.running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not client.active:
                continue

            pos = pygame.mouse.get_pos()
            #print(pos)

            # find the nearest node
            x = (0, 1e9)
            y = (0, 1e9)
            for i in range(N + 1):
                d = abs(locs[0][i][0] - pos[0])
                if d < x[1]:
                    x = (i, d)
            for j in range(N + 1):
                d = abs(locs[j][0][1] - pos[1])
                if d < y[1]:
                    y = (j, d)
            i, j = y[0], x[0]
            #print((i, j))

            # add and render the stone
            if board[i][j] is None:
                stone = Stone(locs[i][j], client.color)
                stones.append(stone)
                pygame.draw.circle(screen, stone.color, stone.loc, stone.r)
                board[i][j] = "BLACK" if client.color == BLACK else "WHITE"

                client.socket.send(json.dumps({"action" : "play", "ij" : (i, j), "color" : client.color}).encode("utf-8"))

                # detect a 5 in column
                c = detect(i, j, (0, 1), board[i][j])

                # detect a 5 in row
                r = detect(i, j, (1, 0), board[i][j])

                # detect a 5 in diagonal
                d1 = detect(i, j, (1, -1), board[i][j])
                d2 = detect(i, j, (1, 1), board[i][j])
                
                #print(max(c, r, d1, d2))
                if max(c, r, d1, d2) >= 5:
                    client.socket.send(json.dumps({"action" : "end_game"}).encode("utf-8"))
                    client.win = True
                    client.playing = False 

                    #client.running = False

                client.active = False

    caption = "Your turn" if client.active else "Opponent's turn"
    pygame.display.set_caption(caption)

    pygame.display.update()

time.sleep(0.5)

if client.win is not None:
    font = pygame.font.Font("freesansbold.ttf", FONT_SIZE)
    strr = "You won!" if client.win == True else "You lost!"
    text = font.render(strr, True, BLACK) 
    textRect = text.get_rect()
    textRect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    screen.blit(text, textRect)
    pygame.display.update()
    time.sleep(1)

#pygame.quit()
sys.exit()  
    




        


    