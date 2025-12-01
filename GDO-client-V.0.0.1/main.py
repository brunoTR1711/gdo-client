import sys
import math
import pygame

# Dimensões base do layout original
BASE_WIDTH = 1920
BASE_HEIGHT = 1080
START_WIDTH = 800
START_HEIGHT = 600

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
ORANGE = (240, 140, 0)
GREEN = (0, 180, 0)
RED = (210, 40, 40)

# Fontes
FONTS = {
    "xs": pygame.font.SysFont("arial", 12),
    "sm": pygame.font.SysFont("arial", 14),
    "md": pygame.font.SysFont("arial", 18, bold=True),
    "lg": pygame.font.SysFont("arial", 28, bold=True),
    "xl": pygame.font.SysFont("arial", 52, bold=True),
}

# Estado dos atributos (valor e retângulos dos botões serão preenchidos a cada draw)
ATTRIBUTES = [
    {"code": "VIG", "name": "Vigor", "value": 0, "minus_rect": None, "plus_rect": None},
    {"code": "FOR", "name": "Força", "value": 0, "minus_rect": None, "plus_rect": None},
    {"code": "AGI", "name": "Agilidade", "value": 0, "minus_rect": None, "plus_rect": None},
    {"code": "INT", "name": "Intelecto", "value": 0, "minus_rect": None, "plus_rect": None},
    {"code": "PRE", "name": "Presença", "value": 0, "minus_rect": None, "plus_rect": None},
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
    {"name": "Pilotagem", "attr": "AGI", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Furtividade", "attr": "AGI", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Iniciativa", "attr": "AGI", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Crime*", "attr": "AGI", "cat": "FISICA", "requires_training": True, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Reflexo", "attr": "AGI", "cat": "FISICA", "requires_training": True, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Atletismo", "attr": "FOR", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Lutar", "attr": "FOR", "cat": "FISICA", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Fortitude", "attr": "VIG", "cat": "FISICA", "requires_training": True, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Esquiva*", "attr": "AGI", "cat": "FISICA", "requires_training": True, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Contra-Ataque*", "attr": "FOR", "cat": "FISICA", "requires_training": True, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Bloqueio*", "attr": "VIG", "cat": "FISICA", "requires_training": True, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    # Intelecto
    {"name": "Atualidade*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Ciencia*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Intuicao", "attr": "INT", "cat": "INTELECTO", "requires_training": False, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Investigacao", "attr": "INT", "cat": "INTELECTO", "requires_training": False, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Medicina*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Ocultismo*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Profissao*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Sobrevivencia", "attr": "INT", "cat": "INTELECTO", "requires_training": False, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Tatica*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Tecnologia*", "attr": "INT", "cat": "INTELECTO", "requires_training": True, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    # Sociais
    {"name": "Adestramento", "attr": "PRE", "cat": "SOCIAL", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Artes*", "attr": "PRE", "cat": "SOCIAL", "requires_training": True, "bonus": 2, "bonus_choice": None, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Diplomacia*", "attr": "PRE", "cat": "SOCIAL", "requires_training": True, "bonus": 1, "bonus_choice": None, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Enganacao", "attr": "PRE", "cat": "SOCIAL", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Intimidacao", "attr": "PRE", "cat": "SOCIAL", "requires_training": False, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Percepcao", "attr": "PRE", "cat": "SOCIAL", "requires_training": False, "bonus": 1, "bonus_choice": 1, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Religiao*", "attr": "PRE", "cat": "SOCIAL", "requires_training": True, "bonus": 2, "bonus_choice": None, "trained": False, "rect": None, "choice_rects": None},
    {"name": "Vontade", "attr": "PRE", "cat": "SOCIAL", "requires_training": False, "bonus": 2, "bonus_choice": 2, "trained": False, "rect": None, "choice_rects": None},
]

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
        value_rect = pygame.Rect(rect.x + 4, rect.y + 4, 70, rect.height - 8)
        pygame.draw.rect(surface, BLACK, value_rect)
        draw_text(surface, str(value), FONTS["xl"], WHITE, value_rect.center, center=True)

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
            text_color = GREEN if s["trained"] else WHITE
            s["choice_rects"] = None
            s["rect"] = None
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
                for label, rect in [("+1", rect1), ("+2", rect2)]:
                    filled = (s["bonus_choice"] == 1 and label == "+1") or (s["bonus_choice"] == 2 and label == "+2")
                    pygame.draw.rect(surface, ORANGE if filled else GRAY_30, rect)
                    pygame.draw.rect(surface, WHITE, rect, 1)
                    lbl_y = rect.centery - FONTS["md"].get_height() // 2
                    draw_text(surface, label, FONTS["md"], WHITE, (rect.right + 5, lbl_y))
                label_w = FONTS["md"].size("+2")[0]
                name_x = rect2.right + 10 + label_w
            else:
                # caixa única normal alinhada à esquerda
                box_rect = pygame.Rect(col_x + 6, y, checkbox_size, checkbox_size)
                s["rect"] = box_rect
                box_color = GREEN if s["trained"] else GRAY_30
                pygame.draw.rect(surface, box_color, box_rect)
                pygame.draw.rect(surface, WHITE, box_rect, 1)
                name_x = box_rect.right + 4

            draw_text(surface, name_text, FONTS["md"], text_color, (name_x, y - 2))
            draw_text(surface, s["attr"], FONTS["sm"], text_color, (attr_x, y - 2))
            y += row_h


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

    running = True
    while running:
        scale, offset = calc_transform(WINDOW.get_size())
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
                    prev_focus = EFFORT_STATE["focus"]
                    if prev_focus:
                        apply_effort_buffer(prev_focus)
                    EFFORT_STATE["focus"] = None
                    NOTE_STATE["focus"] = None
                    for attr in ATTRIBUTES:
                        old_val = attr["value"]
                        if attr.get("minus_rect") and attr["minus_rect"].collidepoint(pos_base):
                            attr["value"] = max(-6, attr["value"] - 1)
                        if attr.get("plus_rect") and attr["plus_rect"].collidepoint(pos_base):
                            attr["value"] = min(6, attr["value"] + 1)
                        if attr["code"] == "INT" and attr["value"] != old_val:
                            EFFORT_STATE["manual_total"] = False
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
                        elif s.get("rect") and s["rect"].collidepoint(pos_base):
                            s["trained"] = not s["trained"]
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
            elif event.type == pygame.MOUSEWHEEL:
                mouse_pos = getattr(event, "pos", pygame.mouse.get_pos())
                pos_base = window_to_canvas(mouse_pos, scale, offset)
                if pos_base and "body" in NOTE_STATE["rects"]:
                    body_rect = NOTE_STATE["rects"]["body"]
                    if body_rect.collidepoint(pos_base):
                        NOTE_STATE["scroll"] = max(
                            0, min(NOTE_STATE["max_scroll"], NOTE_STATE["scroll"] - event.y * 2)
                        )

        # Desenha na canvas base
        CANVAS.fill(BLACK)
        draw_attribute_column(CANVAS)
        draw_vitals_panel(CANVAS)
        draw_notes_panel(CANVAS)
        draw_skills_panel(CANVAS)

        # Escala para a janela atual mantendo proporção
        scaled_surface = pygame.transform.smoothscale(
            CANVAS, (int(BASE_WIDTH * scale), int(BASE_HEIGHT * scale))
        )
        WINDOW.fill(BLACK)
        WINDOW.blit(scaled_surface, offset)
        pygame.display.flip()
        CLOCK.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
