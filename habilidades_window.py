import sys
import math
import pygame

# Dimensoes base
WIDTH, HEIGHT = 755, 700
FPS = 60

# Cores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY_20 = (35, 35, 35)
GRAY_40 = (70, 70, 70)
GRAY_60 = (110, 110, 110)
GRAY_80 = (170, 170, 170)
PURPLE = (180, 0, 200)
ORANGE = (240, 140, 0)
GREEN = (0, 200, 0)
RED = (200, 40, 40)

pygame.init()
pygame.display.set_caption("Painel de Habilidades (demo)")
WINDOW = None
CLOCK = pygame.time.Clock()

FONTS = {
    "xs": pygame.font.SysFont("arial", 12),
    "sm": pygame.font.SysFont("arial", 14),
    "sm_b": pygame.font.SysFont("arial", 14, bold=True),
    "md": pygame.font.SysFont("arial", 18, bold=True),
    "lg": pygame.font.SysFont("arial", 28, bold=True),
}


def wrap_text(text, font, max_width):
    lines = []
    current = ""
    for word in text.split(" "):
        candidate = (current + " " + word).strip() if current else word
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def wrap_text_with_starts(text, font, max_width):
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
                    start_idx += len(current) + 1
                current = word
        lines.append(current)
        line_starts.append(start_idx)
    return lines, line_starts


DEFAULT_ABILITIES = [
    {
        "name": "Contra-ataque",
        "tipo": "Combate",
        "custo": "1 PE",
        "bonus": "+2",
        "dano": "1D6 + FOR",
        "resumo": "Reage a um ataque corpo a corpo.",
        "descricao": "Quando um alvo errar um ataque corpo a corpo em voce, gaste 1 PE para realizar um contra-ataque imediato.",
        "categoria": "COMBATE",
    },
    {
        "name": "Discurso Inspirador",
        "tipo": "Narrativa",
        "custo": "2 PE",
        "bonus": "+1 aliados",
        "dano": "",
        "resumo": "Discursar para motivar o grupo.",
        "descricao": "Aliados que ouvirem recebem +1 em testes sociais ate o fim da cena.",
        "categoria": "NARRATIVA",
    },
    {
        "name": "Estouro Arcano",
        "tipo": "Magika",
        "custo": "3 PE",
        "bonus": "",
        "dano": "2D6 + INT",
        "resumo": "Explosao de energia.",
        "descricao": "Causa dano de energia em area pequena. Alvos fazem teste de Reflexo para metade.",
        "categoria": "MAGIKA",
    },
]


HABILIDADES_STATE = {
    "tabs": ["GERAL", "INVENTARIO", "HABILIDADES", "ANOTACOES"],
    "active_tab": "HABILIDADES",
    "filter": None,
    "abilities": [dict(item) for item in DEFAULT_ABILITIES],
    "selected": None,
    "form": {
        "name": "",
        "tipo": "",
        "custo": "",
        "bonus": "",
        "dano": "",
        "resumo": "",
        "descricao": "",
        "categoria": "",
    },
    "dropdown": None,  # {"field": str, "rects": [(opt, rect)]}
    "focus": None,
    "error": "",
    "show_form": False,
    "cursor": {"name": 0, "resumo": 0, "descricao": 0, "resist_text": 0},
    "attrs": {"AGI": 0, "FOR": 0, "VIG": 0},
    "armor_bonus": 0,  # bônus da armadura aplicado ao Bloqueio
    "armor_block_reduction": 0,
    "skills_trained": {"ESQUIVA": False, "BLOQUEIO": False, "CONTRA": False},
    "resist_text": "",
    "prof_armas": "",
    "prof_protecoes": "",
    "prof_outros": "",
}

FIELD_OPTIONS = {
    "tipo": ["Combate", "Narrativa", "Magika"],
    "custo": ["1PE", "2PE", "5PE", "10PE", "15PE"],
    "bonus": ["---", "+AGI", "+FOR", "+VIG", "+PRE", "+INT"],
    "dano": ["---", "1D4", "1D6", "1D8", "1D10", "1D12", "1D20"],
}

