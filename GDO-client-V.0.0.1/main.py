import sys
import pygame

# Dimensões base do layout original
BASE_WIDTH = 1908
BASE_HEIGHT = 901
START_WIDTH = 1400
START_HEIGHT = 900

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
      VIG=6 -> LEVE 7, FERIDO 5, MACHUCADO 3, MORRENDO 1
      VIG=0 -> mínimo 1 em todas
    """
    mapping = {
        "LEVE": 1,
        "FERIDO": -1,
        "MACHUCADO": -3,
        "MORRENDO": -5,
    }
    counts = {}
    for key, offset in mapping.items():
        counts[key] = max(1, min(7, vigor_value + offset))
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
    Contagem das caixas de sanidade baseada em Presença (PRE).
    Regras iguais às de vida: 7/5/3/1 no máximo (PRE 6), mínimo 1.
    """
    mapping = {
        "ESTÁVEL": 1,
        "INSTÁVEL": -1,
        "PERTURBADO": -3,
        "ENLOUQUECENDO": -5,
    }
    counts = {}
    for key, offset in mapping.items():
        counts[key] = max(1, min(7, pres_value + offset))
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


def draw_death_saves(surface, card_rect):
    """Desenha resistência à morte com o visual solicitado, centralizado dentro do card."""
    global DEATH_RECTS
    DEATH_RECTS.clear()
    radius = 8
    spacing = 18
    block_gap = 70
    block_width = (radius * 2 + spacing * 2)  # largura aproximada de 3 círculos
    total_width = block_width * 2 + block_gap
    x = card_rect.x + (card_rect.width - total_width) // 2
    y = card_rect.bottom - 56

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


def draw_sanity_saves(surface, card_rect):
    """Resistência à loucura, espelhando a de morte."""
    global SAN_SAVE_RECTS
    SAN_SAVE_RECTS.clear()
    radius = 8
    spacing = 18
    block_gap = 70
    block_width = (radius * 2 + spacing * 2)
    total_width = block_width * 2 + block_gap
    x = card_rect.x + (card_rect.width - total_width) // 2
    y = card_rect.bottom - 56

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
    row_h = 22
    box_size = 12
    box_step = box_size + 4
    label_x = life_rect.x + 14
    max_boxes = max(counts.values()) if counts else 1
    max_width = box_size + (max_boxes - 1) * box_step
    box_x = life_rect.right - 12 - max_width
    for idx, key in enumerate(LIFE_TRACKS):
        y = start_y + idx * row_h
        draw_text(surface, key.title(), FONTS["xs"], WHITE, (label_x, y))
        marks = LIFE_MARKS[key]
        for j in range(counts[key]):
            brect = pygame.Rect(box_x + j * (box_size + 4), y, box_size, box_size)
            pygame.draw.rect(surface, RED, brect)
            pygame.draw.rect(surface, WHITE, brect, 1)
            if marks[j]:
                pygame.draw.line(surface, WHITE, (brect.x + 2, brect.y + 2), (brect.right - 2, brect.bottom - 2), 2)
                pygame.draw.line(surface, WHITE, (brect.right - 2, brect.y + 2), (brect.x + 2, brect.bottom - 2), 2)
            LIFE_RECTS.append((key, j, brect))

    # Resistência à morte aparece apenas quando alguma caixa de MORRENDO está marcada
    if any(LIFE_MARKS["MORRENDO"]):
        draw_death_saves(surface, life_rect)

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
    s_row_h = 22
    s_box_size = 12
    s_box_step = s_box_size + 4
    s_label_x = san_rect.x + 14
    s_max_boxes = max(san_counts.values()) if san_counts else 1
    s_max_width = s_box_size + (s_max_boxes - 1) * s_box_step
    s_box_x = san_rect.right - 12 - s_max_width
    for idx, key in enumerate(SAN_TRACKS):
        y = s_start_y + idx * s_row_h
        draw_text(surface, key.title(), FONTS["xs"], WHITE, (s_label_x, y))
        marks = SAN_MARKS[key]
        for j in range(san_counts[key]):
            brect = pygame.Rect(s_box_x + j * s_box_step, y, s_box_size, s_box_size)
            pygame.draw.rect(surface, RED, brect)
            pygame.draw.rect(surface, WHITE, brect, 1)
            if marks[j]:
                pygame.draw.line(surface, WHITE, (brect.x + 2, brect.y + 2), (brect.right - 2, brect.bottom - 2), 2)
                pygame.draw.line(surface, WHITE, (brect.right - 2, brect.y + 2), (brect.x + 2, brect.bottom - 2), 2)
            SAN_RECTS.append((key, j, brect))

    # Resistência à loucura aparece apenas quando alguma caixa de ENLOUQUECENDO está marcada
    if any(SAN_MARKS["ENLOUQUECENDO"]):
        draw_sanity_saves(surface, san_rect)

    # Esforço
    effort_rect = pygame.Rect(base_x, base_y + card_h + 12, card_w * 2 + 10, 88)
    pygame.draw.rect(surface, BLACK, effort_rect)
    pygame.draw.rect(surface, WHITE, effort_rect, 2)
    draw_text(surface, "ESFORÇO", FONTS["md"], WHITE, (effort_rect.x + 10, effort_rect.y + 8))

    bar_rect = pygame.Rect(effort_rect.x + 10, effort_rect.y + 42, effort_rect.width - 20, 16)
    pygame.draw.rect(surface, ORANGE, bar_rect)
    draw_text(surface, "000/000", FONTS["xs"], BLACK, (bar_rect.right - 70, bar_rect.y))

    offsets = [-5, -2, -1, 1, 2, 5]
    btn_w, btn_h = 48, 18
    for i, val in enumerate(offsets):
        bx = effort_rect.x + 10 + i * 52
        by = effort_rect.y + 62
        brect = pygame.Rect(bx, by, btn_w, btn_h)
        pygame.draw.rect(surface, GRAY_30, brect)
        pygame.draw.rect(surface, GRAY_70, brect, 1)
        draw_text(surface, f"{val:+}", FONTS["xs"], WHITE, brect.center, center=True)


def calc_transform(window_size):
    w, h = window_size
    scale = min(w / BASE_WIDTH, h / BASE_HEIGHT)
    offset_x = (w - BASE_WIDTH * scale) / 2
    offset_y = (h - BASE_HEIGHT * scale) / 2
    return scale, (offset_x, offset_y)


def main():
    global WINDOW
    # Estado simples dos atributos
    for attr in ATTRIBUTES:
        attr["value"] = 0

    running = True
    while running:
        scale, offset = calc_transform(WINDOW.get_size())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                WINDOW = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos_base = window_to_canvas(event.pos, scale, offset)
                if pos_base:
                    for attr in ATTRIBUTES:
                        if attr.get("minus_rect") and attr["minus_rect"].collidepoint(pos_base):
                            attr["value"] = max(-6, attr["value"] - 1)
                        if attr.get("plus_rect") and attr["plus_rect"].collidepoint(pos_base):
                            attr["value"] = min(6, attr["value"] + 1)
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

        # Desenha na canvas base
        CANVAS.fill(BLACK)
        draw_attribute_column(CANVAS)
        draw_vitals_panel(CANVAS)

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
