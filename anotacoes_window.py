import sys
import math
import pygame

# Dimensoes base
WIDTH, HEIGHT = 1280, 900
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
pygame.display.set_caption("Painel de Anotações (demo)")
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
CLOCK = pygame.time.Clock()

FONTS = {
    "xs": pygame.font.SysFont("arial", 12),
    "sm": pygame.font.SysFont("arial", 14),
    "sm_b": pygame.font.SysFont("arial", 14, bold=True),
    "sm_i": pygame.font.SysFont("arial", 14, italic=True),
    "sm_bi": pygame.font.SysFont("arial", 14, bold=True, italic=True),
    "md": pygame.font.SysFont("arial", 18, bold=True),
    "lg": pygame.font.SysFont("arial", 28, bold=True),
}

DEFAULT_STYLE = {"bold": False, "italic": False, "underline": False}
STYLE_FONT_CACHE = {}


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


NOTES_STATE = {
    "tabs": ["GERAL", "INVENTARIO", "HABILIDADES", "ANOTACOES"],
    "active_tab": "ANOTACOES",
    "notes": [],
    "filtered": [],
    "search": "",
    "show_form": False,
    "selected": None,
    "focus": None,  # search, title, subject, body
    "cursor": {"search": 0, "title": 0, "subject": 0, "body": 0},
    "form": {"title": "", "subject": "", "body": ""},
    "rects": {"fields": {}, "buttons": {}, "list_rows": []},
    "style_flags": {"bold": False, "italic": False, "underline": False},
    "body_styles": [],
}


def reset_form(state):
    state["form"] = {"title": "", "subject": "", "body": ""}
    state["cursor"] = {k: 0 for k in state["cursor"]}
    state["body_styles"] = []
    state["style_flags"] = DEFAULT_STYLE.copy()
    state["focus"] = None
    state["selected"] = None


def ensure_filtered(state):
    term = state.get("search", "").lower()
    notes = state["notes"]
    if not term:
        state["filtered"] = list(enumerate(notes))
    else:
        state["filtered"] = [
            (idx, n)
            for idx, n in enumerate(notes)
            if term in n.get("title", "").lower() or term in n.get("subject", "").lower()
        ]


def insert_text(state, field, text):
    if field not in state["form"] and field != "search":
        return
    if field == "search":
        buf = state.get("search", "")
        cur = state["cursor"].get(field, len(buf))
        cur = max(0, min(cur, len(buf)))
        new_buf = buf[:cur] + text + buf[cur:]
        state["search"] = new_buf
        state["cursor"][field] = cur + len(text)
        ensure_filtered(state)
    elif field == "body":
        buf = state["form"].get("body", "")
        styles = state.get("body_styles", [])
        cur = state["cursor"].get(field, len(buf))
        cur = max(0, min(cur, len(buf)))
        snapshot = state["style_flags"].copy()
        state["form"]["body"] = buf[:cur] + text + buf[cur:]
        insert_styles = [snapshot for _ in text]
        state["body_styles"] = styles[:cur] + insert_styles + styles[cur:]
        state["cursor"][field] = cur + len(text)
    else:
        buf = state["form"].get(field, "")
        cur = state["cursor"].get(field, len(buf))
        cur = max(0, min(cur, len(buf)))
        new_buf = buf[:cur] + text + buf[cur:]
        state["form"][field] = new_buf
    state["cursor"][field] = cur + len(text)


def ingest_incoming_note(payload):
    """
    Integração: adicionar uma anotação recebida externamente (ex.: painel de main2.py enviando email).
    Espera dict com chaves title, subject, body. Abre na lista como item novo sem abrir o formulário.
    """
    title = (payload.get("title") or "Sem título").strip()
    subject = (payload.get("subject") or "").strip()
    body = payload.get("body") or ""
    NOTES_STATE["notes"].append({"title": title, "subject": subject, "body": body})
    NOTES_STATE["selected"] = None
    NOTES_STATE["show_form"] = False
    NOTES_STATE["focus"] = None
    NOTES_STATE["cursor"]["search"] = len(NOTES_STATE.get("search", ""))
    NOTES_STATE["body_styles"] = []
    ensure_filtered(NOTES_STATE)


