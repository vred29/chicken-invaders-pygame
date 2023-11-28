import pygame
import random
import time
import os
from pygame.locals import *

pygame.font.init()
pygame.mixer.init()

# initialise game
pygame.init()
WIDTH, HEIGHT = 750, 750
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CHICKEN INVADERS")

# load images
PLAYER = pygame.transform.scale(pygame.image.load("space_ship.png"), (60, 60))
CHICKEN = pygame.transform.scale(pygame.image.load("chicken2.png"), (60, 60))
CHICKEN_BOSS = pygame.transform.scale(pygame.image.load("chicken2.png"), (200, 200))

# load audio
shoot = pygame.mixer.Sound("shoot.wav")
shoot.set_volume(0.04)

chicken = pygame.mixer.Sound("chicken.wav")
chicken.set_volume(0.04)

egg = pygame.mixer.Sound("egg.wav")
egg.set_volume(0.04)

explosion = pygame.mixer.Sound("explosion.wav")
explosion.set_volume(0.045)

pygame.mixer.music.load("background.wav")
pygame.mixer.music.play(-1, 0.0)
pygame.mixer.music.set_volume(0.025)

# lasers
LASER_PLAYER = pygame.transform.scale(pygame.image.load("red_laser.png"), (15, 15))
LASER_CHICKEN = pygame.transform.scale(pygame.image.load("Egg.png"), (20, 20))
LASER_CHICKEN_BOSS = pygame.transform.scale(pygame.image.load("Egg.png"), (70, 70))

# background
BG = pygame.transform.scale(pygame.image.load("background_space.png"), (WIDTH, HEIGHT))


class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not (self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


def collide(obj1, obj2):
    offset_x = int(obj2.x - obj1.x)
    offset_y = int(obj2.y - obj1.y)
    return (obj1.mask.overlap(obj2.mask, (offset_x, offset_y)))


class Ship:
    COOLDOWN = 30

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                self.lasers.remove(laser)
                return 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


class Player(Ship):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.ship_img = PLAYER
        self.laser_img = LASER_PLAYER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.score = 0

    def move_lasers(self, vel, objs, score):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        chicken.play()
                        objs.remove(obj)
                        self.score += score
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def move_lasers_boss(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                # for obj in objs:
                if laser.collision(obj):
                    chicken.play()
                    if obj.health - 5 == 0:
                        obj.health -= 5
                        self.score += 100
                    else:
                        obj.health -= 5
                    if laser in self.lasers:
                        self.lasers.remove(laser)

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + PLAYER.get_width() / 2 - LASER_PLAYER.get_width() / 2, self.y, self.laser_img)
            shoot.play()
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def reset(self):
        self.x = WIDTH / 2 - PLAYER.get_width() / 2
        self.y = HEIGHT - 20 - PLAYER.get_height()


class Enemy(Ship):

    def __init__(self, x, y):
        super().__init__(x, y)
        self.ship_img = CHICKEN
        self.laser_img = LASER_CHICKEN
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.cooldown_left = 0
        self.cooldown_right = 0

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + CHICKEN.get_width() / 2 - LASER_CHICKEN.get_width() / 2,
                          self.y + CHICKEN.get_height(), self.laser_img)
            egg.play()
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def move_conditions(self, vel):
        if self.cooldown_left <= 60:
            if self.x - vel >= 0:
                self.move(vel)
            self.cooldown_left += 1
        elif self.cooldown_right <= 60:
            if self.x + vel <= WIDTH - self.get_width():
                self.move(-vel)
            self.cooldown_right += 1
        else:
            self.cooldown_left = 0
            self.cooldown_right = 0

    def move(self, vel):
        self.x -= vel


