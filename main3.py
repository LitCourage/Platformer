import pygame as pg
import random
import pytmx
import json

pg.init()
clock = pg.time.Clock()

SCREEN_WIDTH = 900      #2560
SCREEN_HEIGHT = 600     #1380
FPS = 60
TILE_SCALE = 3
TILE_SIZE = 16
ITEM_SIZE = 56
SLOT_SIZE = 64
SLOT_PADDING = 4
CAMERA_SPEED = 4
HOTBAR_SLOT_ACTIVE = pg.image.load('Assets/interface/hotbar_slot_active.png')
HOTBAR_SLOT_INACTIVE = pg.image.load('Assets/interface/hotbar_slot_inactive.png')
INVALID_TEXTURE = pg.image.load('Assets/interface/invalid_texture.png') 
PLAYER_START_POS = (13*TILE_SIZE*TILE_SCALE, 78*TILE_SIZE*TILE_SCALE)

font = pg.font.Font(None, 36)

def debug(text):
    i, r = render_text(text, 'red')
    Globals.debug_image = i

def draw_rect(rect):
    pg.draw.rect(Globals.screen, 'red', (rect.x-Globals.camera_x, rect.y-Globals.camera_y, rect.width, rect.height))

def render_text(text, color='black', font=font):
    text_image = font.render(str(text), True, color)
    text_rect = text_image.get_rect()
    return text_image, text_rect

def transform_pos(pos):
    return (pos[0]*TILE_SCALE*TILE_SIZE, pos[1]*TILE_SCALE*TILE_SIZE)

class Timer:
    def __init__(self, delay):
        self.timer = pg.time.get_ticks()
        self.delay = delay
    
    def check(self):
        if pg.time.get_ticks() - self.timer >= self.delay:
            self.update()
            return True
    
    def update(self):
        self.timer = pg.time.get_ticks()

    def new_delay(self, delay):
        self.delay = delay

class Sound:
    def __init__(self, path):
        self.sound = pg.mixer.Sound(path)
    def play(self):
        self.sound.play()

class Blueprint(pg.sprite.Sprite):
    def __init__(self):
        super(Blueprint, self).__init__()
        self.set_rect_and_image(pg.Surface((48, 48)))

        # params
        self.gravity = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.current_animation = []
        self.current_image = 0
        self.animation_timer = Timer(100)
    def load_image(self, path: str, size: tuple | list=None):
        if size is not None:
            return self.resize_image(pg.image.load(path), size)
        else:
            return pg.image.load(path)
    def resize_image(self, image, size: tuple | list):
        return pg.transform.scale(image, size)
    def rotate_image(self, image, rotation):
        return pg.transform.rotate(image, rotation)
    def flip_image(self, image):
        return pg.transform.flip(image, True, False)
    def flip_image_by_side(self, image, new_side: str='right', side: str='right'):
        return self.flip_image(image) if new_side != side else image
    def rotate_image_by_side(self, image, new_side: str='right', side: str='right'):
        if side == 'right':
            rotation = 0
        elif side == 'left':
            rotation = 180
        elif side == 'up':
            rotation = 90
        elif side == 'down':
            rotation = -90
        if new_side == 'right':
            return pg.transform.rotate(image, rotation)
        elif new_side == 'left':
            return pg.transform.rotate(image, rotation+180)
        elif new_side == 'up':
            return pg.transform.rotate(image, rotation-90)
        elif new_side == 'down':
            return pg.transform.rotate(image, rotation+90)
    def set_rect_and_image(self, image, pos=(0, 0)):
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)
    def set_rect_by_image(self, image):
        self.rect = image.get_rect(center=self.rect.center)
    def add_velocity(self, velocity: tuple | list):
        self.velocity_x += velocity[0]
        self.velocity_y += velocity[1]
    def set_velocity(self, velocity: tuple | list):
        self.velocity_x = velocity[0]
        self.velocity_y = velocity[1]
    def add_pos(self, pos: tuple | list):
        self.rect.x += pos[0]
        self.rect.y += pos[1]
    def set_pos(self, pos: tuple | list):
        self.rect.x = pos[0]
        self.rect.y += pos[1]
    def move(self):
        if self.velocity_y < 20:
            self.velocity_y += self.gravity
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
    def check_collision(self, rect: pg.rect.Rect):
        return self.rect.colliderect(rect)
    def check_group_collision(self, group: tuple | list):
        hits = []
        for obj in group:
            if self.check_collision(obj.rect):
                if obj is not None:
                    hits.append(obj)
        return hits
    def get_side_hits(self, rect: pg.rect.Rect):
        hits = []
        if self.check_collision(rect):
            if rect.collidepoint(self.rect.midbottom):
                hits.append('bottom')
            if rect.collidepoint(self.rect.midtop):
                hits.append('top')
            if rect.collidepoint(self.rect.midleft):
                hits.append('left')
            if rect.collidepoint(self.rect.midright):
                hits.append('right')
        return hits
    def handle_collision(self, rect: pg.rect.Rect):
        hits = self.get_side_hits(rect)
        if self.velocity_y > 0 and 'bottom' in hits:
            self.rect.bottom = rect.top
            self.velocity_y = 0
        if self.velocity_y < 0 and 'top' in hits:
            self.rect.top = rect.bottom
            self.velocity_y = 0
        if self.velocity_x < 0 and 'left' in hits:
            self.rect.left = rect.right
            self.velocity_x = 0
        if self.velocity_x > 0 and 'right' in hits:
            self.rect.right = rect.left
            self.velocity_x = 0
    def handle_group_collision(self, group: tuple | list):
        for obj in group:
            self.handle_collision(obj.rect)
    def add_animation(self, spritesheet, num_images: int, size: tuple | list=TILE_SIZE, scale: int=TILE_SCALE, side: str='right', new_side: str='right'):
        spritesheet = spritesheet

        animation = []

        for i in range(num_images):
            x = i * size[0]
            rect = pg.Rect(x, 0, size[0], size[1])
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (size[0] * scale, size[1] * scale))
            image = self.rotate_image_by_side(image, side, new_side)
            animation.append(image)

        return animation
    def set_animation(self, animation):
        self.current_animation = animation
        self.current_image = 0
    def handle_animation(self):
        if self.animation_timer.check():
            self.image = self.current_animation[self.current_image]
            self.current_image += 1
            if self.current_image >= len(self.current_animation):
                self.current_image = 0
    def add_sprite(self, sprite, group: pg.sprite.Group=None):
        if group is None:
            Globals.bp_sprites.add(sprite)
        else:
            group.add(sprite)
        return sprite
    def kill(self, group: pg.sprite.Group=None):
        if group is None:
            Globals.bp_sprites.remove(self)
        else:
            group.remove(self)
    def draw(self):
        Globals.screen.blit(self.image, self.rect.move(-Globals.camera_x, -Globals.camera_y))

class Platform(pg.sprite.Sprite):
    def __init__(self, image, x, y):
        super(Platform, self).__init__()

        self.image = pg.transform.scale(image, (Globals.tmx_map.tilewidth*TILE_SCALE, Globals.tmx_map.tileheight*TILE_SCALE))
        self.rect = self.image.get_rect()
        self.rect.x = x*TILE_SCALE
        self.rect.y = y*TILE_SCALE

