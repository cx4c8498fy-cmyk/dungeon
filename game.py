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


BATTLE_UI_LAYOUT = {
    "player_panel": {
        "x_offset": 10,
        "top_margin": 20,
        "width": 325,
        "height": 140,
    },
    "status": {
        "x_offset_from_panel": 30,
        "y_gap_from_panel": 10,
        "line_gap": 4,
    },
    "enemy": {
        "name_bottom_offset": 120,
        "bar_y_offset": 30,
        "state_y_offset": 52,
        "label_x_offset": 40,
        "bar_x_offset": 30,
        "bar_width": 200,
        "bar_height": 10,
    },
    "message_window": {
        "width": 300,
        "height": 530,
        "right_margin": 10,
        "top_margin": 50,
        "text_x_margin": 30,
        "text_y_margin": 40,
        "line_height": 48,
    },
}

WEAPON_LEVEL_ATTRS = {"shield": "pl_shield", "armor": "pl_armor", "sword": "pl_sword"}
EQUIP_SLOT_ATTRS = {"shield": "eq_shield", "armor": "eq_armor", "sword": "eq_sword"}


# すべてのセーブデータから現在のfloorを読み込む
def load_floorlist(base_path):
    floorlist = []
    for i in range(3):
        with open(base_path + "/savedata/data{}.json".format(i+1), "r") as f:
            loaddata = json.load(f)
            floorlist.append(loaddata["floor"])
    return floorlist