class Enemy_boss(Enemy):
    LEFT = random.randrange(0, 90)
    RIGHT = random.randrange(0, 120)

    def __init__(self, x, y, health=100):
        super().__init__(x, y)
        self.ship_img = CHICKEN_BOSS
        self.laser_img = LASER_CHICKEN_BOSS
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.cooldown_left = 0
        self.cooldown_right = 0
        self.max_health = health
        self.health = health

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, (255, 0, 0),
                         (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0, 255, 0), (
        self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health / self.max_health),
        10))

    def move_conditions(self, vel):
        if self.cooldown_left <= self.LEFT:
            if self.x - vel >= 0:
                self.move(vel)
            self.cooldown_left += 1
        elif self.cooldown_right <= self.RIGHT:
            if self.x + vel <= WIDTH - self.get_width():
                self.move(-vel)
            self.cooldown_right += 1
        else:
            self.cooldown_left = 0
            self.cooldown_right = 0
            self.LEFT = random.randrange(0, 120)
            self.RIGHT = random.randrange(0, 120)

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + CHICKEN_BOSS.get_width() / 2 - LASER_CHICKEN_BOSS.get_width() / 2,
                          self.y + CHICKEN_BOSS.get_height(), self.laser_img)
            egg.play()
            self.lasers.append(laser)
            self.cool_down_counter = 1


def main_loop(laser_vel_chicken, add_laser_vel, chicken_vel, player_vel, laser_vel, add_chicken, probability, score,
              difficulty, boss_level):
    # variabile

    run = True
    lost = False
    FPS = 60
    level = 0
    lives = 5
    lost_count = 0
    pause = False

    # fonturile textelor
    main_font = pygame.font.SysFont("timesnewroman", 60)
    lost_font = pygame.font.SysFont("timesnewroman", 100)
    pause_font = pygame.font.SysFont("timesnewroman", 80)
    unpause_font = pygame.font.SysFont("timesnewroman", 60)

    # enemies
    enemies = []
    wave_length = 0
    boss = None

    # jucator
    player = Player(WIDTH / 2 - PLAYER.get_width() / 2, HEIGHT - 20 - PLAYER.get_height())
    clock = pygame.time.Clock()

    def redraw_window():

        # background
        SCREEN.blit(BG, (0, 0))

        # text
        lives_label = main_font.render(f"Lives: {lives}", 1, (255, 50, 0))
        level_label = main_font.render(f"Level: {level}", 1, (255, 50, 0))
        score_label = main_font.render(f"Score: {player.score}", 1, (255, 50, 0))
        # difficulty_label = main_font.render(difficulty,1,(255,50,0))

        SCREEN.blit(lives_label, (10, 10))
        SCREEN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))
        SCREEN.blit(score_label, (WIDTH / 2 - score_label.get_width() / 2, 10))
        # SCREEN.blit(difficulty_label,(WIDTH/2 - level_label.get_width()/2 ,10))

        # jucator&gaini
        if pause:
            pause_label = pause_font.render("Game Paused", 1, (255, 50, 0))
            SCREEN.blit(pause_label,
                        (WIDTH / 2 - pause_label.get_width() / 2, HEIGHT / 2 - pause_label.get_height() / 2))
            unpause_label = unpause_font.render("Press SPACE to resume game", 1, (255, 50, 0))
            SCREEN.blit(unpause_label, (WIDTH / 2 - unpause_label.get_width() / 2,
                                        HEIGHT / 2 + pause_label.get_height() - unpause_label.get_height() / 2))

        else:
            player.draw(SCREEN)
            if boss != None:
                boss.draw(SCREEN)
            else:
                if (len(enemies) != 0):
                    for enemy in enemies:
                        enemy.draw(SCREEN)

        # mesaj de game over
        if lost:
            lost_label = lost_font.render("Game over!", 1, (255, 255, 255))
            SCREEN.blit(lost_label, (WIDTH / 2 - lost_label.get_width() / 2, HEIGHT / 2 - lost_label.get_height() / 2))

        pygame.display.update()

    while run:

        clock.tick(FPS)

        redraw_window()

        # conditie game over
        if lives <= 0:
            lost = True
            lost_count += 1

        # oprire joc daca s a pierdut
        if lost:
            if lost_count > FPS * 3:
                run = False
                print(f"Scor: {player.score}, Dificultate: {difficulty}")
            else:
                continue

        # conditie creere gaini

        if len(enemies) == 0:
            if boss == None:
                level += 1
            if level % boss_level == 0:
                if boss == None:
                    boss = Enemy_boss(WIDTH / 2 - CHICKEN_BOSS.get_width() / 2, 60)
                else:
                    if boss.health == 0:
                        boss = None

            else:
                laser_vel_chicken += add_laser_vel
                wave_length += add_chicken
                for i in range(wave_length):
                    enemy = Enemy(random.randrange(5, WIDTH - CHICKEN.get_width() - 5),
                                  random.randrange(60, int(HEIGHT / 2 - CHICKEN.get_height() - 5))
)
                    enemies.append(enemy)

        # conditie iesire joc
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == K_SPACE:
                    if pause == True:
                        pause = False
                    elif pause == False:
                        pause = True
                if event.key == K_ESCAPE:
                    print(f"Scor: {player.score}, Dificultate: {difficulty}")
                    run = False

        if pause == True:
            continue

        keys = pygame.key.get_pressed()
        # move
        if keys[pygame.K_a] and player.x - player_vel >= 0:  # left
            player.x -= player_vel
        if keys[pygame.K_d] and player.x + player_vel + player.get_width() <= WIDTH:  # right
            player.x += player_vel
        if keys[pygame.K_w] and player.y - player_vel >= 0:  # up
            player.y -= player_vel
        if keys[pygame.K_s] and player.y + player_vel + player.get_height() <= HEIGHT:  # down
            player.y += player_vel
        # if keys[pygame.K_SPACE]:
        player.shoot()

        # shoot.play()
        if (boss != None):
            boss.move_conditions(chicken_vel)
            if random.randrange(0, probability * FPS) == 1:
                boss.shoot()
            if boss.move_lasers(laser_vel_chicken, player) == 1:
                explosion.play()
                lives -= 1
                player.reset()
            if collide(boss, player):
                explosion.play()
                lives -= 1
                boss.health -= 5
                player.reset()

            player.move_lasers_boss(-laser_vel, boss)

        else:
            if (len(enemies) != 0):
                for enemy in enemies[:]:
                    enemy.move_conditions(chicken_vel)

                    if random.randrange(0, probability * FPS) == 1:
                        enemy.shoot()

                    if enemy.move_lasers(laser_vel_chicken, player) == 1:
                        explosion.play()
                        lives -= 1
                        player.reset()
                    if collide(enemy, player):
                        explosion.play()
                        lives -= 1
                        enemies.remove(enemy)
                        player.reset()

                player.move_lasers(-laser_vel, enemies, score)