class PlatformMovable(pg.sprite.Sprite):
    def __init__(self, image, start_pos, end_pos, velocity, _type):
        super(PlatformMovable, self).__init__()

        self.image = pg.transform.scale(image, (Globals.tmx_map.tilewidth*TILE_SCALE, Globals.tmx_map.tileheight*TILE_SCALE))
        self.rect = self.image.get_rect(topleft=(start_pos[0]*TILE_SCALE, start_pos[1]*TILE_SCALE))

        self.type = _type

        if self.type == 'vertical':
            self.start_pos = start_pos[1]*TILE_SCALE
        else:
            self.start_pos = start_pos[0]*TILE_SCALE
        self.end_pos = end_pos*TILE_SCALE*Globals.tmx_map.tilewidth
        self.direction = 'up' if self.start_pos > self.end_pos else 'down'
        self.velocity = -velocity if self.direction == 'up' else velocity

    def update(self):
        if self.type == 'vertical':
            self.rect.y += self.velocity
            if self.direction == 'up' and (self.rect.y >= self.start_pos or self.rect.y <= self.end_pos):
                self.velocity *= -1
            elif self.direction == 'down' and (self.rect.y <= self.start_pos or self.rect.y >= self.end_pos):
                self.velocity *= -1
        else:
            self.rect.x += self.velocity
            if self.direction == 'up' and (self.rect.x >= self.start_pos or self.rect.x <= self.end_pos):
                self.velocity *= -1
            elif self.direction == 'down' and (self.rect.x <= self.start_pos or self.rect.x >= self.end_pos):
                self.velocity *= -1

class Checkpoint(pg.sprite.Sprite):
    def __init__(self, image, pos):
        super(Checkpoint, self).__init__()

        self.image = pg.transform.scale(image, (TILE_SIZE*TILE_SCALE, TILE_SIZE*TILE_SCALE))
        self.rect = self.image.get_rect(topleft=(pos[0]*TILE_SCALE*TILE_SIZE, pos[1]*TILE_SCALE*TILE_SIZE))

    def update(self):
        if self.rect.colliderect(Globals.player.rect):
            Globals.player.spawn_point = self.rect.center
            Globals.checkpoints.remove(self)

class Entity(pg.sprite.Sprite):
    def __init__(self):
        super(Entity, self).__init__()

        self.image = pg.Surface((100, 100))
        self.image.fill('red')

        self.rect = self.image.get_rect()
        self.rect.center = (200, 100)  # Начальное положение персонажа

        # характеристики
        self.hp = 16
        self.max_hp = self.hp
        self.walkspeed = 6
        self.jump_velocity = -25
        self.knockback = 0
        self.is_dead = False

        self.damage_timer = pg.time.get_ticks()
        self.damage_interval = 500
        self.damage_sound = pg.mixer.Sound('Assets/sounds/damage.wav')
        self.heal_timer = pg.time.get_ticks()
        self.heal_interval = 500

        # Начальная скорость и гравитация
        self.velocity_x = 0
        self.velocity_y = 0
        self.gravity = 1.75
        self.is_jumping = False

        self.side = 'right'

        self.timer = pg.time.get_ticks()
        self.interval = 100

        self.inventory = Inventory()

    def update(self):
        self.move()

        if self.hp <= 0:
            self.death()

        self.map_collision()

    def jump(self):
        self.velocity_y = -25
        self.is_jumping = True

    def get_damage(self, dmg=1, interval=-1, knockback=(0, 0)):
        if pg.time.get_ticks() - self.damage_timer > (interval if interval != -1 else self.damage_interval) and self.hp > 0:
            self.hp -= dmg
            self.knockback = knockback[0]
            self.velocity_y += knockback[1]
            self.damage_timer = pg.time.get_ticks()
            self.damage_sound.play()

    def heal(self, val=1, interval=-1):
        if pg.time.get_ticks() - self.heal_timer > (interval if interval != -1 else self.heal_interval):
            self.hp += val
            self.heal_timer = pg.time.get_ticks()
            if self.hp > self.max_hp:
                self.hp = self.max_hp
    
    def drop_loot(self, items):
        for item in items:
            item = Item(item, self.rect.center)
            item.drop(self.rect.center)
            Globals.items.add(item)

    def map_collision(self, keys=None):
        for platform in Globals.platforms:
            if self.rect.colliderect(platform.rect):
                if platform.type == 'block' or platform.type == 'vertical' or platform.type == 'horizontal':
                    if self.velocity_y > 0 and platform.rect.collidepoint(self.rect.midbottom):
                        self.rect.bottom = platform.rect.top
                        self.velocity_y = 0
                        self.is_jumping = False
                        if keys and keys[pg.K_SPACE] and not self.is_jumping:
                            self.jump()
                        if platform.type == 'horizontal':
                            self.rect.x += platform.velocity
                        elif platform.type == 'vertical':
                            self.rect.y += platform.velocity
                    if self.velocity_y < 0 and platform.rect.collidepoint(self.rect.midtop):
                        self.rect.top = platform.rect.bottom
                        self.velocity_y = 0
                    if self.velocity_x < 0 and platform.rect.collidepoint(self.rect.midleft):
                        self.rect.left = platform.rect.right
                        self.velocity_x = 0
                    if self.velocity_x > 0 and platform.rect.collidepoint(self.rect.midright):
                        self.rect.right = platform.rect.left
                        self.velocity_x = 0

                elif platform.type == 'spike':
                    self.get_damage(1, 750, (0, -15))
    
    def handle_animation(self):
        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.current_animation):
                self.current_image = 0
            self.image = self.current_animation[self.current_image]
            self.timer = pg.time.get_ticks()
    
    def draw_healthbar(self):
        pg.draw.rect(Globals.screen, pg.Color('black'), (self.rect.centerx - 25 - Globals.camera_x, self.rect.top - 25 - Globals.camera_y, 50, 10), 2)
        pg.draw.rect(Globals.screen, pg.Color('red'), (self.rect.centerx - 22 - Globals.camera_x, self.rect.top - 22 - Globals.camera_y, self.hp/self.max_hp*44, 4))

    def move(self):
        if self.velocity_y <= 50:
            self.velocity_y += self.gravity
        self.rect.y += self.velocity_y
        self.rect.x += self.velocity_x
        if self.velocity_y-self.gravity != 0:
            self.rect.x += self.knockback
        else:
            self.knockback = 0