class Game:
    # ゲーム全体の初期化
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
        self.imgFairy = pygame.image.load(self.path + "/image/fairy.png")
        self.imgLockedStairs = pygame.image.load(self.path + "/image/locked_stairs.png")
        self.imgWallInfo = pygame.image.load(self.path + "/image/wall_info.png")

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
        self.pl_magmax = 1000
        self.pl_exp = 0
        self.pl_level = 1
        self.pl_shield = [0, 0, 0]
        self.pl_armor = [0, 0, 0]
        self.pl_sword = [0, 0, 0]
        self.eq_shield = 0
        self.eq_armor = 0
        self.eq_sword = 0
        self.potion = 0
        self.potion_lv = 0
        self.blazegem = 0
        self.blazegem_lv = 0
        self.guard = 0
        self.guard_lv = 0
        self.truth_fragment = 0
        self.truth_fragment_floors = set()
        self.heirloom_pendant = 1
        self.tool_food = 0
        self.tool_magic_water = 0
        self.tool_magic_seed = 0
        self.tool_growth = 0
        self.tool_sword_polish = 0
        self.tool_shield_harden = 0
        self.tool_armor_patch = 0
        self.treasure = 0

        self.emy_name = ""
        self.emy_lev = 0
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
        self.tool_growth_choice_active = False
        self.tool_growth_choice_cmd = 0
        self.tool_weapon_choice_active = False
        self.tool_weapon_choice_cmd = 0
        self.tool_weapon_choice_targets = []
        self.tool_weapon_choice_tool_id = ""
        self.tool_weapon_choice_prompt = ""
        self.tool_notice_text = ""
        self.tool_notice_timer = 0
        self.equip_cursor = 0
        self.equip_back_lock = False
        self.equip_accept_lock = False
        self.settings_cmd = 0
        self.settings_back_lock = False
        self.settings_accept_lock = False
        self.save_cmd = 0
        self.save_from_stair = False
        self.save_from_boss = False
        self.stair_save_slot = 0
        self.stair_choice_cmd = 0
        self.stair_prompted = False
        self.stair_choice_input_lock = False
        self.boss_save_cmd = 0
        self.boss_save_input_lock = False
        self.boss_transition_mode = False
        self.floor_transition_delta = 1
        self.btl_cmd = 0
        self.powup = 1
        self.emy_powup = 1
        self.poison = 0
        self.emy_poison = 0
        self.madoka = 0
        self.burn_turns = 0
        self.inferno = 0
        self.boss_mode = "normal"
        self.guard_remain = 0
        self.change = 0
        self.auto_equip_attack_sword = False
        self.auto_equip_magic_staff = False
        self.auto_equip_bomb_cannon = False
        self.auto_equip_guard_shield = False
        self.auto_equip_potion_armor = False
        self.battle_restore_eq_shield = 0
        self.battle_restore_eq_armor = 0
        self.battle_restore_eq_sword = 0
        self.battle_auto_equip_used = False
        self.wall_item = None
        self.fairy_pos = None
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
        self.boss_talk_lines = []
        self.boss_talk_index = 0
        self.boss_talk_kind = "init"
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
        self.keep_title_bgm_on_next_title = False
        self.recollection_stage = 0
        self.clear_save_payload = None
        self.emy_skip_turn = False
        self.item_talk_lines = []
        self.item_talk_index = 0
        self.item_talk_char_count = 0
        self.item_talk_last_tick = 0
        self.tool_desc_tool_id = ""
        self.tool_desc_char_count = 0
        self.tool_desc_last_tick = 0
        self.item_popup_text = ""
        self.enemy_poison_fail_count = 0
        self.item_event_phase = 0
        self.item_choice = 0
        self.item_reward = None
        self.item_event_kind = ""
        self.item_reward_count = 3
        self.item_event_popup_timer = 0
        self.true_episode_heard = False
        self.wall_item = None
        self.event_wall_pos = None
        self.event_talk_lines = []
        self.event_talk_index = 0
        self.event_talk_char_count = 0
        self.event_talk_last_tick = 0
        self.wall_event = None
        self.truth_fragment_drop_battle = False
        self.growth_essence_drop_battle = False
        self.map_seen = None
        self.map_stairs = None
        self.map_bosses = None
        self.map_item_walls = None
        self.map_event_walls = None
        self.map_info_walls = None
        self.map_grid_surface = None
        self.map_surface = None
        self.map_surface_scale = None
        self.map_surface_size = None
        self.fixed_floor_data = None
        self.last_talk_mode = 1
        self.floor99_trial_missing = 0
        self.floor99_trial_total = 0
        self.floor99_trial_battle_active = False
        self.floor99_trial_post_pending = False
        self.reset_tutorial_runtime()

    # init floor variant map を初期化する
    def init_floor_variant_map(self):
        count = max(len(self.floor_variants), 1)
        self.floor_var_map = [[random.randint(0, count - 1) for j in range(DUNGEON_W)] for i in range(DUNGEON_H)]

    # init floor flip map を初期化する
    def init_floor_flip_map(self):
        self.floor_flip_map = [[random.randint(0, 1) for j in range(DUNGEON_W)] for i in range(DUNGEON_H)]

    # init map state を初期化する
    def init_map_state(self):
        self.map_seen = [[False for j in range(DUNGEON_W)] for i in range(DUNGEON_H)]
        self.map_stairs = set()
        self.map_bosses = set()
        self.map_item_walls = set()
        self.map_event_walls = set()
        self.map_info_walls = set()
        self.map_grid_surface = pygame.Surface((DUNGEON_W, DUNGEON_H), pygame.SRCALPHA)
        self.map_grid_surface.fill((0, 0, 0, 120))
        self.map_surface = None
        self.map_surface_scale = None
        self.map_surface_size = None

    # 階段がロックされているか判定する
    def is_stairs_locked(self, floor=None):
        check_floor = self.floor if floor is None else floor
        if check_floor not in LOCKED_STAIRS_ITEM_WALL_FLOORS:
            return False
        return any(7 in row for row in self.dungeon)

    # 武具セットを所持しているかどうかの判定
    def has_full_basic_set(self):
        return (
            self.pl_shield[0] > 0 and
            self.pl_armor[0] > 0 and
            self.pl_sword[0] > 0
        )

    # セーブデータから武器レベル配列を読み込む
    def read_weapon_levels_from_save(self, data, key):
        values = data.get(key, [0, 0, 0])
        if not isinstance(values, list):
            values = [0, 0, 0]
        values = (values + [0, 0, 0])[:3]
        levels = []
        for value in values:
            try:
                level = int(value)
            except (TypeError, ValueError):
                level = 0
            levels.append(max(0, min(99, level)))
        return levels

    # pl_magmax を更新する
    def refresh_pl_magmax(self):
        self.pl_magmax = 1000 + (self.pl_level - 1) * 50

    # pl_mag を増減させる
    def add_pl_mag(self, amount):
        self.pl_mag = max(0, min(self.pl_mag + amount, self.pl_magmax))

    # guardの効果を計算する
    def get_guard_damage_multiplier(self, target="player"):
        if target == "player":
            return max(0.01, 0.35 - self.get_active_weapon_level("shield", 2) * 0.0018 - self.guard_lv * 0.005)
        else:
            return max(0.01, 0.35 - self.guard_lv * 0.005)

    # 妖精の座標を返す
    def find_fairy_position(self):
        for y in range(DUNGEON_H):
            for x in range(DUNGEON_W):
                if self.dungeon[y][x] == 11:
                    return (x, y)
        return None

    # place fairy for floor を配置する
    def place_fairy_for_floor(self):
        self.fairy_pos = None
        if self.floor % 10 not in FAIRY_FLOOR_MODS:
            return
        fairy_cells = [
            (x, y)
            for y in range(3, DUNGEON_H - 3)
            for x in range(3, DUNGEON_W - 3)
            if self.dungeon[y][x] == 0 and (x, y) != (self.pl_x, self.pl_y)
        ]
        if fairy_cells:
            fx, fy = random.choice(fairy_cells)
            self.dungeon[fy][fx] = 11
            self.fairy_pos = (fx, fy)

    # start fairy upgrade event を開始する
    def start_fairy_upgrade_event(self):
        if self.fairy_pos:
            fx, fy = self.fairy_pos
            if 0 <= fx < DUNGEON_W and 0 <= fy < DUNGEON_H and self.dungeon[fy][fx] == 11:
                self.dungeon[fy][fx] = 0
        self.fairy_pos = None
        self.init_item_event(kind="fairy_upgrade", lines=FAIRY_UPGRADE_TALK)
        self.idx = 131
        self.tmr = 0

    # try catch fairy を試行する
    def try_catch_fairy(self):
        if self.fairy_pos and (self.pl_x, self.pl_y) == self.fairy_pos:
            self.start_fairy_upgrade_event()
            return True
        return False

    # move fairy one step の移動・更新を行う
    def move_fairy_one_step(self):
        if not self.fairy_pos:
            return
        fx, fy = self.fairy_pos
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx = fx + dx
            ny = fy + dy
            if not (0 <= nx < DUNGEON_W and 0 <= ny < DUNGEON_H):
                continue
            if self.dungeon[ny][nx] == 0:
                self.dungeon[fy][fx] = 0
                self.dungeon[ny][nx] = 11
                self.fairy_pos = (nx, ny)
                return

    # セーブ値と所持状態に応じて装備スロットを確定する
    def resolve_equipped_slot(self, group, slot_data):
        slot = int(slot_data)
        levels = getattr(self, WEAPON_LEVEL_ATTRS[group])
        if levels[slot] > 0:
            return slot
        for i, level in enumerate(levels):
            if level > 0:
                return i
        return 0

    # 3カテゴリの装備スロットをまとめて適用する
    def apply_equipped_slots(self, shield_slot=0, armor_slot=0, sword_slot=0):
        self.eq_shield = self.resolve_equipped_slot("shield", shield_slot)
        self.eq_armor = self.resolve_equipped_slot("armor", armor_slot)
        self.eq_sword = self.resolve_equipped_slot("sword", sword_slot)

    # weapon index to group slot の処理を行う
    def weapon_index_to_group_slot(self, weapon_index):
        row = weapon_index // 3
        slot = weapon_index % 3
        if row == 0:
            return "shield", slot
        if row == 1:
            return "armor", slot
        return "sword", slot

    # get weapon level を取得する
    def get_weapon_level(self, group, slot):
        if not (0 <= slot < 3):
            return 0
        levels = getattr(self, WEAPON_LEVEL_ATTRS[group])
        return levels[slot]

    # get active weapon level を取得する
    def get_active_weapon_level(self, group, slot):
        if getattr(self, EQUIP_SLOT_ATTRS[group]) != slot:
            return 0
        return self.get_weapon_level(group, slot)

    # 武器カテゴリとスロットから武器IDを取得する
    def get_weapon_id(self, group, slot):
        if group not in ("shield", "armor", "sword") or not (0 <= slot < 3):
            return -1
        group_offset = {"shield": 0, "armor": 1, "sword": 2}[group]
        return slot * 3 + group_offset

    # 武器カテゴリとスロットから武器名を取得する
    def get_weapon_name(self, group, slot):
        weapon_id = self.get_weapon_id(group, slot)
        if 0 <= weapon_id < len(WPN_NAME):
            return WPN_NAME[weapon_id]
        return "？"

    # is weapon equipped index を判定する
    def is_weapon_equipped_index(self, weapon_index):
        group, slot = self.weapon_index_to_group_slot(weapon_index)
        return getattr(self, EQUIP_SLOT_ATTRS[group]) == slot

    # equip weapon index の装備処理を行う
    def equip_weapon_index(self, weapon_index):
        group, slot = self.weapon_index_to_group_slot(weapon_index)
        if self.get_weapon_level(group, slot) <= 0:
            return False
        setattr(self, EQUIP_SLOT_ATTRS[group], slot)
        return True

    # パラメータウィンドウ表示用の装備中武器のテキストを取得
    def get_equipped_weapon_text(self, group, fallback_label):
        slot = getattr(self, EQUIP_SLOT_ATTRS[group])
        level = self.get_weapon_level(group, slot)
        if level <= 0:
            return f"{fallback_label}　-"
        return f"{self.get_weapon_name(group, slot)} Lv.{level}"

    # 装備中の武器の防御力を取得する
    def get_equipped_defence(self):
        shield_lv = self.get_weapon_level("shield", self.eq_shield)
        armor_lv = self.get_weapon_level("armor", self.eq_armor)
        return shield_lv + armor_lv

    # 戦闘中の自動装備復元情報を初期化する
    def start_battle_equip_session(self):
        self.battle_restore_eq_shield = self.eq_shield
        self.battle_restore_eq_armor = self.eq_armor
        self.battle_restore_eq_sword = self.eq_sword
        self.battle_auto_equip_used = False

    # 自動装備前の装備状態に復元する
    def restore_battle_equip_session(self):
        if not self.battle_auto_equip_used:
            return
        self.apply_equipped_slots(
            self.battle_restore_eq_shield,
            self.battle_restore_eq_armor,
            self.battle_restore_eq_sword,
        )
        self.update_player_images()
        self.battle_auto_equip_used = False

    # 自動装備で武器スロットを切り替える
    def try_auto_equip_slot(self, group, slot):
        if self.get_weapon_level(group, slot) <= 0:
            return False
        if getattr(self, EQUIP_SLOT_ATTRS[group]) == slot:
            return False
        self.battle_restore_eq_shield = self.eq_shield
        self.battle_restore_eq_armor = self.eq_armor
        self.battle_restore_eq_sword = self.eq_sword
        setattr(self, EQUIP_SLOT_ATTRS[group], slot)
        self.update_player_images()
        self.battle_auto_equip_used = True
        return True

    # 戦闘コマンドに応じた自動装備を適用する
    def apply_auto_equip_for_battle_command(self, cmd):
        if cmd == 0 and self.auto_equip_attack_sword:
            self.try_auto_equip_slot("sword", 0)
        elif cmd == 1 and self.auto_equip_magic_staff:
            self.try_auto_equip_slot("sword", 1)
        elif cmd == 2 and self.auto_equip_potion_armor:
            self.try_auto_equip_slot("armor", 2)
        elif cmd == 3 and self.auto_equip_bomb_cannon:
            self.try_auto_equip_slot("sword", 2)
        elif cmd == 4 and self.auto_equip_guard_shield:
            self.try_auto_equip_slot("shield", 2)

    # 敵側の戦闘中一時パラメータを初期化する
    def reset_enemy_battle_params(self):
        self.emy_skip_turn =False
        self.enemy_poison_fail_count =0
        self.emy_poison =0

    # プレイヤー側の戦闘中一時パラメータを初期化する
    def reset_player_battle_params(self):
        self.btl_cmd =0
        self.guard_remain =0
        self.poison =0
        self.powup =1
        self.madoka =0
        self.emy_powup =1
        self.burn_turns =0
        self.inferno =0
        self.boss_mode = "normal"
        self.change =0

    # 敵の毒ダメージ処理
    def resolve_enemy_poison_tick(self):
        if self.emy_poison <= 0:
            self.tmr =self.tmr +1 
            return 0
        dmg = self.emy_poison * 40
        self.set_message (f"　毒 {dmg}ダメージ！")
        self.emy_life =self.emy_life -dmg
        self.emy_blink =2
        self.emy_poison =max (self.emy_poison -1 ,0)
        if self.emy_life <=0 :
            self.emy_life =0
            self.idx =241
            self.tmr =0
            return 2
        return 1

    # アイアンドウブの強化素材ドロップ条件を判定する
    def should_drop_iron_upgrade(self):
        return self.boss ==0 and self.emy_typ ==10 and not self.floor99_trial_battle_active

    # display index to weapon id を表示用に変換する
    def display_index_to_weapon_id(self, weapon_index):
        group, slot = self.weapon_index_to_group_slot(weapon_index)
        return self.get_weapon_id(group, slot)

    # プレイヤーの画像を更新する
    def update_player_images(self):
        if self.has_full_basic_set():
            self.imgPlayer = self.imgPlayerBase1
        else:
            self.imgPlayer = self.imgPlayerBase0

    # floor assets を設定する
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
        event_path = os.path.join(self.path, "image", "wall", "wallA{}_event.png".format(wall_set))
        self.wall_event = pygame.image.load(event_path)

    # set floor assets for current floor を設定する
    def set_floor_assets_for_current_floor(self):
        floor_index = (self.floor - 1) // 10
        self.set_floor_assets(floor_index, self.floor)

    # set floor assets for transition を設定する
    def set_floor_assets_for_transition(self, floor_value):
        floor_index = (floor_value - 1) // 10
        self.set_floor_assets(floor_index, floor_value)

    # プレイヤーの正面のタイルIDを返す
    def get_front_tile_id(self):
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
            return self.dungeon[ty][tx]
        return None

    # すべての繭がクリアされているかの判定
    def all_cocoons_cleared(self):
        return all((2 not in row) and (10 not in row) for row in self.dungeon)

    # チュートリアルの進行状態を初期化
    def default_tutorial_progress(self):
        return {
            "talked": [False, False, False, False, False, False, False],
            "room2_chest_opened": False,
            "room3_enemy_defeated": False,
            "room4_item_obtained": False,
            "room4_item_used": False,
            "room5_enemy_defeated": False,
        }

    # reset tutorial runtime の処理を行う
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

    # parse pos を解析する
    def parse_pos(self, value):
        if (isinstance(value, (list, tuple)) and len(value) == 2 and
                all(isinstance(v, int) for v in value)):
            return (value[0], value[1])
        return None

    # load fixed floor data を読み込む
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
                
                # Adjust fixed item wall position if it exists
                if "item_wall_pos" in data:
                    data["item_wall_pos"] = (data["item_wall_pos"][0] + offset_x, data["item_wall_pos"][1] + offset_y)
                if "event_wall_pos" in data:
                    data["event_wall_pos"] = (data["event_wall_pos"][0] + offset_x, data["event_wall_pos"][1] + offset_y)
                
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

    # pad dungeon to standard size の処理を行う
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

    # setup tutorial floor の処理を行う
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
                wx, wy = pos
                if 0 <= wx < DUNGEON_W and 0 <= wy < DUNGEON_H:
                    if self.dungeon[wy][wx] in (7, 9, 13):
                        self.dungeon[wy][wx] = 13
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

    # tutorial save data の処理を行う
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

    # tutorial stage for wall の処理を行う
    def tutorial_stage_for_wall(self, pos):
        if not self.tutorial_enabled:
            return 0
        return self.tutorial_wall_stage.get(pos, 0)

    # init tutorial talk を初期化する
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

    # complete tutorial talk の完了処理を行う
    def complete_tutorial_talk(self):
        if not self.tutorial_enabled:
            self.tutorial_active_stage = 0
            return
        stage = self.tutorial_active_stage
        if 1 <= stage <= 6:
            self.tutorial_progress["talked"][stage] = True
        self.tutorial_active_stage = 0
        self.update_tutorial_floor_state()

    # update tutorial floor state を更新する
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

    # restore tutorial cocoon を復元する
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

    # ボスとの会話内容を初期化
    def init_boss_talk(self, mode="init"):
        boss_id = 9 + int(self.floor // 10)
        boss_map_id = boss_id - 10
        self.boss_talk_kind = mode
        if mode == "end":
            talk_table = BOSS_END_TALK
        else:
            talk_table = BOSS_INIT_TALK
        self.boss_talk_lines = talk_table.get(boss_map_id, [])
        self.boss_talk_index = 0
        self.boss_talk_char_count = 0
        self.boss_talk_last_tick = pygame.time.get_ticks()

    # 最終会話の内容を初期化
    def init_last_talk(self, mode=1):
        self.last_talk_mode = mode
        if mode == 2: # 真エンドの会話
            self.boss_talk_lines = BOSS_LASTTALK2
        else: # ノーマルエンドの会話
            self.boss_talk_lines = BOSS_LASTTALK1
        self.boss_talk_index = 0
        self.boss_talk_char_count = 0
        self.boss_talk_last_tick = pygame.time.get_ticks()

    # init item event を初期化する
    def init_item_event(self, kind=None, reward_count=3, lines=None):
        self.item_event_phase = 0
        self.item_choice = 0
        self.item_reward = None
        self.item_event_popup_timer = 0
        self.item_talk_index = 0
        self.item_talk_char_count = 0
        self.item_talk_last_tick = pygame.time.get_ticks()
        self.item_reward_count = reward_count
        if kind is None:
            kind = "item"
        self.item_event_kind = kind
        if lines is not None:
            self.item_talk_lines = lines
        else:
            self.item_talk_lines = [
                "おお　あわれなニンゲンよ。\nそなたに恵みを　授けよう",
            ]

    # 99階イベントの開始条件を判定してイベント種別を初期化
    def init_floor99_item_event(self):
        if self.floor not in self.truth_fragment_floors:
            self.init_item_event(kind="floor99_need", lines=FLOOR99_NEED_FRAGMENT_TALK)
            return
        self.floor99_trial_missing = max(0, 99 - self.truth_fragment)
        self.floor99_trial_total = self.floor99_trial_missing
        if self.floor99_trial_missing > 0:
            lines = [line.format(n=self.floor99_trial_missing) for line in FLOOR99_TRIAL_OFFER_LINES]
            self.init_item_event(kind="floor99_offer", lines=lines)
        else:
            self.init_item_event(kind="floor99_bonus", reward_count=5, lines=FLOOR99_COMPLETE_LINES)

    # 99階イベント専用の試練戦闘を準備する
    def start_floor99_trial_battle(self):
        if self.floor99_trial_missing <= 0:
            return
        self.floor99_trial_battle_active = True
        self.floor99_trial_post_pending = False
        self.truth_fragment_drop_battle = False
        self.growth_essence_drop_battle = False
        self.idx = 200
        self.tmr = 0

    # 99階イベント専用の戦闘後イベントを開始する
    def init_floor99_after_trial_event(self):
        self.init_item_event(kind="floor99_after", reward_count=5, lines=[FLOOR99_AFTER_TRIAL_LINES[0]])

    # get item wall rewards を取得する
    def get_item_wall_rewards(self):
        if self.item_event_kind == "item":
            return [
                {"label": "傷薬", "attr": "potion", "treasure": 0},
                {"label": "爆弾", "attr": "blazegem", "treasure": 1},
                {"label": "守護", "attr": "guard", "treasure": 2},
            ]
        if self.item_event_kind in ("item_upgrade", "floor99_bonus", "floor99_after"):
            return [
                {"label": TRE_NAME[7], "attr": "tool_sword_polish", "treasure": 7},
                {"label": TRE_NAME[8], "attr": "tool_shield_harden", "treasure": 8},
                {"label": TRE_NAME[9], "attr": "tool_armor_patch", "treasure": 9},
            ]
        return []

    # init event talk を初期化する
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

    # infoWall用の会話を初期化する
    def init_info_talk(self):
        self.tutorial_active_stage = 0
        talk = INFO_TALK.get(self.floor, "古い壁画だ。文字がかすれていて読み取れない。")
        if isinstance(talk, str):
            self.event_talk_lines = [talk]
        elif isinstance(talk, list):
            self.event_talk_lines = [str(line) for line in talk]
        else:
            self.event_talk_lines = [str(talk)]
        self.event_talk_index = 0
        self.event_talk_char_count = 0
        self.event_talk_last_tick = pygame.time.get_ticks()

    # get boss map image を取得する
    def get_boss_map_image(self):
        cache_key = "boss_map"
        if cache_key not in self.boss_map_cache:
            path = self.path + "/image/boss_map.png"
            self.boss_map_cache[cache_key] = pygame.image.load(path)
        return self.boss_map_cache[cache_key]

    # dungeonマップ を生成する
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
                    if self.floor %10 ==0 :
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

    # dungeon を描画する
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
            for x in range (start_x ,start_x +cols ): # 画面に表示される範囲のタイルをループ
                X =offset_x +(x -start_x )*tile 
                Y =offset_y +(y -start_y )*tile 
                dx =self.pl_x +x 
                dy =self.pl_y +y 
                wall_only =(y >=start_y +rows )
                if 0 <=dx <DUNGEON_W and 0 <=dy <DUNGEON_H :
                    tile_id =self.dungeon [dy ][dx ]
                    if not wall_only and tile_id not in (7 ,8 ,9 ,13 ):
                        if not self.map_seen [dy ][dx ]:
                            self.map_seen [dy ][dx ]=True
                            new_seen .append ((dx ,dy ))
                        if tile_id ==3 :
                            self.map_stairs .add ((dx ,dy ))
                    if not wall_only and tile_id ==7 and self.map_item_walls is not None:
                        self.map_item_walls.add((dx, dy))
                    if not wall_only and tile_id ==8 and self.map_event_walls is not None:
                        self.map_event_walls.add((dx, dy))
                    if not wall_only and tile_id ==13 and self.map_info_walls is not None:
                        self.map_info_walls.add((dx, dy))
                    if not wall_only and tile_id in (0 ,1 ,2 ,3 ,4 ,5 ,6 ,10 ,11 ,12 ):
                        if tile_id in (0 ,1 ,2 ,4 ,10 ,11 ,12 ):
                            variant =self.floor_var_map [dy ][dx ]
                            if self.floor_flip_map [dy ][dx ]:
                                bg .blit (self.floor_variants_flipped [variant ],[X ,Y ])
                            else :
                                bg .blit (self.floor_variants [variant ],[X ,Y ])
                            overlay_tile =2 if tile_id ==10 else tile_id
                            if overlay_tile ==11 :
                                bg .blit (self.imgFairy ,[X ,Y ])
                            elif overlay_tile ==12 :
                                if not wall_only and self.map_bosses is not None:
                                    self.map_bosses.add((dx, dy))
                                boss_map = self.get_boss_map_image()
                                bg .blit (boss_map ,[X ,Y -40 ])
                            elif overlay_tile !=0 :
                                bg .blit (self.imgFloor [overlay_tile ],[X ,Y ])
                        else :
                            if tile_id ==3 and self.is_stairs_locked ():
                                bg .blit (self.imgLockedStairs ,[X ,Y ])
                            else:
                                bg .blit (self.imgFloor [tile_id ],[X ,Y ])
                    if tile_id in (7 ,8 ,9 ,13 ):
                        if tile_id ==8 and self.wall_event:
                            bg .blit (self.wall_event ,[X ,Y -40 ])
                        else :
                            bg .blit (self.imgWall ,[X ,Y -40 ])
                        if tile_id ==7 :
                            bg .blit (self.imgFloor [-1 ],[X ,Y ])
                        if tile_id ==13 :
                            bg .blit (self.imgWallInfo ,[X ,Y ])
                        if dy >=1 and self.dungeon [dy -1 ][dx ] in (7 ,8 ,9 ,13 ):
                            bg .blit (self.imgWall2 ,[X ,Y -80 ])
                if not wall_only and x ==0 and y ==0 :# 主人公キャラの表示
                    bg .blit (self.imgPlayer [self.pl_a ],[X ,Y -40 ])
        bg .set_clip (prev_clip )
        self.update_minimap_grid (new_seen )
        if self.idx ==100 :
            self.draw_minimap (bg ,bg_rect ,new_seen )
        floor_text ="地下 {}階".format (self.floor)
        floor_x =view_left +60
        floor_y =view_top +view_h -40
        self.draw_text (bg ,floor_text ,floor_x ,floor_y ,fnt ,WHITE )
        if self.floor in self.truth_fragment_floors:
            star_x =floor_x +fnt .size (floor_text )[0 ]+12
            self.draw_text (bg ,"★",star_x ,floor_y ,fnt ,GOLD )
        self.draw_para (bg ,fnt ,bg_rect )# 主人公の能力を表示

    # event の配置
    def put_event (self ):
    # 階段かボスの配置
        self.event_wall_pos = None
        self.fairy_pos = None
        fixed_item_wall_placed =False
        fixed_item_wall_front =None
        fixed_event_wall_front =None
        fixed_player_start =None
        if self.fixed_floor_data and self.floor == 1: # チュートリアルフロアの配置
            self.setup_tutorial_floor()
            self.pl_x, self.pl_y = self.fixed_floor_data["pl_start"]
            self.pl_d =1
            self.pl_a =5
            self.stair_prompted =False
            return
        is_boss_floor =self.floor %10 ==0
        if self.fixed_floor_data and self.floor == 100: # 最終フロアの配置
            self.pl_x, self.pl_y = self.fixed_floor_data["pl_start"]
            fixed_player_start =(self.pl_x ,self.pl_y )
            item_wall_pos =self.parse_pos (self.fixed_floor_data.get ("item_wall_pos"))
            if item_wall_pos:
                wx ,wy =item_wall_pos
                if (0 <=wx <DUNGEON_W and 0 <=wy <DUNGEON_H -1 and
                    self.dungeon [wy ][wx ]==9 and self.dungeon [wy +1 ][wx ]==0 ):
                    self.dungeon [wy ][wx ]=7
                    fixed_item_wall_placed =True
                    fixed_item_wall_front =(wx ,wy +1 )
            event_wall_pos =self.parse_pos (self.fixed_floor_data.get ("event_wall_pos"))
            if event_wall_pos:
                wx ,wy =event_wall_pos
                if (0 <=wx <DUNGEON_W and 0 <=wy <DUNGEON_H -1 and
                    self.dungeon [wy ][wx ]==9 and self.dungeon [wy +1 ][wx ]==0 ):
                    self.dungeon [wy ][wx ]=8
                    self.event_wall_pos =(wx ,wy )
                    fixed_event_wall_front =(wx ,wy +1 )
        floor_cells =[
            (x ,y )
            for y in range (3 ,DUNGEON_H -3 )
            for x in range (3 ,DUNGEON_W -3 )
            if (self.dungeon [y ][x ]==0 and
                (x ,y )!=fixed_item_wall_front and
                (x ,y )!=fixed_event_wall_front and
                (x ,y )!=fixed_player_start)
        ]
        random .shuffle (floor_cells )
        def take_cells (count ):
            taken =floor_cells [:count ]
            del floor_cells [:count ]
            return taken
        has_boss_tile =any (12 in row for row in self.dungeon )
        if is_boss_floor and not has_boss_tile:
            boss_cells =take_cells (1 )
            if boss_cells:
                bx ,by =boss_cells [0 ]
                self.dungeon [by ][bx ]=12
                has_boss_tile =True
        if not has_boss_tile:
            stairs_cells =take_cells (1 )
            if stairs_cells:
                sx ,sy =stairs_cells [0 ]
                self.dungeon [sy ][sx ]=3
        t_box_num = 7 if is_boss_floor else 4
        for x, y in take_cells(t_box_num): # 宝箱の配置
            self.dungeon[y][x] = 1
        w_box_num = 0 if self.floor < 11 else 7 if is_boss_floor else 4 if self.floor < 91 else 5
        for x ,y in take_cells (w_box_num ): # 強化素材箱の配置
            self.dungeon [y ][x ]=4
        cocoon_target =33 if is_boss_floor else 19
        cocoon_cells =take_cells (cocoon_target )
        for x ,y in cocoon_cells: # 繭の配置
            self.dungeon [y ][x ]=2
        if cocoon_cells: # 真実の繭の配置
            sx ,sy =random .choice (cocoon_cells )
            self.dungeon [sy ][sx ]=10
        if not self.floor in {1, 100}:
            self.pl_x, self.pl_y = take_cells(1)[0] # プレイヤーの初期位置
        self.pl_d =1 
        self.pl_a =5 
        self.place_fairy_for_floor ()
        place_item_wall =self.floor in {7 ,17 ,27 ,37 ,47 ,57 ,67 ,77 ,87, 
                                        15, 25, 35, 45, 55, 65, 75, 85, 
                                        91, 92, 93, 95, 96, 97, 98, 99, 100} or self.floor in ITEM_WALL_WEAPON_SET
        if place_item_wall: # アイテム壁を配置
            if not (self.floor ==100 and fixed_item_wall_placed):
                wall_cells =[
                    (x ,y )
                    for y in range (DUNGEON_H -1 )
                    for x in range (DUNGEON_W )
                    if self.dungeon [y ][x ]==9 and self.dungeon [y +1 ][x ]==0
                ]
                if wall_cells:
                    wx ,wy =random .choice (wall_cells )
                    self.dungeon [wy ][wx ]=7
        place_event_wall =self.wall_event and ((self.floor %10 ==4 and self.floor !=94 )or self.floor ==99 )
        if place_event_wall: # 壁イベントを配置
            wall_cells = [
                (x, y)
                for y in range(DUNGEON_H - 1)
                for x in range(DUNGEON_W)
                if self.dungeon[y][x] == 9 and self.dungeon[y + 1][x] == 0
            ]
            if wall_cells:
                wx, wy = random.choice(wall_cells)
                self.dungeon[wy][wx] = 8
        place_info_wall = (self.floor %10 ==2 )
        if place_info_wall: # 情報壁を配置
            wall_cells =[
                (x ,y )
                for y in range (DUNGEON_H -1 )
                for x in range (DUNGEON_W )
                if self.dungeon [y ][x ]==9 and self.dungeon [y +1 ][x ]==0
            ]
            if wall_cells:
                wx ,wy =random .choice (wall_cells )
                self.dungeon [wy ][wx ]=13

    # player の移動・更新を行う
    def move_player (self ,key ):
        if self.dungeon [self.pl_y ][self.pl_x ]==11 : # 妖精に載った
            self.start_fairy_upgrade_event ()
            return
        if self.dungeon [self.pl_y ][self.pl_x ]==1 :# 宝箱に載った
            self.dungeon [self.pl_y ][self.pl_x ]=0 
            self.treasure =random .choice ([0 ,0 ,1 ,1 ,2 ])
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
        if self.dungeon [self.pl_y ][self.pl_x ]==4 :# 強化素材箱に載った
            self.dungeon [self.pl_y ][self.pl_x ]=0 
            self.treasure =random .choice ([7 ,8 ,9 ])
            add_num = 3 if self.floor > 90 else 2 if self.floor > 60 else 1
            self.item_reward_count =add_num
            if self.treasure ==7 :
                self.tool_sword_polish +=add_num
            elif self.treasure ==8 :
                self.tool_shield_harden +=add_num
            else :
                self.tool_armor_patch +=add_num
            self.idx =120 
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
                self.item_reward_count =1
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
            if self.dungeon [self.pl_y -1 ][self.pl_x ] not in (7 ,8 ,9 ,12 ,13 ):
                self.pl_y =self.pl_y -1 
        if key [K_DOWN ]==1 :
            self.pl_d =1 
            if self.dungeon [self.pl_y +1 ][self.pl_x ] not in (7 ,8 ,9 ,12 ,13 ):
                self.pl_y =self.pl_y +1 
        if key [K_LEFT ]==1 :
            self.pl_d =2 
            if self.dungeon [self.pl_y ][self.pl_x -1 ] not in (7 ,8 ,9 ,12 ,13 ):
                self.pl_x =self.pl_x -1 
        if key [K_RIGHT ]==1 :
            self.pl_d =3 
            if self.dungeon [self.pl_y ][self.pl_x +1 ] not in (7 ,8 ,9 ,12 ,13 ):
                self.pl_x =self.pl_x +1 
        self.pl_a =self.pl_d *3 +2 
        if self.pl_x !=x or self.pl_y !=y :
            walk_cycle =[0 ,2 ,1 ,2 ]
            self.pl_a =self.pl_d *3 +walk_cycle [self.tmr %4 ]# 移動したら足踏みのアニメーション
            if self.try_catch_fairy ():
                return
            self.move_fairy_one_step ()
            self.try_catch_fairy ()

    # text を描画する
    def draw_text (self ,bg ,txt ,x ,y ,fnt ,col ):
        sur =fnt .render (txt ,True ,BLACK )
        bg .blit (sur ,[x +1 ,y +2 ])
        sur =fnt .render (txt ,True ,col )
        bg .blit (sur ,[x ,y ])

    # text alpha を描画する
    def draw_text_alpha (self ,bg ,txt ,x ,y ,fnt ,col ,alpha ):
        shadow =fnt .render (txt ,True ,BLACK )
        shadow .set_alpha (alpha )
        bg .blit (shadow ,[x +1 ,y +2 ])
        text =fnt .render (txt ,True ,col )
        text .set_alpha (alpha )
        bg .blit (text ,[x ,y ])

    # blit scaled bg の処理を行う
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

    # new game を開始する
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
        self.refresh_pl_magmax ()
        self.potion =2 
        self.potion_lv =0
        self.blazegem =2 
        self.blazegem_lv =0
        self.guard =2 
        self.guard_lv =0
        self.truth_fragment =0
        self.truth_fragment_floors = set()
        self.heirloom_pendant =1
        self.tool_food =0
        self.tool_magic_water =0
        self.tool_magic_seed =0
        self.tool_growth =0
        self.tool_sword_polish =0
        self.tool_shield_harden =0
        self.tool_armor_patch =0
        self.item_popup_text =""
        self.truth_fragment_drop_battle =False
        self.growth_essence_drop_battle =False
        self.floor99_trial_missing =0
        self.floor99_trial_total =0
        self.floor99_trial_battle_active =False
        self.floor99_trial_post_pending =False
        self.reset_enemy_battle_params ()
        self.save_from_stair = False
        self.save_from_boss = False
        self.stair_save_slot = 0
        self.stair_choice_cmd = 0
        self.stair_prompted = False
        self.stair_choice_input_lock = False
        self.boss_save_cmd = 0
        self.boss_save_input_lock = False
        self.boss_transition_mode = False
        self.floor_transition_delta = 1
        self.tool_growth_choice_active = False
        self.tool_growth_choice_cmd = 0
        self.tool_weapon_choice_active = False
        self.tool_weapon_choice_cmd = 0
        self.tool_weapon_choice_targets = []
        self.tool_weapon_choice_tool_id = ""
        self.tool_weapon_choice_prompt = ""
        self.tool_notice_text = ""
        self.tool_notice_timer = 0
        self.true_episode_heard = False
        self.encountered_enemies = set()
        self.powup =1
        self.emy_powup =1
        self.poison =0
        self.auto_equip_attack_sword =False
        self.auto_equip_magic_staff =False
        self.auto_equip_bomb_cannon =False
        self.auto_equip_guard_shield =False
        self.auto_equip_potion_armor =False
        self.battle_auto_equip_used =False
        self.fairy_pos =None
        self.idx =100 
        self.tmr =0 
        self.pl_shield =[0 ,0 ,0 ]
        self.pl_armor =[0 ,0 ,0 ]
        self.pl_sword =[0 ,0 ,0 ]
        self.apply_equipped_slots()
        self.update_player_images ()
        self.move_bgm_path =self.path +"/sound/bgm_"+str ((self.floor-1) //10 )+".wav"
        self.move_bgm_pos_ms =0 
        self.move_bgm_start_time =time .time ()
        pygame .mixer .music .load (self.move_bgm_path )
        pygame .mixer .music .play (-1 )

    # game data を読み込む
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
                self.potion_lv =loaddata .get ("potion_lv",0 )
                self.blazegem =loaddata ["blazegem"]
                self.blazegem_lv =loaddata .get ("blazegem_lv",0 )
                self.guard =loaddata ["guard"]
                self.guard_lv =loaddata .get ("guard_lv",0 )
                self.truth_fragment =loaddata .get ("truth_fragment",0 )
                self.truth_fragment_floors =set (int (v )for v in loaddata .get ("truth_fragment_floors",[] )if isinstance (v ,int ))
                self.heirloom_pendant =loaddata .get ("heirloom_pendant",1 )
                self.tool_food =loaddata .get ("tool_food",0 )
                self.tool_magic_water =loaddata .get ("tool_magic_water",0 )
                self.tool_magic_seed =loaddata .get ("tool_magic_seed",0 )
                self.tool_growth =loaddata .get ("tool_growth",0 )
                self.tool_sword_polish =loaddata .get ("tool_sword_polish",0 )
                self.tool_shield_harden =loaddata .get ("tool_shield_harden",0 )
                self.tool_armor_patch =loaddata .get ("tool_armor_patch",0 )
                self.auto_equip_attack_sword =bool (loaddata .get ("auto_equip_attack_sword",False ))
                self.auto_equip_magic_staff =bool (loaddata .get ("auto_equip_magic_staff",False ))
                self.auto_equip_bomb_cannon =bool (loaddata .get ("auto_equip_bomb_cannon",False ))
                self.auto_equip_guard_shield =bool (loaddata .get ("auto_equip_guard_shield",False ))
                self.auto_equip_potion_armor =bool (loaddata .get ("auto_equip_potion_armor",False ))
                self.item_popup_text =""
                self.truth_fragment_drop_battle =False
                self.growth_essence_drop_battle =False
                self.floor99_trial_missing =0
                self.floor99_trial_total =0
                self.floor99_trial_battle_active =False
                self.floor99_trial_post_pending =False
                self.reset_enemy_battle_params ()
                self.battle_auto_equip_used =False
                self.powup =1
                self.emy_powup =1
                self.poison =0
                self.save_from_stair = False
                self.save_from_boss = False
                self.stair_save_slot = 0
                self.stair_choice_cmd = 0
                self.stair_prompted = False
                self.stair_choice_input_lock = False
                self.boss_save_cmd = 0
                self.boss_save_input_lock = False
                self.boss_transition_mode = False
                self.floor_transition_delta = 1
                self.tool_growth_choice_active = False
                self.tool_growth_choice_cmd = 0
                self.tool_weapon_choice_active = False
                self.tool_weapon_choice_cmd = 0
                self.tool_weapon_choice_targets = []
                self.tool_weapon_choice_tool_id = ""
                self.tool_weapon_choice_prompt = ""
                self.tool_notice_text = ""
                self.tool_notice_timer = 0
                self.pl_shield =self.read_weapon_levels_from_save (loaddata ,"shield")
                self.pl_armor =self.read_weapon_levels_from_save (loaddata ,"armor")
                self.pl_sword =self.read_weapon_levels_from_save (loaddata ,"sword")
                self.apply_equipped_slots(
                    loaddata .get ("equip_shield",0 ),
                    loaddata .get ("equip_armor",0 ),
                    loaddata .get ("equip_sword",0 ),
                )
                self.refresh_pl_magmax ()
                self.update_player_images ()
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
                self.fairy_pos =self.find_fairy_position ()
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

    # save data を生成する
    def make_current_save_data(self):
        return {
            "floor": self.floor,
            "pl_lifemax": self.pl_lifemax,
            "pl_life": self.pl_life,
            "pl_mag": self.pl_mag,
            "pl_magmax": self.pl_magmax,
            "pl_str": self.pl_str,
            "pl_exp": self.pl_exp,
            "pl_level": self.pl_level,
            "potion": self.potion,
            "potion_lv": self.potion_lv,
            "blazegem": self.blazegem,
            "blazegem_lv": self.blazegem_lv,
            "guard": self.guard,
            "guard_lv": self.guard_lv,
            "truth_fragment": self.truth_fragment,
            "truth_fragment_floors": sorted (self.truth_fragment_floors),
            "heirloom_pendant": self.heirloom_pendant,
            "tool_food": self.tool_food,
            "tool_magic_water": self.tool_magic_water,
            "tool_magic_seed": self.tool_magic_seed,
            "tool_growth": self.tool_growth,
            "tool_sword_polish": self.tool_sword_polish,
            "tool_shield_harden": self.tool_shield_harden,
            "tool_armor_patch": self.tool_armor_patch,
            "auto_equip_attack_sword": self.auto_equip_attack_sword,
            "auto_equip_magic_staff": self.auto_equip_magic_staff,
            "auto_equip_bomb_cannon": self.auto_equip_bomb_cannon,
            "auto_equip_guard_shield": self.auto_equip_guard_shield,
            "auto_equip_potion_armor": self.auto_equip_potion_armor,
            "shield": self.pl_shield,
            "armor": self.pl_armor,
            "sword": self.pl_sword,
            "equip_shield": self.eq_shield,
            "equip_armor": self.eq_armor,
            "equip_sword": self.eq_sword,
            "dungeon": self.dungeon,
            "pl_x": self.pl_x,
            "pl_y": self.pl_y,
            "true_episode_heard": self.true_episode_heard,
            "encountered_enemies": sorted(self.encountered_enemies),
            "tutorial_progress": self.tutorial_save_data(),
        }

    # プロローグ終了後にゲームを開始する
    def start_game_after_prologue(self):
        self.start_new_game()
        bg_rect =self.blit_scaled_bg (pygame .display .get_surface (),self.imgBtlBG ,0 ,0 ,False )
        bg_left ,bg_top ,bg_w ,bg_h =bg_rect
        self.floor_title_active = True
        self.floor_title_pos = (bg_left +bg_w //2 -42 ,bg_top +int (bg_h *0.4 ))
        self.idx =110
        self.tmr =6

    # 文章スクロール演出を描画する
    def draw_story_scroll(self, bg, fnt, key, lines, line_duration, fade_in, end_hold, end_fade, lock_attr=None, complete_callback=None):
        max_lines =12
        line_height =32
        total_duration =len (lines )*line_duration

        if key [K_s ]:
            if complete_callback:
                complete_callback()
            return True

        line_index =self.tmr //line_duration
        phase =self.tmr %line_duration
        if lock_attr and getattr(self, lock_attr, False):
            if not (key [K_RETURN ]or key [K_RIGHT ]or key [K_a ]):
                setattr(self, lock_attr, False)
        else:
            if key [K_RETURN ]or key [K_RIGHT ]or key [K_a ]:
                if line_index <len (lines )and phase <fade_in:
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

        if self.tmr >=total_duration:
            end_phase =self.tmr -total_duration
            if end_phase >=end_hold +end_fade:
                if complete_callback:
                    complete_callback()
                return True
            if end_phase <end_hold:
                alpha =255
            else:
                alpha =int (255 *(1 -(end_phase -end_hold )/end_fade ))
            visible_start =max (0 ,len (lines )-max_lines )
            for i in range (visible_start ,len (lines )):
                txt =lines [i ]
                if txt:
                    y =start_y +(i -visible_start )*line_height
                    self.draw_text_alpha (bg ,txt ,text_x ,y ,fnt ,WHITE ,alpha )
            return False

        visible_start =max (0 ,line_index -(max_lines -1 ))
        for i in range (visible_start ,min (line_index ,len (lines ))):
            txt =lines [i ]
            if txt:
                y =start_y +(i -visible_start )*line_height
                self.draw_text (bg ,txt ,text_x ,y ,fnt ,WHITE )
        alpha =int (255 *phase /fade_in )if phase <fade_in else 255
        if line_index <len (lines ):
            txt =lines [line_index ]
            if txt:
                y =start_y +(line_index -visible_start )*line_height
                self.draw_text_alpha (bg ,txt ,text_x ,y ,fnt ,WHITE ,alpha )
        return False

    # prologue を描画する
    def draw_prologue (self ,bg ,fnt ,key ):
        self.draw_story_scroll (
            bg ,
            fnt ,
            key ,
            self.prologue_lines ,
            line_duration =20 ,
            fade_in =15 ,
            end_hold =30 ,
            end_fade =60 ,
            lock_attr ="prologue_input_lock",
            complete_callback =self.start_game_after_prologue
        )

    # epilogue を描画する
    def draw_epilogue (self ,bg ,fnt ,key ):
        return self.draw_story_scroll (
            bg ,
            fnt ,
            key ,
            EPILOGUE_LINES ,
            line_duration =15 ,
            fade_in =13 ,
            end_hold =30 ,
            end_fade =30
        )

    # end roll を描画する
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

    # フォントを取得する
    def get_font (self ,size ):
        font_path =os .path .join (self.path ,"fonts","PixelMplus12-Regular.ttf")
        return pygame .font .Font (font_path ,size )

    # パラメータウィンドウを描画する
    def draw_para (self ,bg ,fnt ,view_rect =None ):
        panel =BATTLE_UI_LAYOUT ["player_panel"]
        if view_rect :
            view_left ,view_top ,view_w ,view_h =view_rect
        else :
            view_left =0 
            view_top =0 
            view_w ,view_h =bg .get_size ()
        X =view_left +panel ["x_offset"]
        W =panel ["width"]
        H =panel ["height"]
        Y =view_top +panel ["top_margin"]
        win =pygame .Surface ((W ,H ),pygame .SRCALPHA )
        win .fill ((0 ,0 ,0 ,100 ))
        bg .blit (win ,[X ,Y ])

        self.draw_text (bg ,f"傷薬: {self.potion}",X +10 ,Y +8 ,fnt ,WHITE )
        self.draw_text (bg ,f"爆弾: {self.blazegem}",X +110 ,Y +8 ,fnt ,WHITE )
        self.draw_text (bg ,f"守護: {self.guard}",X +210 ,Y +8 ,fnt ,WHITE )

        col =WHITE 
        if self.pl_life <int (self.pl_lifemax /5 )and self.tmr %2 ==0 :col =RED 
        self.draw_text (bg ,f"生命　{self.pl_life}/{self.pl_lifemax}",X +10 ,Y +40 ,fnt ,col )
        self.draw_text (bg ,f"攻撃　{self.pl_str}",X +10 ,Y +65 ,fnt ,WHITE )
        self.draw_text (bg ,f"魔力　{self.pl_mag}/{self.pl_magmax}",X +10 ,Y +90 ,fnt ,WHITE )
        self.draw_text (bg ,f"レベル　{self.pl_level}　　経験　{self.pl_exp}/{(self.pl_lifemax -250 )*20}",X +10 ,Y +115 ,fnt ,WHITE )

        self.draw_text (bg ,self.get_equipped_weapon_text ("shield","盾"),X +175 ,Y +40 ,fnt ,WHITE )
        self.draw_text (bg ,self.get_equipped_weapon_text ("armor","鎧"),X +175 ,Y +65 ,fnt ,WHITE )
        self.draw_text (bg ,self.get_equipped_weapon_text ("sword","剣"),X +175 ,Y +90 ,fnt ,WHITE )

    # ミニマップを更新する
    def update_minimap_grid (self ,new_seen ):
        if self.map_grid_surface is None or self.map_grid_surface.get_size ()!=(DUNGEON_W ,DUNGEON_H ):
            self.map_grid_surface = pygame.Surface((DUNGEON_W, DUNGEON_H), pygame.SRCALPHA)
            self.map_grid_surface.fill((0, 0, 0, 120))
            for y in range (DUNGEON_H ):
                row =self.map_seen [y ]
                for x in range (DUNGEON_W ):
                    if row [x ]and self.dungeon [y ][x ] not in (7 ,8 ,9 ,13 ) :
                        self.map_grid_surface.set_at((x, y), (140, 140, 140, 160))
        if new_seen :
            for x ,y in new_seen :
                self.map_grid_surface.set_at((x, y), (140, 140, 140, 160))

    # ミニマップを描画する
    def draw_minimap (self ,bg ,view_rect ,new_seen ):
        view_left ,view_top ,view_w ,view_h =view_rect
        margin =20
        max_w =int (view_w *0.3 )
        max_h =int (view_h *0.3 )
        scale =min (max_w /DUNGEON_W ,max_h /DUNGEON_H )
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
        for wx ,wy in self.map_item_walls :
            if 0 <=wy <len (self.dungeon )and 0 <=wx <len (self.dungeon [wy ])and self.dungeon [wy ][wx ]==7 :
                mx =int (wx *scale )
                my =int (wy *scale )
                bg .fill ((255 ,255 ,0 ,220 ),[map_x +mx ,map_y +my ,marker ,marker ])
        for wx ,wy in self.map_event_walls :
            if 0 <=wy <len (self.dungeon )and 0 <=wx <len (self.dungeon [wy ])and self.dungeon [wy ][wx ]==8 :
                mx =int (wx *scale )
                my =int (wy *scale )
                bg .fill ((80 ,255 ,80 ,220 ),[map_x +mx ,map_y +my ,marker ,marker ])
        for wx ,wy in self.map_info_walls :
            if 0 <=wy <len (self.dungeon )and 0 <=wx <len (self.dungeon [wy ])and self.dungeon [wy ][wx ]==13 :
                mx =int (wx *scale )
                my =int (wy *scale )
                bg .fill ((205 ,120 ,255 ,220 ),[map_x +mx ,map_y +my ,marker ,marker ])
        if self.fairy_pos :
            fx ,fy =self.fairy_pos
            mx =int (fx *scale )
            my =int (fy *scale )
            bg .fill ((0 ,192 ,255 ,220 ),[map_x +mx ,map_y +my ,marker ,marker ])
        px =int (self.pl_x *scale )
        py =int (self.pl_y *scale )
        bg .fill ((255 ,0 ,0 ,200 ),[map_x +px ,map_y +py ,marker ,marker ])


    # ダンジョンBGMを現在フロア用に再開する
    def resume_dungeon_bgm(self):
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


    # 通常の戦闘を初期化する
    def init_battle (self ):
        if self.floor99_trial_battle_active:
            self.emy_typ =random .choice ([7 ,8 ,9 ,10 ])
            self.emy_lev =99
        else:
            self.emy_typ =random .randint (0 ,EMY_APPEAR [self.floor -1 ] )
            if self.truth_fragment_drop_battle and self.emy_typ ==6 :
                while self.emy_typ ==6 :
                    self.emy_typ =random .randint (0 ,EMY_APPEAR [self.floor -1 ] )
            self.emy_lev =random .randint (1 ,self.floor )
        self.encountered_enemies.add(self.emy_typ)
        self.imgEnemy =pygame .image .load (self.path +"/image/enemy/enemy"+str (self.emy_typ )+"_"+str ((self.floor -1 )//30 )+".png")
        new_w =int (self.imgEnemy .get_width ()*1.1 )
        new_h =int (self.imgEnemy .get_height ()*1.1 )
        self.imgEnemy =pygame .transform .scale (self.imgEnemy ,(new_w ,new_h ))
        self.emy_name =EMY_NAME [self.emy_typ ]
        tier =(self.floor -1 )//10
        base =max (1 ,int (2.4 *EMY_LIFE [self.emy_typ ]-100 ))
        floor_mul =1.0 +0.16 *tier
        level_mul =1.0 +0.12 *(self.emy_lev -1 )/99
        level_add =(self.emy_lev -1 )*10
        self.emy_lifemax =int (base *floor_mul *level_mul +level_add +tier*45 )
        self.emy_life =self.emy_lifemax 
        str_base =max (1 ,int (EMY_STR [self.emy_typ ]))
        str_level_add =(self.emy_lev -1 )
        self.emy_str =int (str_base *floor_mul *level_mul +str_level_add +tier*15)
        screen =pygame .display .get_surface ()
        screen_w ,screen_h =screen .get_size ()
        self.emy_x =screen_w //2 -self.imgEnemy .get_width ()//2 
        self.emy_y =1.45*screen_h //2 -self.imgEnemy .get_height () 


    # bossbattle を初期化する
    def init_bossbattle (self ):
        self.emy_lev =1
        self.emy_typ =109 +int (self.floor //10 ) +self.change
        self.encountered_enemies.add(self.emy_typ)
        self.imgEnemy =pygame .image .load (self.path +"/image/boss/boss_"+str (self.emy_typ -110 )+".png")
        new_w =int (self.imgEnemy .get_width ()*1.1 )
        new_h =int (self.imgEnemy .get_height ()*1.1 )
        self.imgEnemy =pygame .transform .scale (self.imgEnemy ,(new_w ,new_h ))
        self.emy_name =EMY_NAME [self.emy_typ ]
        self.emy_lifemax =EMY_LIFE [self.emy_typ ]
        self.emy_life =self.emy_lifemax 
        self.emy_str =EMY_STR [self.emy_typ ]
        screen =pygame .display .get_surface ()
        screen_w ,screen_h =screen .get_size ()
        self.emy_x =screen_w //2 -self.imgEnemy .get_width ()//2 
        self.emy_y =1.45*screen_h //2 -self.imgEnemy .get_height ()

    # grant weapon set for floor を付与する
    def grant_weapon_set_for_floor (self ,floor ):
        level ,trap_ids =ITEM_WALL_WEAPON_SET [floor ]
        for trap_id in trap_ids :
            slot =trap_id //3
            if trap_id %3 ==0 :
                self.pl_shield [slot ]=level
            elif trap_id %3 ==1 :
                self.pl_armor [slot ]=level
            else :
                self.pl_sword [slot ]=level
        self.update_player_images ()

    # 敵の体力バーを描画する
    def draw_bar (self ,bg ,x ,y ,w ,h ,val ,ma ):
        pygame .draw .rect (bg ,WHITE ,[x -2 ,y -2 ,w +4 ,h +4 ])
        pygame .draw .rect (bg ,BLACK ,[x ,y ,w ,h ])
        if val >0 :
            pygame .draw .rect (bg , SILVER, [x ,y ,w *val /ma ,h ])

    # 戦闘画面を描画する
    def draw_battle (self ,bg ,fnt ):
        panel =BATTLE_UI_LAYOUT ["player_panel"]
        status_layout =BATTLE_UI_LAYOUT ["status"]
        enemy_layout =BATTLE_UI_LAYOUT ["enemy"]
        msg_layout =BATTLE_UI_LAYOUT ["message_window"]
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
        enemy_name_y =bg_top +bg_h -enemy_layout ["name_bottom_offset"]
        enemy_bar_y =enemy_name_y +enemy_layout ["bar_y_offset"]
        enemy_state_y =enemy_name_y +enemy_layout ["state_y_offset"]
        W =msg_layout ["width"]
        H =msg_layout ["height"]
        msg_x =bg_left +bg_w -msg_layout ["right_margin"]-W
        msg_y =bg_top +msg_layout ["top_margin"]
        win =pygame .Surface ((W ,H ),pygame .SRCALPHA )
        win .fill ((0 ,0 ,0 ,100 ))
        bg .blit (win ,[msg_x ,msg_y ])
        if self.emy_life >0 and self.emy_blink %2 ==0 :
            bg .blit (self.imgEnemy ,[self.emy_x ,self.emy_y +self.emy_step])
        enemy_state_entries =[]
        if self.burn_turns >0 :
            fx = self.emy_x + self.imgEnemy.get_width() - self.imgFire.get_width()
            fy = self.emy_y + self.emy_step - self.imgFire.get_height() // 2
            bg .blit (self.imgFire ,[fx ,fy ])
            enemy_state_entries .append ((f"火傷 {'・'*self.burn_turns}",RED ))
        if self.emy_powup >1 :
            enemy_state_entries .append (("力↑",RED ))
        if self.emy_poison >0 :
            enemy_state_entries .append ((f"毒 {'・'*self.emy_poison}",COPPER ))
        if self.emy_typ ==116 or self.emy_typ ==120 :
            enemy_state_entries .append (("マギア : "+str (self.madoka )+"/1000",WHITE ))
        enemy_state_line_h =fnt .get_height ()+2
        for i ,(state_txt ,state_col )in enumerate (enemy_state_entries ):
            self.draw_text (bg ,state_txt ,bg_left +enemy_layout ["label_x_offset"],enemy_state_y +i *enemy_state_line_h ,fnt ,state_col )
        self.draw_bar (bg ,bg_left +enemy_layout ["bar_x_offset"],enemy_bar_y ,enemy_layout ["bar_width"],enemy_layout ["bar_height"],self.emy_life ,self.emy_lifemax )
        if self.emy_blink >0 :
            self.emy_blink =self.emy_blink -1 
        para_x =bg_left +panel ["x_offset"]
        status_y =bg_top +panel ["top_margin"]+panel ["height"]+status_layout ["y_gap_from_panel"]
        status_x =para_x +status_layout ["x_offset_from_panel"]
        status_line_h =fnt .get_height ()+status_layout ["line_gap"]
        status_entries =[]
        if self.guard_remain >0 :
            status_entries .append ((f"守護 {'・'*self.guard_remain}",GREEN ))
        if self.poison >0 :
            status_entries .append ((f"毒 {'・'*self.poison}",COPPER ))
        if self.powup >1 :
            status_entries .append (("力↑",RED ))
        for i ,(status_txt ,status_col )in enumerate (status_entries ):
            self.draw_text (bg ,status_txt ,status_x ,status_y +i *status_line_h ,fnt ,status_col )
        for i in range (10 ):# 戦闘メッセージの表示
            self.draw_text (bg ,self.message [i ],msg_x +msg_layout ["text_x_margin"],msg_y +msg_layout ["text_y_margin"]+i *msg_layout ["line_height"],fnt ,WHITE )
        if self.boss ==0 :
            self.draw_text (bg ,f"{self.emy_name}  Lv.{self.emy_lev}",bg_left +enemy_layout ["label_x_offset"],enemy_name_y ,fnt ,WHITE )
        else :
            self.draw_text (bg ,f"{self.emy_name}",bg_left +enemy_layout ["label_x_offset"],enemy_name_y ,fnt ,WHITE )
        self.draw_para (bg ,fnt ,bg_rect )# 主人公の能力を表示

    # menu command の処理を行う
    def menu_command (self ,bg ,fnt ,key ):
        ent =False 
        if self.menu_cmd >=len (MENU ):
            self.menu_cmd =len (MENU )-1 
        if key [K_UP ]and self.menu_cmd >0 :
            self.menu_cmd -=1 
        if key [K_DOWN ]and self.menu_cmd <len (MENU )-1 :
            self.menu_cmd +=1 
        if key [K_RETURN ]or key [K_a ]:
            ent =True 
        win_w =360 
        line_h =32 
        win_h =line_h *len (MENU )+20 
        screen_w ,screen_h =bg .get_size ()
        win_x =(screen_w -win_w )//2 
        win_y =(screen_h -win_h )//2 
        pygame .draw .rect (bg ,BLACK ,[win_x ,win_y ,win_w ,win_h ])
        for i, label in enumerate (MENU ):
            y =win_y +10 +i *line_h 
            if self.menu_cmd ==i :
                self.draw_text (bg ,"▶",win_x +20 ,y ,fnt ,WHITE )
            self.draw_text (bg ,label ,win_x +50 ,y ,fnt ,WHITE )
        return ent 

    # 自動装備設定の項目を取得する
    def get_auto_equip_settings(self):
        rules = [
            {"attr": "auto_equip_attack_sword", "action": "通常攻撃時", "group": "sword", "slot": 0},
            {"attr": "auto_equip_magic_staff", "action": "魔法使用時", "group": "sword", "slot": 1},
            {"attr": "auto_equip_bomb_cannon", "action": "爆弾使用時", "group": "sword", "slot": 2},
            {"attr": "auto_equip_guard_shield", "action": "守護使用時", "group": "shield", "slot": 2},
            {"attr": "auto_equip_potion_armor", "action": "傷薬使用時", "group": "armor", "slot": 2},
        ]
        options = []
        for rule in rules:
            weapon_name = self.get_weapon_name(rule["group"], rule["slot"])
            options.append({
                "attr": rule["attr"],
                "label": f'{rule["action"]}に自動的に{weapon_name}を装備する',
                "group": rule["group"],
                "slot": rule["slot"],
            })
        return options

    # 設定画面の描画とコマンド処理
    def settings_command(self, bg, fnt, key):
        ent = False
        options = self.get_auto_equip_settings()
        if self.settings_cmd >= len(options):
            self.settings_cmd = len(options) - 1
        if key[K_UP] and self.settings_cmd > 0:
            self.settings_cmd -= 1
        if key[K_DOWN] and self.settings_cmd < len(options) - 1:
            self.settings_cmd += 1
        if key[K_RETURN] or key[K_a]:
            ent = True

        win_w = 860
        line_h = 32
        title_h = 46
        footer_h = 54
        win_h = title_h + line_h * len(options) + footer_h
        screen_w, screen_h = bg.get_size()
        win_x = (screen_w - win_w) // 2
        win_y = (screen_h - win_h) // 2
        pygame.draw.rect(bg, BLACK, [win_x, win_y, win_w, win_h])
        pygame.draw.rect(bg, WHITE, [win_x, win_y, win_w, win_h], 2)
        self.draw_text(bg, "設定を変える", win_x + 20, win_y + 10, fnt, WHITE)
        for i, option in enumerate(options):
            y = win_y + title_h + i * line_h
            if self.settings_cmd == i:
                self.draw_text(bg, "▶", win_x + 20, y, fnt, WHITE)
            self.draw_text(bg, option["label"], win_x + 52, y, fnt, WHITE)
            state = "ON" if getattr(self, option["attr"], False) else "OFF"
            state_col = GREEN if state == "ON" else GRAY
            self.draw_text(bg, state, win_x + win_w - 70, y, fnt, state_col)
        self.draw_text(bg, "[A]/[Enter] ON/OFF  [B]/[Back] 戻る", win_x + 20, win_y + win_h - 30, fnt, WHITE)
        return ent

    # 装備変更画面の入力処理を共通化する
    def handle_equip_screen_input(self, bg, fnt, key, back_idx, back_tmr=0, set_menu_back=False):
        if self.equip_back_lock:
            if not (key[K_b] or key[K_BACKSPACE]):
                self.equip_back_lock = False
        if self.equip_accept_lock:
            if not (key[K_RETURN] or key[K_a]):
                self.equip_accept_lock = False
        if (key[K_b] or key[K_BACKSPACE]) and not self.equip_back_lock:
            self.equip_back_lock = True
            if set_menu_back:
                self.menu_back_lock = True
            self.idx = back_idx
            self.tmr = back_tmr
            return
        ent = self.equip_grid_command(bg, fnt, key)
        if self.equip_accept_lock:
            ent = False
        if ent:
            if self.equip_weapon_index(self.equip_cursor):
                self.update_player_images()
            self.equip_accept_lock = True

    # どうぐ一覧の描画系処理
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
            if i ==self.tool_cmd and not (self.tool_confirm_active or self.tool_growth_choice_active or self.tool_weapon_choice_active):
                self.draw_text (bg ,"▶",win_x +8 ,y ,fnt ,WHITE )
            self.draw_text (bg ,name ,win_x +28 ,y ,fnt ,WHITE )
            cnt =f"x {count}"
            cnt_w =fnt .size (cnt )[0 ]
            self.draw_text (bg ,cnt ,win_x +win_w -30 -cnt_w ,y ,fnt ,WHITE )
        if len (tools )==0 :
            self.draw_text (bg ,"（どうぐなし）",win_x +28 ,start_y ,fnt ,WHITE )
        self.draw_text (bg ,"[B]/[Back] 戻る",win_x +win_w -170 ,win_y +win_h -32 ,fnt ,WHITE )
        selected_tool =None
        if len (tools )>0 and 0 <=self.tool_cmd <len (tools ):
            selected_tool =tools [self.tool_cmd ]
        self.draw_tool_description (bg ,fnt ,selected_tool )
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
        if self.tool_growth_choice_active :
            options =["生命 +4","攻撃 +2"]
            box_w =250
            box_h =120
            box_x =win_x +win_w -box_w -20
            box_y =win_y +win_h -box_h -46
            pygame .draw .rect (bg ,BLACK ,[box_x ,box_y ,box_w ,box_h ])
            pygame .draw .rect (bg ,WHITE ,[box_x ,box_y ,box_w ,box_h ],2 )
            self.draw_text (bg ,"強化対象を選んでください",box_x +16 ,box_y +10 ,fnt ,WHITE )
            for i ,label in enumerate (options ):
                y =box_y +44 +i *28
                if self.tool_growth_choice_cmd ==i :
                    self.draw_text (bg ,"▶",box_x +16 ,y ,fnt ,WHITE )
                self.draw_text (bg ,label ,box_x +42 ,y ,fnt ,WHITE )
        if self.tool_weapon_choice_active :
            options =self.tool_weapon_choice_targets
            line_h_choice =26
            box_w =340
            box_h =84 +line_h_choice *max (1 ,len (options ))
            box_x =win_x +win_w -box_w -20
            box_y =win_y +win_h -box_h -46
            pygame .draw .rect (bg ,BLACK ,[box_x ,box_y ,box_w ,box_h ])
            pygame .draw .rect (bg ,WHITE ,[box_x ,box_y ,box_w ,box_h ],2 )
            prompt =self.tool_weapon_choice_prompt if self.tool_weapon_choice_prompt else "どの武器に使用しますか？"
            self.draw_text (bg ,prompt ,box_x +16 ,box_y +10 ,fnt ,WHITE )
            for i ,target in enumerate (options ):
                label =f"{target ['name']} Lv.{target ['level']}"
                y =box_y +46 +i *line_h_choice
                if self.tool_weapon_choice_cmd ==i :
                    self.draw_text (bg ,"▶",box_x +16 ,y ,fnt ,WHITE )
                text_col =WHITE if target .get ("can_upgrade",True )else GRAY
                self.draw_text (bg ,label ,box_x +42 ,y ,fnt ,text_col )

    # draw tool description を描画する
    def draw_tool_description (self ,bg ,fnt ,tool ):
        if tool is None :
            tool_id =""
            desc =""
        else :
            tool_id =tool ["id"]
            desc =TOOL_INFO .get (tool_id ,"情報が登録されていません。")
        if self.tool_notice_timer >0 and self.tool_notice_text:
            desc =self.tool_notice_text
            self.tool_notice_timer -=1
            if self.tool_notice_timer <=0:
                self.tool_notice_text =""
        if tool_id !=self.tool_desc_tool_id :
            self.tool_desc_tool_id =tool_id
        self.draw_bottom_description_window (bg ,fnt ,desc )

    # 共通のセリフウィンドウレイアウト情報を取得する
    def get_dialog_window_layout(self, bg, dlg_y_ratio=525 / 720):
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
        dlg_y =view_top +int (dlg_y_ratio *view_h )
        dlg_w =max (1 ,int (800 *scale_x ))
        dlg_h =max (1 ,int (160 *scale_y ))
        text_x =view_left +int (60 *scale_x )
        text_y =view_top +int (560 *scale_y )
        line_h =max (1 ,int (28 *scale_y ))
        prompt_x =view_left +int (700 *scale_x )
        prompt_y =view_top +int (640 *scale_y )
        return {
            "view_left": view_left,
            "view_top": view_top,
            "view_w": view_w,
            "view_h": view_h,
            "scale_x": scale_x,
            "scale_y": scale_y,
            "dlg_x": dlg_x,
            "dlg_y": dlg_y,
            "dlg_w": dlg_w,
            "dlg_h": dlg_h,
            "text_x": text_x,
            "text_y": text_y,
            "line_h": line_h,
            "prompt_x": prompt_x,
            "prompt_y": prompt_y,
        }

    # 共通のセリフウィンドウを描画する
    def draw_dialog_window(self, bg, layout, alpha=255):
        dialog = pygame.Surface((layout["dlg_w"], layout["dlg_h"]), pygame.SRCALPHA)
        dialog.fill((0, 0, 0, alpha))
        bg.blit(dialog, [layout["dlg_x"], layout["dlg_y"]])
        pygame.draw.rect(bg, WHITE, [layout["dlg_x"], layout["dlg_y"], layout["dlg_w"], layout["dlg_h"]], 2)

    # 共通のセリフ本文を描画する
    def draw_dialog_text(self, bg, fnt, layout, text):
        if len(text) <= 0:
            return
        parts = text.split("\n")
        for i, part in enumerate(parts):
            self.draw_text(bg, part, layout["text_x"], layout["text_y"] + i * layout["line_h"], fnt, WHITE)

    # 共通の文字送り処理を進行して可視テキストを返す
    def step_talk_text(self, lines, talk_index, talk_char_count, talk_last_tick, interval_ms=100):
        visible = ""
        if talk_index < len(lines):
            line = lines[talk_index]
            now = pygame.time.get_ticks()
            if talk_char_count < len(line) and now - talk_last_tick >= interval_ms:
                talk_char_count += 1
                talk_last_tick = now
            visible = line[:talk_char_count]
        return visible, talk_index, talk_char_count, talk_last_tick

    # 共通のA/Enter入力でセリフ送りを進める
    def advance_talk_text(self, lines, talk_index, talk_char_count, talk_last_tick):
        if talk_index < len(lines):
            line = lines[talk_index]
            if talk_char_count < len(line):
                talk_char_count = len(line)
            else:
                talk_index += 1
                talk_char_count = 0
                talk_last_tick = pygame.time.get_ticks()
        finished = talk_index >= len(lines)
        return talk_index, talk_char_count, talk_last_tick, finished

    # itemイベント用の共通セリフ描画と進行処理
    def step_item_event_talk(self, bg, fnt, layout, accept, show_prompt=True):
        visible ,self.item_talk_index ,self.item_talk_char_count ,self.item_talk_last_tick =self.step_talk_text (
            self.item_talk_lines ,
            self.item_talk_index ,
            self.item_talk_char_count ,
            self.item_talk_last_tick
        )
        self.draw_dialog_text (bg ,fnt ,layout ,visible )
        if show_prompt:
            self.draw_text (bg ,"[A]/[Enter]",layout ["prompt_x"],layout ["prompt_y"],fnt ,WHITE )
        finished =False
        if accept:
            self.item_talk_index ,self.item_talk_char_count ,self.item_talk_last_tick ,finished =self.advance_talk_text (
                self.item_talk_lines ,
                self.item_talk_index ,
                self.item_talk_char_count ,
                self.item_talk_last_tick
            )
        return finished

    # draw bottom description window を描画する
    def draw_bottom_description_window (self ,bg ,fnt ,desc ):
        layout =self.get_dialog_window_layout (bg ,dlg_y_ratio =525 /720 )
        self.draw_dialog_window (bg ,layout ,alpha =255 )
        self.draw_dialog_text (bg ,fnt ,layout ,desc )

    # draw equip description を描画する
    def draw_equip_description (self ,bg ,fnt ):
        if not (0 <=self.equip_cursor <9 ):
            desc =""
        elif not self.is_weapon_owned (self.equip_cursor ):
            desc =""
        else :
            trap_id =self.display_index_to_weapon_id (self.equip_cursor )
            desc =WEAPON_INFO .get (trap_id ,"情報が登録されていません。")
        self.draw_bottom_description_window (bg ,fnt ,desc )

    # draw zukan description を描画する
    def draw_zukan_description(self, bg, fnt):
        desc = ""
        if self.zukan_kind == 1 and 0 <= self.zukan_cursor < 3:
            item_name = TRE_NAME[self.zukan_cursor]
            item_level = [self.potion_lv, self.blazegem_lv, self.guard_lv][self.zukan_cursor]
            base_desc = ITEM_INFO.get(self.zukan_cursor, "情報が登録されていません。")
            desc = f"{item_name}　レベル{item_level}\n{base_desc}"
        self.draw_bottom_description_window(bg, fnt, desc)

    # どうぐ一覧に表示するためのどうぐリストを取得
    def get_tool_entries (self ):
        tools =[]
        if self.tool_food >0 :
            tools .append ({"id":"food","name":TRE_NAME [3 ],"count":self.tool_food ,"usable":True })
        if self.tool_magic_water >0 :
            tools .append ({"id":"magic_water","name":TRE_NAME [4 ],"count":self.tool_magic_water ,"usable":True })
        if self.tool_magic_seed >0 :
            tools .append ({"id":"magic_seed","name":TRE_NAME [5 ],"count":self.tool_magic_seed ,"usable":True })
        if self.tool_growth >0 :
            tools .append ({"id":"growth_essence","name":TRE_NAME [6 ],"count":self.tool_growth ,"usable":True })
        if self.tool_sword_polish >0 :
            tools .append ({
                "id":"sword_polish",
                "name":TRE_NAME [7 ],
                "count":self.tool_sword_polish ,
                "usable":any (target .get ("can_upgrade",True )for target in self.get_weapon_upgrade_targets ("sword_polish"))
            })
        if self.tool_shield_harden >0 :
            tools .append ({
                "id":"shield_harden",
                "name":TRE_NAME [8 ],
                "count":self.tool_shield_harden ,
                "usable":any (target .get ("can_upgrade",True )for target in self.get_weapon_upgrade_targets ("shield_harden"))
            })
        if self.tool_armor_patch >0 :
            tools .append ({
                "id":"armor_patch",
                "name":TRE_NAME [9 ],
                "count":self.tool_armor_patch ,
                "usable":any (target .get ("can_upgrade",True )for target in self.get_weapon_upgrade_targets ("armor_patch"))
            })
        if self.truth_fragment >0 :
            tools .append ({"id":"truth_fragment","name":"しんじつのかけら","count":self.truth_fragment ,"usable":True })
        if self.heirloom_pendant >0 :
            tools .append ({"id":"heirloom_pendant","name":"形見のペンダント","count":self.heirloom_pendant ,"usable":False })
        return tools

    # 強化対象となる武器のリストを適切な順番で取得
    def get_weapon_upgrade_targets (self ,tool_id ):
        targets =[]
        if tool_id =="sword_polish":
            weapon_list =self.pl_sword
            mapping =[(0 ,2 ),(1 ,5 ),(2 ,8 )]
            group ="sword"
        elif tool_id =="shield_harden":
            weapon_list =self.pl_shield
            mapping =[(0 ,0 ),(1 ,3 ),(2 ,6 )]
            group ="shield"
        elif tool_id =="armor_patch":
            weapon_list =self.pl_armor
            mapping =[(0 ,1 ),(1 ,4 ),(2 ,7 )]
            group ="armor"
        else :
            return targets
        equipped_slot =getattr (self ,EQUIP_SLOT_ATTRS [group ])
        for slot ,trap_id in mapping:
            if weapon_list [slot ]>0 :
                targets .append ({
                    "group":group ,
                    "slot":slot ,
                    "trap_id":trap_id ,
                    "name":WPN_NAME [trap_id ],
                    "level":weapon_list [slot ],
                    "can_upgrade":weapon_list [slot ]<99 ,
                })
        targets .sort (
            key =lambda target :(
                0 if target ["can_upgrade"] else 1 ,
                0 if (target ["can_upgrade"] and target ["slot"]==equipped_slot )else 1 ,
                target ["slot"]
            )
        )
        return targets

    # find first upgradable target index を取得する
    def find_first_upgradable_target_index (self ,targets ):
        for i ,target in enumerate (targets ):
            if target .get ("can_upgrade",True ):
                return i
        return -1

    # move weapon choice cursor の移動処理を行う
    def move_weapon_choice_cursor (self ,step ):
        if not self.tool_weapon_choice_targets :
            return
        idx =self.tool_weapon_choice_cmd +step
        while 0 <=idx <len (self.tool_weapon_choice_targets ):
            if self.tool_weapon_choice_targets [idx ].get ("can_upgrade",True ):
                self.tool_weapon_choice_cmd =idx
                return
            idx +=step

    # start weapon upgrade choice を開始する
    def start_weapon_upgrade_choice (self ,tool_id ):
        targets =self.get_weapon_upgrade_targets (tool_id )
        if len (targets )==0 :
            return False
        first_upgradable =self.find_first_upgradable_target_index (targets )
        if first_upgradable <0 :
            return False
        self.tool_weapon_choice_active =True
        self.tool_weapon_choice_cmd =first_upgradable
        self.tool_weapon_choice_targets =targets
        self.tool_weapon_choice_tool_id =tool_id
        self.tool_weapon_choice_prompt ="どの武器に使用しますか？"
        return True

    # 強化対象に選ばれた武器のレベルを上げる
    def apply_weapon_upgrade (self ):
        if not self.tool_weapon_choice_active:
            return False
        if not (0 <=self.tool_weapon_choice_cmd <len (self.tool_weapon_choice_targets )):
            return False
        target =self.tool_weapon_choice_targets [self.tool_weapon_choice_cmd ]
        if not target .get ("can_upgrade",True ):
            return False
        group =target ["group"]
        slot =target ["slot"]
        if group =="sword" and self.tool_sword_polish >0 and self.pl_sword [slot ]>0 :
            self.tool_sword_polish -=1
            self.pl_sword [slot ]=min (99 ,self.pl_sword [slot ]+1 )
            return True
        elif group =="shield" and self.tool_shield_harden >0 and self.pl_shield [slot ]>0 :
            self.tool_shield_harden -=1
            self.pl_shield [slot ]=min (99 ,self.pl_shield [slot ]+1 )
            return True
        elif group =="armor" and self.tool_armor_patch >0 and self.pl_armor [slot ]>0 :
            self.tool_armor_patch -=1
            self.pl_armor [slot ]=min (99 ,self.pl_armor [slot ]+1 )
            return True
        return False

    # 食料系の道具を使用した時の効果処理
    def use_selected_tool (self ,tool_id ):
        if tool_id =="food" and self.tool_food >0 :
            self.tool_food -=1 
            self.pl_life =min (self.pl_life +40 ,self.pl_lifemax )
        elif tool_id =="magic_water" and self.tool_magic_water >0 :
            self.tool_magic_water -=1 
            self.pl_life =min (self.pl_life +20 ,self.pl_lifemax )
            self.add_pl_mag (20 )
        elif tool_id =="magic_seed" and self.tool_magic_seed >0 :
            self.tool_magic_seed -=1 
            self.add_pl_mag (100 )
            if self.tutorial_enabled and self.floor ==1 :
                self.tutorial_progress ["room4_item_used"]=True
                self.update_tutorial_floor_state ()
        elif tool_id =="truth_fragment":
            self.use_truth_fragment_item ()

    # どうぐ一覧で使用不可メッセージを表示する
    def show_tool_notice (self ,text ,duration =90 ):
        self.tool_notice_text =text
        self.tool_notice_timer =duration

    # しんじつのかけら使用時に1階戻る処理を実行する
    def use_truth_fragment_item (self ):
        if self.floor %10 ==1 :
            self.show_tool_notice ("この階では　使用できません")
            return False
        consume =2 if self.floor in self.truth_fragment_floors else 1
        if self.truth_fragment <consume :
            self.show_tool_notice ("しんじつのかけらが足りない")
            return False
        self.truth_fragment -=consume
        self.save_from_stair =False
        self.save_from_boss =False
        self.boss_transition_mode =False
        self.floor_transition_delta =-1
        self.idx =110
        self.tmr =0
        return True

    # 成長エキス使用時の効果処理
    def use_growth_essence (self ,target ):
        if self.tool_growth <=0 :
            return
        self.tool_growth -=1
        if target =="life":
            self.pl_lifemax +=4
        elif target =="str":
            self.pl_str +=2

    # 図鑑のレイアウトを取得する
    def get_zukan_layout(self):
        if self.zukan_kind == 0:
            return 4, 7, len(EMY_ZUKAN_IDS), "敵の図鑑"
        return 3, 1, 3, "アイテムの図鑑"

    # is weapon owned を判定する
    def is_weapon_owned(self, weapon_index):
        group, slot = self.weapon_index_to_group_slot(weapon_index)
        return self.get_weapon_level(group, slot) > 0

    # is enemy encountered for zukan を判定する
    def is_enemy_encountered_for_zukan(self, enemy_index):
        if not (0 <= enemy_index < len(EMY_ZUKAN_IDS)):
            return False
        enemy_id = EMY_ZUKAN_IDS[enemy_index]
        return enemy_id in self.encountered_enemies

    # get enemy catalog image を取得する
    def get_enemy_catalog_image(self, enemy_id):
        if enemy_id in self.zukan_enemy_cache:
            return self.zukan_enemy_cache[enemy_id]
        paths = []
        if enemy_id >= 110:
            paths.append(self.path + f"/image/boss/boss_{enemy_id - 110}.png")
        else:
            paths.extend(self.path + f"/image/enemy/enemy{enemy_id}_{i}.png" for i in range(4))
        if 10 <= enemy_id < 110:
            paths.append(self.path + f"/image/boss/boss_{enemy_id - 10}.png")
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

    # zukan category command の処理を行う
    def zukan_category_command(self, bg, fnt, key):
        ent = False
        options = ["敵の図鑑", "アイテムの図鑑"]
        if self.zukan_menu_cmd >= len(options):
            self.zukan_menu_cmd = len(options) - 1
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

    # zukan grid command の処理を行う
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
                else:
                    label = item_names[i]
                self.draw_text(bg, label, x + 8, y + cell // 2 - 10, fnt, WHITE)
            else:
                pygame.draw.rect(bg, (80, 80, 80), [x, y, cell, cell], 1)
            if i == self.zukan_cursor:
                pygame.draw.rect(bg, (255, 220, 90), [x, y, cell, cell], 3)

        self.draw_zukan_description(bg, fnt)
        return ent

    # draw zukan detail を描画する
    def draw_zukan_detail(self, bg, fnt):
        if not (0 <= self.zukan_detail < len(EMY_ZUKAN_IDS)):
            return
        enemy_id = EMY_ZUKAN_IDS[self.zukan_detail]
        name = EMY_NAME.get(enemy_id, f"Enemy {enemy_id}")
        info = ENEMY_INFO.get(enemy_id, "情報が登録されていません。")
        img = self.get_enemy_catalog_image(enemy_id)

        win_w = 760
        win_h = 430
        screen_w, screen_h = bg.get_size()
        win_x = (screen_w - win_w) // 2
        win_y = (screen_h - win_h) // 2
        pygame.draw.rect(bg, BLACK, [win_x, win_y, win_w, win_h])
        pygame.draw.rect(bg, WHITE, [win_x, win_y, win_w, win_h], 2)

        max_w = 260
        max_h = 260
        scale = min(max_w / max(1, img.get_width()), max_h / max(1, img.get_height()))
        draw_img = pygame.transform.scale(img, (max(1, int(img.get_width() * scale)), max(1, int(img.get_height() * scale))))
        img_x = win_x + 30 + (max_w - draw_img.get_width()) // 2
        img_y = win_y + 90 + (max_h - draw_img.get_height()) // 2
        bg.blit(draw_img, [img_x, img_y])
        pygame.draw.rect(bg, WHITE, [win_x + 30, win_y + 90, max_w, max_h], 1)

        self.draw_text(bg, name, win_x + 320, win_y + 45, self.get_font(22), WHITE)
        parts = str(info).split("\n")
        for i, part in enumerate(parts):
            self.draw_text(bg, part, win_x + 320, win_y + 110 + i * 28, fnt, WHITE)
        self.draw_text(bg, "[B]/[Back] 戻る", win_x + win_w - 180, win_y + win_h - 36, fnt, WHITE)

    # equip grid command の装備処理を行う
    def equip_grid_command(self, bg, fnt, key):
        ent = False
        cols, rows, count = 3, 3, 9
        if self.equip_cursor >= count:
            self.equip_cursor = count - 1
        row = self.equip_cursor // cols
        col = self.equip_cursor % cols
        if key[K_UP] and row > 0:
            self.equip_cursor -= cols
        if key[K_DOWN] and row < rows - 1:
            self.equip_cursor += cols
        if key[K_LEFT] and col > 0:
            self.equip_cursor -= 1
        if key[K_RIGHT] and col < cols - 1:
            self.equip_cursor += 1
        if key[K_RETURN] or key[K_a]:
            ent = True

        cell_w = int(72 * 1.7)
        cell_h = 72
        gap_x = 10
        gap_y = 10
        label_w = 36
        pad = 20
        title_h = 30
        footer_h = 38
        win_w = pad * 2 + label_w + cols * cell_w + (cols - 1) * gap_x
        win_h = pad * 2 + rows * cell_h + (rows - 1) * gap_y + title_h + footer_h
        screen_w, screen_h = bg.get_size()
        win_x = (screen_w - win_w) // 2
        win_y = (screen_h - win_h) // 2
        pygame.draw.rect(bg, BLACK, [win_x, win_y, win_w, win_h])
        pygame.draw.rect(bg, WHITE, [win_x, win_y, win_w, win_h], 2)
        self.draw_text(bg, "装備を変える", win_x + 20, win_y + 8, fnt, WHITE)

        start_x = win_x + pad + label_w
        start_y = win_y + pad + title_h
        row_labels = ["盾", "鎧", "剣"]
        for row in range(rows):
            ly = start_y + row * (cell_h + gap_y) + cell_h // 2 - 10
            self.draw_text(bg, row_labels[row], win_x + pad + 4, ly, fnt, WHITE)
        for i in range(count):
            r = i // cols
            c = i % cols
            x = start_x + c * (cell_w + gap_x)
            y = start_y + r * (cell_h + gap_y)
            pygame.draw.rect(bg, WHITE, [x, y, cell_w, cell_h], 1)
            owned = self.is_weapon_owned(i)
            trap_id = self.display_index_to_weapon_id(i)
            label = WPN_NAME[trap_id] if owned else "？"
            self.draw_text(bg, label, x + 8, y + cell_h // 2 - 10, fnt, WHITE)
            if self.is_weapon_equipped_index(i):
                pygame.draw.rect(bg, GREEN, [x + 2, y + 2, cell_w - 4, cell_h - 4], 2)
            if i == self.equip_cursor:
                pygame.draw.rect(bg, (255, 220, 90), [x, y, cell_w, cell_h], 3)

        self.draw_text(bg, "[A]/[Enter] 装備  [B]/[Back] 戻る", win_x + 20, win_y + win_h - 28, fnt, WHITE)
        self.draw_equip_description (bg ,fnt )
        return ent

    # save command を保存用に処理する
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

    # 階段の選択コマンドの処理
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

    # boss save choice command の処理を行う
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

    # battle command の戦闘用処理を行う
    def battle_command (self ,bg ,fnt ,key ):
        ent =False 
        labels = ["攻撃", "魔法", "傷薬", "爆弾", "守護", "逃走", "情報", "装備"]
        grid = [
            [0, 1, 5, 6],
            [2, 3, 4, 7],
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
        if key [K_e ]:
            self.btl_cmd =7
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

    # メッセージリストを初期化する
    def init_message (self ):
        for i in range (10 ):
            self.message [i ]=""

    # メッセージを設定する
    def set_message (self ,msg ):
        for i in range (10 ):
            if self.message [i ]=="":
                self.message [i ]=msg 
                return 
        for i in range (9 ):
            self.message [i ]=self.message [i +1 ]
        self.message [9 ]=msg 

    # 鎧系の処理
    def apply_armor_effects (self ):
        armor_heal =self.get_active_weapon_level ("armor",0 )
        armor_mag =self.get_active_weapon_level ("armor",1 )
        if armor_heal >0 :
            if random .random ()>0.7 :
                cure =int(armor_heal +random .randint (0 ,10))
                self.pl_life =min (self.pl_life +cure ,self.pl_lifemax )
                self.set_message ("　鎧の癒し 生命 +{}" .format (cure ))
                self.se [2 ].play ()
            else :
                self.tmr =self.tmr +1 
        if armor_mag >0 :
            if random .random ()>0.7 :
                mgup =int (10 +armor_mag +random .randint (0 ,armor_mag //5 ))
                self.add_pl_mag (mgup )
                self.set_message ("　鎧の魔力 魔力 +{}" .format (mgup ))
                self.se [9 ].play ()
            else :
                self.tmr =self.tmr +1 

    # 敵の行動に関する処理
    def emy_action (self ,bg ):
        action =True 
        if self.emy_typ ==4 or self.emy_typ ==115 :
            self.emy_powup =1 
            if random .random ()>0.7 :
                self.emy_powup ={4:2 ,115:15 }[self.emy_typ ]
                self.set_message ("　敵は　力をためた!")
            action =False 
        if self.emy_typ ==5 or self.emy_typ ==112:
            suck = {5:5+self.emy_lev, 112:104}[self.emy_typ] + random .randint (1 ,{5:5, 112:12}[self.emy_typ] )
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
            cure = self.emy_lifemax //{7:10, 118:100}[self.emy_typ] +random.randint (0, 10)
            self.set_message ("　敵の回復 +{}".format (int (min (cure ,self.emy_lifemax -self.emy_life ))))
            pygame .mixer .Sound (self.path +"/sound/ohd_se_potion.wav").play ()
            self.emy_life =min (self.emy_life +cure ,self.emy_lifemax )
            action =False 
        self.poison =max (self.poison -1 ,0 )
        if self.emy_typ ==8 or self.emy_typ ==111:
            force_poison =self.enemy_poison_fail_count >=7
            if force_poison or random .random ()>{8:0.3, 111:0.84}[self.emy_typ]:
                self.poison ={8:1, 111:2}[self.emy_typ]
                self.set_message ("　毒を　くらった!")
                self.enemy_poison_fail_count =0
                action =False 
            else :
                self.enemy_poison_fail_count +=1
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
                    self.truth_fragment_floors = set()
                    self.heirloom_pendant =1
                    self.tool_food =0
                    self.tool_magic_water =0
                    self.tool_magic_seed =0
                    self.tool_growth =0
                    self.tool_sword_polish =0
                    self.tool_shield_harden =0
                    self.tool_armor_patch =0
                    self.item_popup_text =""
                    self.truth_fragment_drop_battle =False
                    self.growth_essence_drop_battle =False
                    self.floor99_trial_missing =0
                    self.floor99_trial_total =0
                    self.floor99_trial_battle_active =False
                    self.floor99_trial_post_pending =False
                    self.reset_enemy_battle_params ()
                    self.tool_weapon_choice_active =False
                    self.tool_weapon_choice_cmd =0
                    self.tool_weapon_choice_targets =[]
                    self.tool_weapon_choice_tool_id =""
                    self.tool_weapon_choice_prompt =""
                    if self.keep_title_bgm_on_next_title:
                        self.keep_title_bgm_on_next_title = False
                    else:
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
                            self.potion_lv =loaddata .get ("potion_lv",0 )
                            self.blazegem =loaddata ["blazegem"]
                            self.blazegem_lv =loaddata .get ("blazegem_lv",0 )
                            self.guard =loaddata ["guard"]
                            self.guard_lv =loaddata .get ("guard_lv",0 )
                            self.truth_fragment =loaddata .get ("truth_fragment",0 )
                            self.truth_fragment_floors =set (int (v )for v in loaddata .get ("truth_fragment_floors",[] )if isinstance (v ,int ))
                            self.heirloom_pendant =loaddata .get ("heirloom_pendant",1 )
                            self.tool_food =loaddata .get ("tool_food",0 )
                            self.tool_magic_water =loaddata .get ("tool_magic_water",0 )
                            self.tool_magic_seed =loaddata .get ("tool_magic_seed",0 )
                            self.tool_growth =loaddata .get ("tool_growth",0 )
                            self.tool_sword_polish =loaddata .get ("tool_sword_polish",0 )
                            self.tool_shield_harden =loaddata .get ("tool_shield_harden",0 )
                            self.tool_armor_patch =loaddata .get ("tool_armor_patch",0 )
                            self.auto_equip_attack_sword =bool (loaddata .get ("auto_equip_attack_sword",False ))
                            self.auto_equip_magic_staff =bool (loaddata .get ("auto_equip_magic_staff",False ))
                            self.auto_equip_bomb_cannon =bool (loaddata .get ("auto_equip_bomb_cannon",False ))
                            self.auto_equip_guard_shield =bool (loaddata .get ("auto_equip_guard_shield",False ))
                            self.auto_equip_potion_armor =bool (loaddata .get ("auto_equip_potion_armor",False ))
                            self.item_popup_text =""
                            self.truth_fragment_drop_battle =False
                            self.growth_essence_drop_battle =False
                            self.floor99_trial_missing =0
                            self.floor99_trial_total =0
                            self.floor99_trial_battle_active =False
                            self.floor99_trial_post_pending =False
                            self.battle_auto_equip_used =False
                            self.powup =1
                            self.reset_enemy_battle_params ()
                            self.emy_powup =1
                            self.poison =0
                            self.idx =100 
                            self.pl_shield =self.read_weapon_levels_from_save (loaddata ,"shield")
                            self.pl_armor =self.read_weapon_levels_from_save (loaddata ,"armor")
                            self.pl_sword =self.read_weapon_levels_from_save (loaddata ,"sword")
                            self.apply_equipped_slots(
                                loaddata .get ("equip_shield",0 ),
                                loaddata .get ("equip_armor",0 ),
                                loaddata .get ("equip_sword",0 ),
                            )
                            self.refresh_pl_magmax ()
                            self.update_player_images ()
                            self.true_episode_heard = bool(loaddata.get("true_episode_heard", False))
                            self.item_event_phase = 0
                            self.item_choice = 0
                            self.item_reward = None
                            self.item_event_kind = ""
                            self.item_talk_lines = []
                            self.item_talk_index = 0
                            self.item_talk_char_count = 0
                            self.item_talk_last_tick = pygame.time.get_ticks()
                            self.tool_weapon_choice_active = False
                            self.tool_weapon_choice_cmd = 0
                            self.tool_weapon_choice_targets = []
                            self.tool_weapon_choice_tool_id = ""
                            self.tool_weapon_choice_prompt = ""
                            self.set_floor_assets_for_current_floor ()
                            self.init_floor_variant_map ()
                            self.init_map_state ()
                            self.fixed_floor_data = self.load_fixed_floor_data (self.floor )
                            if self.floor ==1 and self.fixed_floor_data:
                                self.setup_tutorial_floor (loaddata .get ("tutorial_progress"))
                            else:
                                self.reset_tutorial_runtime ()
                            self.fairy_pos =self.find_fairy_position ()
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
                        if self.menu_cmd ==0 :#tools
                            self.tool_back_lock =True
                            self.tool_accept_lock = True
                            self.tool_confirm_active = False
                            self.tool_confirm_cmd = 0
                            self.tool_growth_choice_active = False
                            self.tool_growth_choice_cmd = 0
                            self.tool_weapon_choice_active = False
                            self.tool_weapon_choice_cmd = 0
                            self.tool_weapon_choice_targets = []
                            self.tool_weapon_choice_tool_id = ""
                            self.tool_weapon_choice_prompt = ""
                            self.tool_notice_text = ""
                            self.tool_notice_timer = 0
                            self.tool_cmd = 0
                            self.tool_desc_tool_id =""
                            self.tool_desc_char_count =0
                            self.tool_desc_last_tick =0
                            self.idx =34
                            self.tmr =0
                        elif self.menu_cmd ==1 :#図鑑
                            self.zukan_menu_cmd =0
                            self.zukan_kind =0
                            self.zukan_cursor =0
                            self.zukan_detail =0
                            self.zukan_accept_lock = True
                            self.idx =31
                            self.tmr =0
                        elif self.menu_cmd ==2 :#equip
                            self.equip_cursor =0
                            self.equip_back_lock =True
                            self.equip_accept_lock =True
                            self.idx =35
                            self.tmr =0
                        elif self.menu_cmd ==3 :#settings
                            self.settings_cmd =0
                            self.settings_back_lock =True
                            self.settings_accept_lock =True
                            self.idx =36
                            self.tmr =0
                        elif self.menu_cmd ==4 :#go_title
                            self.confirm_cmd =0 
                            self.title_confirm_lock = True
                            self.idx =60 
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
                            if self.zukan_kind ==0 :
                                if not self.is_enemy_encountered_for_zukan (self.zukan_cursor ):
                                    self.zukan_accept_lock = True
                                else:
                                    self.zukan_detail =self.zukan_cursor
                                    self.zukan_accept_lock = True
                                    self.idx =33
                                    self.tmr =0

            elif self.idx ==33 :# 図鑑詳細（敵のみ）
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
                if self.tool_weapon_choice_active:
                    if self.tool_weapon_choice_targets:
                        self.tool_weapon_choice_cmd =max (0 ,min (self.tool_weapon_choice_cmd ,len (self.tool_weapon_choice_targets )-1 ))
                        if not self.tool_weapon_choice_targets [self.tool_weapon_choice_cmd ].get ("can_upgrade",True ):
                            first_upgradable =self.find_first_upgradable_target_index (self.tool_weapon_choice_targets )
                            if first_upgradable >=0 :
                                self.tool_weapon_choice_cmd =first_upgradable
                    if key [K_UP ]:
                        self.move_weapon_choice_cursor (-1 )
                    if key [K_DOWN ]:
                        self.move_weapon_choice_cursor (1 )
                    if (key [K_b ]or key [K_BACKSPACE ]) and not self.tool_back_lock:
                        self.tool_back_lock = True
                        self.tool_weapon_choice_active = False
                        self.tool_weapon_choice_targets = []
                        self.tool_weapon_choice_tool_id = ""
                        self.tool_weapon_choice_prompt = ""
                    elif accept and not self.tool_accept_lock:
                        if self.apply_weapon_upgrade ():
                            tool_entries =self.get_tool_entries ()
                            if len (tool_entries )==0 :
                                self.tool_cmd =0
                            elif self.tool_cmd >=len (tool_entries ):
                                self.tool_cmd =len (tool_entries )-1
                            self.tool_weapon_choice_active = False
                            self.tool_weapon_choice_targets = []
                            self.tool_weapon_choice_tool_id = ""
                            self.tool_weapon_choice_prompt = ""
                            self.tool_accept_lock = True
                elif self.tool_growth_choice_active:
                    if key [K_UP ]and self.tool_growth_choice_cmd >0 :
                        self.tool_growth_choice_cmd -=1
                    if key [K_DOWN ]and self.tool_growth_choice_cmd <1 :
                        self.tool_growth_choice_cmd +=1
                    if (key [K_b ]or key [K_BACKSPACE ]) and not self.tool_back_lock:
                        self.tool_back_lock = True
                        self.tool_growth_choice_active = False
                    elif accept and not self.tool_accept_lock:
                        if self.tool_growth_choice_cmd ==0 :
                            self.use_growth_essence ("life")
                        else :
                            self.use_growth_essence ("str")
                        tool_entries =self.get_tool_entries ()
                        if len (tool_entries )==0 :
                            self.tool_cmd =0
                        elif self.tool_cmd >=len (tool_entries ):
                            self.tool_cmd =len (tool_entries )-1
                        self.tool_growth_choice_active = False
                        self.tool_accept_lock = True
                elif self.tool_confirm_active:
                    if key [K_UP ]and self.tool_confirm_cmd >0 :
                        self.tool_confirm_cmd -=1 
                    if key [K_DOWN ]and self.tool_confirm_cmd <1 :
                        self.tool_confirm_cmd +=1 
                    if (key [K_b ]or key [K_BACKSPACE ]) and not self.tool_back_lock:
                        self.tool_back_lock = True
                        self.tool_confirm_active = False
                    elif accept and not self.tool_accept_lock:
                        if self.tool_confirm_cmd ==0 and len (tool_entries )>0 and tool_entries [self.tool_cmd ]["usable"]:
                            selected_tool_id =tool_entries [self.tool_cmd ]["id"]
                            if selected_tool_id =="growth_essence":
                                self.tool_growth_choice_active = True
                                self.tool_growth_choice_cmd =0
                            elif selected_tool_id in ("sword_polish","shield_harden","armor_patch"):
                                if self.start_weapon_upgrade_choice (selected_tool_id ):
                                    self.tool_accept_lock = True
                            else:
                                self.use_selected_tool (selected_tool_id)
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
                                selected_tool_id =tool_entries [self.tool_cmd ]["id"]
                                if selected_tool_id =="growth_essence":
                                    self.tool_growth_choice_active =True
                                    self.tool_growth_choice_cmd =0
                                    self.tool_accept_lock =True
                                elif selected_tool_id in ("sword_polish","shield_harden","armor_patch"):
                                    if self.start_weapon_upgrade_choice (selected_tool_id ):
                                        self.tool_accept_lock =True
                                else:
                                    self.tool_confirm_active = True
                                    self.tool_confirm_cmd = 0
                                    self.tool_accept_lock = True

            elif self.idx ==35 :# 装備変更
                self.draw_dungeon (screen ,fontS )
                self.handle_equip_screen_input (screen ,fontS ,key ,back_idx =30 ,back_tmr =0 ,set_menu_back =True )

            elif self.idx ==36 :# 設定変更
                self.draw_dungeon (screen ,fontS )
                if self.settings_back_lock:
                    if not (key [K_b ]or key [K_BACKSPACE ]):
                        self.settings_back_lock = False
                if self.settings_accept_lock:
                    if not (key [K_RETURN ]or key [K_a ]):
                        self.settings_accept_lock = False
                if (key [K_b ]or key [K_BACKSPACE ]) and not self.settings_back_lock:
                    self.settings_back_lock = True
                    self.menu_back_lock = True
                    self.idx =30
                    self.tmr =0
                else:
                    ent =self.settings_command (screen ,fontS ,key )
                    if self.settings_accept_lock:
                        ent =False
                    if ent and len (self.get_auto_equip_settings ())>0 :
                        setting =self.get_auto_equip_settings ()[self.settings_cmd ]
                        attr =setting ["attr"]
                        setattr (self ,attr ,not getattr (self ,attr ,False ))
                        self.settings_accept_lock =True

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
                d =self.make_current_save_data ()
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
                elif self.tmr ==100 :
                    self.idx =0 
                    self.tmr =0 


            elif self.idx ==82 :# エピローグ
                if self.draw_epilogue (screen ,fontS ,key ):
                    self.idx =83 
                    self.tmr =0 

            elif self.idx ==83 :# エンドロール
                if self.draw_end_roll (screen ,fontS ,key ):
                    self.idx =0 
                    self.tmr =0 

            elif self.idx ==84 :# ラスボス会話後フェードアウト
                self.draw_dungeon (screen ,fontS )
                fade_frames =20
                alpha =min (255 ,int (255 *self.tmr /fade_frames ))
                fade =pygame .Surface (screen .get_size (),pygame .SRCALPHA )
                fade .fill ((0 ,0 ,0 ,alpha ))
                screen .blit (fade ,[0 ,0 ])
                if self.tmr >=fade_frames :
                    pygame .mixer .music .load (self.path +"/sound/bgm_title.wav")
                    pygame .mixer .music .play (-1 )
                    self.recollection_stage =0
                    self.idx =85
                    self.tmr =0

            elif self.idx ==85 :# 回想（floor0〜9）
                if self.tmr ==1 :
                    recollection_floor_index =self.recollection_stage
                    recollection_floor_value =recollection_floor_index *10 +1
                    self.set_floor_assets (recollection_floor_index ,recollection_floor_value )
                self.draw_dungeon (screen ,fontS )
                fade_len =8
                hold_len =8
                cycle_len =fade_len *2 +hold_len
                if self.tmr <=fade_len :
                    alpha =int (255 *(1 -self.tmr /fade_len ))
                elif self.tmr <=fade_len +hold_len :
                    alpha =0
                else:
                    alpha =int (255 *(self.tmr -(fade_len +hold_len ))/fade_len )
                alpha =max (0 ,min (255 ,alpha ))
                if alpha >0 :
                    fade =pygame .Surface (screen .get_size (),pygame .SRCALPHA )
                    fade .fill ((0 ,0 ,0 ,alpha ))
                    screen .blit (fade ,[0 ,0 ])
                if self.tmr >=cycle_len :
                    self.recollection_stage +=1
                    if self.recollection_stage >=10 :
                        self.boss_save_cmd =0
                        self.boss_save_input_lock = True
                        self.save_cmd =0
                        self.load_accept_lock = True
                        self.idx =86
                        self.tmr =0
                    else:
                        self.tmr =0

            elif self.idx ==86 :# クリア後セーブ確認
                screen .fill (BLACK )
                if self.boss_save_input_lock:
                    self.boss_save_choice_command (screen ,fontS ,key ,enable_input =False )
                    if not (key [K_UP ]or key [K_DOWN ]or key [K_LEFT ]or key [K_RIGHT ]or key [K_RETURN ]or key [K_a ]or key [K_b ]or key [K_BACKSPACE ]):
                        self.boss_save_input_lock = False
                else:
                    if self.boss_save_choice_command (screen ,fontS ,key )==True :
                        if self.boss_save_cmd ==0 :
                            self.load_accept_lock = True
                            self.idx =87
                            self.tmr =0
                        else :
                            self.idx =88
                            self.tmr =0

            elif self.idx ==87 :# クリア後セーブ先選択
                screen .fill (BLACK )
                self.draw_text (screen ,"セーブ先を選択してください",260 ,200 ,fontS ,WHITE )
                if self.save_command (screen ,fontS ,key )==True :
                    save_data =self.clear_save_payload if self.clear_save_payload else self.make_current_save_data ()
                    with open (self.path +"/savedata/data{}.json".format (self.save_cmd +1 ),"w")as f :
                        json .dump (save_data ,f )
                    se [9 ].play ()
                    self.floorlist [self.save_cmd ]=save_data ["floor"]
                    self.idx =88
                    self.tmr =0
                if key [K_b ]or key [K_BACKSPACE ]:
                    self.boss_save_input_lock = True
                    self.idx =86
                    self.tmr =0

            elif self.idx ==88 :# タイトル遷移待機
                screen .fill (BLACK )
                if self.tmr >=5 :
                    self.clear_save_payload = None
                    self.keep_title_bgm_on_next_title = True
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
                menu_label ="[M]enu "
                menu_x =view_left +view_w -int (view_w *0.1 )-fontS .size (menu_label )[0 ]
                self.draw_text (screen ,menu_label ,menu_x ,view_top +40 ,fontS ,WHITE )
                if self.dungeon [self.pl_y ][self.pl_x ]!=3 :
                    self.stair_prompted =False 
                elif self.is_stairs_locked ():
                    if not self.stair_prompted:
                        self.stair_prompted =True
                        self.init_item_event (kind ="locked_stairs",lines =["この階段は　まだ降りることができない"])
                        self.idx =131
                        self.tmr =0
                elif not self.stair_prompted:
                    self.stair_prompted =True 
                    self.stair_choice_cmd =0 
                    self.stair_choice_input_lock = True
                    self.idx =111 
                    self.tmr =0 
                if self.idx ==100 and accept and self.pl_d == 0:
                    front_tile =self.get_front_tile_id ()
                    tx =self.pl_x
                    ty =self.pl_y -1
                    if front_tile ==8:
                        if self.floor ==99:
                            self.init_floor99_item_event ()
                            self.idx =131
                            self.tmr =0
                        elif self.floor ==100:
                            if self.true_episode_heard:
                                self.init_item_event (kind="true_episode_event_replay", lines=TRUE_EPISODE_TALK)
                            else:
                                self.init_item_event (kind="true_episode_event", lines=FLOOR100_EVENT_UNREADABLE_TALK)
                            self.idx =131
                            self.tmr =0
                        else:
                            self.init_event_talk ()
                            self.idx =132
                            self.tmr =0
                    elif front_tile ==13:
                        if self.tutorial_enabled and self.floor ==1:
                            stage =self.tutorial_stage_for_wall ((tx ,ty ))
                            if stage >0 and self.init_tutorial_talk (stage ):
                                self.idx =132
                                self.tmr =0
                            else:
                                self.init_info_talk()
                                self.idx =132
                                self.tmr =0
                        else:
                            self.init_info_talk()
                            self.idx =132
                            self.tmr =0
                    elif front_tile ==7:
                        if self.tutorial_enabled and self.floor ==1:
                            stage =self.tutorial_stage_for_wall ((tx ,ty ))
                            if stage >0 and self.init_tutorial_talk (stage ):
                                self.idx =132
                                self.tmr =0
                        elif self.floor in ITEM_WALL_WEAPON_SET:
                            self.init_item_event (
                                kind ="weapon_set",
                                lines =ITEM_WALL_WEAPON_SET_TALK
                            )
                            self.idx =131
                            self.tmr =0
                        elif self.floor >= 91 and not self.all_cocoons_cleared():
                            self.init_item_event (kind="blocked", lines=["魔物を……滅ぼすのだ……"])
                            self.idx =131
                            self.tmr =0
                        else:
                            if 91 <= self.floor <= 100:
                                self.init_item_event (kind="item", reward_count=5)
                            elif self.floor %10 ==5:
                                self.init_item_event (kind="item_upgrade")
                            else:
                                self.init_item_event ()
                            self.idx =131
                            self.tmr =0
                if self.idx ==100 and accept and self.get_front_tile_id ()==12:
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

            elif self.idx ==110 :# 画面切り替え
                transition_black =self.boss_transition_mode
                transition_delta =self.floor_transition_delta if self.floor_transition_delta in (-1 ,1 )else 1
                if transition_black and self.tmr <=9 :
                    screen .fill (BLACK )
                else:
                    self.draw_dungeon (screen ,fontS )
                if self.floor_title_active and self.floor_title_pos :
                    disp_floor =self.floor
                    x ,y =self.floor_title_pos
                else:
                    if self.tmr <=5 :
                        disp_floor =self.floor +transition_delta
                    else:
                        disp_floor =self.floor
                    title_text =f"地下 {disp_floor}階"
                    screen_w ,screen_h =screen .get_size ()
                    x =screen_w //2 -font .size (title_text )[0 ]//2
                    y =screen_h //2 -font .get_height ()//2
                if 1 <=self.tmr and self.tmr <=5 :
                    alpha =int (255 *self.tmr /5 )
                    fade =pygame .Surface (screen .get_size (),pygame .SRCALPHA )
                    fade .fill ((0 ,0 ,0 ,alpha ))
                    screen .blit (fade ,[0 ,0 ])
                if self.tmr ==5 :
                    self.floor =max (1 ,self.floor +transition_delta )
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
                        d =self.make_current_save_data ()
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
                    self.boss_transition_mode = False
                    self.floor_transition_delta =1
                    self.idx =100 

            elif self.idx ==120 :# アイテム入手もしくはトラップ
                self.draw_dungeon (screen ,fontS )
                if self.tmr ==1 :
                    x = win_x + win_w//2 - 42
                    y = title_top +int (title_h *0.4 )
                dialog = pygame.Surface((400, 100), pygame.SRCALPHA)
                dialog.fill((0, 0, 0, 100))
                screen.blit(dialog, [x-100, y-40])
                item_text =self.item_popup_text if self.item_popup_text else TRE_NAME [self.treasure ]
                if not self.item_popup_text and self.treasure in (0 ,1 ,2 ,3 ,4 ,5 ,6 ,7 ,8 ,9 ):
                    item_text =f"{item_text} x {self.item_reward_count}"
                self.draw_text (screen ,item_text ,x ,y ,font ,WHITE )
                if self.tmr ==10 :
                    self.item_popup_text =""
                    self.idx =100 

            elif self.idx ==130 :# ボス会話
                self.draw_dungeon (screen ,fontS )
                layout =self.get_dialog_window_layout (screen ,dlg_y_ratio =520 /720 )
                self.draw_dialog_window (screen ,layout ,alpha =255 )
                visible ,self.boss_talk_index ,self.boss_talk_char_count ,self.boss_talk_last_tick =self.step_talk_text (
                    self.boss_talk_lines ,
                    self.boss_talk_index ,
                    self.boss_talk_char_count ,
                    self.boss_talk_last_tick
                )
                self.draw_dialog_text (screen ,fontS ,layout ,visible )
                self.draw_text (screen ,"[A]/[Enter]",layout ["prompt_x"],layout ["prompt_y"],fontS ,WHITE )
                if accept:
                    before_index =self.boss_talk_index
                    self.boss_talk_index ,self.boss_talk_char_count ,self.boss_talk_last_tick ,_ =self.advance_talk_text (
                        self.boss_talk_lines ,
                        self.boss_talk_index ,
                        self.boss_talk_char_count ,
                        self.boss_talk_last_tick
                    )
                    if (before_index !=self.boss_talk_index and
                        self.boss_talk_kind == "init" and self.floor ==40 and before_index ==0 ):
                        se [2 ].play ()
                        self.pl_life =self.pl_lifemax 
                    if self.boss_talk_index >=len (self.boss_talk_lines ):
                        self.truth_fragment_drop_battle =False
                        if self.boss_talk_kind == "end":
                            self.boss_save_cmd =0
                            self.boss_save_input_lock = True
                            self.save_from_boss = False
                            if 90 <self.floor <100 :
                                pygame .mixer .music .load (self.path +"/sound/bgm_9.wav")
                                pygame .mixer .music .play (-1 )
                            self.idx =112 
                        else:
                            self.idx =200 
                        self.tmr =0 

            elif self.idx ==133 :# ラスボス会話
                self.draw_dungeon (screen ,fontS )
                layout =self.get_dialog_window_layout (screen ,dlg_y_ratio =520 /720 )
                self.draw_dialog_window (screen ,layout ,alpha =255 )
                visible ,self.boss_talk_index ,self.boss_talk_char_count ,self.boss_talk_last_tick =self.step_talk_text (
                    self.boss_talk_lines ,
                    self.boss_talk_index ,
                    self.boss_talk_char_count ,
                    self.boss_talk_last_tick
                )
                self.draw_dialog_text (screen ,fontS ,layout ,visible )
                self.draw_text (screen ,"[A]/[Enter]",layout ["prompt_x"],layout ["prompt_y"],fontS ,WHITE )
                if accept:
                    self.boss_talk_index ,self.boss_talk_char_count ,self.boss_talk_last_tick ,_ =self.advance_talk_text (
                        self.boss_talk_lines ,
                        self.boss_talk_index ,
                        self.boss_talk_char_count ,
                        self.boss_talk_last_tick
                    )
                    if self.boss_talk_index >=len (self.boss_talk_lines ):
                        if self.last_talk_mode == 2:
                            self.idx =82 
                        else:
                            self.clear_save_payload =self.make_current_save_data ()
                            self.idx =84 
                        self.tmr =0 

            elif self.idx ==131 :# itemWallイベント
                self.draw_dungeon (screen ,fontS )
                layout =self.get_dialog_window_layout (screen ,dlg_y_ratio =525 /720 )
                view_left =layout ["view_left"]
                view_top =layout ["view_top"]
                view_w =layout ["view_w"]
                view_h =layout ["view_h"]
                scale_x =layout ["scale_x"]
                scale_y =layout ["scale_y"]
                text_x =layout ["text_x"]
                text_y =layout ["text_y"]
                line_h =layout ["line_h"]
                prompt_x =layout ["prompt_x"]
                prompt_y =layout ["prompt_y"]
                dialog_alpha = 255
                if self.item_event_phase == 1:
                    dialog_alpha = 100
                self.draw_dialog_window (screen ,layout ,alpha =dialog_alpha )
                if self.item_event_kind == "floor99_offer":
                    if self.item_event_phase in (0 ,2 ,3 ):
                        finished =self.step_item_event_talk (screen ,fontS ,layout ,accept )
                        if finished:
                            if self.item_event_phase ==0 :
                                self.item_event_phase =1
                            elif self.item_event_phase ==2 :
                                self.start_floor99_trial_battle ()
                            else:
                                self.idx =100
                                self.tmr =0
                    elif self.item_event_phase ==1 :
                        options =["はい","いいえ"]
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
                        if key [K_DOWN ]and self.item_choice <1 :
                            self.item_choice +=1
                        if accept:
                            if self.item_choice ==0 :
                                self.item_talk_lines =FLOOR99_TRIAL_ACCEPT_LINES
                                self.item_event_phase =2
                            else:
                                self.item_talk_lines =FLOOR99_TRIAL_DECLINE_LINES
                                self.item_event_phase =3
                            self.item_talk_index =0
                            self.item_talk_char_count =0
                            self.item_talk_last_tick =pygame .time .get_ticks ()

                elif self.item_event_kind in ("floor99_bonus","floor99_after"):
                    reward_entries =self.get_item_wall_rewards ()
                    if len (reward_entries )==0 :
                        self.idx =100
                        self.tmr =0
                    elif self.item_event_phase in (0 ,2 ,4 ):
                        finished =self.step_item_event_talk (screen ,fontS ,layout ,accept )
                        if finished:
                            if self.item_event_phase ==0 :
                                if self.item_event_kind =="floor99_after":
                                    self.truth_fragment =min (100 ,self.truth_fragment +self.floor99_trial_total )
                                    self.item_event_popup_timer =0
                                    self.item_event_phase =1
                                else:
                                    self.item_event_phase =3
                            elif self.item_event_phase ==2 :
                                self.item_event_phase =3
                            elif self.item_event_phase ==4 :
                                selected =self.item_reward if self.item_reward is not None else self.item_choice
                                selected =max (0 ,min (selected ,len (reward_entries )-1 ))
                                self.treasure =reward_entries [selected ]["treasure"]
                                self.dungeon [self.pl_y -1 ][self.pl_x ]=9
                                self.floor99_trial_battle_active =False
                                self.floor99_trial_post_pending =False
                                self.floor99_trial_missing =0
                                self.floor99_trial_total =0
                                self.idx =120
                                self.tmr =0
                            if self.item_event_phase in (3 ,4 ):
                                self.item_talk_index =0
                                self.item_talk_char_count =0
                                self.item_talk_last_tick =pygame .time .get_ticks ()
                        self.tmr =0
                    elif self.item_event_phase ==1 :
                        win_w =360
                        win_x =view_left +(view_w -win_w )//2
                        title_top =view_top
                        title_h =view_h
                        x = win_x + win_w//2 - 42
                        y = title_top +int (title_h *0.4 )
                        dialog = pygame.Surface((400, 100), pygame.SRCALPHA)
                        dialog.fill((0, 0, 0, 100))
                        screen.blit(dialog, [x-100, y-40])
                        item_text =f"{TRE_NAME [10 ]} x {self.floor99_trial_total}"
                        self.draw_text (screen ,item_text ,x ,y ,font ,WHITE )
                        self.item_event_popup_timer +=1
                        if self.item_event_popup_timer >=10 :
                            self.item_talk_lines =FLOOR99_AFTER_TRIAL_LINES [1 :]
                            self.item_talk_index =0
                            self.item_talk_char_count =0
                            self.item_talk_last_tick =pygame .time .get_ticks ()
                            self.item_event_phase =2
                    elif self.item_event_phase ==3 :
                        options =[entry ["label"]for entry in reward_entries ]
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
                        if key [K_DOWN ]and self.item_choice <len (options )-1 :
                            self.item_choice +=1
                        if accept and self.item_reward is None:
                            self.item_reward =self.item_choice
                        if self.item_reward is not None:
                            selected =max (0 ,min (self.item_reward ,len (reward_entries )-1 ))
                            attr =reward_entries [selected ]["attr"]
                            setattr (self ,attr ,getattr (self ,attr )+self.item_reward_count )
                            if self.item_event_kind =="floor99_after":
                                self.item_talk_lines =FLOOR99_AFTER_TRIAL_REWARD_LINE
                            else:
                                self.item_talk_lines =FLOOR99_COMPLETE_REWARD_LINE
                            self.item_talk_index =0
                            self.item_talk_char_count =0
                            self.item_talk_last_tick =pygame .time .get_ticks ()
                            self.item_event_phase =4

                elif self.item_event_kind == "true_episode_event":
                    if self.item_event_phase in (0, 2):
                        finished =self.step_item_event_talk (screen ,fontS ,layout ,accept )
                        if finished:
                            if self.item_event_phase == 0:
                                if self.truth_fragment >=100:
                                    self.item_talk_lines =FLOOR100_EVENT_USE_FRAGMENT_PROMPT
                                    self.item_talk_index =0
                                    self.item_talk_char_count =0
                                    self.item_talk_last_tick =pygame.time.get_ticks()
                                    self.item_choice =0
                                    self.item_event_phase =1
                                else:
                                    self.idx =100
                                    self.tmr =0
                            else:
                                self.true_episode_heard =True
                                self.idx =100
                                self.tmr =0
                    elif self.item_event_phase == 1:
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
                        options =["はい","いいえ"]
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
                        if key [K_DOWN ]and self.item_choice <1 :
                            self.item_choice +=1
                        if accept:
                            if self.item_choice ==0 :
                                self.item_talk_lines =TRUE_EPISODE_TALK
                                self.item_talk_index =0
                                self.item_talk_char_count =0
                                self.item_talk_last_tick =pygame.time.get_ticks()
                                self.item_event_phase =2
                            else:
                                self.idx =100
                                self.tmr =0
                elif self.item_event_kind in ("true_episode_event_replay","true_episode"):
                    finished =self.step_item_event_talk (screen ,fontS ,layout ,accept )
                    if finished:
                        self.true_episode_heard = True
                        self.idx =100
                        self.tmr =0
                elif self.item_event_kind in ("blocked","locked_stairs","floor99_need"):
                    finished =self.step_item_event_talk (screen ,fontS ,layout ,accept )
                    if finished:
                        self.idx =100
                        self.tmr =0
                elif self.item_event_kind == "weapon_set":
                    finished =self.step_item_event_talk (screen ,fontS ,layout ,accept )
                    if finished:
                        self.grant_weapon_set_for_floor (self.floor )
                        self.item_popup_text ="武具セット"
                        self.dungeon [self.pl_y -1 ][self.pl_x ]=9
                        self.idx =120
                        self.tmr =0
                elif self.item_event_kind == "fairy_upgrade":
                    if self.item_event_phase in (0, 2):
                        finished =self.step_item_event_talk (screen ,fontS ,layout ,accept )
                        if finished:
                            if self.item_event_phase == 0:
                                self.item_event_phase = 1
                            elif self.item_event_phase == 2:
                                self.idx =100
                                self.tmr =0
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
                                self.potion_lv +=1
                            if self.item_reward ==1 :
                                self.blazegem_lv +=1
                            if self.item_reward ==2 :
                                self.guard_lv +=1
                            self.item_talk_lines = ["神秘の力で　アイテムの効果が強まった。"]
                            self.item_talk_index = 0
                            self.item_talk_char_count = 0
                            self.item_talk_last_tick = pygame.time.get_ticks()
                            self.item_event_phase = 2
                elif self.item_event_kind in ("item","item_upgrade"):
                    reward_entries =self.get_item_wall_rewards ()
                    if len (reward_entries )==0 :
                        self.idx =100
                        self.tmr =0
                    elif self.item_event_phase in (0, 2):
                        finished =self.step_item_event_talk (screen ,fontS ,layout ,accept )
                        if finished:
                            if self.item_event_phase == 0:
                                self.item_event_phase = 1
                            elif self.item_event_phase == 2:
                                selected =self.item_reward if self.item_reward is not None else self.item_choice
                                selected =max (0 ,min (selected ,len (reward_entries )-1 ))
                                self.treasure =reward_entries [selected ]["treasure"]
                                self.dungeon [self.pl_y -1 ][self.pl_x ]=9
                                self.idx =120
                        self.tmr =0 
                    elif self.item_event_phase == 1:
                        options =[entry ["label"]for entry in reward_entries ]
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
                        if key [K_DOWN ]and self.item_choice <len (options )-1 :
                            self.item_choice +=1 
                        if accept and self.item_reward is None:
                            self.item_reward =self.item_choice
                        if self.item_reward is not None:
                            selected =max (0 ,min (self.item_reward ,len (reward_entries )-1 ))
                            attr =reward_entries [selected ]["attr"]
                            setattr (self ,attr ,getattr (self ,attr )+self.item_reward_count )
                            self.item_talk_lines = ["よろしい。そなたに差し上げよう。"]
                            self.item_talk_index = 0
                            self.item_talk_char_count = 0
                            self.item_talk_last_tick = pygame.time.get_ticks()
                            self.item_event_phase = 2

            elif self.idx ==132 :# eventWall会話
                self.draw_dungeon (screen ,fontS )
                layout =self.get_dialog_window_layout (screen ,dlg_y_ratio =520 /720 )
                self.draw_dialog_window (screen ,layout ,alpha =255 )
                visible ,self.event_talk_index ,self.event_talk_char_count ,self.event_talk_last_tick =self.step_talk_text (
                    self.event_talk_lines ,
                    self.event_talk_index ,
                    self.event_talk_char_count ,
                    self.event_talk_last_tick
                )
                self.draw_dialog_text (screen ,fontS ,layout ,visible )
                self.draw_text (screen ,"[A]/[Enter]",layout ["prompt_x"],layout ["prompt_y"],fontS ,WHITE )
                if accept:
                    self.event_talk_index ,self.event_talk_char_count ,self.event_talk_last_tick ,_ =self.advance_talk_text (
                        self.event_talk_lines ,
                        self.event_talk_index ,
                        self.event_talk_char_count ,
                        self.event_talk_last_tick
                    )
                    if self.event_talk_index >=len (self.event_talk_lines ):
                        if self.tutorial_enabled and self.tutorial_active_stage >0 :
                            self.complete_tutorial_talk ()
                        self.idx =100 
                        self.tmr =0 


            elif self.idx ==200 :# 戦闘開始
                if self.tmr ==1 :
                    self.start_battle_equip_session ()
                    self.growth_essence_drop_battle =False
                    self.powup =1
                    self.reset_enemy_battle_params ()
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
                        if self.emy_typ ==116 :
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
                    self.restore_battle_equip_session ()
                    self.btl_cmd =0 
                    self.set_message ("プレイヤーのターン")
                    self.guard_remain =max (self.guard_remain -1 ,0 )
                if self.battle_command (screen ,fontS ,key )==True :
                    if self.btl_cmd in (1 ,2 ,3 ,4 ,5 ) and self.powup >1 :
                        self.powup =1
                    if self.btl_cmd ==0 :#Attack
                        self.apply_auto_equip_for_battle_command (0 )
                        self.idx =220 
                        self.tmr =0 
                    if self.btl_cmd ==1 and self.pl_mag >99 :#Magic
                        self.apply_auto_equip_for_battle_command (1 )
                        self.idx =221 
                        self.tmr =0 
                    if self.btl_cmd ==2 and self.potion >0 :#Potion
                        self.apply_auto_equip_for_battle_command (2 )
                        self.idx =222 
                        self.tmr =0 
                    if self.btl_cmd ==3 and self.blazegem >0 :#Blaze gem
                        self.apply_auto_equip_for_battle_command (3 )
                        self.idx =223 
                        self.tmr =0 
                    if self.btl_cmd ==4 and self.guard >0 :#Guard
                        self.apply_auto_equip_for_battle_command (4 )
                        self.idx =224 
                        self.tmr =0 
                    if self.btl_cmd ==5 :#Run
                        self.idx =240 
                        self.tmr =0 
                    if self.btl_cmd ==6 :#Info
                        self.idx =225 
                        self.tmr =0 
                    if self.btl_cmd ==7 :#Equip
                        self.equip_back_lock =True
                        self.equip_accept_lock =True
                        self.idx =226
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
                    atk_effect =self.imgEffect [3 ]if self.get_active_weapon_level ("sword",0 )>0 else self.imgEffect [0 ]
                    screen .blit (atk_effect ,[eff_x ,eff_y ])
                if self.tmr ==3 :
                    dmg_add =0
                    if self.get_active_weapon_level ("sword",0 )>0 :
                        dmg_add = self.pl_sword [0 ]
                        if random .random ()>0.7 :
                            cri =1 
                            se [0 ].play ()
                            self.set_message ("　会心の一撃！")
                    dmg =self.pl_str +random .randint (0 ,9 )
                    dmg =dmg *(1 +0.01 *cri *self.pl_sword [0 ]) +dmg_add
                    dmg =dmg *self.powup
                    self.powup =1
                if self.tmr ==7 :
                    if self.emy_typ ==110 :
                        if random .random ()>0.7 :
                            self.set_message ("　攻撃は　防御された！")
                            se [11 ].play ()
                            dmg = dmg /2
                    if self.guard_remain >0 and self.emy_typ ==119 :
                        dmg =dmg *self.get_guard_damage_multiplier ("enemy")
                    dmg =max (1 +cri ,int (EMY_APRO [self.emy_typ ] * dmg /(2 *self.poison +1 )))
                    self.emy_blink =5 
                    self.set_message (f"　{dmg}　ダメージ！")
                if self.tmr ==11 :
                    self.emy_life =self.emy_life -dmg 
                    if self.emy_life <=0 :
                        self.emy_life =0 
                        self.idx =241 
                        self.tmr =0
                if self.tmr ==12 :
                    if self.emy_typ ==118 :
                        self.boss_mode = "normal"
                    if self.burn_turns >0 :
                        se [0 ].play ()
                        burn_dmg = 200 +random .randint (-30 ,30 )
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
                    active_ice_sword =self.get_active_weapon_level ("sword",1 )
                    if active_ice_sword >0 :
                        if random .random ()>0.95 -0.003 *active_ice_sword :
                            ice =1
                    dmg_add = 0 if active_ice_sword == 0 else self.pl_sword [1 ]
                    dmg =self.pl_str *1.5 +random .randint (0 ,9 )+ dmg_add
                    if self.guard_remain >0 and self.emy_typ ==119 :
                        dmg =dmg *self.get_guard_damage_multiplier ("enemy")
                    dmg =max (1 ,int(EMY_MPRO [self.emy_typ ] *dmg) )
                    if self.boss_mode == "ice":
                        dmg =0 
                blit_time =8
                if self.tmr <=blit_time :
                    magic_effect =self.imgEffect [4 ]if self.get_active_weapon_level ("sword",1 )>0 else self.imgEffect [1 ]
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
                    if self.emy_typ ==118 :
                        self.boss_mode = "ice"
                    if ice ==1 :
                        self.set_message ("　敵は　凍りついた！")
                    else :
                        self.tmr =self.tmr +3
                if self.tmr ==18 : # プレイヤーの毒処理
                    self.poison =max (self.poison -1 ,0 )
                    if ice*self.poison >0 :
                        self.set_message (f"　毒 {self.poison *40}ダメージ！")
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
                    elif self.emy_typ ==120 :
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
                    cure =min (500 +3 *self.get_active_weapon_level ("armor",2 )+5 *self.potion_lv,self.pl_lifemax -self.pl_life )
                    if self.emy_typ ==113 :
                        self.set_message ("　傷薬を無効化されている！")
                        cure =0 
                    else:
                        self.set_message ("　傷薬 +{}".format (cure ))
                        se [2 ].play ()
                if self.tmr ==6 :
                    self.pl_life =min (self.pl_lifemax ,self.pl_life +cure )
                    self.potion =self.potion -1 
                    active_potion_armor =self.get_active_weapon_level ("armor",2 )
                    if active_potion_armor >0 and random .random ()>0.7 :
                        self.powup =1.5 +0.01 *active_potion_armor
                        self.set_message ("　ちからをためた！")
                if self.tmr ==11 :
                    if self.emy_typ ==116 or self.emy_typ ==120 :
                        self.idx =232 
                        self.tmr =0 
                    elif self.emy_typ ==119 :
                        self.idx =233 
                        self.tmr =0 
                    else :
                        self.idx =230 
                        self.tmr =0 

            elif self.idx ==223 :# Blaze gem
                self.draw_battle (screen ,fontS )
                blaze_effect =self.imgEffect [5 ]if self.get_active_weapon_level ("sword",2 )>0 else self.imgEffect [2 ]
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
                    active_gem_sword =self.get_active_weapon_level ("sword", 2 )
                    dmg_add = 0 if active_gem_sword == 0 else self.pl_sword [2 ]*15
                    dmg =1000 +dmg_add +25 *self.blazegem_lv
                    dmg =max (1 ,int(EMY_BPRO [self.emy_typ ] *dmg) )
                    if self.burn_turns >0 or self.boss_mode == "fire":
                        dmg =0
                    if self.emy_typ ==113:
                        self.emy_skip_turn = True
                if self.tmr ==11 :
                    self.emy_blink =5 
                    self.set_message (f"　{dmg}　ダメージ！")
                if self.tmr ==17 :
                    self.emy_life =self.emy_life -dmg 
                    if self.emy_life <=0 :
                        self.emy_life =0 
                        self.idx =241 
                        self.tmr =0
                if self.tmr ==19 :
                    if self.emy_typ ==118 :
                        self.boss_mode = "fire"
                    if self.emy_typ ==112:
                        self.burn_turns =4 
                        self.set_message ("　敵は　火傷した！")
                    else:
                        active_bomb_sword =self.get_active_weapon_level ("sword",2 )
                        if active_bomb_sword >0 and random .random ()>0.7 :
                            self.emy_poison =1
                            if random .random ()<0.01 *active_bomb_sword :
                                self.emy_poison =2
                            self.set_message ("　敵は　毒をくらった！")
                        self.tmr =self.tmr +2
                if self.tmr ==22 :
                    if self.emy_typ ==114:
                        self.idx =231 
                        self.tmr =0 
                    elif self.emy_typ ==116 or self.emy_typ ==120 :
                        self.idx =232 
                        self.tmr =0 
                    elif self.emy_typ ==117 :
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
                name = f"{self.emy_name}  Lv.{self.emy_lev}"
                info = ENEMY_INFO.get(self.emy_typ, "info text")
                self.draw_text (screen ,name ,win_x + 30 ,win_y + 40 ,font ,WHITE )
                parts = info.split("\n")
                for i, part in enumerate(parts):
                    self.draw_text (screen ,part ,win_x + 30 ,win_y + 110 + i * 28 ,fontS ,WHITE )
                self.draw_text (screen ,"[B]/[Back] 戻る",win_x + 460 ,win_y + 380 ,fontS ,WHITE )
                if self.tmr >5 :
                    if key [K_b ] or key [K_BACKSPACE ]:
                        self.idx =210 
                        self.tmr =1 

            elif self.idx ==226 :# 戦闘中の装備変更
                self.draw_battle (screen ,fontS )
                self.dungeon_view_rect =self.btl_bg_rect if getattr (self ,"btl_bg_rect",None )else None
                self.handle_equip_screen_input (screen ,fontS ,key ,back_idx =210 ,back_tmr =2 ,set_menu_back =False )

            elif self.idx ==224 :#guard
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.guard_remain =3 
                    if random .random ()<0.01 *self.get_active_weapon_level ("shield",2 ):
                        self.guard_remain =4 
                    self.set_message ("　{}ターンの　守護を得た".format (self.guard_remain ))
                    se [8 ].play ()
                if self.tmr ==6 :
                    self.guard =self.guard -1 
                if self.tmr ==11 :
                    if self.emy_typ ==116 or self.emy_typ ==120 :
                        self.idx =232 
                        self.tmr =0 
                    elif self.emy_typ ==119 :
                        self.idx =234 
                        self.tmr =0 
                    else :
                        self.idx =230 
                        self.tmr =0 

            elif self.idx ==230 :# 敵のターン、敵の攻撃
                self.draw_battle (screen ,fontS )
                defence =self.get_equipped_defence ()
                if self.tmr ==1 :
                    self.set_message (f"{self.emy_name}のターン")
                    if self.emy_typ ==112 and self.burn_turns >0 :
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
                if self.tmr ==7 :
                    pro =0 
                    cou =0 
                    active_defence_shield =self.get_active_weapon_level ("shield",0 )
                    active_counter_shield =self.get_active_weapon_level ("shield",1 )
                    if active_defence_shield >0 :
                        if random .random ()>0.7 and self.emy_typ !=119 :
                            pro =0.3 +0.01 *active_defence_shield
                            self.set_message ("　盾で　防御した！")
                            se [11 ].play ()
                    if active_counter_shield >0 :
                        if random .random ()>0.65 :
                            cou =active_counter_shield
                    if self.emy_typ ==119 :
                        dmg_tmp =dmg 
                    dmg =self.emy_str +random .randint (0 ,9 )-defence
                    if self.emy_typ ==118 and self.boss_mode == "fire":
                        dmg =dmg *2
                    if self.guard_remain >0 : # 守護の効果処理
                        if self.emy_typ ==114 or self.emy_typ ==117 :
                            self.set_message ("　守護が破壊された！")
                            self.guard_remain =0 
                        else :
                            dmg =dmg *self.get_guard_damage_multiplier ()
                    if self.emy_typ ==2 or self.emy_typ ==110:
                        if random .random ()>0.7 :
                            se [0 ].play ()
                            self.set_message ("　会心の一撃！")
                            dmg =dmg *{2:1.5, 110:2, 118:2.5}[self.emy_typ]
                    if self.emy_typ ==117 : #インフェルノの火力が低下
                        self.inferno -= 15 + random .randint (0 ,10 )
                    if self.emy_typ ==120 : #ゆうしゃ２は生命が減るほど攻撃が強くなる
                        dmg = int(dmg * self.emy_lifemax/(1.3*self.emy_life))
                    dmg =max(int (dmg /(1 +pro ) /(2 *self.emy_poison +1 ))*self.emy_powup ,1 )
                    if self.emy_typ ==119 : #ゆうしゃ１はプレイヤーからの攻撃を模倣
                        dmg =dmg_tmp 
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
                        dmg =int (self.pl_str //20 +self.pl_str *cou *0.005 +random .randint (0 ,cou //5 ))
                        self.set_message (f"　{dmg}　カウンター！")
                        se [11 ].play ()
                        self.emy_life =self.emy_life -dmg 
                        if self.emy_life <=0 :
                            self.emy_life =0 
                            self.idx =241 
                            self.tmr =0 
                if self.tmr ==14 :
                    if self.emy_action (screen ):
                        self.tmr =self.tmr +3 
                if self.tmr ==18 :
                    self.resolve_enemy_poison_tick ()
                    self.apply_armor_effects ()
                    if self.emy_typ ==6 and self.idx ==236 :
                        self.tmr =0 
                if self.tmr ==22 :
                    self.idx =210 
                    self.tmr =0 


            elif self.idx ==231 :#destroy
                self.draw_battle (screen ,fontS )
                if self.tmr ==5 :
                    self.set_message (self.emy_name +"の デストロイ!")
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
                        self.set_message ("　マギアの　チャージ！")
                    elif self.madoka >=1000 :
                        self.set_message ("　敵の　マギア")
                        se [6 ].play ()
                        self.emy_step =30 
                if self.tmr ==9 :
                    if self.madoka <1000 :
                        dmg =0 
                        life_rate = self.emy_life /self.emy_lifemax
                        charge_magia = int (life_rate *{116:1000, 120:1500}[self.emy_typ] +100 )
                        self.set_message ("　マギア +{}".format (charge_magia ))
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
                    self.resolve_enemy_poison_tick ()
                    self.apply_armor_effects ()
                if self.tmr ==28 :
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
                    self.resolve_enemy_poison_tick ()
                    self.apply_armor_effects ()
                if self.tmr ==15 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==234 :#敵のガード
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.set_message ("　敵は　{}ターンの守護を得た".format (self.guard_remain ))
                    se [8 ].play ()
                if self.tmr ==6 :
                    self.resolve_enemy_poison_tick ()
                    self.apply_armor_effects ()
                if self.tmr ==10 :
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
                    self.floor99_trial_battle_active =False
                    self.floor99_trial_post_pending =False
                    self.floor99_trial_missing =0
                    self.floor99_trial_total =0
                    self.idx =244 


            elif self.idx ==237 :# 火炎攻撃
                self.draw_battle (screen ,fontS )
                defence =self.get_equipped_defence ()
                if self.tmr ==5 :
                    self.set_message (f"　{self.emy_name}の　攻撃！")
                    se [0 ].play ()
                    self.emy_step =30 
                if self.tmr ==9 :
                    dmg =max (self.emy_str +random .randint (0 ,9 )-defence ,1 )
                    dmg =dmg *3 
                    if self.guard_remain >0 :
                        dmg =int (dmg *self.get_guard_damage_multiplier ())
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
                    self.set_message (f"　敵の火傷 {recoil}　ダメージ！")
                    self.burn_turns -=1 
                    if self.emy_life <=0 :
                        self.emy_life =0 
                        self.idx =241 
                        self.tmr =0
                if self.tmr ==16 :
                    self.resolve_enemy_poison_tick ()
                    self.apply_armor_effects ()
                if self.tmr ==20 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==238 :# 豪炎
                self.draw_battle (screen ,fontS )
                if self.tmr ==5 :
                    self.set_message (f"　{self.emy_name}の　インフェルノ！")
                    se [1 ].play ()
                    self.emy_step =30 
                if self.tmr ==9 :
                    dmg =150 + self.inferno +random .randint (-30 ,30 )
                    self.set_message (f"　{dmg}　ダメージ！")
                    self.dmg_eff =6
                    self.emy_step =0
                    self.inferno = self.inferno + 35 + random.randint(0, 20)
                if self.tmr ==12 :
                    self.pl_life =self.pl_life -dmg 
                    if self.pl_life <=0 :
                        self.pl_life =0 
                        self.idx =242 
                        self.tmr =0 
                if self.tmr ==16 :
                    self.resolve_enemy_poison_tick ()
                    self.apply_armor_effects ()
                if self.tmr ==20 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==239 :# 毒攻撃
                self.draw_battle (screen ,fontS )
                defence =self.get_equipped_defence ()
                if self.tmr ==1 :
                    self.set_message (self.emy_name +"のターン")
                    pro =0 
                    cou =0 
                if self.tmr ==5 :
                    self.set_message (f"　{self.emy_name}の　攻撃！")
                    se [0 ].play ()
                    self.emy_step =30 
                if self.tmr ==8 :
                    active_defence_shield =self.get_active_weapon_level ("shield",0 )
                    active_counter_shield =self.get_active_weapon_level ("shield",1 )
                    if active_defence_shield >0 :
                        if random .random ()>0.7 and self.emy_typ !=119 :
                            pro =0.3 +0.01 *active_defence_shield
                            self.set_message ("　盾で　防御した！")
                            se [11 ].play ()
                    if active_counter_shield >0 :
                        if random .random ()>0.65 :
                            cou =active_counter_shield
                    dmg =max (self.emy_str +random .randint (0 ,9 )-defence ,1 )
                    dmg =int (dmg /(1 +pro ))* self.emy_powup
                    if self.guard_remain >0 :
                        dmg =int (dmg *self.get_guard_damage_multiplier ())
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
                        dmg =int (self.pl_str //10 +self.pl_str *cou *0.003 +random .randint (0 ,cou //5 ))
                        self.set_message (f"　{dmg}　のカウンター！")
                        se [11 ].play ()
                        self.emy_life =self.emy_life -dmg 
                        if self.emy_life <=0 :
                            self.emy_life =0 
                            self.idx =241 
                            self.tmr =0 
                if self.tmr ==14 :
                    self.poison =max (self.poison -1 ,0 )
                    self.poison = 3
                    self.set_message ("　毒を くらった！")
                    self.set_message (f"　毒 {self.poison *40}ダメージ！")
                    self.pl_life =self.pl_life -self.poison *40 
                    if self.pl_life <=0 :
                        self.pl_life =0 
                        self.idx =242 
                        self.tmr =0 
                if self.tmr ==18 :
                    self.resolve_enemy_poison_tick ()
                    self.apply_armor_effects ()
                if self.tmr ==22 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==240 :# 逃げられる？
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :self.set_message ("　逃走を試みた")
                if self.tmr ==10 :
                    if self.boss ==1 :
                        self.set_message ("　逃走に失敗した！")
                    elif random .randint (0 ,99 )<60 or self.emy_typ ==10:
                        self.floor99_trial_battle_active =False
                        self.floor99_trial_post_pending =False
                        self.floor99_trial_missing =0
                        self.floor99_trial_total =0
                        self.idx =244 
                    else :
                        self.set_message ("　逃走に失敗した！")
                if self.tmr ==15 :
                    if self.emy_typ ==119 :
                        self.idx =235 
                        self.tmr =0 
                    else :
                        self.idx =230
                        self.tmr =0 


            elif self.idx ==241 :# 勝利
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    if self.emy_typ ==119 :
                        self.reset_player_battle_params ()
                        self.reset_enemy_battle_params ()
                        self.idx =245 
                        self.tmr =0
                if self.tmr ==2 :
                    self.set_message ("{}を　たおした！".format (self.emy_name ))
                    self.growth_essence_drop_battle =(self.boss ==0 and random .random ()<0.05 )
                    if self.floor99_trial_battle_active:
                        self.growth_essence_drop_battle =False
                    pygame .mixer .music .stop ()
                    if self.boss ==1 :
                        se [7 ].play ()
                    else :
                        se [5 ].play ()
                    self.pl_exp =self.pl_exp +int (EMY_EXP [self.emy_typ ]*(1 +0.01 *(self.emy_lev -1))*(1 +0.01 *self.truth_fragment ))
                    self.add_pl_mag (EMY_MAG_GAIN [self.emy_typ ])
                    if self.tutorial_enabled and self.tutorial_pending_battle:
                        if self.tutorial_pending_battle =="room3":
                            self.tutorial_progress ["room3_enemy_defeated"]=True
                        elif self.tutorial_pending_battle =="room5":
                            self.tutorial_progress ["room5_enemy_defeated"]=True
                        self.tutorial_pending_battle =""
                        self.update_tutorial_floor_state ()
                if self.tmr ==15 :
                    if self.boss ==1 :
                        time .sleep (3 )
                    if self.pl_exp >=(self.pl_lifemax -250 )*20 :
                        self.idx =243 
                        self.tmr =0 
                    elif self.floor99_trial_battle_active:
                        self.floor99_trial_post_pending =True
                        self.idx =244
                        self.tmr =0
                    elif self.should_drop_iron_upgrade ():
                        self.idx =246
                        self.tmr =0
                    elif self.growth_essence_drop_battle:
                        self.idx =248
                        self.tmr =0
                    elif self.truth_fragment_drop_battle:
                        self.idx =247 
                        self.tmr =0 
                    else :
                        self.idx =244 

            elif self.idx ==242 :# 敗北
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.restore_battle_equip_session ()
                    pygame .mixer .music .stop ()
                    self.boss =0 
                    self.reset_player_battle_params ()
                    self.reset_enemy_battle_params ()
                    self.truth_fragment_drop_battle =False
                    self.growth_essence_drop_battle =False
                    self.floor99_trial_battle_active =False
                    self.floor99_trial_post_pending =False
                    self.floor99_trial_missing =0
                    self.floor99_trial_total =0
                    self.tutorial_pending_battle =""
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
                    self.refresh_pl_magmax ()
                    lif_p =random .randint (10 ,20 )
                    str_p =random .randint (6 ,8 )
                    mag_p =random .randint (15 ,30 )
                    self.pl_exp =self.pl_exp -(self.pl_lifemax -250 )*20 
                if self.tmr ==10 :
                    self.pl_lifemax =self.pl_lifemax +lif_p 
                    self.pl_life =self.pl_life +lif_p 
                    self.add_pl_mag (mag_p )
                    self.pl_str =self.pl_str +str_p 
                    self.set_message (f"　最大生命 +{lif_p}")
                    self.set_message (f"　攻撃 +{str_p}")
                    self.set_message (f"　魔力 +{mag_p}")
                    self.set_message (f"　魔力上限 +50")
                if self.tmr ==23 :
                    if self.pl_exp >(self.pl_lifemax -250 )*20 :
                        self.idx =243 
                        self.tmr =0 
                    elif self.floor99_trial_battle_active:
                        self.floor99_trial_post_pending =True
                        self.idx =244
                        self.tmr =0
                    else :
                        if self.should_drop_iron_upgrade ():
                            self.idx =246
                            self.tmr =0 
                        elif self.growth_essence_drop_battle:
                            self.idx =248
                            self.tmr =0 
                        elif self.truth_fragment_drop_battle:
                            self.idx =247 
                            self.tmr =0 
                        else :
                            self.idx =244 

            elif self.idx ==244 :# 戦闘終了
                self.restore_battle_equip_session ()
                self.reset_player_battle_params ()
                self.truth_fragment_drop_battle =False
                self.growth_essence_drop_battle =False
                self.reset_enemy_battle_params ()
                if self.tutorial_enabled and self.tutorial_pending_battle:
                    self.restore_tutorial_cocoon ()
                if self.emy_typ ==120 :
                    time .sleep (1 )
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
                    self.boss_transition_mode = True
                    self.init_boss_talk ("end")
                    self.idx =130 
                    self.tmr =0 
                else :
                    if self.floor99_trial_post_pending:
                        self.floor99_trial_post_pending =False
                        if self.floor99_trial_missing >1:
                            self.floor99_trial_missing -=1
                            self.start_floor99_trial_battle ()
                        else:
                            self.floor99_trial_missing =0
                            self.floor99_trial_battle_active =False
                            self.resume_dungeon_bgm ()
                            self.init_floor99_after_trial_event ()
                            self.idx =131
                            self.tmr =0
                    else:
                        self.resume_dungeon_bgm ()
                        self.floor99_trial_battle_active =False
                        self.idx =100 

            elif self.idx ==245 :#最終ボスの形態変化
                self.draw_battle (screen ,fontS )
                screen_w ,screen_h =screen .get_size ()
                bar_h =max (1 ,int (screen_h *320 /720 ))
                if 1 <=self.tmr <=5 :
                    pygame .draw .rect (screen ,BLACK ,[0 ,0 ,screen_w ,bar_h ])
                    pygame .draw .rect (screen ,BLACK ,[0 ,screen_h -bar_h ,screen_w ,bar_h ])
                if self.tmr ==1 :
                    self.init_message ()
                    self.change +=1 
                    self.init_bossbattle ()
                if 6 <=self.tmr and self.tmr <=9 :
                    pygame .draw .rect (screen ,BLACK ,[0 ,0 ,screen_w ,bar_h ])
                    pygame .draw .rect (screen ,BLACK ,[0 ,screen_h -bar_h ,screen_w ,bar_h ])
                if self.tmr ==10 :
                    self.idx =210 
                    self.tmr =0 

            elif self.idx ==246 :# 強化素材ドロップ（アイアンドウブ）
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.treasure =random .choice ([7 ,8 ,9 ])
                    self.set_message (f"{TRE_NAME [self.treasure ]}を　落とした")
                    self.se [9 ].play ()
                if self.tmr ==18 :
                    if self.treasure ==7 :
                        self.tool_sword_polish +=1
                    elif self.treasure ==8 :
                        self.tool_shield_harden +=1
                    else :
                        self.tool_armor_patch +=1
                    if self.growth_essence_drop_battle:
                        self.idx =248
                    elif self.truth_fragment_drop_battle:
                        self.idx =247
                    else:
                        self.idx =244
                    self.tmr =0

            elif self.idx ==247 :#しんじつのかけらドロップ
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.set_message ("しんじつのかけらを　落とした")
                    self.se [10 ].play ()
                if self.tmr ==18 :
                    self.truth_fragment =min (100 ,self.truth_fragment +1 )
                    self.truth_fragment_floors .add (self.floor )
                    self.truth_fragment_drop_battle =False
                    self.idx =244
                    self.tmr =0

            elif self.idx ==248 :#成長エキスドロップ
                self.draw_battle (screen ,fontS )
                if self.tmr ==1 :
                    self.set_message ("成長エキスを　落とした")
                    self.se [9 ].play ()
                if self.tmr ==18 :
                    self.tool_growth +=1
                    self.growth_essence_drop_battle =False
                    if self.truth_fragment_drop_battle:
                        self.idx =247
                    else:
                        self.idx =244
                    self.tmr =0

            pygame .display .update ()
            clock .tick (10 )
            self.prev_return = key [K_RETURN ]
            self.prev_a = key [K_a ]


# ゲームを起動するエントリ
def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