PROF_OPTIONS = {
    "prof_armas": ["---", "Simples", "Táticas", "Pesadas"],
    "prof_protecoes": ["---", "Leves", "Pesadas", "Escudo"],
    "prof_outros": ["---", "Ferramentas de concerto", "Ferramentas de artesão", "Instrumentos musicais"],
}

ALL_DROPDOWN_OPTIONS = {**FIELD_OPTIONS, **PROF_OPTIONS}

TEXT_FIELDS = {"name", "resumo", "descricao"}
TOP_TEXT_FIELDS = {"resist_text"}
TOP_DROPDOWN_FIELDS = set(PROF_OPTIONS.keys())

DEF_CONFIG = [
    {"key": "ESQUIVA", "label": "ESQUIVA", "attr": "AGI"},
    {"key": "BLOQUEIO", "label": "BLOQUEIO (1PE)", "attr": "FOR"},
    {"key": "CONTRA", "label": "CONTRA-ATAQUE", "attr": "FOR"},
]


def compute_base_defense(state):
    vig = state.get("attrs", {}).get("VIG", 0) or 0
    return 10 + vig


def compute_defense_value(state, key, attr_key):
    attr_val = state.get("attrs", {}).get(attr_key, 0) or 0
    trained = state.get("skills_trained", {}).get(key, False)
    if key == "BLOQUEIO":
        train_bonus = 1 if trained else 0
        armor_bonus = state.get("armor_bonus", 0) if trained else 0
        armor_bonus = armor_bonus or 0
        return attr_val + train_bonus + armor_bonus, attr_val, train_bonus, armor_bonus
    train_bonus = 2 if trained else 0
    if key == "CONTRA":
        parts = [f"{attr_key}({attr_val:+})"]
        if train_bonus:
            parts.append(f"Treino({train_bonus:+})")
        return " + ".join(parts), attr_val, train_bonus, 0
    return attr_val + train_bonus, attr_val, train_bonus, 0


def draw_text(surface, text, font, color, pos, center=False):
    render = font.render(text, True, color)
    rect = render.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(render, rect)
    return rect


def draw_tabs(surface, state):
    tab_h = 36
    tab_w = WIDTH // len(state["tabs"])
    rects = []
    for idx, label in enumerate(state["tabs"]):
        rect = pygame.Rect(idx * tab_w, 0, tab_w, tab_h)
        active = label == state["active_tab"]
        pygame.draw.rect(surface, GRAY_60 if active else GRAY_40, rect)
        pygame.draw.rect(surface, BLACK, rect, 1)
        draw_text(surface, label, FONTS["md"], WHITE, rect.center, center=True)
        rects.append((label, rect))
    return rects, tab_h


def draw_pentagon(surface, center, radius):
    points = []
    for i in range(5):
        angle = -math.pi / 2 + i * 2 * math.pi / 5
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(surface, BLACK, points)
    pygame.draw.polygon(surface, WHITE, points, 2)
    draw_text(surface, "BASE", FONTS["xs"], WHITE, (center[0], center[1] - 36), center=True)


def draw_checkbox(surface, rect, checked):
    pygame.draw.rect(surface, BLACK, rect)
    pygame.draw.rect(surface, WHITE, rect, 1)
    if checked:
        pygame.draw.line(surface, PURPLE, rect.topleft, rect.bottomright, 2)
        pygame.draw.line(surface, PURPLE, (rect.left, rect.bottom), (rect.right, rect.top), 2)


def draw_diamond(surface, center, size, text, border_color=WHITE, fill_color=BLACK):
    cx, cy = center
    half = size // 2
    pts = [(cx, cy - half), (cx + half, cy), (cx, cy + half), (cx - half, cy)]
    pygame.draw.polygon(surface, fill_color, pts)
    pygame.draw.polygon(surface, border_color, pts, 2)
    draw_text(surface, text, FONTS["xs"], WHITE, center, center=True)


def draw_button(surface, rect, label, color_bg, color_border=WHITE, font="xs"):
    pygame.draw.rect(surface, color_bg, rect)
    pygame.draw.rect(surface, color_border, rect, 1)
    draw_text(surface, label, FONTS[font], BLACK, rect.center, center=True)