def main_menu():
    run = True
    title_font = pygame.font.SysFont("comicsans", 70)
    while run:
        SCREEN.blit(BG, (0, 0))
        title_label = title_font.render("Choose difficulty to start game", 1, (255, 255, 255))
        instructions_label = title_font.render("Press 1, 2 or 3 to start:", 1, (255, 255, 255))
        easy_label = title_font.render("1 - Easy", 1, (255, 255, 255))
        medium_label = title_font.render("2 - Medium", 1, (255, 255, 0))
        hard_label = title_font.render("3 - Hard", 1, (255, 0, 0))

        SCREEN.blit(title_label, (WIDTH / 2 - title_label.get_width() / 2, HEIGHT / 4 - title_label.get_height() / 2))
        SCREEN.blit(instructions_label, (
        WIDTH / 2 - instructions_label.get_width() / 2, 3 * HEIGHT / 8 - instructions_label.get_height() / 2))
        SCREEN.blit(easy_label, (WIDTH / 2 - easy_label.get_width() / 2, 4 * HEIGHT / 8 - easy_label.get_height() / 2))
        SCREEN.blit(medium_label,
                    (WIDTH / 2 - medium_label.get_width() / 2, 5 * HEIGHT / 8 - medium_label.get_height() / 2))
        SCREEN.blit(hard_label, (WIDTH / 2 - hard_label.get_width() / 2, 6 * HEIGHT / 8 - hard_label.get_height() / 2))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == K_1:
                    main_loop(laser_vel_chicken=1, add_laser_vel=1, chicken_vel=1, player_vel=7, laser_vel=9,
                              add_chicken=1, probability=10, score=1, difficulty="Easy", boss_level=10)
                if event.key == K_2:
                    main_loop(laser_vel_chicken=2, add_laser_vel=1, chicken_vel=2, player_vel=6, laser_vel=8,
                              add_chicken=2, probability=5, score=2, difficulty="Medium", boss_level=10)
                if event.key == K_3:
                    main_loop(laser_vel_chicken=3, add_laser_vel=2, chicken_vel=3, player_vel=5, laser_vel=7,
                              add_chicken=3, probability=3, score=3, difficulty="Hard", boss_level=5)

    pygame.quit()


main_menu()
