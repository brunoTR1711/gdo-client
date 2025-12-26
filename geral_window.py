import random
import pygame

# Dimensoes alinhadas aos outros paineis
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
pygame.display.set_caption("Painel Geral (demo)")
WINDOW = None
CLOCK = pygame.time.Clock()

FONTS = {
    "xs": pygame.font.SysFont("arial", 12),
    "sm": pygame.font.SysFont("arial", 14),
    "sm_b": pygame.font.SysFont("arial", 14, bold=True),
    "md": pygame.font.SysFont("arial", 18, bold=True),
    "lg": pygame.font.SysFont("arial", 26, bold=True),
}


def wrap_text(text, font, max_width):
    lines = []
    current = ""
    for word in str(text or "").split(" "):
        candidate = (current + " " + word).strip() if current else word
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def safe_int(value, default=0):
    try:
        if isinstance(value, str):
            value = value.strip() or default
        return int(value)
    except (ValueError, TypeError):
        return default


def roll_custom_dice(count, sides):
    return [random.randint(1, max(2, sides)) for _ in range(max(1, count))]


def normalize_category_key(category):
    cat = (category or "").strip().lower()
    if cat.startswith("arma"):
        return "arma"
    if cat.startswith("munic"):
        return "municao"
    if cat.startswith("protec"):
        return "protecao"
    if cat.startswith("magik"):
        return "magikos"
    if cat.startswith("colet"):
        return "coletaveis"
    if cat.startswith("equip"):
        return "equipamentos"
    if cat.startswith("comp"):
        return "componentes"
    return cat


def get_total_weight(items):
    return sum(max(0, safe_int(item.get("space", 0))) for item in items)


def get_weight_limit(strength, bonus):
    strength = safe_int(strength)
    bonus = safe_int(bonus)
    if strength <= 0:
        limit = 1 + strength
    if strength == 1:
        limit = 2 + strength
    if strength == 2:
        limit = 2 + strength
    if strength == 3:
        limit = 3 + strength
    if strength == 4:
        limit = 4 + strength
    if strength == 5:
        limit = 5 + strength
    if strength == 6:
        limit = 6 + strength
    return max(0, limit + bonus)


def get_best_protection(items):
    return max(0, max((safe_int(item.get("protecao", 0)) for item in items), default=0))


def filter_armas(items):
    armas = []
    for item in items:
        if normalize_category_key(item.get("category", "")) != "arma":
            continue
        armas.append(
            {
                "name": item.get("name", "--"),
                "tipo": item.get("tipo", "--"),
                "dano": item.get("dano", "--"),
                "alcance": item.get("alcance", "--"),
                "punho": item.get("empunhadura", item.get("punho", "--")),
            }
        )
    return armas


def compute_base_defense(attrs):
    return 10 + safe_int(attrs.get("VIG", 0))


def compute_defense_snapshot(attrs, hab_state=None):
    attrs = attrs or {}
    get_attr = lambda code: safe_int(attrs.get(code, 0))
    trained = (hab_state or {}).get("skills_trained", {})
    armor_bonus = safe_int((hab_state or {}).get("armor_bonus", 0))

    base = compute_base_defense(attrs)
    esquiva_trained = bool(trained.get("ESQUIVA"))
    bloqueio_trained = bool(trained.get("BLOQUEIO"))
    contra_trained = bool(trained.get("CONTRA"))

    esquiva_val = base + get_attr("AGI") + (2 if esquiva_trained else 0) if esquiva_trained else None
    bloqueio_val = get_attr("FOR") + 1 + armor_bonus if bloqueio_trained else None
    contra_val = get_attr("FOR") + (2 if contra_trained else 0) if contra_trained else None

    return {
        "base": base,
        "esquiva": esquiva_val,
        "bloqueio": bloqueio_val,
        "contra": contra_val,
        "resistencia": (hab_state or {}).get("resist_text", ""),
        "proficiencia": (hab_state or {}).get("prof_text", ""),
    }