class Player(Entity):
    def __init__(self):
        super(Player, self).__init__()
        self.load_animations()
        self.image = self.idle_animation_right[0]

        self.rect = self.image.get_rect()
        self.spawn_point = PLAYER_START_POS
        self.rect.center = self.spawn_point  # Начальное положение персонажа

        self.hand_pos_right = -12
        self.hand_pos_centery = 25

        self.current_animation = self.idle_animation_right
        self.current_image = 0

        self.money = 0
        self.money_image = pg.transform.scale(pg.image.load('Assets/moneds/Coin.png'), (24, 24))
        self.money_rect = self.money_image.get_rect(center=(SCREEN_WIDTH-48, 24))
        self.money_text_image, self.money_text_rect = render_text(self.money)
        self.money_text_rect.center = (SCREEN_WIDTH-24, 24)

        self.add_hotbar_slots()

    def add_money(self, amount=1):
        self.money += 1
        self.money_text_image, self.money_text_rect = render_text(self.money)
        self.money_text_rect.center = (SCREEN_WIDTH-24, 24)

    def draw_money(self, screen):
        screen.blit(self.money_image, self.money_rect)
        screen.blit(self.money_text_image, self.money_text_rect)

    def drop_item_hotbar(self):
        item = self.hotbar_slots[self.active_slot].item
        if item is None:
            return
        self.hotbar_slots[self.active_slot].item = None
        self.inventory.drop_item(item)

    def add_hotbar_slots(self):
        self.hotbar_slots = []
        self.active_slot = 0
        self.active_item = None

        cursor = [SCREEN_WIDTH/2 - SLOT_SIZE*4.5, SCREEN_HEIGHT - SLOT_SIZE]

        slot_num = 0

        for slot in self.inventory.slots:
            if slot.type == 'hotbar':
                slot.hotbar_rect = pg.rect.Rect((cursor[0], cursor[1], SLOT_SIZE, SLOT_SIZE))
                slot.num = slot_num
                slot_num += 1
                self.hotbar_slots.append(slot)
                cursor[0] += SLOT_SIZE

        self.active_item = self.hotbar_slots[self.active_slot].item
        self.last_item = self.active_item

    def draw_hotbar(self, screen):
        cursor = [SCREEN_WIDTH/2 - SLOT_SIZE*4.5, SCREEN_HEIGHT - SLOT_SIZE]

        for slot in self.hotbar_slots:
            if self.active_slot == slot.num:
                screen.blit(HOTBAR_SLOT_ACTIVE, slot.hotbar_rect)
            else:
                screen.blit(HOTBAR_SLOT_INACTIVE, slot.hotbar_rect)

            if slot.item is not None:
                screen.blit(slot.item.icon, (cursor[0]+SLOT_PADDING, cursor[1]+SLOT_PADDING, SLOT_SIZE, SLOT_SIZE))
            cursor[0] += SLOT_SIZE

    def update_hotbar(self):
        mouse_keys = pg.mouse.get_pressed()
        mouse_pos = pg.mouse.get_pos()
        keys = pg.key.get_pressed()

        for slot in self.hotbar_slots:
            if keys[pg.K_1]:
                self.active_slot = 0
            elif keys[pg.K_2]:
                self.active_slot = 1
            elif keys[pg.K_3]:
                self.active_slot = 2
            elif keys[pg.K_4]:
                self.active_slot = 3
            elif keys[pg.K_5]:
                self.active_slot = 4
            elif keys[pg.K_6]:
                self.active_slot = 5
            elif keys[pg.K_7]:
                self.active_slot = 6
            elif keys[pg.K_8]:
                self.active_slot = 7
            elif keys[pg.K_9]:
                self.active_slot = 8
            elif keys[pg.K_0]:
                self.active_slot = 9

        self.last_item = self.active_item
        self.active_item = self.hotbar_slots[self.active_slot].item

    def update(self, platforms, items):
        keys = pg.key.get_pressed()

        if not self.is_jumping:
            if self.current_image >= len(self.jump_animation_right)-1:
                self.current_animation = self.idle_animation_right if self.side == 'right' else self.idle_animation_left
            if keys[pg.K_a]:
                if self.current_animation != self.move_animation_left:
                    self.side = 'left'
                    self.current_animation = self.move_animation_left
                    self.current_image = 0
                    self.image = self.current_animation[self.current_image]
                    self.timer = pg.time.get_ticks()
                self.velocity_x = -self.walkspeed
            elif keys[pg.K_d]:
                if self.current_animation != self.move_animation_right:
                    self.side = 'right'
                    self.current_animation = self.move_animation_right
                    self.current_image = 0
                    self.image = self.current_animation[self.current_image]
                    self.timer = pg.time.get_ticks()
                self.velocity_x = self.walkspeed
            else:
                if self.current_animation == self.move_animation_right:
                    self.side = 'right'
                    self.current_animation = self.idle_animation_right
                    self.current_image = 0
                    self.image = self.current_animation[self.current_image]
                    self.timer = pg.time.get_ticks()
                elif self.current_animation == self.move_animation_left:
                    self.side = 'left'
                    self.current_animation = self.idle_animation_left
                    self.current_image = 0
                    self.image = self.current_animation[self.current_image]
                    self.timer = pg.time.get_ticks()
                self.velocity_x = 0
        else:
            if self.current_animation != self.jump_animation_right and self.side == 'right':
                self.current_animation = self.jump_animation_right
                self.current_image = 0
            elif self.current_animation != self.jump_animation_left and self.side == 'left':
                self.current_animation = self.jump_animation_left
                self.current_image = 0
            if keys[pg.K_a]:
                self.side = 'left'
                self.current_animation = self.jump_animation_left
                self.velocity_x = -self.walkspeed
            elif keys[pg.K_d]:
                self.side = 'right'
                self.current_animation = self.jump_animation_right
                self.velocity_x = self.walkspeed
            else:
                self.velocity_x = 0

        self.move()

        self.map_collision(keys)

        self.items_collision()

        self.handle_animation()

    def items_collision(self):
        for slot in self.inventory.slots:
                if slot.item is None:
                    break
        else:
            return
        for item in Globals.items:
            if self.rect.colliderect(item.rect):
                self.inventory.pick_up_item(item)
    
    def load_animations(self):
        tile_scale = 4

        self.idle_animation_right = []

        num_images = 4
        tile_size = 19

        for i in range(1, num_images+1):
            x = i * tile_size
            y = 0
            image = pg.image.load(f'Assets/01 - Hobbit/pngs/Hobbit - Idle{i}.png')
            image = pg.transform.scale(image, (tile_size * TILE_SCALE * 1.25, tile_size * TILE_SCALE * 1.25))
            self.idle_animation_right.append(image)

        self.idle_animation_left = [pg.transform.flip(image, True, False) for image in self.idle_animation_right]

        self.move_animation_right = []

        num_images = 10
        tile_size = 19

        for i in range(1, num_images+1):
            x = i * tile_size
            y = 0
            image = pg.image.load(f'Assets/01 - Hobbit/pngs/Hobbit - run{i}.png')
            image = pg.transform.scale(image, (tile_size * TILE_SCALE * 1.25, tile_size * TILE_SCALE * 1.25))
            self.move_animation_right.append(image)
        
        self.move_animation_left = [pg.transform.flip(image, True, False) for image in self.move_animation_right]

        self.jump_animation_right = []

        num_images = 10
        tile_size = 19

        for i in range(1, num_images+1):
            x = i * tile_size
            y = 0
            image = pg.image.load(f'Assets/01 - Hobbit/pngs/Hobbit - jumpt{i}.png')
            image = pg.transform.scale(image, (tile_size * TILE_SCALE * 1.25, tile_size * TILE_SCALE * 1.25))
            self.jump_animation_right.append(image)

        self.jump_animation_left = [pg.transform.flip(image, True, False) for image in self.jump_animation_right]

class Enemy(Entity):
    def __init__(self, start_pos, final_pos, weapon_class, enemies):
        super(Enemy, self).__init__()

        self.left_edge = start_pos[0]
        self.right_edge = final_pos
        self.walkspeed = 3
        self.loot = []

        self.max_hp = 10
        self.hp = 10

        self.hand_pos_right = -12
        self.hand_pos_centery = 25

        self.current_image = 0

        self.side = 'right' if self.left_edge < self.right_edge else 'left'
        self.distation = abs(abs(self.left_edge) - abs(self.right_edge))
        self.last_pos = self.left_edge

        self.weapon_class = weapon_class

        if self.weapon_class == 'sword':
            self.weapon = Sword(self, enemies, damage=1, knockback=(2, -10))
        elif self.weapon_class == 'bow':
            self.weapon = Bow(self, enemies)

    def patrol(self):
        self.velocity_x = self.walkspeed if self.side == 'right' else -self.walkspeed
        if abs(abs(self.last_pos) - abs(self.rect.x)) >= self.distation:
            self.side = 'right' if self.side == 'left' else 'left'
            self.last_pos = self.rect.x
        self.current_animation = self.move_animation_right if self.side == 'right' else self.move_animation_left

    def update_weapon(self):
        if self.weapon_class == 'sword':
            if self.weapon.rect.colliderect(Globals.player.rect):
                self.weapon.attack()
        elif self.weapon_class == 'bow':
            if Globals.player.rect.colliderect(pg.rect.Rect(self.rect.centerx, self.rect.top, 500 if self.side == 'right' else -500, self.rect.size[1])) and self.weapon.current_image < 3:
                self.velocity_x = 0
                self.current_animation = self.idle_animation_left if self.side == 'left' else self.idle_animation_right
                do = True
            else:
                do = False
            self.weapon.pull(do)

    def handle_death(self):
        if self.current_image == 0:
            if self.side == 'right':
                self.current_animation = self.death_animation_right
            elif self.side == 'left':
                self.current_animation = self.death_animation_left
            self.rect = self.death_animation_left[0].get_rect(center=self.rect.center)
        elif self.current_animation != self.death_animation_left and self.current_animation != self.death_animation_right:
            self.current_image = 0
            self.velocity_x = 0
            self.damage_interval = 10000
        elif self.current_image == 5:
            if pg.time.get_ticks() - self.timer > self.interval:
                self.is_dead = True
                self.drop_loot(self.loot)

    def update(self):
        pass

