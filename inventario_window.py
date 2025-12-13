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
    "xs": pygame.font.SysFont("arial", 11),
    "sm": pygame.font.SysFont("arial", 14),
    "sm_b": pygame.font.SysFont("arial", 14, bold=True),
    "md": pygame.font.SysFont("arial", 18, bold=True),
    "lg": pygame.font.SysFont("arial", 26, bold=True),
}

CATEGORIES = ["Armas", "Municao", "Protecao", "Magikos", "Coletaveis", "Itens chave", "Componentes"]

# Itens de exemplo removidos; lista inicia vazia para uso real.
DEFAULT_ITEMS = []

OPTION_VALUES = {
    "category": ["---"] + CATEGORIES,
    "space": ["---", "0", "1", "2", "3", "4", "5"],
    "tipo": ["---", "Corpo a corpo", "Distancia", "Explosivo", "M. CURTA", "M. LONGA", "M. ESPECIAL", "Energia", "Morte", "conhecimento", "sangue", "Medo"],
    "alcance": ["---", "Perto", "6m", "9m", "12m", "18m"],
    "empunhadura": ["---", "Leve", "Uma mao", "Duas maos"],
    "dano": ["---", "1D4", "1D6", "1D8", "1D10", "1D12", "1D20", "1D100"],
    "protecao": ["---", "1", "2", "3", "4", "5"],
}

OPTION_FIELDS = {"space", "tipo", "alcance", "empunhadura", "dano", "protecao", "category"}


def _normalize_text(txt):
    mapping = str.maketrans("áàãâäéèêëíìîïóòõôöúùûüçÁÀÃÂÄÉÈÊËÍÌÎÏÓÒÕÔÖÚÙÛÜÇ", "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC")
    return (txt or "").translate(mapping).lower().strip()


def normalize_category_key(category):
    cat = _normalize_text(category)
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
    if "chave" in cat:
        return "itens chave"
    if cat.startswith("comp"):
        return "componentes"
    return cat


def get_allowed_option_fields(category):
    cat = normalize_category_key(category)
    if cat == "arma":
        return {"space", "tipo", "alcance", "empunhadura", "dano"}
    if cat == "municao":
        return {"space", "tipo"}
    if cat == "protecao":
        return {"space", "protecao"}
    if cat == "magikos":
        return {"space", "tipo", "dano"}
    if cat in ("coletaveis", "itens chave", "componentes"):
        return {"space"}
    return set(OPTION_FIELDS) - {"category"}


def get_category_options(category, field):
    cat = normalize_category_key(category)
    base = OPTION_VALUES.get(field)
    if base is None:
        return None
    allowed = get_allowed_option_fields(category)
    if field in OPTION_FIELDS and field != "category" and field not in allowed:
        return []
    if cat == "arma":
        if field == "protecao":
            return []
        if field == "tipo":
            return ["---", "Corpo a corpo", "Distancia", "Explosivo"]
        if field == "space":
            return ["---", "1", "2", "3", "4", "5"]
        return base
    if cat == "municao":
        if field == "tipo":
            return ["---", "M. CURTA", "M. LONGA", "M. ESPECIAL"]
        if field == "space":
            return ["1", "2", "3", "4", "5"]
        return []
    if cat == "protecao":
        if field == "space":
            return ["---", "1", "2", "3"]
        if field == "protecao":
            return base
        return []
    if cat == "magikos":
        if field == "space":
            return ["---", "1", "2", "3", "4", "5"]
        if field == "tipo":
            return ["---", "Energia", "Morte", "conhecimento", "sangue", "Medo"]
        if field == "dano":
            return OPTION_VALUES["dano"]
        return []
    if cat in ("coletaveis", "itens chave", "componentes"):
        if field == "space":
            return ["---", "1", "2", "3", "4", "5"]
        return []
    return base


def get_form_options(form, field):
    """Retorna lista de opcoes validas para o campo conforme formulario."""
    if field == "category":
        return OPTION_VALUES["category"]
    category = (form or {}).get("category")
    return get_category_options(category, field)


def normalize_form_for_category(form):
    cat = form.get("category", "")
    allowed = get_allowed_option_fields(cat)
    for field in OPTION_FIELDS:
        if field == "category":
            continue
        if field not in allowed:
            form[field] = ""
            continue
        opts = get_category_options(cat, field)
        if opts is None:
            continue
        if not opts:
            form[field] = ""
            continue
        if form.get(field) not in opts:
            form[field] = opts[0]
    return form


def clone_default_items():
    return [item.copy() for item in DEFAULT_ITEMS]


def make_blank_item(state):
    """Cria item basico para adicao rapida respeitando filtro atual."""
    current_filter = (state.get("filters", {}).get("category") or "Todos").strip()
    category = current_filter if current_filter.lower() != "todos" else OPTION_VALUES["category"][0]
    base_name = ""
    return {
        "name": base_name,
        "category": category,
        "space": OPTION_VALUES["space"][0],
        "tipo": OPTION_VALUES["tipo"][0],
        "alcance": OPTION_VALUES["alcance"][0],
        "empunhadura": OPTION_VALUES["empunhadura"][0],
        "dano": OPTION_VALUES["dano"][0],
        "protecao": OPTION_VALUES["protecao"][0],
        "descricao": "",
        "localizacao": "",
        "info1": "",
        "info2": "",
        "image_path": None,
    }


def add_new_item(state):
    state.setdefault("items", [])
    new_item = make_blank_item(state)
    state["items"].append(new_item)
    ensure_filtered(state)
    state["selected"] = len(state["items"]) - 1
    set_status(state, "Item adicionado.", GREEN)
    return new_item


def open_add_modal(state):
    blank = make_blank_item(state)
    form = {}
    for k, v in blank.items():
        if k == "_image_cache":
            continue
        if k in OPTION_VALUES:
            form[k] = v if v in OPTION_VALUES[k] else OPTION_VALUES[k][0]
        else:
            form[k] = "" if v is None else str(v)
    normalize_form_for_category(form)
    state["modal"] = {
        "type": "add_item",
        "form": form,
        "focus": "name",
        "cursor": {"name": len(form.get("name", ""))},
        "dropdown": None,
        "scrolls": {"descricao": 0, "info1": 0, "info2": 0},
        "scroll_max": {"descricao": 0, "info1": 0, "info2": 0},
    }


