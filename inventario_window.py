import sys
import pygame

# Dimensoes base alinhadas com outros paineis
WIDTH, HEIGHT = 755, 700
FPS = 60

# Cores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY_15 = (30, 30, 30)
GRAY_25 = (45, 45, 45)
GRAY_40 = (70, 70, 70)
GRAY_60 = (110, 110, 110)
GRAY_80 = (170, 170, 170)
PURPLE = (150, 60, 200)
ORANGE = (240, 140, 0)
GREEN = (0, 200, 0)
RED = (210, 60, 60)

pygame.init()
pygame.display.set_caption("Painel de Inventario (demo)")
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
CLOCK = pygame.time.Clock()

FONTS = {
    "xs": pygame.font.SysFont("arial", 12),
    "sm": pygame.font.SysFont("arial", 14),
    "sm_b": pygame.font.SysFont("arial", 14, bold=True),
    "md": pygame.font.SysFont("arial", 18, bold=True),
    "lg": pygame.font.SysFont("arial", 26, bold=True),
}

CATEGORIES = ["Armas", "Municao", "Protecao", "Magikos", "Coletaveis", "Itens chave", "Componentes"]

DEFAULT_ITEMS = [
    {
        "name": "Espada curta",
        "category": "Armas",
        "space": 2,
        "tipo": "Leve",
        "alcance": "1m",
        "empunhadura": "Uma mao",
        "dano": "1D6",
        "protecao": 0,
        "descricao": "Lamina simples, equilibrada para combates rapidos.",
        "localizacao": "Coldres",
        "info1": "Fabricada pelos ferreiros de Rorul.",
        "info2": "Ocupa 2 espacos do inventario.",
    },
    {
        "name": "Escudo pequeno",
        "category": "Protecao",
        "space": 3,
        "tipo": "Defesa",
        "alcance": "---",
        "empunhadura": "Braco",
        "dano": "---",
        "protecao": 2,
        "descricao": "Escudo leve que concede +2 de protecao enquanto equipado.",
        "localizacao": "Costas",
        "info1": "Concede cobertura parcial em abrigos.",
        "info2": "Requer uma mao livre para uso.",
    },
    {
        "name": "Pistola arcana",
        "category": "Magikos",
        "space": 1,
        "tipo": "Fogo",
        "alcance": "9m",
        "empunhadura": "Uma mao",
        "dano": "1D8",
        "protecao": 0,
        "descricao": "Dispara rajadas concentradas de energia canalizada.",
        "localizacao": "Coldres",
        "info1": "Consome um cartucho arcano por cena.",
        "info2": "Nao sofre penalidade em ambientes fechados.",
    },
    {
        "name": "Colete reforcado",
        "category": "Protecao",
        "space": 2,
        "tipo": "Armadura",
        "alcance": "---",
        "empunhadura": "---",
        "dano": "---",
        "protecao": 5,
        "descricao": "Colete resistente que adiciona protecao adicional ao usuario.",
        "localizacao": "Equipado",
        "info1": "Concede resistencia a dano perfurante.",
        "info2": "Necessita manutencao semanal.",
    },
]


def clone_default_items():
    return [item.copy() for item in DEFAULT_ITEMS]


def wrap_text(text, font, max_width):
    """Divide texto em linhas respeitando largura maxima."""
    lines = []
    current = ""
    for word in (text or "").split(" "):
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


def get_total_weight(state):
    return sum(max(0, safe_int(item.get("space", 0))) for item in state["items"])


def get_weight_limit(state):
    base = state.get("base_limit", 10)
    return max(0, base + state.get("weight_bonus", 0))


def get_best_protection(state):
    return max(0, max((safe_int(item.get("protecao", 0)) for item in state["items"]), default=0))


def ensure_filtered(state):
    """Atualiza cache filtrado (lista de tuplas (idx, item))."""
    query = (state.get("search") or "").strip().lower()
    category = (state.get("filters", {}).get("category") or "Todos").strip().lower()
    filtered = []
    for idx, item in enumerate(state["items"]):
        name = (item.get("name") or "").lower()
        cat = (item.get("category") or "").lower()
        if category not in ("", "todos") and cat != category:
            continue
        if query and query not in name:
            continue
        filtered.append((idx, item))
    state["_filtered"] = filtered
    return filtered


def clamp_scroll(state, max_rows):
    filtered = state.get("_filtered") or ensure_filtered(state)
    max_scroll = max(0, len(filtered) - max_rows)
    state["scroll"] = max(0, min(state.get("scroll", 0), max_scroll))
    state["max_scroll"] = max_scroll