class Orc(Enemy):
    def __init__(self, start_pos, final_pos, weapon_class, enemies):
        super(Orc, self).__init__(start_pos, final_pos, weapon_class, enemies)

        self.load_animations()
        self.image = self.idle_animation_right[0]
        self.loot = [Potion(Globals.player, 'heal')]

        self.rect = self.image.get_rect(bottomleft=start_pos)

        self.current_animation = self.idle_animation_right

    def draw(self):
        pass

    def update(self):
        if self.hp > 0:
            self.patrol()
            self.update_weapon()
        else:
            self.handle_death()

        self.move()

        self.map_collision()

        self.handle_animation()

    def load_animations(self):
        tile_width = 20
        tile_height = 32
        tile_scale = 4

        self.idle_animation_right = []

        num_images = 4
        spritesheet = pg.image.load('Assets/enemies/Orc - Rogue/Idle/Idle-Sheet.png')

        for i in range(num_images):
            x = i * tile_width
            y = 0
            rect = pg.Rect(x, y, tile_width, tile_height)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_width * TILE_SCALE, tile_height * TILE_SCALE))
            self.idle_animation_right.append(image)

        self.idle_animation_left = [pg.transform.flip(image, True, False) for image in self.idle_animation_right]

        self.move_animation_right = []

        num_images = 6
        tile_width = 24
        tile_height = 32
        spritesheet = pg.image.load('Assets/enemies/Orc - Rogue/Run/Run-Sheet.png')

        for i in range(num_images):
            x = i * tile_width
            y = 0
            rect = pg.Rect(x, y, tile_width, tile_height)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_width * TILE_SCALE, tile_height * TILE_SCALE))
            self.move_animation_right.append(image)
        self.move_animation_left = [pg.transform.flip(image, True, False) for image in self.move_animation_right]

        self.death_animation_right = []

        num_images = 6
        tile_width = 33
        tile_height = 37
        spritesheet = pg.image.load('Assets/enemies/Orc - Rogue/Death/Death-Sheet.png')

        for i in range(num_images):
            x = i * tile_width
            y = 0
            rect = pg.Rect(x, y, tile_width, tile_height)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_width * TILE_SCALE, tile_height * TILE_SCALE))
            self.death_animation_right.append(image)
        self.death_animation_left = [pg.transform.flip(image, True, False) for image in self.death_animation_right]

class Skeleton(Enemy):
    def __init__(self, start_pos, final_pos, weapon_class, enemies):
        super(Skeleton, self).__init__(start_pos, final_pos, weapon_class, enemies)

        self.walkspeed = 3

        self.load_animations()
        self.image = self.idle_animation_right[0]

        self.rect = self.image.get_rect(bottomleft=start_pos)

        self.current_animation = self.idle_animation_right

    def update(self):
        if self.hp > 0:
            self.patrol()
            self.update_weapon()
        else:
            self.handle_death()

        self.move()

        self.map_collision()

        self.handle_animation()

    def load_animations(self):
        tile_width = 20
        tile_height = 32

        self.idle_animation_right = []

        num_images = 4
        spritesheet = pg.image.load('Assets/enemies/Skeleton - Warrior/Idle/Idle-Sheet.png')

        for i in range(num_images):
            x = i * tile_width
            y = 0
            rect = pg.Rect(x, y, tile_width, tile_height)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_width * TILE_SCALE, tile_height * TILE_SCALE))
            self.idle_animation_right.append(image)

        self.idle_animation_left = [pg.transform.flip(image, True, False) for image in self.idle_animation_right]

        self.move_animation_right = []

        num_images = 6
        tile_width = 23
        tile_height = 32
        spritesheet = pg.image.load('Assets/enemies/Skeleton - Warrior/Run/Run-Sheet.png')

        for i in range(num_images):
            x = i * tile_width
            y = 0
            rect = pg.Rect(x, y, tile_width, tile_height)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_width * TILE_SCALE, tile_height * TILE_SCALE))
            self.move_animation_right.append(image)
        self.move_animation_left = [pg.transform.flip(image, True, False) for image in self.move_animation_right]

        self.death_animation_right = []

        num_images = 6
        tile_width = 36
        tile_height = 46
        spritesheet = pg.image.load('Assets/enemies/Skeleton - Warrior/Death/Death-Sheet.png')

        for i in range(num_images):
            x = i * tile_width
            y = 0
            rect = pg.Rect(x, y, tile_width, tile_height)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_width * TILE_SCALE, tile_height * TILE_SCALE))
            self.death_animation_right.append(image)
        self.death_animation_left = [pg.transform.flip(image, True, False) for image in self.death_animation_right]

class Usable(Blueprint):
    def __init__(self, owner, _type=None, amount=1):
        super(Usable, self).__init__()

        self.owner = owner
        self.side = 'right'
        self.type = _type
        self.stacksize = 1
        self.amount = amount

        if self.type == 'arrow':
            image = self.load_image('Assets/weapons/arrow.png', (56, 16))
            self.icon = self.load_image('Assets/weapons/arrow_icon.png')
            self.set_rect_and_image(image)
            self.stacksize = 16
        else:
            self.image = INVALID_TEXTURE
            self.icon = INVALID_TEXTURE

        # misc
        self.delete = False

    def default(self):
        pass

    def check_side(self):
        self.image = self.flip_image_by_side(self.image, self.owner.side, self.side)
        self.side = self.owner.side
        if self.owner.side == 'left':
            self.rect.bottomright = self.owner.rect.left - self.owner.hand_pos_right, self.owner.rect.centery + self.owner.hand_pos_centery
        elif self.owner.side == 'right':
            self.rect.bottomleft = self.owner.rect.right + self.owner.hand_pos_right, self.owner.rect.centery + self.owner.hand_pos_centery
    
    def check_side_alt(self):
        self.default_image = self.flip_image_by_side(self.default_image, self.owner.side, self.side)
        self.image = self.flip_image_by_side(self.image, self.owner.side, self.side)
        self.side = self.owner.side
        if self.owner.side == 'left':
            self.rect.bottomright = self.owner.rect.left - self.owner.hand_pos_right, self.owner.rect.centery + self.owner.hand_pos_centery
        elif self.owner.side == 'right':
            self.rect.bottomleft = self.owner.rect.right + self.owner.hand_pos_right, self.owner.rect.centery + self.owner.hand_pos_centery

    def update(self):
        self.check_side()
        self.kill()

class Sword(Usable):
    def __init__(self, owner, enemies, damage=4, knockback=(5, -15)):
        super(Sword, self).__init__(owner)

        self.rotation = 0
        self.enemies = enemies
        self.is_attacking = False
        self.type = 'sword'

        self.damage = damage
        self.knockback = knockback

        self.default_image = pg.image.load('Assets/weapons/sword.png')
        self.icon = pg.transform.scale(self.default_image, (ITEM_SIZE, ITEM_SIZE))
        self.default_image = pg.transform.scale(self.default_image, (45, 45))
        self.default_image = pg.transform.rotate(self.default_image, -self.rotation)
        self.image = self.default_image
        self.rect = self.image.get_rect()

        self.check_side_alt()

        self.is_pressed = False

    def default(self):
        self.is_pressed = False
        self.image = self.default_image
        self.is_attacking = False
        self.rotation = 0

    def update(self):
        if isinstance(self.owner, Player):
            mouse_keys = pg.mouse.get_pressed()

            if mouse_keys[0]:
                if not self.is_pressed:
                    self.attack()
                    self.is_pressed = True
            else:
                self.is_pressed = False

        if self.is_attacking:
            self.rotation += 5
            if self.rotation >= 75:
                self.rotation = 0
                self.is_attacking = False
            self.image = pg.transform.rotate(self.default_image, -self.rotation if self.side == 'right' else self.rotation)
            for enemy in self.enemies:
                if self.rect.colliderect(enemy.rect):
                    kx = self.knockback[0] if self.side == 'right' else -self.knockback[0]
                    ky = self.knockback[1]
                    enemy.get_damage(self.damage, knockback=(kx, ky))

        self.check_side_alt()

    def draw(self):
        Globals.screen.blit(self.image, self.rect.move(-Globals.camera_x, -Globals.camera_y))
    
    def attack(self):
        if not self.is_attacking:
            self.rotation = 0
            self.is_attacking = True