def close_modal(state):
    state["modal"] = None


def build_item_from_form(state, form):
    normalize_form_for_category(form)
    item = make_blank_item(state)
    item["name"] = (form.get("name") or "").strip()
    item["category"] = (form.get("category") or item["category"]).strip() or OPTION_VALUES["category"][0]
    item["space"] = (form.get("space") or item["space"]).strip() or OPTION_VALUES["space"][0]
    item["tipo"] = (form.get("tipo") or item["tipo"]).strip() or OPTION_VALUES["tipo"][0]
    item["alcance"] = (form.get("alcance") or item["alcance"]).strip() or OPTION_VALUES["alcance"][0]
    item["empunhadura"] = (form.get("empunhadura") or item["empunhadura"]).strip() or OPTION_VALUES["empunhadura"][0]
    item["dano"] = (form.get("dano") or item["dano"]).strip() or OPTION_VALUES["dano"][0]
    item["protecao"] = (form.get("protecao") or item["protecao"]).strip() or OPTION_VALUES["protecao"][0]
    item["descricao"] = form.get("descricao") or ""
    item["localizacao"] = (form.get("localizacao") or "").strip()
    item["info1"] = form.get("info1") or ""
    item["info2"] = form.get("info2") or ""
    img_val = form.get("image_path")
    item["image_path"] = img_val if img_val else None
    return item


def confirm_add_modal(state):
    modal = state.get("modal") or {}
    form = modal.get("form") or {}
    state.setdefault("items", [])
    mode = modal.get("type") or "add_item"
    if mode == "edit_item" and "edit_index" in modal and modal["edit_index"] is not None:
        idx = modal["edit_index"]
        if 0 <= idx < len(state["items"]):
            updated = build_item_from_form(state, form)
            state["items"][idx] = updated
            ensure_filtered(state)
            state["selected"] = idx
            close_modal(state)
            set_status(state, "Item atualizado.", GREEN)
            return updated
    new_item = build_item_from_form(state, form)
    state["items"].append(new_item)
    ensure_filtered(state)
    state["selected"] = len(state["items"]) - 1
    close_modal(state)
    set_status(state, "Item adicionado.", GREEN)
    return new_item


def wrap_text(text, font, max_width):
    """Divide texto em linhas respeitando largura maxima, quebrando palavras longas se preciso."""
    lines = []
    current = ""
    for word in (text or "").split(" "):
        candidate = (current + " " + word).strip() if current else word
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            # quebra palavra longa em blocos
            chunk = ""
            for ch in word:
                if font.size(chunk + ch)[0] <= max_width:
                    chunk += ch
                else:
                    lines.append(chunk)
                    chunk = ch
            current = chunk
    if current:
        lines.append(current)
    return lines or [""]


