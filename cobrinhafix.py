import pygame
import sys
import random
import time
import os

# constantes

MENU = "menu"
JOGO = "jogo"
SCORE = "score"
HOW_TO_PLAY = "how_to_play"
WIDTH, HEIGHT = 1000, 800
BLOCK_SIZE = 20
INFO_WIDTH = 150
SNAKE_SPEED = 1
SNAKE_UPDATE_INTERVAL = 0.1  # seconds
ENEMY_UPDATE_INTERVAL = 0.5  # seconds
BOSS_UPDATE_INTERVAL = 0.2  # seconds
scores = []
VOLUME_INCREMENT = 0.1
MAX_VOLUME = 1.0
MIN_VOLUME = 0.0


# func
def carregar_scores():
    if os.path.exists('score.txt'):
        with open('score.txt', 'r') as f:
            for linha in f:
                nome, score = linha.strip().split(',')
                scores.append((nome, float(score)))
        scores.sort(key=lambda x: x[1], reverse=True)


def is_valid_character(char):
    return char.isalnum() or char in " _-"


def salvar_score(nome, score):
    with open('score.txt', 'a') as f:
        f.write(f"{nome},{score}\n")


def carregar_som(caminho):
    try:
        return pygame.mixer.Sound(caminho)
    except pygame.error as e:
        print(f"Erro no som: {e}")
        return None