class Bow(Usable):
    def __init__(self, owner, enemies):
        super(Bow, self).__init__(owner)
        self.enemies = enemies
        self.type = 'bow'

        self.idle_image = self.load_image('Assets/weapons/Bow/idle.png', (45, 45))
        self.image = self.idle_image
        self.icon = pg.transform.scale(self.idle_image, (ITEM_SIZE, ITEM_SIZE))
        self.pull_images = [self.load_image(f'Assets/weapons/Bow/pull/pull{i+1}.png', (45, 45)) for i in range(3)]
        self.current_image = 0
        self.set_rect_and_image(self.image)

        self.is_pulling = False
        self.pull_timer = Timer(750)
        self.shoot_timer = Timer(750)
        self.power = 10

    def default(self):
        self.power = 10
        self.is_pulling = False
        self.shoot_timer.update()
        self.pull_timer.update()
        self.image = self.idle_image if self.side == 'right' else pg.transform.flip(self.idle_image, True, False)
        self.current_image = 0

    def update(self):
        if isinstance(self.owner, Player):
            mouse_keys = pg.mouse.get_pressed()
            for slot in Globals.player.inventory.slots:
                if slot.item is not None and slot.item.item_type.type == 'arrow':
                    do = True
                    arrow = slot.item.item_type
                    break
            else: 
                do = False
                arrow = None
            self.pull(mouse_keys[0] and do, arrow)
 
        self.check_side()

    def pull(self, do, arrow=None):
        if do:
            if self.shoot_timer.check():
                if not self.is_pulling:
                    self.is_pulling = True
                    self.image = self.pull_images[self.current_image] if self.side == 'right' else pg.transform.flip(self.pull_images[self.current_image], True, False)
                if self.pull_timer.check() and self.current_image < 3:
                    self.power += 10
                    self.current_image += 1
                    if self.current_image < 3:
                        self.image = self.pull_images[self.current_image] if self.side == 'right' else pg.transform.flip(self.pull_images[self.current_image], True, False)
        elif self.is_pulling:
            self.shoot(self.power, self.enemies, arrow)
            self.power = 10

    def shoot(self, power, enemies, arrow):
        Globals.arrows.add(Arrow(self.rect.centerx, self.rect.centery, power, self.side, enemies))
        if arrow is not None:
            arrow.amount -= 1
        self.is_pulling = False
        self.current_image = 0
        self.image = self.idle_image if self.side == 'right' else pg.transform.flip(self.idle_image, True, False)
        self.power = 10
        self.shoot_timer.update()

class Arrow(Blueprint):
    def __init__(self, pos, power, side, enemies):
        super(Arrow, self).__init__()

        self.collision_sound = Sound('Assets/sounds/arrow.wav')

        self.side = side
        self.power = power
        self.rotation = 0
        self.rot_k = 4 if self.side == 'right' else -4

        self.default_image = self.flip_image_by_side(self.load_image('Assets/weapons/arrow.png'), self.side)
        self.default_image = self.resize_image(self.default_image, (56, 14))
        self.set_rect_and_image(self.default_image, pos)

        self.velocity_x = power if self.side == 'right' else -power
        self.velocity_y = -power/20
        self.gravity = 2/power

        self.can_move = True
        self.despawn_timer = Timer(10000)
        self.despawn_delay_default = 50000

        self.enemies = enemies

    def update(self):
        if self.can_move:
            hits = self.check_group_collision(Globals.platforms)
            if hits:
                self.set_rect_by_image(self.image)
                self.can_move = False
                self.collision_sound.play()
                self.despawn_timer.new_delay(self.despawn_delay_default)
                for hit in hits:
                    sides = self.get_side_hits(hit.rect)
                    if sides:
                        if 'top' in sides:
                            self.rect.top = hit.rect.bottom - 10
                        elif 'bottom' in sides:
                            self.rect.bottom = hit.rect.top + 10
                        elif 'left' in sides:
                            self.rect.left = hit.rect.right - 10
                        elif 'right' in sides:
                            self.rect.right = hit.rect.left + 10
                        return
            
            hits = self.check_group_collision(self.enemies)
            for hit in hits:
                kx = 5 if self.side == 'right' else -5
                ky = -15
                hit.get_damage(self.power/6, knockback=(kx, ky), interval=0)
                self.kill(Globals.arrows)

            self.move()

            self.rotation = self.velocity_y * self.rot_k

            self.image = self.rotate_image(self.default_image, -self.rotation)

class Item(pg.sprite.Sprite):
    def __init__(self, item_type, pos, kx=0, ky=0):
        super(Item, self).__init__()

        self.item_type = item_type
        self.update_timer()
        self.pick_up_delay = 750

        try:
            self.icon = self.item_type.icon
        except:
            self.icon = INVALID_TEXTURE

        self.image = pg.transform.scale(self.icon, (42, 42))
        self.rect = self.image.get_rect(center=pos)

        self.velocity_x = kx
        self.velocity_y = ky

        self.gravity = 1

    def update_timer(self):
        self.pick_up_timer = pg.time.get_ticks()

    def drop(self, pos):
        self.update_timer()
        self.add_knockback(pos, random.randint(-5, 5), -10)

    def add_knockback(self, pos, kx, ky):
        self.rect.center = pos
        self.velocity_x = kx
        self.velocity_y = ky

    def update(self):
        for platform in Globals.platforms:
            if self.rect.colliderect(platform.rect):
                if platform.rect.collidepoint(self.rect.midtop):
                    self.velocity_x, self.velocity_y = 0, 0
                    self.rect.top = platform.rect.bottom
                elif platform.rect.collidepoint(self.rect.midbottom):
                    self.velocity_x, self.velocity_y = 0, 0
                    self.rect.bottom = platform.rect.top
                elif platform.rect.collidepoint(self.rect.midleft):
                    self.velocity_x, self.velocity_y = 0, 0
                    self.rect.left = platform.rect.right
                elif platform.rect.collidepoint(self.rect.midright):
                    self.velocity_x, self.velocity_y = 0, 0
                    self.rect.right = platform.rect.left

        if self.velocity_y < 20:
            self.velocity_y += self.gravity

        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y

class Slot:
    def __init__(self, rect, slot_type, item=None):
        self.item = item
        self.rect = rect
        self.type = slot_type