def wrap_text_clamped(text, font, max_width, max_height):
    """Divide texto respeitando largura e altura."""
    base_lines = wrap_text(text or "", font, max_width)
    line_step = font.get_height() + 2
    max_lines = max(1, max_height // max(1, line_step))
    if len(base_lines) <= max_lines:
        return base_lines
    trimmed = base_lines[:max_lines]
    if trimmed:
        last = trimmed[-1]
        trimmed[-1] = (last[: max(0, len(last) - 3)] + "...") if len(last) > 3 else "..."
    return trimmed


def wrap_text_with_starts(text, font, max_width):
    """Quebra texto em largura fixa e retorna linhas e indice inicial de cada linha."""
    text = text or ""
    lines = []
    starts = []
    current = ""
    start_idx = 0
    for i, ch in enumerate(text):
        if ch == "\n":
            lines.append(current)
            starts.append(start_idx)
            current = ""
            start_idx = i + 1
            continue
        candidate = current + ch
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            starts.append(start_idx)
            current = ch if font.size(ch)[0] <= max_width else ""
            start_idx = i
    if current or not lines:
        lines.append(current)
        starts.append(start_idx)
    return lines, starts

def clean_option(value):
    """Retorna texto sem marcador '---'."""
    v = (value or "").strip()
    return "" if v == "---" else v


def ellipsize(text, font, max_width):
    """Trunca texto com reticencias para caber na largura."""
    if font.size(text)[0] <= max_width:
        return text
    ellipsis = "..."
    allowed = text
    while allowed and font.size(allowed + ellipsis)[0] > max_width:
        allowed = allowed[:-1]
    return (allowed + ellipsis) if allowed else ellipsis


def load_scaled_image(path, target_size):
    """Carrega e redimensiona uma imagem preservando proporcao para caber em target_size."""
    if not path or str(path).strip() == "---":
        return None
    try:
        img = pygame.image.load(path)
        img = img.convert_alpha()
        iw, ih = img.get_size()
        tw, th = target_size
        if iw <= 0 or ih <= 0 or tw <= 0 or th <= 0:
            return None
        scale = min(tw / iw, th / ih)
        new_size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
        return pygame.transform.smoothscale(img, new_size)
    except Exception as exc:  # noqa: BLE001
        print(f"Erro ao carregar imagem '{path}': {exc}")
        return None


def choose_image_file():
    """Abre dialogo para selecionar imagem e retorna o caminho escolhido."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        file_path = filedialog.askopenfilename(
            title="Selecionar imagem do item",
            filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("Todos os arquivos", "*.*")],
        )
        root.destroy()
        return file_path
    except Exception as exc:  # noqa: BLE001
        print(f"Erro ao abrir seletor de arquivos: {exc}")
        return None


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


def match_category_name(value):
    """Retorna o nome oficial da categoria ou None."""
    norm = normalize_category_key(value)
    for cat in CATEGORIES:
        if normalize_category_key(cat) == norm:
            return cat
    return None


def get_category_counts(state):
    counts = {cat: 0 for cat in CATEGORIES}
    for item in state.get("items", []):
        cat = match_category_name(item.get("category"))
        if cat:
            counts[cat] += 1
    return counts


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
    rects = {"filters": [], "rows": [], "buttons": {}, "fields": {}, "list_area": None, "scroll_fields": []}

    panel_rect = pygame.Rect(8, 2, WIDTH - 16, HEIGHT - 16)
    pygame.draw.rect(surface, GRAY_15, panel_rect)
    pygame.draw.rect(surface, WHITE, panel_rect, 2)
    inner = panel_rect.inflate(-16, -16)

    # draw_text(surface, "INVENTARIO", FONTS["md"], WHITE, (inner.x, inner.y - 4))
    limits_rect = pygame.Rect(inner.x, inner.y + 2, inner.width, 170)

    draw_limits_section(surface, limits_rect, state)

    content_top = limits_rect.bottom + 6
    left_width = int(inner.width * 0.50)
    left_rect = pygame.Rect(inner.x, content_top, left_width - 2, inner.bottom - content_top)
    right_rect = pygame.Rect(left_rect.right + 2, content_top, inner.right - left_rect.right - 6, left_rect.height)

    draw_left_detail(surface, left_rect, state, rects)
    draw_right_panel(surface, right_rect, state, rects)

    if state.get("modal"):
        rects["modal"] = draw_modal(surface, state)

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


def draw_limits_section(surface, rect, state):
    pygame.draw.rect(surface, BLACK, rect)
    pygame.draw.rect(surface, WHITE, rect, 1)
    inner = rect.inflate(-12, -12)
    
    weight_rect = pygame.Rect(inner.right - 50, inner.y + 4, 50, 36)
    draw_text(surface, "PESO", FONTS["sm"], WHITE, (weight_rect.x - 40, weight_rect.y + 12))
    pygame.draw.rect(surface, BLACK, weight_rect)
    pygame.draw.rect(surface, WHITE, weight_rect, 1)
    weight_text = f"{get_total_weight(state):02d}/{get_weight_limit(state):02d}"
    draw_text(surface, weight_text, FONTS["sm_b"], WHITE, weight_rect.center, center=True)

    grid_top = max(inner.y + 36, weight_rect.bottom + 10)
    counts = get_category_counts(state)
    cols = 4
    col_gap = 8
    row_gap = 10
    rows = (len(CATEGORIES) + cols - 1) // cols
    box_w = max(80, (inner.width - col_gap * (cols - 1)) // cols)
    available_height = inner.bottom - grid_top
    box_h = max(48, (available_height - row_gap * (rows - 1)) // max(1, rows))

    total = len(CATEGORIES)
    for row in range(rows):
        start_idx = row * cols
        remaining = max(0, total - start_idx)
        if remaining <= 0:
            break
        cols_in_row = min(cols, remaining)
        row_width = cols_in_row * box_w + max(0, cols_in_row - 1) * col_gap
        base_x = inner.centerx - row_width // 2
        y = grid_top + row * (box_h + row_gap)
        for col in range(cols_in_row):
            idx = start_idx + col
            cat = CATEGORIES[idx]
            x = base_x + col * (box_w + col_gap)
            box_rect = pygame.Rect(x, y, box_w, box_h)
            pygame.draw.rect(surface, BLACK, box_rect)
            pygame.draw.rect(surface, WHITE, box_rect, 1)
            draw_text(surface, cat.upper(), FONTS["xs"], WHITE, (box_rect.centerx, box_rect.y + 6), center=True)
            count = counts.get(cat, 0)
            count_text = f"{count:02d}"
            draw_text(surface, count_text, FONTS["md"], WHITE, box_rect.center, center=True)


def draw_form_box(surface, rect, label, text, scroll_offset=0, return_max=False):
    pygame.draw.rect(surface, BLACK, rect)
    pygame.draw.rect(surface, WHITE, rect, 1)
    draw_text(surface, label, FONTS["xs"], WHITE, (rect.x, rect.y - 16))
    lines = wrap_text(text or "--", FONTS["xs"], rect.width - 12)
    line_h = FONTS["xs"].get_height() + 2
    max_lines = max(1, rect.height // line_h)
    max_scroll = max(0, len(lines) - max_lines)
    start = max(0, min(scroll_offset, max_scroll))
    y = rect.y + 6
    for line in lines[start : start + max_lines]:
        draw_text(surface, line, FONTS["xs"], WHITE, (rect.x + 6, y))
        y += line_h
    if return_max:
        return max_scroll


def draw_left_detail(surface, detail_rect, state, rects):
    pygame.draw.rect(surface, BLACK, detail_rect)
    pygame.draw.rect(surface, WHITE, detail_rect, 1)
    inner = detail_rect.inflate(-10, -10)
    item = get_selected_item(state)
    if not item:
        draw_text(surface, "Nenhum item selecionado.", FONTS["sm"], GRAY_80, (inner.x, inner.y))
        return

    image_rect = pygame.Rect(inner.x, inner.y, 140, 140)
    rects["buttons"]["image_upload"] = image_rect
    pygame.draw.rect(surface, BLACK, image_rect)
    pygame.draw.rect(surface, WHITE, image_rect, 2)
    target_size = (image_rect.width - 6, image_rect.height - 6)
    img_surface = None
    image_path = item.get("image_path")
    if image_path == "---":
        image_path = None
    cache = item.get("_image_cache", {})
    cache_key = (image_path, target_size)
    if cache.get("key") == cache_key:
        img_surface = cache.get("surf")
    elif image_path:
        loaded = load_scaled_image(image_path, target_size)
        if loaded:
            img_surface = loaded
            item["_image_cache"] = {"key": cache_key, "surf": loaded}
    if img_surface:
        img_rect = img_surface.get_rect(center=image_rect.center)
        surface.blit(img_surface, img_rect)
    else:
        draw_text(surface, "imagem do\nitem*", FONTS["xs"], WHITE, image_rect.center, center=True)

    info_rect = pygame.Rect(image_rect.right + 10, inner.y, inner.width - image_rect.width - 10, 145)
    pygame.draw.rect(surface, BLACK, info_rect)
    pygame.draw.rect(surface, WHITE, info_rect, 1)
    title_text = ellipsize(item.get("name") or "Nome do item*", FONTS["sm_b"], info_rect.width - 12)
    draw_text(surface, title_text, FONTS["sm_b"], WHITE, (info_rect.x + 6, info_rect.y + 6))
    info_pairs = [
        ("Categoria", clean_option(item.get("category", ""))),
        ("Espaco", clean_option(item.get("space", ""))),
        ("Tipo", clean_option(item.get("tipo", ""))),
        ("Alcance", clean_option(item.get("alcance", ""))),
        ("Punho", clean_option(item.get("empunhadura", ""))),
        ("Dano", clean_option(item.get("dano", ""))),
        ("Protecao", f"+{clean_option(item.get('protecao', ''))}" if clean_option(item.get("protecao", "")) else ""),
        ("Achado", clean_option(item.get("localizacao", ""))),
    ]
    info_inner = info_rect.inflate(-8, -8)
    text_y = info_inner.y + 20
    font_xs = FONTS["xs"]
    cols = 2
    col_gap = 12
    col_w = max(80, (info_inner.width - col_gap * (cols - 1)) // cols)
    valid_pairs = [(label, value) for label, value in info_pairs if value]
    line_h = font_xs.get_height()
    col_positions = [info_inner.x + i * (col_w + col_gap) for i in range(cols)]
    col_y = [text_y for _ in range(cols)]

    block_fields = {"Achado"}

    for label, value in valid_pairs:
        col_idx = min(range(cols), key=lambda idx: col_y[idx])
        x = col_positions[col_idx]
        y = col_y[col_idx]
        label_text = f"{label}:"
        if label in block_fields:
            draw_text(surface, label_text, font_xs, GRAY_80, (x, y))
            block_lines = wrap_text(str(value), font_xs, col_w)
            line_y = y + line_h + 2
            for line in block_lines:
                draw_text(surface, line, font_xs, WHITE, (x, line_y))
                line_y += line_h
            col_y[col_idx] = line_y + 4
            continue
        label_surface_w = font_xs.size(label_text)[0]
        label_w = min(label_surface_w, col_w - 40)
        label_lines = [label_text]
        label_height = line_h
        if label_surface_w > col_w - 4:
            label_lines = wrap_text(label_text, font_xs, col_w - 4)
            label_height = len(label_lines) * line_h
        value_width = max(40, col_w - label_w - 4)
        default_label_w = min(max(label_surface_w, 32), col_w - 40)
        value_width = max(40, col_w - default_label_w - 4)
        value_lines = wrap_text(str(value), font_xs, value_width)
        value_height = len(value_lines) * line_h
        label_height = line_h
        if len(value_lines) > 1:
            label_w = max(default_label_w, min(label_surface_w, col_w - value_width - 4))
        else:
            available = col_w - (font_xs.size(value_lines[0])[0] + 4)
            if label_surface_w > available:
                label_w = max(default_label_w, available)
            else:
                label_w = label_surface_w
        line_y = y
        for line in label_lines:
            draw_text(surface, line, font_xs, GRAY_80, (x, line_y))
            line_y += line_h
        line_y = y
        for line in value_lines:
            draw_text(surface, line, font_xs, WHITE, (x + label_w + 4, line_y))
            line_y += line_h
        col_y[col_idx] = max(line_y, y + label_height) + 4
        draw_text(surface, label_text, font_xs, GRAY_80, (x, y))
        value_lines = wrap_text(str(value), font_xs, value_width)
        line_y = y
        for line in value_lines:
            draw_text(surface, line, font_xs, WHITE, (x + label_w + 4, line_y))
            line_y += line_h
        col_y[col_idx] = line_y + 4

    scrolls = state.setdefault("scrolls", {"descricao": 0, "info1": 0, "info2": 0})
    scroll_max = state.setdefault("scroll_max", {})
    rects["scroll_fields"] = rects.get("scroll_fields", [])

    def dyn_height(text, min_h, max_h, width):
        lines = wrap_text(text or "--", FONTS["xs"], width - 12)
        h = len(lines) * (FONTS["xs"].get_height() + 2) + 8
        return max(min_h, min(max_h, h))

    start_y = image_rect.bottom + 30
    min_desc, max_desc = 54, 220
    min_info, max_info = 54, 180
    available = inner.bottom - start_y - 80  # space for buttons
    desired_desc = dyn_height(item.get("descricao", ""), min_desc, max_desc, inner.width)
    desired_info1 = dyn_height(item.get("info1", ""), min_info, max_info, inner.width)
    desired_info2 = dyn_height(item.get("info2", ""), min_info, max_info, inner.width)
    total_desired = desired_desc + 25 + desired_info1 + 20 + desired_info2
    if total_desired > available and total_desired > 0:
        scale = available / total_desired
        desired_desc = max(min_desc, int(desired_desc * scale))
        desired_info1 = max(min_info, int(desired_info1 * scale))
        desired_info2 = max(min_info, int(desired_info2 * scale))

    desc_rect = pygame.Rect(inner.x, start_y, inner.width, desired_desc)
    scroll_max["descricao"] = draw_form_box(
        surface, desc_rect, "Descricao*", item.get("descricao", ""), scrolls.get("descricao", 0), True
    )
    rects["scroll_fields"].append(("descricao", desc_rect))

    info1_rect = pygame.Rect(inner.x, desc_rect.bottom + 25, inner.width, desired_info1)
    scroll_max["info1"] = draw_form_box(
        surface, info1_rect, "Info adicional 1", item.get("info1", ""), scrolls.get("info1", 0), True
    )
    rects["scroll_fields"].append(("info1", info1_rect))

    info2_rect = pygame.Rect(inner.x, info1_rect.bottom + 20, inner.width, desired_info2)
    scroll_max["info2"] = draw_form_box(
        surface, info2_rect, "Info adicional 2", item.get("info2", ""), scrolls.get("info2", 0), True
    )
    rects["scroll_fields"].append(("info2", info2_rect))

    btn_h = 32
    btn_w = 120
    btn_gap = 10
    btn_area_y = info2_rect.bottom + 12
    edit_rect = pygame.Rect(inner.x, btn_area_y, btn_w, btn_h)
    remove_rect = pygame.Rect(edit_rect.right + btn_gap, btn_area_y, btn_w, btn_h)
    rects["buttons"]["edit_item"] = edit_rect
    rects["buttons"]["remove_item"] = remove_rect
    pygame.draw.rect(surface, ORANGE, edit_rect)
    pygame.draw.rect(surface, WHITE, edit_rect, 1)
    pygame.draw.rect(surface, RED, remove_rect)
    pygame.draw.rect(surface, WHITE, remove_rect, 1)
    draw_text(surface, "EDITAR", FONTS["sm_b"], BLACK, edit_rect.center, center=True)
    draw_text(surface, "REMOVER", FONTS["sm_b"], BLACK, remove_rect.center, center=True)


def draw_filter_row(surface, start_rect, state):
    filter_rects = []
    labels = ["Todos"] + CATEGORIES
    active = (state.get("filters", {}).get("category") or "Todos").lower()
    cols = 2
    rows = 4
    col_gap = 6
    row_gap = 6
    btn_h = 22
    font = FONTS["xs"]
    col_w = max(70, (start_rect.width - col_gap * (cols - 1)) // cols)
    for idx, label in enumerate(labels):
        col = 0 if idx < rows else 1
        row = idx % rows
        text = label.upper()
        text_w = font.size(text)[0]
        w = min(col_w, max(70, text_w + 16))
        x_base = start_rect.x + col * (col_w + col_gap)
        x = x_base + max(0, (col_w - w) // 2)
        y = start_rect.y + row * (btn_h + row_gap)
        rect = pygame.Rect(x, y, w, btn_h)
        is_active = active == label.lower()
        color = PURPLE if is_active else GRAY_40
        pygame.draw.rect(surface, color, rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, rect, 1, border_radius=4)
        draw_text(surface, text, font, WHITE, rect.center, center=True)
        filter_rects.append((label, rect))
    filters_bottom = start_rect.y + rows * btn_h + (rows - 1) * row_gap
    return filter_rects, filters_bottom


def draw_modal(surface, state):
    modal = state.get("modal") or {}
    overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    modal_w, modal_h = 600, 620
    modal_rect = pygame.Rect(0, 0, modal_w, modal_h)
    modal_rect.center = surface.get_rect().center
    pygame.draw.rect(surface, GRAY_25, modal_rect, border_radius=6)
    pygame.draw.rect(surface, WHITE, modal_rect, 2, border_radius=6)

    title = "Adicionar novo item"
    draw_text(surface, title, FONTS["md"], WHITE, (modal_rect.x + 16, modal_rect.y + 14))
    draw_text(surface, "Preencha os campos e confirme para adicionar.", FONTS["xs"], GRAY_80, (modal_rect.x + 16, modal_rect.y + 40))

    form = modal.get("form") or {}
    normalize_form_for_category(form)
    focus_key = modal.get("focus")
    allowed_fields = get_allowed_option_fields(form.get("category"))
    options_map = {f: get_form_options(form, f) for f in OPTION_FIELDS}
    fields_rects = {}

    padding_x = modal_rect.x + 16
    padding_y = modal_rect.y + 68
    col_gap = 10
    row_gap = 8
    input_h = 26
    col_w = (modal_w - 32 - col_gap) // 2
    label_height = FONTS["xs"].get_height()
    label_spacing = 6
    row_stride = label_height + label_spacing + input_h + row_gap

    base_small_fields = [
        ("name", "Nome"),
        ("category", "Categoria"),
        ("space", "Espaco"),
        ("tipo", "Tipo"),
        ("alcance", "Alcance"),
        ("empunhadura", "Punho"),
        ("dano", "Dano"),
        ("protecao", "Protecao"),
        ("localizacao", "Achado"),
    ]
    small_fields = []
    for key, label in base_small_fields:
        if key in OPTION_FIELDS and key != "category":
            if key not in allowed_fields:
                continue
            opts = options_map.get(key, OPTION_VALUES.get(key))
            if opts is not None and len(opts) == 0:
                continue
            if form.get(key) not in opts:
                form[key] = opts[0] if opts else form.get(key, "")
        small_fields.append((key, label))
    for idx, (key, label) in enumerate(small_fields):
        col = idx % 2
        row = idx // 2
        x = padding_x + col * (col_w + col_gap)
        y = padding_y + row * row_stride
        rect = pygame.Rect(x, y + label_height + label_spacing, col_w, input_h)
        is_focus = key == focus_key
        pygame.draw.rect(surface, BLACK, rect)
        pygame.draw.rect(surface, WHITE if is_focus else GRAY_60, rect, 1)
        draw_text(surface, label, FONTS["xs"], WHITE, (x, y))
        text_val = form.get(key, "")
        shown = ellipsize(text_val, FONTS["sm"], rect.width - 8)
        draw_text(surface, shown, FONTS["sm"], WHITE, (rect.x + 4, rect.y + 4))
        if key in OPTION_VALUES:
            tri_color = WHITE if is_focus else GRAY_80
            cx = rect.right - 10
            cy = rect.centery + 3
            pygame.draw.polygon(surface, tri_color, [(cx - 4, cy - 4), (cx + 4, cy - 4), (cx, cy)])
        elif is_focus:
            cur = modal.get("cursor", {}).get(key, len(text_val))
            cur = max(0, min(cur, len(text_val)))
            caret_x = rect.x + 4 + FONTS["sm"].size(text_val[:cur])[0]
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                pygame.draw.line(surface, WHITE, (caret_x, rect.y + 4), (caret_x, rect.bottom - 4), 1)
        fields_rects[key] = rect

    rows_small = (len(small_fields) + 1) // 2
    big_start_y = padding_y + rows_small * row_stride + 10
    big_fields = [
        ("image_path", "Imagem (clique para selecionar)"),
        ("descricao", "Descricao"),
        ("info1", "Info adicional 1"),
        ("info2", "Info adicional 2"),
    ]
    min_heights = {"image_path": 30, "descricao": 48, "info1": 48, "info2": 48}
    max_heights = {"image_path": 30, "descricao": 220, "info1": 180, "info2": 180}
    desired_heights = []
    for key, _ in big_fields:
        raw_text = form.get(key, "") or ""
        if key == "image_path":
            h = min_heights[key]
        else:
            lines = wrap_text(raw_text or "--", FONTS["sm"], modal_w - 40)
            h = len(lines) * (FONTS["sm"].get_height() + 2) + 8
            h = max(min_heights[key], min(max_heights[key], h))
        desired_heights.append(h)
    total_desired = sum(desired_heights) + 10 * (len(big_fields) - 1)
    available = modal_rect.bottom - (big_start_y) - 70  # leave space for buttons
    if total_desired > available and total_desired > 0:
        scale = available / total_desired
        for i in range(len(desired_heights)):
            key = big_fields[i][0]
            desired_heights[i] = max(min_heights[key], int(desired_heights[i] * scale))
    current_y = big_start_y
    for idx_b, (key, label) in enumerate(big_fields):
        h = desired_heights[idx_b]
        rect = pygame.Rect(padding_x, current_y + 14, modal_w - 32, h)
        is_focus = key == focus_key
        pygame.draw.rect(surface, BLACK, rect)
        pygame.draw.rect(surface, WHITE if is_focus else GRAY_60, rect, 1)
        draw_text(surface, label, FONTS["xs"], WHITE, (rect.x, current_y))
        raw_text = form.get(key, "") or ("---" if key == "image_path" else "")
        if key == "image_path":
            shown_text = ellipsize(raw_text, FONTS["sm"], rect.width - 8)
            draw_text(surface, shown_text, FONTS["sm"], WHITE, (rect.x + 4, rect.y + 6))
        else:
            scrolls = modal.setdefault("scrolls", {})
            scroll_max = modal.setdefault("scroll_max", {})
            lines, starts = wrap_text_with_starts(raw_text, FONTS["sm"], rect.width - 8)
            max_lines = max(1, (rect.height - 8) // (FONTS["sm"].get_height() + 2))
            caret_idx = modal.get("cursor", {}).get(key, len(raw_text))
            caret_idx = max(0, min(caret_idx, len(raw_text)))
            caret_line = 0
            for i, start_idx in enumerate(starts):
                end_idx = starts[i + 1] if i + 1 < len(starts) else len(raw_text)
                if start_idx <= caret_idx <= end_idx:
                    caret_line = i
                    break
            cur_scroll = max(0, min(scrolls.get(key, 0), max(0, len(lines) - max_lines)))
            if caret_line < cur_scroll:
                cur_scroll = caret_line
            elif caret_line >= cur_scroll + max_lines:
                cur_scroll = caret_line - max_lines + 1
            scrolls[key] = cur_scroll
            scroll_max[key] = max(0, len(lines) - max_lines)
            visible = lines[cur_scroll : cur_scroll + max_lines]
            y_text = rect.y + 4
            for i_line, line in enumerate(visible):
                draw_text(surface, line, FONTS["sm"], WHITE, (rect.x + 4, y_text))
                y_text += FONTS["sm"].get_height() + 2
            if is_focus and (pygame.time.get_ticks() // 400) % 2 == 0:
                rel_line = caret_line - cur_scroll
                if 0 <= rel_line < max_lines:
                    line_start_idx = starts[caret_line]
                    caret_sub = raw_text[line_start_idx:caret_idx]
                    caret_x = rect.x + 4 + FONTS["sm"].size(caret_sub)[0]
                    caret_y = rect.y + 4 + rel_line * (FONTS["sm"].get_height() + 2)
                    pygame.draw.line(surface, WHITE, (caret_x, caret_y), (caret_x, caret_y + FONTS["sm"].get_height()), 1)
        fields_rects[key] = rect
        current_y = rect.bottom + 10

    btn_w, btn_h = 140, 34
    btn_y = modal_rect.bottom - btn_h - 16
    cancel_rect = pygame.Rect(modal_rect.x + 16, btn_y, btn_w, btn_h)
    add_rect = pygame.Rect(modal_rect.right - btn_w - 16, btn_y, btn_w, btn_h)
    pygame.draw.rect(surface, GRAY_40, cancel_rect, border_radius=4)
    pygame.draw.rect(surface, WHITE, cancel_rect, 1, border_radius=4)
    pygame.draw.rect(surface, GREEN, add_rect, border_radius=4)
    pygame.draw.rect(surface, WHITE, add_rect, 1, border_radius=4)
    draw_text(surface, "CANCELAR", FONTS["sm_b"], WHITE, cancel_rect.center, center=True)
    draw_text(surface, "ADICIONAR", FONTS["sm_b"], BLACK, add_rect.center, center=True)

    dropdown_info = None
    dropdown = modal.get("dropdown")
    if dropdown and dropdown.get("field") in OPTION_VALUES:
        base_rect = fields_rects.get(dropdown["field"])
        options = options_map.get(dropdown["field"])
        if options is None:
            options = OPTION_VALUES.get(dropdown["field"], [])
        if base_rect and options:
            opt_h = input_h
            opt_pad = 2
            opt_rects = []
            drop_y = base_rect.bottom + 4
            max_drop_bottom = modal_rect.bottom - 80
            total_h = len(options) * (opt_h + opt_pad)
            if drop_y + total_h > max_drop_bottom:
                drop_y = max(modal_rect.y + 12, base_rect.top - 4 - total_h)
            drop_rect = pygame.Rect(base_rect.x, drop_y, base_rect.width, total_h)
            pygame.draw.rect(surface, GRAY_40, drop_rect)
            pygame.draw.rect(surface, WHITE, drop_rect, 1)
            for idx_opt, opt_val in enumerate(options):
                r = pygame.Rect(base_rect.x, drop_y + idx_opt * (opt_h + opt_pad), base_rect.width, opt_h)
                pygame.draw.rect(surface, GRAY_60 if idx_opt % 2 else GRAY_25, r)
                is_current = form.get(dropdown["field"]) == opt_val
                if is_current:
                    pygame.draw.rect(surface, PURPLE, r, 2)
                draw_text(surface, opt_val, FONTS["sm"], WHITE, (r.x + 4, r.y + 4))
                opt_rects.append((opt_val, r))
            dropdown_info = {"field": dropdown["field"], "rects": opt_rects, "area": drop_rect}
        else:
            modal["dropdown"] = None

    return {
        "type": modal.get("type"),
        "add": add_rect,
        "cancel": cancel_rect,
        "area": modal_rect,
        "fields": fields_rects,
        "dropdown": dropdown_info,
    }


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

    search_rect = pygame.Rect(inner.x, filters_bottom + 20, inner.width, 32)
    pygame.draw.rect(surface, BLACK, search_rect)
    pygame.draw.rect(surface, WHITE if state.get("focus") == "search" else GRAY_60, search_rect, 1)
    placeholder = "Pesquisar por nome..."
    text = state.get("search", "")
    draw_text(surface, placeholder, FONTS["xs"], GRAY_80, (search_rect.x, search_rect.y - 16))
    draw_text(surface, text, FONTS["sm"], WHITE, (search_rect.x + 2, search_rect.y + 2))
    rects["fields"]["search"] = search_rect
    if state.get("focus") == "search":
        cursor = state.get("cursor", {}).get("search", len(text))
        cursor = max(0, min(cursor, len(text)))
        caret_x = search_rect.x + 2 + FONTS["sm"].size(text[:cursor])[0]
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            pygame.draw.line(surface, WHITE, (caret_x, search_rect.y + 2), (caret_x, search_rect.bottom - 2), 1)

    list_top = search_rect.bottom + 8
    list_rect = pygame.Rect(inner.x, list_top, inner.width, inner.bottom - list_top - 16)
    rects["list_area"] = list_rect
    rows = draw_item_list(surface, list_rect, state)
    rects["rows"] = rows

    if state.get("status"):
        draw_text(surface, state["status"], FONTS["xs"], state.get("status_color", WHITE), (inner.x, inner.bottom - 18))


def draw_item_list(surface, list_rect, state):
    pygame.draw.rect(surface, BLACK, list_rect)
    pygame.draw.rect(surface, WHITE, list_rect, 1)
    filtered = ensure_filtered(state)
    row_h = 75
    max_rows = max(1, list_rect.height // row_h)
    clamp_scroll(state, max_rows)
    start_index = state.get("scroll", 0)
    rows = []
    y = list_rect.y
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
        content_w = row_rect.right - text_x - 10
        name = item.get("name", "Sem nome")
        cat = clean_option(item.get("category", ""))
        dano = clean_option(item.get("dano", ""))
        alcance = clean_option(item.get("alcance", ""))
        protecao = clean_option(item.get("protecao", ""))
        emp = clean_option(item.get("empunhadura", ""))
        desc = item.get("descricao", "") or ""
        # Nome (laranja)
        name_shown = ellipsize(name, FONTS["sm_b"], max(20, content_w // 2 - 8))
        draw_text(surface, name_shown, FONTS["sm_b"], ORANGE, (text_x, y + 6))
        # Categoria (vermelho)
        if cat:
            draw_text(surface, cat, FONTS["xs"], RED, (text_x, y + 22))
        # Dano (azul)
        if dano:
            draw_text(surface, f"Dano: {dano}", FONTS["xs"], (80, 160, 255), (text_x, y + 34))
        # Alcance ou Protecao (verde)
        green_y = y + 46
        if alcance:
            draw_text(surface, f"Alcance: {alcance}", FONTS["xs"], GREEN, (text_x, green_y))
        elif protecao:
            draw_text(surface, f"Protecao: {protecao}", FONTS["xs"], GREEN, (text_x, green_y))
        # Punho (amarelo)
        if emp:
            draw_text(surface, f"Punho: {emp}", FONTS["xs"], ORANGE, (text_x + content_w // 2, y + 10))
        # Descricao (branco, truncada)
        desc_rect = pygame.Rect(text_x + content_w // 2, y + 28, content_w // 2, row_h - 35)
        pygame.draw.rect(surface, BLACK, desc_rect)
        pygame.draw.rect(surface, GRAY_25, desc_rect, 1)
        def wrap_hard(text, font, max_w):
            lines = []
            cur = ""
            for ch in text:
                candidate = cur + ch
                if font.size(candidate)[0] <= max_w:
                    cur = candidate
                else:
                    if cur:
                        lines.append(cur)
                    cur = ch if font.size(ch)[0] <= max_w else ""
            if cur:
                lines.append(cur)
            return lines or [""]

        desc_lines = wrap_hard(desc, FONTS["xs"], desc_rect.width - 6)
        max_desc_lines = max(1, (desc_rect.height - 6) // (FONTS["xs"].get_height() + 2))
        if len(desc_lines) > max_desc_lines:
            desc_lines = desc_lines[:max_desc_lines]
            last = desc_lines[-1]
            ellipsis = "..."
            while last and FONTS["xs"].size(last + ellipsis)[0] > desc_rect.width - 6:
                last = last[:-1]
            desc_lines[-1] = (last + ellipsis) if last else ellipsis
        prev_clip = surface.get_clip()
        surface.set_clip(desc_rect)
        dy = desc_rect.y + 3
        for line in desc_lines:
            draw_text(surface, line, FONTS["xs"], WHITE, (desc_rect.x + 3, dy))
            dy += FONTS["xs"].get_height() + 2
        surface.set_clip(prev_clip)
        rows.append((idx, row_rect))
        y += row_h
    if not rows:
        draw_text(surface, "Nenhum item listado.", FONTS["sm"], GRAY_80, (list_rect.x + 12, list_rect.y + 12))
    return rows


def handle_mouse(pos, rects, state):
    if state.get("modal"):
        modal_rects = rects.get("modal", {})
        opt = modal_rects.get("dropdown")
        if opt and opt.get("rects"):
            for val, r in opt["rects"]:
                if r.collidepoint(pos):
                    state["modal"]["form"][opt["field"]] = val
                    state["modal"]["dropdown"] = None
                    state["modal"]["focus"] = opt["field"]
                    state["modal"].setdefault("cursor", {})[opt["field"]] = len(val)
                    return True
            if opt.get("area") and opt["area"].collidepoint(pos):
                return True
        else:
            state["modal"]["dropdown"] = None

        fields = modal_rects.get("fields", {})
        for key, field_rect in fields.items():
            if field_rect.collidepoint(pos):
                if key == "image_path":
                    file_path = choose_image_file()
                    if file_path:
                        state["modal"]["form"][key] = file_path
                        state["modal"].setdefault("cursor", {})[key] = len(file_path)
                        set_status(state, "Imagem selecionada.", GREEN)
                    else:
                        set_status(state, "Selecao de imagem cancelada.", GRAY_80)
                    return True
                if key in OPTION_VALUES:
                    state["modal"]["dropdown"] = {"field": key, "rects": []}
                    state["modal"]["focus"] = key
                    current = state["modal"]["form"].get(key, "---")
                    state["modal"].setdefault("cursor", {})[key] = len(str(current))
                    return True
                state["modal"]["focus"] = key
                text = state["modal"]["form"].get(key, "")
                state["modal"].setdefault("cursor", {})[key] = len(text)
                return True
        if state["modal"].get("dropdown"):
            state["modal"]["dropdown"] = None
        if modal_rects.get("add") and modal_rects["add"].collidepoint(pos):
            confirm_add_modal(state)
            return True
        if modal_rects.get("cancel") and modal_rects["cancel"].collidepoint(pos):
            close_modal(state)
            set_status(state, "Adicao cancelada.", GRAY_80)
            return True
        return True

    search_rect = rects["fields"].get("search")
    if search_rect and search_rect.collidepoint(pos):
        state["focus"] = "search"
        state.setdefault("cursor", {})["search"] = len(state.get("search", ""))
        return True
    image_rect = rects["buttons"].get("image_upload")
    if image_rect and image_rect.collidepoint(pos):
        item = get_selected_item(state)
        if not item:
            return True
        file_path = choose_image_file()
        if file_path:
            item["image_path"] = file_path
            item.pop("_image_cache", None)
            set_status(state, "Imagem carregada.", GREEN)
        else:
            set_status(state, "Selecao de imagem cancelada.", GRAY_80)
        return True
    for label, rect in rects.get("filters", []):
        if rect.collidepoint(pos):
            state.setdefault("filters", {})["category"] = label
            state["scroll"] = 0
            ensure_filtered(state)
            return True
    add_rect = rects["buttons"].get("add")
    if add_rect and add_rect.collidepoint(pos):
        open_add_modal(state)
        return True
    for key, rect in rects["buttons"].items():
        if key == "add":
            continue
        if rect.collidepoint(pos):
            if key == "edit_item":
                item = get_selected_item(state)
                if item is not None:
                    form = {k: str(item.get(k, "---") if item.get(k, "---") is not None else "---") for k in item if k != "_image_cache"}
                    state["modal"] = {
                        "type": "edit_item",
                        "edit_index": state.get("selected"),
                        "form": form,
                        "focus": "name",
                        "cursor": {"name": len(form.get("name", ""))},
                        "dropdown": None,
                    }
                return True
            if key == "remove_item":
                sel = state.get("selected")
                if sel is not None and 0 <= sel < len(state.get("items", [])):
                    state["items"].pop(sel)
                    ensure_filtered(state)
                    state["selected"] = None
                    set_status(state, "Item removido.", ORANGE)
                return True
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
    if state.get("modal"):
        modal_rects = rects.get("modal", {})
        fields = modal_rects.get("fields", {})
        if pos and fields:
            for key, r in fields.items():
                if r.collidepoint(pos):
                    modal = state.get("modal", {})
                    if key in ("descricao", "info1", "info2"):
                        scrolls = modal.setdefault("scrolls", {})
                        maxes = modal.setdefault("scroll_max", {})
                        cur = scrolls.get(key, 0)
                        mx = maxes.get(key, 0)
                        scrolls[key] = max(0, min(mx, cur - delta))
                    return True
        return True
    if pos:
        # scroll em campos de texto do detalhe
        for key, field_rect in rects.get("scroll_fields", []):
            if field_rect.collidepoint(pos):
                scrolls = state.setdefault("scrolls", {})
                maxes = state.setdefault("scroll_max", {})
                cur = scrolls.get(key, 0)
                mx = maxes.get(key, 0)
                scrolls[key] = max(0, min(mx, cur - delta))
                return True
        list_area = rects.get("list_area")
        if list_area and list_area.collidepoint(pos):
            state["scroll"] = max(0, min(state.get("scroll", 0) - delta, state.get("max_scroll", 0)))
            return True
    return False


def handle_text_input(event, state):
    if state.get("modal"):
        modal = state["modal"]
        focus = modal.get("focus")
        if focus and focus in modal.get("form", {}):
            if focus in OPTION_VALUES:
                return True
            ch = event.text
            if ch.isprintable():
                text = modal["form"].get(focus, "")
                cursor = modal.setdefault("cursor", {}).get(focus, len(text))
                cursor = max(0, min(len(text), cursor))
                new_text = text[:cursor] + ch + text[cursor:]
                max_len = 45 if focus == "name" else None
                if max_len is not None:
                    new_text = new_text[:max_len]
                modal["form"][focus] = new_text
                modal["cursor"][focus] = min(len(new_text), cursor + len(ch))
            return True
        return False
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
    if state.get("modal"):
        modal = state["modal"]
        focus = modal.get("focus")
        if focus and focus in modal.get("form", {}):
            if focus in OPTION_VALUES:
                options = get_form_options(modal.get("form"), focus) or OPTION_VALUES.get(focus, [])
                if not options:
                    return True
                current = modal["form"].get(focus, options[0])
                if current not in options:
                    current_idx = 0
                else:
                    current_idx = options.index(current)
                if event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                    current_idx = (current_idx + 1) % len(options)
                    modal["form"][focus] = options[current_idx]
                    return True
                if event.key in (pygame.K_UP, pygame.K_LEFT):
                    current_idx = (current_idx - 1) % len(options)
                    modal["form"][focus] = options[current_idx]
                    return True
                if event.key == pygame.K_HOME:
                    modal["form"][focus] = options[0]
                    return True
                if event.key == pygame.K_END:
                    modal["form"][focus] = options[-1]
                    return True
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    modal["dropdown"] = {"field": focus, "rects": []}
                    return True
                return True
            text = modal["form"].get(focus, "")
            cursor = modal.setdefault("cursor", {}).get(focus, len(text))
            if event.key == pygame.K_BACKSPACE:
                if cursor > 0:
                    modal["form"][focus] = text[: cursor - 1] + text[cursor:]
                    modal["cursor"][focus] = cursor - 1
                return True
            if event.key == pygame.K_DELETE:
                if cursor < len(text):
                    modal["form"][focus] = text[:cursor] + text[cursor + 1 :]
                return True
            if event.key == pygame.K_LEFT:
                modal["cursor"][focus] = max(0, cursor - 1)
                return True
            if event.key == pygame.K_RIGHT:
                modal["cursor"][focus] = min(len(text), cursor + 1)
                return True
        if event.key == pygame.K_ESCAPE:
            close_modal(state)
            set_status(state, "Adicao cancelada.", GRAY_80)
            return True
        if event.key == pygame.K_RETURN:
            confirm_add_modal(state)
            return True
        return False
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
        "modal": None,
        "scrolls": {"descricao": 0, "info1": 0, "info2": 0},
        "scroll_max": {"descricao": 0, "info1": 0, "info2": 0},
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