def add_note(state):
    data = {
        "title": state["form"]["title"] or "Sem título",
        "subject": state["form"]["subject"],
        "body": state["form"]["body"],
    }
    if state.get("selected") is None:
        state["notes"].append(data)
        new_idx = len(state["notes"]) - 1
    else:
        new_idx = state["selected"]
        if 0 <= new_idx < len(state["notes"]):
            state["notes"][new_idx] = data
    ensure_filtered(state)
    return new_idx
    ensure_filtered(state)


def remove_note(state):
    idx = state.get("selected")
    if idx is None:
        return
    if 0 <= idx < len(state["notes"]):
        state["notes"].pop(idx)
    state["selected"] = None
    reset_form(state)
    ensure_filtered(state)


def toolbar_action(state, action):
    field = "body"
    if action == "bold":
        state["style_flags"]["bold"] = not state["style_flags"].get("bold", False)
    elif action == "italic":
        state["style_flags"]["italic"] = not state["style_flags"].get("italic", False)
    elif action == "underline":
        state["style_flags"]["underline"] = not state["style_flags"].get("underline", False)
    elif action == "bullet":
        insert_text(state, field, "\n• ")
    elif action == "number":
        insert_text(state, field, "\n1. ")
    elif action == "align_left":
        insert_text(state, field, "\n")
    elif action == "align_center":
        insert_text(state, field, "\n")
    elif action == "align_right":
        insert_text(state, field, "\n")


def draw_text_input(rect, label, value, focus, key, state, multiline=False, max_lines=3):
    border = ORANGE if focus == key else WHITE
    pygame.draw.rect(WINDOW, GRAY_20, rect)
    pygame.draw.rect(WINDOW, border, rect, 1)
    draw_text(WINDOW, label, FONTS["sm_b"], WHITE, (rect.x, rect.y - 16))
    inner_pad_x = 6
    if multiline:
        lines, line_starts = wrap_text_with_starts(value or "", FONTS["sm"], rect.width - inner_pad_x * 2)
        line_h = FONTS["sm"].get_height()
        for i, line in enumerate(lines[:max_lines]):
            draw_text(WINDOW, line, FONTS["sm"], WHITE, (rect.x + inner_pad_x, rect.y + 4 + i * line_h))
        if focus == key:
            cur = state["cursor"].get(key, len(value))
            cur = max(0, min(cur, len(value)))
            line_idx = 0
            for idx, start in enumerate(line_starts):
                if cur >= start:
                    line_idx = idx
            line_idx = min(line_idx, len(lines) - 1) if lines else 0
            caret_line = lines[line_idx] if lines else ""
            offset_in_line = cur - line_starts[line_idx]
            caret_text = caret_line[:offset_in_line]
            caret_x = rect.x + inner_pad_x + FONTS["sm"].size(caret_text)[0]
            caret_y = rect.y + 4 + line_idx * line_h
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                pygame.draw.line(WINDOW, WHITE, (caret_x, caret_y), (caret_x, caret_y + line_h), 1)
    else:
        draw_text(WINDOW, value or "", FONTS["sm"], WHITE, (rect.x + inner_pad_x, rect.y + 4))
        if focus == key:
            cur = state["cursor"].get(key, len(value))
            cur = max(0, min(cur, len(value)))
            caret_x = rect.x + inner_pad_x + FONTS["sm"].size((value or "")[:cur])[0]
            caret_y = rect.y + 3
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                pygame.draw.line(WINDOW, WHITE, (caret_x, caret_y), (caret_x, rect.bottom - 3), 1)


def draw_toolbar(surface, rect, state):
    actions = [
        ("B", "bold"),
        ("I", "italic"),
        ("U", "underline"),
        ("•", "bullet"),
        ("1.", "number"),
        ("L", "align_left"),
        ("C", "align_center"),
        ("R", "align_right"),
    ]
    btn_w = 36
    btn_h = rect.height
    btn_gap = 4
    rects = []
    for i, (label, action) in enumerate(actions):
        bx = rect.x + i * (btn_w + btn_gap)
        brect = pygame.Rect(bx, rect.y, btn_w, btn_h)
        active = False
        if action in ("bold", "italic", "underline"):
            active = state["style_flags"].get(action, False)
        pygame.draw.rect(surface, GRAY_40 if not active else GRAY_60, brect)
        pygame.draw.rect(surface, ORANGE if active else WHITE, brect, 1)
        draw_text(surface, label, FONTS["sm_b"], WHITE, brect.center, center=True)
        rects.append((action, brect))
    return rects