class Interface:
    def __init__(self):
        self.background_image = pg.image.load('Assets/interface/background.png')
        self.rect = self.background_image.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))

        self.is_active = False

        # Параметры интерфейса    
        self.background_padding = 100
        self.border_padding = 46
        self.slot_size = 64
        self.row = 9
        self.slot_padding = 4

        self.slot_inactive_image = pg.image.load('Assets/interface/slot_inactive.png')
        self.slot_active_image = pg.image.load('Assets/interface/slot_active.png')

        self.order = ''
        self.slots = []

        self.picked_item = None
        self.is_pressed = False

    def choose_item(self):
        mouse_pos = pg.mouse.get_pos()
        mouse_keys = pg.mouse.get_pressed()

        for slot in self.slots:
            if mouse_keys[0]:
                if not self.is_pressed:
                    if slot.rect.collidepoint(mouse_pos):
                        item = slot.item
                        slot.item = self.picked_item
                        self.picked_item = item
                        self.is_pressed = True
            else:
                self.is_pressed = False

    def update(self):
        self.choose_item()

    def draw_interface(self):
        Globals.screen.blit(self.background_image, self.rect)
        self.cursor = [self.rect.x + self.border_padding, self.rect.y + self.border_padding]

        mouse_pos = pg.mouse.get_pos()
        mouse_keys = pg.mouse.get_pressed()

        for i in self.order:
            if i == '0':
                self.cursor[0] += self.slot_size + self.slot_padding
            elif i == '1':
                slot_rect = pg.rect.Rect(self.cursor[0], self.cursor[1], self.slot_size, self.slot_size)
                if slot_rect.collidepoint(mouse_pos):
                    Globals.screen.blit(self.slot_active_image, (slot_rect))
                else:
                    Globals.screen.blit(self.slot_inactive_image, (slot_rect))
                self.cursor[0] += self.slot_size + self.slot_padding
            elif i == '2':
                slot_rect = pg.rect.Rect(self.cursor[0], self.cursor[1], self.slot_size, self.slot_size)
                if slot_rect.collidepoint(mouse_pos):
                    Globals.screen.blit(self.slot_active_image, (slot_rect))
                else:
                    Globals.screen.blit(self.slot_inactive_image, (slot_rect))
                self.cursor[0] += self.slot_size + self.slot_padding
            elif i == 'n':
                self.cursor[0] = self.rect.x + self.border_padding
                self.cursor[1] += self.slot_size + self.slot_padding
            elif i == 'h':
                self.cursor[0] = self.rect.x + self.border_padding
                self.cursor[1] += self.slot_size/2 + self.slot_padding
        
        for slot in self.slots:
            if slot.item is not None:
                Globals.screen.blit(slot.item.icon, slot.rect)
                if slot.item.item_type.amount >= 2:
                    i, r = render_text(slot.item.item_type.amount)
                    r.center = slot.rect.bottomright
                    Globals.screen.blit(i, r)


        if self.picked_item is not None:
            self.picked_item.rect.center = mouse_pos
            Globals.screen.blit(self.picked_item.icon, self.picked_item.rect)

    def add_slots(self):
        self.cursor = [self.rect.x + self.border_padding, self.rect.y + self.border_padding]

        for i in self.order:
            if i == '0':
                self.cursor[0] += self.slot_size + self.slot_padding
            elif i == '1':
                self.slots.append(Slot(pg.rect.Rect(self.cursor[0]+self.slot_padding, self.cursor[1]+self.slot_padding, self.slot_size-self.slot_padding, self.slot_size-self.slot_padding), 'inventory'))
                self.cursor[0] += self.slot_size + self.slot_padding
            elif i == '2':
                self.slots.append(Slot(pg.rect.Rect(self.cursor[0]+self.slot_padding, self.cursor[1]+self.slot_padding, self.slot_size-self.slot_padding, self.slot_size-self.slot_padding), 'hotbar'))
                self.cursor[0] += self.slot_size + self.slot_padding
            elif i == 'n':
                self.cursor[0] = self.rect.x + self.border_padding
                self.cursor[1] += self.slot_size + self.slot_padding
            elif i == 'h':
                self.cursor[0] = self.rect.x + self.border_padding
                self.cursor[1] += self.slot_size/2 + self.slot_padding

class Inventory(Interface):
    def __init__(self):
        super(Inventory, self).__init__()

        self.order = '111111111n111111111nnh222222222'

        self.add_slots()

    def pick_up_item(self, item):
        if pg.time.get_ticks() - item.pick_up_timer >= item.pick_up_delay:
            for slot in self.slots:
                if slot.item is not None and slot.type == 'hotbar' and slot.item.item_type.type == item.item_type.type:
                    if slot.item.item_type.amount + item.item_type.amount <= slot.item.item_type.stacksize:
                        slot.item.item_type.amount += item.item_type.amount
                        Globals.items.remove(item)
                        return
                    elif slot.item.item_type.amount + item.item_type.amount > slot.item.item_type.stacksize:
                        item.item_type.amount -= slot.item.item_type.stacksize - slot.item.item_type.amount
                        slot.item.item_type.amount = slot.item.item_type.stacksize
                if slot.type == 'hotbar' and slot.item is None:
                    slot.item = item
                    Globals.items.remove(item)
                    return
            for slot in self.slots:
                if slot.item is not None and slot.type == 'inventory' and slot.item.item_type.type == item.item_type.type:
                    if slot.item.item_type.amount + item.item_type.amount <= slot.item.item_type.stacksize:
                        slot.item.item_type.amount += item.item_type.amount
                        Globals.items.remove(item)
                        return
                    elif slot.item.item_type.amount + item.item_type.amount > slot.item.item_type.stacksize:
                        item.item_type.amount -= slot.item.item_type.stacksize - slot.item.item_type.amount
                        slot.item.item_type.amount = slot.item.item_type.stacksize
                if slot.type == 'inventory' and slot.item is None:
                    slot.item = item
                    Globals.items.remove(item)
                    return

    def drop_item(self, item):
        if item is None:
            return
        item.update_timer()
        kx = 10 if Globals.player.side == 'right' else -10
        ky = -10
        item.add_knockback(Globals.player.rect.center, kx, ky)
        Globals.items.add(item)   

class Chest(pg.sprite.Sprite):
    def __init__(self, pos, container=[]):
        super(Chest, self).__init__()

        self.image = pg.transform.scale(pg.image.load('Assets/Legacy Adventure Pack - RUINS/Assets/Chest_closed.png'), (48, 48))
        self.rect = self.image.get_rect(topleft=(pos[0]*TILE_SCALE, pos[1]*TILE_SCALE))

        self.container = container
        self.is_opened = False

        self.delay = 1000
        self.timer = pg.time.get_ticks()

    def update(self):
        if len(self.container) > 0:
            if not self.is_opened:
                if Globals.player.rect.colliderect(self.rect):
                    self.is_opened = True
                    self.image = pg.transform.scale(pg.image.load('Assets/Legacy Adventure Pack - RUINS/Assets/Chest_opened.png'), (48, 48))
                    self.timer = pg.time.get_ticks()
            else:
                if pg.time.get_ticks() - self.timer >= self.delay:
                    item = Item(self.container.pop(0), self.rect.center)
                    item.drop(self.rect.center)
                    Globals.items.add(item)
                    self.timer = pg.time.get_ticks()

class Coin(pg.sprite.Sprite):
    def __init__(self, pos, _type, amount=1):
        super(Coin, self).__init__()

        self.amount = 1
        self.type = _type

        self.load_animations()
        self.current_image = 0
        self.image = self.animation[0]
        self.rect = self.image.get_rect(topleft=pos)

        self.timer = pg.time.get_ticks()
        self.interval = 100

        self.is_alive = True
        self.is_not_collected = True

        self.despawn_delay = 250
        self.despawn_timer = pg.time.get_ticks()

    def update(self):
        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.animation):
                self.current_image = 0
            self.image = self.animation[self.current_image]
            self.timer = pg.time.get_ticks()

        if self.is_not_collected:
            if Globals.player.rect.colliderect(self.rect):
                self.is_not_collected = False
                self.despawn_timer = pg.time.get_ticks()
        elif not pg.time.get_ticks() - self.despawn_timer >= self.despawn_delay:
            self.rect.y -= 4
        else:
            self.is_alive = False

    def load_animations(self):
        tile_size = 16
        num_images = 5

        spritesheet = pg.image.load('Assets/moneds/MonedaD.png')

        self.animation = []

        for i in range(num_images):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size*TILE_SCALE, tile_size*TILE_SCALE))
            self.animation.append(image)