class Snake:
    def __init__(self, x, y):
        self.head = (x, y)
        self.body = [(x, y)]
        self.direction = (0, -1)
        self.speed = SNAKE_SPEED
        self.grow = 0
        self.name = ""
        self.buffered_direction = self.direction

    def move(self):
        self.apply_buffered_direction()
        new_head = (self.head[0] + self.direction[0] * BLOCK_SIZE * self.speed,
                    self.head[1] + self.direction[1] * BLOCK_SIZE * self.speed)

        if new_head[0] < 0:
            new_head = (WIDTH - BLOCK_SIZE, new_head[1])
        elif new_head[0] >= WIDTH:
            new_head = (0, new_head[1])
        elif new_head[1] < 0:
            new_head = (new_head[0], HEIGHT - BLOCK_SIZE)
        elif new_head[1] >= HEIGHT:
            new_head = (new_head[0], 0)

        self.head = new_head
        self.body.insert(0, self.head)

        if self.grow > 0:
            self.grow -= 1
        else:
            self.body.pop()

        return new_head

    def change_direction(self, direction):
        if direction[0] != -self.direction[0] and direction[1] != -self.direction[1]:
            self.direction = direction
            self.buffered_direction = direction

    def apply_buffered_direction(self):
        if self.head[0] % BLOCK_SIZE == 0 and self.head[1] % BLOCK_SIZE == 0:
            self.direction = self.buffered_direction

    def grow_snake(self, segments):
        self.grow += segments

    def check_collision(self):
        if self.head in self.body[1:]:
            return True
        return False


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH + INFO_WIDTH, HEIGHT))
        pygame.display.set_caption("Snake")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 74)
        self.font_medium = pygame.font.Font(None, 50)
        self.font_small = pygame.font.Font(None, 24)
        self.volume = 1.0
        self.is_muted = False
        self.selected_menu_option = 0
        self.load_assets()
        self.set_volume(self.volume)
        self.reset()
        self.snake_timer = 0
        self.enemy_timer = 0
        self.boss_timer = 0
        self.last_direction_change_time = 0

    def load_assets(self):

        self.images = {
            "snake_head": pygame.transform.scale(pygame.image.load('cobra.png'), (BLOCK_SIZE, BLOCK_SIZE)),
            "snake_body": pygame.transform.scale(pygame.image.load('body.png'), (BLOCK_SIZE, BLOCK_SIZE)),
            "food": {
                0: pygame.transform.scale(pygame.image.load('maca.png'), (BLOCK_SIZE, BLOCK_SIZE)),
                1: pygame.transform.scale(pygame.image.load('laranja.png'), (BLOCK_SIZE, BLOCK_SIZE)),
                2: pygame.transform.scale(pygame.image.load('pera.png'), (BLOCK_SIZE, BLOCK_SIZE)),
                3: pygame.transform.scale(pygame.image.load('uva.png'), (BLOCK_SIZE, BLOCK_SIZE)),
            },
            "item": pygame.transform.scale(pygame.image.load('item.png'), (BLOCK_SIZE, BLOCK_SIZE)),
            "enemy": pygame.transform.scale(pygame.image.load('inimigo.png'), (BLOCK_SIZE, BLOCK_SIZE)),
            "boss": pygame.transform.scale(pygame.image.load('boss.png'), (BLOCK_SIZE * 2, BLOCK_SIZE * 2)),
            "menu_background": pygame.image.load('menu.png'),
            "score_background": pygame.image.load('score.png'),
            "game_background": pygame.image.load('game.png'),
            "how_image": pygame.image.load('tutorial.png')
        }
        self.sounds = {
            "eat": carregar_som('eat.wav'),
            "enemy": carregar_som('inimigo.wav'),
            "game_over": carregar_som('go.wav'),
            "level_up": carregar_som('nvl.wav'),
            "boss": carregar_som('boss.wav'),
            "item": carregar_som('item.wav'),
            "enemy_death": carregar_som('inimigo_death.wav'),
            "game_sound": carregar_som('game.wav'),
            "menu_sound": carregar_som('menu.wav'),
            "score_sound": carregar_som('score.wav'),
            "boss_death": carregar_som('boss_death.wav')
        }

        self.set_volume(self.volume)

    def set_volume(self, volume):
        self.volume = volume
        pygame.mixer.music.set_volume(self.volume)
        self.is_muted = (self.volume == 0.0)
        for sound in self.sounds.values():
            sound.set_volume(self.volume)

    def toggle_mute(self):
        if self.is_muted:
            self.set_volume(self.previous_volume)
        else:
            self.previous_volume = self.volume
            self.set_volume(0.0)

    def play_sound(self, sound_name, loop=False):
        sound = self.sounds[sound_name]
        if loop:
            sound.play(loops=-1)
        else:
            sound.play()

    def stop_sound(self, sound_name):
        self.sounds[sound_name].stop()

    def stop_all_sounds(self):
        for sound in self.sounds.values():
            sound.stop()

    def reset(self):
        self.snake = Snake(WIDTH // 2, HEIGHT // 2)
        self.food = self.generate_food()
        self.items = self.generate_item()
        self.enemies = self.generate_enemies()
        self.bosses = []
        self.state = MENU
        self.level = 1
        self.food_collected = 0
        self.start_time = time.time()
        self.elapsed_time = 0
        self.score = 0
        carregar_scores()

    @staticmethod
    def generate_food():
        food_count = random.randint(1, 4)
        food = []
        for _ in range(food_count):
            pos = (random.randint(0, (WIDTH // BLOCK_SIZE) - 1) * BLOCK_SIZE,
                   random.randint(0, (HEIGHT // BLOCK_SIZE) - 1) * BLOCK_SIZE)
            bonus = random.randint(0, 3)
            food.append({"pos": pos, "bonus": bonus})
        return food

    @staticmethod
    def generate_item():
        chance = random.randint(1, 100)
        item_type = 0 if chance <= 25 else 1 if chance <= 50 else 2 if chance <= 75 else 3 if chance <= 95 else 4
        pos = (random.randint(0, (WIDTH // BLOCK_SIZE) - 1) * BLOCK_SIZE,
               random.randint(0, (HEIGHT // BLOCK_SIZE) - 1) * BLOCK_SIZE)
        return [{"pos": pos, "type": item_type}]

    @staticmethod
    def generate_enemies():
        enemy_count = random.randint(1, 5)
        enemies = []
        for _ in range(enemy_count):
            pos = (random.randint(0, (WIDTH // BLOCK_SIZE) - 1) * BLOCK_SIZE,
                   random.randint(0, (HEIGHT // BLOCK_SIZE) - 1) * BLOCK_SIZE)
            direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            enemies.append({"pos": pos, "dir": direction})
        return enemies

    @staticmethod
    def generate_boss():
        pos = (WIDTH // 2 - BLOCK_SIZE, HEIGHT // 2 - BLOCK_SIZE)
        return {"pos": pos, "dir": (0, -1), "size": BLOCK_SIZE * 2}

    @staticmethod
    def move_boss(boss, snake_head):
        delta_x = snake_head[0] - boss["pos"][0]
        delta_y = snake_head[1] - boss["pos"][1]
        distance = (delta_x ** 2 + delta_y ** 2) ** 0.5
        if distance != 0:
            boss["pos"] = (
                boss["pos"][0] + int(delta_x / distance * BLOCK_SIZE),
                boss["pos"][1] + int(delta_y / distance * BLOCK_SIZE)
            )
        return boss

    def draw_text(self, text, size, color, pos):
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, pos)

    def draw_menu(self):
        self.screen.blit(self.images["menu_background"], (0, 0))
        options = [
            "Novo Jogo",
            "Score",
            "Como jogar?",
            "Volume",
            "Sair"
        ]

        index = 0
        option = options[index]
        color = (0, 0, 255) if index != self.selected_menu_option else (255, 0, 0)
        self.draw_text(option, 50, color, (200, 120))

        index = 1
        option = options[index]
        color = (0, 0, 255) if index != self.selected_menu_option else (255, 0, 0)
        self.draw_text(option, 50, color, (230, 255))

        index = 2
        option = options[index]
        color = (0, 0, 255) if index != self.selected_menu_option else (255, 0, 0)
        self.draw_text(option, 38, color, (200, 395))

        index = 3
        option = options[index]
        color = (0, 0, 255) if index != self.selected_menu_option else (255, 0, 0)
        self.draw_text(option, 50, color, (215, 518))

        index = 4
        option = options[index]
        color = (0, 0, 255) if index != self.selected_menu_option else (255, 0, 0)
        self.draw_text(option, 50, color, (240, 650))

        if self.selected_menu_option == 3:
            volume_text = f"{'Silencioso' if self.is_muted else f'{int(self.volume * 100)}%'}"
            color = (0, 0, 255) if index != self.selected_menu_option else (255, 0, 0)
            self.draw_text(volume_text, 50, color,(400, 518))

        pygame.display.flip()

    def draw_game(self):
        self.screen.blit(self.images["game_background"], (0, 0))

        # draw snake
        for i, pos in enumerate(self.snake.body):
            if i == 0:
                rotated_image = self.rotate_image(self.images["snake_head"], self.snake.direction)
                self.screen.blit(rotated_image, pos)
            else:
                self.screen.blit(self.images["snake_body"], pos)

        # draw food
        for f in self.food:
            self.screen.blit(self.images["food"][f["bonus"]], f["pos"])

        # draw items
        for item in self.items:
            self.screen.blit(self.images["item"], item["pos"])

        # draw enemies
        for enemy in self.enemies:
            rotated_image = self.rotate_image(self.images["enemy"], enemy["dir"])
            self.screen.blit(rotated_image, enemy["pos"])

        # draw boss
        for boss in self.bosses:
            rotated_image = self.rotate_image(self.images["boss"], boss["dir"])
            self.screen.blit(rotated_image, boss["pos"])

        # draw info
        info_rect = pygame.Rect(WIDTH, 0, INFO_WIDTH, HEIGHT)
        pygame.draw.rect(self.screen, (50, 50, 50), info_rect)

        self.draw_text(f"Tempo: {self.elapsed_time:.1f}s", 24, (255, 255, 255), (WIDTH + 10, 10))
        self.draw_text(f"Pontuação: {self.score:.2f}", 24, (255, 255, 255), (WIDTH + 10, 30))
        self.draw_text(f"Comidas: {self.food_collected}", 24, (255, 255, 255), (WIDTH + 10, 50))

        pygame.display.flip()

    def draw_how_to_play(self):
        self.screen.blit(self.images["how_image"], (0, 0))
        instructions = [
            ("Instruções do jogo:", (255, 0, 0)),
            ("No menu, você pode usar o mouse, click para selecionar, scroll up/down pra aumentar diminuir volume",
             (255, 255, 255)),
            ("Utilize as setas ou o WASD do teclado para mover a cobra.", (255, 255, 255)),
            ("Colete frutas para ganhar pontos e crescer.", (255, 255, 255)),
            ("Cada fruta aumenta o tamanho de forma diferente.", (255, 255, 255)),
            ("Colidir com inimigos diminui o seu tamanho.", (255, 255, 255)),
            ("Se colidir com o corpo da cobra, você perde!!", (255, 255, 255)),
            ("Itens especiais podem ajudar ou atrapalhar você.", (255, 255, 255)),
            ("Ao coletar uma certa quantidade de comida, um boss será invocado.", (255, 255, 255)),
            ("Pressione ESC para voltar ao menu", (255, 0, 0)),
        ]
        y = 100
        screen_width = self.screen.get_width()
        for instruction, color in instructions:
            text_surface = self.font_small.render(instruction, True, color)
            text_rect = text_surface.get_rect(center=(screen_width // 2, y))
            self.screen.blit(text_surface, text_rect)
            y += 50
        pygame.display.flip()

    def draw_score(self):
        self.screen.blit(self.images["score_background"], (0, 0))

        y_offset = 100
        for i, (name, score) in enumerate(scores[:10]):
            self.draw_text(f"{name} - {score:.2f}", 40, (255, 255, 255), (100, y_offset))
            y_offset += 50

        self.draw_text("Digite seu nome:", 50, (255, 255, 255), (100, 650))
        self.draw_text(self.snake.name, 50, (255, 255, 255), (WIDTH // 4 + 135, 650))

        self.draw_text(f"Score: {self.score}", 50, (255, 255, 255), (WIDTH // 4, HEIGHT // 2 + 300))
        pygame.display.flip()

    @staticmethod
    def rotate_image(image, direction):
        angles = {
            (0, 1): 0,
            (0, -1): 180,
            (1, 0): 90,
            (-1, 0): -90,
        }
        return pygame.transform.rotate(image, angles[direction])

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if self.state == MENU:
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.selected_menu_option = (self.selected_menu_option + 1) % 5
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.selected_menu_option = (self.selected_menu_option - 1) % 5
                    elif event.key == pygame.K_RETURN:
                        if self.selected_menu_option == 0:
                            self.reset()
                            self.state = JOGO
                            self.stop_all_sounds()
                            self.play_sound("game_sound", loop=True)
                        elif self.selected_menu_option == 1:
                            self.state = SCORE
                            self.stop_all_sounds()
                            self.play_sound("score_sound", loop=True)
                        elif self.selected_menu_option == 2:
                            self.state = HOW_TO_PLAY
                        elif self.selected_menu_option == 4:
                            pygame.quit()
                            sys.exit()
                    elif self.selected_menu_option == 3:
                        if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                            self.set_volume(min(self.volume + VOLUME_INCREMENT, MAX_VOLUME))
                        elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                            self.set_volume(max(self.volume - VOLUME_INCREMENT, MIN_VOLUME))
                        elif event.key == pygame.K_m:
                            self.toggle_mute()
                elif self.state == JOGO:
                    current_time = time.time()
                    if current_time - self.last_direction_change_time > 0.05:
                        if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                            self.snake.change_direction((-1, 0))
                            self.last_direction_change_time = current_time
                        elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                            self.snake.change_direction((1, 0))
                            self.last_direction_change_time = current_time
                        elif event.key == pygame.K_UP or event.key == pygame.K_w:
                            self.snake.change_direction((0, -1))
                            self.last_direction_change_time = current_time
                        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            self.snake.change_direction((0, 1))
                            self.last_direction_change_time = current_time
                        elif event.key == pygame.K_ESCAPE:
                            self.state = MENU
                            self.stop_all_sounds()
                            self.play_sound("menu_sound", loop=True)
                elif self.state == HOW_TO_PLAY:
                    if event.key == pygame.K_ESCAPE:
                        self.state = MENU
                elif self.state == SCORE:
                    if event.key == pygame.K_RETURN:
                        salvar_score(self.snake.name, self.score)
                        scores.append((self.snake.name, self.score))
                        scores.sort(key=lambda x: x[1], reverse=True)
                        self.snake.name = " "
                        self.state = MENU
                        self.stop_all_sounds()
                        self.play_sound("menu_sound", loop=True)
                    elif event.key == pygame.K_BACKSPACE:
                        self.snake.name = self.snake.name[:-1]
                    elif is_valid_character(event.unicode):
                        self.snake.name += event.unicode
                    elif event.key == pygame.K_ESCAPE:
                        self.state = MENU
                        self.stop_all_sounds()
                        self.play_sound("menu_sound", loop=True)
            elif event.type == pygame.MOUSEMOTION:
                if self.state == MENU:
                    x, y = event.pos
                    if 200 <= x <= 400:
                        if 120 <= y <= 170: 
                            self.selected_menu_option = 0
                        elif 255 <= y <= 305:   
                            self.selected_menu_option = 1
                        elif 395 <= y <= 433:   
                            self.selected_menu_option = 2
                        elif 518 <= y <= 568:   
                            self.selected_menu_option = 3
                        elif 650 <= y <= 700:   
                            self.selected_menu_option = 4
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == MENU:
                    x, y = event.pos
                    if 200 <= x <= 400:
                        if 120 <= y <= 170:
                            self.selected_menu_option = 0
                        elif 255 <= y <= 305:
                            self.selected_menu_option = 1
                        elif 395 <= y <= 433:
                            self.selected_menu_option = 2
                        elif 518 <= y <= 568:
                            self.selected_menu_option = 3
                        elif 650 <= y <= 700:
                            self.selected_menu_option = 4

                        if event.button == 1:
                            if self.selected_menu_option == 0:
                                self.reset()
                                self.state = JOGO
                                self.stop_all_sounds()
                                self.play_sound("game_sound", loop=True)
                            elif self.selected_menu_option == 1:
                                self.state = SCORE
                                self.stop_all_sounds()
                                self.play_sound("score_sound", loop=True)
                            elif self.selected_menu_option == 2:
                                self.state = HOW_TO_PLAY
                            elif self.selected_menu_option == 3:
                                self.toggle_mute()
                                self.set_volume(0.0 if self.is_muted else self.volume)
                            elif self.selected_menu_option == 4:
                                pygame.quit()
                                sys.exit()
                        elif event.button == 4:
                            self.set_volume(min(self.volume + 0.1, 1.0))
                        elif event.button == 5:
                            self.set_volume(max(self.volume - 0.1, 0.0))

    def update_game_logic(self, delta_time):
        global SNAKE_UPDATE_INTERVAL, ENEMY_UPDATE_INTERVAL, BOSS_UPDATE_INTERVAL

        self.elapsed_time += delta_time

        self.snake_timer += delta_time
        self.enemy_timer += delta_time
        self.boss_timer += delta_time

        if self.snake_timer >= SNAKE_UPDATE_INTERVAL:
            self.snake_timer -= SNAKE_UPDATE_INTERVAL
            new_head = self.snake.move()

            if self.snake.check_collision():
                self.state = SCORE
                self.stop_all_sounds()
                self.sounds["game_over"].play()
                self.play_sound("score_sound", loop=True)
                return

            # check food collision
            for food in self.food:
                if new_head == food["pos"]:
                    self.snake.grow_snake(food["bonus"] + 1)
                    self.sounds["eat"].play()
                    self.food = self.generate_food()
                    self.food_collected += 1
                    if self.food_collected % 10 == 0 and self.food_collected != 0:
                        self.level += 1
                        SNAKE_UPDATE_INTERVAL = max(0.1, SNAKE_UPDATE_INTERVAL - 0.005)
                        ENEMY_UPDATE_INTERVAL = max(0.1, ENEMY_UPDATE_INTERVAL - 0.005)
                        BOSS_UPDATE_INTERVAL = max(0.1, BOSS_UPDATE_INTERVAL - 0.005)
                        self.sounds["level_up"].play()
                    if self.food_collected % 15 == 0 and self.food_collected != 0:
                        self.bosses.append(self.generate_boss())
                        self.sounds["boss"].play()

            self.score = len(self.snake.body) * self.level - (self.elapsed_time // 2)

            # check item collision
            for item in self.items:
                if new_head == item["pos"]:
                    self.sounds["item"].play()
                    if item["type"] == 0:
                        self.snake.grow_snake(5)
                    elif item["type"] == 1:
                        self.snake.body = self.snake.body[:-5] if len(self.snake.body) > 5 else [self.snake.body[0]]
                        if len(self.snake.body) == 1:
                            self.state = SCORE
                            self.stop_all_sounds()
                            self.play_sound("game_over")
                            self.play_sound("score_sound", loop=True)
                    elif item["type"] == 2:
                        self.enemies = self.generate_enemies()
                        self.sounds["enemy"].play()
                    elif item["type"] == 3:
                        self.enemies.extend(self.generate_enemies())
                    elif item["type"] == 4:
                        self.bosses.append(self.generate_boss())
                        self.sounds["boss"].play()
                    self.items = self.generate_item()

        # move enemies
        if self.enemy_timer >= SNAKE_UPDATE_INTERVAL:
            self.enemy_timer -= SNAKE_UPDATE_INTERVAL
            for enemy in self.enemies:
                new_enemy_pos = (enemy["pos"][0] + enemy["dir"][0] * BLOCK_SIZE,
                                 enemy["pos"][1] + enemy["dir"][1] * BLOCK_SIZE)

                if new_enemy_pos[0] < 0:
                    new_enemy_pos = (WIDTH - BLOCK_SIZE, new_enemy_pos[1])
                elif new_enemy_pos[0] >= WIDTH:
                    new_enemy_pos = (0, new_enemy_pos[1])
                elif new_enemy_pos[1] < 0:
                    new_enemy_pos = (new_enemy_pos[0], HEIGHT - BLOCK_SIZE)
                elif new_enemy_pos[1] >= HEIGHT:
                    new_enemy_pos = (new_enemy_pos[0], 0)

                if new_enemy_pos in self.snake.body:
                    self.snake.body.pop()
                    self.sounds["enemy_death"].play()
                    if len(self.snake.body) == 0:
                        self.state = SCORE
                        self.stop_all_sounds()
                        self.play_sound("game_over")
                        self.play_sound("score_sound", loop=True)
                    else:
                        self.enemies.remove(enemy)
                else:
                    enemy["pos"] = new_enemy_pos
            if not self.enemies:
                self.enemies = self.generate_enemies()

        # move boss
        if self.boss_timer >= BOSS_UPDATE_INTERVAL:
            self.boss_timer -= BOSS_UPDATE_INTERVAL
            for boss in self.bosses:
                boss = self.move_boss(boss, self.snake.head)
                boss_rect = pygame.Rect(boss["pos"], (boss["size"], boss["size"]))
                snake_rects = [pygame.Rect(pos, (BLOCK_SIZE, BLOCK_SIZE)) for pos in self.snake.body]
                if any(boss_rect.colliderect(snake_rect) for snake_rect in snake_rects):
                    self.snake.body = self.snake.body[:-10]
                    self.sounds["boss_death"].play()
                    if len(self.snake.body) <= 1:
                        self.state = SCORE
                        self.stop_all_sounds()
                        self.play_sound("game_over")
                        self.play_sound("score_sound", loop=True)
                    else:
                        self.bosses.remove(boss)

    def run(self):
        self.play_sound("menu_sound", loop=True)
        while True:
            delta_time = self.clock.tick(60) / 1000
            self.handle_events()
            if self.state == MENU:
                self.draw_menu()
            elif self.state == JOGO:
                self.update_game_logic(delta_time)
                self.draw_game()
            elif self.state == HOW_TO_PLAY:
                self.draw_how_to_play()
            elif self.state == SCORE:
                self.draw_score()


if __name__ == "__main__":
    game = Game()
    game.run()