def make_default_state():
    return {
        "attrs": {"AGI": 0, "FOR": 0, "VIG": 0, "PRE": 0, "INT": 0},
        "inventory": {
            "items": [],
            "peso_total": 0,
            "peso_limite": 0,
            "armas": [],
            "protecao": 0,
            "weight_bonus": 0,
        },
        "defenses": {
            "base": 0,
            "esquiva": None,
            "bloqueio": None,
            "contra": None,
            "resistencia": "",
            "proficiencia": "",
        },
        "skills": {"FISICA": [], "INTELECTO": [], "SOCIAL": []},
        "status": {"vida": "", "sanidade": ""},
        "roll": {"summary": "Clique em uma pericia treinada para rolar.", "detail": ""},
        "scroll": {"armas": 0, "skills": {"FISICA": 0, "INTELECTO": 0, "SOCIAL": 0}},
    }


GERAL_STATE = make_default_state()


def update_from_sources(attrs=None, hab_state=None, inv_state=None, skills=None, vida=None, sanidade=None):
    """Sincroniza o painel com os estados existentes das outras janelas."""
    if attrs:
        for k, v in attrs.items():
            GERAL_STATE["attrs"][k] = safe_int(v)

    if inv_state is not None:
        items = inv_state.get("items", [])
        GERAL_STATE["inventory"]["items"] = list(items)
        GERAL_STATE["inventory"]["armas"] = filter_armas(items)
        GERAL_STATE["inventory"]["peso_total"] = get_total_weight(items)
        GERAL_STATE["inventory"]["peso_limite"] = get_weight_limit(
            inv_state.get("strength", 0), inv_state.get("weight_bonus", 0)
        )
        GERAL_STATE["inventory"]["weight_bonus"] = safe_int(inv_state.get("weight_bonus", 0))
        GERAL_STATE["inventory"]["protecao"] = get_best_protection(items)

    if hab_state is not None:
        GERAL_STATE["defenses"] = compute_defense_snapshot(GERAL_STATE["attrs"], hab_state)

    if skills is not None:
        mapped = {"FISICA": [], "INTELECTO": [], "SOCIAL": []}
        for s in skills:
            if not s.get("trained"):
                continue
            cat = s.get("cat")
            if cat in mapped:
                mapped[cat].append(
                    {
                        "name": s.get("name", "--").replace("*", "").strip(),
                        "attr": s.get("attr", ""),
                        "bonus": safe_int(s.get("bonus", 0)),
                        "trained": True,
                    }
                )
        for cat in mapped:
            mapped[cat].sort(key=lambda sk: sk["name"].lower())
        GERAL_STATE["skills"] = mapped

    if vida is not None:
        GERAL_STATE["status"]["vida"] = vida
    if sanidade is not None:
        GERAL_STATE["status"]["sanidade"] = sanidade


def draw_text(surface, text, font, color, pos, center=False):
    render = font.render(text, True, color)
    rect = render.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(render, rect)
    return rect


def draw_badge(surface, rect, title, value, color_bg=GRAY_20, color_border=WHITE, value_color=WHITE):
    pygame.draw.rect(surface, color_bg, rect, border_radius=6)
    pygame.draw.rect(surface, color_border, rect, 1, border_radius=6)
    draw_text(surface, title, FONTS["xs"], GRAY_80, (rect.x + 6, rect.y + 4))
    value_render = FONTS["sm_b"].render(str(value), True, value_color)
    value_rect = value_render.get_rect()
    value_rect.midright = (rect.right - 6, rect.centery + 2)
    surface.blit(value_render, value_rect)