class Potion(Usable):
    def __init__(self, owner, effect=None):
        super(Potion, self).__init__(owner)
        self.effect = effect
        self.type = 'bottle_'+self.effect

        self.image = pg.transform.scale(pg.image.load('Assets/Legacy Adventure Pack - RUINS/Assets/Bottle.png'), (36, 36))
        self.icon = pg.transform.scale(self.image, (ITEM_SIZE, ITEM_SIZE))
        self.rect = self.image.get_rect()

    def update(self):
        mouse_keys = pg.mouse.get_pressed()
        if mouse_keys[0]:
            self.apply_effect()
            self.delete = True
        self.check_side()

    def apply_effect(self):
        if self.effect == 'heal':
            self.owner.heal(2, 0)

    def draw(self):
        Globals.screen.blit(self.image, self.rect.move(-Globals.camera_x, -Globals.camera_y))

class Dispencer(Blueprint):
    def __init__(self, pos, side):
        super(Dispencer, self).__init__()
        
        self.side = side
        image = self.rotate_image_by_side(self.load_image('Assets/Legacy Adventure Pack - RUINS/Assets/dispencer.png', (TILE_SIZE*TILE_SCALE, TILE_SIZE*TILE_SCALE)), self.side)
        self.set_rect_and_image(image, pos)

        self.shoot_timer = Timer(2000)

    def update(self):
        if self.shoot_timer.check():
            Globals.bp_sprites.add(Fireball(self.rect.center, self.side))

class Fireball(Blueprint):
    def __init__(self, pos, side):
        super(Fireball, self).__init__()
        spritesheet = self.load_image('Assets/weapons/fireball_sheet.png')

        self.side = side

        if side == 'left':
            self.set_velocity((-4, 0))
        elif side == 'right':
            self.set_velocity((4, 0))
        elif side == 'up':
            self.set_velocity((0, -4))
        elif side == 'down':
            self.set_velocity((0, 4))

        self.animation = self.add_animation(spritesheet, 5, (35, 18), scale=1.25, new_side=side)
        self.set_animation(self.animation)

        self.set_rect_and_image(self.animation[0], pos)
        self.rect.center = pos

    def update(self):
        self.handle_animation()
        self.move()

        if self.check_group_collision(Globals.platforms):
            self.kill()

        if self.check_collision(Globals.player.rect):
            Globals.player.get_damage(5, 500, (5 if self.side == 'right' else -5 if self.side == 'left' else 0, -15))
            self.kill()

class Globals:
    # BLUEPRINTS
    bp_sprites = pg.sprite.Group()

    # sprite groups
    enemies = pg.sprite.Group() 
    coins = pg.sprite.Group()
    arrows = pg.sprite.Group()
    items = pg.sprite.Group()
    chests = pg.sprite.Group()

    # params
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    debug_image = None

    player = Player()

    # camera
    camera_x = 0
    camera_y = 0

    screen_rect = pg.rect.Rect((-camera_x, -camera_y, SCREEN_WIDTH, SCREEN_HEIGHT))

    @classmethod
    def load_map(cls):
        cls.platforms = pg.sprite.Group()
        cls.fg_platforms = pg.sprite.Group()
        cls.bg_platforms = pg.sprite.Group()
        cls.checkpoints = pg.sprite.Group()

        cls.tmx_map = pytmx.load_pygame('maps/map.tmx')

        cls.tile_size = cls.tmx_map.tilewidth * TILE_SCALE
        cls.map_pixel_width = cls.tmx_map.width * cls.tile_size
        cls.map_pixel_height = cls.tmx_map.height * cls.tile_size

        for layer in cls.tmx_map:
            if layer.name == 'platforms':
                for x, y, gid in layer:
                    tile = cls.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        platform = Platform(tile, x * cls.tmx_map.tilewidth, y * cls.tmx_map.tileheight)
                        platform.type = 'block'
                        cls.platforms.add(platform)
            elif layer.name == 'foreground':
                for x, y, gid in layer:
                    tile = cls.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        platform = Platform(tile, x * cls.tmx_map.tilewidth, y * cls.tmx_map.tileheight)
                        cls.fg_platforms.add(platform)
            elif layer.name == 'background':
                for x, y, gid in layer:
                    tile = cls.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        platform = Platform(tile, x * cls.tmx_map.tilewidth, y * cls.tmx_map.tileheight)
                        cls.bg_platforms.add(platform)
            elif layer.name == 'spikes':
                for x, y, gid in layer:
                    tile = cls.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        platform = Platform(tile, x * cls.tmx_map.tilewidth, y * cls.tmx_map.tileheight)
                        platform.type = 'spike'
                        cls.platforms.add(platform)
            elif layer.name == 'moneds_D':
                for x, y, gid in layer:
                    tile = cls.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        coin = Coin((x * cls.tmx_map.tilewidth * TILE_SCALE, y * cls.tmx_map.tileheight * TILE_SCALE), 'moned_D')
                        cls.coins.add(coin)
            elif layer.name == 'moving':
                for obj in layer:
                    cls.platforms.add(PlatformMovable(obj.image, (obj.x, obj.y), obj.properties['end_pos'], obj.properties['velocity'], obj.properties['_type']))
            elif layer.name == 'enemies':
                for obj in layer:
                    cls.enemies.add(cls.add_enemy(obj.properties['_type'], (obj.x, obj.y), obj.properties['end_pos'], obj.properties['weapon'], obj.properties['hp'], obj.properties['damage']))
            elif layer.name == 'chests':
                for obj in layer:
                    exec(f'chest = Chest(({obj.x, obj.y}), {obj.properties["container"]})', globals())
                    cls.chests.add(chest)
            elif layer.name == 'dispencers':
                for obj in layer:
                    cls.bp_sprites.add(Dispencer((obj.x*TILE_SCALE, obj.y*TILE_SCALE), obj.properties['side']))
            elif layer.name == 'checkpoints':
                for x, y, gid in layer:
                    tile = cls.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        checkpoint = Checkpoint(tile, (x, y))
                        cls.checkpoints.add(checkpoint)

    @classmethod
    def add_enemy(cls, _type, start_pos, end_pos, weapon='sword', hp=10, damage=1):
        if _type == 'orc':
            enemy = Orc((start_pos[0]*TILE_SCALE, start_pos[1]*TILE_SCALE), end_pos*cls.tile_size, weapon, [cls.player])
        elif _type == 'skeleton':
            enemy = Skeleton((start_pos[0]*TILE_SCALE, start_pos[1]*TILE_SCALE), end_pos*cls.tile_size, weapon, [cls.player])
        enemy.hp = hp
        enemy.max_hp = hp
        enemy.weapon.damage = damage
        return enemy

class Bow(Usable):
    def __init__(self, owner, enemies):
        super(Bow, self).__init__(owner)
        self.enemies = enemies
        self.type = 'bow'

        self.idle_image = self.load_image('Assets/weapons/Bow/idle.png', (45, 45))
        self.image = self.idle_image
        self.icon = self.resize_image(self.idle_image, (ITEM_SIZE, ITEM_SIZE))
        self.pull_images = [self.resize_image(self.load_image(f'Assets/weapons/Bow/pull/pull{i+1}.png'), (45, 45)) for i in range(3)]
        self.current_image = 0
        self.set_rect_and_image(self.image)

        self.is_pulling = False
        self.shoot_timer = Timer(750)
        self.pull_timer = Timer(750)
        self.power = 10

    def default(self):
        self.power = 10
        self.is_pulling = False
        self.shoot_timer.update()
        self.pull_timer.update()
        self.image = self.flip_image_by_side(self.idle_image, self.owner.side, 'right')
        self.current_image = 0

    def update(self):
        if isinstance(self.owner, Player):
            mouse_keys = pg.mouse.get_pressed()
            for slot in Globals.player.inventory.slots:
                if slot.item is not None and slot.item.item_type.type == 'arrow':
                    do = True
                    arrow = slot.item.item_type
                    break
            else:
                do = False
                arrow = None
            self.pull(mouse_keys[0] and do, arrow)
        self.check_side()

    def pull(self, do, arrow=None):
        if do:
            if self.shoot_timer.check():
                if not self.is_pulling:
                    self.is_pulling = True
                    self.pull_timer.update()
                    self.image = self.flip_image_by_side(self.pull_images[self.current_image], self.side)
                if self.pull_timer.check() and self.current_image < 3:
                    self.power += 10
                    self.current_image += 1
                    if self.current_image < 3:
                        self.image = self.flip_image_by_side(self.pull_images[self.current_image], self.side)
        elif self.is_pulling:
            self.shoot(self.power, self.enemies, arrow)
            self.power = 10

    def shoot(self, power, enemies, arrow):
        self.side = self.owner.side
        self.add_sprite(Arrow((self.rect.centerx, self.rect.centery), power, self.side, enemies), Globals.arrows)
        if arrow is not None:
            arrow.amount -= 1
        self.is_pulling = False
        self.current_image = 0
        self.image = self.flip_image_by_side(self.idle_image, self.owner.side)
        self.power = 10
        self.shoot_timer.update()