def filtered_abilities(state):
    target = state.get("filter")
    if not target:
        return list(enumerate(state["abilities"]))
    target = target.strip().lower()
    return [(idx, a) for idx, a in enumerate(state["abilities"]) if a.get("categoria", "").strip().lower() == target]


def snapshot_form(state):
    form = state["form"]
    return {k: form.get(k, "").strip() for k in form}


def clear_form(state):
    for key in state["form"]:
        state["form"][key] = ""
    state["focus"] = None
    state["selected"] = None
    for k in TEXT_FIELDS:
        state["cursor"][k] = 0


def add_or_update(state, mode):
    data = snapshot_form(state)
    if not data["name"]:
        state["error"] = "Informe o nome da habilidade"
        return
    if not data["categoria"]:
        data["categoria"] = state.get("filter") or "COMBATE"
    state["error"] = ""
    if mode == "add" or state["selected"] is None:
        state["abilities"].append(data)
        state["selected"] = len(state["abilities"]) - 1
    else:
        idx = state["selected"]
        if 0 <= idx < len(state["abilities"]):
            state["abilities"][idx] = data
    state["focus"] = None


def remove_selected(state):
    idx = state.get("selected")
    if idx is None:
        return
    if 0 <= idx < len(state["abilities"]):
        state["abilities"].pop(idx)
    state["selected"] = None
    clear_form(state)
    state["show_form"] = False