def draw_geral_panel(surface, state):
    surface.fill(BLACK)
    pad = 10
    offset_y = -74  # desloca tudo levemente para cima
    rects = {"skills": [], "skill_cols": {}, "armas_area": None}

    frame_rect = pygame.Rect(pad, pad + offset_y, WIDTH - pad * 1, HEIGHT - pad * 2 - offset_y)
    pygame.draw.rect(surface, GRAY_20, frame_rect)
    pygame.draw.rect(surface, WHITE, frame_rect, 1, border_radius=2)
    inner = frame_rect.inflate(-16, -16)

    header_rect = pygame.Rect(inner.x, inner.y, inner.width, 56)

    #attr_codes = ["AGI", "FOR", "VIG", "PRE", "INT"]
    badge_w = 64
    badge_h = 24
    gap = 6
    #start_x = header_rect.right - (badge_w * len(attr_codes) + gap * (len(attr_codes) - 1)) - 10
    #badge_y = header_rect.y + (header_rect.height - badge_h) // 2
    #for idx, code in enumerate(attr_codes):
    #    rect = pygame.Rect(start_x + idx * (badge_w + gap), badge_y, badge_w, badge_h)
    #    val = safe_int(state.get("attrs", {}).get(code, 0))
    #    draw_badge(surface, rect, code, f"{val:+d}", color_bg=GRAY_20, color_border=WHITE, value_color=WHITE)

    content_top = header_rect.bottom + 12
    top_h = 200
    gap_y = 12
    col_gap = 12
    left_w = int(inner.width * 0.54)
    inv_rect = pygame.Rect(inner.x, content_top, left_w, top_h)
    hab_rect = pygame.Rect(inv_rect.right + col_gap, content_top, inner.right - inv_rect.right - col_gap, top_h)

    # Inventario
    pygame.draw.rect(surface, GRAY_20, inv_rect)
    pygame.draw.rect(surface, WHITE, inv_rect, 2)
    inv_header = pygame.Rect(inv_rect.x, inv_rect.y, inv_rect.width, 32)
    pygame.draw.rect(surface, GRAY_40, inv_header)
    pygame.draw.rect(surface, WHITE, inv_header, 1)
    pygame.draw.line(surface, PURPLE, (inv_header.x, inv_header.bottom - 2), (inv_header.right, inv_header.bottom - 2), 2)
    draw_text(surface, "INVENTARIO RAPIDO", FONTS["md"], WHITE, (inv_header.x + 10, inv_header.y + 6))
    peso_text = f"{state['inventory']['peso_total']:02d}/{state['inventory']['peso_limite']:02d}"
    peso_rect = pygame.Rect(inv_header.right - 120, inv_header.y + 5, 108, inv_header.height - 10)
    draw_badge(surface, peso_rect, "PESO", peso_text, color_bg=GRAY_20, color_border=WHITE, value_color=ORANGE)

    table_x = inv_rect.x + 10
    table_y = inv_header.bottom + 8
    table_w = inv_rect.width - 20
    header_h = 22
    row_h = 22
    headers = [("Arma", 150), ("Tipo", 90), ("Dano", 70), ("Alcance", 70), ("Punho", 80)]
    header_row_rect = pygame.Rect(table_x, table_y, table_w, header_h)
    pygame.draw.rect(surface, GRAY_40, header_row_rect)
    pygame.draw.rect(surface, WHITE, header_row_rect, 1)
    cur_x = table_x + 6
    for text, width in headers:
        draw_text(surface, text.upper(), FONTS["xs"], WHITE, (cur_x, table_y + 4))
        cur_x += width
    armas_area_h = inv_rect.bottom - table_y - header_h - 42
    armas_area_h = max(44, armas_area_h)
    armas_area = pygame.Rect(table_x, table_y + header_h + 2, table_w, armas_area_h)
    pygame.draw.rect(surface, BLACK, armas_area)
    pygame.draw.rect(surface, WHITE, armas_area, 1)
    rects["armas_area"] = armas_area

    armas = state.get("inventory", {}).get("armas", [])
    max_rows = max(1, armas_area.height // row_h)
    start = max(0, state.get("scroll", {}).get("armas", 0))
    start = min(start, max(0, len(armas) - max_rows))
    end = min(len(armas), start + max_rows)
    if not armas:
        draw_text(surface, "Nenhuma arma cadastrada.", FONTS["xs"], GRAY_80, (armas_area.x + 6, armas_area.y + 4))
    else:
        for idx, item in enumerate(armas[start:end], start=start):
            y = armas_area.y + (idx - start) * row_h
            row_rect = pygame.Rect(armas_area.x + 1, y, armas_area.width - 2, row_h)
            row_fill = GRAY_20 if (idx - start) % 2 == 0 else GRAY_40
            pygame.draw.rect(surface, row_fill, row_rect)
            cur_x = table_x + 6
            cols = [item["name"], item["tipo"], item["dano"], item["alcance"], item["punho"]]
            for col_idx, (_, width) in enumerate(headers):
                color = WHITE if col_idx == 0 else GRAY_80
                draw_text(surface, cols[col_idx], FONTS["xs"], color, (cur_x, y + 2))
                cur_x += width

    protecao_val = state.get("inventory", {}).get("protecao", 0)
    protecao_rect = pygame.Rect(inv_rect.x + 10, inv_rect.bottom - 30, 160, 22)
    draw_badge(surface, protecao_rect, "PROTECAO", f"{protecao_val:+d}", color_bg=GRAY_20, color_border=WHITE, value_color=GREEN)

    # Habilidades / defesas
    pygame.draw.rect(surface, GRAY_20, hab_rect)
    pygame.draw.rect(surface, WHITE, hab_rect, 2)
    hab_header = pygame.Rect(hab_rect.x, hab_rect.y, hab_rect.width, 32)
    pygame.draw.rect(surface, GRAY_40, hab_header)
    pygame.draw.rect(surface, WHITE, hab_header, 1)
    pygame.draw.line(surface, PURPLE, (hab_header.x, hab_header.bottom - 2), (hab_header.right, hab_header.bottom - 2), 2)
    draw_text(surface, "DEFESAS E TREINOS", FONTS["md"], WHITE, (hab_header.x + 10, hab_header.y + 6))

    base = state.get("defenses", {}).get("base", 0)
    base_rect = pygame.Rect(hab_rect.x + 10, hab_header.bottom + 8, hab_rect.width - 20, 32)
    draw_badge(surface, base_rect, "DEFESA BASE", f"{base:02d}", color_bg=GRAY_20, color_border=WHITE, value_color=WHITE)

    entries = [
        ("ESQUIVA", state.get("defenses", {}).get("esquiva")),
        ("BLOQUEIO", state.get("defenses", {}).get("bloqueio")),
        ("CONTRA-ATAQUE", state.get("defenses", {}).get("contra")),
    ]
    entry_h = 36
    col_count = 3
    col_w = (hab_rect.width - 20 - (col_count - 1) * 8) // col_count
    start_y = base_rect.bottom + 6
    for i, (label, val) in enumerate(entries):
        row = i // col_count
        col = i % col_count
        x = hab_rect.x + 10 + col * (col_w + 8)
        y = start_y + row * (entry_h + 8)
        entry_rect = pygame.Rect(x, y, col_w, entry_h)
        trained = val is not None
        border_color = GREEN if trained else GRAY_60
        display_val = f"{val:02d}" if val is not None else "--"
        draw_badge(surface, entry_rect, label, display_val, color_bg=GRAY_20, color_border=border_color, value_color=WHITE)

    res_txt = state.get("defenses", {}).get("resistencia", "") or "--"
    prof_txt = state.get("defenses", {}).get("proficiencia", "") or "--"
    info_y = hab_rect.bottom - 64
    res_rect = pygame.Rect(hab_rect.x + 10, info_y, (hab_rect.width - 26) // 2, 30)
    prof_rect = pygame.Rect(res_rect.right + 6, info_y, hab_rect.width - res_rect.width - 26, 30)
    draw_badge(surface, res_rect, "RESISTENCIA", res_txt, color_bg=GRAY_20, color_border=WHITE, value_color=ORANGE)
    draw_badge(surface, prof_rect, "PROFICIENCIA", prof_txt, color_bg=GRAY_20, color_border=WHITE, value_color=ORANGE)

    # Pericias treinadas
    skills_h = 220
    skills_rect = pygame.Rect(inner.x, inv_rect.bottom + gap_y, inner.width, skills_h)
    pygame.draw.rect(surface, GRAY_20, skills_rect)
    pygame.draw.rect(surface, WHITE, skills_rect, 2)
    skills_header = pygame.Rect(skills_rect.x, skills_rect.y, skills_rect.width, 32)
    pygame.draw.rect(surface, GRAY_40, skills_header)
    pygame.draw.rect(surface, WHITE, skills_header, 1)
    pygame.draw.line(surface, PURPLE, (skills_header.x, skills_header.bottom - 2), (skills_header.right, skills_header.bottom - 2), 2)
    draw_text(surface, "PERICIAS TREINADAS", FONTS["md"], WHITE, (skills_header.x + 10, skills_header.y + 6))
    #draw_text(surface, "Clique em uma pericia treinada para rolar.", FONTS["xs"], GRAY_80, (skills_header.x + 10, skills_header.bottom - 14))

    col_pad = 10
    col_gap = 8
    row_h_skill = 22
    col_w = (skills_rect.width - col_pad * 2 - col_gap * 2) // 3
    list_top = skills_header.bottom + 8
    list_h = skills_rect.bottom - list_top - 12
    categories = [("FISICA", "FISICAS"), ("INTELECTO", "INTELECTUAIS"), ("SOCIAL", "SOCIAIS")]
    for idx, (key, label) in enumerate(categories):
        col_x = skills_rect.x + col_pad + idx * (col_w + col_gap)
        col_rect = pygame.Rect(col_x, list_top, col_w, list_h)
        head_rect = pygame.Rect(col_rect.x, col_rect.y, col_rect.width, 24)
        pygame.draw.rect(surface, GRAY_40, head_rect)
        pygame.draw.rect(surface, WHITE, head_rect, 1)
        draw_text(surface, label, FONTS["sm_b"], WHITE, head_rect.center, center=True)
        list_area = pygame.Rect(col_rect.x, head_rect.bottom + 2, col_rect.width, col_rect.height - head_rect.height - 4)
        pygame.draw.rect(surface, BLACK, list_area)
        pygame.draw.rect(surface, WHITE, list_area, 1)
        rects["skill_cols"][key] = list_area

        skills_list = state.get("skills", {}).get(key, [])
        offset = state.get("scroll", {}).get("skills", {}).get(key, 0)
        max_rows_skill = max(1, list_area.height // row_h_skill)
        offset = max(0, min(offset, max(0, len(skills_list) - max_rows_skill)))
        for i_skill, skill in enumerate(skills_list[offset : offset + max_rows_skill], start=offset):
            y = list_area.y + (i_skill - offset) * row_h_skill
            row_rect = pygame.Rect(list_area.x + 2, y, list_area.width - 4, row_h_skill - 2)
            pygame.draw.rect(surface, GRAY_20 if (i_skill - offset) % 2 == 0 else GRAY_40, row_rect, border_radius=4)
            clickable_rect = row_rect.copy()
            draw_text(
                surface,
                f"- {skill['name']} ({skill['attr']})",
                FONTS["xs"],
                GREEN,
                (row_rect.x + 6, row_rect.y + 2),
            )
            rects["skills"].append((key, skill, clickable_rect))

    # Status e ultima rolagem
    status_rect = pygame.Rect(inner.x, skills_rect.bottom + gap_y, inner.width, inner.bottom - (skills_rect.bottom + gap_y))
    pygame.draw.rect(surface, GRAY_20, status_rect)
    pygame.draw.rect(surface, WHITE, status_rect, 2)
    status_header = pygame.Rect(status_rect.x, status_rect.y, status_rect.width, 32)
    pygame.draw.rect(surface, GRAY_40, status_header)
    pygame.draw.rect(surface, WHITE, status_header, 1)
    pygame.draw.line(surface, PURPLE, (status_header.x, status_header.bottom - 2), (status_header.right, status_header.bottom - 2), 2)
    draw_text(surface, "STATUS", FONTS["md"], WHITE, (status_header.x + 10, status_header.y + 6))

    vida = state.get("status", {}).get("vida", "") or "--"
    sanidade = state.get("status", {}).get("sanidade", "") or "--"
    pill_w = 150
    pill_h = 28
    status_y = status_header.bottom + 8
    vida_rect = pygame.Rect(status_rect.x + 12, status_y, pill_w, pill_h)
    san_rect = pygame.Rect(vida_rect.right + 10, status_y, pill_w, pill_h)
    draw_badge(surface, vida_rect, "VIDA", vida, color_bg=GRAY_20, color_border=WHITE, value_color=GREEN)
    draw_badge(surface, san_rect, "SANIDADE", sanidade, color_bg=GRAY_20, color_border=WHITE, value_color=ORANGE)

    roll_rect = pygame.Rect(status_rect.x + 12, vida_rect.bottom + 10, status_rect.width - 24, status_rect.bottom - (vida_rect.bottom + 16))
    #pygame.draw.rect(surface, BLACK, roll_rect)
    #pygame.draw.rect(surface, WHITE, roll_rect, 1)
    #roll_summary = state.get("roll", {}).get("summary", "")
    #roll_lines = wrap_text(roll_summary, FONTS["xs"], roll_rect.width - 12)
    #for i, line in enumerate(roll_lines[:4]):
    #    color = ORANGE if i == 0 else GRAY_80
    #    draw_text(surface, line, FONTS["xs"], color, (roll_rect.x + 6, roll_rect.y + 4 + i * 16))
    #roll_detail = state.get("roll", {}).get("detail", "")
    #if roll_detail:
    #    detail_lines = wrap_text(roll_detail, FONTS["xs"], roll_rect.width - 12)
    #    base_y = roll_rect.y + 4 + len(roll_lines[:4]) * 16 + 2
    #    for j, line in enumerate(detail_lines[:3]):
    #        draw_text(surface, line, FONTS["xs"], GRAY_60, (roll_rect.x + 6, base_y + j * 16))

    return rects


def roll_skill_local(skill, state):
    attr_val = safe_int(state.get("attrs", {}).get(skill.get("attr", ""), 0))
    skill_bonus = safe_int(skill.get("bonus", 0)) if skill.get("trained") else 0
    dice = roll_custom_dice(3, 6)
    total = sum(dice) + attr_val + skill_bonus
    dice_str = "+".join(str(d) for d in dice)
    state["roll"]["summary"] = f"{skill['name']}: 3D6({dice_str}) + {skill['attr']}({attr_val:+}) + Treino({skill_bonus:+}) = {total}"


def handle_mouse(pos, rects, state, roll_callback=None):
    for key, skill, rect in rects.get("skills", []):
        if rect.collidepoint(pos):
            if callable(roll_callback):
                roll_callback(skill)
                state["roll"]["summary"] = f"{skill['name']}: rolando no painel principal"
            else:
                roll_skill_local(skill, state)
            return True
    return False


def handle_mousewheel(delta, rects, state, pos=None):
    if rects.get("armas_area") and (pos is None or rects["armas_area"].collidepoint(pos)):
        total = len(state.get("inventory", {}).get("armas", []))
        visible = max(1, rects["armas_area"].height // 22)
        if total > visible:
            state["scroll"]["armas"] = max(0, min(total - visible, state["scroll"]["armas"] - delta))
            return True
    for key, col_rect in rects.get("skill_cols", {}).items():
        if pos is None or col_rect.collidepoint(pos):
            skills_list = state.get("skills", {}).get(key, [])
            visible = max(1, col_rect.height // 22)
            total = len(skills_list)
            if total > visible:
                cur = state["scroll"]["skills"].get(key, 0)
                cur = max(0, min(total - visible, cur - delta))
                state["scroll"]["skills"][key] = cur
                return True
    return False


def handle_key(event, state):
    return False


def main():
    global WINDOW
    WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Painel Geral (demo)")
    running = True

    # Exemplo simples para visualizacao rapida
    demo_items = [
        {"name": "Pistola", "category": "Armas", "tipo": "Distancia", "dano": "1D6", "alcance": "9m", "empunhadura": "Leve", "space": 1},
        {"name": "Escudo", "category": "Protecao", "protecao": "2", "space": 1},
    ]
    demo_skills = [
        {"name": "Esquiva*", "attr": "AGI", "cat": "FISICA", "trained": True, "bonus": 2},
        {"name": "Bloqueio", "attr": "FOR", "cat": "FISICA", "trained": True, "bonus": 1},
        {"name": "Percepcao", "attr": "PRE", "cat": "SOCIAL", "trained": True, "bonus": 1},
    ]
    demo_attrs = {"AGI": 2, "FOR": 1, "VIG": 2}
    demo_hab = {"skills_trained": {"ESQUIVA": True, "BLOQUEIO": True, "CONTRA": False}, "armor_bonus": 0, "resist_text": "Fogo", "prof_text": "Armas leves"}
    demo_inv = {"items": demo_items, "strength": demo_attrs["FOR"], "weight_bonus": 0}
    update_from_sources(attrs=demo_attrs, hab_state=demo_hab, inv_state=demo_inv, skills=demo_skills, vida="SAUDAVEL", sanidade="ESTAVEL")

    while running:
        rects = draw_geral_panel(WINDOW, GERAL_STATE)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if handle_mouse(event.pos, rects, GERAL_STATE):
                    continue
            elif event.type == pygame.MOUSEWHEEL:
                handle_mousewheel(-event.y, rects, GERAL_STATE, getattr(event, "pos", None))
        CLOCK.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
