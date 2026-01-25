#!/usr/bin/env python
# coding: utf-8

import pygame
import sys
import os
import random
import time
import json
import glob
from pygame.locals import *
from game_data import *
from assets import load_images, load_sounds, load_floor_variants, load_wall_variants


def load_floorlist(base_path):
    floorlist = []
    for i in range(3):
        with open(base_path + "/savedata/data{}.json".format(i+1), "r") as f:
            loaddata = json.load(f)
            floorlist.append(loaddata["floor"])
    return floorlist


class Game:
    def __init__(self):
        self.path = os.path.dirname(os.path.abspath(sys.argv[0]))

        images = load_images(self.path)
        self.imgTitle = images.title
        self.wall_variantsA = images.wallAs
        self.wall_variantsB = images.wallBs
        self.imgWall = self.wall_variantsA[0]
        self.imgWall2 = self.wall_variantsB[0]
        self.wall_item = None
        self.imgBtlBG = images.btl_bg
        self.imgEnemy = images.enemy
        self.imgItem = images.items
        self.imgFloor = images.floors
        self.imgPlayer = images.players
        self.imgEffect = images.effects
        self.imgFire = pygame.image.load(self.path + "/image/fire.png")
        self.imgPoison = pygame.image.load(self.path + "/image/poison.png")

        self.floor_variants = load_floor_variants(self.path, 0)
        if not self.floor_variants:
            self.floor_variants = [self.imgFloor[0]]
        self.floor_variants_flipped = [pygame.transform.flip(img, True, False) for img in self.floor_variants]
        self.imgFloor[0] = self.floor_variants[0]

        self.floorlist = load_floorlist(self.path)

        self.idx = 0
        self.title_mode = 0
        self.title_cmd = 0
        self.tmr = 0
        self.floor = 0
        self.boss = 0

        self.pl_x = 0
        self.pl_y = 0
        self.pl_d = 0
        self.pl_a = 0
        self.pl_lifemax = 0
        self.pl_life = 0
        self.pl_str = 0
        self.pl_mag = 0
        self.pl_exp = 0
        self.pl_shield = [[0, 0], [0, 0], [0, 0]]
        self.pl_armor = [[0, 0], [0, 0], [0, 0]]
        self.pl_sword = [[0, 0], [0, 0], [0, 0]]
        self.potion = 0
        self.blazegem = 0
        self.guard = 0
        self.treasure = 0
        self.trap = 0
        self.wpn_lev = 0

        self.emy_name = ""
        self.lev = 0
        self.emy_lifemax = 0
        self.emy_life = 0
        self.emy_str = 0
        self.emy_x = 0
        self.emy_y = 0
        self.emy_step = 0
        self.emy_blink = 0
        self.emy_typ = 0

        self.dmg_eff = 0
        self.menu_cmd = 0
        self.confirm_cmd = 0
        self.load_accept_lock = False
        self.title_confirm_lock = False
        self.save_confirm_lock = False
        self.menu_back_lock = False
        self.menu_accept_lock = False
        self.save_cmd = 0
        self.btl_cmd = 0
        self.pow_up = 1
        self.poison = 0
        self.madoka = 0
        self.burn_turns = 0
        self.inferno = 0
        self.boss_mode = "normal"
        self.guard_remain = 0
        self.change = 0
        self.wall_item = None

        self.maze = [[0 for j in range(MAZE_W)] for i in range(MAZE_H)]
        self.dungeon = [[0 for j in range(DUNGEON_W)] for i in range(DUNGEON_H)]

        self.message = [""] * 10
        self.init_floor_variant_map()
        self.init_floor_flip_map()
        self.prologue_lines = PROLOGUE_LINES
        self.prologue_input_lock = False
        self.boss_pos = None
        self.boss_area = set()
        self.boss_talk_lines = []
        self.boss_talk_index = 0
        self.boss_map_cache = {}
        self.bg_cache = {}
        self.prev_return = False
        self.prev_a = False
        self.boss_talk_char_count = 0
        self.boss_talk_last_tick = 0
        self.move_bgm_path = ""
        self.move_bgm_pos_ms = 0
        self.move_bgm_start_time = 0.0
        self.emy_skip_turn = False
        self.item_wall_pos = None
        self.item_wall_used = False
        self.item_wall_used = False
        self.item_talk_lines = []
        self.item_talk_index = 0
        self.item_talk_char_count = 0
        self.item_talk_last_tick = 0
        self.item_event_phase = 0
        self.item_choice = 0
        self.item_reward = None
        self.item_event_kind = ""
        self.item_reward_count = 3
        self.item_wall_claimed = set()
        self.true_episode_heard = False
        self.item_wall_pos = None
        self.wall_item = None
        self.event_wall_pos = None
        self.event_talk_lines = []
        self.event_talk_index = 0
        self.event_talk_char_count = 0
        self.event_talk_last_tick = 0
        self.wall_event = None
        self.map_seen = None
        self.map_stairs = None
        self.map_grid_surface = None
        self.map_surface = None
        self.map_surface_scale = None
        self.map_surface_size = None
        self.fixed_floor_data = None
        self.last_talk_mode = 1

    def init_floor_variant_map(self):
        count = max(len(self.floor_variants), 1)
        self.floor_var_map = [[random.randint(0, count - 1) for j in range(DUNGEON_W)] for i in range(DUNGEON_H)]

    def init_floor_flip_map(self):
        self.floor_flip_map = [[random.randint(0, 1) for j in range(DUNGEON_W)] for i in range(DUNGEON_H)]

    def init_map_state(self):
        self.map_seen = [[False for j in range(DUNGEON_W)] for i in range(DUNGEON_H)]
        self.map_stairs = set()
        self.map_grid_surface = pygame.Surface((DUNGEON_W, DUNGEON_H), pygame.SRCALPHA)
        self.map_grid_surface.fill((0, 0, 0, 120))
        self.map_surface = None
        self.map_surface_scale = None
        self.map_surface_size = None

    def set_floor_assets(self, floor_index, floor_value):
        self.floor_variants = load_floor_variants(self.path, floor_index)
        if not self.floor_variants:
            self.floor_variants = [self.imgFloor[0]]
        self.floor_variants_flipped = [pygame.transform.flip(img, True, False) for img in self.floor_variants]
        self.imgFloor[0] = self.floor_variants[0]
        self.imgFloor[2] = pygame.image.load(self.path + "/image/cocoon" + str(floor_index) + ".png")
        wall_set = (floor_value - 1) // 10
        self.wall_variantsA = load_wall_variants(self.path, "wallA", wall_set)
        if not self.wall_variantsA:
            self.wall_variantsA = [self.imgWall]
        self.wall_variantsB = load_wall_variants(self.path, "wallB", wall_set)
        if not self.wall_variantsB:
            self.wall_variantsB = [self.imgWall2]
        self.imgWall = self.wall_variantsA[0]
        self.imgWall2 = self.wall_variantsB[0]
        item_path = os.path.join(self.path, "image", "wallA{}_item.png".format(wall_set))
        self.wall_item = pygame.image.load(item_path) if os.path.exists(item_path) else None
        event_path = os.path.join(self.path, "image", "wallA{}_event.png".format(wall_set))
        self.wall_event = pygame.image.load(event_path) if os.path.exists(event_path) else None

    def set_floor_assets_for_current_floor(self):
        floor_index = (self.floor - 1) // 10
        self.set_floor_assets(floor_index, self.floor)

    def set_floor_assets_for_transition(self, floor_value):
        floor_index = (floor_value - 1) // 10
        self.set_floor_assets(floor_index, floor_value)

    def is_boss_tile(self, x, y):
        return (x, y) in self.boss_area

    def boss_in_front(self):
        if not self.boss_area:
            return False
        dx = 0
        dy = 0
        if self.pl_d == 0:
            dy = -1
        elif self.pl_d == 1:
            dy = 1
        elif self.pl_d == 2:
            dx = -1
        elif self.pl_d == 3:
            dx = 1
        tx = self.pl_x + dx
        ty = self.pl_y + dy
        return (tx, ty) in self.boss_area

    def stair_in_front(self):
        dx = 0
        dy = 0
        if self.pl_d == 0:
            dy = -1
        elif self.pl_d == 1:
            dy = 1
        elif self.pl_d == 2:
            dx = -1
        elif self.pl_d == 3:
            dx = 1
        tx = self.pl_x + dx
        ty = self.pl_y + dy
        if 0 <= tx < DUNGEON_W and 0 <= ty < DUNGEON_H:
            return self.dungeon[ty][tx] == 3
        return False

    def all_cocoons_cleared(self):
        return all(2 not in row for row in self.dungeon)

    def all_item_walls_claimed(self):
        return all(floor in self.item_wall_claimed for floor in range(91, 100))

    def place_boss(self):
        self.boss_pos = None
        self.boss_area = set()
        candidates = []
        for y in range(3, DUNGEON_H - 5):
            for x in range(3, DUNGEON_W - 4):
                if (self.dungeon[y][x] == 0 and self.dungeon[y][x + 1] == 0 and
                    self.dungeon[y + 1][x] == 0 and self.dungeon[y + 1][x + 1] == 0 and
                    self.dungeon[y + 2][x] == 0 and self.dungeon[y + 2][x + 1] == 0):
                    candidates.append((x, y))
        if candidates:
            x, y = random.choice(candidates)
            self.boss_pos = (x, y)
            self.boss_area = {(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)}
            return
        x = random.randint(3, DUNGEON_W - 4)
        y = random.randint(3, DUNGEON_H - 5)
        for ry in range(0, 3):
            for rx in range(0, 2):
                self.dungeon[y + ry][x + rx] = 0
        self.boss_pos = (x, y)
        self.boss_area = {(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)}

    def init_boss_talk(self):
        boss_id = 9 + int(self.floor // 10)
        if 90 < self.floor < 100:
            boss_id = 9 + int(self.floor % 10)
        boss_map_id = boss_id - 9
        self.boss_talk_lines = BOSS_TALK[boss_map_id]
        self.boss_talk_index = 0
        self.boss_talk_char_count = 0
        self.boss_talk_last_tick = pygame.time.get_ticks()

    def init_last_talk(self, mode=1):
        self.last_talk_mode = mode
        if mode == 2:
            self.boss_talk_lines = BOSS_LASTTALK2
        else:
            self.boss_talk_lines = BOSS_LASTTALK1
        self.boss_talk_index = 0
        self.boss_talk_char_count = 0
        self.boss_talk_last_tick = pygame.time.get_ticks()

    def init_item_event(self, kind=None, reward_count=3, lines=None):
        self.item_event_phase = 0
        self.item_choice = 0
        self.item_reward = None
        self.item_talk_index = 0
        self.item_talk_char_count = 0
        self.item_talk_last_tick = pygame.time.get_ticks()
        self.item_reward_count = reward_count
        if kind is None:
            if (self.floor // 10) % 2 == 0:
                kind = "item"
            else:
                kind = "weapon"
        self.item_event_kind = kind
        if lines is not None:
            self.item_talk_lines = lines
        else:
            self.item_talk_lines = [
                "迷える子羊よ。そなたに恵みをもたらしましょう。",
                "あなたが必要としているものは何ですか？",
            ]

    def init_event_talk(self):
        event_id = (self.floor - 1) // 10
        if 0 <= event_id < len(EVENT_TALK):
            self.event_talk_lines = EVENT_TALK[event_id]
        else:
            self.event_talk_lines = ["Event talk missing."]
        self.event_talk_index = 0
        self.event_talk_char_count = 0
        self.event_talk_last_tick = pygame.time.get_ticks()

    def get_boss_map_image(self):
        boss_id = 9 + int(self.floor // 10)
        if 90 < self.floor < 100:
            boss_id = 9 + int(self.floor % 10)
        boss_map_id = boss_id - 9
        if boss_map_id not in self.boss_map_cache:
            path = self.path + "/image/boss_map" + str(boss_map_id) + ".png"
            self.boss_map_cache[boss_map_id] = pygame.image.load(path)
        return self.boss_map_cache[boss_map_id]

    def make_dungeon (self ):
        self.fixed_floor_data = None
        self.last_talk_mode = 1
        if self.floor == 100:
            floor_path = os.path.join(self.path, "floor_100.json")
            if os.path.exists(floor_path):
                with open(floor_path, "r") as f:
                    data = json.load(f)
                dungeon = data.get("dungeon")
                if (isinstance(dungeon, list) and len(dungeon) == DUNGEON_H and
                        all(isinstance(row, list) and len(row) == DUNGEON_W for row in dungeon)):
                    self.dungeon = dungeon
                    self.fixed_floor_data = data
                    self.init_floor_variant_map()
                    self.init_floor_flip_map()
                    self.init_map_state()
                    return
        XP =[0 ,1 ,0 ,-1 ]
        YP =[-1 ,0 ,1 ,0 ]
        cell = 9
        center = 4
        hall_half = 1

        #周りの壁
        for x in range (MAZE_W ):
            self.maze [0 ][x ]=1 
            self.maze [MAZE_H -1 ][x ]=1 
        for y in range (1 ,MAZE_H -1 ):
            self.maze [y ][0 ]=1 
            self.maze [y ][MAZE_W -1 ]=1 
        #中を何もない状態に
        for y in range (1 ,MAZE_H -1 ):
            for x in range (1 ,MAZE_W -1 ):
                self.maze [y ][x ]=0 
        #柱
        for y in range (2 ,MAZE_H -2 ,2 ):
            for x in range (2 ,MAZE_W -2 ,2 ):
                self.maze [y ][x ]=1 
        #柱から壁を作る
        for y in range (2 ,MAZE_H -2 ,2 ):
            for x in range (2 ,MAZE_W -2 ,2 ):
                d =random .randint (0 ,3 )
                if x >2 :
                    d =random .randint (0 ,2 )
                self.maze [y +YP [d ]][x +XP [d ]]=1 

        #迷路からダンジョンを生成
        for y in range (DUNGEON_H ):
            for x in range (DUNGEON_W ):
                self.dungeon [y ][x ]=9 
        #部屋と通路の配置
        for y in range (1 ,MAZE_H -1 ):
            for x in range (1 ,MAZE_W -1 ):
                dx =x *cell +center 
                dy =y *cell +center 
                if self.maze [y ][x ]==0 :
                    if self.floor %10 ==0 or self.floor >90 :
                        bossfloor =80 
                    else :
                        bossfloor =0 
                    if random .randint (0 ,99 )<20 +bossfloor :
                        for ry in range (-center ,center +1 ):
                            for rx in range (-center ,center +1 ):
                                self.dungeon [dy +ry ][dx +rx ]=0 
                    else :#通路を作る
                        for ry in range (-hall_half ,hall_half +1 ):
                            for rx in range (-hall_half ,hall_half +1 ):
                                self.dungeon [dy +ry ][dx +rx ]=0 
                    if self.maze [y -1 ][x ]==0 :
                        for step in range (1 ,center +1 ):
                            for rx in range (-hall_half ,hall_half +1 ):
                                self.dungeon [dy -step ][dx +rx ]=0 
                    if self.maze [y +1 ][x ]==0 :
                        for step in range (1 ,center +1 ):
                            for rx in range (-hall_half ,hall_half +1 ):
                                self.dungeon [dy +step ][dx +rx ]=0 
                    if self.maze [y ][x -1 ]==0 :
                        for step in range (1 ,center +1 ):
                            for ry in range (-hall_half ,hall_half +1 ):
                                self.dungeon [dy +ry ][dx -step ]=0 
                    if self.maze [y ][x +1 ]==0 :
                        for step in range (1 ,center +1 ):
                            for ry in range (-hall_half ,hall_half +1 ):
                                self.dungeon [dy +ry ][dx +step ]=0 
        self.init_floor_variant_map()
        self.init_floor_flip_map()
        self.init_map_state()

    def draw_dungeon (self ,bg ,fnt ):
        bg .fill (BLACK )
        bg_rect =self.blit_scaled_bg (bg ,self.imgBtlBG ,0 ,0 ,False )
        self.dungeon_view_rect =bg_rect
        view_left =bg_rect [0 ]
        view_top =bg_rect [1 ]
        view_w =bg_rect [2 ]
        view_h =bg_rect [3 ]
        if self.map_seen is None :
            self.init_map_state ()
        new_seen =[]
        prev_clip =bg .get_clip ()
        bg .set_clip (pygame .Rect (view_left ,view_top ,view_w ,view_h ))
        tile =80 
        cols =view_w //tile +2 
        rows =view_h //tile +2 
        start_x =-(cols //2 )
        start_y =-(rows //2 )
        offset_x =view_left +view_w //2 -tile //2 -(cols //2 )*tile 
        offset_y =view_top +view_h //2 -tile //2 -(rows //2 )*tile 
        for y in range (start_y ,start_y +rows ):
            for x in range (start_x ,start_x +cols ):
                X =offset_x +(x -start_x )*tile 
                Y =offset_y +(y -start_y )*tile 
                dx =self.pl_x +x 
                dy =self.pl_y +y 
                if 0 <=dx <DUNGEON_W and 0 <=dy <DUNGEON_H :
                    tile_id =self.dungeon [dy ][dx ]
                    if tile_id !=9 :
                        if not self.map_seen [dy ][dx ]:
                            self.map_seen [dy ][dx ]=True
                            new_seen .append ((dx ,dy ))
                        if tile_id ==3 :
                            self.map_stairs .add ((dx ,dy ))
                    if tile_id <=7 :
                        if tile_id in (0 ,1 ,2 ,4 ):
                            variant =self.floor_var_map [dy ][dx ]
                            if self.floor_flip_map [dy ][dx ]:
                                bg .blit (self.floor_variants_flipped [variant ],[X ,Y ])
                            else :
                                bg .blit (self.floor_variants [variant ],[X ,Y ])
                            if tile_id !=0 :
                                bg .blit (self.imgFloor [tile_id ],[X ,Y ])
                        else :
                            bg .blit (self.imgFloor [tile_id ],[X ,Y ])
                    if tile_id ==9 :
                        if self.event_wall_pos and (dx, dy) == self.event_wall_pos and self.wall_event:
                            bg .blit (self.wall_event ,[X ,Y -40 ])
                        elif self.item_wall_pos and (dx, dy) == self.item_wall_pos and self.wall_item:
                            bg .blit (self.wall_item ,[X ,Y -40 ])
                        else:
                            bg .blit (self.imgWall ,[X ,Y -40 ])
                        if dy >=1 and self.dungeon [dy -1 ][dx ]==9 :
                            bg .blit (self.imgWall2 ,[X ,Y -80 ])
                    if self.boss_pos and dx == self.boss_pos[0] + 1 and dy == self.boss_pos[1] + 1:
                        boss_map = self.get_boss_map_image()
                        bx = X - 80
                        by = Y - 80
                        bg .blit (boss_map ,[bx ,by ])
                if x ==0 and y ==0 :# 主人公キャラの表示
                    bg .blit (self.imgPlayer [self.pl_a ],[X ,Y -40 ])
        bg .set_clip (prev_clip )
        self.update_minimap_grid (new_seen )
        if self.idx ==100 :
            self.draw_minimap (bg ,bg_rect ,new_seen )
        self.draw_para (bg ,fnt ,bg_rect )# 主人公の能力を表示

    def put_event (self ):
    # 階段かボスの配置
        self.boss_pos = None
        self.boss_area = set()
        self.item_wall_pos = None
        self.item_wall_used = False
        self.event_wall_pos = None
        is_boss_floor =self.floor %10 ==0 or self.floor >90
        if self.fixed_floor_data and self.floor == 100:
            boss_pos = self.fixed_floor_data.get("boss_pos")
            if boss_pos:
                bx, by = boss_pos
                self.boss_pos = (bx, by)
                self.boss_area = {(bx, by), (bx + 1, by), (bx, by + 1), (bx + 1, by + 1)}
        if is_boss_floor :
            if not self.boss_pos:
                self.place_boss()
        if not self.boss_pos:
            while True :
                x =random .randint (3 ,DUNGEON_W -4 )
                y =random .randint (3 ,DUNGEON_H -4 )
                if (self.dungeon [y ][x ]==0 ):
                    self.dungeon [y ][x ]=3 
                    break 
        # 宝箱と繭と武器の配置
        floor_cells =[
            (x ,y )
            for y in range (3 ,DUNGEON_H -3 )
            for x in range (3 ,DUNGEON_W -3 )
            if self.dungeon [y ][x ]==0 and not self.is_boss_tile (x ,y )
        ]
        random .shuffle (floor_cells )
        def take_cells (count ):
            taken =floor_cells [:count ]
            del floor_cells [:count ]
            return taken
        if not is_boss_floor :
            for x ,y in take_cells (5 ):
                self.dungeon [y ][x ]=1
            for x ,y in take_cells (3 ):
                self.dungeon [y ][x ]=4
        if is_boss_floor :
            for x ,y in take_cells (10 ):
                self.dungeon [y ][x ]=1
            for x ,y in take_cells (5 ):
                self.dungeon [y ][x ]=4
        cocoon_target =40 if is_boss_floor else 22
        for x ,y in take_cells (cocoon_target ):
            self.dungeon [y ][x ]=2
        # ダメージ、回復床の配置
        if self.floor >50 :
            for i in range ((7 +int (self.floor //90 )*(self.floor -83 ))*10 ):
                x =random .randint (3 ,DUNGEON_W -4 )
                y =random .randint (3 ,DUNGEON_H -4 )
                if (self.dungeon [y ][x ]==0 )and not self.is_boss_tile (x ,y ):
                    if random .random ()>0.5 :
                        self.dungeon [y ][x ]=5 
                    else :
                        self.dungeon [y ][x ]=6 
        # プレイヤーの初期位置
        if self.fixed_floor_data and self.floor == 100 and self.fixed_floor_data.get("pl_start"):
            self.pl_x, self.pl_y = self.fixed_floor_data["pl_start"]
        else:
            while True :
                self.pl_x =random .randint (3 ,DUNGEON_W -4 )
                self.pl_y =random .randint (3 ,DUNGEON_H -4 )
                if (self.dungeon [self.pl_y ][self.pl_x ]==0 )and not self.is_boss_tile (self.pl_x ,self.pl_y ):
                    break 
        self.pl_d =1 
        self.pl_a =2 
        if self.floor >= 91:
            if self.wall_item:
                wall_cells = [
                    (x, y)
                    for y in range(DUNGEON_H - 1)
                    for x in range(DUNGEON_W)
                    if self.dungeon[y][x] == 9 and self.dungeon[y + 1][x] == 0
                ]
                if wall_cells:
                    self.item_wall_pos = random.choice(wall_cells)
        else:
            if self.floor %10 ==7 and self.wall_item:
                wall_cells = [
                    (x, y)
                    for y in range(DUNGEON_H - 1)
                    for x in range(DUNGEON_W)
                    if self.dungeon[y][x] == 9 and self.dungeon[y + 1][x] == 0
                ]
                if wall_cells:
                    self.item_wall_pos = random.choice(wall_cells)
            if self.floor %10 ==4 and self.wall_event:
                wall_cells = [
                    (x, y)
                    for y in range(DUNGEON_H - 1)
                    for x in range(DUNGEON_W)
                    if self.dungeon[y][x] == 9 and self.dungeon[y + 1][x] == 0
                ]
                if wall_cells:
                    self.event_wall_pos = random.choice(wall_cells)

    def move_player (self ,key ):

        if self.dungeon [self.pl_y ][self.pl_x ]==1 :# 宝箱に載った
            self.dungeon [self.pl_y ][self.pl_x ]=0 
            self.treasure =random .choice ([0 ,0 ,1 ,1 ,1 ,2 ])
            if self.treasure ==0 :
                self.potion =self.potion +1 
            if self.treasure ==1 :
                self.blazegem =self.blazegem +1 
            if self.treasure ==2 :
                self.guard =self.guard +1 
            self.idx =120 
            self.tmr =0 
            return 
        if self.dungeon [self.pl_y ][self.pl_x ]==4 :# 武器箱に載った
            self.dungeon [self.pl_y ][self.pl_x ]=0 
            w_a =WEP_APPEAR [(self.floor -1 )//10 ]
            self.trap =random .randint (2 ,4 +w_a )#最大で2~10を用意
            low =max (1 ,self.floor -14 )
            self.wpn_lev =random .randint (low ,self.floor )
            if self.trap %3 ==2 :
                if self.pl_shield [(w_a +2 )//3 ][0 ]==0 :
                    self.trap =2 +3 *((w_a +2 )//3 )
                self.pl_shield [self.trap //3 ][0 ]=1 
                self.pl_shield [self.trap //3 ][1 ]=max (self.wpn_lev ,self.pl_shield [self.trap //3 ][1 ])
            if self.trap %3 ==0 :
                if self.pl_armor [(w_a +1 )//3 ][0 ]==0 :
                    self.trap =3 +3 *((w_a +1 )//3 )
                self.pl_armor [self.trap //3 -1 ][0 ]=1 
                self.pl_armor [self.trap //3 -1 ][1 ]=max (self.wpn_lev ,self.pl_armor [self.trap //3 -1 ][1 ])
            if self.trap %3 ==1 :
                if self.pl_sword [(w_a )//3 ][0 ]==0 :
                    self.trap =4 +3 *((w_a )//3 )
                self.pl_sword [self.trap //3 -1 ][0 ]=1 
                self.pl_sword [self.trap //3 -1 ][1 ]=max (self.wpn_lev ,self.pl_sword [self.trap //3 -1 ][1 ])
            self.idx =121 
            self.tmr =0 
            return 
        if self.dungeon [self.pl_y ][self.pl_x ]==5 :# ダメージ床
            self.dungeon [self.pl_y ][self.pl_x ]=0 
            self.trap =0 
            pygame .mixer .Sound (self.path +"/sound/ohd_se_attack.wav").play ()
            self.pl_life =self.pl_life -10 *((self.floor -1 )//10 )+30 
            self.idx =121 
            self.tmr =0 
            if self.pl_life <=0 :
                self.pl_life =0 
                pygame .mixer .music .stop ()
                self.idx =70 
                self.tmr =0 
            return 
        if self.dungeon [self.pl_y ][self.pl_x ]==6 :# 回復床
            self.dungeon [self.pl_y ][self.pl_x ]=0 
            self.trap =1 
            pygame .mixer .Sound (self.path +"/sound/ohd_se_potion.wav").play ()
            self.pl_life =min (self.pl_life -20 +10 *((self.floor -1 )//10 ),self.pl_lifemax )
            self.idx =121 
            self.tmr =0 
            return 
        if self.dungeon [self.pl_y ][self.pl_x ]==2 :# 繭に載った
            self.dungeon [self.pl_y ][self.pl_x ]=0 
            r =random .randint (0 ,99 )
            if r <35 :# 食料
                self.treasure =random .choice ([3 ,3 ,3 ,3 ,3 ,4 ,4 ,4 ,4 ,4 ,5 ])
                if self.treasure ==3 :
                    self.pl_life =min (self.pl_life +40 ,self.pl_lifemax )
                if self.treasure ==4 :
                    self.pl_life =min (self.pl_life +20 ,self.pl_lifemax )
                    self.pl_mag =self.pl_mag +40 
                if self.treasure ==5 :
                    self.pl_mag =self.pl_mag +120 
                self.idx =120 
                self.tmr =0 
            else :# 敵出現
                self.idx =200 
                self.tmr =0 
            return 
        if key [K_m ]==1 :# メニュー
            self.idx =30 

        # 方向キーで上下左右に移動
        x =self.pl_x 
        y =self.pl_y 
        if key [K_UP ]==1 :
            self.pl_d =0 
            if self.dungeon [self.pl_y -1 ][self.pl_x ]!=9 and self.dungeon [self.pl_y -1 ][self.pl_x ]!=3 and not self.is_boss_tile (self.pl_x ,self.pl_y -1 ):
                self.pl_y =self.pl_y -1 
        if key [K_DOWN ]==1 :
            self.pl_d =1 
            if self.dungeon [self.pl_y +1 ][self.pl_x ]!=9 and self.dungeon [self.pl_y +1 ][self.pl_x ]!=3 and not self.is_boss_tile (self.pl_x ,self.pl_y +1 ):
                self.pl_y =self.pl_y +1 
        if key [K_LEFT ]==1 :
            self.pl_d =2 
            if self.dungeon [self.pl_y ][self.pl_x -1 ]!=9 and self.dungeon [self.pl_y ][self.pl_x -1 ]!=3 and not self.is_boss_tile (self.pl_x -1 ,self.pl_y ):
                self.pl_x =self.pl_x -1 
        if key [K_RIGHT ]==1 :
            self.pl_d =3 
            if self.dungeon [self.pl_y ][self.pl_x +1 ]!=9 and self.dungeon [self.pl_y ][self.pl_x +1 ]!=3 and not self.is_boss_tile (self.pl_x +1 ,self.pl_y ):
                self.pl_x =self.pl_x +1 
        self.pl_a =self.pl_d *2 
        if self.pl_x !=x or self.pl_y !=y :
            self.pl_a =self.pl_a +self.tmr %2 # 移動したら足踏みのアニメーション

    def draw_text (self ,bg ,txt ,x ,y ,fnt ,col ):
        sur =fnt .render (txt ,True ,BLACK )
        bg .blit (sur ,[x +1 ,y +2 ])
        sur =fnt .render (txt ,True ,col )
        bg .blit (sur ,[x ,y ])

    def draw_text_alpha (self ,bg ,txt ,x ,y ,fnt ,col ,alpha ):
        shadow =fnt .render (txt ,True ,BLACK )
        shadow .set_alpha (alpha )
        bg .blit (shadow ,[x +1 ,y +2 ])
        text =fnt .render (txt ,True ,col )
        text .set_alpha (alpha )
        bg .blit (text ,[x ,y ])

    def blit_scaled_bg (self ,bg ,img ,off_x =0 ,off_y =0 ,draw =True ,alpha =None ):
        screen_w ,screen_h =bg .get_size ()
        key =(id (img ),screen_w ,screen_h )
        cached =self.bg_cache .get (key )
        if cached :
            scaled ,base_x ,base_y ,new_w ,new_h =cached
        else :
            img_w ,img_h =img .get_size ()
            scale =min (screen_w /img_w ,screen_h /img_h )
            new_w =max (1 ,int (img_w *scale ))
            new_h =max (1 ,int (img_h *scale ))
            scaled =pygame .transform .scale (img ,(new_w ,new_h ))
            base_x =(screen_w -new_w )//2 
            base_y =(screen_h -new_h )//2 
            self.bg_cache [key ]=(scaled ,base_x ,base_y ,new_w ,new_h )
        if draw :
            if alpha is None :
                bg .blit (scaled ,[base_x +off_x ,base_y +off_y ])
            else :
                temp =scaled .copy ()
                temp .set_alpha (alpha )
                bg .blit (temp ,[base_x +off_x ,base_y +off_y ])
        return (base_x +off_x ,base_y +off_y ,new_w ,new_h )

    def start_new_game (self ):
        self.floor =1 
        self.set_floor_assets_for_current_floor ()
        self.make_dungeon ()
        self.put_event ()
        self.pl_lifemax =300 
        self.pl_life =self.pl_lifemax 
        self.pl_str =100 
        self.pl_mag =0 
        self.pl_exp =0 
        self.potion =0 
        self.blazegem =0 
        self.guard =0 
        self.item_wall_claimed = set()
        self.true_episode_heard = False
        self.idx =100 
        self.tmr =0 
        self.pl_shield =[[0 ,0 ],[0 ,0 ],[0 ,0 ]]
        self.pl_armor =[[0 ,0 ],[0 ,0 ],[0 ,0 ]]
        self.pl_sword =[[0 ,0 ],[0 ,0 ],[0 ,0 ]]
        self.move_bgm_path =self.path +"/sound/bgm_"+str ((self.floor-1) //10 )+".wav"
        self.move_bgm_pos_ms =0 
        self.move_bgm_start_time =time .time ()
        pygame .mixer .music .load (self.move_bgm_path )
        pygame .mixer .music .play (-1 )

    def load_game_data (self ,slot_index ):
        with open (self.path +"/savedata/data{}.json".format (slot_index +1 ),"r")as f :
            loaddata =json .load (f )
            self.floor =loaddata ["floor"]
            if self.floor >0 :
                self.dungeon =loaddata ["dungeon"]
                self.pl_x =loaddata ["pl_x"]
                self.pl_y =loaddata ["pl_y"]
                self.pl_lifemax =loaddata ["pl_lifemax"]
                self.pl_life =loaddata ["pl_life"]
                self.pl_str =loaddata ["pl_str"]
                self.pl_mag =loaddata ["pl_mag"]
                self.pl_exp =loaddata ["pl_exp"]
                self.potion =loaddata ["potion"]
                self.blazegem =loaddata ["blazegem"]
                self.guard =loaddata ["guard"]
                self.idx =100 
                self.pl_shield =loaddata ["shield"]
                self.pl_armor =loaddata ["armor"]
                self.pl_sword =loaddata ["sword"]
                if "boss_pos" in loaddata and loaddata ["boss_pos"] is not None:
                    bx, by = loaddata ["boss_pos"]
                    self.boss_pos = (bx, by)
                    self.boss_area = {(bx, by), (bx + 1, by), (bx, by + 1), (bx + 1, by + 1)}
                else:
                    self.boss_pos = None
                    self.boss_area = set()
                if "item_wall_pos" in loaddata and loaddata ["item_wall_pos"] is not None:
                    ix, iy = loaddata ["item_wall_pos"]
                    self.item_wall_pos = (ix, iy)
                else:
                    self.item_wall_pos = None
                self.item_wall_used = bool(loaddata.get("item_wall_used", False))
                self.item_wall_claimed = set(loaddata.get("item_wall_claimed", []))
                if 91 <= self.floor <= 99 and self.item_wall_used:
                    self.item_wall_claimed.add(self.floor)
                self.true_episode_heard = bool(loaddata.get("true_episode_heard", False))
                if "event_wall_pos" in loaddata and loaddata ["event_wall_pos"] is not None:
                    ex, ey = loaddata ["event_wall_pos"]
                    self.event_wall_pos = (ex, ey)
                else:
                    self.event_wall_pos = None
                self.item_event_phase = 0
                self.item_choice = 0
                self.item_reward = None
                self.item_event_kind = ""
                self.item_talk_lines = []
                self.item_talk_index = 0
                self.item_talk_char_count = 0
                self.item_talk_last_tick = pygame.time.get_ticks()
                self.set_floor_assets_for_current_floor ()
                if self.floor >= 91:
                    self.event_wall_pos = None
                    if self.item_wall_pos is None and self.wall_item:
                        wall_cells = [
                            (x, y)
                            for y in range(DUNGEON_H - 1)
                            for x in range(DUNGEON_W)
                            if self.dungeon[y][x] == 9 and self.dungeon[y + 1][x] == 0
                        ]
                        if wall_cells:
                            self.item_wall_pos = random.choice(wall_cells)
                self.init_floor_variant_map ()
                self.init_map_state ()
                self.move_bgm_path =self.path +"/sound/bgm_"+str ((self.floor-1) //10 )+".wav"
                self.move_bgm_pos_ms =0 
                self.move_bgm_start_time =time .time ()
                pygame .mixer .music .load (self.move_bgm_path )
                pygame .mixer .music .play (-1 )

    def draw_prologue (self ,bg ,fnt ,key ):
        line_duration =20 
        fade_in =15 
        end_hold =30 
        end_fade =60 
        max_lines =12 
        line_height =32 
        start_y =90 
        total_duration =len (self.prologue_lines )*line_duration 

        if key [K_s ]:
            self.start_new_game ()
            return 

        line_index =self.tmr //line_duration 
        phase =self.tmr %line_duration 
        if self.prologue_input_lock:
            if not (key [K_RETURN ]or key [K_RIGHT ]or key [K_a ]):
                self.prologue_input_lock = False
        else:
            if key [K_RETURN ]or key [K_RIGHT ]or key [K_a ]:
                if line_index <len (self.prologue_lines )and phase <fade_in :
                    self.tmr =line_index *line_duration +fade_in 
                    phase =fade_in 

        bg .fill (BLACK )
        bg_rect =self.blit_scaled_bg (bg ,self.imgBtlBG ,0 ,0 ,False )
        bg_left ,bg_top ,bg_w ,bg_h =bg_rect
        text_x =bg_left +int (bg_w *0.1 )
        start_y =bg_top +90
        skip_label ="[S]kip"
        skip_x =bg_left +bg_w -int (bg_w *0.1 )-fnt .size (skip_label )[0 ]
        self.draw_text (bg ,skip_label ,skip_x ,bg_top +40 ,fnt ,WHITE )

        if self.tmr >=total_duration :
            end_phase =self.tmr -total_duration 
            if end_phase >=end_hold +end_fade :
                self.start_new_game ()
                return 
            if end_phase <end_hold :
                alpha =255 
            else :
                alpha =int (255 *(1 -(end_phase -end_hold )/end_fade ))
            visible_start =max (0 ,len (self.prologue_lines )-max_lines )
            for i in range (visible_start ,len (self.prologue_lines )):
                txt =self.prologue_lines [i ]
                if txt :
                    y =start_y +(i -visible_start )*line_height 
                    self.draw_text_alpha (bg ,txt ,text_x ,y ,fnt ,WHITE ,alpha )
            return 

        visible_start =max (0 ,line_index -(max_lines -1 ))
        for i in range (visible_start ,line_index ):
            txt =self.prologue_lines [i ]
            if txt :
                y =start_y +(i -visible_start )*line_height 
                self.draw_text (bg ,txt ,text_x ,y ,fnt ,WHITE )
        if phase <fade_in :
            alpha =int (255 *phase /fade_in )
        else :
            alpha =255 
        txt =self.prologue_lines [line_index ]
        if txt :
            y =start_y +(line_index -visible_start )*line_height 
            self.draw_text_alpha (bg ,txt ,text_x ,y ,fnt ,WHITE ,alpha )

    def draw_epilogue (self ,bg ,fnt ,key ):
        lines = EPILOGUE_LINES
        line_duration =15
        fade_in =13
        end_hold =30 
        end_fade =30 
        max_lines =12 
        line_height =32 
        start_y =90 
        total_duration =len (lines )*line_duration 

        if key [K_s ]:
            return True

        line_index =self.tmr //line_duration 
        phase =self.tmr %line_duration 
        if key [K_RETURN ]or key [K_RIGHT ]or key [K_a ]:
            if line_index <len (lines )and phase <fade_in :
                self.tmr =line_index *line_duration +fade_in 
                phase =fade_in 

        bg .fill (BLACK )
        bg_rect =self.blit_scaled_bg (bg ,self.imgBtlBG ,0 ,0 ,False )
        bg_left ,bg_top ,bg_w ,bg_h =bg_rect
        text_x =bg_left +int (bg_w *0.1 )
        start_y =bg_top +90
        skip_label ="[S]kip"
        skip_x =bg_left +bg_w -int (bg_w *0.1 )-fnt .size (skip_label )[0 ]
        self.draw_text (bg ,skip_label ,skip_x ,bg_top +40 ,fnt ,WHITE )

        if self.tmr >=total_duration :
            end_phase =self.tmr -total_duration 
            if end_phase >=end_hold +end_fade :
                return True
            if end_phase <end_hold :
                alpha =255 
            else :
                alpha =int (255 *(1 -(end_phase -end_hold )/end_fade ))
            visible_start =max (0 ,len (lines )-max_lines )
            for i in range (visible_start ,len (lines )):
                txt =lines [i ]
                if txt :
                    y =start_y +(i -visible_start )*line_height 
                    self.draw_text_alpha (bg ,txt ,text_x ,y ,fnt ,WHITE ,alpha )
            return False

        visible_start =max (0 ,line_index -(max_lines -1 ))
        for i in range (visible_start ,line_index ):
            txt =lines [i ]
            if txt :
                y =start_y +(i -visible_start )*line_height 
                self.draw_text (bg ,txt ,text_x ,y ,fnt ,WHITE )
        if phase <fade_in :
            alpha =int (255 *phase /fade_in )
        else :
            alpha =255 
        if line_index <len (lines ):
            txt =lines [line_index ]
            if txt :
                y =start_y +(line_index -visible_start )*line_height 
                self.draw_text_alpha (bg ,txt ,text_x ,y ,fnt ,WHITE ,alpha )
        return False

    def draw_end_roll (self ,bg ,fnt ,key ):
        lines = END_ROLL
        line_height =36 
        speed =2
        start_y =720 +line_height 
        y0 =start_y -self.tmr *speed 

        bg .fill (BLACK )
        for i, txt in enumerate(lines):
            y =y0 +i *line_height 
            if -line_height <= y <= 720 + line_height:
                self.draw_text (bg ,txt ,240 ,y ,fnt ,WHITE )
        finished = y0 +len (lines )*line_height < -line_height
        if finished:
            self.draw_text (bg ,"Press space key",320 ,640 ,fnt ,BLINK [self.tmr %6 ])
            if key [K_SPACE ]==1 :
                return True
        return False

    def get_font (self ,size ):
        font_path =os .path .join (self.path ,"fonts","PixelMplus12-Regular.ttf")
        return pygame .font .Font (font_path ,size )

    def draw_para (self ,bg ,fnt ,view_rect =None ):
        if view_rect :
            view_left ,view_top ,view_w ,view_h =view_rect
        else :
            view_left =0 
            view_top =0 
            view_w ,view_h =bg .get_size ()
        X =view_left +10
        W =325 
        H =140 
        margin_bottom =15 
        Y =view_top +view_h -H -margin_bottom 
        win =pygame .Surface ((W ,H ),pygame .SRCALPHA )
        win .fill ((0 ,0 ,0 ,100 ))
        # pygame .draw .rect (win ,WHITE ,[0 ,0 ,W ,H ],2 )
        bg .blit (win ,[X ,Y ])

        self.draw_text (bg ,"傷薬",X +10 ,Y +8 ,fnt ,WHITE )
        self.draw_text (bg ,str (self.potion ),X +55 ,Y +8 ,fnt ,WHITE )
        self.draw_text (bg ,"爆弾",X +110 ,Y +8 ,fnt ,WHITE )
        self.draw_text (bg ,str (self.blazegem ),X +155 ,Y +8 ,fnt ,WHITE )
        self.draw_text (bg ,"守護",X +210 ,Y +8 ,fnt ,WHITE )
        self.draw_text (bg ,str (self.guard ),X +255 ,Y +8 ,fnt ,WHITE )

        col =WHITE 
        if self.pl_life <int (self.pl_lifemax /5 )and self.tmr %2 ==0 :col =RED 
        self.draw_text (bg ,"生命",X +10 ,Y +44 ,fnt ,WHITE )
        self.draw_text (bg ,"{}/{}".format (self.pl_life ,self.pl_lifemax ),X +73 ,Y +44 ,fnt ,col )
        self.draw_text (bg ,"攻撃",X +10 ,Y +69 ,fnt ,WHITE )
        self.draw_text (bg ,str (self.pl_str ),X +73 ,Y +69 ,fnt ,WHITE )
        self.draw_text (bg ,"魔力",X +10 ,Y +95 ,fnt ,WHITE )
        self.draw_text (bg ,str (self.pl_mag ),X +73 ,Y +95 ,fnt ,WHITE )
        self.draw_text (bg ,"経験",X +10 ,Y +120 ,fnt ,WHITE )
        self.draw_text (bg ,str (self.pl_exp )+"/"+str ((self.pl_lifemax -250 )*20 ),X +73 ,Y +120 ,fnt ,WHITE )

        self.draw_text (bg ,"盾",X +180 ,Y +46 ,fnt ,WHITE )
        self.draw_text (bg ,"{}-{}-{}".format (self.pl_shield [0 ][1 ],self.pl_shield [1 ][1 ],self.pl_shield [2 ][1 ]),X +225 ,Y +46 ,fnt ,WHITE )
        self.draw_text (bg ,"鎧",X +180 ,Y +71 ,fnt ,WHITE )
        self.draw_text (bg ,"{}-{}-{}".format (self.pl_armor [0 ][1 ],self.pl_armor [1 ][1 ],self.pl_armor [2 ][1 ]),X +225 ,Y +71 ,fnt ,WHITE )
        self.draw_text (bg ,"剣",X +180 ,Y +97 ,fnt ,WHITE )
        self.draw_text (bg ,"{}-{}-{}".format (self.pl_sword [0 ][1 ],self.pl_sword [1 ][1 ],self.pl_sword [2 ][1 ]),X +225 ,Y +97 ,fnt ,WHITE )

    def update_minimap_grid (self ,new_seen ):
        if self.map_grid_surface is None or self.map_grid_surface.get_size ()!=(DUNGEON_W ,DUNGEON_H ):
            self.map_grid_surface = pygame.Surface((DUNGEON_W, DUNGEON_H), pygame.SRCALPHA)
            self.map_grid_surface.fill((0, 0, 0, 120))
            for y in range (DUNGEON_H ):
                row =self.map_seen [y ]
                for x in range (DUNGEON_W ):
                    if row [x ]and self.dungeon [y ][x ]!=9 :
                        self.map_grid_surface.set_at((x, y), (140, 140, 140, 160))
        if new_seen :
            for x ,y in new_seen :
                self.map_grid_surface.set_at((x, y), (140, 140, 140, 160))

    def draw_minimap (self ,bg ,view_rect ,new_seen ):

        view_left ,view_top ,view_w ,view_h =view_rect
        margin =20
        max_w =int (view_w *0.3 )
        max_h =int (view_h *0.3 )
        if max_w <=0 or max_h <=0 :
            return
        scale =min (max_w /DUNGEON_W ,max_h /DUNGEON_H )
        if scale <=0 :
            return
        map_w =max (1 ,int (DUNGEON_W *scale ))
        map_h =max (1 ,int (DUNGEON_H *scale ))
        self.update_minimap_grid (new_seen )
        if self.map_surface is None or self.map_surface_size !=(map_w ,map_h )or self.map_surface_scale !=scale :
            self.map_surface =pygame .Surface ((map_w ,map_h ),pygame .SRCALPHA )
            self.map_surface_scale =scale
            self.map_surface_size =(map_w ,map_h )
        self.map_surface =pygame .transform .scale (self.map_grid_surface ,(map_w ,map_h ))
        map_x =view_left +view_w -margin -map_w
        map_y =view_top +view_h -margin -map_h
        bg .blit (self.map_surface ,[map_x ,map_y ])
        marker =max (3 ,int (scale )+1 )
        for sx ,sy in self.map_stairs :
            mx =int (sx *scale )
            my =int (sy *scale )
            bg .fill ((255 ,255 ,255 ,200 ),[map_x +mx ,map_y +my ,marker ,marker ])
        px =int (self.pl_x *scale )
        py =int (self.pl_y *scale )
        bg .fill ((255 ,0 ,0 ,200 ),[map_x +px ,map_y +py ,marker ,marker ])

    def init_battle (self ):
        self.emy_skip_turn = False
        self.emy_typ =random .randint (0 ,EMY_APPEAR [self.floor -1 ])
        geta =((self.floor -1 )//90 )*(9 -self.emy_typ )*10 
        if self.emy_typ ==10 :
            self.emy_typ =22 
            geta =0 
        self.lev =random .randint (1 ,self.floor )
        self.imgEnemy =pygame .image .load (self.path +"/image/enemy"+str (self.emy_typ )+"_"+str ((self.floor -1 )//30 )+".png")
        self.emy_name =EMY_NAME [self.emy_typ ]
        self.emy_lifemax =int ((73 *(self.emy_typ +1 )+EMY_LIFE [self.emy_typ ])*(1.2 *((self.floor -1 )//30 )+1 ))+(self.lev -1 )*8 +geta *3 
        self.emy_life =self.emy_lifemax 
        self.emy_str =int (self.emy_lifemax /7 +EMY_STR [self.emy_typ ]*(0.5 *((self.floor -1 )//30 )+1 ))+geta 
        screen =pygame .display .get_surface ()
        screen_w ,screen_h =screen .get_size ()
        self.emy_x =screen_w //2 -self.imgEnemy .get_width ()//2 
        self.emy_y =1.4*screen_h //2 -self.imgEnemy .get_height () 

    def init_bossbattle (self ):
        self.emy_skip_turn = False
        base_typ =9 +int (self.floor //10 )
        if 90 <self.floor <100 :
            base_typ =9 +int (self.floor %10 )
        elif self.floor ==100 :
            base_typ =20 
        self.emy_typ =base_typ + self.change#10~
        geta =((self.floor -1 )//90 )*(19 -self.emy_typ )*30 
        self.imgEnemy =pygame .image .load (self.path +"/image/boss_"+str (self.emy_typ -9 )+".png")
        self.emy_name =EMY_NAME [self.emy_typ ]
        self.emy_lifemax =EMY_LIFE [self.emy_typ ]+geta *20 
        self.emy_life =self.emy_lifemax 
        self.emy_str =EMY_STR [self.emy_typ ]+geta 
        screen =pygame .display .get_surface ()
        screen_w ,screen_h =screen .get_size ()
        self.emy_x =screen_w //2 -self.imgEnemy .get_width ()//2 
        self.emy_y =1.4*screen_h //2 -self.imgEnemy .get_height ()

    def draw_bar (self ,bg ,x ,y ,w ,h ,val ,ma ):
        pygame .draw .rect (bg ,WHITE ,[x -2 ,y -2 ,w +4 ,h +4 ])
        pygame .draw .rect (bg ,BLACK ,[x ,y ,w ,h ])
        if val >0 :
            pygame .draw .rect (bg , SILVER, [x ,y ,w *val /ma ,h ])

    def draw_battle (self ,bg ,fnt ):
        bx =0 ;by =0 
        if self.dmg_eff >1 :
            self.dmg_eff =self.dmg_eff -1 
            bx =random .randint (-20 ,20 )
            by =random .randint (-10 ,10 )
        elif self.dmg_eff ==1 :
            bg.fill(BLACK)
            self.dmg_eff =self.dmg_eff -1 
        bg_rect =self.blit_scaled_bg (bg ,self.imgBtlBG ,bx ,by )
        self.btl_bg_rect =bg_rect
        bg_left =bg_rect [0 ]
        bg_top =bg_rect [1 ]
        bg_w =bg_rect [2 ]
        bg_h =bg_rect [3 ]
        W =300; H =530
        msg_x =bg_left +bg_w -10 -W
        msg_y =bg_top +50
        win =pygame .Surface ((W ,H ),pygame .SRCALPHA )
        win .fill ((0 ,0 ,0 ,100 ))
        bg .blit (win ,[msg_x ,msg_y ])
        if self.emy_life >0 and self.emy_blink %2 ==0 :
            bg .blit (self.imgEnemy ,[self.emy_x ,self.emy_y +self.emy_step])
        if self.burn_turns >0 :
            fx = self.emy_x + self.imgEnemy.get_width() - self.imgFire.get_width()
            fy = self.emy_y + self.emy_step - self.imgFire.get_height() // 2
            bg .blit (self.imgFire ,[fx ,fy ])
            self.draw_text (bg ,f"火傷",bg_left +40 ,bg_top +82 ,fnt ,WHITE )
        if self.pow_up >1 :
            self.draw_text (bg ,f"力↑",bg_left +40 ,bg_top +82 ,fnt ,WHITE )
        if self.emy_typ ==16 or self.emy_typ ==21 :
            self.draw_text (bg ,"Magia : "+str (self.madoka )+"/1000",bg_left +40 ,bg_top +82 ,fnt ,WHITE )
        self.draw_bar (bg ,bg_left +30 ,bg_top +60 ,200 ,10 ,self.emy_life ,self.emy_lifemax )
        if self.emy_blink >0 :
            self.emy_blink =self.emy_blink -1 
        para_x =bg_left +10
        para_h =140
        para_margin_bottom =15
        para_y =bg_top +bg_h -para_h -para_margin_bottom
        status_y =para_y -35
        if self.guard_remain >0 :
            self.draw_text (bg ,f"守護 {self.guard_remain}",para_x +30 ,status_y ,fnt ,WHITE )
        if self.poison >0 :
            self.draw_text (bg ,f"毒 {self.poison}",para_x +100 ,status_y ,fnt ,WHITE )
        for i in range (10 ):# 戦闘メッセージの表示
            self.draw_text (bg ,self.message [i ],msg_x +30 ,msg_y +40 +i *48 ,fnt ,WHITE )
        if self.boss ==0 :
            self.draw_text (bg ,f"{self.emy_name}  Lv.{self.lev}",bg_left +40 ,bg_top +30 ,fnt ,WHITE )
        else :
            self.draw_text (bg ,f"{self.emy_name}",bg_left +40 ,bg_top +30 ,fnt ,WHITE )
        self.draw_para (bg ,fnt ,bg_rect )# 主人公の能力を表示

    def menu_command (self ,bg ,fnt ,key ):
        ent =False 
        options = ["Save data", "Back to title", "Close menu"]
        if key [K_UP ]and self.menu_cmd >0 :
            self.menu_cmd -=1 
        if key [K_DOWN ]and self.menu_cmd <len (options )-1 :
            self.menu_cmd +=1 
        if key [K_RETURN ]or key [K_a ]:
            ent =True 
        win_w =360 
        line_h =32 
        win_h =line_h *len (options )+20 
        screen_w ,screen_h =bg .get_size ()
        win_x =(screen_w -win_w )//2 
        win_y =(screen_h -win_h )//2 
        pygame .draw .rect (bg ,BLACK ,[win_x ,win_y ,win_w ,win_h ])
        for i, label in enumerate (options ):
            y =win_y +10 +i *line_h 
            if self.menu_cmd ==i :
                self.draw_text (bg ,"▶",win_x +20 ,y ,fnt ,WHITE )
            self.draw_text (bg ,label ,win_x +50 ,y ,fnt ,WHITE )
        return ent 

    def save_command (self ,bg ,fnt ,key ):
        ent =False 
        if self.load_accept_lock:
            if not (key [K_RETURN ]or key [K_a ]):
                self.load_accept_lock = False
        SAVE =["data[1] : 地下 {}階".format (self.floorlist [0 ]),
        "data[2] : 地下 {}階".format (self.floorlist [1 ]),
        "data[3] : 地下 {}階".format (self.floorlist [2 ])]
        if key [K_1 ]:
            self.save_cmd =0 
            ent =True 
        if key [K_2 ]:
            self.save_cmd =1 
            ent =True 
        if key [K_3 ]:
            self.save_cmd =2 
            ent =True 
        if key [K_UP ]and self.save_cmd >0 :
            self.save_cmd -=1 
        if key [K_DOWN ]and self.save_cmd <2 :
            self.save_cmd +=1 
        if key [K_RETURN ]or key [K_a ]:
            if not self.load_accept_lock:
                ent =True
        win_w =360 
        line_h =32 
        win_h =line_h *len (SAVE )+20 
        screen_w ,screen_h =bg .get_size ()
        win_x =(screen_w -win_w )//2 
        win_y =(screen_h -win_h )//2 
        pygame .draw .rect (bg ,BLACK ,[win_x ,win_y ,win_w ,win_h ])
        for i, label in enumerate (SAVE ):
            y =win_y +10 +i *line_h 
            if self.save_cmd ==i :
                self.draw_text (bg ,"▶",win_x +20 ,y ,fnt ,WHITE )
            self.draw_text (bg ,label ,win_x +50 ,y ,fnt ,WHITE )
        return ent 

    def battle_command (self ,bg ,fnt ,key ):
        ent =False 
        labels = ["攻撃", "魔法", "傷薬", "爆弾", "守護", "逃走", "情報"]
        grid = [
            [0, 1, 5, 6],
            [2, 3, 4, None],
        ]
        if key [K_m ]:
            self.btl_cmd =1 
        if key [K_p ]:
            self.btl_cmd =2 
        if key [K_b ]:
            self.btl_cmd =3 
        if key [K_g ]:
            self.btl_cmd =4 
        if key [K_r ]:
            self.btl_cmd =5 
        if key [K_i ]:
            self.btl_cmd =6 
        row =0 
        col =0 
        for r, row_items in enumerate (grid ):
            for c, idx in enumerate (row_items ):
                if idx is not None and self.btl_cmd == idx:
                    row =r 
                    col =c 
                    break
        if key [K_UP ]:
            if row >0 :
                new_row =row -1 
                max_col =max (i for i, v in enumerate (grid [new_row ]) if v is not None )
                new_col =min (col ,max_col )
                while new_col >=0 and grid [new_row ][new_col ]is None:
                    new_col -=1 
                if new_col >=0 :
                    self.btl_cmd =grid [new_row ][new_col ]
        if key [K_DOWN ]:
            if row <len (grid )-1 :
                new_row =row +1 
                max_col =max (i for i, v in enumerate (grid [new_row ]) if v is not None )
                new_col =min (col ,max_col )
                while new_col >=0 and grid [new_row ][new_col ]is None:
                    new_col -=1 
                if new_col >=0 :
                    self.btl_cmd =grid [new_row ][new_col ]
        if key [K_LEFT ]:
            if col >0 :
                new_col =col -1 
                while new_col >=0 and grid [row ][new_col ]is None:
                    new_col -=1 
                if new_col >=0 :
                    self.btl_cmd =grid [row ][new_col ]
        if key [K_RIGHT ]:
            if col <len (grid [row ])-1 :
                new_col =col +1 
                while new_col <len (grid [row ]) and grid [row ][new_col ]is None:
                    new_col +=1 
                if new_col <len (grid [row ]):
                    self.btl_cmd =grid [row ][new_col ]
        if key [K_RETURN ]or key [K_a ]:
            ent =True 
        win_w =380
        line_h =32 
        win_h =line_h *len (grid )+20 
        if getattr (self ,"btl_bg_rect",None ):
            bg_left ,bg_top ,bg_w ,bg_h =self.btl_bg_rect
            win_x =bg_left +bg_w -80 -win_w 
            win_y =bg_top +bg_h -20 -win_h 
        else :
            win_x =420
            win_y =720 -win_h -20 
        pygame .draw .rect (bg ,BLACK ,[win_x ,win_y ,win_w ,win_h ])
        col_w =85
        for r, row_items in enumerate (grid ):
            y =win_y +12 +r *line_h 
            for c, idx in enumerate (row_items ):
                if idx is None:
                    continue
                arrow_x = win_x +20 +c *col_w 
                text_x =arrow_x +20 
                if self.btl_cmd == idx:
                    self.draw_text (bg ,"▶",arrow_x ,y ,fnt ,WHITE )
                self.draw_text (bg ,labels [idx ],text_x ,y ,fnt ,WHITE )
        return ent 

    def init_message (self ):
        for i in range (10 ):
            self.message [i ]=""

    def set_message (self ,msg ):
        for i in range (10 ):
            if self.message [i ]=="":
                self.message [i ]=msg 
                return 
        for i in range (9 ):
            self.message [i ]=self.message [i +1 ]
        self.message [9 ]=msg 

    def apply_armor_effects (self ):
        if self.pl_armor [0 ][0 ]==1 :
            if random .random ()>0.7 :
                cure =self.pl_armor [0 ][1 ]*2 -random .randint (0 ,self.pl_armor [0 ][1 ]//3 )
                self.pl_life =min (self.pl_life +cure ,self.pl_lifemax )
                self.set_message ("　鎧の癒し +{}" .format (cure ))
                self.se [2 ].play ()
            else :
                self.tmr =self.tmr +1 
        if self.pl_armor [1 ][0 ]==1 :
            if random .random ()>0.7 :
                mgup =int (10 +self.pl_armor [1 ][1 ]*0.7 +random .randint (0 ,self.pl_armor [1 ][1 ]//5 ))
                self.pl_mag =self.pl_mag +mgup 
                self.set_message ("　鎧の魔力 +{}" .format (mgup ))
                self.se [9 ].play ()
            else :
                self.tmr =self.tmr +1 

    def emy_action (self ,bg ):
        action =True 
        if self.emy_typ ==4 or self.emy_typ ==8 or self.emy_typ ==15 :
            self.pow_up =1 
            if random .random ()>0.7 :
                self.pow_up ={4:2 ,8:2 ,15:3 }[self.emy_typ ]
                self.set_message ("　敵は　力をためた!")
            action =False 
        if self.emy_typ ==5 or self.emy_typ ==12:
            suck = {5:5+self.lev, 12:104}[self.emy_typ] + random .randint (1 ,self.emy_typ )
            suck = min(suck, self.pl_mag)
            self.set_message (f"　MPを　{suck}　吸収された!")
            self.pl_mag =self.pl_mag -suck 
            action =False 
        if self.emy_typ ==6 :
            if random .random ()>0.5 :
                self.emy_life =0 #表示を消去
                self.idx =236 
                self.tmr =0 
            action =False 
        if self.emy_typ ==7 or self.boss_mode == "ice":
            cure = self.emy_lifemax //10 + random.randint (-self.emy_lifemax//100, self.emy_lifemax//100)
            cure += {7:0, 18:-3100}[self.emy_typ]
            self.set_message ("　敵の回復 +{}".format (int (min (cure ,self.emy_lifemax -self.emy_life ))))
            pygame .mixer .Sound (self.path +"/sound/ohd_se_potion.wav").play ()
            self.emy_life =min (self.emy_life +cure ,self.emy_lifemax )
            action =False 
        self.poison =max (self.poison -1 ,0 )
        if self.emy_typ ==11:
            if random .random ()>0.84:
                self.poison =2
                self.set_message ("　毒を喰らった!")
                action =False 
        if self.poison >0 :
            self.set_message (f"　毒 {self.poison *40}ダメージ！")
            self.pl_life =self.pl_life -self.poison *40 
            if self.pl_life <=0 :
                self.pl_life =0 
                self.idx =242 
                self.tmr =0
            action =False 
        return action 

    def run (self ):
        dmg =0 
        lif_p =0 
        str_p =0 

        pygame .init ()
        pygame .display .set_caption ("One hour Dungeon")
        screen =pygame .display .set_mode ((0 ,0 ),FULLSCREEN )
        clock =pygame .time .Clock ()
        font =self.get_font (25 )
        fontS =self.get_font (18 )

        se =load_sounds (self.path )# 効果音とジングル
        self.se = se

        while True :
            for event in pygame .event .get ():
                if event .type ==QUIT :
                    pygame .quit ()
                    sys .exit ()

            self.tmr =self.tmr +1 
            key =pygame .key .get_pressed ()
            accept = (key [K_RETURN ]and not self.prev_return )or (key [K_a ]and not self.prev_a )

            if self.idx ==0 :# タイトル画面
                if self.tmr ==1 :
                    pygame .mixer .music .load (self.path +"/sound/ohd_bgm_title.wav")
                    pygame .mixer .music .play (-1 )
                    self.title_mode = 0
                    self.title_cmd = 0
                screen .fill (BLACK )
                title_rect =self.blit_scaled_bg (screen ,self.imgTitle )
                if self.title_mode == 0:
                    options = ["はじめから", "つづきから"]
                    selected = self.title_cmd
                    if key [K_UP ]and self.title_cmd >0 :
                        self.title_cmd -=1 
                    if key [K_DOWN ]and self.title_cmd <len (options )-1 :
                        self.title_cmd +=1 
                    if accept:
                        if self.title_cmd ==0 :
                            self.prologue_input_lock = True
                            self.idx =10 
                            self.tmr =0 
                        else:
                            self.title_mode = 1
                else:
                    if key [K_b ]or key [K_LEFT ]:
                        self.title_mode = 0
                        options = ["はじめから", "つづきから"]
                        selected = self.title_cmd
                    else:
                        options = [
                            "data[1] : 地下 {}階".format (self.floorlist [0 ]),
                            "data[2] : 地下 {}階".format (self.floorlist [1 ]),
                            "data[3] : 地下 {}階".format (self.floorlist [2 ])
                        ]
                        selected = self.save_cmd
                        if key [K_UP ]and self.save_cmd >0 :
                            self.save_cmd -=1 
                        if key [K_DOWN ]and self.save_cmd <2 :
                            self.save_cmd +=1 
                        if accept:
                            self.load_game_data (self.save_cmd )
                rows = len (options )
                line_h =32 
                win_w =360 
                win_h =3 *line_h +20 
                screen_w =screen .get_size ()[0 ]
                win_x =(screen_w -win_w )//2 
                title_top =title_rect [1 ]
                title_h =title_rect [3 ]
                anchor_y =title_top +int (title_h *0.7 )
                win_y =anchor_y -win_h //2 
                title_win = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
                title_win.fill((0, 0, 0, 200))
                screen.blit(title_win, [win_x, win_y])
                for i, label in enumerate (options ):
                    y = int(win_y + win_h//2 - ((rows-1) *0.5)* line_h + i * line_h) - 10
                    x = win_x + win_w//2 - len(options[0])*0.5*6 - 30
                    if i == selected :
                        self.draw_text (screen ,"▶",x - 30 ,y ,fontS ,WHITE )
                    self.draw_text (screen ,label ,x ,y ,fontS ,WHITE )

            elif self.idx ==10 :# プロローグ
                self.draw_prologue (screen ,fontS ,key )

            elif self.idx ==20 :#データのロード
                screen .fill (BLACK )
                self.blit_scaled_bg (screen ,self.imgTitle )
                self.draw_text (screen ,"Choose load data.",320 ,200 ,font ,WHITE )
                self.draw_text (screen ,"[B]ack to title.",320 ,420 ,font ,WHITE )
                if key [K_b ]==1 :
                    self.idx =0 
                    self.tmr =2 
                if self.save_command (screen ,fontS ,key )==True :
                    with open (self.path +"/savedata/data{}.json".format (self.save_cmd +1 ),"r")as f :
                        loaddata =json .load (f )
                        self.floor =loaddata ["floor"]
                        if self.floor >0 :
                            self.dungeon =loaddata ["dungeon"]
                            self.pl_x =loaddata ["pl_x"]
                            self.pl_y =loaddata ["pl_y"]
                            self.pl_lifemax =loaddata ["pl_lifemax"]
                            self.pl_life =loaddata ["pl_life"]
                            self.pl_str =loaddata ["pl_str"]
                            self.pl_mag =loaddata ["pl_mag"]
                            self.pl_exp =loaddata ["pl_exp"]
                            self.potion =loaddata ["potion"]
                            self.blazegem =loaddata ["blazegem"]
                            self.guard =loaddata ["guard"]
                            self.idx =100 
                            self.pl_shield =loaddata ["shield"]
                            self.pl_armor =loaddata ["armor"]
                            self.pl_sword =loaddata ["sword"]
                            if "boss_pos" in loaddata and loaddata ["boss_pos"] is not None:
                                bx, by = loaddata ["boss_pos"]
                                self.boss_pos = (bx, by)
                                self.boss_area = {(bx, by), (bx + 1, by), (bx, by + 1), (bx + 1, by + 1)}
                            else:
                                self.boss_pos = None
                                self.boss_area = set()
                            if "item_wall_pos" in loaddata and loaddata ["item_wall_pos"] is not None:
                                ix, iy = loaddata ["item_wall_pos"]
                                self.item_wall_pos = (ix, iy)
                            else:
                                self.item_wall_pos = None
                            self.item_wall_used = bool(loaddata.get("item_wall_used", False))
                            self.item_wall_claimed = set(loaddata.get("item_wall_claimed", []))
                            if 91 <= self.floor <= 99 and self.item_wall_used:
                                self.item_wall_claimed.add(self.floor)
                            self.true_episode_heard = bool(loaddata.get("true_episode_heard", False))
                            if "event_wall_pos" in loaddata and loaddata ["event_wall_pos"] is not None:
                                ex, ey = loaddata ["event_wall_pos"]
                                self.event_wall_pos = (ex, ey)
                            else:
                                self.event_wall_pos = None
                            self.item_event_phase = 0
                            self.item_choice = 0
                            self.item_reward = None
                            self.item_event_kind = ""
                            self.item_talk_lines = []
                            self.item_talk_index = 0
                            self.item_talk_char_count = 0
                            self.item_talk_last_tick = pygame.time.get_ticks()
                            self.set_floor_assets_for_current_floor ()
                            if self.floor >= 91:
                                self.event_wall_pos = None
                                if self.item_wall_pos is None and self.wall_item:
                                    wall_cells = [
                                        (x, y)
                                        for y in range(DUNGEON_H - 1)
                                        for x in range(DUNGEON_W)
                                        if self.dungeon[y][x] == 9 and self.dungeon[y + 1][x] == 0
                                    ]
                                    if wall_cells:
                                        self.item_wall_pos = random.choice(wall_cells)
                            self.init_floor_variant_map ()
                            self.move_bgm_path =self.path +"/sound/bgm_"+str ((self.floor-1) //10 )+".wav"
                            self.move_bgm_pos_ms =0 
                            self.move_bgm_start_time =time .time ()
                            pygame .mixer .music .load (self.move_bgm_path )
                            pygame .mixer .music .play (-1 )

            elif self.idx ==30 :#メニュー
                self.draw_dungeon (screen ,fontS )
                if self.menu_back_lock:
                    if not (key [K_b ]or key [K_LEFT ]):
                        self.menu_back_lock = False
                if self.menu_accept_lock:
                    if not (key [K_RETURN ]or key [K_a ]):
                        self.menu_accept_lock = False
                if (key [K_b ]or key [K_LEFT ]) and not self.menu_back_lock:
                    self.idx =100 
                    self.tmr =0 
                else:
                    ent = self.menu_command (screen ,fontS ,key )
                    if self.menu_accept_lock:
                        ent = False
                    if ent == True :
                        if self.menu_cmd ==0 :#savedata
                            self.load_accept_lock = True
                            self.idx =40 
                        if self.menu_cmd ==1 :#go_title
                            self.confirm_cmd =0 
                            self.title_confirm_lock = True
                            self.idx =60 
                            self.tmr =0 
                        if self.menu_cmd ==2 :#close
                            self.idx =100 
                            self.tmr =0 

            elif self.idx ==40 :#セーブデータ選択
                self.draw_dungeon (screen ,fontS )
                if self.save_command (screen ,fontS ,key )==True :
                    self.confirm_cmd =0 
                    self.save_confirm_lock = True
                    self.idx =50 
                    self.tmr =0 
                if key [K_b ]==1 or key [K_LEFT ]==1 :
                    self.menu_back_lock = True
                    self.idx =30 

            elif self.idx ==50 :#確認とセーブ
                self.draw_dungeon (screen ,fontS )
                d ={
                "floor":self.floor ,
                "pl_lifemax":self.pl_lifemax ,
                "pl_life":self.pl_life ,
                "pl_mag":self.pl_mag ,
                "pl_str":self.pl_str ,
                "pl_exp":self.pl_exp ,
                "potion":self.potion ,
                "blazegem":self.blazegem ,
                "guard":self.guard ,
                "shield":self.pl_shield ,
                "armor":self.pl_armor ,
                "sword":self.pl_sword ,
                "dungeon":self.dungeon ,
                "pl_x":self.pl_x ,
                "pl_y":self.pl_y ,
                "boss_pos":self.boss_pos ,
                "item_wall_pos":self.item_wall_pos ,
                "item_wall_used":self.item_wall_used ,
                "item_wall_claimed":sorted(self.item_wall_claimed),
                "true_episode_heard":self.true_episode_heard,
                "event_wall_pos":self.event_wall_pos 
                }
                if self.floorlist [self.save_cmd ]>0 :
                    if self.save_confirm_lock:
                        if not (key [K_RETURN ]or key [K_a ]):
                            self.save_confirm_lock = False
                    options = ["Yes", "No"]
                    if key [K_UP ]and self.confirm_cmd >0 :
                        self.confirm_cmd -=1 
                    if key [K_DOWN ]and self.confirm_cmd <len (options )-1 :
                        self.confirm_cmd +=1 
                    confirm_yes = False
                    confirm_no = False
                    if key [K_y ]==1 :
                        confirm_yes = True
                    if key [K_n ]==1 :
                        confirm_no = True
                    if (key [K_RETURN ]or key [K_a ]) and not self.save_confirm_lock:
                        if self.confirm_cmd ==0 :
                            confirm_yes = True
                        else :
                            confirm_no = True
                    win_w =360 
                    line_h =32 
                    win_h =line_h *(len (options )+1 )+20 
                    screen_w ,screen_h =screen .get_size ()
                    win_x =(screen_w -win_w )//2 
                    win_y =(screen_h -win_h )//2 
                    pygame .draw .rect (screen ,BLACK ,[win_x ,win_y ,win_w ,win_h ])
                    self.draw_text (screen ,"上書きしますか？",win_x +30 ,win_y +10 ,fontS ,WHITE )
                    for i, label in enumerate (options ):
                        y =win_y +10 +line_h *(i +1 )
                        if self.confirm_cmd ==i :
                            self.draw_text (screen ,"▶",win_x +20 ,y ,fontS ,WHITE )
                        self.draw_text (screen ,label ,win_x +50 ,y ,fontS ,WHITE )
                    if confirm_yes :
                        with open (self.path +"/savedata/data{}.json".format (self.save_cmd +1 ),"w")as f :
                            json .dump (d ,f )
                        se [9 ].play ()
                        self.floorlist [self.save_cmd ]=self.floor 
                        self.load_accept_lock = True
                        self.idx =40 
                    if confirm_no :
                        self.load_accept_lock = True
                        self.idx =40 
                else :
                    with open (self.path +"/savedata/data{}.json".format (self.save_cmd +1 ),"w")as f :
                        json .dump (d ,f )
                    se [9 ].play ()
                    self.floorlist [self.save_cmd ]=self.floor 
                    self.load_accept_lock = True
                    self.idx =40 

            elif self.idx ==60 :#タイトルへ
                self.draw_dungeon (screen ,fontS )
                options = ["Yes", "No"]
                msg_lines = [
                    "セーブしていないデータは",
                    "消えてしまいますが、",
                    "タイトル画面に戻りますか？",
                ]
                if self.title_confirm_lock:
                    if not (key [K_RETURN ]or key [K_a ]):
                        self.title_confirm_lock = False
                if key [K_UP ]and self.confirm_cmd >0 :
                    self.confirm_cmd -=1 
                if key [K_DOWN ]and self.confirm_cmd <len (options )-1 :
                    self.confirm_cmd +=1 
                if key [K_LEFT ]or key [K_b ]:
                    self.menu_back_lock = True
                    self.idx =30 
                    self.tmr =0 
                if (key [K_RETURN ]or key [K_a ]) and not self.title_confirm_lock:
                    if self.confirm_cmd ==0 :
                        pygame .mixer .music .stop ()
                        self.idx =0 
                        self.tmr =0 
                    else :
                        self.menu_accept_lock = True
                        self.idx =30 
                        self.tmr =0 
                win_w =360 
                line_h =32 
                win_h =line_h *(len (options )+len (msg_lines ))+20 
                screen_w ,screen_h =screen .get_size ()
                win_x =(screen_w -win_w )//2 
                win_y =(screen_h -win_h )//2 
                pygame .draw .rect (screen ,BLACK ,[win_x ,win_y ,win_w ,win_h ])
                for i, line in enumerate (msg_lines ):
                    y =win_y +10 +i *line_h 
                    self.draw_text (screen ,line ,win_x +20 ,y ,fontS ,WHITE )
                base_y =win_y +10 +line_h *len (msg_lines )
                for i, label in enumerate (options ):
                    y =base_y +i *line_h 
                    if self.confirm_cmd ==i :
                        self.draw_text (screen ,"▶",win_x +20 ,y ,fontS ,WHITE )
                    self.draw_text (screen ,label ,win_x +50 ,y ,fontS ,WHITE )

            elif self.idx ==70 :# ゲームオーバー
                if self.tmr <=30 :
                    PL_TURN =[2 ,4 ,0 ,6 ]
                    self.pl_a =PL_TURN [self.tmr %4 ]
                    if self.tmr ==30 :self.pl_a =8 # 倒れた絵
                    self.draw_dungeon (screen ,fontS )
                elif self.tmr ==31 :
                    se [3 ].play ()
                    self.draw_text (screen ,"君は　死んでしまった。",340 ,240 ,font ,RED )
                elif self.tmr ==100 :
                    self.idx =0 
                    self.tmr =0 


            elif self.idx ==80 :#ゲームクリア画面１
                if self.tmr ==1 :
                    pygame .mixer .music .load (self.path +"/sound/bgm_last.wav")
                    pygame .mixer .music .play (-1 )
                screen .fill (BLACK )
                if self.tmr >=40 :
                    self.draw_text (screen ,"Congratulations!",320 ,630 ,font ,WHITE )
                    self.imgEnemy =pygame .image .load (self.path +"/image/enemy"+str (int (0.1 *(self.tmr -40 )%10 ))+"_0"+".png")
                    screen_w ,screen_h =screen .get_size ()
                    self.emy_x =screen_w //2 -self.imgEnemy .get_width ()//2 
                    self.emy_y =screen_h //2 -self.imgEnemy .get_height ()//2 
                    screen .blit (self.imgEnemy ,[self.emy_x ,self.emy_y ])
                if self.tmr >=80 :
                    self.draw_text (screen ,"Press space key",320 ,580 ,font ,BLINK [self.tmr %6 ])
                    if key [K_SPACE ]==1 :
                        self.idx =81 
                        self.tmr =0 
                        time .sleep (1 )

            elif self.idx ==81 :#ゲームクリア画面２
                screen .fill (BLACK )
                if self.tmr >=10 :
                    self.draw_text (screen ,"Thank you for playing!",260 ,100 ,font ,WHITE )
                if self.tmr >=30 :
                    self.draw_text (screen ,"This is my first game.",260 ,150 ,font ,WHITE )
                if self.tmr >=50 :
                    self.draw_text (screen ,"Making game was one of my dream,",260 ,200 ,font ,WHITE )
                if self.tmr >=70 :
                    self.draw_text (screen ,"so I'm very happy.",260 ,250 ,font ,WHITE )
                if self.tmr >=90 :
                    self.draw_text (screen ,"If I make another game",260 ,300 ,font ,WHITE )
                if self.tmr >=110 :
                    self.draw_text (screen ,"in the future,",260 ,350 ,font ,WHITE )
                if self.tmr >=130 :
                    self.draw_text (screen ,"please play it.",260 ,400 ,font ,WHITE )
                if self.tmr >=150 :
                    self.draw_text (screen ,"See you again.",260 ,450 ,font ,WHITE )
                if self.tmr >=170 :
                    self.draw_text (screen ,"Koyo",520 ,500 ,font ,WHITE )
                if self.tmr >=200 :
                    self.draw_text (screen ,"Press space key",320 ,560 ,font ,BLINK [self.tmr %6 ])
                    if key [K_SPACE ]==1 :
                        self.idx =0 
                        self.tmr =0 
                        time .sleep (1 )

            elif self.idx ==82 :# エピローグ
                if self.draw_epilogue (screen ,fontS ,key ):
                    self.idx =83 
                    self.tmr =0 

            elif self.idx ==83 :# エンドロール
                if self.draw_end_roll (screen ,fontS ,key ):
                    self.idx =0 
                    self.tmr =0 

            elif self.idx ==100 :# プレイヤーの移動
                self.move_player (key )
                self.draw_dungeon (screen ,fontS )
                view_rect =getattr (self ,"dungeon_view_rect",None )
                if view_rect :
                    view_left ,view_top ,view_w ,view_h =view_rect
                else :
                    view_left =0 
                    view_top =0 
                    view_w ,view_h =screen .get_size ()
                self.draw_text (screen ,"地下 {}階".format (self.floor),view_left +60 ,view_top +40 ,fontS ,WHITE )
                menu_label ="[M]enu "
                menu_x =view_left +view_w -int (view_w *0.1 )-fontS .size (menu_label )[0 ]
                self.draw_text (screen ,menu_label ,menu_x ,view_top +40 ,fontS ,WHITE )
                if accept and self.event_wall_pos:
                    if self.pl_d == 0 and (self.pl_x, self.pl_y - 1) == self.event_wall_pos:
                        self.init_event_talk ()
                        self.idx =132 
                        self.tmr =0 
                if accept and self.item_wall_pos and not self.item_wall_used:
                    if self.pl_d == 0 and (self.pl_x, self.pl_y - 1) == self.item_wall_pos:
                        if self.floor >= 91 and not self.all_cocoons_cleared():
                            pass
                        else:
                            if self.floor >= 91:
                                if self.floor == 100 and self.all_item_walls_claimed() and not self.true_episode_heard:
                                    self.init_item_event (kind="true_episode", lines=TRUE_EPISODE_TALK)
                                else:
                                    self.init_item_event (kind="item", reward_count=5)
                            else:
                                self.init_item_event ()
                            self.idx =131 
                            self.tmr =0 
                if accept and self.stair_in_front ():
                    self.idx =110 
                    self.tmr =0 
                if accept and self.boss_in_front ():
                    self.init_boss_talk ()
                    self.idx =130 
                    self.tmr =0 
                    self.boss =1 

            elif self.idx ==110 :# 画面切り替え
                self.draw_dungeon (screen ,fontS )
                if self.tmr == 1:
                    disp_floor =self.floor +1 
                    x = win_x + win_w//2 - 42
                    y = title_top +int (title_h *0.4 )
                if 1 <=self.tmr and self.tmr <=5 :
                    alpha =int (255 *self.tmr /5 )
                    fade =pygame .Surface (screen .get_size (),pygame .SRCALPHA )
                    fade .fill ((0 ,0 ,0 ,alpha ))
                    screen .blit (fade ,[0 ,0 ])
                if self.tmr ==5 :
                    self.floor =self.floor +1 
                    if self.floor %10 ==1 :
                        self.set_floor_assets_for_transition (self.floor )
                        self.move_bgm_path =self.path +"/sound/bgm_"+str ((self.floor-1) //10 )+".wav"
                        self.move_bgm_pos_ms =0 
                        self.move_bgm_start_time =time .time ()
                        pygame .mixer .music .load (self.move_bgm_path )
                        pygame .mixer .music .play (-1 )
                    self.make_dungeon ()
                    self.put_event ()
                if 6 <=self.tmr and self.tmr <=9 :
                    fade =pygame .Surface (screen .get_size (),pygame .SRCALPHA )
                    fade .fill ((0 ,0 ,0 ,255 ))
                    screen .blit (fade ,[0 ,0 ])
                if 10 <=self.tmr and self.tmr <=13 :
                    alpha =int (255 *(14 -self.tmr )/4 )
                    fade =pygame .Surface (screen .get_size (),pygame .SRCALPHA )
                    fade .fill ((0 ,0 ,0 ,alpha ))
                    screen .blit (fade ,[0 ,0 ])
                self.draw_text (screen ,f"地下 {disp_floor}階" ,x ,y ,font ,WHITE )
                if self.tmr ==14 :
                    self.idx =100 

            elif self.idx ==120 :# アイテム入手もしくはトラップ
                self.draw_dungeon (screen ,fontS )
                if self.tmr ==1 :
                    x = win_x + win_w//2 - 42
                    y = title_top +int (title_h *0.4 )
                screen .blit (self.imgItem [self.treasure ],[x ,y-10 ])
                self.draw_text (screen ,TRE_NAME [self.treasure ],x+60 ,y ,font ,WHITE )
                if self.tmr ==10 :
                    self.idx =100 

            elif self.idx ==121 :# 武器入手もしくはダメージ床
                self.draw_dungeon (screen ,fontS )
                if self.tmr ==1 :
                    x = win_x + win_w//2 - 42
                    y = title_top +int (title_h *0.4 )
                if self.trap ==0 :
                    self.draw_text (screen ,TRAP_NAME [self.trap ]+" {}".format (30 -10 *((self.floor -1 )//10 )),x ,y ,font ,WHITE )
                elif self.trap ==1 :
                    self.draw_text (screen ,TRAP_NAME [self.trap ]+" +{}".format (-20 +10 *((self.floor -1 )//10 )),x ,y ,font ,WHITE )
                else :
                    self.draw_text (screen ,TRAP_NAME [self.trap ]+" Lv. "+str (self.wpn_lev ),x ,y ,font ,WHITE )
                if self.tmr ==10 :
                    self.idx =100 

            elif self.idx ==130 :# ボス会話
                self.draw_dungeon (screen ,fontS )
                view_rect =getattr (self ,"dungeon_view_rect",None )
                if view_rect :
                    view_left ,view_top ,view_w ,view_h =view_rect
                else :
                    view_left =0 
                    view_top =0 
                    view_w ,view_h =screen .get_size ()
                scale_x =view_w /880 
                scale_y =view_h /720 
                dlg_x =view_left +int (40 *scale_x )
                dlg_y =view_top +int (520 *scale_y )
                dlg_w =max (1 ,int (800 *scale_x ))
                dlg_h =max (1 ,int (160 *scale_y ))
                text_x =view_left +int (60 *scale_x )
                text_y =view_top +int (560 *scale_y )
                line_h =max (1 ,int (28 *scale_y ))
                prompt_x =view_left +int (700 *scale_x )
                prompt_y =view_top +int (640 *scale_y )
                pygame .draw .rect (screen ,BLACK ,[dlg_x ,dlg_y ,dlg_w ,dlg_h ])
                pygame .draw .rect (screen ,WHITE ,[dlg_x ,dlg_y ,dlg_w ,dlg_h ],2 )
                if self.boss_talk_index <len (self.boss_talk_lines ):
                    line = self.boss_talk_lines [self.boss_talk_index ]
                    now = pygame.time.get_ticks()
                    if self.boss_talk_char_count < len(line) and now - self.boss_talk_last_tick >= 100:
                        self.boss_talk_char_count += 1
                        self.boss_talk_last_tick = now
                    visible = line [:self.boss_talk_char_count ]
                    parts = visible.split("\n")
                    for i, part in enumerate(parts):
                        self.draw_text (screen ,part ,text_x ,text_y + i *line_h ,fontS ,WHITE )
                self.draw_text (screen ,"[A]/[Enter]",prompt_x ,prompt_y ,fontS ,WHITE )
                if accept:
                    if self.boss_talk_index <len (self.boss_talk_lines ):
                        line = self.boss_talk_lines [self.boss_talk_index ]
                        if self.boss_talk_char_count < len(line):
                            self.boss_talk_char_count = len(line)
                        else:
                            if self.floor ==40 and self.boss_talk_index ==0 :
                                se [2 ].play ()
                                self.pl_life =self.pl_lifemax 
                            self.boss_talk_index +=1 
                            self.boss_talk_char_count = 0
                            self.boss_talk_last_tick = pygame.time.get_ticks()
                    if self.boss_talk_index >=len (self.boss_talk_lines ):
                        self.idx =200 
                        self.tmr =0 

            elif self.idx ==133 :# ラスボス会話
                self.draw_dungeon (screen ,fontS )
                view_rect =getattr (self ,"dungeon_view_rect",None )
                if view_rect :
                    view_left ,view_top ,view_w ,view_h =view_rect
                else :
                    view_left =0 
                    view_top =0 
                    view_w ,view_h =screen .get_size ()
                scale_x =view_w /880 
                scale_y =view_h /720 
                dlg_x =view_left +int (40 *scale_x )
                dlg_y =view_top +int (520 *scale_y )
                dlg_w =max (1 ,int (800 *scale_x ))
                dlg_h =max (1 ,int (160 *scale_y ))
                text_x =view_left +int (60 *scale_x )
                text_y =view_top +int (560 *scale_y )
                line_h =max (1 ,int (28 *scale_y ))
                prompt_x =view_left +int (700 *scale_x )
                prompt_y =view_top +int (640 *scale_y )
                pygame .draw .rect (screen ,BLACK ,[dlg_x ,dlg_y ,dlg_w ,dlg_h ])
                pygame .draw .rect (screen ,WHITE ,[dlg_x ,dlg_y ,dlg_w ,dlg_h ],2 )
                if self.boss_talk_index <len (self.boss_talk_lines ):
                    line = self.boss_talk_lines [self.boss_talk_index ]
                    now = pygame.time.get_ticks()
                    if self.boss_talk_char_count < len(line) and now - self.boss_talk_last_tick >= 100:
                        self.boss_talk_char_count += 1
                        self.boss_talk_last_tick = now
                    visible = line [:self.boss_talk_char_count ]
                    parts = visible.split("\n")
                    for i, part in enumerate(parts):
                        self.draw_text (screen ,part ,text_x ,text_y + i *line_h ,fontS ,WHITE )
                self.draw_text (screen ,"[A]/[Enter]",prompt_x ,prompt_y ,fontS ,WHITE )
                if accept:
                    if self.boss_talk_index <len (self.boss_talk_lines ):
                        line = self.boss_talk_lines [self.boss_talk_index ]
                        if self.boss_talk_char_count < len(line):
                            self.boss_talk_char_count = len(line)
                        else:
                            self.boss_talk_index +=1 
                            self.boss_talk_char_count = 0
                            self.boss_talk_last_tick = pygame.time.get_ticks()
                    if self.boss_talk_index >=len (self.boss_talk_lines ):
                        if self.last_talk_mode == 2:
                            self.idx =82 
                        else:
                            self.idx =80 
                        self.tmr =0 

            elif self.idx ==131 :# itemWallイベント
                self.draw_dungeon (screen ,fontS )
                view_rect =getattr (self ,"dungeon_view_rect",None )
                if view_rect :
                    view_left ,view_top ,view_w ,view_h =view_rect
                else :
                    view_left =0 
                    view_top =0 
                    view_w ,view_h =screen .get_size ()
                scale_x =view_w /880 
                scale_y =view_h /720 
                dlg_x =view_left +int (40 *scale_x )
                dlg_y =view_top +int (525 *scale_y )
                dlg_w =max (1 ,int (800 *scale_x ))
                dlg_h =max (1 ,int (160 *scale_y ))
                text_x =view_left +int (60 *scale_x )
                text_y =view_top +int (560 *scale_y )
                line_h =max (1 ,int (28 *scale_y ))
                prompt_x =view_left +int (700 *scale_x )
                prompt_y =view_top +int (640 *scale_y )
                dialog_alpha = 255
                if self.item_event_phase == 1:
                    dialog_alpha = 100
                dialog = pygame.Surface((dlg_w, dlg_h), pygame.SRCALPHA)
                dialog.fill((0, 0, 0, dialog_alpha))
                screen.blit(dialog, [dlg_x, dlg_y])
                pygame .draw .rect (screen ,WHITE ,[dlg_x ,dlg_y ,dlg_w ,dlg_h ],2 )
                if self.item_event_kind == "true_episode":
                    if self.item_talk_index <len (self.item_talk_lines ):
                        line = self.item_talk_lines [self.item_talk_index ]
                        now = pygame.time.get_ticks()
                        if self.item_talk_char_count < len(line) and now - self.item_talk_last_tick >= 100:
                            self.item_talk_char_count += 1
                            self.item_talk_last_tick = now
                        visible = line [:self.item_talk_char_count ]
                        parts = visible.split("\n")
                        for i, part in enumerate(parts):
                            self.draw_text (screen ,part ,text_x ,text_y + i *line_h ,fontS ,WHITE )
                    self.draw_text (screen ,"[A]/[Enter]",prompt_x ,prompt_y ,fontS ,WHITE )
                    if accept:
                        if self.item_talk_index <len (self.item_talk_lines ):
                            line = self.item_talk_lines [self.item_talk_index ]
                            if self.item_talk_char_count < len(line):
                                self.item_talk_char_count = len(line)
                            else:
                                self.item_talk_index +=1 
                                self.item_talk_char_count = 0
                                self.item_talk_last_tick = pygame.time.get_ticks()
                        if self.item_talk_index >=len (self.item_talk_lines ):
                            self.true_episode_heard = True
                            self.init_item_event (kind="item", reward_count=5)
                elif self.item_event_kind == "weapon":
                    if self.item_event_phase == 0:
                        if self.item_talk_index <len (self.item_talk_lines ):
                            line = self.item_talk_lines [self.item_talk_index ]
                            now = pygame.time.get_ticks()
                            if self.item_talk_char_count < len(line) and now - self.item_talk_last_tick >= 100:
                                self.item_talk_char_count += 1
                                self.item_talk_last_tick = now
                            visible = line [:self.item_talk_char_count ]
                            parts = visible.split("\n")
                            for i, part in enumerate(parts):
                                self.draw_text (screen ,part ,text_x ,text_y + i *line_h ,fontS ,WHITE )
                        self.draw_text (screen ,"[A]/[Enter]",prompt_x ,prompt_y ,fontS ,WHITE )
                        if accept:
                            if self.item_talk_index <len (self.item_talk_lines ):
                                line = self.item_talk_lines [self.item_talk_index ]
                                if self.item_talk_char_count < len(line):
                                    self.item_talk_char_count = len(line)
                                else:
                                    self.item_talk_index +=1 
                                    self.item_talk_char_count = 0
                                    self.item_talk_last_tick = pygame.time.get_ticks()
                            if self.item_talk_index >=len (self.item_talk_lines ):
                                self.item_event_phase = 1
                    elif self.item_event_phase == 1:
                        w_a =WEP_APPEAR [(self.floor -1 )//10 ]
                        options = list(range(2, 4 + w_a + 1))
                        if self.item_choice >= len(options):
                            self.item_choice = max(0, len(options) - 1)
                        sel_line_h =max (1 ,int (22 *scale_y ))
                        box_h =max (1 ,int (15 *scale_y ))+sel_line_h *len (options )
                        box_w =max (1 ,int (280 *scale_x ))
                        box_x =view_left +int (520 *scale_x )
                        box_y =view_top +int (505 *scale_y )-box_h
                        arrow_x =view_left +int (540 *scale_x )
                        text_sel_x =view_left +int (560 *scale_x )
                        arrow_y =view_top +int (513 *scale_y )
                        pygame .draw .rect (screen ,BLACK ,[box_x ,box_y ,box_w ,box_h ])
                        pygame .draw .rect (screen ,WHITE ,[box_x ,box_y ,box_w ,box_h ],2 )
                        for i, trap_id in enumerate(options):
                            if i == self.item_choice:
                                self.draw_text (screen ,"▶",arrow_x ,arrow_y + i *sel_line_h -box_h ,fontS ,WHITE )
                            self.draw_text (screen ,TRAP_NAME [trap_id ],text_sel_x ,arrow_y + i *sel_line_h -box_h,fontS ,WHITE )
                        if key [K_UP ]and self.item_choice >0 :
                            self.item_choice -=1 
                        if key [K_DOWN ]and self.item_choice <len (options )-1 :
                            self.item_choice +=1 
                        if accept:
                            self.item_reward = options [self.item_choice ]
                            self.trap = self.item_reward
                            self.wpn_lev = self.floor
                            if self.trap %3 ==2 :
                                if self.pl_shield [(w_a +2 )//3 ][0 ]==0 :
                                    self.trap =2 +3 *((w_a +2 )//3 )
                                self.pl_shield [self.trap //3 ][0 ]=1 
                                self.pl_shield [self.trap //3 ][1 ]=max (self.wpn_lev ,self.pl_shield [self.trap //3 ][1 ])
                            if self.trap %3 ==0 :
                                if self.pl_armor [(w_a +1 )//3 ][0 ]==0 :
                                    self.trap =3 +3 *((w_a +1 )//3 )
                                self.pl_armor [self.trap //3 -1 ][0 ]=1 
                                self.pl_armor [self.trap //3 -1 ][1 ]=max (self.wpn_lev ,self.pl_armor [self.trap //3 -1 ][1 ])
                            if self.trap %3 ==1 :
                                if self.pl_sword [(w_a )//3 ][0 ]==0 :
                                    self.trap =4 +3 *((w_a )//3 )
                                self.pl_sword [self.trap //3 -1 ][0 ]=1 
                                self.pl_sword [self.trap //3 -1 ][1 ]=max (self.wpn_lev ,self.pl_sword [self.trap //3 -1 ][1 ])
                            self.item_wall_used = True
                            self.idx =121
                            self.tmr =0
                else:
                    if self.item_event_phase in (0, 2):
                        if self.item_talk_index <len (self.item_talk_lines ):
                            line = self.item_talk_lines [self.item_talk_index ]
                            now = pygame.time.get_ticks()
                            if self.item_talk_char_count < len(line) and now - self.item_talk_last_tick >= 100:
                                self.item_talk_char_count += 1
                                self.item_talk_last_tick = now
                            visible = line [:self.item_talk_char_count ]
                            parts = visible.split("\n")
                            for i, part in enumerate(parts):
                                self.draw_text (screen ,part ,text_x ,text_y + i *line_h ,fontS ,WHITE )
                        self.draw_text (screen ,"[A]/[Enter]",prompt_x ,prompt_y ,fontS ,WHITE )
                        if accept:
                            if self.item_talk_index <len (self.item_talk_lines ):
                                line = self.item_talk_lines [self.item_talk_index ]
                                if self.item_talk_char_count < len(line):
                                    self.item_talk_char_count = len(line)
                                else:
                                    self.item_talk_index +=1 
                                    self.item_talk_char_count = 0
                                    self.item_talk_last_tick = pygame.time.get_ticks()
                            if self.item_talk_index >=len (self.item_talk_lines ):
                                if self.item_event_phase == 0:
                                    self.item_event_phase = 1
                                elif self.item_event_phase == 2:
                                    self.item_wall_used = True
                                    self.treasure = self.item_reward if self.item_reward is not None else self.item_choice                            
                                    if 91 <= self.floor <= 99:
                                        self.item_wall_claimed.add(self.floor)
                                    self.idx =120
                        self.tmr =0 
                    elif self.item_event_phase == 1:
                        options = ["傷薬", "爆弾", "守護"]
                        sel_line_h =max (1 ,int (25 *scale_y ))
                        box_h =max (1 ,int (15 *scale_y ))+sel_line_h *len (options )
                        box_w =max (1 ,int (280 *scale_x ))
                        box_x =view_left +int (520 *scale_x )
                        box_y =view_top +int (420 *scale_y )
                        arrow_x =view_left +int (540 *scale_x )
                        text_sel_x =view_left +int (560 *scale_x )
                        arrow_y =view_top +int (435 *scale_y )
                        pygame .draw .rect (screen ,BLACK ,[box_x ,box_y ,box_w ,box_h ])
                        pygame .draw .rect (screen ,WHITE ,[box_x ,box_y ,box_w ,box_h ],2 )
                        for i, option in enumerate(options):
                            if i == self.item_choice:
                                self.draw_text (screen ,"▶",arrow_x ,arrow_y + i *sel_line_h ,fontS ,WHITE )
                            self.draw_text (screen ,option ,text_sel_x ,arrow_y + i *sel_line_h ,fontS ,WHITE )
                        if key [K_UP ]and self.item_choice >0 :
                            self.item_choice -=1 
                        if key [K_DOWN ]and self.item_choice <2 :
                            self.item_choice +=1 
                        if accept and self.item_reward is None:
                            self.item_reward = self.item_choice
                        if self.item_reward is not None:
                            if self.item_reward ==0 :
                                self.potion =self.potion +self.item_reward_count
                            if self.item_reward ==1 :
                                self.blazegem =self.blazegem +self.item_reward_count
                            if self.item_reward ==2 :
                                self.guard =self.guard +self.item_reward_count
                            self.item_talk_lines = ["よろしい。そなたに差し上げます。\n神のお恵みを"]
                            self.item_talk_index = 0
                            self.item_talk_char_count = 0
                            self.item_talk_last_tick = pygame.time.get_ticks()
                            self.item_event_phase = 2

            elif self.idx ==132 :# eventWall会話
                self.draw_dungeon (screen ,fontS )
                view_rect =getattr (self ,"dungeon_view_rect",None )
                if view_rect :
                    view_left ,view_top ,view_w ,view_h =view_rect
                else :
                    view_left =0 
                    view_top =0 
                    view_w ,view_h =screen .get_size ()
                scale_x =view_w /880 
                scale_y =view_h /720 
                dlg_x =view_left +int (40 *scale_x )
                dlg_y =view_top +int (520 *scale_y )
                dlg_w =max (1 ,int (800 *scale_x ))
                dlg_h =max (1 ,int (160 *scale_y ))
                text_x =view_left +int (60 *scale_x )
                text_y =view_top +int (560 *scale_y )
                line_h =max (1 ,int (28 *scale_y ))
                prompt_x =view_left +int (700 *scale_x )
                prompt_y =view_top +int (640 *scale_y )
                pygame .draw .rect (screen ,BLACK ,[dlg_x ,dlg_y ,dlg_w ,dlg_h ])
                pygame .draw .rect (screen ,WHITE ,[dlg_x ,dlg_y ,dlg_w ,dlg_h ],2 )
                if self.event_talk_index <len (self.event_talk_lines ):
                    line = self.event_talk_lines [self.event_talk_index ]
                    now = pygame.time.get_ticks()
                    if self.event_talk_char_count < len(line) and now - self.event_talk_last_tick >= 100:
                        self.event_talk_char_count += 1
                        self.event_talk_last_tick = now
                    visible = line [:self.event_talk_char_count ]
                    parts = visible.split("\n")
                    for i, part in enumerate(parts):
                        self.draw_text (screen ,part ,text_x ,text_y + i *line_h ,fontS ,WHITE )
                self.draw_text (screen ,"[A]/[Enter]",prompt_x ,prompt_y ,fontS ,WHITE )
                if accept:
                    if self.event_talk_index <len (self.event_talk_lines ):
                        line = self.event_talk_lines [self.event_talk_index ]
                        if self.event_talk_char_count < len(line):
                            self.event_talk_char_count = len(line)
                        else:
                            self.event_talk_index +=1 
                            self.event_talk_char_count = 0
                            self.event_talk_last_tick = pygame.time.get_ticks()
                    if self.event_talk_index >=len (self.event_talk_lines ):
                        self.idx =100 
                        self.tmr =0 


            elif self.idx ==200 :# 戦闘開始
                if self.tmr ==1 :
                    if self.move_bgm_path :
                        now =time .time ()
                        self.move_bgm_pos_ms =int ((now -self.move_bgm_start_time )*1000 )
                    bg_idx = (self.floor - 1) // 10
                    self.imgBtlBG =pygame .image .load (self.path +"/image/btlbg{}.png".format (bg_idx ))
                    if self.boss ==1 :
                        self.init_bossbattle ()
                        pygame .mixer .music .load (self.path +"/sound/bgm_battle_1.wav")
                        pygame .mixer .music .play (-1 )
                        self.init_message ()
                        if self.emy_typ ==16 :
                            self.madoka =0 
                    else :
                        self.init_battle ()
                        pygame .mixer .music .load (self.path +"/sound/bgm_battle_0.wav")
                        pygame .mixer .music .play (-1 )
                        self.init_message ()
                    self.set_message (f"{self.emy_name}が　あらわれた！")
                elif self.tmr <=4 :
                    alpha =int (255 *self.tmr /4 )
                    bg_rect =self.blit_scaled_bg (screen ,self.imgBtlBG ,0 ,0 ,True ,alpha )
                    self.btl_bg_rect =bg_rect
                    self.draw_para (screen ,fontS ,bg_rect )
                elif self.tmr <=16 :
                    self.draw_battle (screen ,fontS )
                else :
                    self.idx =210 
                    self.tmr =0 
                    

            elif self.idx ==210 :# プレイヤーのターン（入力待ち）
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.set_message ("プレイヤーのターン")
                    self.guard_remain =max (self.guard_remain -1 ,0 )
                if self.battle_command (screen ,fontS ,key )==True :
                    if self.btl_cmd ==0 :#Attack
                        self.idx =220 
                        self.tmr =0 
                    if self.btl_cmd ==1 and self.pl_mag >100 :#Magic
                        self.idx =221 
                        self.tmr =0 
                    if self.btl_cmd ==2 and self.potion >0 :#Potion
                        self.idx =222 
                        self.tmr =0 
                    if self.btl_cmd ==3 and self.blazegem >0 :#Blaze gem
                        self.idx =223 
                        self.tmr =0 
                    if self.btl_cmd ==4 and self.guard >0 :#Guard
                        self.idx =224 
                        self.tmr =0 
                    if self.btl_cmd ==5 :#Run
                        self.idx =240 
                        self.tmr =0 
                    if self.btl_cmd ==6 :#Info
                        self.idx =225 
                        self.tmr =0 

            elif self.idx ==220 :# プレイヤーの攻撃
                self.draw_battle (screen ,fontS )
                cri =0 
                if self.tmr ==1 :
                    self.set_message (f"　{self.emy_name}に　攻撃！")
                    se [0 ].play ()
                    if self.pl_sword [0 ][0 ]==1 :
                        if random .random ()>0.7 :
                            cri =1 
                            self.set_message ("　クリティカルヒット！")
                    dmg =self.pl_str +random .randint (0 ,9 )-EMY_APRO [self.emy_typ ]
                    dmg =int (dmg *(1 +0.01 *cri *self.pl_sword [0 ][1 ]))+2 *self.pl_sword [0 ][1 ]+self.pl_sword [2 ][1 ]
                    dmg =max (1 +cri ,int (dmg /(2 *self.poison +1 )))
                    if self.emy_typ ==8 or self.emy_typ ==10 :
                        if random .random ()>0.7 :
                            self.set_message ("　攻撃は　防御された！")
                            dmg =int (dmg /2 )
                    if self.guard_remain >0 and self.emy_typ ==20 :
                        dmg =int (dmg *(0.35 -self.pl_shield [2 ][1 ]*0.002 ))
                if 2 <=self.tmr <=4 :
                    screen_w =screen .get_size ()[0 ]
                    eff_x =screen_w //2 +260 -self.tmr *120 
                    eff_y =-100 +self.tmr *120 
                    screen .blit (self.imgEffect [0 ],[eff_x ,eff_y ])
                if self.tmr ==5 :
                    self.emy_blink =5 
                    self.set_message (f"　{dmg}　ダメージ！")
                if self.tmr ==11 :
                    self.emy_life =self.emy_life -dmg 
                    if self.emy_life <=0 :
                        self.emy_life =0 
                        self.idx =241 
                        self.tmr =0
                if self.tmr ==12 :
                    if self.emy_typ ==18 :
                        self.boss_mode = "normal"
                    if self.burn_turns >0 :
                        se [0 ].play ()
                        burn_dmg = 400 +random .randint (-50 ,50 )
                        self.set_message ("　火傷 -{}".format (burn_dmg ))
                        self.pl_life =self.pl_life -burn_dmg 
                        if self.pl_life <=0 :
                            self.pl_life =0 
                            self.idx =242 
                            self.tmr =0 
                    else:
                        self.tmr == self.tmr + 2
                if self.tmr ==16 :
                    self.idx =230 
                    self.tmr =0 


            elif self.idx ==221 :# プレイヤーの魔法
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    ice =0 
                    self.set_message ("　魔法による攻撃！")
                    se [6 ].play ()
                    if self.pl_sword [1 ][0 ]==1 :
                        if random .random ()>0.95 -0.003 *self.pl_sword [1 ][1 ]:
                            ice =1 
                    dmg =int (self.pl_str *1.5 )+random .randint (0 ,9 )-EMY_MPRO [self.emy_typ ]+2 *self.pl_sword [1 ][1 ]+self.pl_sword [2 ][1 ]
                    if self.guard_remain >0 and self.emy_typ ==20 :
                        dmg =int (dmg *(0.35 -self.pl_shield [2 ][1 ]*0.002 ))
                    dmg =max (1 ,dmg )
                    if self.boss_mode == "ice":
                        dmg =0 
                if 2 <=self.tmr <=4 :
                    screen_w =screen .get_size ()[0 ]
                    eff_x =screen_w //2 -190 -self.tmr *12 
                    eff_y =-150 +self.tmr *50 
                    screen .blit (self.imgEffect [2 ],[eff_x ,eff_y ])
                if self.tmr ==5 :
                    self.emy_blink =5 
                    self.set_message (f"　{dmg}　ダメージ！")
                if self.tmr ==11 :
                    self.emy_life =self.emy_life -dmg 
                    self.pl_mag =max (0 ,self.pl_mag -100 )
                    if self.emy_life <=0 :
                        self.emy_life =0 
                        self.idx =241 
                        self.tmr =0 
                if self.tmr ==13 :
                    if self.emy_typ ==18 :
                        self.boss_mode = "ice"
                    if ice ==1 :
                        self.set_message ("　敵は　凍りついた！")
                    else :
                        self.tmr =self.tmr +3
                if self.tmr ==18 :
                    self.poison =max (self.poison -1 ,0 )
                    if ice*self.poison >0 :
                        self.set_message ("　毒 -{}".format (self.poison *40 ))
                        self.pl_life =self.pl_life -self.poison *40 
                        if self.pl_life <=0 :
                            self.pl_life =0 
                            self.idx =242 
                            self.tmr =0
                    else:
                        self.tmr =self.tmr +4
                if self.tmr ==24 :
                    if ice ==1 :
                        self.apply_armor_effects ()
                    elif self.emy_typ ==21 :
                        self.idx =239
                        self.tmr =0
                    else :
                        self.idx =230 
                        self.tmr =0 
                if self.tmr ==26 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==222 :# Potion
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    cure =min (500 +3 *self.pl_armor [2 ][1 ],self.pl_lifemax -self.pl_life )
                    if self.emy_typ ==13 :
                        self.set_message ("　傷薬を無効化されている！")
                        cure =0 
                    else:
                        self.set_message ("　傷薬 +{}".format (cure ))
                        se [2 ].play ()
                if self.tmr ==6 :
                    self.pl_life =min (self.pl_lifemax ,self.pl_life +cure )
                    self.potion =self.potion -1 
                if self.tmr ==11 :
                    if self.emy_typ ==16 or self.emy_typ ==21 :
                        self.idx =232 
                        self.tmr =0 
                    elif self.emy_typ ==20 :
                        self.idx =233 
                        self.tmr =0 
                    else :
                        self.idx =230 
                        self.tmr =0 

            elif self.idx ==223 :# Blaze gem
                self.draw_battle (screen ,fontS )
                img_rz =pygame .transform .rotozoom (self.imgEffect [1 ],30 *self.tmr ,(12 -self.tmr )/8 )
                screen_w =screen .get_size ()[0 ]
                X =screen_w //2 -img_rz .get_width ()/2 
                Y =360 -img_rz .get_height ()/2 
                screen .blit (img_rz ,[X ,Y ])
                if self.tmr ==1 :
                    self.set_message ("　爆弾による攻撃！")
                    se [1 ].play ()
                if self.tmr ==6 :
                    self.blazegem =self.blazegem -1 
                if self.tmr ==11 :
                    dmg =1000 +self.pl_sword [2 ][1 ]*16 
                    if self.emy_typ ==11:
                        self.set_message ("　敵は　爆弾を捕食した！")
                        dmg =0 
                    if self.burn_turns >0 :
                        dmg = self.pl_sword [2 ][1 ]*16
                    if self.emy_typ ==13 :
                        dmg =0 
                        self.emy_skip_turn = True
                    if self.boss_mode == "fire":
                        dmg =0 
                if self.tmr ==15 :
                    self.emy_blink =5 
                    self.set_message (f"　{dmg}　ダメージ！")
                if self.tmr ==21 :
                    self.emy_life =self.emy_life -dmg 
                    if self.emy_life <=0 :
                        self.emy_life =0 
                        self.idx =241 
                        self.tmr =0
                if self.tmr ==23 :
                    if self.emy_typ ==18 :
                        self.boss_mode = "fire"
                    if self.emy_typ ==12:
                        self.burn_turns =4 
                        self.set_message ("　敵は　火傷した！")
                    else:
                        self.tmr =self.tmr +2
                if self.tmr ==26 :
                    if self.emy_typ ==14:
                        self.idx =231 
                        self.tmr =0 
                    elif self.emy_typ ==16 or self.emy_typ ==21 :
                        self.idx =232 
                        self.tmr =0 
                    elif self.emy_typ ==17 :
                        self.idx =238
                        self.tmr =0 
                    else :
                        self.idx =230 
                        self.tmr =0 

    
            elif self.idx ==225 :#情報
                self.draw_battle (screen ,fontS )
                screen_w ,screen_h =screen .get_size ()
                win_w =720 
                win_h =420 
                win_x =screen_w //2 -win_w //2 
                win_y =screen_h //2 -win_h //2 
                pygame .draw .rect (screen ,BLACK ,[win_x ,win_y ,win_w ,win_h ])
                pygame .draw .rect (screen ,WHITE ,[win_x ,win_y ,win_w ,win_h ],2 )
                name = f"{self.emy_name}  Lv.{self.lev}"
                info = ENEMY_INFO.get(self.emy_typ, "info text")
                self.draw_text (screen ,name ,win_x + 30 ,win_y + 40 ,font ,WHITE )
                parts = info.split("\n")
                for i, part in enumerate(parts):
                    self.draw_text (screen ,part ,win_x + 30 ,win_y + 110 + i * 28 ,fontS ,WHITE )
                self.draw_text (screen ,"[B]/[←] Back",win_x + 460 ,win_y + 380 ,fontS ,WHITE )
                if self.tmr >5 :
                    if key [K_b ] or key [K_LEFT ]:
                        self.idx =210 
                        self.tmr =1 

            elif self.idx ==224 :#guard
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.guard_remain =3 
                    if random .random ()<0.01 *self.pl_shield [2 ][1 ]:
                        self.guard_remain =4 
                    self.set_message ("　{}ターンの　守護を得た".format (self.guard_remain ))
                    se [8 ].play ()
                if self.tmr ==6 :
                    self.guard =self.guard -1 
                if self.tmr ==11 :
                    if self.emy_typ ==16 or self.emy_typ ==21 :
                        self.idx =232 
                        self.tmr =0 
                    elif self.emy_typ ==20 :
                        self.idx =234 
                        self.tmr =0 
                    else :
                        self.idx =230 
                        self.tmr =0 

            elif self.idx ==230 :# 敵のターン、敵の攻撃
                self.draw_battle (screen ,fontS )
                defence =self.pl_shield [0 ][1 ]+self.pl_shield [1 ][1 ]+self.pl_shield [2 ][1 ]+self.pl_armor [0 ][1 ]+self.pl_armor [1 ][1 ]+self.pl_armor [2 ][1 ]
                defence =int (defence /2 )
                if self.tmr ==1 :
                    self.set_message (f"{self.emy_name}のターン")
                    pro =0 
                    cou =0 
                    if self.emy_typ ==12 and self.burn_turns >0 :
                        self.idx =237 
                        self.tmr =0 
                        continue
                if self.tmr ==5 :
                    if self.emy_skip_turn :
                        self.emy_skip_turn = False
                        self.set_message ("　敵は　よろけている！")
                        self.tmr =self.tmr+6
                    else:
                        self.set_message (f"　{self.emy_name}の　攻撃！")
                        se [0 ].play ()
                        self.emy_step =30 
                if self.tmr ==9 :
                    if self.pl_shield [0 ][0 ]==1 :
                        if random .random ()>0.7 and self.emy_typ !=20 :
                            pro =0.3 +0.01 *self.pl_shield [0 ][1 ]
                            self.set_message ("　盾で　防御した！")
                    if self.pl_shield [1 ][0 ]==1 :
                        if random .random ()>0.7 :
                            cou =self.pl_shield [1 ][1 ]
                    if self.emy_typ ==20 :
                        dmg_tmp =dmg 
                    dmg =max (self.emy_str +random .randint (0 ,9 )-defence ,1 )
                    dmg =int (dmg /(1 +pro ))*self.pow_up 
                    if self.emy_typ ==18 and self.boss_mode == "fire":
                        dmg =int (dmg *1.3 )
                    if self.guard_remain >0 :
                        if self.emy_typ ==14 or self.emy_typ ==17 :
                            self.set_message ("　守護が破壊された！")
                            self.guard_remain =0 
                        else :
                            dmg =int (dmg *(0.35 -self.pl_shield [2 ][1 ]*0.002 ))
                    if self.emy_typ ==2 or self.emy_typ ==10 or (self.emy_typ ==18 and self.boss_mode == "normal"):
                        if random .random ()>0.7 :
                            self.set_message ("　クリティカルヒット！")
                            dmg =int (dmg *{2:1.5, 10:2, 18:2.5}[self.emy_typ] )
                    if self.emy_typ ==17 :
                        self.inferno -= 15 + random .randint (0 ,10 )
                    if self.emy_typ ==20 :
                        dmg =dmg_tmp 
                    if self.emy_typ ==21 :
                        dmg = int(dmg * self.emy_lifemax/self.emy_life)
                    self.set_message (f"　{dmg}　ダメージ！")
                    self.dmg_eff =6
                    self.emy_step =0 
                if self.tmr ==12 :
                    self.pl_life =self.pl_life -dmg 
                    if self.pl_life <=0 :
                        self.pl_life =0 
                        self.idx =242 
                        self.tmr =0 
                    if cou >0 :
                        self.emy_blink =2 
                        dmg =int (self.pl_str //10 +self.pl_str *self.pl_shield [1 ][1 ]*0.003 +random .randint (0 ,self.pl_shield [1 ][1 ]//5 ))
                        self.set_message (f"　{dmg}　カウンター！")
                        self.emy_life =self.emy_life -dmg 
                        if self.emy_life <=0 :
                            self.emy_life =0 
                            self.idx =241 
                            self.tmr =0 
                if self.tmr ==14 :
                    if self.emy_action (screen ):
                        self.tmr =self.tmr +3 
                if self.tmr ==18 :
                    self.apply_armor_effects ()
                    if self.emy_typ ==6 and self.idx ==236 :
                        self.tmr =0 
                if self.tmr ==21 :
                    self.idx =210 
                    self.tmr =0 


            elif self.idx ==231 :#destroy
                self.draw_battle (screen ,fontS )
                if self.tmr ==5 :
                    self.set_message (self.emy_name +" destroy!")
                    se [1 ].play ()
                    self.emy_step =30 
                if self.tmr ==9 :
                    dmg =self.pl_life -self.pl_life //10
                    self.set_message (f"　{dmg}　ダメージ！")
                if self.tmr ==15 :
                    self.pl_life =self.pl_life //10 
                    if self.pl_life <=0 :
                        self.pl_life =0 
                        self.idx =242 
                        self.tmr =0 
                if self.tmr ==19 :
                    if self.emy_action (screen ):
                        self.tmr =self.tmr +3 
                if self.tmr ==23 :
                    self.apply_armor_effects ()
                if self.tmr ==26 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==232 :#Magia
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.set_message (f"{self.emy_name}のターン")
                if self.tmr ==5 :
                    if self.madoka <1000 :
                        self.set_message ("　Magiaのチャージ！")
                    elif self.madoka >=1000 :
                        self.set_message ("　Magiaを発動")
                        se [6 ].play ()
                        self.emy_step =30 
                if self.tmr ==9 :
                    if self.madoka <1000 :
                        dmg =0 
                        charge_magia = int (self.emy_life *{16:0.02, 21:0.025}[self.emy_typ] +100 )
                        self.set_message ("　Magia +{}".format (charge_magia ))
                        self.madoka =self.madoka +charge_magia
                    elif self.madoka >=1000 :
                        dmg =1000 
                        self.set_message (f"　{dmg}　ダメージ！")
                        self.madoka =self.madoka -1000 
                if self.tmr ==15 :
                    self.pl_life =self.pl_life -dmg 
                    if self.pl_life <0 :
                        self.pl_life =0 
                        self.idx =242 
                        self.tmr =0 
                if self.tmr ==20 :
                    if self.emy_action (screen ):
                        self.tmr =self.tmr +3 
                if self.tmr ==24 :
                    self.apply_armor_effects ()
                if self.tmr ==27 :
                    self.idx =210 
                    self.tmr =0 


            elif self.idx ==233 :#敵のポーション
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    cure =min (cure ,self.emy_lifemax -self.emy_life )
                    self.set_message ("　敵の生命 +{}".format (cure ))
                    se [2 ].play ()
                if self.tmr ==6 :
                    self.emy_life =min (self.emy_lifemax ,self.emy_life +cure )
                if self.tmr ==11 :
                    self.apply_armor_effects ()
                if self.tmr ==14 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==234 :#敵のガード
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.set_message ("　敵は　{}ターンの守護を得た".format (self.guard_remain ))
                    se [8 ].play ()
                if self.tmr ==6 :
                    self.apply_armor_effects ()
                if self.tmr ==11 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==235 :#逃亡？
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.set_message ("　敵は　こちらを見つめている")
                if self.tmr ==6 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==236 :#敵の逃亡
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.set_message ("　敵は逃げていった")
                if self.tmr ==10 :
                    self.guard_remain =0 
                    self.idx =244 


            elif self.idx ==237 :# 火炎攻撃
                self.draw_battle (screen ,fontS )
                defence =self.pl_shield [0 ][1 ]+self.pl_shield [1 ][1 ]+self.pl_shield [2 ][1 ]+self.pl_armor [0 ][1 ]+self.pl_armor [1 ][1 ]+self.pl_armor [2 ][1 ]
                defence =int (defence /2 )
                if self.tmr ==5 :
                    self.set_message (f"　{self.emy_name}の　攻撃！")
                    se [0 ].play ()
                    self.emy_step =30 
                if self.tmr ==9 :
                    dmg =max (self.emy_str +random .randint (0 ,9 )-defence ,1 )
                    dmg =dmg *3 
                    if self.guard_remain >0 :
                        dmg =int (dmg *(0.35 -self.pl_shield [2 ][1 ]*0.002 ))
                    self.set_message (f"　{dmg}　ダメージ！")
                    self.dmg_eff =6
                    self.emy_step =0 
                if self.tmr ==12 :
                    self.pl_life =self.pl_life -dmg 
                    if self.pl_life <=0 :
                        self.pl_life =0 
                        self.idx =242 
                        self.tmr =0 
                    recoil =2000 +random .randint (-100 ,100 )
                    self.emy_life =max (0 ,self.emy_life -recoil )
                    self.set_message ("　反動 -{}".format (recoil ))
                    self.burn_turns -=1 
                    if self.emy_life <=0 :
                        self.emy_life =0 
                        self.idx =241 
                        self.tmr =0
                if self.tmr ==16 :
                    self.apply_armor_effects ()
                if self.tmr ==19 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==238 :# 豪炎
                self.draw_battle (screen ,fontS )
                if self.tmr ==5 :
                    self.set_message (f"　{self.emy_name}の　豪炎！")
                    se [1 ].play ()
                    self.emy_step =30 
                if self.tmr ==9 :
                    dmg =150 + self.inferno +random .randint (-30 ,30 )
                    self.set_message (f"　{dmg}　ダメージ！")
                    self.dmg_eff =6
                    self.emy_step =0
                    self.inferno = self.inferno + 30 + random.randint(0, 20)
                if self.tmr ==12 :
                    self.pl_life =self.pl_life -dmg 
                    if self.pl_life <=0 :
                        self.pl_life =0 
                        self.idx =242 
                        self.tmr =0 
                if self.tmr ==16 :
                    self.apply_armor_effects ()
                if self.tmr ==19 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==239 :# 毒攻撃
                self.draw_battle (screen ,fontS )
                defence =self.pl_shield [0 ][1 ]+self.pl_shield [1 ][1 ]+self.pl_shield [2 ][1 ]+self.pl_armor [0 ][1 ]+self.pl_armor [1 ][1 ]+self.pl_armor [2 ][1 ]
                defence =int (defence /2 )
                if self.tmr ==1 :
                    self.set_message (self.emy_name +"のターン")
                    pro =0 
                    cou =0 
                if self.tmr ==5 :
                    self.set_message (f"　{self.emy_name}の　攻撃！")
                    se [0 ].play ()
                    self.emy_step =30 
                if self.tmr ==9 :
                    if self.pl_shield [0 ][0 ]==1 :
                        if random .random ()>0.7 and self.emy_typ !=20 :
                            pro =0.3 +0.01 *self.pl_shield [0 ][1 ]
                            self.set_message ("　盾で　防御した！")
                    if self.pl_shield [1 ][0 ]==1 :
                        if random .random ()>0.7 :
                            cou =self.pl_shield [1 ][1 ]
                    if self.emy_typ ==20 :
                        dmg_tmp =dmg 
                    dmg =max (self.emy_str +random .randint (0 ,9 )-defence ,1 )
                    dmg =int (dmg /(1 +pro ))*self.pow_up 
                    if self.guard_remain >0 :
                        if self.emy_typ ==14 or self.emy_typ ==17 :
                            self.set_message ("　守護が　破壊された")
                            self.guard_remain =0 
                        else :
                            dmg =int (dmg *(0.35 -self.pl_shield [2 ][1 ]*0.002 ))
                    self.set_message (f"　{dmg}　ダメージ！")
                    self.dmg_eff =6
                    self.emy_step =0 
                if self.tmr ==12 :
                    self.pl_life =self.pl_life -dmg 
                    if self.pl_life <=0 :
                        self.pl_life =0 
                        self.idx =242 
                        self.tmr =0 
                    if cou >0 :
                        self.emy_blink =2 
                        dmg =int (self.pl_str //10 +self.pl_str *self.pl_shield [1 ][1 ]*0.003 +random .randint (0 ,self.pl_shield [1 ][1 ]//5 ))
                        self.set_message (f"　{dmg}　のカウンター！")
                        self.emy_life =self.emy_life -dmg 
                        if self.emy_life <=0 :
                            self.emy_life =0 
                            self.idx =241 
                            self.tmr =0 
                if self.tmr ==14 :
                    self.poison =max (self.poison -1 ,0 )
                    self.poison = 4
                    self.set_message ("　毒を喰らった！")
                    self.set_message ("　毒 -{}".format (self.poison *40 ))
                    self.pl_life =self.pl_life -self.poison *40 
                    if self.pl_life <=0 :
                        self.pl_life =0 
                        self.idx =242 
                        self.tmr =0 
                if self.tmr ==18 :
                    self.apply_armor_effects ()
                if self.tmr ==21 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==240 :# 逃げられる？
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :self.set_message ("　逃走を試みた")
                if self.tmr ==10 :
                    if self.boss ==1 :
                        self.set_message ("　逃走に失敗した！")
                    elif random .randint (0 ,99 )<60 or self.emy_typ == 22:
                        self.btl_cmd =0
                        self.guard_remain =0 
                        self.poison =0 
                        self.madoka =0 
                        self.pow_up =1 
                        self.burn_turns =0 
                        self.inferno =0
                        self.boss_mode = "normal"
                        self.change = 0
                        self.idx =244 
                    else :
                        self.set_message ("　逃走に失敗した！")
                if self.tmr ==15 :
                    if self.emy_typ ==16 or self.emy_typ ==21 :
                        self.idx =232 
                        self.tmr =0 
                    if self.emy_typ ==20 :
                        self.idx =235 
                        self.tmr =0 
                    else :
                        self.idx =230 
                        self.tmr =0 


            elif self.idx ==241 :# 勝利
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.btl_cmd =0
                    self.guard_remain =0 
                    self.poison =0 
                    self.madoka =0 
                    self.pow_up =1 
                    self.burn_turns =0 
                    self.inferno =0
                    self.boss_mode = "normal"
                    if self.emy_typ ==20 :
                        self.idx =245 
                        self.tmr =0
                if self.tmr ==2 :
                    self.change = 0
                    self.set_message ("{}を　たおした！".format (self.emy_name ))
                    pygame .mixer .music .stop ()
                    if self.boss ==1 :
                        se [7 ].play ()
                    else :
                        se [5 ].play ()
                    self.pl_exp =self.pl_exp +int ((500 +self.emy_typ *50 +EMY_EXP [self.emy_typ ])*(0.7 *((self.floor -1 )//30 )+1 ))
                    self.pl_mag =self.pl_mag +self.emy_typ *2 +self.boss *300 
                    if self.emy_typ ==22 :
                        self.idx =246 
                        self.tmr =0 
                if self.tmr ==15 :
                    if self.boss ==1 :
                        time .sleep (3 )
                    self.idx =244 
                    if self.pl_exp >=(self.pl_lifemax -250 )*20 :
                        self.idx =243 
                        self.tmr =0 

            elif self.idx ==242 :# 敗北
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    pygame .mixer .music .stop ()
                    self.btl_cmd =0
                    self.guard_remain =0 
                    self.poison =0 
                    self.madoka =0 
                    self.pow_up =1 
                    self.burn_turns =0 
                    self.inferno =0
                    self.boss_mode = "normal"
                    self.change = 0
                    self.set_message ("負けてしまった")
                if self.tmr ==11 :
                    self.idx =70 
                    self.tmr =29 

            elif self.idx ==243 :# レベルアップ
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.set_message ("レベルアップ！")
                    se [4 ].play ()
                    lif_p =random .randint (10 ,20 )
                    str_p =random .randint (7 ,9 )
                    mag_p =random .randint (15 ,30 )
                    self.pl_exp =self.pl_exp -(self.pl_lifemax -250 )*20 
                if self.tmr ==13 :
                    self.pl_lifemax =self.pl_lifemax +lif_p 
                    self.pl_life =self.pl_life +lif_p 
                    self.pl_mag =self.pl_mag +mag_p 
                    self.pl_str =self.pl_str +str_p 
                if self.tmr ==23 :
                    if self.pl_exp >(self.pl_lifemax -250 )*20 :
                        self.idx =243 
                        self.tmr =0 
                    else :
                        self.idx =244 

            elif self.idx ==244 :# 戦闘終了
                if self.emy_typ ==21 :
                    time .sleep (1 )
                    charge =0 
                    self.boss =0 
                    if self.true_episode_heard:
                        self.init_last_talk (2)
                    else:
                        self.init_last_talk (1)
                    self.idx =133 
                    self.tmr =0 
                elif self.boss ==1 :
                    time .sleep (1 )
                    self.idx =110 
                    self.boss =0 
                    if 90 <self.floor <100 :
                        pygame .mixer .music .load (self.path +"/sound/bgm_9.wav")
                        pygame .mixer .music .play (-1 )
                    self.tmr =0 
                else :
                    if self.move_bgm_path :
                        pygame .mixer .music .load (self.move_bgm_path )
                        try:
                            pygame .mixer .music .play (-1 ,self.move_bgm_pos_ms /1000.0 )
                            self.move_bgm_start_time =time .time ()-self.move_bgm_pos_ms /1000.0 
                        except pygame.error:
                            pygame .mixer .music .play (-1 )
                            self.move_bgm_pos_ms =0 
                            self.move_bgm_start_time =time .time ()
                    else :
                        pygame .mixer .music .load (self.path +"/sound/bgm_"+str ((self.floor-1) //10 )+".wav")
                        pygame .mixer .music .play (-1 )
                    self.idx =100 

            elif self.idx ==245 :#最終ボスの形態変化
                self.draw_battle (screen ,fontS )
                if 1 <=self.tmr <=5 :
                    pygame .draw .rect (screen ,BLACK ,[0 ,0 ,880 ,320 ])
                    pygame .draw .rect (screen ,BLACK ,[0 ,720 -320 ,880 ,320 ])
                if self.tmr ==1 :
                    self.init_message ()
                if self.tmr ==5 :
                    self.change +=1 
                    self.init_bossbattle ()
                if 6 <=self.tmr and self.tmr <=9 :
                    pygame .draw .rect (screen ,BLACK ,[0 ,0 ,880 ,320 ])
                    pygame .draw .rect (screen ,BLACK ,[0 ,720 -320 ,880 ,320 ])
                if self.tmr ==10 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==246 :#ドロップ
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    trap_drop =random .randint (2 ,10 )#最大で2~10を用意
                    wpn_lev_drop =self.lev 
                if self.tmr ==10 :
                    if trap_drop %3 ==2 :
                        self.pl_shield [trap_drop //3 ][0 ]=1 
                        self.pl_shield [trap_drop //3 ][1 ]=max (wpn_lev_drop ,self.pl_shield [trap_drop //3 ][1 ])
                    if trap_drop %3 ==0 :
                        self.pl_armor [trap_drop //3 -1 ][0 ]=1 
                        self.pl_armor [trap_drop //3 -1 ][1 ]=max (wpn_lev_drop ,self.pl_armor [trap_drop //3 -1 ][1 ])
                    if trap_drop %3 ==1 :
                        self.pl_sword [trap_drop //3 -1 ][0 ]=1 
                        self.pl_sword [trap_drop //3 -1 ][1 ]=max (wpn_lev_drop ,self.pl_sword [trap_drop //3 -1 ][1 ])
                    self.set_message ("Drop {} lv.{}".format (TRAP_NAME [trap_drop ],wpn_lev_drop ))
                if self.tmr ==23 :
                    self.idx =241 
                    self.tmr =14 

            pygame .display .update ()
            clock .tick (10 )
            self.prev_return = key [K_RETURN ]
            self.prev_a = key [K_a ]


def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