def get_font_for_style(style):
    bold = style.get("bold", False)
    italic = style.get("italic", False)
    underline = style.get("underline", False)
    key = (bold, italic, underline)
    if key in STYLE_FONT_CACHE:
        return STYLE_FONT_CACHE[key]
    font = pygame.font.SysFont("arial", 14, bold=bold, italic=italic)
    font.set_underline(underline)
    STYLE_FONT_CACHE[key] = font
    return font


def draw_notes_panel(surface, state):
    surface.fill(BLACK)
    rects = {"fields": {}, "buttons": {}, "list_rows": [], "toolbar": []}

    panel_rect = pygame.Rect(8, 8, WIDTH - 16, HEIGHT - 16)
    pygame.draw.rect(surface, BLACK, panel_rect)
    pygame.draw.rect(surface, WHITE, panel_rect, 2)

    left_pad = panel_rect.x + 18
    top_y = panel_rect.y + 16

    # Search and add on left panel
    left_w = panel_rect.width // 3
    left_rect = pygame.Rect(left_pad, top_y, left_w, panel_rect.height - 24)
    pygame.draw.rect(surface, BLACK, left_rect)
    pygame.draw.rect(surface, WHITE, left_rect, 2)
    inner_left = left_rect.inflate(-10, -10)

    search_rect = pygame.Rect(inner_left.x, inner_left.y, inner_left.width - 90, 26)
    pygame.draw.rect(surface, GRAY_20, search_rect)
    pygame.draw.rect(surface, ORANGE if state["focus"] == "search" else WHITE, search_rect, 1)
    draw_text(surface, "pesquisar por titulo...", FONTS["xs"], GRAY_80, (search_rect.x + 4, search_rect.y - 14))
    draw_text(surface, state["search"], FONTS["sm"], WHITE, (search_rect.x + 4, search_rect.y + 4))
    if state["focus"] == "search":
        cur = state["cursor"].get("search", len(state["search"]))
        cur = max(0, min(cur, len(state["search"])))
        caret_x = search_rect.x + 4 + FONTS["sm"].size(state["search"][:cur])[0]
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            pygame.draw.line(surface, WHITE, (caret_x, search_rect.y + 4), (caret_x, search_rect.bottom - 4), 1)
    rects["fields"]["search"] = search_rect
    add_left_rect = pygame.Rect(search_rect.right + 6, search_rect.y, 80, 26)
    pygame.draw.rect(surface, GREEN, add_left_rect)
    pygame.draw.rect(surface, WHITE, add_left_rect, 1)
    draw_text(surface, "Adicionar", FONTS["xs"], BLACK, add_left_rect.center, center=True)
    rects["buttons"]["add_left"] = add_left_rect

    # List of notes
    list_rect = pygame.Rect(inner_left.x, search_rect.bottom + 8, inner_left.width, inner_left.bottom - search_rect.bottom - 8)
    pygame.draw.rect(surface, BLACK, list_rect)
    pygame.draw.rect(surface, WHITE, list_rect, 1)
    header_h = 30
    pygame.draw.rect(surface, GRAY_20, (list_rect.x, list_rect.y, list_rect.width, header_h))
    pygame.draw.rect(surface, WHITE, (list_rect.x, list_rect.y, list_rect.width, header_h), 1)
    draw_text(surface, "Titulo da anotacao*", FONTS["sm_b"], WHITE, (list_rect.x + 6, list_rect.y + 6))

    rects["list_rows"] = []
    y_row = list_rect.y + header_h
    row_h = 60
    ensure_filtered(state)
    for idx_display, (idx_note, note) in enumerate(state["filtered"]):
        if y_row + row_h > list_rect.bottom:
            break
        row_rect = pygame.Rect(list_rect.x, y_row, list_rect.width, row_h)
        pygame.draw.rect(surface, BLACK, row_rect)
        pygame.draw.rect(surface, WHITE, row_rect, 1)
        if state.get("selected") == idx_note:
            pygame.draw.rect(surface, PURPLE, row_rect, 2)
        draw_text(surface, note.get("title", "Sem titulo"), FONTS["sm_b"], WHITE, (row_rect.x + 6, row_rect.y + 4))
        draw_text(surface, f"Sobre: {note.get('subject','')}", FONTS["xs"], WHITE, (row_rect.x + 6, row_rect.y + 24))
        rects["list_rows"].append((idx_note, row_rect))
        y_row += row_h

    # Right form
    right_x = left_rect.right + 12
    right_w = panel_rect.right - right_x - 12
    right_rect = pygame.Rect(right_x, top_y, right_w, panel_rect.height - 24)
    pygame.draw.rect(surface, BLACK, right_rect)
    pygame.draw.rect(surface, WHITE, right_rect, 2)
    inner_right = right_rect.inflate(-10, -10)

    if state.get("show_form") or state.get("selected") is not None:
        title_rect = pygame.Rect(inner_right.x, inner_right.y + 10, inner_right.width - 200, 32)
        draw_text_input(title_rect, "Titulo da anotacao*", state["form"]["title"], state["focus"], "title", state, multiline=False)
        rects["fields"]["title"] = title_rect

        btn_remove = pygame.Rect(title_rect.right + 8, title_rect.y, 90, 26)
        btn_edit = pygame.Rect(btn_remove.right + 8, title_rect.y, 90, 26)
        pygame.draw.rect(surface, RED, btn_remove)
        pygame.draw.rect(surface, WHITE, btn_remove, 1)
        draw_text(surface, "Remover", FONTS["xs"], BLACK, btn_remove.center, center=True)
        pygame.draw.rect(surface, GREEN, btn_edit)
        pygame.draw.rect(surface, WHITE, btn_edit, 1)
        edit_label = "Adicionar" if state.get("selected") is None else "Editar"
        draw_text(surface, edit_label, FONTS["xs"], BLACK, btn_edit.center, center=True)
        rects["buttons"]["remove"] = btn_remove
        rects["buttons"]["save"] = btn_edit

        subject_rect = pygame.Rect(inner_right.x, title_rect.bottom + 12, inner_right.width, 32)
        draw_text_input(subject_rect, "SOBRE*", state["form"]["subject"], state["focus"], "subject", state, multiline=False)
        rects["fields"]["subject"] = subject_rect

        toolbar_rect = pygame.Rect(inner_right.x, subject_rect.bottom + 6, 8 * 40 - 4, 26)
        toolbar_rects = draw_toolbar(surface, toolbar_rect, state)
        rects["toolbar"] = toolbar_rects

        body_rect = pygame.Rect(inner_right.x, toolbar_rect.bottom + 8, inner_right.width, inner_right.bottom - toolbar_rect.bottom - 12)
        border = ORANGE if state.get("focus") == "body" else WHITE
        pygame.draw.rect(surface, GRAY_20, body_rect)
        pygame.draw.rect(surface, border, body_rect, 1)
        draw_text(surface, "Conteudo da anotacao (caracteres ilimitados)", FONTS["xs"], WHITE, (body_rect.x, body_rect.y - 16))
        # Render body with per-character styles
        text_body = state["form"]["body"]
        styles = state.get("body_styles", [])
        default_style = DEFAULT_STYLE
        x = body_rect.x + 4
        y = body_rect.y + 4
        max_w = body_rect.width - 8
        line_h = get_font_for_style(default_style).get_height()
        caret_pos = state["cursor"].get("body", len(text_body))
        caret_coords = (x, y)
        for idx, ch in enumerate(text_body):
            style = styles[idx] if idx < len(styles) else default_style
            font = get_font_for_style(style)
            ch_w, ch_h = font.size(ch)
            if ch == "\n" or x + ch_w > body_rect.x + max_w:
                x = body_rect.x + 4
                y += line_h
            if ch == "\n":
                line_h = font.get_height()
                if idx == caret_pos:
                    caret_coords = (x, y)
                continue
            surface.blit(font.render(ch, True, WHITE), (x, y))
            if idx == caret_pos:
                caret_coords = (x, y)
            x += ch_w
            line_h = max(line_h, ch_h)
        # caret at end
        if caret_pos == len(text_body):
            caret_coords = (x, y)
        if state.get("focus") == "body" and (pygame.time.get_ticks() // 400) % 2 == 0:
            pygame.draw.line(surface, WHITE, caret_coords, (caret_coords[0], caret_coords[1] + line_h), 1)
        rects["fields"]["body"] = body_rect
    else:
        placeholder = "Clique em ADICIONAR ou selecione uma anotacao"
        draw_text(surface, placeholder, FONTS["sm"], WHITE, right_rect.center, center=True)

    return rects


def handle_mouse(pos, rects, state):
    # toolbar
    for action, r in rects.get("toolbar", []):
        if r.collidepoint(pos):
            toolbar_action(state, action)
            return
    # buttons
    btns = rects.get("buttons", {})
    if btns.get("add_left") and btns["add_left"].collidepoint(pos):
        reset_form(state)
        state["show_form"] = True
        return
    if btns.get("save") and btns["save"].collidepoint(pos):
        was_new = state.get("selected") is None
        new_idx = add_note(state)
        if was_new:
            reset_form(state)
            state["show_form"] = False
            state["selected"] = None
        else:
            state["selected"] = new_idx
            state["show_form"] = True
        return
    if btns.get("remove") and btns["remove"].collidepoint(pos):
        remove_note(state)
        return
    # fields
    for key, rect in rects.get("fields", {}).items():
        if rect and rect.collidepoint(pos):
            state["focus"] = key
            if key == "search":
                state["cursor"]["search"] = len(state["search"])
            elif key in {"title", "subject", "body"}:
                state["cursor"][key] = len(state["form"][key])
            return
    # list rows
    for idx, rect in rects.get("list_rows", []):
        if rect.collidepoint(pos):
            state["selected"] = idx
            note = state["notes"][idx]
            state["form"] = {
                "title": note.get("title", ""),
                "subject": note.get("subject", ""),
                "body": note.get("body", ""),
            }
            for k in {"title", "subject", "body"}:
                state["cursor"][k] = len(state["form"][k])
            default_style = DEFAULT_STYLE.copy()
            state["body_styles"] = [default_style for _ in state["form"]["body"]]
            state["show_form"] = True
            state["focus"] = None
            return
    state["focus"] = None


def handle_key(event, state):
    field = state.get("focus")
    if not field:
        return
    if field in {"search", "title", "subject", "body"}:
        if field in {"title", "subject", "body"} and not state.get("show_form"):
            return
        buf = state["search"] if field == "search" else state["form"][field]
    else:
        return
    cur = state["cursor"].get(field, len(buf))
    cur = max(0, min(cur, len(buf)))
    key = event.key
    if key == pygame.K_BACKSPACE:
        if cur > 0:
            buf = buf[:cur - 1] + buf[cur:]
            if field == "body":
                styles = state.get("body_styles", [])
                state["body_styles"] = styles[:cur - 1] + styles[cur:]
            cur -= 1
    elif key == pygame.K_DELETE:
        if cur < len(buf):
            buf = buf[:cur] + buf[cur + 1:]
            if field == "body":
                styles = state.get("body_styles", [])
                state["body_styles"] = styles[:cur] + styles[cur + 1:]
    elif key == pygame.K_LEFT:
        cur = max(0, cur - 1)
    elif key == pygame.K_RIGHT:
        cur = min(len(buf), cur + 1)
    elif key == pygame.K_HOME:
        cur = 0
    elif key == pygame.K_END:
        cur = len(buf)
    elif key == pygame.K_RETURN:
        if field == "body":
            buf = buf[:cur] + "\n" + buf[cur:]
            styles = state.get("body_styles", [])
            styles = styles[:cur] + [state["style_flags"].copy()] + styles[cur:]
            state["body_styles"] = styles
            cur += 1
    if field == "search":
        state["search"] = buf
        ensure_filtered(state)
    else:
        state["form"][field] = buf
    state["cursor"][field] = cur


def handle_text_input(event, state):
    text = event.text
    if not text:
        return
    field = state.get("focus")
    if not field:
        return
    if field in {"title", "subject", "body"} and not state.get("show_form"):
        return
    if field in {"search", "title", "subject", "body"}:
        insert_text(state, field, text)


def main():
    running = True
    ensure_filtered(NOTES_STATE)
    while running:
        rects = draw_notes_panel(WINDOW, NOTES_STATE)
        pygame.display.flip()
        CLOCK.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_mouse(event.pos, rects, NOTES_STATE)
            elif event.type == pygame.TEXTINPUT:
                handle_text_input(event, NOTES_STATE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    handle_key(event, NOTES_STATE)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