def get_selected_item(state):
    filtered = state.get("_filtered") or ensure_filtered(state)
    if not filtered:
        state["selected"] = None
        return None
    indices = [idx for idx, _ in filtered]
    sel = state.get("selected")
    if sel not in indices:
        sel = indices[0]
        state["selected"] = sel
    for idx, item in filtered:
        if idx == sel:
            return item
    state["selected"] = indices[0]
    return filtered[0][1]


def set_status(state, message, color=None):
    state["status"] = message
    state["status_color"] = color or WHITE


def select_next(state, delta):
    filtered = state.get("_filtered") or ensure_filtered(state)
    if not filtered:
        state["selected"] = None
        return
    indices = [idx for idx, _ in filtered]
    if state.get("selected") not in indices:
        state["selected"] = indices[0]
        return
    pos = indices.index(state["selected"])
    pos = max(0, min(len(indices) - 1, pos + delta))
    state["selected"] = indices[pos]


def draw_inventory_panel(surface, state):
    surface.fill(BLACK)
    rects = {"filters": [], "rows": [], "buttons": {}, "fields": {}, "list_area": None}

    panel_rect = pygame.Rect(8, 8, WIDTH - 16, HEIGHT - 16)
    pygame.draw.rect(surface, GRAY_15, panel_rect)
    pygame.draw.rect(surface, WHITE, panel_rect, 2)
    inner = panel_rect.inflate(-16, -16)

    draw_text(surface, "INVENTARIO", FONTS["md"], WHITE, (inner.x, inner.y - 4))
    limits_rect = pygame.Rect(inner.x, inner.y + 10, inner.width, 120)
    draw_limits_section(surface, limits_rect, state)

    content_top = limits_rect.bottom + 12
    left_width = int(inner.width * 0.45)
    left_rect = pygame.Rect(inner.x, content_top, left_width - 6, inner.bottom - content_top)
    right_rect = pygame.Rect(left_rect.right + 12, content_top, inner.right - left_rect.right - 12, left_rect.height)

    draw_left_detail(surface, left_rect, state)
    draw_right_panel(surface, right_rect, state, rects)

    state["rects"] = rects
    return rects


def draw_text(surface, text, font, color, pos, center=False):
    render = font.render(str(text), True, color)
    rect = render.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(render, rect)
    return rect


def draw_limit_row(surface, label, values, start_pos):
    label_pos = (start_pos[0], start_pos[1])
    draw_text(surface, label, FONTS["xs"], WHITE, label_pos)
    x = label_pos[0]
    y = label_pos[1] + 16
    box_w, box_h = 40, 30
    gap = 6
    for val in values:
        rect = pygame.Rect(x, y, box_w, box_h)
        pygame.draw.rect(surface, BLACK, rect)
        pygame.draw.rect(surface, WHITE, rect, 1)
        draw_text(surface, f"{val:02d}", FONTS["sm"], WHITE, rect.center, center=True)
        x += box_w + gap


def draw_limits_section(surface, rect, state):
    pygame.draw.rect(surface, BLACK, rect)
    pygame.draw.rect(surface, WHITE, rect, 1)
    inner = rect.inflate(-10, -10)
    row_height = 55
    draw_limit_row(surface, "LIMITE DE ITENS", state.get("limit_slots", []), (inner.x, inner.y))
    draw_limit_row(
        surface,
        "TOTAL NO INVENTARIO",
        state.get("total_slots", []),
        (inner.x, inner.y + row_height),
    )
    weight_rect = pygame.Rect(inner.right - 150, inner.y + 12, 138, 36)
    draw_text(surface, "PESO", FONTS["xs"], WHITE, (weight_rect.x, weight_rect.y - 16))
    pygame.draw.rect(surface, BLACK, weight_rect)
    pygame.draw.rect(surface, WHITE, weight_rect, 1)
    weight_text = f"{get_total_weight(state):02d}/{get_weight_limit(state):02d}"
    draw_text(surface, weight_text, FONTS["sm_b"], WHITE, weight_rect.center, center=True)


