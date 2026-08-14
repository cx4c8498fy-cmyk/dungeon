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
    para: object
    btl_bg: object
    enemy: object
    floors: list
    players: list
    effects: list


def load_images(base_path: str) -> ImageAssets:
    """Load image assets from disk."""
    img_title = pygame.image.load(base_path + "/image/title.png")
    wall_as = load_wall_variants(base_path, "wallA", 0)
    if not wall_as:
        wall_as = [pygame.image.load(base_path + "/image/wall/wallA0_0.png")]
    wall_bs = [make_wall_top(img) for img in wall_as]
    img_btl_bg = pygame.image.load(base_path + "/image/btlbg/btlbg0.png")
    img_enemy = pygame.image.load(base_path + "/image/enemy/enemy0_0.png")

    floor_variants = load_floor_variants(base_path, 0)
    base_floor = floor_variants[0] if floor_variants else pygame.image.load(base_path + "/image/floor/floor0.png")
    img_floors = [
        base_floor,
        pygame.image.load(base_path + "/image/tbox.png"),
        pygame.image.load(base_path + "/image/cocoon/cocoon0.png"),
        pygame.image.load(base_path + "/image/stairs.png"),
        pygame.image.load(base_path + "/image/wbox.png"),
        pygame.image.load(base_path + "/image/wall_item.png"),
    ]
    img_players = [
        pygame.image.load(base_path + f"/image/mychr/mychr_{i//3}_{i%3}_0.png")
        for i in range(12)
    ]
    img_players.append(pygame.image.load(base_path + "/image/mychr/mychr_4_0_0.png"))
    img_effects = [
        pygame.image.load(base_path + "/image/effect/effect_a_0.png"),
        pygame.image.load(base_path + "/image/effect/effect_b_0.png"),
        pygame.image.load(base_path + "/image/effect/effect_c_0.png"),
        pygame.image.load(base_path + "/image/effect/effect_a_1.png"),
        pygame.image.load(base_path + "/image/effect/effect_b_1.png"),
        pygame.image.load(base_path + "/image/effect/effect_c_1.png"),
    ]

    return ImageAssets(
        title=img_title,
        wallAs=wall_as,
        wallBs=wall_bs,
        para=None,
        btl_bg=img_btl_bg,
        enemy=img_enemy,
        floors=img_floors,
        players=img_players,
        effects=img_effects,
    )


def load_sounds(base_path: str) -> list:
    """Load sound effects and jingles in the existing order."""
    return [
        pygame.mixer.Sound(base_path + "/sound/ohd_se_attack.wav"),
        pygame.mixer.Sound(base_path + "/sound/se_blaze.wav"),
        pygame.mixer.Sound(base_path + "/sound/ohd_se_potion.wav"),
        pygame.mixer.Sound(base_path + "/sound/ohd_jin_gameover.wav"),
        pygame.mixer.Sound(base_path + "/sound/jin_levup.wav"),
        pygame.mixer.Sound(base_path + "/sound/jin_win.wav"),
        pygame.mixer.Sound(base_path + "/sound/se_magic.wav"),
        pygame.mixer.Sound(base_path + "/sound/jin_bosswin.wav"),
        pygame.mixer.Sound(base_path + "/sound/se_guard.wav"),
        pygame.mixer.Sound(base_path + "/sound/se_magup.wav"),
        pygame.mixer.Sound(base_path + "/sound/se_kakera.wav"),
        pygame.mixer.Sound(base_path + "/sound/se_defence.wav"),
        pygame.mixer.Sound(base_path + "/sound/se_powup.wav"),
    ]


def load_floor_variants(base_path: str, floor_index: int) -> list:
    """Load floor tile variants like floor0_0.png, floor0_1.png, ..."""
    pattern = os.path.join(base_path, "image", "floor", f"floor{floor_index}_*.png")
    paths = sorted(glob.glob(pattern))
    if paths:
        return [pygame.image.load(path) for path in paths]
    fallback = os.path.join(base_path, "image", "floor", f"floor{floor_index}.png")
    if os.path.exists(fallback):
        return [pygame.image.load(fallback)]
    return []


def load_wall_variants(base_path: str, wall_prefix: str, wall_set: int) -> list:
    """Load wall variants like wallA1_0.png, wallA1_1.png, ..."""
    pattern = os.path.join(base_path, "image", "wall", f"{wall_prefix}{wall_set}_*.png")
    paths = sorted(
        path for path in glob.glob(pattern)
        if os.path.splitext(os.path.basename(path))[0].rsplit("_", 1)[-1].isdigit()
    )
    if paths:
        return [pygame.image.load(path) for path in paths]
    fallback = os.path.join(base_path, "image", "wall", f"{wall_prefix}{wall_set}.png")
    if os.path.exists(fallback):
        return [pygame.image.load(fallback)]
    return []


def make_wall_top(wall_a_img: pygame.Surface) -> pygame.Surface:
    """Create wallB-like image by cropping top 40px from a wallA image."""
    width = wall_a_img.get_width()
    height = max(1, min(40, wall_a_img.get_height()))
    top = pygame.Surface((width, height), pygame.SRCALPHA)
    top.blit(wall_a_img, (0, 0), pygame.Rect(0, 0, width, height))
    return top
