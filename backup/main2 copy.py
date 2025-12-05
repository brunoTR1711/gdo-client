import sys
import math
import random
import pygame
import tkinter as tk
from tkinter import filedialog

# Dimensões base do layout original
BASE_WIDTH = 1920
BASE_HEIGHT = 1080
START_WIDTH = 800
START_HEIGHT = 600
FPS = 60

pygame.init()
pygame.display.set_caption("GDO - Coluna de Atributos")

# Janela real (redimensionável) e canvas base para manter proporção
WINDOW = pygame.display.set_mode((START_WIDTH, START_HEIGHT), pygame.RESIZABLE)
CANVAS = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
CLOCK = pygame.time.Clock()

# Cores
BLACK = (0, 0, 0)
GRAY_30 = (45, 45, 45)
GRAY_50 = (90, 90, 90)
GRAY_70 = (140, 140, 140)
WHITE = (255, 255, 255)
PURPLE = (150, 60, 200)
ORANGE = (240, 140, 0)
GREEN = (0, 180, 0)
RED = (210, 40, 40)

# Fontes
FONTS = {
    "xs": pygame.font.SysFont("arial", 12),
    "sm": pygame.font.SysFont("arial", 14),
    "sm_b": pygame.font.SysFont("arial", 14, bold=True),
    "md": pygame.font.SysFont("arial", 18, bold=True),
    "lg": pygame.font.SysFont("arial", 28, bold=True),
    "xl": pygame.font.SysFont("arial", 52, bold=True),
}

# Estado dos atributos (valor e retângulos dos botões serão preenchidos a cada draw)
ATTRIBUTES = [
    {"code": "VIG", "name": "Vigor", "value": 0, "minus_rect": None, "plus_rect": None, "value_rect": None},
    {"code": "FOR", "name": "Força", "value": 0, "minus_rect": None, "plus_rect": None, "value_rect": None},
    {"code": "AGI", "name": "Agilidade", "value": 0, "minus_rect": None, "plus_rect": None, "value_rect": None},
    {"code": "INT", "name": "Intelecto", "value": 0, "minus_rect": None, "plus_rect": None, "value_rect": None},
    {"code": "PRE", "name": "Presença", "value": 0, "minus_rect": None, "plus_rect": None, "value_rect": None},
]

# Vida: trilhas de tolerância interativas
LIFE_TRACKS = ["LEVE", "FERIDO", "MACHUCADO", "MORRENDO"]
LIFE_MARKS = {k: [] for k in LIFE_TRACKS}
LIFE_RECTS = []  # (track_key, idx, rect)
# Resistência à morte: 3 sucessos, 3 falhas
DEATH_SAVES = {"success": [False, False, False], "fail": [False, False, False]}
DEATH_RECTS = []  # (type, idx, rect)

# Sanidade: trilhas semelhantes às de vida
SAN_TRACKS = ["ESTÁVEL", "INSTÁVEL", "PERTURBADO", "ENLOUQUECENDO"]
SAN_MARKS = {k: [] for k in SAN_TRACKS}
SAN_RECTS = []  # (track_key, idx, rect)
SAN_SAVES = {"success": [False, False, False], "fail": [False, False, False]}
SAN_SAVE_RECTS = []  # (type, idx, rect)

# Esforço
EFFORT_STATE = {
    "current": 0,
    "total": 0,
    "bonus": 0,
    "manual_total": False,
    "focus": None,  # "current" ou "total"
    "buffers": {"current": "0", "total": "0", "bonus": "0"},
    "btn_rects": [],
    "input_rects": {},
}

NOTE_STATE = {
    "title": "",
    "subject": "",
    "body": "",
    "focus": None,  # "title", "subject", "body"
    "scroll": 0,
    "max_scroll": 0,
    "rects": {},
    "send_rect": None,
    "cursor": {"title": 0, "subject": 0, "body": 0},
}