class Game:
    def __init__(self):
        pg.display.set_caption("Platformer")
        self.setup()

    def setup(self):
        self.mode = 'game'

        self.clock = pg.time.Clock()
        self.is_running = False

        Globals.load_map()

        self.run()

    def run(self):
        self.is_running = True
        while self.is_running:
            self.event()
            self.update()
            self.draw()
            self.clock.tick(60)
        pg.quit()
        quit()

    def event(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.is_running = False
            if event.type == pg.KEYDOWN:
                if self.mode == 'game over':
                    Globals.player.rect.center = Globals.player.spawn_point
                    Globals.player.hp = Globals.player.max_hp // 3
                    self.mode = 'game'
                if event.key == pg.K_e:
                    Globals.player.inventory.is_active = not Globals.player.inventory.is_active
                if event.key == pg.K_m:
                    Globals.load_map()
                if event.key == pg.K_q:
                    Globals.player.drop_item_hotbar()
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 5:
                    Globals.player.active_slot += 1
                    if Globals.player.active_slot > 8:
                        Globals.player.active_slot = 0
                elif event.button == 4:
                    Globals.player.active_slot -= 1
                    if Globals.player.active_slot < 0:
                        Globals.player.active_slot = 8

        keys = pg.key.get_pressed()

        if keys[pg.K_LEFT]:
            Globals.camera_x -= CAMERA_SPEED
        if keys[pg.K_RIGHT]:
            Globals.camera_x += CAMERA_SPEED
        if keys[pg.K_UP]:
            Globals.camera_y -= CAMERA_SPEED
        if keys[pg.K_DOWN]:
            Globals.camera_y += CAMERA_SPEED

    def update(self):
        Globals.player.update(Globals.platforms, Globals.items)
        Globals.player.update_hotbar()

        for platform in Globals.platforms:
            if platform.type == 'vertical' or platform.type == 'horizontal':
                platform.update()
        for checkpoint in Globals.checkpoints:
            checkpoint.update()
        for enemy in Globals.enemies:
            enemy.update()
            enemy.weapon.update()
            if enemy.is_dead:
                Globals.enemies.remove(enemy)
        for arrow in Globals.arrows:
            arrow.update()
        for coin in Globals.coins:
            coin.update()
            if not coin.is_alive:
                Globals.coins.remove(coin)
                Globals.player.add_money(1)
        for chest in Globals.chests:
            chest.update()
        for item in Globals.items:
            item.update()

        for sprite in Globals.bp_sprites:
            sprite.update()

        if Globals.player.inventory.is_active:
            Globals.player.inventory.update()
        else:
            Globals.player.inventory.drop_item(Globals.player.inventory.picked_item)
            Globals.player.inventory.picked_item = None

        current_item = Globals.player.active_item
        if current_item is not None:
            if not Globals.player.inventory.is_active:
                current_item.item_type.update()
            else:
                current_item.item_type.default()
            if Globals.player.last_item is not None:
                if Globals.player.last_item.item_type != current_item.item_type:
                    Globals.player.last_item.item_type.default()
        elif Globals.player.last_item is not None:
            if Globals.player.last_item.item_type != current_item:
                Globals.player.last_item.item_type.default()
        for slot in Globals.player.inventory.slots:
            if slot.item is not None:
                if slot.item.item_type.amount <= 0:
                    slot.item = None
                    continue
                if slot.item.item_type.delete:
                    slot.item = None
                    continue

        Globals.camera_x = Globals.player.rect.centerx - SCREEN_WIDTH/2
        Globals.camera_y = Globals.player.rect.centery - SCREEN_HEIGHT/2
        Globals.camera_x = max(0, min(Globals.camera_x, Globals.map_pixel_width - SCREEN_WIDTH))
        Globals.camera_y = max(0, min(Globals.camera_y, Globals.map_pixel_height - SCREEN_HEIGHT))

        if Globals.player.hp <= 0:
            self.mode = 'game over'
            return

        if Globals.player.rect.y >= Globals.map_pixel_height:
            Globals.player.get_damage(4, 500)

    def draw(self):
        Globals.screen.fill(pg.Color('#373737'))

        for platform in Globals.bg_platforms:
            Globals.screen.blit(platform.image, platform.rect.move(-Globals.camera_x, -Globals.camera_y))
        for chest in Globals.chests:
            Globals.screen.blit(chest.image, chest.rect.move(-Globals.camera_x, -Globals.camera_y))
        for coin in Globals.coins:
            Globals.screen.blit(coin.image, coin.rect.move(-Globals.camera_x, -Globals.camera_y))
        for arrow in Globals.arrows:
            Globals.screen.blit(arrow.image, arrow.rect.move(-Globals.camera_x, -Globals.camera_y))
        for platform in Globals.platforms:
            Globals.screen.blit(platform.image, platform.rect.move(-Globals.camera_x, -Globals.camera_y))
        for checkpoint in Globals.checkpoints:
            Globals.screen.blit(checkpoint.image, checkpoint.rect.move(-Globals.camera_x, -Globals.camera_y))
        for platform in Globals.fg_platforms:
            Globals.screen.blit(platform.image, platform.rect.move(-Globals.camera_x, -Globals.camera_y))
        for enemy in Globals.enemies:
            Globals.screen.blit(enemy.image, enemy.rect.move(-Globals.camera_x, -Globals.camera_y))
            enemy.draw_healthbar()
            if enemy.hp > 0:
                Globals.screen.blit(enemy.weapon.image, enemy.weapon.rect.move(-Globals.camera_x, -Globals.camera_y))

        Globals.screen.blit(Globals.player.image, Globals.player.rect.move(-Globals.camera_x, -Globals.camera_y))

        for item in Globals.items:
            Globals.screen.blit(item.image, item.rect.move(-Globals.camera_x, -Globals.camera_y))

        if Globals.player.active_item is not None:
            Globals.player.active_item.item_type.draw()

        if Globals.player.inventory.is_active:
            Globals.player.inventory.draw_interface()

        pg.draw.rect(Globals.screen, pg.Color('black'), (95, 15, 110, 25), 3)
        pg.draw.rect(Globals.screen, pg.Color('red'), (100, 20, Globals.player.hp/Globals.player.max_hp*100, 15))

        Globals.player.draw_money(Globals.screen)
        Globals.player.draw_hotbar(Globals.screen)

        for sprite in Globals.bp_sprites:
            sprite.draw()

        if self.mode == 'game over':
            text = font.render('ВЫ ПРОИГРАЛИ!', True, (255, 0, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            Globals.screen.blit(text, text_rect)

        if Globals.debug_image is not None:
            Globals.screen.blit(Globals.debug_image, (25, 50))

        pg.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    game = Game()   