def draw_form_box(surface, rect, label, text):
    pygame.draw.rect(surface, BLACK, rect)
    pygame.draw.rect(surface, WHITE, rect, 1)
    draw_text(surface, label, FONTS["xs"], WHITE, (rect.x, rect.y - 16))
    lines = wrap_text(text or "--", FONTS["xs"], rect.width - 12)
    y = rect.y + 6
    max_lines = max(1, rect.height // (FONTS["xs"].get_height() + 2))
    for line in lines[:max_lines]:
        draw_text(surface, line, FONTS["xs"], WHITE, (rect.x + 6, y))
        y += FONTS["xs"].get_height() + 2


def draw_left_detail(surface, detail_rect, state):
    pygame.draw.rect(surface, BLACK, detail_rect)
    pygame.draw.rect(surface, WHITE, detail_rect, 1)
    inner = detail_rect.inflate(-12, -12)
    item = get_selected_item(state)
    if not item:
        draw_text(surface, "Nenhum item selecionado.", FONTS["sm"], GRAY_80, (inner.x, inner.y))
        return

    image_rect = pygame.Rect(inner.x, inner.y, 140, 140)
    pygame.draw.rect(surface, BLACK, image_rect)
    pygame.draw.rect(surface, WHITE, image_rect, 1)
    draw_text(surface, "imagem do\nitem*", FONTS["xs"], WHITE, image_rect.center, center=True)

    info_rect = pygame.Rect(image_rect.right + 10, inner.y, inner.width - image_rect.width - 10, 140)
    pygame.draw.rect(surface, BLACK, info_rect)
    pygame.draw.rect(surface, WHITE, info_rect, 1)
    draw_text(surface, item.get("name", "Nome do item*"), FONTS["sm_b"], WHITE, (info_rect.x + 6, info_rect.y + 6))
    info_pairs = [
        ("Categoria", item.get("category", "--")),
        ("Espaco", str(item.get("space", "--"))),
        ("Tipo", item.get("tipo", "--")),
        ("Alcance", item.get("alcance", "--")),
        ("Empunhadura", item.get("empunhadura", "--")),
        ("Dano", item.get("dano", "--")),
        ("Protecao", f"+{item.get('protecao', 0)}"),
        ("Localizacao", item.get("localizacao", "--")),
    ]
    info_inner = info_rect.inflate(-8, -10)
    text_y = info_inner.y + 24
    row_height = 18
    cols = 2 if info_inner.width >= 260 else 1
    col_w = max(120, info_inner.width // cols)
    for idx, (label, value) in enumerate(info_pairs):
        col = idx % cols
        row = idx // cols
        y = text_y + row * row_height
        x = info_inner.x + col * col_w
        draw_text(surface, f"{label}:", FONTS["xs"], GRAY_80, (x, y))
        value_text = str(value)
        value_x = x + 72
        max_x = info_inner.x + min(info_inner.width, (col + 1) * col_w) - 4
        if value_x + FONTS["xs"].size(value_text)[0] > max_x:
            value_x = max(info_inner.x + col * col_w + 72, max_x - FONTS["xs"].size(value_text)[0])
        draw_text(surface, value_text, FONTS["xs"], WHITE, (value_x, y))

    desc_rect = pygame.Rect(inner.x, image_rect.bottom + 20, inner.width, 140)
    draw_form_box(surface, desc_rect, "Descricao*", item.get("descricao", ""))

    info1_rect = pygame.Rect(inner.x, desc_rect.bottom + 14, inner.width, 86)
    draw_form_box(surface, info1_rect, "Info adicional 1", item.get("info1", ""))

    info2_rect = pygame.Rect(inner.x, info1_rect.bottom + 14, inner.width, 86)
    draw_form_box(surface, info2_rect, "Info adicional 2", item.get("info2", ""))


def draw_filter_row(surface, start_rect, state):
    filter_rects = []
    labels = ["Todos"] + CATEGORIES
    active = (state.get("filters", {}).get("category") or "Todos").lower()
    x = start_rect.x
    y = start_rect.y
    max_width = start_rect.width
    for label in labels:
        text = label.upper()
        w = max(80, FONTS["xs"].size(text)[0] + 24)
        if x + w > start_rect.x + max_width:
            y += 34
            x = start_rect.x
        rect = pygame.Rect(x, y, w, 28)
        is_active = active == label.lower()
        color = PURPLE if is_active else GRAY_40
        pygame.draw.rect(surface, color, rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, rect, 1, border_radius=4)
        draw_text(surface, text, FONTS["xs"], WHITE, rect.center, center=True)
        filter_rects.append((label, rect))
        x = rect.right + 6
    return filter_rects, y + 28


def draw_right_panel(surface, rect, state, rects):
    pygame.draw.rect(surface, BLACK, rect)
    pygame.draw.rect(surface, WHITE, rect, 1)
    inner = rect.inflate(-10, -10)

    add_rect = pygame.Rect(inner.right - 120, inner.y, 120, 32)
    pygame.draw.rect(surface, GREEN, add_rect)
    pygame.draw.rect(surface, WHITE, add_rect, 1)
    draw_text(surface, "ADICIONAR", FONTS["sm_b"], BLACK, add_rect.center, center=True)
    rects["buttons"]["add"] = add_rect

    filter_width = max(160, inner.width - add_rect.width - 16)
    filter_rect = pygame.Rect(inner.x, inner.y, filter_width, 28)
    filters, filters_bottom = draw_filter_row(surface, filter_rect, state)
    rects["filters"] = filters

    search_rect = pygame.Rect(inner.x, filters_bottom + 10, inner.width, 32)
    pygame.draw.rect(surface, BLACK, search_rect)
    pygame.draw.rect(surface, WHITE if state.get("focus") == "search" else GRAY_60, search_rect, 1)
    placeholder = "Pesquisar por nome..."
    text = state.get("search", "")
    draw_text(surface, placeholder, FONTS["xs"], GRAY_80, (search_rect.x, search_rect.y - 16))
    draw_text(surface, text, FONTS["sm"], WHITE, (search_rect.x + 6, search_rect.y + 6))
    rects["fields"]["search"] = search_rect
    if state.get("focus") == "search":
        cursor = state.get("cursor", {}).get("search", len(text))
        cursor = max(0, min(cursor, len(text)))
        caret_x = search_rect.x + 6 + FONTS["sm"].size(text[:cursor])[0]
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            pygame.draw.line(surface, WHITE, (caret_x, search_rect.y + 6), (caret_x, search_rect.bottom - 6), 1)

    list_top = search_rect.bottom + 12
    list_rect = pygame.Rect(inner.x, list_top, inner.width, inner.bottom - list_top - 16)
    rects["list_area"] = list_rect
    rows = draw_item_list(surface, list_rect, state)
    rects["rows"] = rows

    if state.get("status"):
        draw_text(surface, state["status"], FONTS["xs"], state.get("status_color", WHITE), (inner.x, inner.bottom - 18))


def draw_item_list(surface, list_rect, state):
    pygame.draw.rect(surface, BLACK, list_rect)
    pygame.draw.rect(surface, WHITE, list_rect, 1)
    header_h = 32
    pygame.draw.rect(surface, GRAY_25, (list_rect.x, list_rect.y, list_rect.width, header_h))
    draw_text(surface, "IMAGEM DO ITEM*", FONTS["xs"], WHITE, (list_rect.x + 12, list_rect.y + 8))
    draw_text(surface, "NOME DO ITEM*", FONTS["xs"], WHITE, (list_rect.x + 130, list_rect.y + 8))

    filtered = ensure_filtered(state)
    row_h = 78
    max_rows = max(1, (list_rect.height - header_h) // row_h)
    clamp_scroll(state, max_rows)
    start_index = state.get("scroll", 0)
    rows = []
    y = list_rect.y + header_h
    highlight_idx = state.get("selected")
    for pos in range(start_index, min(start_index + max_rows, len(filtered))):
        idx, item = filtered[pos]
        row_rect = pygame.Rect(list_rect.x, y, list_rect.width, row_h)
        selected = highlight_idx == idx
        pygame.draw.rect(surface, GRAY_15 if pos % 2 else GRAY_25, row_rect)
        pygame.draw.rect(surface, PURPLE if selected else WHITE, row_rect, 2 if selected else 1)
        image_rect = pygame.Rect(row_rect.x + 12, y + 10, 86, row_h - 20)
        pygame.draw.rect(surface, BLACK, image_rect)
        pygame.draw.rect(surface, WHITE, image_rect, 1)
        draw_text(surface, "imagem", FONTS["xs"], GRAY_80, image_rect.center, center=True)

        text_x = image_rect.right + 10
        draw_text(surface, item.get("name", "Sem nome"), FONTS["sm_b"], WHITE, (text_x, y + 8))
        stats_line = f"Dano: {item.get('dano', '--')}   Alcance: {item.get('alcance', '--')}"
        draw_text(surface, stats_line, FONTS["xs"], WHITE, (text_x, y + 30))
        cat_line = f"Categoria: {item.get('category', '--')}   Tipo: {item.get('tipo', '--')}"
        draw_text(surface, cat_line, FONTS["xs"], GRAY_80, (text_x, y + 48))
        rows.append((idx, row_rect))
        y += row_h
    if not rows:
        draw_text(surface, "Nenhum item listado.", FONTS["sm"], GRAY_80, (list_rect.x + 12, list_rect.y + header_h + 12))
    return rows


def handle_mouse(pos, rects, state):
    search_rect = rects["fields"].get("search")
    if search_rect and search_rect.collidepoint(pos):
        state["focus"] = "search"
        state.setdefault("cursor", {})["search"] = len(state.get("search", ""))
        return True
    for label, rect in rects.get("filters", []):
        if rect.collidepoint(pos):
            state.setdefault("filters", {})["category"] = label
            state["scroll"] = 0
            ensure_filtered(state)
            return True
    add_rect = rects["buttons"].get("add")
    if add_rect and add_rect.collidepoint(pos):
        set_status(state, "Fluxo de cadastro sera implementado futuramente.", ORANGE)
        return True
    for key, rect in rects["buttons"].items():
        if key == "add":
            continue
        if rect.collidepoint(pos):
            set_status(state, f"Acao '{key}' aguardando implementacao.", ORANGE)
            return True
    for idx, row_rect in rects.get("rows", []):
        if row_rect.collidepoint(pos):
            state["selected"] = idx
            set_status(state, "", WHITE)
            return True
    list_area = rects.get("list_area")
    if list_area and list_area.collidepoint(pos):
        state["focus"] = None
    return False


def handle_mousewheel(delta, rects, state, pos=None):
    list_area = rects.get("list_area")
    if pos and list_area and list_area.collidepoint(pos):
        state["scroll"] = max(0, min(state.get("scroll", 0) - delta, state.get("max_scroll", 0)))
        return True
    return False


def handle_text_input(event, state):
    if state.get("focus") == "search":
        ch = event.text
        if ch.isprintable():
            current = state.get("search", "")
            cursor = state.setdefault("cursor", {}).get("search", len(current))
            cursor = max(0, min(len(current), cursor))
            new_text = current[:cursor] + ch + current[cursor:]
            state["search"] = new_text[:48]
            state["cursor"]["search"] = cursor + len(ch)
            ensure_filtered(state)
            return True
    return False


def handle_key(event, state):
    if state.get("focus") == "search":
        current = state.get("search", "")
        cursor = state.setdefault("cursor", {}).get("search", len(current))
        if event.key == pygame.K_BACKSPACE:
            if cursor > 0:
                state["search"] = current[: cursor - 1] + current[cursor:]
                state["cursor"]["search"] = cursor - 1
                ensure_filtered(state)
            return True
        if event.key == pygame.K_DELETE:
            if cursor < len(current):
                state["search"] = current[:cursor] + current[cursor + 1 :]
                ensure_filtered(state)
            return True
        if event.key == pygame.K_LEFT:
            state["cursor"]["search"] = max(0, cursor - 1)
            return True
        if event.key == pygame.K_RIGHT:
            state["cursor"]["search"] = min(len(current), cursor + 1)
            return True
        if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            state["focus"] = None
            return True
        return False
    if event.key == pygame.K_DOWN:
        select_next(state, 1)
        return True
    if event.key == pygame.K_UP:
        select_next(state, -1)
        return True
    if event.key == pygame.K_PAGEUP:
        state["scroll"] = max(0, state.get("scroll", 0) - 3)
        return True
    if event.key == pygame.K_PAGEDOWN:
        state["scroll"] = min(state.get("max_scroll", 0), state.get("scroll", 0) + 3)
        return True
    return False


def make_default_state():
    return {
        "base_limit": 12,
        "weight_bonus": 0,
        "items": clone_default_items(),
        "limit_slots": [0, 0, 0, 0, 0, 0],
        "total_slots": [0, 0, 0, 0, 0, 0],
        "filters": {"category": "Todos"},
        "search": "",
        "selected": 0,
        "focus": None,
        "cursor": {"search": 0},
        "scroll": 0,
        "status": "",
        "status_color": WHITE,
    }


INVENTARIO_STATE = make_default_state()


def main():
    running = True
    while running:
        rects = draw_inventory_panel(WINDOW, INVENTARIO_STATE)
        pygame.display.flip()
        CLOCK.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.TEXTINPUT:
                handle_text_input(event, INVENTARIO_STATE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and INVENTARIO_STATE.get("focus") is None:
                    running = False
                else:
                    handle_key(event, INVENTARIO_STATE)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    handle_mouse(event.pos, rects, INVENTARIO_STATE)
            elif event.type == pygame.MOUSEWHEEL:
                pos = pygame.mouse.get_pos()
                handle_mousewheel(event.y, rects, INVENTARIO_STATE, pos)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
