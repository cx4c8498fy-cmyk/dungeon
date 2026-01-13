# coding: utf-8

from dataclasses import dataclass
import os
import glob
import pygame

@dataclass
class ImageAssets:
    title: object
    wallAs: list
    wallBs: list
    dark: object
    para: object
    btl_bg: object
    enemy: object
    items: list
    floors: list
    players: list
    effects: list


def load_images(base_path: str) -> ImageAssets:
    """Load image assets from disk."""
    img_title = pygame.image.load(base_path + "/image/title.png")
    wall_as = load_wall_variants(base_path, "wallA", 0)
    wall_bs = load_wall_variants(base_path, "wallB", 0)
    if not wall_as:
        wall_as = [pygame.image.load(base_path + "/image/wall.png")]
    if not wall_bs:
        wall_bs = [pygame.image.load(base_path + "/image/wall2.png")]
    img_dark = pygame.image.load(base_path + "/image/dark.png")
    img_btl_bg = pygame.image.load(base_path + "/image/btlbg0.png")
    img_enemy = pygame.image.load(base_path + "/image/enemy0_0.png")

    img_items = [
        pygame.image.load(base_path + "/image/potion.png"),
        pygame.image.load(base_path + "/image/blaze_gem.png"),
        pygame.image.load(base_path + "/image/guard.png"),
        pygame.image.load(base_path + "/image/apple.png"),
        pygame.image.load(base_path + "/image/magic_apple.png"),
        pygame.image.load(base_path + "/image/mag_pot.png"),
    ]



    floor_variants = load_floor_variants(base_path, 0)
    base_floor = floor_variants[0] if floor_variants else pygame.image.load(base_path + "/image/floor0.png")
    img_floors = [
        base_floor,
        pygame.image.load(base_path + "/image/tbox.png"),
        pygame.image.load(base_path + "/image/cocoon0.png"),
        pygame.image.load(base_path + "/image/stairs.png"),
        pygame.image.load(base_path + "/image/wbox.png"),
        pygame.image.load(base_path + "/image/floor_dmg.png"),
        pygame.image.load(base_path + "/image/floor_cure.png"),
        pygame.image.load(base_path + "/image/stairs.png"),
    ]
    img_players = [
        pygame.image.load(base_path + "/image/mychr0.png"),
        pygame.image.load(base_path + "/image/mychr1.png"),
        pygame.image.load(base_path + "/image/mychr2.png"),
        pygame.image.load(base_path + "/image/mychr3.png"),
        pygame.image.load(base_path + "/image/mychr4.png"),
        pygame.image.load(base_path + "/image/mychr5.png"),
        pygame.image.load(base_path + "/image/mychr6.png"),
        pygame.image.load(base_path + "/image/mychr7.png"),
        pygame.image.load(base_path + "/image/mychr8.png"),
    ]
    img_effects = [
        pygame.image.load(base_path + "/image/effect_a.png"),
        pygame.image.load(base_path + "/image/effect_b.png"),
        pygame.image.load(base_path + "/image/effect_c.png"),
    ]

    return ImageAssets(
        title=img_title,
        wallAs=wall_as,
        wallBs=wall_bs,
        dark=img_dark,
        para=None,
        btl_bg=img_btl_bg,
        enemy=img_enemy,
        items=img_items,
        floors=img_floors,
        players=img_players,
        effects=img_effects,
    )


def load_sounds(base_path: str) -> list:
    """Load sound effects and jingles in the existing order."""
    return [
        pygame.mixer.Sound(base_path + "/sound/ohd_se_attack.wav"),
        pygame.mixer.Sound(base_path + "/sound/ohd_se_blaze.wav"),
        pygame.mixer.Sound(base_path + "/sound/ohd_se_potion.wav"),
        pygame.mixer.Sound(base_path + "/sound/ohd_jin_gameover.wav"),
        pygame.mixer.Sound(base_path + "/sound/jin_levup.wav"),
        pygame.mixer.Sound(base_path + "/sound/jin_win.wav"),
        pygame.mixer.Sound(base_path + "/sound/se_magic.wav"),
        pygame.mixer.Sound(base_path + "/sound/jin_bosswin.wav"),
        pygame.mixer.Sound(base_path + "/sound/se_guard.wav"),
        pygame.mixer.Sound(base_path + "/sound/se_magup.wav"),
    ]


def load_floor_variants(base_path: str, floor_index: int) -> list:
    """Load floor tile variants like floor0_0.png, floor0_1.png, ..."""
    pattern = os.path.join(base_path, "image", f"floor{floor_index}_*.png")
    paths = sorted(glob.glob(pattern))
    if paths:
        return [pygame.image.load(path) for path in paths]
    fallback = os.path.join(base_path, "image", f"floor{floor_index}.png")
    if os.path.exists(fallback):
        return [pygame.image.load(fallback)]
    return []


def load_wall_variants(base_path: str, wall_prefix: str, wall_set: int) -> list:
    """Load wall variants like wallA1_0.png, wallA1_1.png, ..."""
    pattern = os.path.join(base_path, "image", f"{wall_prefix}{wall_set}_*.png")
    paths = sorted(glob.glob(pattern))
    if paths:
        return [pygame.image.load(path) for path in paths]
    fallback = os.path.join(base_path, "image", f"{wall_prefix}{wall_set}.png")
    if os.path.exists(fallback):
        return [pygame.image.load(fallback)]
    return []
