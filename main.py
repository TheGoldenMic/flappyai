# (C) 2023 TheGoldenMic Media LLC. Code by MrJack TheGoldenMic
# Tutorial: https://www.youtube.com/playlist?list=PLzMcBGfZo4-lwGZWXz5Qgta_YNX3_vLS2

import pygame
import neat
import time
import os
import random

pygame.font.init()

# WINDOWS SIZES
WIN_WIDHT  = 576
WIN_HEIGHT = 900

# IMAGES
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))
            ]
PIPE_IMG  = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG  = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG    = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("BurbankBigCondensed-Black", 50)

GEN = 0

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROTATION_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_cnt = 0
        self.vel = 0
        self.h = self.y
        self.img_cnt = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_cnt = 0
        self.h = self.y

    def move(self):
        self.tick_cnt += 1
        
        # Calculate new movement
        d = self.vel * self.tick_cnt + 1.5 * self.tick_cnt**2

        # FAilsafe checks
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2

        # Change bird y position
        self.y = self.y + d

        # Tilting the bird
        if (d < 0 or self.y < self.h + 50) and self.tilt < self.MAX_ROTATION:
            self.tilt = self.MAX_ROTATION
        elif self.tilt > -90:
                self.tilt -= self.ROTATION_VEL
    
    def draw(self, win):
        self.img_cnt += 1

        # Check animation state
        if self.img_cnt < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_cnt < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_cnt < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_cnt < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_cnt == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_cnt = 0

        # Display animation when tilting
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_cnt = self.ANIMATION_TIME * 2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.h = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        self.h = random.randrange(40, 450)
        self.top = self.h - self.PIPE_TOP.get_height()
        self.bottom = self.h + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask    = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset    = (self.x - bird.x, self.top    - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        
        return False

class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def draw_window(win, birds, pipes, base, score, gen, alive):
    # DRAW BG
    win.blit(BG_IMG, (0, -100))
    # DRAW PIPES
    for pipe in pipes:
        pipe.draw(win)
    # DRAW BASE
    base.draw(win)
    # DRAW BIRD
    for bird in birds:
        bird.draw(win)
    # DRAW SCORE
    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDHT - 10 - text.get_width(), 10))
    # DRAW GEN
    text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))
    # DRAW ALIVE
    text = STAT_FONT.render("Alive: " + str(alive), 1, (255, 255, 255))
    win.blit(text, (10, 10 + 5 + 40))

    pygame.display.update()

# MAIN IS ACTUALLY THE FITNESS FUNCTION FOR THE AI
def main(genomes, config):
    global GEN
    GEN += 1

    nets = []
    ge   = []
    birds = []

    PIPE_OFFSET = 700

    for _, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(genome)

    base = Base(730)
    pipes = [Pipe(PIPE_OFFSET)]

    win = pygame.display.set_mode((WIN_WIDHT, WIN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0

    run = True
    while run and len(birds) > 0:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_i = 0
        if len(birds) > 0 and len(pipes) > 1 and birds[0].x > birds[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_i == 1

        # BIRD MOVEMENT
        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_i].h), abs(bird.y - pipes[pipe_i].bottom)))

            if output[0] > 0.5:
                bird.jump()

        # MOVE PIPES
        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()

            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True # CHECK IF PLAYER PASSED THE PIPE
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe) # REMOVE PIPE WHEN IT GETS OFF THE SCREEN            pipe.move()
        
        if add_pipe: # ADD PIPES WHEN NEEDED
            score += 1
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(PIPE_OFFSET))
        for r in rem: # REMOVE PIPES OFF THE SCREEN
            pipes.remove(r)

        # CHECK IF BIRD HITS THE FLOOR OR THE SKY
        for x, bird in enumerate(birds):
            # bird.move()
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()

        draw_window(win, birds, pipes, base, score, GEN, len(birds))

def run_ai(config_path):
    # LOAD CONFIG
    config = neat.Config(neat.DefaultGenome,
                         neat.DefaultReproduction,
                         neat.DefaultSpeciesSet,
                         neat.DefaultStagnation,
                         config_path
                        )
    # POPULATION
    p = neat.Population(config)
    # STATS
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "neat.config")
    run_ai(config_path)