SKILLS = [
    # Físicas
    {"name": "Acrobacia", "attr": "AGI", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Furtividade", "attr": "AGI", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Iniciativa", "attr": "AGI", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Reflexo", "attr": "AGI", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Atletismo", "attr": "FOR", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Lutar", "attr": "FOR", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Pontaria", "attr": "AGI", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Fortitude", "attr": "VIG", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Pilotagem*", "attr": "AGI", "cat": "FISICA", "requires_training": True, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Crime*", "attr": "AGI", "cat": "FISICA", "requires_training": True, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Esquiva*", "attr": "AGI", "cat": "FISICA", "requires_training": True, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Contra-Ataque*", "attr": "FOR", "cat": "FISICA", "requires_training": True, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Bloqueio*", "attr": "VIG", "cat": "FISICA", "requires_training": True, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    # Intelecto
    {"name": "Atualidade", "attr": "INT", "cat": "INTELECTO", "requires_training": False, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Sobrevivencia", "attr": "INT", "cat": "INTELECTO", "requires_training": False, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Intuicao", "attr": "INT", "cat": "INTELECTO", "requires_training": False, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Investigacao", "attr": "INT", "cat": "INTELECTO", "requires_training": False, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Medicina*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Ocultismo*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Profissao*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Ciencia*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Tatica*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Tecnologia*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    # Sociais
    {"name": "Adestramento", "attr": "PRE", "cat": "SOCIAL", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Vontade", "attr": "PRE", "cat": "SOCIAL", "requires_training": False, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Enganacao", "attr": "PRE", "cat": "SOCIAL", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Intimidacao", "attr": "PRE", "cat": "SOCIAL", "requires_training": False, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Percepcao", "attr": "PRE", "cat": "SOCIAL", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Diplomacia*", "attr": "PRE", "cat": "SOCIAL", "requires_training": True, "bonus": 1, "bonus_choice": None, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Artes*", "attr": "PRE", "cat": "SOCIAL", "requires_training": True, "bonus": 2, "bonus_choice": None, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Religiao*", "attr": "PRE", "cat": "SOCIAL", "requires_training": True, "bonus": 2, "bonus_choice": None, "trained": False, "rect": None, "choice_rects": None},
]

DICE_STATE = {
    "current": None,
    "history": [],
    "rolling": False,
    "roll_start": 0,
    "pending": None,
    "display_dice": [1, 1, 1],
    "last_anim": 0,
    "anim_config": {"count": 3, "sides": 6},
}

UI_STATE = {"hover_attr": None, "hover_skill": None}

INVENTORY_STATE = {
    "limit_values": [0, 0, 0, 0, 0],
    "total_values": [0, 0, 0, 0, 0],
    "limit_rects": [],
    "total_rects": [],
    "dropdown": None,  # {"type": "limit", "index": int, "options": [rects]}
    "weight_bonus": 0,
    "current_weight": 0,
    "tabs": ["GERAL", "INVENTARIO", "HABILIDADES", "ANOTACOES"],
    "active_tab": "INVENTARIO",
    "tab_rects": [],
    "show_form": False,
    "form": {
        "image_path": "",
        "image_surface": None,
        "name": "",
        "category": "",
        "space": "",
        "tipo": "",
        "alcance": "",
        "empunhadura": "",
        "dano": "",
        "localizacao": "",
        "descricao": "",
        "info1": "",
        "info2": "",
        "rects": {},
        "focus": None,
    },
    "form_dropdown": None,
    "form_buttons": {},
    "items": [],
    "item_rows": [],
    "filter_buttons": [],
    "category_filter": None,
    "view_item_index": None,
    "summary_buttons": {},
    "editing_index": None,
    "form_error": "",
}

def send_note_payload():
    """Prepara payload simples para futura integração com o menu de anotações/email."""
    return {
        "title": NOTE_STATE["title"].strip(),
        "subject": NOTE_STATE["subject"].strip(),
        "body": NOTE_STATE["body"].strip(),
    }


def note_move_cursor(field, direction):
    """Move cursor in note fields; supports left/right/home/end and up/down for body."""
    text = NOTE_STATE[field]
    cur = NOTE_STATE["cursor"].get(field, 0)
    if direction == "left":
        cur = max(0, cur - 1)
    elif direction == "right":
        cur = min(len(text), cur + 1)
    elif direction == "home":
        # go to start of line
        prev_newline = text.rfind("\n", 0, cur)
        cur = 0 if prev_newline == -1 else prev_newline + 1
    elif direction == "end":
        next_newline = text.find("\n", cur)
        cur = len(text) if next_newline == -1 else next_newline
    elif direction in ("up", "down") and field == "body":
        # navigate lines ignoring wrapping; use logical lines
        lines = text.split("\n")
        # find current line and col
        idx = cur
        line_start = 0
        line_idx = 0
        for i, ln in enumerate(lines):
            line_end = line_start + len(ln)
            if idx <= line_end:
                line_idx = i
                col = idx - line_start
                break
            line_start = line_end + 1
        target = line_idx - 1 if direction == "up" else line_idx + 1
        if 0 <= target < len(lines):
            target_line_start = sum(len(l) + 1 for l in lines[:target])
            cur = min(target_line_start + col, target_line_start + len(lines[target]))
    NOTE_STATE["cursor"][field] = cur


def note_insert_text(field, text):
    cur = NOTE_STATE["cursor"].get(field, 0)
    current = NOTE_STATE[field]
    NOTE_STATE[field] = current[:cur] + text + current[cur:]
    NOTE_STATE["cursor"][field] = cur + len(text)


def note_backspace(field):
    cur = NOTE_STATE["cursor"].get(field, 0)
    if cur == 0:
        return
    current = NOTE_STATE[field]
    NOTE_STATE[field] = current[:cur - 1] + current[cur:]
    NOTE_STATE["cursor"][field] = cur - 1


def note_delete(field):
    cur = NOTE_STATE["cursor"].get(field, 0)
    current = NOTE_STATE[field]
    if cur >= len(current):
        return
    NOTE_STATE[field] = current[:cur] + current[cur + 1:]


def draw_text(surface, text, font, color, pos, center=False):
    render = font.render(text, True, color)
    rect = render.get_rect(topleft=pos)
    if center:
        rect = render.get_rect(center=pos)
    surface.blit(render, rect)
    return rect


def window_to_canvas(pos, scale, offset):
    """Converte coordenadas da janela para a base; retorna None se fora da área válida."""
    x = (pos[0] - offset[0]) / scale
    y = (pos[1] - offset[1]) / scale
    if 0 <= x <= BASE_WIDTH and 0 <= y <= BASE_HEIGHT:
        return (x, y)
    return None


def wrap_text(text, font, max_width):
    lines = []
    line_starts = []
    for paragraph in text.split("\n"):
        if paragraph == "":
            lines.append("")
            line_starts.append(len("\n".join(lines[:-1])) + (1 if lines[:-1] else 0))
            continue
        current = ""
        start_idx = len("\n".join(lines)) + (1 if lines else 0)
        for word in paragraph.split(" "):
            candidate = (current + " " + word).strip() if current else word
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                    line_starts.append(start_idx)
                    start_idx += len(current) + 1  # space
                current = word
        lines.append(current)
        line_starts.append(start_idx)
    return lines, line_starts


FORM_DROPDOWN_OPTIONS = {
    "category": ["Armas", "municao", "Protecao", "Magikos", "Coletaveis", "Itens chave", "componentes"],
    "space": ["0", "1", "2", "3", "4", "5"],
    "tipo": ["1", "2", "3", "4", "5"],
    "alcance": ["---", "1m", "3m", "6m", "9m", "12m"],
    "empunhadura": ["---", "leve", "uma mao", "duas maos"],
    "dano": ["1D4", "1D6", "1D8", "1D10", "1D12", "1D20"],
}
FORM_TEXT_FIELDS = {"name", "localizacao", "descricao", "info1", "info2"}
FORM_MULTILINE_FIELDS = {"descricao", "info1", "info2"}
FORM_BOLD_FIELDS = {"info1", "info2"}


def form_insert_text(field, text):
    buf = INVENTORY_STATE["form"].get(field, "")
    INVENTORY_STATE["form"][field] = buf + text


def form_backspace(field):
    buf = INVENTORY_STATE["form"].get(field, "")
    if buf:
        INVENTORY_STATE["form"][field] = buf[:-1]


def reset_inventory_form():
    form = INVENTORY_STATE["form"]
    for key in ["name", "category", "space", "tipo", "alcance", "empunhadura", "dano", "localizacao", "descricao", "info1", "info2"]:
        form[key] = ""
    form["image_path"] = ""
    form["image_surface"] = None
    form["rects"] = {}
    form["focus"] = None
    INVENTORY_STATE["form_dropdown"] = None
    INVENTORY_STATE["form_error"] = ""
    INVENTORY_STATE["editing_index"] = None


def select_inventory_image():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    file_path = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.bmp")],
    )
    root.destroy()
    if not file_path:
        return "", None
    try:
        surface = pygame.image.load(file_path).convert_alpha()
    except pygame.error:
        return "", None
    return file_path, surface


def form_set_focus(field):
    INVENTORY_STATE["form"]["focus"] = field


def form_clear_dropdown():
    INVENTORY_STATE["form_dropdown"] = None


def snapshot_inventory_form():
    form = INVENTORY_STATE["form"]
    fields = ["name", "category", "space", "tipo", "alcance", "empunhadura", "dano", "localizacao", "descricao", "info1", "info2"]
    data = {}
    for field in fields:
        value = form.get(field, "")
        if isinstance(value, str):
            data[field] = value.strip() if field in {"name", "category", "space", "alcance", "empunhadura", "dano", "localizacao"} else value
        else:
            data[field] = value
    image_surface = form.get("image_surface")
    data["image_surface"] = image_surface.copy() if image_surface else None
    data["image_path"] = form.get("image_path", "")
    return data


def filter_inventory_items():
    """Retorna lista de tuplas (index_original, item) respeitando o filtro de categoria."""
    items = INVENTORY_STATE.get("items", [])
    category = INVENTORY_STATE.get("category_filter")
    if not category:
        return list(enumerate(items))
    target = category.strip().lower()
    filtered = []
    for idx, item in enumerate(items):
        item_cat = (item.get("category") or "").strip().lower()
        if item_cat == target:
            filtered.append((idx, item))
    return filtered


def add_inventory_item_from_form():
    item = snapshot_inventory_form()
    if not item.get("name"):
        item["name"] = "Item sem nome"
    space_val = safe_space_value(item.get("space"))
    raw_tipo = item.get("tipo")
    tipo_val = safe_type_value(raw_tipo) if str(raw_tipo).strip() else None
    type_idx = (tipo_val - 1) if tipo_val else None
    edit_index = INVENTORY_STATE.get("editing_index")
    base_weight = calc_inventory_weight(exclude_index=edit_index)
    limit = get_inventory_weight_limit()
    if space_val > 0 and base_weight + space_val > limit:
        INVENTORY_STATE["form_error"] = "Limite de peso atingido"
        return
    if tipo_val:
        type_counts = count_items_by_type(exclude_index=edit_index)
        type_limit = INVENTORY_STATE["limit_values"][type_idx]
        if type_limit > 0 and type_counts[type_idx] + 1 > type_limit:
            INVENTORY_STATE["form_error"] = f"Limite do tipo {tipo_val} atingido"
            return
    INVENTORY_STATE["form_error"] = ""
    items = INVENTORY_STATE.setdefault("items", [])
    if edit_index is not None and 0 <= edit_index < len(items):
        items[edit_index] = item
    else:
        items.append(item)
    refresh_inventory_totals()
    reset_inventory_form()
    INVENTORY_STATE["show_form"] = False
    INVENTORY_STATE["view_item_index"] = None


def cancel_inventory_form():
    reset_inventory_form()
    INVENTORY_STATE["show_form"] = False
    INVENTORY_STATE["view_item_index"] = None
    INVENTORY_STATE["editing_index"] = None


def close_inventory_summary():
    INVENTORY_STATE["view_item_index"] = None
    INVENTORY_STATE["summary_buttons"] = {}
    INVENTORY_STATE["editing_index"] = None


def remove_inventory_item(index):
    items = INVENTORY_STATE.setdefault("items", [])
    if 0 <= index < len(items):
        items.pop(index)
    refresh_inventory_totals()
    close_inventory_summary()


def roll_3d6():
    """Retorna lista com 3 resultados de d6."""
    return [random.randint(1, 6) for _ in range(3)]


def build_roll_entry(label, attr_code, attr_value, skill_bonus, roll_type, skill_name=None, trained=False):
    dice = roll_custom_dice(3, 6)
    total = sum(dice) + attr_value + skill_bonus
    return {
        "label": label,
        "roll_type": roll_type,
        "skill_name": skill_name or label,
        "attr_code": attr_code,
        "attr_value": attr_value,
        "skill_bonus": skill_bonus,
        "trained": trained,
        "dice": dice,
        "total": total,
        "dice_config": {"count": 3, "sides": 6},
    }


def record_roll(entry):
    """Move resultado atual para historico e guarda a nova rolagem."""
    if DICE_STATE["current"]:
        DICE_STATE["history"].insert(0, DICE_STATE["current"])
        DICE_STATE["history"] = DICE_STATE["history"][:4]
    DICE_STATE["current"] = entry


def roll_attribute(attr):
    entry = build_roll_entry(
        label=attr["name"],
        attr_code=attr["code"],
        attr_value=attr["value"],
        skill_bonus=0,
        roll_type="attribute",
        skill_name=attr["name"],
        trained=False,
    )
    start_roll(entry)


def roll_skill(skill):
    # Skills marcadas com * exigem treino para teste.
    if skill.get("requires_training") and not skill.get("trained"):
        return
    attr_value = get_attr_value(skill["attr"])
    skill_bonus = skill["bonus"] if skill["trained"] else 0
    entry = build_roll_entry(
        label=skill["name"],
        attr_code=skill["attr"],
        attr_value=attr_value,
        skill_bonus=skill_bonus,
        roll_type="skill",
        skill_name=skill["name"],
        trained=skill["trained"],
    )
    start_roll(entry)


def roll_item_damage(index):
    items = INVENTORY_STATE.get("items", [])
    if index is None or not (0 <= index < len(items)):
        return
    item = items[index]
    dmg_info = parse_damage_die(item.get("dano"))
    if not dmg_info:
        return
    count, sides = dmg_info
    dice = roll_custom_dice(count, sides)
    total = sum(dice)
    entry = {
        "label": f"{item.get('name', 'Item')} (Dano)",
        "roll_type": "damage",
        "skill_name": item.get("name", "Item"),
        "attr_code": "DMG",
        "attr_value": 0,
        "skill_bonus": 0,
        "trained": False,
        "dice": dice,
        "total": total,
        "dice_config": {"count": count, "sides": sides},
        "damage_expr": f"{count}D{sides}",
    }
    start_roll(entry)


def roll_inventory_item_damage(index):
    roll_item_damage(index)


def roll_summary(entry):
    dice_str = "+".join(str(d) for d in entry["dice"])
    label = entry.get("label", entry["roll_type"].title())
    total = entry["total"]
    roll_type = entry.get("roll_type")
    if roll_type in ("attribute", "skill"):
        parts = [
            f"3D6({dice_str})",
            f"{entry['attr_code']}({entry['attr_value']:+})",
        ]
        if roll_type == "skill":
            if entry["skill_bonus"]:
                parts.append(f"Treino({entry['skill_bonus']:+})")
            else:
                parts.append("Sem treino")
        return f"{label}: {' + '.join(parts)} = {total}"
    elif roll_type == "damage":
        expr = entry.get("damage_expr", "Dano")
        return f"{label}: {expr}({dice_str}) = {total}"
    else:
        return f"{label}: {dice_str} = {total}"


def start_roll(entry):
    """Inicia animação de rolagem e agenda aplicação do resultado."""
    now = pygame.time.get_ticks()
    DICE_STATE["pending"] = entry
    DICE_STATE["rolling"] = True
    DICE_STATE["roll_start"] = now
    DICE_STATE["last_anim"] = now
    config = entry.get("dice_config") or {"count": 3, "sides": 6}
    DICE_STATE["anim_config"] = config
    DICE_STATE["display_dice"] = roll_custom_dice(config.get("count", 3), config.get("sides", 6))


def update_dice_roll():
    """Atualiza animação e finaliza rolagem após o tempo."""
    if not DICE_STATE["rolling"] or not DICE_STATE["pending"]:
        return
    now = pygame.time.get_ticks()
    # Gira os dados rapidamente enquanto rola
    if now - DICE_STATE["last_anim"] > 80:
        config = DICE_STATE.get("anim_config") or {"count": 3, "sides": 6}
        DICE_STATE["display_dice"] = roll_custom_dice(config.get("count", 3), config.get("sides", 6))
        DICE_STATE["last_anim"] = now
    # Finaliza após 1s
    if now - DICE_STATE["roll_start"] >= 1000:
        entry = DICE_STATE["pending"]
        record_roll(entry)
        DICE_STATE["display_dice"] = entry["dice"]
        DICE_STATE["rolling"] = False
        DICE_STATE["pending"] = None


def draw_attribute_column(surface):
    base_x = 14
    base_y = 14
    width = 180
    height = 118
    for idx, attr in enumerate(ATTRIBUTES):
        code, name, value = attr["code"], attr["name"], attr["value"]
        top = base_y + idx * height
        rect = pygame.Rect(base_x, top, width, height - 6)

        # Bloco principal
        pygame.draw.rect(surface, GRAY_30, rect)
        pygame.draw.rect(surface, WHITE, rect, 2)

        # Área do valor
        value_size = 70
        value_rect = pygame.Rect(rect.x + 4, rect.y + 8, value_size, value_size)
        attr["value_rect"] = value_rect
        pygame.draw.rect(surface, BLACK, value_rect)
        val_color = PURPLE if UI_STATE.get("hover_attr") == code else WHITE
        draw_text(surface, str(value), FONTS["xl"], val_color, value_rect.center, center=True)

        # Rótulos
        draw_text(surface, code, FONTS["lg"], WHITE, (rect.x + 80, rect.y + 8))
        draw_text(surface, name, FONTS["sm"], WHITE, (rect.x + 80, rect.y + 36))
        draw_text(surface, "Valor base", FONTS["xs"], GRAY_70, (rect.x + 80, rect.y + 60))

        # Botões + e -
        btn_size = 20
        btn_y = rect.y + rect.height - btn_size - 8
        minus_rect = pygame.Rect(rect.x + 10, btn_y, btn_size, btn_size)
        plus_rect = pygame.Rect(rect.x + rect.width - btn_size - 10, btn_y, btn_size, btn_size)
        attr["minus_rect"] = minus_rect
        attr["plus_rect"] = plus_rect
        for r, label in [(minus_rect, "-"), (plus_rect, "+")]:
            pygame.draw.rect(surface, GRAY_50, r)
            pygame.draw.rect(surface, WHITE, r, 1)
            draw_text(surface, label, FONTS["sm"], WHITE, r.center, center=True)


def draw_pips(surface, x, y, count, size=10, danger_index=None):
    """Desenha pequenos marcadores quadrados; danger_index colore os finais como alerta."""
    for i in range(count):
        color = WHITE
        if danger_index is not None:
            if i >= danger_index:
                color = RED  # vermelho
            elif i == danger_index - 1:
                color = ORANGE  # laranja
        pygame.draw.rect(surface, color, (x + i * (size + 4), y, size, size))


def get_attr_value(code):
    for attr in ATTRIBUTES:
        if attr["code"] == code:
            return attr["value"]
    return 0


def safe_space_value(value):
    """Converte valor do campo de espaço para inteiro >= 0."""
    if value is None:
        return 0
    try:
        val = int(str(value).strip() or 0)
    except (ValueError, TypeError):
        return 0
    return max(0, val)


def safe_type_value(value):
    """Converte valor de tipo para 1-5; padrão 1."""
    try:
        val = int(str(value).strip() or 1)
    except (ValueError, TypeError):
        return 1
    return min(5, max(1, val))


def get_inventory_weight_limit():
    bonus = INVENTORY_STATE.get("weight_bonus", 0)
    base_for = get_attr_value("FOR")
    extra = 2
    if base_for >= 6:
        extra = 9
    elif base_for >= 5:
        extra = 7
    elif base_for >= 4:
        extra = 4
    return max(0, base_for + extra + bonus)


def calc_inventory_weight(exclude_index=None):
    total = 0
    for idx, item in enumerate(INVENTORY_STATE.get("items", [])):
        if exclude_index is not None and idx == exclude_index:
            continue
        total += safe_space_value(item.get("space"))
    return total


def count_items_by_type(exclude_index=None):
    counts = [0, 0, 0, 0, 0]
    for idx, item in enumerate(INVENTORY_STATE.get("items", [])):
        if exclude_index is not None and idx == exclude_index:
            continue
        raw_tipo = item.get("tipo")
        if raw_tipo is None or str(raw_tipo).strip() == "":
            continue
        tipo = safe_type_value(raw_tipo)
        counts[tipo - 1] += 1
    return counts


def refresh_inventory_totals():
    INVENTORY_STATE["total_values"] = count_items_by_type()


def roll_custom_dice(count, sides):
    return [random.randint(1, max(1, sides)) for _ in range(max(1, count))]


def parse_damage_die(text):
    if not text:
        return None
    parts = str(text).lower().strip().split("d")
    if len(parts) != 2:
        return None
    try:
        count = int(parts[0]) if parts[0] else 1
        sides = int(parts[1])
    except ValueError:
        return None
    count = max(1, count)
    sides = max(2, sides)
    return (count, sides)


def calc_life_counts(vigor_value):
    """
    Calcula quantidade de caixas por trilha de vida a partir do VIG.
    Regras:
      VIG=6 -> LEVE 10, FERIDO 8, MACHUCADO 6, MORRENDO 1
      VIG=0 -> minimo 4/2/1/1 (leve/ferido/machucado/morrendo)
    """
    mapping = {
        "LEVE": 4,
        "FERIDO": 2,
        "MACHUCADO": 0,
        "MORRENDO": -2,
    }
    minima = {
        "LEVE": 4,
        "FERIDO": 2,
        "MACHUCADO": 1,
        "MORRENDO": 1,
    }
    maxima = {
        "LEVE": 10,
        "FERIDO": 8,
        "MACHUCADO": 6,
        "MORRENDO": 1,
    }
    counts = {}
    for key, offset in mapping.items():
        counts[key] = max(minima[key], min(maxima[key], vigor_value + offset))
    return counts

def sync_life_marks(counts):
    """Garante que LIFE_MARKS tenha o número correto de caixas por trilha."""
    for key, count in counts.items():
        marks = LIFE_MARKS.get(key, [])
        if len(marks) > count:
            LIFE_MARKS[key] = marks[:count]
        elif len(marks) < count:
            LIFE_MARKS[key] = marks + [False] * (count - len(marks))


def calc_san_counts(pres_value):
    """
    Contagem das caixas de sanidade baseada em Presenca (PRE).
    Regras iguais as de vida: 10/8/6/1 no maximo (PRE 6), minimo 4/2/1/1.
    """
    mapping = {
        "EST\u00c1VEL": 4,
        "INST\u00c1VEL": 2,
        "PERTURBADO": 0,
        "ENLOUQUECENDO": -2,
    }
    minima = {
        "EST\u00c1VEL": 4,
        "INST\u00c1VEL": 2,
        "PERTURBADO": 1,
        "ENLOUQUECENDO": 1,
    }
    maxima = {
        "EST\u00c1VEL": 10,
        "INST\u00c1VEL": 8,
        "PERTURBADO": 6,
        "ENLOUQUECENDO": 1,
    }
    counts = {}
    for key, offset in mapping.items():
        counts[key] = max(minima[key], min(maxima[key], pres_value + offset))
    return counts

def sync_san_marks(counts):
    for key, count in counts.items():
        marks = SAN_MARKS.get(key, [])
        if len(marks) > count:
            SAN_MARKS[key] = marks[:count]
        elif len(marks) < count:
            SAN_MARKS[key] = marks + [False] * (count - len(marks))


def life_status():
    """
    Retorna (texto, cor, nível) para o status da carta VIDA.
    Escala:
      - Saudável (verde) se nada completo
      - Ferido (laranja) quando LEVE completo
      - Machucado (vermelho) quando FERIDO completo
      - Morrendo (preto) quando MACHUCADO completo
    Em Morrendo, a cor da caixa varia conforme os círculos de sucesso/falha:
      Sucessos: 1 verde escuro, 2 verde médio, 3 verde vivo
      Falhas: 1 vermelho escuro, 2 vermelho médio, 3 vermelho vivo
      Empate/sem marcas: preto
    """
    steps = [("SAUDÁVEL", (0, 180, 0)), ("FERIDO", ORANGE), ("MACHUCADO", RED), ("MORRENDO", BLACK)]
    level = 0
    if LIFE_MARKS["LEVE"] and all(LIFE_MARKS["LEVE"]):
        level = 1
    if LIFE_MARKS["FERIDO"] and all(LIFE_MARKS["FERIDO"]):
        level = 2
    if LIFE_MARKS["MACHUCADO"] and all(LIFE_MARKS["MACHUCADO"]):
        level = 3
    # Se houver marca em MORRENDO, consideramos o estado final para refletir os saves.
    if LIFE_MARKS["MORRENDO"] and any(LIFE_MARKS["MORRENDO"]):
        level = max(level, 3)

    text, color = steps[level]

    def grad_green(count):
        if count >= 3:
            return (0, 210, 0)
        if count == 2:
            return (0, 170, 0)
        if count == 1:
            return (0, 130, 0)
        return BLACK

    def grad_red(count):
        if count >= 3:
            return (240, 20, 20)
        if count == 2:
            return (200, 20, 20)
        if count == 1:
            return (160, 20, 20)
        return BLACK

    if level == 3 and any(LIFE_MARKS["MORRENDO"]):
        succ = sum(DEATH_SAVES["success"])
        fail = sum(DEATH_SAVES["fail"])
        if succ > fail and succ > 0:
            text, color = ("VIVO", grad_green(succ))
        elif fail > succ and fail > 0:
            text, color = ("MORTO", grad_red(fail))
        else:
            text, color = ("MORRENDO", BLACK)
    return text, color, level


def sanity_status():
    """
    Estável, Instável, Perturbado, Enlouquecendo, Louco.
    Evolui conforme trilhas de sanidade são completadas.
    """
    steps = [
        ("ESTÁVEL", (0, 170, 140)),
        ("INSTÁVEL", ORANGE),
        ("PERTURBADO", RED),
        ("ENLOUQUECENDO", (140, 0, 60)),
        ("LOUCO", BLACK),
    ]
    level = 0
    if SAN_MARKS["ESTÁVEL"] and all(SAN_MARKS["ESTÁVEL"]):
        level = 1
    if SAN_MARKS["INSTÁVEL"] and all(SAN_MARKS["INSTÁVEL"]):
        level = 2
    if SAN_MARKS["PERTURBADO"] and all(SAN_MARKS["PERTURBADO"]):
        level = 3
    if SAN_MARKS["ENLOUQUECENDO"] and all(SAN_MARKS["ENLOUQUECENDO"]):
        level = 4
    text, color = steps[level]

    def grad_green(count):
        if count >= 3:
            return (0, 210, 0)
        if count == 2:
            return (0, 170, 0)
        if count == 1:
            return (0, 130, 0)
        return BLACK

    def grad_red(count):
        if count >= 3:
            return (240, 20, 20)
        if count == 2:
            return (200, 20, 20)
        if count == 1:
            return (160, 20, 20)
        return BLACK

    if level == 4 and any(SAN_MARKS["ENLOUQUECENDO"]):
        succ = sum(SAN_SAVES["success"])
        fail = sum(SAN_SAVES["fail"])
        if succ > fail and succ > 0:
            text, color = ("ESTÁ TUDO BEM", grad_green(succ))
        elif fail > succ and fail > 0:
            text, color = ("É O FIM", grad_red(fail))
        else:
            text, color = ("LOUCO", BLACK)
    return text, color, level


def draw_death_saves(surface, card_rect, y_start=None):
    """Desenha resistência à morte centralizada dentro do card; y_start opcional para evitar sobreposição."""
    global DEATH_RECTS
    DEATH_RECTS.clear()
    radius = 8
    spacing = 18
    block_gap = 70
    block_width = (radius * 2 + spacing * 2)  # largura aproximada de 3 círculos
    total_width = block_width * 2 + block_gap
    x = card_rect.x + (card_rect.width - total_width) // 2
    default_y = card_rect.bottom - 56
    y = default_y if y_start is None else max(card_rect.y + 10, min(y_start, default_y))

    draw_text(surface, "RESISTÊNCIA À MORTE", FONTS["xs"], WHITE, (card_rect.centerx, y), center=True)
    y += 14
    success_x = x + block_width // 2
    fail_x = x + block_width + block_gap + block_width // 2

    draw_text(surface, "SUCESSO", FONTS["xs"], (0, 200, 0), (success_x, y), center=True)
    draw_text(surface, "FALHA", FONTS["xs"], RED, (fail_x, y), center=True)
    y += 14
    # Sucesso
    for i in range(3):
        cx = x + i * spacing
        rect = pygame.Rect(cx - radius, y - radius, radius * 2, radius * 2)
        DEATH_RECTS.append(("success", i, rect))
        pygame.draw.circle(surface, WHITE if DEATH_SAVES["success"][i] else GRAY_70, (cx, y), radius)
        pygame.draw.circle(surface, WHITE, (cx, y), radius, 1)
    # Falha
    x_fail = x + block_width + block_gap
    for i in range(3):
        cx = x_fail + i * spacing
        rect = pygame.Rect(cx - radius, y - radius, radius * 2, radius * 2)
        DEATH_RECTS.append(("fail", i, rect))
        pygame.draw.circle(surface, WHITE if DEATH_SAVES["fail"][i] else GRAY_70, (cx, y), radius)
        pygame.draw.circle(surface, WHITE, (cx, y), radius, 1)


def draw_sanity_saves(surface, card_rect, y_start=None):
    """Resistência à loucura, espelhando a de morte; y_start opcional para evitar sobreposição."""
    global SAN_SAVE_RECTS
    SAN_SAVE_RECTS.clear()
    radius = 8
    spacing = 18
    block_gap = 70
    block_width = (radius * 2 + spacing * 2)
    total_width = block_width * 2 + block_gap
    x = card_rect.x + (card_rect.width - total_width) // 2
    default_y = card_rect.bottom - 56
    y = default_y if y_start is None else max(card_rect.y + 10, min(y_start, default_y))

    draw_text(surface, "RESISTÊNCIA À LOUCURA", FONTS["xs"], WHITE, (card_rect.centerx, y), center=True)
    y += 14
    success_x = x + block_width // 2
    fail_x = x + block_width + block_gap + block_width // 2
    draw_text(surface, "SUCESSO", FONTS["xs"], (0, 200, 0), (success_x, y), center=True)
    draw_text(surface, "FALHA", FONTS["xs"], RED, (fail_x, y), center=True)
    y += 14
    for i in range(3):
        cx = x + i * spacing
        rect = pygame.Rect(cx - radius, y - radius, radius * 2, radius * 2)
        SAN_SAVE_RECTS.append(("success", i, rect))
        pygame.draw.circle(surface, WHITE if SAN_SAVES["success"][i] else GRAY_70, (cx, y), radius)
        pygame.draw.circle(surface, WHITE, (cx, y), radius, 1)
    x_fail = x + block_width + block_gap
    for i in range(3):
        cx = x_fail + i * spacing
        rect = pygame.Rect(cx - radius, y - radius, radius * 2, radius * 2)
        SAN_SAVE_RECTS.append(("fail", i, rect))
        pygame.draw.circle(surface, WHITE if SAN_SAVES["fail"][i] else GRAY_70, (cx, y), radius)
        pygame.draw.circle(surface, WHITE, (cx, y), radius, 1)


def draw_vitals_panel(surface):
    base_x = 206
    base_y = 14
    card_w = 210
    card_h = 240

    # Painel VIDA com trilhas dinâmicas
    life_rect = pygame.Rect(base_x + 0, base_y, card_w, card_h)
    pygame.draw.rect(surface, BLACK, life_rect)
    pygame.draw.rect(surface, WHITE, life_rect, 2)
    draw_text(surface, "VIDA", FONTS["md"], WHITE, (life_rect.x + 10, life_rect.y + 8))
    status_text, status_color, status_level = life_status()
    status_rect = pygame.Rect(life_rect.x + 10, life_rect.y + 32, 110, 24)
    pygame.draw.rect(surface, status_color, status_rect)
    draw_text(surface, status_text, FONTS["xs"], BLACK if status_color != BLACK else WHITE, status_rect.center, center=True)

    # Trilhas tolerância vida (dinâmicas por VIG)
    vigor_value = get_attr_value("VIG")
    counts = calc_life_counts(vigor_value)
    sync_life_marks(counts)
    LIFE_RECTS.clear()
    start_y = life_rect.y + 74
    row_gap = 4
    box_size = 12
    box_step = box_size + 4
    label_x = life_rect.x + 14
    max_boxes = max(counts.values()) if counts else 1
    max_width = box_size + (max_boxes - 1) * box_step
    box_x = life_rect.right - 12 - max_width
    current_y = start_y
    for key in LIFE_TRACKS:
        label_rect = draw_text(surface, key.title(), FONTS["xs"], WHITE, (label_x, current_y))
        y_boxes = current_y
        row_height = max(box_size, label_rect.height)
        if label_rect.right + 6 > box_x:
            y_boxes = current_y + label_rect.height + 2
            row_height = label_rect.height + 2 + box_size
        marks = LIFE_MARKS[key]
        for j in range(counts[key]):
            brect = pygame.Rect(box_x + j * (box_size + 4), y_boxes, box_size, box_size)
            pygame.draw.rect(surface, RED, brect)
            pygame.draw.rect(surface, WHITE, brect, 1)
            if marks[j]:
                pygame.draw.line(surface, WHITE, (brect.x + 2, brect.y + 2), (brect.right - 2, brect.bottom - 2), 2)
                pygame.draw.line(surface, WHITE, (brect.right - 2, brect.y + 2), (brect.x + 2, brect.bottom - 2), 2)
            LIFE_RECTS.append((key, j, brect))
        current_y += row_height + row_gap

    # Resistência à morte aparece apenas quando alguma caixa de MORRENDO está marcada
    if any(LIFE_MARKS["MORRENDO"]):
        death_block_h = 48
        death_y = min(max(current_y + 10, life_rect.y + 74), life_rect.bottom - death_block_h)
        draw_death_saves(surface, life_rect, y_start=death_y)

    # Painel SANIDADE (agora dinâmico)
    san_rect = pygame.Rect(base_x + card_w + 10, base_y, card_w, card_h)
    pygame.draw.rect(surface, BLACK, san_rect)
    pygame.draw.rect(surface, WHITE, san_rect, 2)
    draw_text(surface, "SANIDADE", FONTS["md"], WHITE, (san_rect.x + 10, san_rect.y + 8))
    san_status_text, san_status_color, san_level = sanity_status()
    san_status_rect = pygame.Rect(san_rect.x + 10, san_rect.y + 32, 110, 24)
    pygame.draw.rect(surface, san_status_color, san_status_rect)
    draw_text(surface, san_status_text, FONTS["xs"], BLACK if san_status_color != BLACK else WHITE, san_status_rect.center, center=True)

    # Trilhas de sanidade
    pres_value = get_attr_value("PRE")
    san_counts = calc_san_counts(pres_value)
    sync_san_marks(san_counts)
    SAN_RECTS.clear()
    s_start_y = san_rect.y + 74
    s_row_gap = 4
    s_box_size = 12
    s_box_step = s_box_size + 4
    s_label_x = san_rect.x + 14
    s_max_boxes = max(san_counts.values()) if san_counts else 1
    s_max_width = s_box_size + (s_max_boxes - 1) * s_box_step
    s_box_x = san_rect.right - 12 - s_max_width
    s_current_y = s_start_y
    for key in SAN_TRACKS:
        label_rect = draw_text(surface, key.title(), FONTS["xs"], WHITE, (s_label_x, s_current_y))
        y_boxes = s_current_y
        row_height = max(s_box_size, label_rect.height)
        if label_rect.right + 6 > s_box_x:
            y_boxes = s_current_y + label_rect.height + 2
            row_height = label_rect.height + 2 + s_box_size
        marks = SAN_MARKS[key]
        for j in range(san_counts[key]):
            brect = pygame.Rect(s_box_x + j * s_box_step, y_boxes, s_box_size, s_box_size)
            pygame.draw.rect(surface, RED, brect)
            pygame.draw.rect(surface, WHITE, brect, 1)
            if marks[j]:
                pygame.draw.line(surface, WHITE, (brect.x + 2, brect.y + 2), (brect.right - 2, brect.bottom - 2), 2)
                pygame.draw.line(surface, WHITE, (brect.right - 2, brect.y + 2), (brect.x + 2, brect.bottom - 2), 2)
            SAN_RECTS.append((key, j, brect))
        s_current_y += row_height + s_row_gap

    # Resistência à loucura aparece apenas quando alguma caixa de ENLOUQUECENDO está marcada
    if any(SAN_MARKS["ENLOUQUECENDO"]):
        sanity_block_h = 48
        sanity_y = min(max(s_current_y + 10, s_start_y), san_rect.bottom - sanity_block_h)
        draw_sanity_saves(surface, san_rect, y_start=sanity_y)

    # Esforço
    effort_rect = pygame.Rect(base_x, base_y + card_h + 12, card_w * 2 + 10, 160)
    pygame.draw.rect(surface, BLACK, effort_rect)
    pygame.draw.rect(surface, WHITE, effort_rect, 2)
    draw_text(surface, "ESFORÇO", FONTS["md"], WHITE, (effort_rect.x + 10, effort_rect.y + 8))

    int_value = get_attr_value("INT")
    sync_effort_with_int(int_value)

    label_y = effort_rect.y + 24
    current_rect = pygame.Rect(effort_rect.x + 140, label_y - 2, 70, 22)
    total_rect = pygame.Rect(effort_rect.x + 260, label_y - 2, 70, 22)
    bonus_rect = pygame.Rect(effort_rect.x + 360, label_y - 2, 60, 22)
    EFFORT_STATE["input_rects"] = {"current": current_rect, "total": total_rect, "bonus": bonus_rect}

    draw_text(surface, "Atual", FONTS["xs"], WHITE, (effort_rect.x + 110, label_y))
    draw_text(surface, "Total", FONTS["xs"], WHITE, (effort_rect.x + 232, label_y))
    draw_text(surface, "Bônus", FONTS["xs"], WHITE, (effort_rect.x + 332, label_y))
    for field, rect in [("current", current_rect), ("total", total_rect), ("bonus", bonus_rect)]:
        pygame.draw.rect(surface, BLACK, rect)
        pygame.draw.rect(surface, ORANGE if EFFORT_STATE["focus"] == field else WHITE, rect, 1)
        buffer_text = EFFORT_STATE["buffers"][field]
        draw_text(surface, buffer_text, FONTS["xs"], WHITE, rect.inflate(-6, -2).topleft)

    # Indicador circular de esforço (lado esquerdo, maior)
    circle_center = (effort_rect.x + 60, effort_rect.y + 96)
    radius = 32
    pygame.draw.circle(surface, GRAY_30, circle_center, radius)
    pygame.draw.circle(surface, WHITE, circle_center, radius, 1)
    effective_current = EFFORT_STATE["current"] + EFFORT_STATE["bonus"]
    ratio = (effective_current / EFFORT_STATE["total"]) if EFFORT_STATE["total"] > 0 else 0
    if ratio > 0:
        start_ang = -math.pi / 2
        end_ang = start_ang + min(ratio, 1) * 2 * math.pi
        pygame.draw.arc(
            surface,
            ORANGE,
            (circle_center[0] - radius, circle_center[1] - radius, radius * 2, radius * 2),
            start_ang,
            end_ang,
            6,
        )
    display_text = f"{effective_current}/{EFFORT_STATE['total']}"
    draw_text(surface, display_text, FONTS["xs"], WHITE, circle_center, center=True)

    offsets = [-5, -2, -1, 1, 2, 5]
    btn_w, btn_h = 48, 18
    EFFORT_STATE["btn_rects"].clear()
    for i, val in enumerate(offsets):
        row = i // 3
        col = i % 3
        bx = effort_rect.x + 140 + col * (btn_w + 12)
        by = effort_rect.y + 60 + row * (btn_h + 10)
        brect = pygame.Rect(bx, by, btn_w, btn_h)
        pygame.draw.rect(surface, GRAY_30, brect)
        pygame.draw.rect(surface, GRAY_70, brect, 1)
        draw_text(surface, f"{val:+}", FONTS["xs"], WHITE, brect.center, center=True)
        EFFORT_STATE["btn_rects"].append((brect, val))


def draw_notes_panel(surface):
    panel_w = 360
    panel_h = 360
    panel_x = 206 + 210 * 2 + 40  # ao lado do painel de esforço, sem sobreposição
    panel_y = 14
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(surface, BLACK, panel_rect)
    pygame.draw.rect(surface, WHITE, panel_rect, 2)
    draw_text(surface, "ANOTACOES", FONTS["md"], WHITE, (panel_rect.x + 10, panel_rect.y + 6))

    inner_pad = 8
    field_height = 26
    gap = 6

    title_rect = pygame.Rect(panel_rect.x + inner_pad, panel_rect.y + 32, panel_rect.width - inner_pad * 2, field_height)
    subject_rect = pygame.Rect(panel_rect.x + inner_pad, title_rect.bottom + gap, panel_rect.width - inner_pad * 2, field_height)
    body_rect = pygame.Rect(panel_rect.x + inner_pad, subject_rect.bottom + gap, panel_rect.width - inner_pad * 2, panel_rect.height - inner_pad - (subject_rect.bottom + gap) - 42)
    send_rect = pygame.Rect(panel_rect.x + inner_pad, body_rect.bottom + gap, panel_rect.width - inner_pad * 2, 28)

    NOTE_STATE["rects"] = {"title": title_rect, "subject": subject_rect, "body": body_rect}
    NOTE_STATE["send_rect"] = send_rect

    # Title
    pygame.draw.rect(surface, GRAY_30, title_rect)
    pygame.draw.rect(surface, ORANGE if NOTE_STATE["focus"] == "title" else WHITE, title_rect, 1)
    title_inner = title_rect.inflate(-6, -2)
    draw_text(surface, NOTE_STATE["title"], FONTS["xs"], WHITE, title_inner.topleft)
    if NOTE_STATE["focus"] == "title":
        cur = NOTE_STATE["cursor"]["title"]
        caret_x = title_inner.x + FONTS["xs"].size(NOTE_STATE["title"][:cur])[0]
        pygame.draw.line(surface, WHITE, (caret_x, title_inner.y), (caret_x, title_inner.bottom), 1)

    # Subject
    pygame.draw.rect(surface, GRAY_30, subject_rect)
    pygame.draw.rect(surface, ORANGE if NOTE_STATE["focus"] == "subject" else WHITE, subject_rect, 1)
    subject_inner = subject_rect.inflate(-6, -2)
    draw_text(surface, NOTE_STATE["subject"], FONTS["xs"], WHITE, subject_inner.topleft)
    if NOTE_STATE["focus"] == "subject":
        cur = NOTE_STATE["cursor"]["subject"]
        caret_x = subject_inner.x + FONTS["xs"].size(NOTE_STATE["subject"][:cur])[0]
        pygame.draw.line(surface, WHITE, (caret_x, subject_inner.y), (caret_x, subject_inner.bottom), 1)

    # Body with scroll
    pygame.draw.rect(surface, GRAY_30, body_rect)
    pygame.draw.rect(surface, ORANGE if NOTE_STATE["focus"] == "body" else WHITE, body_rect, 1)
    body_inner = body_rect.inflate(-6, -6)
    lines, line_starts = wrap_text(NOTE_STATE["body"], FONTS["xs"], body_inner.width)
    line_h = FONTS["xs"].get_height()
    visible_lines = body_inner.height // line_h
    max_scroll = max(0, len(lines) - visible_lines)
    NOTE_STATE["max_scroll"] = max_scroll
    start_idx = NOTE_STATE["scroll"]
    end_idx = start_idx + visible_lines
    for i, line in enumerate(lines[start_idx:end_idx]):
        draw_text(surface, line, FONTS["xs"], WHITE, (body_inner.x, body_inner.y + i * line_h))
    # Caret for body
    if NOTE_STATE["focus"] == "body":
        cur = NOTE_STATE["cursor"]["body"]
        caret_x = body_inner.x
        caret_y = body_inner.y
        # find line index for cursor
        line_idx = 0
        for idx, start in enumerate(line_starts):
            if cur >= start:
                line_idx = idx
        line_idx = min(line_idx, len(lines) - 1)
        caret_line = lines[line_idx] if lines else ""
        offset_in_line = cur - line_starts[line_idx]
        caret_text = caret_line[:offset_in_line]
        caret_x += FONTS["xs"].size(caret_text)[0]
        visible_line_idx = line_idx - start_idx
        if 0 <= visible_line_idx < visible_lines:
            caret_y += visible_line_idx * line_h
            pygame.draw.line(surface, WHITE, (caret_x, caret_y), (caret_x, caret_y + line_h), 1)

    # Send button
    pygame.draw.rect(surface, GRAY_50, send_rect)
    pygame.draw.rect(surface, WHITE, send_rect, 1)
    draw_text(surface, "ENVIAR", FONTS["md"], BLACK, send_rect.center, center=True)


def draw_inventory_panel(surface):
    panel_x = 1080
    panel_y = 14
    panel_w = BASE_WIDTH - panel_x - 20
    panel_h = 790
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(surface, BLACK, panel_rect)
    pygame.draw.rect(surface, WHITE, panel_rect, 2)
    content_pad = 10

    def draw_boxes(label, values, start_y, store_rects):
        draw_text(surface, label, FONTS["sm"], WHITE, (panel_x + content_pad, start_y))
        box_w = 28
        gap = 6
        base_x = panel_x + 150
        for i, val in enumerate(values):
            rect = pygame.Rect(base_x + i * (box_w + gap), start_y - 2, box_w, box_w)
            pygame.draw.rect(surface, BLACK, rect)
            pygame.draw.rect(surface, WHITE, rect, 1)
            draw_text(surface, str(val), FONTS["sm"], WHITE, rect.center, center=True)
            store_rects.append(rect)
        return start_y + box_w + 6

    def draw_form_label(text, rect):
        draw_text(surface, text, FONTS["xs"], WHITE, (rect.x, rect.y - 14))

    def draw_form_text(field, rect, label, multiline=False, bold=False):
        form_state = INVENTORY_STATE["form"]
        focus_field = form_state.get("focus")
        value = form_state.get(field, "")
        border_color = ORANGE if focus_field == field else WHITE
        bg_color = BLACK if multiline else GRAY_30
        pygame.draw.rect(surface, bg_color, rect)
        pygame.draw.rect(surface, border_color, rect, 2 if focus_field == field else 1)
        draw_form_label(label, rect)
        font = FONTS["sm_b"] if bold else FONTS["sm"]
        text_color = WHITE
        if multiline:
            lines, _ = wrap_text(value or "", font, rect.width - 10)
            line_h = font.get_linesize()
            max_lines = max(1, rect.height // line_h)
            for i, line in enumerate(lines[:max_lines]):
                draw_text(surface, line, font, text_color, (rect.x + 5, rect.y + 4 + i * line_h))
        else:
            display = value or ""
            render = font.render(display, True, text_color)
            text_rect = render.get_rect()
            text_rect.topleft = (rect.x + 5, rect.y + rect.height // 2 - text_rect.height // 2)
            surface.blit(render, text_rect)
        INVENTORY_STATE["form"]["rects"][field] = rect
        if focus_field == field:
            caret_visible = (pygame.time.get_ticks() // 400) % 2 == 0
            if caret_visible:
                if multiline:
                    lines, _ = wrap_text(value or "", font, rect.width - 10)
                    if not lines:
                        lines = [""]
                    line_h = font.get_linesize()
                    caret_y = rect.y + 4 + (len(lines) - 1) * line_h
                    caret_x = rect.x + 5 + font.size(lines[-1])[0]
                    caret_h = line_h - 4
                else:
                    caret_x = rect.x + 5 + font.size(value)[0]
                    caret_y = rect.y + rect.height // 2 - font.get_linesize() // 2
                    caret_h = font.get_linesize() - 4
                pygame.draw.line(surface, WHITE, (caret_x, caret_y), (caret_x, caret_y + caret_h), 1)

    def draw_form_dropdown(field, rect, label):
        dropdown = INVENTORY_STATE.get("form_dropdown")
        active = dropdown and dropdown.get("field") == field
        border_color = ORANGE if active else WHITE
        pygame.draw.rect(surface, GRAY_30, rect)
        pygame.draw.rect(surface, border_color, rect, 2 if active else 1)
        draw_form_label(label, rect)
        value = INVENTORY_STATE["form"].get(field, "")
        display = value if value else "--"
        draw_text(surface, display, FONTS["sm"], WHITE, (rect.x + 6, rect.y + 6))
        tri_x = rect.right - 14
        tri_y = rect.y + rect.height // 2
        pygame.draw.polygon(surface, WHITE, [(tri_x - 6, tri_y - 4), (tri_x + 6, tri_y - 4), (tri_x, tri_y + 4)])
        INVENTORY_STATE["form"]["rects"][field] = rect

    def draw_image_field(rect):
        pygame.draw.rect(surface, GRAY_30, rect)
        pygame.draw.rect(surface, WHITE, rect, 1)
        img_surface = INVENTORY_STATE["form"].get("image_surface")
        if img_surface:
            scaled = pygame.transform.smoothscale(img_surface, (rect.width, rect.height))
            surface.blit(scaled, rect)
        else:
            draw_text(surface, "imagem\ndo\nitem*", FONTS["xs"], WHITE, rect.center, center=True)
        INVENTORY_STATE["form"]["rects"]["image"] = rect

    def draw_multiline_box(rect, label, field, bold=False):
        draw_form_text(field, rect, label, multiline=True, bold=bold)

    def draw_summary_field(rect, label, value, multiline=False, bold=False):
        value = value or ("--" if not multiline else "")
        pygame.draw.rect(surface, BLACK, rect)
        pygame.draw.rect(surface, WHITE, rect, 1)
        draw_form_label(label, rect)
        font = FONTS["sm_b"] if bold else FONTS["sm"]
        color = WHITE
        if multiline:
            text = value if value else ""
            lines, _ = wrap_text(text, font, rect.width - 10)
            if not lines:
                lines = ["--"]
            line_h = font.get_linesize()
            max_lines = max(1, rect.height // line_h)
            for i, line in enumerate(lines[:max_lines]):
                draw_text(surface, line, font, color, (rect.x + 5, rect.y + 4 + i * line_h))
        else:
            display = value if value else "--"
            render = font.render(display, True, color)
            rect_text = render.get_rect()
            rect_text.topleft = (rect.x + 5, rect.y + rect.height // 2 - rect_text.height // 2)
            surface.blit(render, rect_text)

    def draw_summary_image(rect, surface_img):
        pygame.draw.rect(surface, GRAY_30, rect)
        pygame.draw.rect(surface, WHITE, rect, 1)
        if surface_img:
            scaled = pygame.transform.smoothscale(surface_img, (rect.width, rect.height))
            surface.blit(scaled, rect)
        else:
            draw_text(surface, "sem\nimagem", FONTS["xs"], WHITE, rect.center, center=True)

    INVENTORY_STATE["tab_rects"].clear()
    tabs = INVENTORY_STATE["tabs"]
    tab_h = 34
    tab_w = panel_w // len(tabs)
    for i, label in enumerate(tabs):
        x = panel_x + i * tab_w
        rect = pygame.Rect(x, panel_y, tab_w, tab_h)
        active = label == INVENTORY_STATE["active_tab"]
        pygame.draw.rect(surface, GRAY_50 if active else GRAY_70, rect)
        pygame.draw.rect(surface, BLACK, rect, 1)
        draw_text(surface, label, FONTS["md"], WHITE, rect.center, center=True)
        INVENTORY_STATE["tab_rects"].append((label, rect))

    content_y = panel_y + tab_h + 6

    INVENTORY_STATE["limit_rects"].clear()
    INVENTORY_STATE["total_rects"].clear()
    INVENTORY_STATE["add_rect"] = None

    y = content_y
    current_tab = INVENTORY_STATE["active_tab"]
    is_inventory = current_tab.upper().startswith("INVENT")

    if is_inventory:
        INVENTORY_STATE["total_values"] = count_items_by_type()
        y = draw_boxes("LIMITE DE ITENS", INVENTORY_STATE["limit_values"], y, INVENTORY_STATE["limit_rects"])
        y = draw_boxes("TOTAL NO INVENTARIO", INVENTORY_STATE["total_values"], y, INVENTORY_STATE["total_rects"])
        draw_text(surface, "PESO", FONTS["sm"], WHITE, (panel_x + content_pad, y))
        max_weight = get_inventory_weight_limit()
        current_w = calc_inventory_weight()
        INVENTORY_STATE["current_weight"] = current_w
        draw_text(surface, f"{current_w:02d}/{max_weight:02d}", FONTS["sm"], WHITE, (panel_x + 150, y))

        form_y = y + 32
        gap = 12
        split_x = panel_x + panel_w // 2
        left_x = panel_x + content_pad
        left_w = split_x - gap // 2 - left_x
        right_x = split_x + gap // 2
        right_w = panel_rect.right - content_pad - right_x

        form_rect = pygame.Rect(left_x, form_y, left_w, panel_h - form_y - content_pad)
        list_rect = pygame.Rect(right_x, form_y, right_w, panel_h - form_y - content_pad)

        pygame.draw.rect(surface, BLACK, list_rect)
        pygame.draw.rect(surface, WHITE, list_rect, 1)
        list_inner = list_rect.inflate(-12, -12)

        add_w, add_h = 90, 26
        add_rect = pygame.Rect(list_rect.right - add_w - 4, list_rect.y - add_h - 6, add_w, add_h)
        pygame.draw.rect(surface, (0, 130, 0), add_rect)
        pygame.draw.rect(surface, WHITE, add_rect, 1)
        draw_text(surface, "ADICIONAR", FONTS["xs"], WHITE, add_rect.center, center=True)
        INVENTORY_STATE["add_rect"] = add_rect

        items = INVENTORY_STATE.get("items", [])
        view_index = INVENTORY_STATE.get("view_item_index")
        category_filter = INVENTORY_STATE.get("category_filter")
        if view_index is not None:
            if not (0 <= view_index < len(items)):
                view_index = None
                INVENTORY_STATE["view_item_index"] = None
            elif category_filter:
                item_cat = (items[view_index].get("category") or "").strip().lower()
                if item_cat != category_filter.strip().lower():
                    view_index = None
                    INVENTORY_STATE["view_item_index"] = None
        mode = "form" if INVENTORY_STATE.get("show_form") else ("view" if view_index is not None else "empty")

        if mode == "form":
            pygame.draw.rect(surface, BLACK, form_rect)
            pygame.draw.rect(surface, WHITE, form_rect, 1)
            form_state = INVENTORY_STATE["form"]
            form_state["rects"] = {}

            inner_pad = 12
            img_size = 120
            img_rect = pygame.Rect(form_rect.x + inner_pad, form_rect.y + inner_pad, img_size, img_size)
            draw_image_field(img_rect)

            name_rect = pygame.Rect(
                img_rect.right + 12,
                img_rect.y,
                form_rect.right - inner_pad - (img_rect.right + 12),
                32,
            )
            draw_form_text("name", name_rect, "Nome do item*")

            details_gap = 8
            col_area = form_rect.right - inner_pad - (img_rect.right + 12)
            col_w = (col_area - details_gap) // 2
            row_h = 30
            rows = [
                ("category", "Categoria", 0, 0, False, False),
                ("space", "Espaco", 0, 1, False, False),
                ("tipo", "Tipo", 1, 0, False, False),
                ("alcance", "Alcance", 1, 1, False, False),
                ("empunhadura", "Empunhadura", 2, 0, False, False),
                ("dano", "Dano", 2, 1, False, False),
                ("localizacao", "Localizacao", 3, 0, True, True),
            ]
            base_y = name_rect.bottom + 16
            details_bottom = base_y
            for field, label, row_idx, col_idx, is_text, full_width in rows:
                width = col_w * 2 + details_gap if full_width else col_w
                x = img_rect.right + 12 if full_width else img_rect.right + 12 + col_idx * (col_w + details_gap)
                y_row = base_y + row_idx * (row_h + 12)
                rect = pygame.Rect(x, y_row, width, row_h)
                if field in FORM_DROPDOWN_OPTIONS and not is_text:
                    draw_form_dropdown(field, rect, label)
                else:
                    draw_form_text(field, rect, label)
                details_bottom = max(details_bottom, rect.bottom)

            desc_rect = pygame.Rect(
                form_rect.x + inner_pad,
                details_bottom + 12,
                form_rect.width - inner_pad * 2,
                150,
            )
            draw_multiline_box(desc_rect, "Descricao*", "descricao")

            info1_rect = pygame.Rect(desc_rect.x, desc_rect.bottom + 12, desc_rect.width, 70)
            draw_multiline_box(info1_rect, "Info adicional 1", "info1", bold=True)

            info2_rect = pygame.Rect(info1_rect.x, info1_rect.bottom + 8, info1_rect.width, 70)
            draw_multiline_box(info2_rect, "Info adicional 2", "info2", bold=True)

            btn_h = 32
            btn_y = info2_rect.bottom + 14
            if btn_y + btn_h + inner_pad > form_rect.bottom:
                btn_y = form_rect.bottom - inner_pad - btn_h
            btn_gap = 12
            btn_w = (form_rect.width - inner_pad * 2 - btn_gap) // 2
            save_rect = pygame.Rect(form_rect.x + inner_pad, btn_y, btn_w, btn_h)
            cancel_rect = pygame.Rect(save_rect.right + btn_gap, btn_y, btn_w, btn_h)
            pygame.draw.rect(surface, GREEN, save_rect)
            pygame.draw.rect(surface, WHITE, save_rect, 1)
            draw_text(surface, "SALVAR", FONTS["sm"], BLACK, save_rect.center, center=True)
            pygame.draw.rect(surface, RED, cancel_rect)
            pygame.draw.rect(surface, WHITE, cancel_rect, 1)
            draw_text(surface, "CANCELAR", FONTS["sm"], BLACK, cancel_rect.center, center=True)
            INVENTORY_STATE["form_buttons"] = {"save": save_rect, "cancel": cancel_rect}
            INVENTORY_STATE["summary_buttons"] = {}
            INVENTORY_STATE["view_item_index"] = None
            error_msg = INVENTORY_STATE.get("form_error")
            if error_msg:
                draw_text(surface, error_msg, FONTS["xs"], RED, (form_rect.x + inner_pad, btn_y - 18))
        elif mode == "view":
            INVENTORY_STATE["form"]["rects"] = {}
            INVENTORY_STATE["form_buttons"] = {}
            INVENTORY_STATE["form_dropdown"] = None
            pygame.draw.rect(surface, BLACK, form_rect)
            pygame.draw.rect(surface, WHITE, form_rect, 1)
            item = items[view_index]

            inner_pad = 12
            img_size = 120
            img_rect = pygame.Rect(form_rect.x + inner_pad, form_rect.y + inner_pad, img_size, img_size)
            draw_summary_image(img_rect, item.get("image_surface"))

            name_rect = pygame.Rect(
                img_rect.right + 12,
                img_rect.y,
                form_rect.right - inner_pad - (img_rect.right + 12),
                32,
            )
            draw_summary_field(name_rect, "Nome do item*", item.get("name"))

            details_gap = 8
            col_area = form_rect.right - inner_pad - (img_rect.right + 12)
            col_w = (col_area - details_gap) // 2
            row_h = 30
            detail_values = [
                ("Categoria", item.get("category"), False),
                ("Espaco", item.get("space"), False),
                ("Tipo", item.get("tipo"), False),
                ("Alcance", item.get("alcance"), False),
                ("Empunhadura", item.get("empunhadura"), False),
                ("Dano", item.get("dano"), False),
                ("Localizacao", item.get("localizacao"), True),
            ]
            base_y = name_rect.bottom + 16
            row_idx = 0
            col_idx = 0
            details_bottom = base_y
            for label, value, full_width in detail_values:
                width = col_w * 2 + details_gap if full_width else col_w
                x = img_rect.right + 12 if full_width else img_rect.right + 12 + col_idx * (col_w + details_gap)
                y_row = base_y + row_idx * (row_h + 12)
                rect = pygame.Rect(x, y_row, width, row_h)
                draw_summary_field(rect, label, value)
                details_bottom = max(details_bottom, rect.bottom)
                if full_width:
                    row_idx += 1
                    col_idx = 0
                else:
                    if col_idx == 0:
                        col_idx = 1
                    else:
                        col_idx = 0
                        row_idx += 1

            desc_rect = pygame.Rect(
                form_rect.x + inner_pad,
                details_bottom + 12,
                form_rect.width - inner_pad * 2,
                150,
            )
            draw_summary_field(desc_rect, "Descricao", item.get("descricao"), multiline=True)

            info1_rect = pygame.Rect(desc_rect.x, desc_rect.bottom + 12, desc_rect.width, 70)
            draw_summary_field(info1_rect, "Info adicional 1", item.get("info1"), multiline=True, bold=True)

            info2_rect = pygame.Rect(info1_rect.x, info1_rect.bottom + 8, info1_rect.width, 70)
            draw_summary_field(info2_rect, "Info adicional 2", item.get("info2"), multiline=True, bold=True)

            btn_h = 32
            btn_y = info2_rect.bottom + 14
            if btn_y + btn_h + inner_pad > form_rect.bottom:
                btn_y = form_rect.bottom - inner_pad - btn_h
            btn_gap = 12
            btn_w = (form_rect.width - inner_pad * 2 - btn_gap * 2) // 3
            close_rect = pygame.Rect(form_rect.x + inner_pad, btn_y, btn_w, btn_h)
            edit_rect = pygame.Rect(close_rect.right + btn_gap, btn_y, btn_w, btn_h)
            remove_rect = pygame.Rect(edit_rect.right + btn_gap, btn_y, btn_w, btn_h)
            pygame.draw.rect(surface, GRAY_50, close_rect)
            pygame.draw.rect(surface, WHITE, close_rect, 1)
            draw_text(surface, "FECHAR", FONTS["sm"], BLACK, close_rect.center, center=True)
            pygame.draw.rect(surface, ORANGE, edit_rect)
            pygame.draw.rect(surface, WHITE, edit_rect, 1)
            draw_text(surface, "EDITAR", FONTS["sm"], BLACK, edit_rect.center, center=True)
            pygame.draw.rect(surface, RED, remove_rect)
            pygame.draw.rect(surface, WHITE, remove_rect, 1)
            draw_text(surface, "REMOVER", FONTS["sm"], BLACK, remove_rect.center, center=True)
            INVENTORY_STATE["summary_buttons"] = {
                "close": close_rect,
                "edit": edit_rect,
                "remove": remove_rect,
                "index": view_index,
            }
        else:
            INVENTORY_STATE["form"]["rects"] = {}
            INVENTORY_STATE["form_buttons"] = {}
            INVENTORY_STATE["summary_buttons"] = {}
            pygame.draw.rect(surface, GRAY_30, form_rect, 1)
            draw_text(surface, "Selecione um item ou clique em ADICIONAR", FONTS["xs"], WHITE, form_rect.center, center=True)
            INVENTORY_STATE["form_dropdown"] = None

        tags = ["Armas", "municao", "Protecao", "Magikos", "Coletaveis", "Itens chave", "componentes"]
        tag_h = 24
        gap = 8
        cols = 3
        btn_w = max(max(FONTS["xs"].size(tag)[0] + 20 for tag in tags), 96)
        INVENTORY_STATE["filter_buttons"] = []
        active_filter = INVENTORY_STATE.get("category_filter")
        for i, tag in enumerate(tags):
            row = i // cols
            col = i % cols
            tx = list_inner.x + col * (btn_w + gap)
            ty = list_inner.y + row * (tag_h + gap)
            rect = pygame.Rect(tx, ty, btn_w, tag_h)
            is_active = active_filter == tag
            fill_color = GRAY_70 if is_active else GRAY_50
            border_color = ORANGE if is_active else WHITE
            pygame.draw.rect(surface, fill_color, rect)
            pygame.draw.rect(surface, border_color, rect, 2 if is_active else 1)
            draw_text(surface, tag, FONTS["xs"], WHITE, rect.center, center=True)
            INVENTORY_STATE["filter_buttons"].append((tag, rect))

        rows_count = (len(tags) + cols - 1) // cols
        table_rect = pygame.Rect(
            list_inner.x,
            list_inner.y + rows_count * (tag_h + gap) + 6,
            list_inner.width,
            list_inner.height - rows_count * (tag_h + gap) - 10,
        )

        dropdown = INVENTORY_STATE.get("dropdown")
        if dropdown and dropdown.get("type") == "limit":
            idx = dropdown.get("index")
            if idx is not None and idx < len(INVENTORY_STATE["limit_rects"]):
                base_rect = INVENTORY_STATE["limit_rects"][idx]
                opt_w = base_rect.width + 6
                opt_h = 22
                opt_pad = 2
                opt_x = base_rect.x
                opt_y = base_rect.bottom + 4
                dropdown_rects = []
                for i in range(1, 6):
                    r = pygame.Rect(opt_x, opt_y + (i - 1) * (opt_h + opt_pad), opt_w, opt_h)
                    dropdown_rects.append((i, r))
                    pygame.draw.rect(surface, GRAY_50, r)
                    pygame.draw.rect(surface, WHITE, r, 1)
                    draw_text(surface, str(i), FONTS["sm"], WHITE, r.center, center=True)
                INVENTORY_STATE["dropdown"]["options"] = dropdown_rects

        header_h = 30
        pygame.draw.rect(surface, GRAY_30, (table_rect.x, table_rect.y, table_rect.width, header_h))
        pygame.draw.rect(surface, WHITE, (table_rect.x, table_rect.y, table_rect.width, header_h), 1)
        col_split = table_rect.x + 90
        pygame.draw.line(surface, WHITE, (col_split, table_rect.y), (col_split, table_rect.y + header_h))
        draw_text(surface, "imagem do item*", FONTS["xs"], WHITE, (table_rect.x + 6, table_rect.y + 8))
        draw_text(surface, "Nome do item*", FONTS["xs"], WHITE, (col_split + 6, table_rect.y + 8))

        INVENTORY_STATE["item_rows"] = []
        row_h = 60
        y_row = table_rect.y + header_h
        filtered_items = filter_inventory_items()
        row_index = 0
        available_rows = int((table_rect.height - header_h) // row_h)
        while row_index < available_rows and y_row + row_h <= table_rect.bottom:
            row_rect = pygame.Rect(table_rect.x, y_row, table_rect.width, row_h)
            pygame.draw.rect(surface, BLACK, row_rect)
            pygame.draw.rect(surface, WHITE, row_rect, 1)
            pygame.draw.line(surface, WHITE, (col_split, y_row), (col_split, y_row + row_h))

            if row_index < len(filtered_items):
                item_index, item = filtered_items[row_index]
                if INVENTORY_STATE.get("view_item_index") == item_index:
                    pygame.draw.rect(surface, GRAY_50, row_rect, 2)
                img = item.get("image_surface")
                if img:
                    thumb_w = col_split - table_rect.x - 12
                    thumb_h = row_h - 12
                    thumb_w = max(10, thumb_w)
                    thumb_h = max(10, thumb_h)
                    thumb = pygame.transform.smoothscale(img, (thumb_w, thumb_h))
                    thumb_rect = thumb.get_rect()
                    thumb_rect.center = (table_rect.x + (col_split - table_rect.x) // 2, y_row + row_h // 2)
                    surface.blit(thumb, thumb_rect)
                else:
                    placeholder_rect = pygame.Rect(table_rect.x + 8, y_row + 8, col_split - table_rect.x - 16, row_h - 16)
                    pygame.draw.rect(surface, GRAY_30, placeholder_rect, 1)
                    draw_text(surface, "sem imagem", FONTS["xs"], GRAY_70, placeholder_rect.center, center=True)

                name = item.get("name", "--") or "--"
                draw_text(surface, name, FONTS["sm_b"], WHITE, (col_split + 8, y_row + 6))
                meta_parts = []
                if item.get("category"):
                    meta_parts.append(item["category"])
                if item.get("dano"):
                    meta_parts.append(item["dano"])
                if item.get("space"):
                    meta_parts.append(f"Espaco {item['space']}")
                if item.get("tipo"):
                    meta_parts.append(f"Tipo {item['tipo']}")
                meta = " | ".join(meta_parts) if meta_parts else "--"
                draw_text(surface, meta, FONTS["xs"], GRAY_70, (col_split + 8, y_row + 28))
                roll_btn_rect = None
                if item.get("descricao"):
                    desc_preview = item["descricao"].strip().split("\n")[0]
                    draw_text(surface, desc_preview[:80], FONTS["xs"], GRAY_70, (col_split + 8, y_row + 44))
                dmg_info = parse_damage_die(item.get("dano"))
                if dmg_info:
                    btn_w = 64
                    btn_h = 22
                    roll_btn_rect = pygame.Rect(row_rect.right - btn_w - 8, y_row + row_h - btn_h - 6, btn_w, btn_h)
                    pygame.draw.rect(surface, GRAY_50, roll_btn_rect)
                    pygame.draw.rect(surface, WHITE, roll_btn_rect, 1)
                    draw_text(surface, "DANO", FONTS["xs"], WHITE, roll_btn_rect.center, center=True)
                INVENTORY_STATE["item_rows"].append(
                    {"index": item_index, "row_rect": row_rect, "roll_rect": roll_btn_rect}
                )
            y_row += row_h
            row_index += 1

        while y_row + row_h <= table_rect.bottom:
            pygame.draw.rect(surface, BLACK, (table_rect.x, y_row, table_rect.width, row_h))
            pygame.draw.rect(surface, WHITE, (table_rect.x, y_row, table_rect.width, row_h), 1)
            pygame.draw.line(surface, WHITE, (col_split, y_row), (col_split, y_row + row_h))
            y_row += row_h

        form_dropdown = INVENTORY_STATE.get("form_dropdown")
        if form_dropdown and INVENTORY_STATE.get("show_form"):
            field = form_dropdown.get("field")
            base_rect = INVENTORY_STATE["form"].get("rects", {}).get(field)
            options = FORM_DROPDOWN_OPTIONS.get(field, [])
            if base_rect and options:
                opt_h = 24
                opt_pad = 3
                opt_rects = []
                drop_height = len(options) * (opt_h + opt_pad)
                drop_y = base_rect.bottom + 4
                max_y = form_rect.bottom - 10
                if drop_y + drop_height > max_y:
                    drop_y = base_rect.top - drop_height - 4
                for idx_opt, opt in enumerate(options):
                    r = pygame.Rect(base_rect.x, drop_y + idx_opt * (opt_h + opt_pad), base_rect.width, opt_h)
                    pygame.draw.rect(surface, GRAY_50, r)
                    pygame.draw.rect(surface, WHITE, r, 1)
                    draw_text(surface, opt, FONTS["sm"], WHITE, (r.x + 6, r.y + 4))
                    opt_rects.append((opt, r))
                INVENTORY_STATE["form_dropdown"]["rects"] = opt_rects
            else:
                INVENTORY_STATE["form_dropdown"] = None
    else:
        INVENTORY_STATE["filter_buttons"] = []
        placeholder_rect = pygame.Rect(panel_x + content_pad, content_y + 10, panel_w - content_pad * 2, panel_h - (content_y + 20))
        pygame.draw.rect(surface, BLACK, placeholder_rect)
        pygame.draw.rect(surface, WHITE, placeholder_rect, 1)
        draw_text(surface, f"{INVENTORY_STATE['active_tab']} em construcao", FONTS["md"], WHITE, placeholder_rect.center, center=True)
        INVENTORY_STATE["form_dropdown"] = None
        INVENTORY_STATE["form"]["rects"] = {}

def draw_skills_panel(surface):
    panel_x = 14
    panel_y = 620
    panel_w = 1040
    panel_h = 440
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(surface, BLACK, panel_rect)
    pygame.draw.rect(surface, WHITE, panel_rect, 2)
    draw_text(surface, "PERICIAS", FONTS["md"], WHITE, (panel_rect.centerx, panel_rect.y + 6), center=True)

    categories = [("FISICA", "FISICAS"), ("INTELECTO", "INTELECTO"), ("SOCIAL", "SOCIAIS")]
    col_w = panel_w // 3
    start_y = panel_y + 30
    row_h = 24
    checkbox_size = 12

    for idx, (cat_key, cat_label) in enumerate(categories):
        col_x = panel_x + idx * col_w
        header_rect = pygame.Rect(col_x, start_y, col_w, 22)
        pygame.draw.rect(surface, BLACK, header_rect)
        pygame.draw.rect(surface, WHITE, header_rect, 1)
        draw_text(surface, cat_label, FONTS["sm"], WHITE, (col_x + 6, start_y + 4))
        y = start_y + 30
        skills = [s for s in SKILLS if s["cat"] == cat_key]
        for s in skills:
            locked = s["requires_training"] and not s["trained"]
            is_hover = UI_STATE.get("hover_skill") == s["name"]
            text_color = PURPLE if (is_hover and not locked) else (GREEN if s["trained"] else (GRAY_50 if locked else WHITE))
            s["choice_rects"] = None
            s["rect"] = None
            s["name_rect"] = None
            name_text = s["name"]
            attr_x = col_x + col_w - 30

            if s["cat"] == "SOCIAL" and s["requires_training"]:
                # somente duas caixas (+1/+2) à esquerda e texto à direita
                box_sz = 12
                base_x = col_x + 6
                cy = y
                rect1 = pygame.Rect(base_x, cy, box_sz, box_sz)
                rect2 = pygame.Rect(base_x + 42, cy, box_sz, box_sz)
                s["choice_rects"] = {"+1": rect1, "+2": rect2}
                base_color = GRAY_50 if locked else GRAY_30
                label_color = GRAY_70 if locked else WHITE
                for label, rect in [("+1", rect1), ("+2", rect2)]:
                    filled = (s["bonus_choice"] == 1 and label == "+1") or (s["bonus_choice"] == 2 and label == "+2")
                    pygame.draw.rect(surface, ORANGE if filled else base_color, rect)
                    pygame.draw.rect(surface, WHITE, rect, 1)
                    lbl_y = rect.centery - FONTS["md"].get_height() // 2
                    draw_text(surface, label, FONTS["md"], label_color, (rect.right + 5, lbl_y))
                label_w = FONTS["md"].size("+2")[0]
                name_x = rect2.right + 10 + label_w
            else:
                # caixa única normal alinhada à esquerda
                box_rect = pygame.Rect(col_x + 6, y, checkbox_size, checkbox_size)
                s["rect"] = box_rect
                box_color = GREEN if s["trained"] else (GRAY_50 if locked else GRAY_30)
                pygame.draw.rect(surface, box_color, box_rect)
                pygame.draw.rect(surface, WHITE, box_rect, 1)
                name_x = box_rect.right + 4

            s["name_rect"] = draw_text(surface, name_text, FONTS["md"], text_color, (name_x, y - 2))
            draw_text(surface, s["attr"], FONTS["sm"], text_color, (attr_x, y - 2))
            y += row_h



def draw_dice_panel(surface):
    panel_x = 1080
    panel_y = 820
    panel_w = BASE_WIDTH - panel_x - 20
    panel_h = 220
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(surface, BLACK, panel_rect)
    pygame.draw.rect(surface, WHITE, panel_rect, 2)
    draw_text(surface, "ROLAGENS", FONTS["md"], WHITE, (panel_rect.x + 10, panel_rect.y + 6))

    left_w = int(panel_w * 0.45)
    current_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 30, left_w - 10, panel_rect.height - 40)
    history_rect = pygame.Rect(current_rect.right + 10, panel_rect.y + 30, panel_rect.right - current_rect.right - 20, panel_rect.height - 40)

    # Atual
    pygame.draw.rect(surface, GRAY_30, current_rect)
    pygame.draw.rect(surface, WHITE, current_rect, 1)
    rolling = DICE_STATE["rolling"]
    entry = DICE_STATE["pending"] if rolling and DICE_STATE["pending"] else DICE_STATE["current"]
    if not entry:
        draw_text(surface, "Clique em um atributo, pericia ou botao de dano para rolar dados.", FONTS["xs"], WHITE, (current_rect.x + 8, current_rect.y + 10))
    else:
        roll_type = entry.get("roll_type", "").lower()
        type_label = {"skill": "Pericia", "attribute": "Atributo", "damage": "Dano"}.get(roll_type, roll_type.title() if roll_type else "")
        title = f"{entry['label']} ({type_label})"
        draw_text(surface, title, FONTS["sm"], WHITE, (current_rect.x + 8, current_rect.y + 8))

        dice_size = 48
        dice_gap = 8
        dice_start_x = current_rect.x + 10
        dice_y = current_rect.y + 30
        dice_values = DICE_STATE["display_dice"] if rolling else entry["dice"]
        config = entry.get("dice_config") or {"count": len(dice_values), "sides": 6}
        max_val = config.get("sides", 6)
        min_val = 1
        for i, val in enumerate(dice_values):
            drect = pygame.Rect(dice_start_x + i * (dice_size + dice_gap), dice_y, dice_size, dice_size)
            pygame.draw.rect(surface, GRAY_50, drect)
            pygame.draw.rect(surface, WHITE, drect, 1)
            color = WHITE
            if not rolling:
                if val >= max_val:
                    color = GREEN
                elif val <= min_val:
                    color = RED
            draw_text(surface, str(val), FONTS["lg"], color, drect.center, center=True)

        info_bottom = dice_y + dice_size
        if roll_type in ("attribute", "skill"):
            bonus_y = dice_y + dice_size + 8
            attr_rect = pygame.Rect(dice_start_x, bonus_y, 140, 26)
            pygame.draw.rect(surface, GRAY_50, attr_rect)
            pygame.draw.rect(surface, WHITE, attr_rect, 1)
            draw_text(surface, f"Atributo {entry['attr_value']:+}", FONTS["xs"], WHITE, (attr_rect.x + 6, attr_rect.y + 8))
            draw_text(surface, entry["attr_code"], FONTS["md"], WHITE, (attr_rect.right - 34, attr_rect.y + 4))
            info_bottom = attr_rect.bottom
            if roll_type == "skill":
                skill_rect = pygame.Rect(dice_start_x, attr_rect.bottom + 6, 140, 26)
                pygame.draw.rect(surface, GRAY_50, skill_rect)
                pygame.draw.rect(surface, WHITE, skill_rect, 1)
                skill_label = f"Treino {entry['skill_bonus']:+}" if entry["skill_bonus"] else "Sem treino"
                draw_text(surface, skill_label, FONTS["xs"], WHITE, (skill_rect.x + 6, skill_rect.y + 8))
                info_bottom = skill_rect.bottom
        elif roll_type == "damage":
            dmg_rect = pygame.Rect(dice_start_x, dice_y + dice_size + 8, 140, 26)
            pygame.draw.rect(surface, GRAY_50, dmg_rect)
            pygame.draw.rect(surface, WHITE, dmg_rect, 1)
            expr = entry.get("damage_expr", f"{config.get('count', 1)}D{config.get('sides', 6)}")
            draw_text(surface, f"Dado {expr}", FONTS["xs"], WHITE, (dmg_rect.x + 6, dmg_rect.y + 8))
            info_bottom = dmg_rect.bottom

        total_rect_w = 120
        total_rect_h = 48
        total_rect = pygame.Rect(current_rect.right - total_rect_w - 10, current_rect.y + 28, total_rect_w, total_rect_h)
        pygame.draw.rect(surface, GRAY_70, total_rect)
        pygame.draw.rect(surface, WHITE, total_rect, 1)
        draw_text(surface, "Total", FONTS["xs"], BLACK, (total_rect.centerx, total_rect.y + 6), center=True)
        total_text = "..." if rolling else str(entry["total"])
        draw_text(surface, total_text, FONTS["lg"], BLACK, (total_rect.centerx, total_rect.y + 24), center=True)

        summary = "Rolando..." if rolling else roll_summary(entry)
        draw_text(surface, summary, FONTS["xs"], WHITE, (dice_start_x, info_bottom + 8))

    # Histórico
    pygame.draw.rect(surface, GRAY_30, history_rect)
    pygame.draw.rect(surface, WHITE, history_rect, 1)
    history_font = FONTS["md"]
    entries = []
    if DICE_STATE["current"]:
        entries.append(DICE_STATE["current"])
    entries.extend(DICE_STATE["history"])
    entries = entries[:5]
    draw_text(surface, f"Histórico ({len(entries)})", history_font, WHITE, (history_rect.x + 8, history_rect.y + 6))
    hy = history_rect.y + 28
    if not entries:
        draw_text(surface, "Sem rolagens ainda.", history_font, GRAY_70, (history_rect.x + 8, hy))
    else:
        for entry in entries:
            summary = roll_summary(entry)
            lines, _ = wrap_text(summary, history_font, history_rect.width - 16)
            for line in lines:
                if hy + history_font.get_height() > history_rect.bottom - 6:
                    break
                draw_text(surface, line, history_font, WHITE, (history_rect.x + 8, hy))
                hy += history_font.get_height()
            hy += 6


def calc_transform(window_size):
    w, h = window_size
    scale = min(w / BASE_WIDTH, h / BASE_HEIGHT)
    offset_x = (w - BASE_WIDTH * scale) / 2
    offset_y = (h - BASE_HEIGHT * scale) / 2
    return scale, (offset_x, offset_y)


def calc_effort_cap(int_value):
    val = max(0, int_value)
    if val <= 2:
        return val * 2
    if val <= 5:
        return val * 3
    return val * 5


def sync_effort_with_int(int_value):
    """Atualiza o total automaticamente se não foi editado manualmente."""
    if not EFFORT_STATE["manual_total"]:
        new_total = calc_effort_cap(int_value)
        if EFFORT_STATE["total"] != new_total:
            EFFORT_STATE["total"] = new_total
            EFFORT_STATE["buffers"]["total"] = str(new_total)
            EFFORT_STATE["current"] = new_total
            EFFORT_STATE["buffers"]["current"] = str(new_total)
            EFFORT_STATE["bonus"] = 0
            EFFORT_STATE["buffers"]["bonus"] = "0"
    if EFFORT_STATE["current"] > EFFORT_STATE["total"]:
        EFFORT_STATE["current"] = EFFORT_STATE["total"]
        EFFORT_STATE["buffers"]["current"] = str(EFFORT_STATE["current"])


def apply_effort_buffer(field):
    """Converte buffer para número e aplica ao estado, clampando valores."""
    buf = EFFORT_STATE["buffers"][field].strip()
    try:
        val = int(buf) if buf else 0
    except ValueError:
        val = 0
    val = max(0, val)
    if field == "total":
        EFFORT_STATE["manual_total"] = True
        EFFORT_STATE["total"] = val
        EFFORT_STATE["current"] = val
        EFFORT_STATE["buffers"]["current"] = str(val)
        if EFFORT_STATE["bonus"] < 0:
            EFFORT_STATE["bonus"] = 0
            EFFORT_STATE["buffers"]["bonus"] = "0"
    else:
        if field == "current":
            EFFORT_STATE["current"] = min(val, EFFORT_STATE["total"])
            EFFORT_STATE["buffers"]["current"] = str(EFFORT_STATE["current"])
        elif field == "bonus":
            EFFORT_STATE["bonus"] = max(0, val)
            EFFORT_STATE["buffers"]["bonus"] = str(EFFORT_STATE["bonus"])


def apply_effort_delta(delta):
    """Aplica variação via botões: primeiro no bônus se houver; se zerar, passa a afetar o atual."""
    if delta == 0:
        return
    # Operação em bônus
    if delta > 0:
        if EFFORT_STATE["bonus"] > 0:
            EFFORT_STATE["bonus"] += delta
            EFFORT_STATE["buffers"]["bonus"] = str(EFFORT_STATE["bonus"])
            return
    else:  # delta negativo
        if EFFORT_STATE["bonus"] > 0:
            new_bonus = EFFORT_STATE["bonus"] + delta
            if new_bonus >= 0:
                EFFORT_STATE["bonus"] = new_bonus
                EFFORT_STATE["buffers"]["bonus"] = str(EFFORT_STATE["bonus"])
                return
            # sobra negativa vai para o atual
            EFFORT_STATE["bonus"] = 0
            EFFORT_STATE["buffers"]["bonus"] = "0"
            delta = new_bonus  # negativo, magnitude restante
    # Ajusta atual com clamp ao total e zero
    EFFORT_STATE["current"] = max(0, min(EFFORT_STATE["total"], EFFORT_STATE["current"] + delta))
    EFFORT_STATE["buffers"]["current"] = str(EFFORT_STATE["current"])


def main():
    global WINDOW
    # Estado simples dos atributos
    for attr in ATTRIBUTES:
        attr["value"] = 0
    EFFORT_STATE["manual_total"] = False
    EFFORT_STATE["current"] = 0
    EFFORT_STATE["total"] = calc_effort_cap(0)
    EFFORT_STATE["bonus"] = 0
    EFFORT_STATE["buffers"]["current"] = "0"
    EFFORT_STATE["buffers"]["total"] = str(EFFORT_STATE["total"])
    EFFORT_STATE["buffers"]["bonus"] = "0"
    EFFORT_STATE["focus"] = None
    INVENTORY_STATE["limit_values"] = [0, 0, 0, 0, 0]
    INVENTORY_STATE["total_values"] = [0, 0, 0, 0, 0]
    INVENTORY_STATE["dropdown"] = None
    INVENTORY_STATE["show_form"] = False

    running = True
    while running:
        scale, offset = calc_transform(WINDOW.get_size())
        # Atualiza hovers com base na posição atual do mouse
        mouse_base = window_to_canvas(pygame.mouse.get_pos(), scale, offset)
        UI_STATE["hover_attr"] = None
        UI_STATE["hover_skill"] = None
        if mouse_base:
            for attr in ATTRIBUTES:
                if attr.get("value_rect") and attr["value_rect"].collidepoint(mouse_base):
                    UI_STATE["hover_attr"] = attr["code"]
                    break
            for s in SKILLS:
                locked = s.get("requires_training") and not s.get("trained")
                if locked:
                    continue
                if s.get("name_rect") and s["name_rect"].collidepoint(mouse_base):
                    UI_STATE["hover_skill"] = s["name"]
                    break
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                WINDOW = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    continue
                if NOTE_STATE["focus"]:
                    field = NOTE_STATE["focus"]
                    if event.key == pygame.K_BACKSPACE:
                        note_backspace(field)
                    elif event.key == pygame.K_DELETE:
                        note_delete(field)
                    elif event.key == pygame.K_RETURN:
                        if field == "body":
                            note_insert_text(field, "\n")
                    elif event.key == pygame.K_LEFT:
                        note_move_cursor(field, "left")
                    elif event.key == pygame.K_RIGHT:
                        note_move_cursor(field, "right")
                    elif event.key == pygame.K_HOME:
                        note_move_cursor(field, "home")
                    elif event.key == pygame.K_END:
                        note_move_cursor(field, "end")
                    elif event.key == pygame.K_UP:
                        note_move_cursor(field, "up")
                    elif event.key == pygame.K_DOWN:
                        note_move_cursor(field, "down")
                    elif event.unicode and event.unicode.isprintable():
                        note_insert_text(field, event.unicode)
                    continue
                form_focus = INVENTORY_STATE["form"].get("focus") if INVENTORY_STATE.get("show_form") else None
                if form_focus:
                    text_fields = FORM_TEXT_FIELDS.union(FORM_MULTILINE_FIELDS)
                    if event.key == pygame.K_ESCAPE:
                        INVENTORY_STATE["form"]["focus"] = None
                    elif event.key == pygame.K_BACKSPACE:
                        form_backspace(form_focus)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if form_focus in FORM_MULTILINE_FIELDS:
                            form_insert_text(form_focus, "\n")
                        else:
                            INVENTORY_STATE["form"]["focus"] = None
                    elif event.key == pygame.K_TAB:
                        pass
                    elif event.unicode and event.unicode.isprintable() and form_focus in text_fields:
                        if event.unicode not in ("\r", "\n"):
                            form_insert_text(form_focus, event.unicode)
                        elif event.unicode == "\n" and form_focus in FORM_MULTILINE_FIELDS:
                            form_insert_text(form_focus, "\n")
                    continue
                if EFFORT_STATE["focus"]:
                    field = EFFORT_STATE["focus"]
                    if event.key == pygame.K_RETURN:
                        apply_effort_buffer(field)
                        EFFORT_STATE["focus"] = None
                    elif event.key == pygame.K_BACKSPACE:
                        buf = EFFORT_STATE["buffers"][field]
                        EFFORT_STATE["buffers"][field] = buf[:-1]
                    elif event.unicode and event.unicode.isdigit():
                        buf = EFFORT_STATE["buffers"][field]
                        if len(buf) < 6:
                            EFFORT_STATE["buffers"][field] = buf + event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos_base = window_to_canvas(event.pos, scale, offset)
                if pos_base:
                    # Dropdown de inventário: clique em opções
                    if INVENTORY_STATE.get("dropdown") and INVENTORY_STATE["dropdown"].get("options"):
                        handled_dropdown = False
                        for val, rect in INVENTORY_STATE["dropdown"]["options"]:
                            if rect.collidepoint(pos_base):
                                idx = INVENTORY_STATE["dropdown"].get("index")
                                if idx is not None and 0 <= idx < len(INVENTORY_STATE["limit_values"]):
                                    INVENTORY_STATE["limit_values"][idx] = val
                                INVENTORY_STATE["dropdown"] = None
                                handled_dropdown = True
                                break
                        if not handled_dropdown:
                            # Fechar dropdown se clicou fora dele
                            INVENTORY_STATE["dropdown"] = None
                    form_dropdown = INVENTORY_STATE.get("form_dropdown")
                    if form_dropdown and form_dropdown.get("rects"):
                        handled_form_dropdown = False
                        for val, rect in form_dropdown["rects"]:
                            if rect.collidepoint(pos_base):
                                field = form_dropdown.get("field")
                                if field:
                                    INVENTORY_STATE["form"][field] = val
                                INVENTORY_STATE["form_dropdown"] = None
                                handled_form_dropdown = True
                                break
                        if handled_form_dropdown:
                            continue
                        INVENTORY_STATE["form_dropdown"] = None

                    prev_focus = EFFORT_STATE["focus"]
                    if prev_focus:
                        apply_effort_buffer(prev_focus)
                    EFFORT_STATE["focus"] = None
                    NOTE_STATE["focus"] = None
                    INVENTORY_STATE["form"]["focus"] = None
                    for attr in ATTRIBUTES:
                        old_val = attr["value"]
                        if attr.get("minus_rect") and attr["minus_rect"].collidepoint(pos_base):
                            attr["value"] = max(-6, attr["value"] - 1)
                        if attr.get("plus_rect") and attr["plus_rect"].collidepoint(pos_base):
                            attr["value"] = min(6, attr["value"] + 1)
                        if attr["code"] == "INT" and attr["value"] != old_val:
                            EFFORT_STATE["manual_total"] = False
                        if attr.get("value_rect") and attr["value_rect"].collidepoint(pos_base):
                            roll_attribute(attr)
                    for track_key, idx, rect in LIFE_RECTS:
                        if rect.collidepoint(pos_base):
                            marks = LIFE_MARKS.get(track_key, [])
                            if idx < len(marks):
                                marks[idx] = not marks[idx]
                    for track_key, idx, rect in SAN_RECTS:
                        if rect.collidepoint(pos_base):
                            marks = SAN_MARKS.get(track_key, [])
                            if idx < len(marks):
                                marks[idx] = not marks[idx]
                    for dtype, idx, rect in SAN_SAVE_RECTS:
                        if rect.collidepoint(pos_base):
                            SAN_SAVES[dtype][idx] = not SAN_SAVES[dtype][idx]
                    for dtype, idx, rect in DEATH_RECTS:
                        if rect.collidepoint(pos_base):
                            DEATH_SAVES[dtype][idx] = not DEATH_SAVES[dtype][idx]
                    # Anotacoes
                    for field, rect in NOTE_STATE["rects"].items():
                        if rect.collidepoint(pos_base):
                            NOTE_STATE["focus"] = field
                            NOTE_STATE["cursor"][field] = len(NOTE_STATE[field])
                            break
                    if NOTE_STATE["send_rect"] and NOTE_STATE["send_rect"].collidepoint(pos_base):
                        _note = send_note_payload()
                        # Futuro: integrar _note com menu/listagem de anotações
                        NOTE_STATE["title"] = ""
                        NOTE_STATE["subject"] = ""
                        NOTE_STATE["body"] = ""
                        NOTE_STATE["scroll"] = 0
                        NOTE_STATE["focus"] = None
                        NOTE_STATE["cursor"] = {"title": 0, "subject": 0, "body": 0}
                    # Skills toggles
                    for s in SKILLS:
                        clicked = False
                        if s.get("choice_rects"):
                            for label, rect in s["choice_rects"].items():
                                if rect.collidepoint(pos_base):
                                    choice = 1 if label == "+1" else 2
                                    if s["bonus_choice"] == choice:
                                        s["bonus_choice"] = None
                                        s["bonus"] = 0
                                        s["trained"] = False
                                    else:
                                        s["bonus_choice"] = choice
                                        s["bonus"] = choice
                                        s["trained"] = True
                                    clicked = True
                                    break
                        if not clicked and s.get("rect") and s["rect"].collidepoint(pos_base):
                            s["trained"] = not s["trained"]
                            clicked = True
                        if not clicked and s.get("name_rect") and s["name_rect"].collidepoint(pos_base):
                            roll_skill(s)
                            clicked = True
                        if clicked:
                            break
                    # Esforço: campos e botões
                    for field, rect in EFFORT_STATE["input_rects"].items():
                        if rect.collidepoint(pos_base):
                            EFFORT_STATE["focus"] = field
                            break
                    if not EFFORT_STATE["focus"]:
                        for rect, val in EFFORT_STATE["btn_rects"]:
                            if rect.collidepoint(pos_base):
                                apply_effort_delta(val)
                                break
                    # Inventário: caixas de limite abrem dropdown
                    for idx, rect in enumerate(INVENTORY_STATE["limit_rects"]):
                        if rect.collidepoint(pos_base):
                            INVENTORY_STATE["dropdown"] = {"type": "limit", "index": idx, "options": []}
                            break
                    # Inventario: campos do formulario
                    form_handled = False
                    if INVENTORY_STATE.get("show_form"):
                        form_rects = INVENTORY_STATE["form"].get("rects", {})
                        if form_rects:
                            img_rect = form_rects.get("image")
                            if img_rect and img_rect.collidepoint(pos_base):
                                image_path, image_surface = select_inventory_image()
                                if image_path and image_surface:
                                    INVENTORY_STATE["form"]["image_path"] = image_path
                                    INVENTORY_STATE["form"]["image_surface"] = image_surface
                                form_handled = True
                            else:
                                text_fields = FORM_TEXT_FIELDS.union(FORM_MULTILINE_FIELDS)
                                for field in text_fields:
                                    rect = form_rects.get(field)
                                    if rect and rect.collidepoint(pos_base):
                                        INVENTORY_STATE["form"]["focus"] = field
                                        INVENTORY_STATE["form_dropdown"] = None
                                        form_handled = True
                                        break
                            if not form_handled:
                                for field in FORM_DROPDOWN_OPTIONS.keys():
                                    rect = form_rects.get(field)
                                    if rect and rect.collidepoint(pos_base):
                                        INVENTORY_STATE["form_dropdown"] = {"field": field, "rects": []}
                                        form_handled = True
                                        break
                    if INVENTORY_STATE.get("show_form") and not form_handled:
                        buttons = INVENTORY_STATE.get("form_buttons", {})
                        save_rect = buttons.get("save")
                        cancel_rect = buttons.get("cancel")
                        if save_rect and save_rect.collidepoint(pos_base):
                            add_inventory_item_from_form()
                            form_handled = True
                        elif cancel_rect and cancel_rect.collidepoint(pos_base):
                            cancel_inventory_form()
                            form_handled = True
                    if (
                        not INVENTORY_STATE.get("show_form")
                        and INVENTORY_STATE.get("view_item_index") is not None
                        and not form_handled
                    ):
                        summary_buttons = INVENTORY_STATE.get("summary_buttons", {})
                        close_rect = summary_buttons.get("close")
                        edit_rect = summary_buttons.get("edit")
                        remove_rect = summary_buttons.get("remove")
                        idx_summary = summary_buttons.get("index")
                        if close_rect and close_rect.collidepoint(pos_base):
                            close_inventory_summary()
                            form_handled = True
                        elif edit_rect and edit_rect.collidepoint(pos_base):
                            idx = idx_summary
                            items = INVENTORY_STATE.get("items", [])
                            if idx is not None and 0 <= idx < len(items):
                                item = items[idx]
                                form = INVENTORY_STATE["form"]
                                for key in ["name", "category", "space", "tipo", "alcance", "empunhadura", "dano", "localizacao", "descricao", "info1", "info2"]:
                                    form[key] = item.get(key, "")
                                form["image_path"] = item.get("image_path", "")
                                form["image_surface"] = item.get("image_surface")
                                form["rects"] = {}
                                form["focus"] = None
                                INVENTORY_STATE["editing_index"] = idx
                                INVENTORY_STATE["show_form"] = True
                                INVENTORY_STATE["view_item_index"] = None
                                INVENTORY_STATE["form_dropdown"] = None
                                INVENTORY_STATE["form_error"] = ""
                                INVENTORY_STATE["summary_buttons"] = {}
                                form_handled = True
                        elif remove_rect and remove_rect.collidepoint(pos_base):
                            if idx_summary is not None:
                                remove_inventory_item(idx_summary)
                            form_handled = True
                    if form_handled:
                        continue
                    filter_clicked = False
                    if INVENTORY_STATE.get("active_tab") == "INVENTARIO":
                        for tag, rect in INVENTORY_STATE.get("filter_buttons", []):
                            if rect.collidepoint(pos_base):
                                current = INVENTORY_STATE.get("category_filter")
                                INVENTORY_STATE["category_filter"] = None if current == tag else tag
                                INVENTORY_STATE["view_item_index"] = None
                                INVENTORY_STATE["summary_buttons"] = {}
                                filter_clicked = True
                                break
                    if filter_clicked:
                        continue
                    clicked_row = None
                    handled_row_action = False
                    for row_info in INVENTORY_STATE.get("item_rows", []):
                        roll_rect = row_info.get("roll_rect")
                        if roll_rect and roll_rect.collidepoint(pos_base):
                            roll_inventory_item_damage(row_info.get("index"))
                            handled_row_action = True
                            break
                        row_rect = row_info.get("row_rect")
                        if row_rect and row_rect.collidepoint(pos_base):
                            clicked_row = row_info.get("index")
                            break
                    if handled_row_action:
                        continue
                    if clicked_row is not None:
                        INVENTORY_STATE["view_item_index"] = clicked_row
                        INVENTORY_STATE["show_form"] = False
                        INVENTORY_STATE["form_dropdown"] = None
                        INVENTORY_STATE["summary_buttons"] = {}
                        continue
                    # Inventário: abas
                    for label, rect in INVENTORY_STATE["tab_rects"]:
                        if rect.collidepoint(pos_base):
                            INVENTORY_STATE["active_tab"] = label
                            INVENTORY_STATE["dropdown"] = None
                            INVENTORY_STATE["show_form"] = False
                            INVENTORY_STATE["form_dropdown"] = None
                            INVENTORY_STATE["view_item_index"] = None
                            INVENTORY_STATE["summary_buttons"] = {}
                            break
                    # Inventário: botão adicionar abre formulário da esquerda
                    add_rect = INVENTORY_STATE.get("add_rect")
                    if add_rect and add_rect.collidepoint(pos_base):
                        if not INVENTORY_STATE.get("show_form"):
                            reset_inventory_form()
                            close_inventory_summary()
                        INVENTORY_STATE["show_form"] = True
            elif event.type == pygame.MOUSEWHEEL:
                mouse_pos = getattr(event, "pos", pygame.mouse.get_pos())
                pos_base = window_to_canvas(mouse_pos, scale, offset)
                if pos_base and "body" in NOTE_STATE["rects"]:
                    body_rect = NOTE_STATE["rects"]["body"]
                    if body_rect.collidepoint(pos_base):
                        NOTE_STATE["scroll"] = max(
                            0, min(NOTE_STATE["max_scroll"], NOTE_STATE["scroll"] - event.y * 2)
                        )

        update_dice_roll()
        # Desenha na canvas base
        CANVAS.fill(BLACK)
        draw_attribute_column(CANVAS)
        draw_vitals_panel(CANVAS)
        draw_notes_panel(CANVAS)
        draw_inventory_panel(CANVAS)
        draw_skills_panel(CANVAS)
        draw_dice_panel(CANVAS)

        # Escala para a janela atual mantendo proporção
        scaled_surface = pygame.transform.smoothscale(
            CANVAS, (int(BASE_WIDTH * scale), int(BASE_HEIGHT * scale))
        )
        WINDOW.fill(BLACK)
        WINDOW.blit(scaled_surface, offset)
        pygame.display.flip()
        CLOCK.tick_busy_loop(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
