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
from assets import load_images, load_sounds, load_floor_variants, load_wall_variants, make_wall_top


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
        # self.imgItem = images.items
        self.imgFloor = images.floors
        self.imgPlayerBase0 = images.players
        self.imgPlayerBase1 = [
            pygame.image.load(self.path + f"/image/mychr/mychr_{i//3}_{i%3}_1.png")
            for i in range(12)
        ]
        self.imgPlayerBase1.append(pygame.image.load(self.path + "/image/mychr/mychr_4_0_1.png"))
        self.imgPlayer = self.imgPlayerBase0
        self.imgEffect = images.effects
        self.imgFire = pygame.image.load(self.path + "/image/fire.png")
        # self.imgPoison = pygame.image.load(self.path + "/image/poison.png")

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
        self.pl_a = 2
        self.pl_lifemax = 0
        self.pl_life = 0
        self.pl_str = 0
        self.pl_mag = 0
        self.pl_exp = 0
        self.pl_level = 1
        self.pl_shield = [[0, 0], [0, 0], [0, 0]]
        self.pl_armor = [[0, 0], [0, 0], [0, 0]]
        self.pl_sword = [[0, 0], [0, 0], [0, 0]]
        self.potion = 0
        self.blazegem = 0
        self.guard = 0
        self.truth_fragment = 0
        self.tool_food = 0
        self.tool_magic_water = 0
        self.tool_magic_seed = 0
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
        self.zukan_menu_cmd = 0
        self.zukan_kind = 0
        self.zukan_cursor = 0
        self.zukan_detail = 0
        self.zukan_back_lock = False
        self.zukan_accept_lock = False
        self.zukan_enemy_cache = {}
        self.encountered_enemies = set()
        self.confirm_cmd = 0
        self.load_accept_lock = False
        self.title_confirm_lock = False
        self.save_confirm_lock = False
        self.menu_back_lock = False
        self.menu_accept_lock = False
        self.tool_back_lock = False
        self.tool_accept_lock = False
        self.tool_cmd = 0
        self.tool_confirm_active = False
        self.tool_confirm_cmd = 0
        self.save_cmd = 0
        self.save_from_stair = False
        self.save_from_boss = False
        self.stair_save_slot = 0
        self.stair_choice_cmd = 0
        self.stair_prompted = False
        self.stair_choice_input_lock = False
        self.boss_save_cmd = 0
        self.boss_save_input_lock = False
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
        self.fixed_floor_offset = (0, 0)  # Track offset for padded fixed floors

        self.maze = [[0 for j in range(MAZE_W)] for i in range(MAZE_H)]
        self.dungeon = [[0 for j in range(DUNGEON_W)] for i in range(DUNGEON_H)]

        self.message = [""] * 10
        self.init_floor_variant_map()
        self.init_floor_flip_map()
        self.prologue_lines = PROLOGUE_LINES
        self.prologue_input_lock = False
        self.floor_title_active = False
        self.floor_title_pos = None
        self.boss_pos = None
        self.boss_area = set()
        self.boss_talk_lines = []
        self.boss_talk_index = 0
        self.boss_map_cache = {}
        self.bg_cache = {}
        self.last_btl_bg_idx = None
        self.prev_return = False
        self.prev_a = False
        self.boss_talk_char_count = 0
        self.boss_talk_last_tick = 0
        self.move_bgm_path = ""
        self.move_bgm_pos_ms = 0
        self.move_bgm_start_time = 0.0
        self.emy_skip_turn = False
        self.item_talk_lines = []
        self.item_talk_index = 0
        self.item_talk_char_count = 0
        self.item_talk_last_tick = 0
        self.item_event_phase = 0
        self.item_choice = 0
        self.item_reward = None
        self.item_event_kind = ""
        self.item_reward_count = 3
        self.true_episode_heard = False
        self.wall_item = None
        self.event_wall_pos = None
        self.event_talk_lines = []
        self.event_talk_index = 0
        self.event_talk_char_count = 0
        self.event_talk_last_tick = 0
        self.wall_event = None
        self.truth_fragment_drop_battle = False
        self.map_seen = None
        self.map_stairs = None
        self.map_bosses = None
        self.map_grid_surface = None
        self.map_surface = None
        self.map_surface_scale = None
        self.map_surface_size = None
        self.fixed_floor_data = None
        self.last_talk_mode = 1
        self.reset_tutorial_runtime()

    def init_floor_variant_map(self):
        count = max(len(self.floor_variants), 1)
        self.floor_var_map = [[random.randint(0, count - 1) for j in range(DUNGEON_W)] for i in range(DUNGEON_H)]

    def init_floor_flip_map(self):
        self.floor_flip_map = [[random.randint(0, 1) for j in range(DUNGEON_W)] for i in range(DUNGEON_H)]

    def init_map_state(self):
        self.map_seen = [[False for j in range(DUNGEON_W)] for i in range(DUNGEON_H)]
        self.map_stairs = set()
        self.map_bosses = set()
        self.map_grid_surface = pygame.Surface((DUNGEON_W, DUNGEON_H), pygame.SRCALPHA)
        self.map_grid_surface.fill((0, 0, 0, 120))
        self.map_surface = None
        self.map_surface_scale = None
        self.map_surface_size = None

    def has_full_basic_set(self):
        return (
            self.pl_shield[0][0] == 1 and
            self.pl_armor[0][0] == 1 and
            self.pl_sword[0][0] == 1
        )

    def update_player_images(self):
        if self.has_full_basic_set():
            self.imgPlayer = self.imgPlayerBase1
        else:
            self.imgPlayer = self.imgPlayerBase0

    def set_floor_assets(self, floor_index, floor_value):
        self.floor_variants = load_floor_variants(self.path, floor_index)
        if not self.floor_variants:
            self.floor_variants = [self.imgFloor[0]]
        self.floor_variants_flipped = [pygame.transform.flip(img, True, False) for img in self.floor_variants]
        self.imgFloor[0] = self.floor_variants[0]
        self.imgFloor[2] = pygame.image.load(self.path + "/image/cocoon/cocoon" + str(floor_index) + ".png")
        wall_set = (floor_value - 1) // 10
        self.wall_variantsA = load_wall_variants(self.path, "wallA", wall_set)
        if not self.wall_variantsA:
            self.wall_variantsA = [self.imgWall]
        self.wall_variantsB = [make_wall_top(img) for img in self.wall_variantsA]
        self.imgWall = self.wall_variantsA[0]
        self.imgWall2 = self.wall_variantsB[0]
        event_path = os.path.join(self.path, "image", "wallA{}_event.png".format(wall_set))
        self.wall_event = pygame.image.load(event_path)

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
        return all((2 not in row) and (10 not in row) for row in self.dungeon)

    def default_tutorial_progress(self):
        return {
            "talked": [False, False, False, False, False, False, False],
            "room2_chest_opened": False,
            "room3_enemy_defeated": False,
            "room4_item_obtained": False,
            "room4_item_used": False,
            "room5_enemy_defeated": False,
        }

    def reset_tutorial_runtime(self):
        self.tutorial_enabled = False
        self.tutorial_wall_stage = {}
        self.tutorial_gate_pos = {}
        self.tutorial_stairs_pos = None
        self.tutorial_room2_chest_pos = None
        self.tutorial_room3_truth_pos = None
        self.tutorial_room4_item_pos = None
        self.tutorial_room5_enemy_pos = None
        self.tutorial_progress = self.default_tutorial_progress()
        self.tutorial_active_stage = 0
        self.tutorial_pending_battle = ""

    def parse_pos(self, value):
        if (isinstance(value, (list, tuple)) and len(value) == 2 and
                all(isinstance(v, int) for v in value)):
            return (value[0], value[1])
        return None

    def load_fixed_floor_data(self, floor_value):
        if floor_value not in (1, 100):
            return None
        floor_path = os.path.join(self.path, "floor_{}.json".format(floor_value))
        if not os.path.exists(floor_path):
            return None
        with open(floor_path, "r") as f:
            data = json.load(f)
        dungeon = data.get("dungeon")
        # For floor 1 and 100, accept any valid dungeon size (not restricted to DUNGEON_H/W)
        if isinstance(dungeon, list) and len(dungeon) > 0 and all(isinstance(row, list) and len(row) > 0 for row in dungeon):
            # Pad the dungeon to standard size if needed
            padded_dungeon, offset = self.pad_dungeon_to_standard_size(dungeon)
            data["dungeon"] = padded_dungeon
            data["_dungeon_offset"] = offset
            
            # Adjust all coordinates if padding was applied
            if offset != (0, 0):
                offset_x, offset_y = offset
                
                # Adjust pl_start
                if "pl_start" in data:
                    data["pl_start"] = (data["pl_start"][0] + offset_x, data["pl_start"][1] + offset_y)
                
                # Adjust boss_pos if it exists
                if "boss_pos" in data:
                    data["boss_pos"] = (data["boss_pos"][0] + offset_x, data["boss_pos"][1] + offset_y)
                
                # Adjust all tutorial coordinates
                if "tutorial" in data and isinstance(data["tutorial"], dict):
                    tutorial = data["tutorial"]
                    
                    # Adjust wall_stages
                    if "wall_stages" in tutorial:
                        for entry in tutorial["wall_stages"]:
                            if isinstance(entry, dict) and "pos" in entry:
                                entry["pos"] = [entry["pos"][0] + offset_x, entry["pos"][1] + offset_y]
                    
                    # Adjust gates
                    if "gates" in tutorial:
                        for entry in tutorial["gates"]:
                            if isinstance(entry, dict) and "pos" in entry:
                                entry["pos"] = [entry["pos"][0] + offset_x, entry["pos"][1] + offset_y]
                    
                    # Adjust stairs_pos
                    if "stairs_pos" in tutorial and tutorial["stairs_pos"]:
                        tutorial["stairs_pos"] = [tutorial["stairs_pos"][0] + offset_x, tutorial["stairs_pos"][1] + offset_y]
                    
                    # Adjust room chest positions
                    if "room2_chest" in tutorial and tutorial["room2_chest"]:
                        tutorial["room2_chest"] = [tutorial["room2_chest"][0] + offset_x, tutorial["room2_chest"][1] + offset_y]
                    
                    if "room3_truth_cocoon" in tutorial and tutorial["room3_truth_cocoon"]:
                        tutorial["room3_truth_cocoon"] = [tutorial["room3_truth_cocoon"][0] + offset_x, tutorial["room3_truth_cocoon"][1] + offset_y]
                    
                    if "room4_item_cocoon" in tutorial and tutorial["room4_item_cocoon"]:
                        tutorial["room4_item_cocoon"] = [tutorial["room4_item_cocoon"][0] + offset_x, tutorial["room4_item_cocoon"][1] + offset_y]
                    
                    if "room5_enemy_cocoon" in tutorial and tutorial["room5_enemy_cocoon"]:
                        tutorial["room5_enemy_cocoon"] = [tutorial["room5_enemy_cocoon"][0] + offset_x, tutorial["room5_enemy_cocoon"][1] + offset_y]
            
            return data
        return None

    def pad_dungeon_to_standard_size(self, dungeon):
        """Pad a dungeon to DUNGEON_H x DUNGEON_W by adding walls around it.
        Returns (padded_dungeon, (offset_x, offset_y))"""
        if len(dungeon) == DUNGEON_H and len(dungeon[0]) == DUNGEON_W:
            return dungeon, (0, 0)
        
        # Create a new dungeon filled with walls (9)
        padded = [[9 for _ in range(DUNGEON_W)] for _ in range(DUNGEON_H)]
        
        # Calculate offset to center the original dungeon
        orig_h = len(dungeon)
        orig_w = len(dungeon[0])
        offset_y = (DUNGEON_H - orig_h) // 2
        offset_x = (DUNGEON_W - orig_w) // 2
        
        # Copy the original dungeon into the center
        for y in range(orig_h):
            for x in range(orig_w):
                if offset_y + y < DUNGEON_H and offset_x + x < DUNGEON_W:
                    padded[offset_y + y][offset_x + x] = dungeon[y][x]
        
        return padded, (offset_x, offset_y)

    def setup_tutorial_floor(self, progress_data=None):
        self.reset_tutorial_runtime()
        if self.floor != 1 or not self.fixed_floor_data:
            return
        tutorial = self.fixed_floor_data.get("tutorial")
        if not isinstance(tutorial, dict):
            return
        self.tutorial_enabled = True
        for entry in tutorial.get("wall_stages", []):
            if not isinstance(entry, dict):
                continue
            stage = entry.get("stage")
            pos = self.parse_pos(entry.get("pos"))
            if isinstance(stage, int) and pos:
                self.tutorial_wall_stage[pos] = stage
        for entry in tutorial.get("gates", []):
            if not isinstance(entry, dict):
                continue
            stage = entry.get("stage")
            pos = self.parse_pos(entry.get("pos"))
            if isinstance(stage, int) and pos:
                self.tutorial_gate_pos[stage] = pos
        self.tutorial_stairs_pos = self.parse_pos(tutorial.get("stairs_pos"))
        self.tutorial_room2_chest_pos = self.parse_pos(tutorial.get("room2_chest"))
        self.tutorial_room3_truth_pos = self.parse_pos(tutorial.get("room3_truth_cocoon"))
        self.tutorial_room4_item_pos = self.parse_pos(tutorial.get("room4_item_cocoon"))
        self.tutorial_room5_enemy_pos = self.parse_pos(tutorial.get("room5_enemy_cocoon"))
        if isinstance(progress_data, dict):
            progress = self.default_tutorial_progress()
            talked = progress_data.get("talked")
            if isinstance(talked, list):
                for i in range(1, 7):
                    if i < len(talked):
                        progress["talked"][i] = bool(talked[i])
            for key in ("room2_chest_opened", "room3_enemy_defeated", "room4_item_obtained", "room4_item_used", "room5_enemy_defeated"):
                if key in progress_data:
                    progress[key] = bool(progress_data[key])
            self.tutorial_progress = progress
        else:
            self.tutorial_progress = self.default_tutorial_progress()
        self.tutorial_active_stage = 0
        self.tutorial_pending_battle = ""
        self.update_tutorial_floor_state()

    def tutorial_save_data(self):
        if not self.tutorial_enabled:
            return None
        return {
            "talked": list(self.tutorial_progress["talked"]),
            "room2_chest_opened": self.tutorial_progress["room2_chest_opened"],
            "room3_enemy_defeated": self.tutorial_progress["room3_enemy_defeated"],
            "room4_item_obtained": self.tutorial_progress["room4_item_obtained"],
            "room4_item_used": self.tutorial_progress["room4_item_used"],
            "room5_enemy_defeated": self.tutorial_progress["room5_enemy_defeated"],
        }

    def tutorial_stage_for_wall(self, pos):
        if not self.tutorial_enabled:
            return 0
        return self.tutorial_wall_stage.get(pos, 0)

    def init_tutorial_talk(self, stage):
        lines = TUTORIAL_WALL_TALK.get(stage)
        if not lines:
            return False
        self.event_talk_lines = lines
        self.event_talk_index = 0
        self.event_talk_char_count = 0
        self.event_talk_last_tick = pygame.time.get_ticks()
        self.tutorial_active_stage = stage
        return True

    def complete_tutorial_talk(self):
        if not self.tutorial_enabled:
            self.tutorial_active_stage = 0
            return
        stage = self.tutorial_active_stage
        if 1 <= stage <= 6:
            self.tutorial_progress["talked"][stage] = True
        self.tutorial_active_stage = 0
        self.update_tutorial_floor_state()

    def update_tutorial_floor_state(self):
        if not self.tutorial_enabled:
            return
        talked = self.tutorial_progress["talked"]
        open_rules = {
            1: talked[1],
            2: talked[2] and self.tutorial_progress["room2_chest_opened"],
            3: talked[3] and self.tutorial_progress["room3_enemy_defeated"],
            4: talked[4] and self.tutorial_progress["room4_item_obtained"] and self.tutorial_progress["room4_item_used"],
            5: talked[5] and self.tutorial_progress["room5_enemy_defeated"],
        }
        for stage, pos in self.tutorial_gate_pos.items():
            x, y = pos
            if 0 <= x < DUNGEON_W and 0 <= y < DUNGEON_H:
                self.dungeon[y][x] = 0 if open_rules.get(stage, False) else 9
        if self.tutorial_stairs_pos:
            sx, sy = self.tutorial_stairs_pos
            if 0 <= sx < DUNGEON_W and 0 <= sy < DUNGEON_H:
                self.dungeon[sy][sx] = 3 if talked[6] else 0

    def restore_tutorial_cocoon(self):
        if not self.tutorial_enabled or not self.tutorial_pending_battle:
            return
        if self.tutorial_pending_battle == "room3":
            pos = self.tutorial_room3_truth_pos
            tile = 10
            done = self.tutorial_progress["room3_enemy_defeated"]
        elif self.tutorial_pending_battle == "room5":
            pos = self.tutorial_room5_enemy_pos
            tile = 2
            done = self.tutorial_progress["room5_enemy_defeated"]
        else:
            pos = None
            tile = 0
            done = True
        if not done and pos:
            x, y = pos
            if 0 <= x < DUNGEON_W and 0 <= y < DUNGEON_H and self.dungeon[y][x] == 0:
                self.dungeon[y][x] = tile
        self.tutorial_pending_battle = ""

    def place_boss(self):
        self.boss_pos = None
        self.boss_area = set()
        candidates = []
        for y in range(3, DUNGEON_H - 3):
            for x in range(3, DUNGEON_W - 3):
                if self.dungeon[y][x] == 0:
                    candidates.append((x, y))
        if candidates:
            x, y = random.choice(candidates)
            self.boss_pos = (x, y)
            self.boss_area = {(x, y)}

    def init_boss_talk(self):
        boss_id = 9 + int(self.floor // 10)
        if 90 < self.floor < 100:
            boss_id = 9 + int(self.floor % 10)
        boss_map_id = boss_id - 10
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
        self.tutorial_active_stage = 0
        event_id = (self.floor - 1) // 10
        if 0 <= event_id < len(EVENT_TALK):
            self.event_talk_lines = EVENT_TALK[event_id]
        else:
            self.event_talk_lines = ["Event talk missing."]
        self.event_talk_index = 0
        self.event_talk_char_count = 0
        self.event_talk_last_tick = pygame.time.get_ticks()

    def get_boss_map_image(self):
        cache_key = "boss_map"
        if cache_key not in self.boss_map_cache:
            path = self.path + "/image/boss_map.png"
            self.boss_map_cache[cache_key] = pygame.image.load(path)
        return self.boss_map_cache[cache_key]

    def make_dungeon (self ):
        self.fixed_floor_data = None
        self.last_talk_mode = 1
        self.reset_tutorial_runtime()
        fixed_data = self.load_fixed_floor_data(self.floor)
        if fixed_data:
            self.dungeon = fixed_data["dungeon"]
            self.fixed_floor_data = fixed_data
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
        extra_wall_rows =1 
        start_x =-(cols //2 )
        start_y =-(rows //2 )
        offset_x =view_left +view_w //2 -tile //2 -(cols //2 )*tile 
        offset_y =view_top +view_h //2 -tile //2 -(rows //2 )*tile 
        for y in range (start_y ,start_y +rows +extra_wall_rows ):
            for x in range (start_x ,start_x +cols ):
                X =offset_x +(x -start_x )*tile 
                Y =offset_y +(y -start_y )*tile 
                dx =self.pl_x +x 
                dy =self.pl_y +y 
                wall_only =(y >=start_y +rows )
                if 0 <=dx <DUNGEON_W and 0 <=dy <DUNGEON_H :
                    tile_id =self.dungeon [dy ][dx ]
                    if not wall_only and tile_id not in (7 ,8 ,9 ):
                        if not self.map_seen [dy ][dx ]:
                            self.map_seen [dy ][dx ]=True
                            new_seen .append ((dx ,dy ))
                        if tile_id ==3 :
                            self.map_stairs .add ((dx ,dy ))
                    if not wall_only and tile_id in (0 ,1 ,2 ,3 ,4 ,5 ,6 ,10 ):
                        if tile_id in (0 ,1 ,2 ,4 ,10 ):
                            variant =self.floor_var_map [dy ][dx ]
                            if self.floor_flip_map [dy ][dx ]:
                                bg .blit (self.floor_variants_flipped [variant ],[X ,Y ])
                            else :
                                bg .blit (self.floor_variants [variant ],[X ,Y ])
                            overlay_tile =2 if tile_id ==10 else tile_id
                            if overlay_tile !=0 :
                                bg .blit (self.imgFloor [overlay_tile ],[X ,Y ])
                        else :
                            bg .blit (self.imgFloor [tile_id ],[X ,Y ])
                    if tile_id in (7 ,8 ,9 ):
                        if tile_id ==8 and self.wall_event:
                            bg .blit (self.wall_event ,[X ,Y -40 ])
                        else :
                            bg .blit (self.imgWall ,[X ,Y -40 ])
                        if tile_id ==7 :
                            bg .blit (self.imgFloor [7 ],[X ,Y ])
                        if dy >=1 and self.dungeon [dy -1 ][dx ] in (7 ,8 ,9 ):
                            bg .blit (self.imgWall2 ,[X ,Y -80 ])
                    if self.boss_pos and dx == self.boss_pos[0] and dy == self.boss_pos[1]:
                        if not wall_only and self.map_bosses is not None:
                            self.map_bosses.add((dx, dy))
                        boss_map = self.get_boss_map_image()
                        bg .blit (boss_map ,[X ,Y -40 ])
                if not wall_only and x ==0 and y ==0 :# 主人公キャラの表示
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
        self.event_wall_pos = None
        if self.fixed_floor_data and self.floor == 1:
            self.setup_tutorial_floor()
            if self.fixed_floor_data.get("pl_start"):
                self.pl_x, self.pl_y = self.fixed_floor_data["pl_start"]
            self.pl_d =1
            self.pl_a =5
            self.stair_prompted =False
            return
        is_boss_floor =self.floor %10 ==0 or self.floor >90
        if self.fixed_floor_data and self.floor == 100:
            boss_pos = self.fixed_floor_data.get("boss_pos")
            if boss_pos:
                bx, by = boss_pos
                self.boss_pos = (bx, by)
                self.boss_area = {(bx, by)}
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
            if self.floor >=15 :
                for x ,y in take_cells (3 ):
                    self.dungeon [y ][x ]=4
        if is_boss_floor :
            for x ,y in take_cells (10 ):
                self.dungeon [y ][x ]=1
            if self.floor >=15 :
                for x ,y in take_cells (5 ):
                    self.dungeon [y ][x ]=4
        cocoon_target =35 if is_boss_floor else 20
        cocoon_cells =take_cells (cocoon_target )
        for x ,y in cocoon_cells:
            self.dungeon [y ][x ]=2
        if cocoon_cells:
            sx ,sy =random .choice (cocoon_cells )
            self.dungeon [sy ][sx ]=10
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
        self.pl_a =5 
        if self.floor >= 91:
            wall_cells = [
                (x, y)
                for y in range(DUNGEON_H - 1)
                for x in range(DUNGEON_W)
                if self.dungeon[y][x] == 9 and self.dungeon[y + 1][x] == 0
            ]
            if wall_cells:
                wx, wy = random.choice(wall_cells)
                self.dungeon[wy][wx] = 7
        else:
            if self.floor %10 ==7:
                wall_cells = [
                    (x, y)
                    for y in range(DUNGEON_H - 1)
                    for x in range(DUNGEON_W)
                    if self.dungeon[y][x] == 9 and self.dungeon[y + 1][x] == 0
                ]
                if wall_cells:
                    wx, wy = random.choice(wall_cells)
                    self.dungeon[wy][wx] = 7
            if self.floor %10 ==4 and self.wall_event:
                wall_cells = [
                    (x, y)
                    for y in range(DUNGEON_H - 1)
                    for x in range(DUNGEON_W)
                    if self.dungeon[y][x] == 9 and self.dungeon[y + 1][x] == 0
                ]
                if wall_cells:
                    wx, wy = random.choice(wall_cells)
                    self.dungeon[wy][wx] = 8

    def move_player (self ,key ):
        if self.dungeon [self.pl_y ][self.pl_x ]==1 :# 宝箱に載った
            self.dungeon [self.pl_y ][self.pl_x ]=0 
            self.treasure =random .choice ([0 ,0 ,1 ,1 ,1 ,2 ])
            self.item_reward_count =1
            if self.treasure ==0 :
                self.potion =self.potion +1 
            if self.treasure ==1 :
                self.blazegem =self.blazegem +1 
            if self.treasure ==2 :
                self.guard =self.guard +1 
            if self.tutorial_enabled and self.floor ==1 :
                self.tutorial_progress ["room2_chest_opened"]=True
                self.update_tutorial_floor_state ()
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
            self.update_player_images ()
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
            pos =(self.pl_x ,self.pl_y )
            if self.tutorial_enabled and self.floor ==1 and pos ==self.tutorial_room4_item_pos:
                self.dungeon [self.pl_y ][self.pl_x ]=0 
                self.treasure =5
                self.item_reward_count =1
                self.tool_magic_seed =self.tool_magic_seed +1
                self.tutorial_progress ["room4_item_obtained"]=True
                self.update_tutorial_floor_state ()
                self.idx =120
                self.tmr =0
                return
            if self.tutorial_enabled and self.floor ==1 and pos ==self.tutorial_room5_enemy_pos:
                self.dungeon [self.pl_y ][self.pl_x ]=0
                self.truth_fragment_drop_battle =False
                self.tutorial_pending_battle ="room5"
                self.idx =200
                self.tmr =0
                return
            self.dungeon [self.pl_y ][self.pl_x ]=0 
            r =random .randint (0 ,99 )
            if r <35 :# 食料
                self.treasure =random .choice ([3 ,3 ,3 ,3 ,3 ,4 ,4 ,4 ,4 ,4 ,5 ])
                self.item_reward_count =random .randint (1 ,max (1 ,self.floor //10 ))
                if self.treasure ==3 :
                    self.tool_food =self.tool_food +self.item_reward_count
                if self.treasure ==4 :
                    self.tool_magic_water =self.tool_magic_water +self.item_reward_count
                if self.treasure ==5 :
                    self.tool_magic_seed =self.tool_magic_seed +self.item_reward_count
                self.idx =120 
                self.tmr =0 
            else :# 敵出現
                self.truth_fragment_drop_battle =False
                self.idx =200 
                self.tmr =0 
            return 
        if self.dungeon [self.pl_y ][self.pl_x ]==10 :# しんじつのかけら繭
            self.dungeon [self.pl_y ][self.pl_x ]=0
            self.truth_fragment_drop_battle =True
            if self.tutorial_enabled and self.floor ==1 and (self.pl_x ,self.pl_y )==self.tutorial_room3_truth_pos:
                self.tutorial_pending_battle ="room3"
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
            if self.dungeon [self.pl_y -1 ][self.pl_x ] not in (7 ,8 ,9 ) and not self.is_boss_tile (self.pl_x ,self.pl_y -1 ):
                self.pl_y =self.pl_y -1 
        if key [K_DOWN ]==1 :
            self.pl_d =1 
            if self.dungeon [self.pl_y +1 ][self.pl_x ] not in (7 ,8 ,9 ) and not self.is_boss_tile (self.pl_x ,self.pl_y +1 ):
                self.pl_y =self.pl_y +1 
        if key [K_LEFT ]==1 :
            self.pl_d =2 
            if self.dungeon [self.pl_y ][self.pl_x -1 ] not in (7 ,8 ,9 ) and not self.is_boss_tile (self.pl_x -1 ,self.pl_y ):
                self.pl_x =self.pl_x -1 
        if key [K_RIGHT ]==1 :
            self.pl_d =3 
            if self.dungeon [self.pl_y ][self.pl_x +1 ] not in (7 ,8 ,9 ) and not self.is_boss_tile (self.pl_x +1 ,self.pl_y ):
                self.pl_x =self.pl_x +1 
        self.pl_a =self.pl_d *3 +2 
        if self.pl_x !=x or self.pl_y !=y :
            walk_cycle =[0 ,2 ,1 ,2 ]
            self.pl_a =self.pl_d *3 +walk_cycle [self.tmr %4 ]# 移動したら足踏みのアニメーション

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
        self.pl_level =1 
        self.potion =0 
        self.blazegem =0 
        self.guard =0 
        self.truth_fragment =0
        self.tool_food =0
        self.tool_magic_water =0
        self.tool_magic_seed =0
        self.truth_fragment_drop_battle =False
        self.save_from_stair = False
        self.save_from_boss = False
        self.stair_save_slot = 0
        self.stair_choice_cmd = 0
        self.stair_prompted = False
        self.stair_choice_input_lock = False
        self.boss_save_cmd = 0
        self.boss_save_input_lock = False
        self.true_episode_heard = False
        self.encountered_enemies = set()
        self.idx =100 
        self.tmr =0 
        self.pl_shield =[[0 ,0 ],[0 ,0 ],[0 ,0 ]]
        self.pl_armor =[[0 ,0 ],[0 ,0 ],[0 ,0 ]]
        self.pl_sword =[[0 ,0 ],[0 ,0 ],[0 ,0 ]]
        self.update_player_images ()
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
                self.pl_level =loaddata .get ("pl_level",1 )
                self.potion =loaddata ["potion"]
                self.blazegem =loaddata ["blazegem"]
                self.guard =loaddata ["guard"]
                self.truth_fragment =loaddata .get ("truth_fragment",0 )
                self.tool_food =loaddata .get ("tool_food",0 )
                self.tool_magic_water =loaddata .get ("tool_magic_water",0 )
                self.tool_magic_seed =loaddata .get ("tool_magic_seed",0 )
                self.truth_fragment_drop_battle =False
                self.save_from_stair = False
                self.save_from_boss = False
                self.stair_save_slot = 0
                self.stair_choice_cmd = 0
                self.stair_prompted = False
                self.stair_choice_input_lock = False
                self.boss_save_cmd = 0
                self.boss_save_input_lock = False
                self.pl_shield =loaddata ["shield"]
                self.pl_armor =loaddata ["armor"]
                self.pl_sword =loaddata ["sword"]
                self.update_player_images ()
                if "boss_pos" in loaddata and loaddata ["boss_pos"] is not None:
                    bx, by = loaddata ["boss_pos"]
                    self.boss_pos = (bx, by)
                    self.boss_area = {(bx, by)}
                else:
                    self.boss_pos = None
                    self.boss_area = set()
                self.true_episode_heard = bool(loaddata.get("true_episode_heard", False))
                self.encountered_enemies = set(loaddata.get("encountered_enemies", []))
                self.item_event_phase = 0
                self.item_choice = 0
                self.item_reward = None
                self.item_event_kind = ""
                self.item_talk_lines = []
                self.item_talk_index = 0
                self.item_talk_char_count = 0
                self.item_talk_last_tick = pygame.time.get_ticks()
                self.set_floor_assets_for_current_floor ()
                self.init_floor_variant_map ()
                self.init_map_state ()
                self.fixed_floor_data = self.load_fixed_floor_data (self.floor )
                if self.floor ==1 and self.fixed_floor_data:
                    self.setup_tutorial_floor (loaddata .get ("tutorial_progress"))
                else:
                    self.reset_tutorial_runtime ()
                self.move_bgm_path =self.path +"/sound/bgm_"+str ((self.floor-1) //10 )+".wav"
                self.move_bgm_pos_ms =0 
                self.move_bgm_start_time =time .time ()
                pygame .mixer .music .load (self.move_bgm_path )
                pygame .mixer .music .play (-1 )
                surf =pygame .display .get_surface ()
                if surf :
                    screen_w ,screen_h =surf .get_size ()
                    img_w ,img_h =self.imgBtlBG .get_size ()
                    scale =min (screen_w /img_w ,screen_h /img_h )
                    bg_w =max (1 ,int (img_w *scale ))
                    bg_h =max (1 ,int (img_h *scale ))
                    bg_left =(screen_w -bg_w )//2 
                    bg_top =(screen_h -bg_h )//2 
                    self.floor_title_pos =(bg_left +bg_w //2 -42 ,bg_top +int (bg_h *0.4 ))
                else :
                    self.floor_title_pos =None
                self.floor_title_active = True
                self.idx =110
                self.tmr =6

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
            # Show floor title after prologue using transition screen.
            bg_rect =self.blit_scaled_bg (bg ,self.imgBtlBG ,0 ,0 ,False )
            bg_left ,bg_top ,bg_w ,bg_h =bg_rect
            self.floor_title_active = True
            self.floor_title_pos = (bg_left +bg_w //2 -42 ,bg_top +int (bg_h *0.4 ))
            self.idx =110
            self.tmr =6
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
                # Show floor title after prologue using transition screen.
                bg_left ,bg_top ,bg_w ,bg_h =bg_rect
                self.floor_title_active = True
                self.floor_title_pos = (bg_left +bg_w //2 -42 ,bg_top +int (bg_h *0.4 ))
                self.idx =110
                self.tmr =6
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

        self.draw_text (bg ,f"傷薬: {self.potion}",X +10 ,Y +8 ,fnt ,WHITE )
        self.draw_text (bg ,f"爆弾: {self.blazegem}",X +110 ,Y +8 ,fnt ,WHITE )
        self.draw_text (bg ,f"守護: {self.guard}",X +210 ,Y +8 ,fnt ,WHITE )

        col =WHITE 
        if self.pl_life <int (self.pl_lifemax /5 )and self.tmr %2 ==0 :col =RED 
        self.draw_text (bg ,f"生命　{self.pl_life}/{self.pl_lifemax}",X +10 ,Y +40 ,fnt ,col )
        self.draw_text (bg ,f"攻撃　{self.pl_str}",X +10 ,Y +65 ,fnt ,WHITE )
        self.draw_text (bg ,f"魔力　{self.pl_mag}",X +10 ,Y +90 ,fnt ,WHITE )
        self.draw_text (bg ,f"レベル　{self.pl_level}　　経験　{self.pl_exp}/{(self.pl_lifemax -250 )*20}",X +10 ,Y +115 ,fnt ,WHITE )

        self.draw_text (bg ,f"盾　{self.pl_shield[0][1]}-{self.pl_shield[1][1]}-{self.pl_shield[2][1]}",X +180 ,Y +40 ,fnt ,WHITE )
        self.draw_text (bg ,f"鎧　{self.pl_armor[0][1]}-{self.pl_armor[1][1]}-{self.pl_armor[2][1]}",X +180 ,Y +65 ,fnt ,WHITE )
        self.draw_text (bg ,f"剣　{self.pl_sword[0][1]}-{self.pl_sword[1][1]}-{self.pl_sword[2][1]}",X +180 ,Y +90 ,fnt ,WHITE )

    def update_minimap_grid (self ,new_seen ):
        if self.map_grid_surface is None or self.map_grid_surface.get_size ()!=(DUNGEON_W ,DUNGEON_H ):
            self.map_grid_surface = pygame.Surface((DUNGEON_W, DUNGEON_H), pygame.SRCALPHA)
            self.map_grid_surface.fill((0, 0, 0, 120))
            for y in range (DUNGEON_H ):
                row =self.map_seen [y ]
                for x in range (DUNGEON_W ):
                    if row [x ]and self.dungeon [y ][x ] not in (7 ,8 ,9 ) :
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
        for bx ,by in self.map_bosses :
            mx =int (bx *scale )
            my =int (by *scale )
            bg .fill ((255 ,255 ,255 ,200 ),[map_x +mx ,map_y +my ,marker ,marker ])
        px =int (self.pl_x *scale )
        py =int (self.pl_y *scale )
        bg .fill ((255 ,0 ,0 ,200 ),[map_x +px ,map_y +py ,marker ,marker ])

    def init_battle (self ):
        self.emy_skip_turn = False
        self.emy_typ =random .randint (0 ,EMY_APPEAR [self.floor -1 ])
        self.encountered_enemies.add(self.emy_typ)
        geta =((self.floor -1 )//90 )*(9 -self.emy_typ )*10
        if self.emy_typ ==10 :
            self.emy_typ =22 
            geta =0 
        self.lev =random .randint (1 ,self.floor )
        self.imgEnemy =pygame .image .load (self.path +"/image/enemy"+str (self.emy_typ )+"_"+str ((self.floor -1 )//30 )+".png")
        new_w =int (self.imgEnemy .get_width ()*1.1 )
        new_h =int (self.imgEnemy .get_height ()*1.1 )
        self.imgEnemy =pygame .transform .scale (self.imgEnemy ,(new_w ,new_h ))
        self.emy_name =EMY_NAME [self.emy_typ ]
        self.emy_lifemax =int ((73 *(self.emy_typ +1 )+EMY_LIFE [self.emy_typ ])*(1.2 *((self.floor -1 )//30 )+1 ))+(self.lev -1 )*8 +geta *3 
        self.emy_life =self.emy_lifemax 
        self.emy_str =int (self.emy_lifemax /7 +EMY_STR [self.emy_typ ]*(0.5 *((self.floor -1 )//30 )+1 ))+geta 
        screen =pygame .display .get_surface ()
        screen_w ,screen_h =screen .get_size ()
        self.emy_x =screen_w //2 -self.imgEnemy .get_width ()//2 
        self.emy_y =1.45*screen_h //2 -self.imgEnemy .get_height () 

    def init_bossbattle (self ):
        self.emy_skip_turn = False
        base_typ =9 +int (self.floor //10 )
        if 90 <self.floor <100 :
            base_typ =9 +int (self.floor %10 )
        elif self.floor ==100 :
            base_typ =20
        self.emy_typ =base_typ + self.change#10~
        self.encountered_enemies.add(self.emy_typ)
        geta =((self.floor -1 )//90 )*(19 -self.emy_typ )*30
        self.imgEnemy =pygame .image .load (self.path +"/image/boss_"+str (self.emy_typ -10 )+".png")
        new_w =int (self.imgEnemy .get_width ()*1.1 )
        new_h =int (self.imgEnemy .get_height ()*1.1 )
        self.imgEnemy =pygame .transform .scale (self.imgEnemy ,(new_w ,new_h ))
        self.emy_name =EMY_NAME [self.emy_typ ]
        self.emy_lifemax =EMY_LIFE [self.emy_typ ]+geta *20 
        self.emy_life =self.emy_lifemax 
        self.emy_str =EMY_STR [self.emy_typ ]+geta 
        screen =pygame .display .get_surface ()
        screen_w ,screen_h =screen .get_size ()
        self.emy_x =screen_w //2 -self.imgEnemy .get_width ()//2 
        self.emy_y =1.45*screen_h //2 -self.imgEnemy .get_height ()

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
            self.draw_text (bg ,f"火傷",bg_left +40 ,bg_top +82 ,fnt ,RED )
        if self.pow_up >1 :
            self.draw_text (bg ,f"力↑",bg_left +40 ,bg_top +82 ,fnt ,RED )
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
            self.draw_text (bg ,f"守護 {'・'*self.guard_remain}",para_x +30 ,status_y ,fnt ,GREEN )
        if self.poison >0 :
            self.draw_text (bg ,f"毒 {'・'*self.poison}",para_x +100 ,status_y ,fnt ,COPPER )
        for i in range (10 ):# 戦闘メッセージの表示
            self.draw_text (bg ,self.message [i ],msg_x +30 ,msg_y +40 +i *48 ,fnt ,WHITE )
        if self.boss ==0 :
            self.draw_text (bg ,f"{self.emy_name}  Lv.{self.lev}",bg_left +40 ,bg_top +30 ,fnt ,WHITE )
        else :
            self.draw_text (bg ,f"{self.emy_name}",bg_left +40 ,bg_top +30 ,fnt ,WHITE )
        self.draw_para (bg ,fnt ,bg_rect )# 主人公の能力を表示

    def menu_command (self ,bg ,fnt ,key ):
        ent =False 
        options = ["図鑑を見る", "どうぐをみる", "タイトルに戻る", "メニューを閉じる"]
        if self.menu_cmd >=len (options ):
            self.menu_cmd =len (options )-1 
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

    def draw_tool_inventory (self ,bg ,fnt ):
        tools =self.get_tool_entries ()
        win_w =520
        line_h =36
        header_h =46
        win_h =header_h +line_h *len (tools )+40
        screen_w ,screen_h =bg .get_size ()
        win_x =(screen_w -win_w )//2
        win_y =(screen_h -win_h )//2
        pygame .draw .rect (bg ,BLACK ,[win_x ,win_y ,win_w ,win_h ])
        pygame .draw .rect (bg ,WHITE ,[win_x ,win_y ,win_w ,win_h ],2 )
        self.draw_text (bg ,"どうぐ一覧",win_x +20 ,win_y +12 ,fnt ,WHITE )
        start_y =win_y +header_h
        for i, tool in enumerate (tools ):
            name =tool ["name"]
            count =tool ["count"]
            y =start_y +i *line_h
            if i ==self.tool_cmd and not self.tool_confirm_active:
                self.draw_text (bg ,"▶",win_x +8 ,y ,fnt ,WHITE )
            self.draw_text (bg ,name ,win_x +28 ,y ,fnt ,WHITE )
            cnt =f"x {count}"
            cnt_w =fnt .size (cnt )[0 ]
            self.draw_text (bg ,cnt ,win_x +win_w -30 -cnt_w ,y ,fnt ,WHITE )
        if len (tools )==0 :
            self.draw_text (bg ,"（どうぐなし）",win_x +28 ,start_y ,fnt ,WHITE )
        self.draw_text (bg ,"[B]/[Back] 戻る",win_x +win_w -170 ,win_y +win_h -32 ,fnt ,WHITE )
        if self.tool_confirm_active and len (tools )>0 :
            confirm_options =["はい","いいえ"]
            box_w =220
            box_h =96
            box_x =win_x +win_w -box_w -20
            box_y =win_y +win_h -box_h -46
            pygame .draw .rect (bg ,BLACK ,[box_x ,box_y ,box_w ,box_h ])
            pygame .draw .rect (bg ,WHITE ,[box_x ,box_y ,box_w ,box_h ],2 )
            self.draw_text (bg ,"使用しますか？",box_x +16 ,box_y +10 ,fnt ,WHITE )
            for i, label in enumerate (confirm_options ):
                y =box_y +44 +i *24
                if self.tool_confirm_cmd ==i :
                    self.draw_text (bg ,"▶",box_x +16 ,y ,fnt ,WHITE )
                self.draw_text (bg ,label ,box_x +42 ,y ,fnt ,WHITE )

    def get_tool_entries (self ):
        tools =[]
        if self.truth_fragment >0 :
            tools .append ({"id":"truth_fragment","name":"しんじつのかけら","count":self.truth_fragment ,"usable":False })
        if self.tool_food >0 :
            tools .append ({"id":"food","name":TRE_NAME [3 ],"count":self.tool_food ,"usable":True })
        if self.tool_magic_water >0 :
            tools .append ({"id":"magic_water","name":TRE_NAME [4 ],"count":self.tool_magic_water ,"usable":True })
        if self.tool_magic_seed >0 :
            tools .append ({"id":"magic_seed","name":TRE_NAME [5 ],"count":self.tool_magic_seed ,"usable":True })
        return tools

    def use_selected_tool (self ,tool_id ):
        if tool_id =="food" and self.tool_food >0 :
            self.tool_food -=1 
            self.pl_life =min (self.pl_life +40 ,self.pl_lifemax )
        elif tool_id =="magic_water" and self.tool_magic_water >0 :
            self.tool_magic_water -=1 
            self.pl_life =min (self.pl_life +20 ,self.pl_lifemax )
            self.pl_mag =self.pl_mag +40 
        elif tool_id =="magic_seed" and self.tool_magic_seed >0 :
            self.tool_magic_seed -=1 
            self.pl_mag =self.pl_mag +120 
            if self.tutorial_enabled and self.floor ==1 :
                self.tutorial_progress ["room4_item_used"]=True
                self.update_tutorial_floor_state ()

    def get_zukan_layout(self):
        if self.zukan_kind == 0:
            return 4, 7, len(EMY_NAME), "敵の図鑑"
        if self.zukan_kind == 1:
            return 3, 1, 3, "アイテムの図鑑"
        return 3, 3, 9, "武器の図鑑"

    def is_weapon_owned_for_zukan(self, weapon_index):
        trap_id = weapon_index + 2
        if trap_id % 3 == 2:
            slot = trap_id // 3
            return self.pl_shield[slot][0] > 0
        if trap_id % 3 == 0:
            slot = trap_id // 3 - 1
            return self.pl_armor[slot][0] > 0
        slot = trap_id // 3 - 1
        return self.pl_sword[slot][0] > 0

    def is_enemy_encountered_for_zukan(self, enemy_index):
        return enemy_index in self.encountered_enemies

    def get_enemy_catalog_image(self, enemy_id):
        if enemy_id in self.zukan_enemy_cache:
            return self.zukan_enemy_cache[enemy_id]
        paths = [self.path + f"/image/enemy{enemy_id}_{i}.png" for i in range(4)]
        if enemy_id >= 10:
            paths.append(self.path + f"/image/boss_{enemy_id - 10}.png")
        img = None
        for path in paths:
            if os.path.exists(path):
                img = pygame.image.load(path)
                break
        if img is None:
            img = pygame.Surface((240, 240), pygame.SRCALPHA)
            img.fill((40, 40, 40, 255))
            pygame.draw.rect(img, WHITE, [0, 0, 240, 240], 2)
        self.zukan_enemy_cache[enemy_id] = img
        return img

    def zukan_category_command(self, bg, fnt, key):
        ent = False
        options = ["敵の図鑑", "アイテムの図鑑", "武器の図鑑"]
        if key[K_UP] and self.zukan_menu_cmd > 0:
            self.zukan_menu_cmd -= 1
        if key[K_DOWN] and self.zukan_menu_cmd < len(options) - 1:
            self.zukan_menu_cmd += 1
        if key[K_RETURN] or key[K_a]:
            ent = True
        win_w = 360
        line_h = 32
        win_h = line_h * len(options) + 20
        screen_w, screen_h = bg.get_size()
        win_x = (screen_w - win_w) // 2
        win_y = (screen_h - win_h) // 2
        pygame.draw.rect(bg, BLACK, [win_x, win_y, win_w, win_h])
        pygame.draw.rect(bg, WHITE, [win_x, win_y, win_w, win_h], 2)
        for i, label in enumerate(options):
            y = win_y + 10 + i * line_h
            if self.zukan_menu_cmd == i:
                self.draw_text(bg, "▶", win_x + 20, y, fnt, WHITE)
            self.draw_text(bg, label, win_x + 50, y, fnt, WHITE)
        return ent

    def zukan_grid_command(self, bg, fnt, key):
        ent = False
        cols, rows, count, title = self.get_zukan_layout()
        if count <= 0:
            return ent
        if self.zukan_cursor >= count:
            self.zukan_cursor = count - 1
        row = self.zukan_cursor // cols
        col = self.zukan_cursor % cols
        if key[K_UP] and row > 0:
            nxt = self.zukan_cursor - cols
            if nxt < count:
                self.zukan_cursor = nxt
        if key[K_DOWN] and row < rows - 1:
            nxt = self.zukan_cursor + cols
            if nxt < count:
                self.zukan_cursor = nxt
        if key[K_LEFT] and col > 0:
            nxt = self.zukan_cursor - 1
            if nxt < count:
                self.zukan_cursor = nxt
        if key[K_RIGHT] and col < cols - 1:
            nxt = self.zukan_cursor + 1
            if nxt < count:
                self.zukan_cursor = nxt
        if key[K_RETURN] or key[K_a]:
            ent = True

        cell = 72
        gap = 10
        pad = 20
        title_h = 30
        win_w = pad * 2 + cols * cell + (cols - 1) * gap
        win_h = pad * 2 + rows * cell + (rows - 1) * gap + title_h
        screen_w, screen_h = bg.get_size()
        win_x = (screen_w - win_w) // 2
        win_y = (screen_h - win_h) // 2
        pygame.draw.rect(bg, BLACK, [win_x, win_y, win_w, win_h])
        pygame.draw.rect(bg, WHITE, [win_x, win_y, win_w, win_h], 2)
        self.draw_text(bg, title, win_x + 20, win_y + 8, fnt, WHITE)

        start_x = win_x + pad
        start_y = win_y + pad + title_h
        total = cols * rows
        item_names = ["傷薬", "爆弾", "守護"]
        for i in range(total):
            r = i // cols
            c = i % cols
            x = start_x + c * (cell + gap)
            y = start_y + r * (cell + gap)
            if i < count:
                pygame.draw.rect(bg, WHITE, [x, y, cell, cell], 1)
                if self.zukan_kind == 0:
                    label = str(i) if self.is_enemy_encountered_for_zukan(i) else "？"
                elif self.zukan_kind == 1:
                    label = item_names[i]
                else:
                    label = TRAP_NAME[i + 2] if self.is_weapon_owned_for_zukan(i) else "？"
                self.draw_text(bg, label, x + 8, y + cell // 2 - 10, fnt, WHITE)
            else:
                pygame.draw.rect(bg, (80, 80, 80), [x, y, cell, cell], 1)
            if i == self.zukan_cursor:
                pygame.draw.rect(bg, (255, 220, 90), [x, y, cell, cell], 3)

        return ent

    def draw_zukan_detail(self, bg, fnt):
        win_w = 760
        win_h = 430
        screen_w, screen_h = bg.get_size()
        win_x = (screen_w - win_w) // 2
        win_y = (screen_h - win_h) // 2
        pygame.draw.rect(bg, BLACK, [win_x, win_y, win_w, win_h])
        pygame.draw.rect(bg, WHITE, [win_x, win_y, win_w, win_h], 2)

        if self.zukan_kind == 0:
            enemy_id = self.zukan_detail
            name = EMY_NAME[enemy_id] if 0 <= enemy_id < len(EMY_NAME) else f"Enemy {enemy_id}"
            info = ENEMY_INFO.get(enemy_id, "情報が登録されていません。")
            img = self.get_enemy_catalog_image(enemy_id)
            max_w = 260
            max_h = 260
            scale = min(max_w / max(1, img.get_width()), max_h / max(1, img.get_height()))
            draw_img = pygame.transform.scale(img, (max(1, int(img.get_width() * scale)), max(1, int(img.get_height() * scale))))
            img_x = win_x + 30 + (max_w - draw_img.get_width()) // 2
            img_y = win_y + 90 + (max_h - draw_img.get_height()) // 2
            bg.blit(draw_img, [img_x, img_y])
            pygame.draw.rect(bg, WHITE, [win_x + 30, win_y + 90, max_w, max_h], 1)
        elif self.zukan_kind == 1:
            item_names = ["傷薬", "爆弾", "守護"]
            item_id = self.zukan_detail
            name = item_names[item_id] if 0 <= item_id < len(item_names) else f"Item {item_id}"
            info = ITEM_INFO.get(item_id, "情報が登録されていません。")
            pygame.draw.rect(bg, WHITE, [win_x + 30, win_y + 90, 260, 260], 2)
            self.draw_text(bg, name, win_x + 70, win_y + 210, fnt, WHITE)
        else:
            weapon_id = self.zukan_detail + 2
            name = TRAP_NAME[weapon_id] if 0 <= weapon_id < len(TRAP_NAME) else f"Weapon {weapon_id}"
            info = WEAPON_INFO.get(weapon_id, "情報が登録されていません。")
            pygame.draw.rect(bg, WHITE, [win_x + 30, win_y + 90, 260, 260], 2)
            self.draw_text(bg, name, win_x + 55, win_y + 210, fnt, WHITE)

        self.draw_text(bg, name, win_x + 320, win_y + 45, self.get_font(22), WHITE)
        parts = str(info).split("\n")
        for i, part in enumerate(parts):
            self.draw_text(bg, part, win_x + 320, win_y + 110 + i * 28, fnt, WHITE)
        self.draw_text(bg, "[B]/[Back] Back", win_x + win_w - 180, win_y + win_h - 36, fnt, WHITE)

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

    def stair_choice_command (self ,bg ,fnt ,key ,enable_input =True ):
        ent =False 
        options =[
            "下の階に移動",
            "下の階に移動＋データセーブ",
            "移動しない",
        ]
        if enable_input:
            if key [K_UP ]and self.stair_choice_cmd >0 :
                self.stair_choice_cmd -=1 
            if key [K_DOWN ]and self.stair_choice_cmd <len (options )-1 :
                self.stair_choice_cmd +=1 
            if key [K_RETURN ]or key [K_a ]:
                ent =True 
        win_w =560 
        line_h =32 
        win_h =line_h *len (options )+20 
        screen_w ,screen_h =bg .get_size ()
        win_x =(screen_w -win_w )//2 
        win_y =(screen_h -win_h )//2 
        pygame .draw .rect (bg ,BLACK ,[win_x ,win_y ,win_w ,win_h ])
        pygame .draw .rect (bg ,WHITE ,[win_x ,win_y ,win_w ,win_h ],2 )
        for i, label in enumerate (options ):
            y =win_y +10 +i *line_h 
            if self.stair_choice_cmd ==i :
                self.draw_text (bg ,"▶",win_x +20 ,y ,fnt ,WHITE )
            self.draw_text (bg ,label ,win_x +50 ,y ,fnt ,WHITE )
        return ent 

    def boss_save_choice_command (self ,bg ,fnt ,key ,enable_input =True ):
        ent =False 
        options =["はい","いいえ"]
        if enable_input:
            if key [K_UP ]and self.boss_save_cmd >0 :
                self.boss_save_cmd -=1 
            if key [K_DOWN ]and self.boss_save_cmd <len (options )-1 :
                self.boss_save_cmd +=1 
            if key [K_RETURN ]or key [K_a ]:
                ent =True 
        view_rect =getattr (self ,"dungeon_view_rect",None )
        if view_rect :
            view_left ,view_top ,view_w ,view_h =view_rect
        else :
            view_left =0 
            view_top =0 
            view_w ,view_h =bg .get_size ()
        scale_x =view_w /880 
        scale_y =view_h /720 
        dlg_x =view_left +int (40 *scale_x )
        dlg_y =view_top +int (525 *scale_y )
        dlg_w =max (1 ,int (800 *scale_x ))
        dlg_h =max (1 ,int (160 *scale_y ))
        text_x =view_left +int (60 *scale_x )
        text_y =view_top +int (560 *scale_y )
        dialog =pygame .Surface ((dlg_w ,dlg_h ),pygame .SRCALPHA )
        dialog .fill ((0 ,0 ,0 ,255 ))
        bg .blit (dialog ,[dlg_x ,dlg_y ])
        pygame .draw .rect (bg ,WHITE ,[dlg_x ,dlg_y ,dlg_w ,dlg_h ],2 )
        self.draw_text (bg ,"セーブしますか？",text_x ,text_y ,fnt ,WHITE )
        sel_line_h =max (1 ,int (25 *scale_y ))
        box_h =max (1 ,int (15 *scale_y ))+sel_line_h *len (options )
        box_w =max (1 ,int (280 *scale_x ))
        box_x =view_left +int (520 *scale_x )
        box_y =view_top +int (420 *scale_y )
        arrow_x =view_left +int (540 *scale_x )
        text_sel_x =view_left +int (560 *scale_x )
        arrow_y =view_top +int (435 *scale_y )
        pygame .draw .rect (bg ,BLACK ,[box_x ,box_y ,box_w ,box_h ])
        pygame .draw .rect (bg ,WHITE ,[box_x ,box_y ,box_w ,box_h ],2 )
        for i, option in enumerate(options):
            if i == self.boss_save_cmd:
                self.draw_text (bg ,"▶",arrow_x ,arrow_y + i *sel_line_h ,fnt ,WHITE )
            self.draw_text (bg ,option ,text_sel_x ,arrow_y + i *sel_line_h ,fnt ,WHITE )
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
                self.set_message ("　鎧の癒し 生命+{}" .format (cure ))
                self.se [2 ].play ()
            else :
                self.tmr =self.tmr +1 
        if self.pl_armor [1 ][0 ]==1 :
            if random .random ()>0.7 :
                mgup =int (10 +self.pl_armor [1 ][1 ]*0.7 +random .randint (0 ,self.pl_armor [1 ][1 ]//5 ))
                self.pl_mag =self.pl_mag +mgup 
                self.set_message ("　鎧の魔力 魔力+{}" .format (mgup ))
                self.se [9 ].play ()
            else :
                self.tmr =self.tmr +1 

    def emy_action (self ,bg ):
        action =True 
        if self.emy_typ ==4 or self.emy_typ ==15 :
            self.pow_up =1 
            if random .random ()>0.7 :
                self.pow_up ={4:2 ,15:3 }[self.emy_typ ]
                self.set_message ("　敵は　力をためた!")
            action =False 
        if self.emy_typ ==5 or self.emy_typ ==12:
            suck = {5:5+self.lev, 12:104}[self.emy_typ] + random .randint (1 ,self.emy_typ )
            suck = min(suck, self.pl_mag)
            self.set_message (f"　魔力を　{suck}　吸収された!")
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
        if self.emy_typ ==8 or self.emy_typ ==11:
            if random .random ()>{8:0.3, 11:0.84}[self.emy_typ]:
                self.poison ={8:1, 11:2}[self.emy_typ]
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
                    self.truth_fragment =0
                    self.tool_food =0
                    self.tool_magic_water =0
                    self.tool_magic_seed =0
                    self.truth_fragment_drop_battle =False
                    pygame .mixer .music .load (self.path +"/sound/bgm_title.wav")
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
                    if key [K_b ]or key [K_BACKSPACE ]:
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
                            self.pl_level =loaddata .get ("pl_level",1 )
                            self.potion =loaddata ["potion"]
                            self.blazegem =loaddata ["blazegem"]
                            self.guard =loaddata ["guard"]
                            self.truth_fragment =loaddata .get ("truth_fragment",0 )
                            self.tool_food =loaddata .get ("tool_food",0 )
                            self.tool_magic_water =loaddata .get ("tool_magic_water",0 )
                            self.tool_magic_seed =loaddata .get ("tool_magic_seed",0 )
                            self.truth_fragment_drop_battle =False
                            self.idx =100 
                            self.pl_shield =loaddata ["shield"]
                            self.pl_armor =loaddata ["armor"]
                            self.pl_sword =loaddata ["sword"]
                            self.update_player_images ()
                            if "boss_pos" in loaddata and loaddata ["boss_pos"] is not None:
                                bx, by = loaddata ["boss_pos"]
                                self.boss_pos = (bx, by)
                                self.boss_area = {(bx, by)}
                            else:
                                self.boss_pos = None
                                self.boss_area = set()
                            self.true_episode_heard = bool(loaddata.get("true_episode_heard", False))
                            self.item_event_phase = 0
                            self.item_choice = 0
                            self.item_reward = None
                            self.item_event_kind = ""
                            self.item_talk_lines = []
                            self.item_talk_index = 0
                            self.item_talk_char_count = 0
                            self.item_talk_last_tick = pygame.time.get_ticks()
                            self.set_floor_assets_for_current_floor ()
                            self.init_floor_variant_map ()
                            self.init_map_state ()
                            self.fixed_floor_data = self.load_fixed_floor_data (self.floor )
                            if self.floor ==1 and self.fixed_floor_data:
                                self.setup_tutorial_floor (loaddata .get ("tutorial_progress"))
                            else:
                                self.reset_tutorial_runtime ()
                            self.move_bgm_path =self.path +"/sound/bgm_"+str ((self.floor-1) //10 )+".wav"
                            self.move_bgm_pos_ms =0 
                            self.move_bgm_start_time =time .time ()
                            pygame .mixer .music .load (self.move_bgm_path )
                            pygame .mixer .music .play (-1 )

            elif self.idx ==30 :#メニュー
                self.draw_dungeon (screen ,fontS )
                if self.menu_back_lock:
                    if not (key [K_b ]or key [K_BACKSPACE ]):
                        self.menu_back_lock = False
                if self.menu_accept_lock:
                    if not (key [K_RETURN ]or key [K_a ]):
                        self.menu_accept_lock = False
                if (key [K_b ]or key [K_BACKSPACE ]) and not self.menu_back_lock:
                    self.idx =100 
                    self.tmr =0 
                else:
                    ent = self.menu_command (screen ,fontS ,key )
                    if self.menu_accept_lock:
                        ent = False
                    if ent == True :
                        if self.menu_cmd ==0 :#zukan
                            self.zukan_menu_cmd =0
                            self.zukan_kind =0
                            self.zukan_cursor =0
                            self.zukan_detail =0
                            self.zukan_accept_lock = True
                            self.idx =31
                            self.tmr =0
                        elif self.menu_cmd ==1 :#tools
                            self.tool_back_lock =True
                            self.tool_accept_lock = True
                            self.tool_confirm_active = False
                            self.tool_confirm_cmd = 0
                            self.tool_cmd = 0
                            self.idx =34
                            self.tmr =0
                        elif self.menu_cmd ==2 :#go_title
                            self.confirm_cmd =0 
                            self.title_confirm_lock = True
                            self.idx =60 
                            self.tmr =0 
                        elif self.menu_cmd ==3 :#close
                            self.idx =100 
                            self.tmr =0 

            elif self.idx ==31 :# 図鑑カテゴリ選択
                self.draw_dungeon (screen ,fontS )
                if self.zukan_back_lock:
                    if not (key [K_b ]or key [K_BACKSPACE ]):
                        self.zukan_back_lock = False
                if self.zukan_accept_lock:
                    if not (key [K_RETURN ]or key [K_a ]):
                        self.zukan_accept_lock = False
                if (key [K_b ]or key [K_BACKSPACE ]) and not self.zukan_back_lock:
                    self.zukan_back_lock = True
                    self.menu_back_lock = True
                    self.idx =30
                    self.tmr =0
                else:
                    ent = self.zukan_category_command (screen ,fontS ,key )
                    if self.zukan_accept_lock:
                        ent = False
                    if ent:
                        self.zukan_kind = self.zukan_menu_cmd
                        self.zukan_cursor =0
                        self.zukan_detail =0
                        self.zukan_accept_lock = True
                        self.idx =32
                        self.tmr =0

            elif self.idx ==32 :# 図鑑グリッド
                self.draw_dungeon (screen ,fontS )
                if self.zukan_back_lock:
                    if not (key [K_b ]or key [K_BACKSPACE ]):
                        self.zukan_back_lock = False
                if self.zukan_accept_lock:
                    if not (key [K_RETURN ]or key [K_a ]):
                        self.zukan_accept_lock = False
                if (key [K_b ]or key [K_BACKSPACE ]) and not self.zukan_back_lock:
                    self.zukan_back_lock = True
                    self.idx =31
                    self.tmr =0
                else:
                    ent = self.zukan_grid_command (screen ,fontS ,key )
                    if self.zukan_accept_lock:
                        ent = False
                    if ent:
                        cols ,rows ,count ,_ =self.get_zukan_layout ()
                        if 0 <=self.zukan_cursor <count:
                            if self.zukan_kind ==0 and not self.is_enemy_encountered_for_zukan (self.zukan_cursor ):
                                self.zukan_accept_lock = True
                            elif self.zukan_kind ==2 and not self.is_weapon_owned_for_zukan (self.zukan_cursor ):
                                self.zukan_accept_lock = True
                            else:
                                self.zukan_detail =self.zukan_cursor
                                self.zukan_accept_lock = True
                                self.idx =33
                                self.tmr =0

            elif self.idx ==33 :# 図鑑詳細
                self.draw_dungeon (screen ,fontS )
                self.draw_zukan_detail (screen ,fontS )
                if self.zukan_back_lock:
                    if not (key [K_b ]or key [K_BACKSPACE ]):
                        self.zukan_back_lock = False
                if (key [K_b ]or key [K_BACKSPACE ]) and not self.zukan_back_lock:
                    self.zukan_back_lock = True
                    self.idx =32
                    self.tmr =0

            elif self.idx ==34 :# どうぐ一覧
                self.draw_dungeon (screen ,fontS )
                self.draw_tool_inventory (screen ,fontS )
                if self.tool_back_lock:
                    if not (key [K_b ]or key [K_BACKSPACE ]):
                        self.tool_back_lock = False
                if self.tool_accept_lock:
                    if not (key [K_RETURN ]or key [K_a ]):
                        self.tool_accept_lock = False
                tool_entries =self.get_tool_entries ()
                if len (tool_entries )==0 :
                    self.tool_cmd =0
                elif self.tool_cmd >=len (tool_entries ):
                    self.tool_cmd =len (tool_entries )-1
                if self.tool_confirm_active:
                    if key [K_UP ]and self.tool_confirm_cmd >0 :
                        self.tool_confirm_cmd -=1 
                    if key [K_DOWN ]and self.tool_confirm_cmd <1 :
                        self.tool_confirm_cmd +=1 
                    if (key [K_b ]or key [K_BACKSPACE ]) and not self.tool_back_lock:
                        self.tool_back_lock = True
                        self.tool_confirm_active = False
                    elif accept and not self.tool_accept_lock:
                        if self.tool_confirm_cmd ==0 and len (tool_entries )>0 and tool_entries [self.tool_cmd ]["usable"]:
                            self.use_selected_tool (tool_entries [self.tool_cmd ]["id"])
                            tool_entries =self.get_tool_entries ()
                            if len (tool_entries )==0 :
                                self.tool_cmd =0
                            elif self.tool_cmd >=len (tool_entries ):
                                self.tool_cmd =len (tool_entries )-1
                        self.tool_confirm_active = False
                        self.tool_accept_lock = True
                else:
                    if (key [K_b ]or key [K_BACKSPACE ]) and not self.tool_back_lock:
                        self.tool_back_lock = True
                        self.menu_back_lock = True
                        self.idx =30
                        self.tmr =0
                    else:
                        if key [K_UP ]and self.tool_cmd >0 :
                            self.tool_cmd -=1 
                        if key [K_DOWN ]and len (tool_entries )>0 and self.tool_cmd <len (tool_entries )-1 :
                            self.tool_cmd +=1 
                        if accept and not self.tool_accept_lock and len (tool_entries )>0:
                            if tool_entries [self.tool_cmd ]["usable"]:
                                self.tool_confirm_active = True
                                self.tool_confirm_cmd = 0
                                self.tool_accept_lock = True

            elif self.idx ==40 :#セーブデータ選択
                if self.save_from_boss:
                    screen .fill (BLACK )
                else:
                    self.draw_dungeon (screen ,fontS )
                if self.save_command (screen ,fontS ,key )==True :
                    self.confirm_cmd =0 
                    self.save_confirm_lock = True
                    self.idx =50 
                    self.tmr =0 
                if key [K_b ]==1 or key [K_BACKSPACE ]==1 :
                    if self.save_from_boss:
                        self.save_from_boss = False
                        self.boss_save_input_lock = True
                        self.idx =112 
                        self.tmr =0 
                    elif self.save_from_stair:
                        self.save_from_stair = False
                        self.stair_choice_input_lock = True
                        self.idx =111 
                        self.tmr =0 
                    else:
                        self.menu_back_lock = True
                        self.idx =30 

            elif self.idx ==50 :#確認とセーブ
                if self.save_from_boss:
                    screen .fill (BLACK )
                else:
                    self.draw_dungeon (screen ,fontS )
                d ={
                "floor":self.floor ,
                "pl_lifemax":self.pl_lifemax ,
                "pl_life":self.pl_life ,
                "pl_mag":self.pl_mag ,
                "pl_str":self.pl_str ,
                "pl_exp":self.pl_exp ,
                "pl_level":self.pl_level ,
                "potion":self.potion ,
                "blazegem":self.blazegem ,
                "guard":self.guard ,
                "truth_fragment":self.truth_fragment ,
                "tool_food":self.tool_food ,
                "tool_magic_water":self.tool_magic_water ,
                "tool_magic_seed":self.tool_magic_seed ,
                "shield":self.pl_shield ,
                "armor":self.pl_armor ,
                "sword":self.pl_sword ,
                "dungeon":self.dungeon ,
                "pl_x":self.pl_x ,
                "pl_y":self.pl_y ,
                "boss_pos":self.boss_pos ,
                "true_episode_heard":self.true_episode_heard,
                "encountered_enemies":sorted(self.encountered_enemies),
                "tutorial_progress":self.tutorial_save_data ()
                }
                if key [K_b ]==1 or key [K_BACKSPACE ]==1 :
                    self.load_accept_lock = True
                    self.idx =40
                    self.tmr =0
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
                        if self.save_from_stair or self.save_from_boss:
                            self.stair_save_slot = self.save_cmd
                            self.idx =110 
                            self.tmr =0 
                        else:
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
                    if self.save_from_stair or self.save_from_boss:
                        self.stair_save_slot = self.save_cmd
                        self.idx =110 
                        self.tmr =0 
                    else:
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
                if key [K_BACKSPACE ]or key [K_b ]:
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
                    PL_TURN =[3 ,6 ,0 ,9 ]
                    self.pl_a =PL_TURN [self.tmr %4 ]
                    if self.tmr ==30 :self.pl_a =12 # 倒れた絵
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
                if self.dungeon [self.pl_y ][self.pl_x ]!=3 :
                    self.stair_prompted =False 
                elif not self.stair_prompted:
                    self.stair_prompted =True 
                    self.stair_choice_cmd =0 
                    self.stair_choice_input_lock = True
                    self.idx =111 
                    self.tmr =0 
                if self.idx ==100 and accept and self.pl_d == 0:
                    tx = self.pl_x
                    ty = self.pl_y - 1
                    if 0 <= ty < DUNGEON_H:
                        front_tile = self.dungeon[ty][tx]
                        if front_tile == 8:
                            self.init_event_talk ()
                            self.idx =132 
                            self.tmr =0 
                        elif front_tile == 7:
                            if self.tutorial_enabled and self.floor ==1:
                                stage =self.tutorial_stage_for_wall ((tx ,ty ))
                                if stage >0 and self.init_tutorial_talk (stage ):
                                    self.idx =132
                                    self.tmr =0
                            elif self.floor >= 91 and not self.all_cocoons_cleared():
                                pass
                            else:
                                if 91 <= self.floor <= 99:
                                    self.init_item_event (kind="item", reward_count=5)
                                elif self.floor == 100 and self.truth_fragment >= 100 and not self.true_episode_heard:
                                    self.init_item_event (kind="true_episode", lines=TRUE_EPISODE_TALK)
                                else:
                                    self.init_item_event ()
                                self.idx =131 
                                self.tmr =0 
                if self.idx ==100 and accept and self.boss_in_front ():
                    self.init_boss_talk ()
                    self.idx =130 
                    self.tmr =0 
                    self.boss =1 

            elif self.idx ==111 :# 階段選択
                self.draw_dungeon (screen ,fontS )
                if self.stair_choice_input_lock:
                    self.stair_choice_command (screen ,fontS ,key ,enable_input =False )
                    if not (key [K_UP ]or key [K_DOWN ]or key [K_LEFT ]or key [K_RIGHT ]or key [K_RETURN ]or key [K_a ]or key [K_b ]or key [K_BACKSPACE ]):
                        self.stair_choice_input_lock = False
                else:
                    if self.stair_choice_command (screen ,fontS ,key )==True :
                        if self.stair_choice_cmd ==0 :
                            self.save_from_stair = False
                            self.idx =110 
                            self.tmr =0 
                        elif self.stair_choice_cmd ==1 :
                            self.save_from_stair = True
                            self.load_accept_lock = True
                            self.idx =40 
                            self.tmr =0 
                        else :
                            self.save_from_stair = False
                            self.idx =100 
                            self.tmr =0 
                    if key [K_b ]or key [K_BACKSPACE ]:
                        self.save_from_stair = False
                        self.idx =100 
                        self.tmr =0 

            elif self.idx ==112 :# ボス戦後セーブ確認
                screen .fill (BLACK )
                if self.boss_save_input_lock:
                    self.boss_save_choice_command (screen ,fontS ,key ,enable_input =False )
                    if not (key [K_UP ]or key [K_DOWN ]or key [K_LEFT ]or key [K_RIGHT ]or key [K_RETURN ]or key [K_a ]or key [K_b ]or key [K_BACKSPACE ]):
                        self.boss_save_input_lock = False
                else:
                    if self.boss_save_choice_command (screen ,fontS ,key )==True :
                        if self.boss_save_cmd ==0 :
                            self.save_from_boss = True
                            self.load_accept_lock = True
                            self.idx =40 
                            self.tmr =0 
                        else :
                            self.save_from_boss = False
                            self.idx =110 
                            self.tmr =0 
                    # if key [K_b ]or key [K_BACKSPACE ]:
                    #     self.save_from_boss = False
                    #     self.idx =110 
                    #     self.tmr =0 

            elif self.idx ==110 :# 画面切り替え
                self.draw_dungeon (screen ,fontS )
                if self.floor_title_active and self.floor_title_pos :
                    disp_floor =self.floor
                    x ,y =self.floor_title_pos
                elif self.tmr == 1:
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
                    if self.save_from_stair or self.save_from_boss:
                        d ={
                        "floor":self.floor ,
                        "pl_lifemax":self.pl_lifemax ,
                        "pl_life":self.pl_life ,
                        "pl_mag":self.pl_mag ,
                        "pl_str":self.pl_str ,
                        "pl_exp":self.pl_exp ,
                        "pl_level":self.pl_level ,
                        "potion":self.potion ,
                        "blazegem":self.blazegem ,
                        "guard":self.guard ,
                        "truth_fragment":self.truth_fragment ,
                        "tool_food":self.tool_food ,
                        "tool_magic_water":self.tool_magic_water ,
                        "tool_magic_seed":self.tool_magic_seed ,
                        "shield":self.pl_shield ,
                        "armor":self.pl_armor ,
                        "sword":self.pl_sword ,
                        "dungeon":self.dungeon ,
                        "pl_x":self.pl_x ,
                        "pl_y":self.pl_y ,
                        "boss_pos":self.boss_pos ,
                        "true_episode_heard":self.true_episode_heard,
                        "encountered_enemies":sorted(self.encountered_enemies),
                        "tutorial_progress":self.tutorial_save_data ()
                        }
                        with open (self.path +"/savedata/data{}.json".format (self.stair_save_slot +1 ),"w")as f :
                            json .dump (d ,f )
                        se [9 ].play ()
                        self.floorlist [self.stair_save_slot ]=self.floor 
                        self.save_from_stair = False
                        self.save_from_boss = False
                        self.load_accept_lock = True
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
                    self.floor_title_active = False
                    self.floor_title_pos = None
                    self.idx =100 

            elif self.idx ==120 :# アイテム入手もしくはトラップ
                self.draw_dungeon (screen ,fontS )
                if self.tmr ==1 :
                    x = win_x + win_w//2 - 42
                    y = title_top +int (title_h *0.4 )
                dialog = pygame.Surface((400, 100), pygame.SRCALPHA)
                dialog.fill((0, 0, 0, 100))
                screen.blit(dialog, [x-100, y-40])
                item_text =TRE_NAME [self.treasure ]
                if self.treasure in (0 ,1 ,2 ,3 ,4 ,5 ):
                    item_text =f"{item_text} x {self.item_reward_count}"
                self.draw_text (screen ,item_text ,x ,y ,font ,WHITE )
                if self.tmr ==10 :
                    self.idx =100 

            elif self.idx ==121 :# 武器入手もしくはダメージ床
                self.draw_dungeon (screen ,fontS )
                if self.tmr ==1 :
                    x = win_x + win_w//2 - 42
                    y = title_top +int (title_h *0.4 )
                dialog = pygame.Surface((400, 100), pygame.SRCALPHA)
                dialog.fill((0, 0, 0, 100))
                screen.blit(dialog, [x-100, y-40])
                if self.trap ==0 :
                    self.draw_text (screen ,TRAP_NAME [self.trap ]+" {}".format (30 -10 *((self.floor -1 )//10 )),x ,y ,font ,WHITE )
                elif self.trap ==1 :
                    self.draw_text (screen ,TRAP_NAME [self.trap ]+" +{}".format (-20 +10 *((self.floor -1 )//10 )),x ,y ,font ,WHITE )
                else :
                    self.draw_text (screen ,TRAP_NAME [self.trap ]+" Lv. "+str (self.wpn_lev ),x ,y ,font ,WHITE )
                    # self.draw_text (screen ,TRAP_NAME [self.trap ]+" Lv. "+str (self.wpn_lev ) ,text_x ,text_y ,fontS ,WHITE )
                if self.tmr ==10 :
                    self.idx =100 

            elif self.idx ==130 :# ボス会話
                self.draw_dungeon (screen ,fontS )
                view_rect =getattr (self ,"dungeon_view_rect",None )
                view_left ,view_top ,view_w ,view_h =view_rect
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
                        self.truth_fragment_drop_battle =False
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
                            self.update_player_images ()
                            self.dungeon[self.pl_y - 1][self.pl_x] = 9
                            self.idx =121
                            self.tmr =0
                elif self.item_event_kind == "item":
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
                                    self.treasure = self.item_reward if self.item_reward is not None else self.item_choice                            
                                    self.dungeon[self.pl_y - 1][self.pl_x] = 9
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
                        if self.tutorial_enabled and self.tutorial_active_stage >0 :
                            self.complete_tutorial_talk ()
                        self.idx =100 
                        self.tmr =0 


            elif self.idx ==200 :# 戦闘開始
                if self.tmr ==1 :
                    if self.move_bgm_path :
                        now =time .time ()
                        self.move_bgm_pos_ms =int ((now -self.move_bgm_start_time )*1000 )
                    bg_idx = (self.floor - 1) // 10
                    if self.last_btl_bg_idx != bg_idx:
                        self.bg_cache.clear()
                        self.last_btl_bg_idx = bg_idx
                    self.imgBtlBG =pygame .image .load (self.path +f"/image/btlbg/btlbg{bg_idx}.png")
                    if self.boss ==1 :
                        self.init_bossbattle ()
                        battle_bgm ="bgm_battle_2.wav" if self.floor ==100 else "bgm_battle_1.wav"
                        pygame .mixer .music .load (self.path +"/sound/"+battle_bgm)
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
                if 2 <=self.tmr <=4 :
                    screen_w =screen .get_size ()[0 ]
                    eff_x =screen_w //2 +260 -self.tmr *120 
                    eff_y =-100 +self.tmr *120 
                    atk_effect =self.imgEffect [3 ]if self.pl_sword [0 ][0 ]==1 else self.imgEffect [0 ]
                    screen .blit (atk_effect ,[eff_x ,eff_y ])
                if self.tmr ==4 :
                    if self.pl_sword [0 ][0 ]==1 :
                        if random .random ()>0.7 :
                            cri =1 
                            se [0 ].play ()
                            self.set_message ("　会心の一撃！")
                    dmg =self.pl_str +random .randint (0 ,9 )-EMY_APRO [self.emy_typ ]
                    dmg =int (dmg *(1 +0.01 *cri *self.pl_sword [0 ][1 ]))+2 *self.pl_sword [0 ][1 ]+self.pl_sword [2 ][1 ]
                    dmg =max (1 +cri ,int (dmg /(2 *self.poison +1 )))
                    if self.emy_typ ==10 :
                        if random .random ()>0.7 :
                            self.set_message ("　攻撃は　防御された！")
                            dmg =int (dmg /2 )
                    if self.guard_remain >0 and self.emy_typ ==20 :
                        dmg =int (dmg *(0.35 -self.pl_shield [2 ][1 ]*0.002 ))
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
                blit_time =8
                if self.tmr <=blit_time :
                    magic_effect =self.imgEffect [4 ]if self.pl_sword [1 ][0 ]==1 else self.imgEffect [1 ]
                    zoom =(blit_time +1 -self.tmr )/blit_time
                    img_rz =pygame .transform .rotozoom (magic_effect ,30 *self.tmr ,zoom )
                    screen_w =screen .get_size ()[0 ]
                    eff_x =screen_w //2 -img_rz .get_width ()/2 
                    eff_y =360 -img_rz .get_height ()/2 +20
                    screen .blit (img_rz ,[eff_x ,eff_y ])
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
                blaze_effect =self.imgEffect [5 ]if self.pl_sword [2 ][0 ]==1 else self.imgEffect [2 ]
                blit_time = 8
                if self.tmr <=blit_time :
                    scale =(self.tmr -1 )/max (1 ,blit_time -1 )
                    if scale >0 :
                        new_w =max (1 ,int (blaze_effect .get_width ()*scale ))
                        new_h =max (1 ,int (blaze_effect .get_height ()*scale ))
                        img_sc =pygame .transform .scale (blaze_effect ,(new_w ,new_h ))
                        screen_w =screen .get_size ()[0 ]
                        X =screen_w //2 -img_sc .get_width ()/2
                        Y =360 -img_sc .get_height ()/2 + 20
                        screen .blit (img_sc ,[X ,Y ])
                if self.tmr ==1 :
                    self.set_message ("　爆弾による攻撃！")
                    se [1 ].play ()
                    self.blazegem =self.blazegem -1 
                if self.tmr ==8 :
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
                if self.tmr ==12 :
                    self.emy_blink =5 
                    self.set_message (f"　{dmg}　ダメージ！")
                if self.tmr ==18 :
                    self.emy_life =self.emy_life -dmg 
                    if self.emy_life <=0 :
                        self.emy_life =0 
                        self.idx =241 
                        self.tmr =0
                if self.tmr ==20 :
                    if self.emy_typ ==18 :
                        self.boss_mode = "fire"
                    if self.emy_typ ==12:
                        self.burn_turns =4 
                        self.set_message ("　敵は　火傷した！")
                    else:
                        self.tmr =self.tmr +2
                if self.tmr ==23 :
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
                self.draw_text (screen ,"[B]/[Back] Back",win_x + 460 ,win_y + 380 ,fontS ,WHITE )
                if self.tmr >5 :
                    if key [K_b ] or key [K_BACKSPACE ]:
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
                if self.tmr ==8 :
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
                            se [0 ].play ()
                            self.set_message ("　会心の一撃！")
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
                    if self.tutorial_enabled and self.tutorial_pending_battle:
                        if self.tutorial_pending_battle =="room3":
                            self.tutorial_progress ["room3_enemy_defeated"]=True
                        elif self.tutorial_pending_battle =="room5":
                            self.tutorial_progress ["room5_enemy_defeated"]=True
                        self.tutorial_pending_battle =""
                        self.update_tutorial_floor_state ()
                    if self.emy_typ ==22 :
                        self.truth_fragment_drop_battle =False
                        self.idx =246 
                        self.tmr =0 
                if self.tmr ==15 :
                    if self.boss ==1 :
                        time .sleep (3 )
                    if self.pl_exp >=(self.pl_lifemax -250 )*20 :
                        self.idx =243 
                        self.tmr =0 
                    elif self.truth_fragment_drop_battle:
                        self.idx =247 
                        self.tmr =0 
                    else :
                        self.idx =244 

            elif self.idx ==242 :# 敗北
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    pygame .mixer .music .stop ()
                    self.boss =0 
                    self.btl_cmd =0
                    self.guard_remain =0 
                    self.poison =0 
                    self.madoka =0 
                    self.pow_up =1 
                    self.burn_turns =0 
                    self.inferno =0
                    self.boss_mode = "normal"
                    self.truth_fragment_drop_battle =False
                    self.tutorial_pending_battle =""
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
                    self.pl_level =self.pl_level +1 
                    lif_p =random .randint (10 ,20 )
                    str_p =random .randint (7 ,9 )
                    mag_p =random .randint (15 ,30 )
                    self.pl_exp =self.pl_exp -(self.pl_lifemax -250 )*20 
                if self.tmr ==10 :
                    self.pl_lifemax =self.pl_lifemax +lif_p 
                    self.pl_life =self.pl_life +lif_p 
                    self.pl_mag =self.pl_mag +mag_p 
                    self.pl_str =self.pl_str +str_p 
                    self.set_message (f"　最大生命 +{lif_p}")
                    self.set_message (f"　攻撃 +{str_p}")
                    self.set_message (f"　魔力 +{mag_p}")
                if self.tmr ==23 :
                    if self.pl_exp >(self.pl_lifemax -250 )*20 :
                        self.idx =243 
                        self.tmr =0 
                    else :
                        if self.truth_fragment_drop_battle:
                            self.idx =247 
                            self.tmr =0 
                        else :
                            self.idx =244 

            elif self.idx ==244 :# 戦闘終了
                self.truth_fragment_drop_battle =False
                if self.tutorial_enabled and self.tutorial_pending_battle:
                    self.restore_tutorial_cocoon ()
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
                    self.boss =0 
                    self.boss_save_cmd =0
                    self.boss_save_input_lock = True
                    self.save_from_boss = False
                    if 90 <self.floor <100 :
                        pygame .mixer .music .load (self.path +"/sound/bgm_9.wav")
                        pygame .mixer .music .play (-1 )
                    self.idx =112 
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
                    self.update_player_images ()
                    self.set_message ("Drop {} lv.{}".format (TRAP_NAME [trap_drop ],wpn_lev_drop ))
                if self.tmr ==23 :
                    self.idx =241 
                    self.tmr =14 

            elif self.idx ==247 :#しんじつのかけらドロップ
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.set_message ("敵は　しんじつのかけらを　落とした！")
                    self.se [10 ].play ()
                if self.tmr ==18 :
                    self.truth_fragment =min (100 ,self.truth_fragment +1 )
                    self.truth_fragment_drop_battle =False
                    self.idx =244
                    self.tmr =0

            pygame .display .update ()
            clock .tick (10 )
            self.prev_return = key [K_RETURN ]
            self.prev_a = key [K_a ]


def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