def draw_habilidades_panel(surface, state):
    surface.fill(BLACK)
    rects = {"fields": {}, "buttons": {}, "rows": [], "filters": [], "defenses": []}

    panel_rect = pygame.Rect(8, 8, WIDTH - 16, HEIGHT - 16)
    pygame.draw.rect(surface, BLACK, panel_rect)
    pygame.draw.rect(surface, WHITE, panel_rect, 2)

    content_pad = 12
    content_x = panel_rect.x + content_pad
    content_w = panel_rect.width - content_pad * 2
    content_y = panel_rect.y + content_pad
    top_block_h = int(152 * HEIGHT / 700)

    # Espaços esquerdo/direito proporcionais à largura da janela alvo
    left_w = int(content_w * 0.52)
    right_w = content_w - left_w - content_pad
    left_x = content_x
    right_x = left_x + left_w + content_pad

    # Pentagon / armadura
    pent_center = (left_x + 70, content_y + 70)
    draw_pentagon(surface, pent_center, 56)
    base_def = compute_base_defense(state)
    vig_val = state.get("attrs", {}).get("VIG", 0) or 0
    draw_text(surface, f"{base_def}", FONTS["sm_b"], WHITE, (pent_center[0], pent_center[1] - 14), center=True)
    base_label = f"10 + VIG({vig_val})"
    draw_text(surface, base_label, FONTS["xs"], WHITE, (pent_center[0], pent_center[1] + 10), center=True)
    armor_reduction = state.get("armor_block_reduction", 0) or 0

    # Defenses (ligadas a pericias)
    def_y = content_y + 10
    cb_size = 16
    label_x = left_x + 120
    formula_x = label_x + 148
    diamond_x = left_x + left_w - 30
    for idx, cfg in enumerate(DEF_CONFIG):
        y = def_y + idx * 34
        trained = state.get("skills_trained", {}).get(cfg["key"], False)
        val, attr_val, train_bonus, armor_bonus = compute_defense_value(state, cfg["key"], cfg["attr"])
        draw_text(surface, cfg["label"], FONTS["sm_b"], WHITE, (label_x, y))
        cb_rect = pygame.Rect(label_x + 160, y, cb_size, cb_size)
        draw_checkbox(surface, cb_rect, trained)
        rects["defenses"].append((cfg["key"], cb_rect))
        if cfg["key"] == "CONTRA":
            formula = val  # string like 3D6 + FOR + Treino
            draw_text(surface, formula, FONTS["sm"], WHITE, (formula_x, y))
            mod_total = attr_val + train_bonus
            draw_diamond(surface, (diamond_x, y + cb_size // 2 + 2), 22, f"{mod_total:+}")
        elif cfg["key"] == "BLOQUEIO":
            formula_parts = [f"{cfg['attr']}({attr_val:+})"]
            if train_bonus:
                formula_parts.append(f"Treino({train_bonus:+})")
            if armor_bonus:
                formula_parts.append(f"Arm({armor_bonus:+})")
            formula = " + ".join(formula_parts)
            if armor_reduction:
                formula = f"{formula} / -{armor_reduction} severidade"
            draw_text(surface, formula, FONTS["sm"], WHITE, (formula_x, y))
            mod_total = attr_val + train_bonus + armor_bonus
            draw_diamond(surface, (diamond_x, y + cb_size // 2 + 2), 22, f"{mod_total:+}")
        else:
            formula_parts = [f"{cfg['attr']}({attr_val:+})"]
            if train_bonus:
                formula_parts.append(f"Treino({train_bonus:+})")
            formula = " + ".join(formula_parts)
            draw_text(surface, formula, FONTS["sm"], WHITE, (formula_x, y))
            draw_diamond(surface, (diamond_x, y + cb_size // 2 + 2), 22, f"{val:02d}")

    # Resistencias / proficiencias
    draw_text(surface, "RESISTENCIAS", FONTS["md"], WHITE, (right_x, content_y))
    resist_rect = pygame.Rect(right_x, content_y + 22, right_w, 24)
    border = ORANGE if state.get("focus") == "resist_text" else WHITE
    pygame.draw.rect(surface, GRAY_20, resist_rect)
    pygame.draw.rect(surface, border, resist_rect, 1)
    resist_val = state.get("resist_text", "")
    draw_text(surface, resist_val, FONTS["sm"], WHITE, (resist_rect.x + 6, resist_rect.y + 4))
    if state.get("focus") == "resist_text":
        cur = state["cursor"].get("resist_text", len(resist_val))
        cur = max(0, min(cur, len(resist_val)))
        caret_x = resist_rect.x + 6 + FONTS["sm"].size(resist_val[:cur])[0]
        caret_y = resist_rect.y + 3
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            pygame.draw.line(surface, WHITE, (caret_x, caret_y), (caret_x, resist_rect.bottom - 3), 1)
    rects["fields"]["resist_text"] = resist_rect

    draw_text(surface, "PROFICIENCIAS", FONTS["md"], WHITE, (right_x, resist_rect.bottom + 8))

    # Dropdowns de proficiencia (armas/protecoes/outros)
    select_gap = 8
    select_w = (right_w - select_gap * 2) // 3
    select_h = 24
    select_y = resist_rect.bottom + 32
    select_bottom = select_y
    prof_selects = [
        ("ARMAS", "prof_armas"),
        ("PROTECOES", "prof_protecoes"),
        ("OUTROS", "prof_outros"),
    ]
    for i, (label, key) in enumerate(prof_selects):
        rect = pygame.Rect(right_x + i * (select_w + select_gap), select_y, select_w, select_h)
        border = ORANGE if state.get("focus") == key else WHITE
        pygame.draw.rect(surface, GRAY_20, rect)
        pygame.draw.rect(surface, border, rect, 1)
        draw_text(surface, label, FONTS["xs"], WHITE, (rect.x, rect.y - 14))
        current = state.get(key, "") or "---"
        draw_text(surface, current, FONTS["sm"], WHITE, (rect.x + 6, rect.y + 4))
        rects["fields"][key] = rect
        select_bottom = max(select_bottom, rect.bottom)

    # Filters
    filter_y = max(content_y + top_block_h - 20, select_bottom + 12)
    filters = ["COMBATE", "NARRATIVA", "MAGIKA"]
    filter_w = 110
    filter_gap = 10
    start_x = content_x
    for i, f in enumerate(filters):
        rect = pygame.Rect(start_x + i * (filter_w + filter_gap), filter_y, filter_w, 26)
        active = state.get("filter") == f
        fill = PURPLE if active else GRAY_60
        pygame.draw.rect(surface, fill, rect)
        pygame.draw.rect(surface, WHITE, rect, 1)
        draw_text(surface, f, FONTS["sm_b"], WHITE, rect.center, center=True)
        rects["filters"].append((f, rect))
    # Add toggle button (top-right)
    add_toggle_w = 120
    add_toggle_h = 28
    add_toggle_rect = pygame.Rect(panel_rect.right - content_pad - add_toggle_w, filter_y, add_toggle_w, add_toggle_h)
    draw_button(surface, add_toggle_rect, "Adicionar", GREEN, color_border=WHITE)
    rects["buttons"]["add_toggle"] = add_toggle_rect

    # Form area
    form_y = filter_y + 36
    form_area = pygame.Rect(content_x, form_y, left_w, panel_rect.bottom - form_y - content_pad)
    pygame.draw.rect(surface, BLACK, form_area)
    pygame.draw.rect(surface, WHITE, form_area, 2)

    form = state["form"]
    inner = form_area.inflate(-12, -12)
    y = inner.y

    rect_fields = rects["fields"]
    show_form = state.get("show_form") or state.get("selected") is not None
    if show_form:
        name_rect = pygame.Rect(inner.x, y + 16, inner.width - 140, 56)
        border = ORANGE if state.get("focus") == "name" else WHITE
        pygame.draw.rect(surface, GRAY_20, name_rect)
        pygame.draw.rect(surface, border, name_rect, 1)
        draw_text(surface, "Nome da habilidade*", FONTS["sm_b"], WHITE, (name_rect.x, y))
        text_val = form["name"] or ""
        draw_text(surface, text_val, FONTS["sm_b"], WHITE, (name_rect.x + 6, name_rect.y + 6))
        if state.get("focus") == "name":
            cur = state["cursor"].get("name", len(text_val))
            cur = max(0, min(cur, len(text_val)))
            caret_x = name_rect.x + 6 + FONTS["sm_b"].size(text_val[:cur])[0]
            caret_y = name_rect.y + 4
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                pygame.draw.line(surface, WHITE, (caret_x, caret_y), (caret_x, name_rect.bottom - 4), 1)
        rect_fields["name"] = name_rect

        # Remove / Edit buttons
        btn_block_w = inner.width - name_rect.width - 12
        btn_block_x = name_rect.right + 8
        btn_remove = pygame.Rect(btn_block_x, name_rect.y, btn_block_w, 26)
        btn_edit = pygame.Rect(btn_block_x, name_rect.y + 32, btn_block_w, 26)
        draw_button(surface, btn_remove, "Remover", RED)
        edit_label = "Adicionar" if state.get("selected") is None else "Editar"
        draw_button(surface, btn_edit, edit_label, GREEN)
        rects["buttons"]["remove"] = btn_remove
        rects["buttons"]["edit"] = btn_edit
        y = name_rect.bottom + 16

        # Row tipo/custo/bonus/dano (duas colunas)
        row_gap = 10
        col_w = (inner.width - row_gap) // 2
        field_h = 22
        base_y = y + 4
        vertical_step = 32
        tipo_rect = pygame.Rect(inner.x, base_y, col_w - 2, field_h)
        custo_rect = pygame.Rect(inner.x + col_w + row_gap, base_y, col_w - 2, field_h)
        bonus_rect = pygame.Rect(inner.x, base_y + vertical_step, col_w - 2, field_h)
        dano_rect = pygame.Rect(inner.x + col_w + row_gap, base_y + vertical_step, col_w - 2, field_h)
        defesa_rect = pygame.Rect(inner.x, base_y + vertical_step * 2, col_w - 2, field_h)
        for label, rect, key in [
            ("Tipo", tipo_rect, "tipo"),
            ("Custo", custo_rect, "custo"),
            ("Bonus", bonus_rect, "bonus"),
            ("Dano", dano_rect, "dano"),
            ("Defesa", defesa_rect, "defesa"),
        ]:
            border = ORANGE if state.get("focus") == key else WHITE
            pygame.draw.rect(surface, GRAY_20, rect)
            pygame.draw.rect(surface, border, rect, 1)
            draw_text(surface, f"{label}:", FONTS["xs"], WHITE, (rect.x, rect.y - 14))
            draw_text(surface, form.get(key, "") or "", FONTS["sm"], WHITE, (rect.x + 4, rect.y + 2))
            rect_fields[key] = rect
        # Empurra os textos para mais baixo e reduz alturas
        y = defesa_rect.bottom + 32
        bottom_margin = 10
        resumo_h = 32
        desc_start = y + resumo_h + 10
        desc_h = max(60, inner.bottom - bottom_margin - desc_start)

        # Resumo
        resumo_rect = pygame.Rect(inner.x, y, inner.width - 4, resumo_h)
        border = ORANGE if state.get("focus") == "resumo" else WHITE
        pygame.draw.rect(surface, GRAY_20, resumo_rect)
        pygame.draw.rect(surface, border, resumo_rect, 1)
        draw_text(surface, "Descricao resumo*", FONTS["xs"], WHITE, (resumo_rect.x, resumo_rect.y - 14))
        lines, line_starts = wrap_text_with_starts(form.get("resumo", ""), FONTS["sm"], resumo_rect.width - 8)
        for i, line in enumerate(lines[:4]):
            draw_text(surface, line, FONTS["sm"], WHITE, (resumo_rect.x + 4, resumo_rect.y + 4 + i * 18))
        if state.get("focus") == "resumo":
            cur = state["cursor"].get("resumo", len(form.get("resumo", "")))
            cur = max(0, min(cur, len(form.get("resumo", ""))))
            line_idx = 0
            for idx, start in enumerate(line_starts):
                if cur >= start:
                    line_idx = idx
            line_idx = min(line_idx, len(lines) - 1)
            caret_line = lines[line_idx] if lines else ""
            offset_in_line = cur - line_starts[line_idx]
            caret_text = caret_line[:offset_in_line]
            caret_x = resumo_rect.x + 4 + FONTS["sm"].size(caret_text)[0]
            caret_y = resumo_rect.y + 4 + line_idx * 18
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                pygame.draw.line(surface, WHITE, (caret_x, caret_y), (caret_x, caret_y + FONTS["sm"].get_height()), 1)
        rect_fields["resumo"] = resumo_rect
        # Descricao
        desc_rect = pygame.Rect(inner.x, desc_start, inner.width - 4, desc_h)
        border = ORANGE if state.get("focus") == "descricao" else WHITE
        pygame.draw.rect(surface, GRAY_20, desc_rect)
        pygame.draw.rect(surface, border, desc_rect, 1)
        draw_text(surface, "Descricao detalhada*", FONTS["xs"], WHITE, (desc_rect.x, desc_rect.y - 14))
        desc_lines, desc_starts = wrap_text_with_starts(form.get("descricao", ""), FONTS["sm"], desc_rect.width - 8)
        max_lines = (desc_rect.height - 8) // 18
        for i, line in enumerate(desc_lines[:max_lines]):
            draw_text(surface, line, FONTS["sm"], WHITE, (desc_rect.x + 4, desc_rect.y + 4 + i * 18))
        if state.get("focus") == "descricao":
            cur = state["cursor"].get("descricao", len(form.get("descricao", "")))
            cur = max(0, min(cur, len(form.get("descricao", ""))))
            line_idx = 0
            for idx, start in enumerate(desc_starts):
                if cur >= start:
                    line_idx = idx
            line_idx = min(line_idx, len(desc_lines) - 1)
            caret_line = desc_lines[line_idx] if desc_lines else ""
            offset_in_line = cur - desc_starts[line_idx]
            caret_text = caret_line[:offset_in_line]
            caret_x = desc_rect.x + 4 + FONTS["sm"].size(caret_text)[0]
            caret_y = desc_rect.y + 4 + line_idx * 18
            if (pygame.time.get_ticks() // 400) % 2 == 0 and caret_y < desc_rect.bottom - FONTS["sm"].get_height():
                pygame.draw.line(surface, WHITE, (caret_x, caret_y), (caret_x, caret_y + FONTS["sm"].get_height()), 1)
        rect_fields["descricao"] = desc_rect
    else:
        dropdown = state.get("dropdown")
        # Manter dropdowns do topo (proficiencias) mesmo com o form fechado
        if not (dropdown and dropdown.get("field") in TOP_DROPDOWN_FIELDS):
            state["dropdown"] = None
        placeholder = "Clique em ADICIONAR ou selecione uma habilidade"
        draw_text(surface, placeholder, FONTS["sm"], WHITE, form_area.center, center=True)

    # List area
    list_area = pygame.Rect(right_x, form_y, right_w, panel_rect.bottom - form_y - content_pad)
    pygame.draw.rect(surface, BLACK, list_area)
    pygame.draw.rect(surface, WHITE, list_area, 2)
    list_inner = list_area.inflate(-12, -12)

    # Header
    header_h = 0
    header_rect = pygame.Rect(list_inner.x, list_inner.y, list_inner.width, header_h)
    add_rect = pygame.Rect(header_rect.right - 110, header_rect.bottom + 12, 100, 26)
    draw_button(surface, add_rect, "Adicionar", GREEN, color_border=WHITE)
    rects["buttons"]["add"] = add_rect

    # Rows
    row_h = 76
    y_row = list_inner.y + header_h + 4
    filtered = filtered_abilities(state)
    for display_idx, (idx, ability) in enumerate(filtered):
        row_rect = pygame.Rect(list_inner.x, y_row, list_inner.width, row_h)
        pygame.draw.rect(surface, BLACK, row_rect)
        pygame.draw.rect(surface, WHITE, row_rect, 1)
        if state.get("selected") == idx:
            pygame.draw.rect(surface, PURPLE, row_rect, 2)
        name = ability.get("name", "--")
        draw_text(surface, name, FONTS["sm_b"], WHITE, (row_rect.x + 8, row_rect.y + 6))
        draw_text(surface, f"Tipo: {ability.get('tipo', '--')}", FONTS["xs"], PURPLE, (row_rect.x + 8, row_rect.y + 26))
        draw_text(surface, f"Custo: {ability.get('custo', '--')}", FONTS["xs"], WHITE, (row_rect.x + 170, row_rect.y + 26))
        draw_text(surface, f"Descricao: {ability.get('resumo', '--')}", FONTS["xs"], PURPLE, (row_rect.x + 8, row_rect.y + 44))
        draw_text(surface, f"Dano: {ability.get('dano', '--')}", FONTS["xs"], PURPLE, (row_rect.x + 8, row_rect.y + 60))
        draw_text(surface, f"Bonus: {ability.get('bonus', '--')}", FONTS["xs"], PURPLE, (row_rect.x + 210, row_rect.y + 60))
        rects["rows"].append((idx, row_rect))
        y_row += row_h
        if y_row + row_h > list_inner.bottom:
            break

    # Error message
    if state.get("error"):
        draw_text(surface, state["error"], FONTS["xs"], RED, (form_area.x + 6, form_area.bottom - 16))

    # Dropdown (draw last, above all)
    dropdown = state.get("dropdown")
    if dropdown:
        field = dropdown.get("field")
        base_rect = rects["fields"].get(field)
        options = ALL_DROPDOWN_OPTIONS.get(field, [])
        allow_dropdown = show_form or field in TOP_DROPDOWN_FIELDS
        if base_rect and options and allow_dropdown:
            opt_h = 22
            opt_pad = 3
            opt_rects = []
            drop_y = base_rect.bottom + 4
            for idx_opt, opt in enumerate(options):
                r = pygame.Rect(base_rect.x, drop_y + idx_opt * (opt_h + opt_pad), base_rect.width, opt_h)
                pygame.draw.rect(surface, GRAY_40, r)
                pygame.draw.rect(surface, WHITE, r, 1)
                draw_text(surface, opt, FONTS["sm"], WHITE, (r.x + 4, r.y + 3))
                opt_rects.append((opt, r))
            state["dropdown"]["rects"] = opt_rects
        else:
            state["dropdown"] = None

    return rects


def handle_mouse(pos, rects, state):
    # Dropdown selection
    dropdown = state.get("dropdown")
    if dropdown and dropdown.get("rects"):
        for opt, r in dropdown["rects"]:
            if r.collidepoint(pos):
                field = dropdown.get("field")
                if field in state["form"]:
                    state["form"][field] = opt
                else:
                    state[field] = opt
                state["dropdown"] = None
                state["focus"] = None
                return
    else:
        state["dropdown"] = None

    # Filters
    for label, rect in rects.get("filters", []):
        if rect.collidepoint(pos):
            state["filter"] = None if state.get("filter") == label else label
            return
    # Defense checkboxes (treino)
    for key_def, rect in rects.get("defenses", []):
        if rect.collidepoint(pos):
            current = state.get("skills_trained", {}).get(key_def, False)
            state["skills_trained"][key_def] = not current
            return
    # Fields
    for key, rect in rects.get("fields", {}).items():
        if rect and rect.collidepoint(pos):
            if key in ALL_DROPDOWN_OPTIONS:
                state["dropdown"] = {"field": key, "rects": []}
            else:
                state["dropdown"] = None
            state["focus"] = key
            if key in TEXT_FIELDS:
                state["cursor"][key] = len(state["form"].get(key, "") or "")
            elif key in TOP_TEXT_FIELDS:
                state["cursor"][key] = len(state.get(key, "") or "")
            return
    # Buttons
    btns = rects.get("buttons", {})
    if btns.get("add_toggle") and btns["add_toggle"].collidepoint(pos):
        clear_form(state)
        state["show_form"] = True
        state["selected"] = None
        return
    if btns.get("add") and btns["add"].collidepoint(pos):
        state["show_form"] = True
        add_or_update(state, "add")
        return
    if btns.get("edit") and btns["edit"].collidepoint(pos):
        state["show_form"] = True
        add_or_update(state, "edit")
        return
    if btns.get("remove") and btns["remove"].collidepoint(pos):
        remove_selected(state)
        state["show_form"] = False
        return
    # Rows
    for idx, rect in rects.get("rows", []):
        if rect.collidepoint(pos):
            state["selected"] = idx
            ability = state["abilities"][idx]
            for key in state["form"]:
                state["form"][key] = ability.get(key, "")
            state["focus"] = None
            state["show_form"] = True
            for k in TEXT_FIELDS:
                state["cursor"][k] = len(state["form"].get(k, "") or "")
            return
    # Click outside dropdown closes it
    state["dropdown"] = None
    state["focus"] = None


def handle_key(event, state):
    field = state.get("focus")
    if not field:
        return
    if field in ALL_DROPDOWN_OPTIONS:
        return

    # Determine storage and guard on visibility
    if field in TEXT_FIELDS:
        if not state.get("show_form"):
            return
        buf = state["form"][field]
    elif field in TOP_TEXT_FIELDS:
        buf = state.get(field, "")
    else:
        return

    cur = state["cursor"].get(field, len(buf))
    cur = max(0, min(cur, len(buf)))
    key = event.key
    if key == pygame.K_BACKSPACE:
        if cur > 0:
            buf = buf[:cur - 1] + buf[cur:]
            cur -= 1
    elif key == pygame.K_DELETE:
        if cur < len(buf):
            buf = buf[:cur] + buf[cur + 1:]
    elif key == pygame.K_LEFT:
        cur = max(0, cur - 1)
    elif key == pygame.K_RIGHT:
        cur = min(len(buf), cur + 1)
    elif key == pygame.K_HOME:
        cur = 0
    elif key == pygame.K_END:
        cur = len(buf)
    elif key == pygame.K_RETURN:
        if field in {"resumo", "descricao"}:
            buf = buf[:cur] + "\n" + buf[cur:]
            cur += 1
    else:
        ch = event.unicode
        if ch:
            buf = buf[:cur] + ch + buf[cur:]
            cur += len(ch)

    if field in TEXT_FIELDS:
        state["form"][field] = buf
    else:
        state[field] = buf
    state["cursor"][field] = cur


def main():
    global WINDOW
    WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Painel de Habilidades (demo)")
    running = True
    while running:
        rects = draw_habilidades_panel(WINDOW, HABILIDADES_STATE)
        pygame.display.flip()
        CLOCK.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_mouse(event.pos, rects, HABILIDADES_STATE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    handle_key(event, HABILIDADES_STATE)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
