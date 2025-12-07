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
GRAY_30 = (55, 55, 55)
GRAY_40 = (70, 70, 70)
GRAY_60 = (110, 110, 110)
GRAY_70 = (150, 150, 150)
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

DEFAULT_STYLE = {"bold": False, "italic": False, "underline": False, "align": "left"}
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
    "body_scroll": 0,
    "body_scroll_max": 0,
    "number_sequence": None,
    "align_mode": "left",
}


def reset_form(state):
    state["form"] = {"title": "", "subject": "", "body": ""}
    state["cursor"] = {k: 0 for k in state["cursor"]}
    state["body_styles"] = []
    state["style_flags"] = DEFAULT_STYLE.copy()
    state["focus"] = None
    state["selected"] = None
    state["body_scroll"] = 0
    state["body_scroll_max"] = 0
    state["number_sequence"] = None
    state["align_mode"] = "left"


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
        seq_align = state.get("align_mode", "left")
        insert_styles = []
        for ch in text:
            entry_style = snapshot.copy()
            entry_style["align"] = seq_align
            insert_styles.append(entry_style)
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
        if state.get("number_sequence"):
            state["number_sequence"] = None
        else:
            state["number_sequence"] = 1
            insert_text(state, field, "\n1. ")
    elif action == "align_left":
        state["align_mode"] = "left"
    elif action == "align_center":
        state["align_mode"] = "center"
    elif action == "align_right":
        state["align_mode"] = "right"


def draw_text_input(surface, rect, label, value, focus, key, state, multiline=False, max_lines=3):
    border = ORANGE if focus == key else WHITE
    pygame.draw.rect(surface, GRAY_20, rect)
    pygame.draw.rect(surface, border, rect, 1)
    draw_text(surface, label, FONTS["sm_b"], WHITE, (rect.x, rect.y - 16))
    inner_pad_x = 6
    if multiline:
        lines, line_starts = wrap_text_with_starts(value or "", FONTS["sm"], rect.width - inner_pad_x * 2)
        line_h = FONTS["sm"].get_height()
        for i, line in enumerate(lines[:max_lines]):
            draw_text(surface, line, FONTS["sm"], WHITE, (rect.x + inner_pad_x, rect.y + 4 + i * line_h))
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
        draw_text(surface, value or "", FONTS["sm"], WHITE, (rect.x + inner_pad_x, rect.y + 4))
        if focus == key:
            cur = state["cursor"].get(key, len(value))
            cur = max(0, min(cur, len(value)))
            caret_x = rect.x + inner_pad_x + FONTS["sm"].size((value or "")[:cur])[0]
            caret_y = rect.y + 3
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                pygame.draw.line(surface, WHITE, (caret_x, caret_y), (caret_x, rect.bottom - 3), 1)


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
    btn_w = 28
    btn_h = rect.height
    btn_gap = 3
    rects = []
    for i, (label, action) in enumerate(actions):
        bx = rect.x + i * (btn_w + btn_gap)
        brect = pygame.Rect(bx, rect.y, btn_w, btn_h)
        active = False
        if action in ("bold", "italic", "underline"):
            active = state["style_flags"].get(action, False)
        elif action in ("align_left", "align_center", "align_right"):
            mode = {"align_left": "left", "align_center": "center", "align_right": "right"}[action]
            active = state.get("align_mode", "left") == mode
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

    content_pad = 14
    column_gap = 16
    usable_height = panel_rect.height - content_pad * 2
    left_w = int((panel_rect.width - column_gap - content_pad * 2) * 0.4)
    left_rect = pygame.Rect(panel_rect.x + content_pad, panel_rect.y + content_pad, left_w, usable_height)
    right_rect = pygame.Rect(
        left_rect.right + column_gap,
        left_rect.y,
        panel_rect.right - content_pad - (left_rect.right + column_gap),
        usable_height,
    )

    # Painel esquerdo (busca + lista)
    pygame.draw.rect(surface, BLACK, left_rect)
    pygame.draw.rect(surface, WHITE, left_rect, 2)
    inner_left = left_rect.inflate(-12, -12)
    draw_text(surface, "ANOTACOES", FONTS["md"], WHITE, (inner_left.x, inner_left.y - 6))

    search_rect = pygame.Rect(inner_left.x, inner_left.y + 18, inner_left.width, 30)
    pygame.draw.rect(surface, GRAY_20, search_rect)
    pygame.draw.rect(surface, ORANGE if state["focus"] == "search" else WHITE, search_rect, 1)
    draw_text(surface, "Pesquisar por titulo ou assunto", FONTS["xs"], GRAY_80, (search_rect.x, search_rect.y - 14))
    draw_text(surface, state["search"], FONTS["sm"], WHITE, (search_rect.x + 6, search_rect.y + 6))
    if state["focus"] == "search":
        cur = state["cursor"].get("search", len(state["search"]))
        cur = max(0, min(cur, len(state["search"])))
        caret_x = search_rect.x + 6 + FONTS["sm"].size(state["search"][:cur])[0]
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            pygame.draw.line(surface, WHITE, (caret_x, search_rect.y + 5), (caret_x, search_rect.bottom - 5), 1)
    rects["fields"]["search"] = search_rect

    add_left_rect = pygame.Rect(inner_left.x, search_rect.bottom + 10, inner_left.width, 32)
    pygame.draw.rect(surface, GREEN, add_left_rect)
    pygame.draw.rect(surface, WHITE, add_left_rect, 1)
    draw_text(surface, "Adicionar anotacao", FONTS["sm_b"], BLACK, add_left_rect.center, center=True)
    rects["buttons"]["add_left"] = add_left_rect

    list_rect = pygame.Rect(
        inner_left.x,
        add_left_rect.bottom + 14,
        inner_left.width,
        inner_left.bottom - add_left_rect.bottom - 14,
    )
    pygame.draw.rect(surface, BLACK, list_rect)
    pygame.draw.rect(surface, WHITE, list_rect, 1)
    header_h = 30
    title_split = list_rect.x + int(list_rect.width * 0.55)
    pygame.draw.rect(surface, GRAY_20, (list_rect.x, list_rect.y, list_rect.width, header_h))
    pygame.draw.rect(surface, WHITE, (list_rect.x, list_rect.y, list_rect.width, header_h), 1)
    pygame.draw.line(surface, WHITE, (title_split, list_rect.y), (title_split, list_rect.y + header_h))
    draw_text(surface, "Titulo", FONTS["sm_b"], WHITE, (list_rect.x + 6, list_rect.y + 6))
    draw_text(surface, "Sobre", FONTS["sm_b"], WHITE, (title_split + 6, list_rect.y + 6))

    rects["list_rows"] = []
    y_row = list_rect.y + header_h
    row_h = 62
    ensure_filtered(state)
    for idx_note, note in state["filtered"]:
        if y_row + row_h > list_rect.bottom:
            break
        row_rect = pygame.Rect(list_rect.x, y_row, list_rect.width, row_h)
        pygame.draw.rect(surface, BLACK, row_rect)
        pygame.draw.rect(surface, WHITE, row_rect, 1)
        pygame.draw.line(surface, WHITE, (title_split, y_row), (title_split, y_row + row_h))
        if state.get("selected") == idx_note:
            pygame.draw.rect(surface, PURPLE, row_rect, 2)
        title = note.get("title", "Sem titulo") or "Sem titulo"
        subject = note.get("subject", "")
        preview = (note.get("body", "") or "").strip().split("\n")[0][:60]
        draw_text(surface, title, FONTS["sm_b"], WHITE, (row_rect.x + 6, row_rect.y + 6))
        draw_text(surface, preview or "Sem conteudo", FONTS["xs"], GRAY_80, (row_rect.x + 6, row_rect.y + 30))
        draw_text(surface, subject or "--", FONTS["sm"], WHITE, (title_split + 6, row_rect.y + 18))
        rects["list_rows"].append((idx_note, row_rect))
        y_row += row_h

    # Painel direito (formulario)
    pygame.draw.rect(surface, BLACK, right_rect)
    pygame.draw.rect(surface, WHITE, right_rect, 2)
    inner_right = right_rect.inflate(-12, -12)

    if state.get("show_form") or state.get("selected") is not None:
        action_block = 2 * 96 + 20
        title_width = max(160, inner_right.width - action_block - 6)
        title_rect = pygame.Rect(inner_right.x, inner_right.y + 6, title_width, 34)
        draw_text_input(surface, title_rect, "Titulo da anotacao*", state["form"]["title"], state["focus"], "title", state, multiline=False)
        rects["fields"]["title"] = title_rect

        btn_remove = pygame.Rect(title_rect.right + 10, title_rect.y, 96, 30)
        btn_edit = pygame.Rect(btn_remove.right + 10, title_rect.y, 96, 30)
        pygame.draw.rect(surface, RED, btn_remove)
        pygame.draw.rect(surface, WHITE, btn_remove, 1)
        draw_text(surface, "Remover", FONTS["sm"], BLACK, btn_remove.center, center=True)
        pygame.draw.rect(surface, GREEN, btn_edit)
        pygame.draw.rect(surface, WHITE, btn_edit, 1)
        edit_label = "Adicionar" if state.get("selected") is None else "Editar"
        draw_text(surface, edit_label, FONTS["sm"], BLACK, btn_edit.center, center=True)
        rects["buttons"]["remove"] = btn_remove
        rects["buttons"]["save"] = btn_edit

        subject_rect = pygame.Rect(inner_right.x, title_rect.bottom + 12, inner_right.width, 34)
        draw_text_input(surface, subject_rect, "SOBRE*", state["form"]["subject"], state["focus"], "subject", state, multiline=False)
        rects["fields"]["subject"] = subject_rect

        toolbar_rect = pygame.Rect(inner_right.x, subject_rect.bottom + 10, inner_right.width, 30)
        toolbar_rects = draw_toolbar(surface, toolbar_rect, state)
        rects["toolbar"] = toolbar_rects

        scrollbar_width = 12
        body_rect = pygame.Rect(
            inner_right.x,
            toolbar_rect.bottom + 10,
            inner_right.width,
            inner_right.bottom - toolbar_rect.bottom - 12,
        )
        border = ORANGE if state.get("focus") == "body" else WHITE
        pygame.draw.rect(surface, GRAY_20, body_rect)
        pygame.draw.rect(surface, border, body_rect, 1)
        draw_text(surface, "Conteudo da anotacao (caracteres ilimitados)", FONTS["xs"], WHITE, (body_rect.x, body_rect.y - 16))
        # Render body com suporte a scroll/alinhamento
        text_body = state["form"]["body"]
        styles = state.get("body_styles", [])
        default_style = DEFAULT_STYLE
        text_width = max(10, body_rect.width - 8 - scrollbar_width)
        visible_height = body_rect.height - 8
        scroll = max(0, min(state.get("body_scroll", 0), state.get("body_scroll_max", 0)))
        caret_pos = state["cursor"].get("body", len(text_body))
        entries = []
        line_widths = [0]
        line_tops = [0]
        line_heights = [get_font_for_style(default_style).get_height()]
        current_line = 0
        x_local = 0
        y_local = 0
        current_line_height = line_heights[0]
        caret_coords_local = (0, 0)
        caret_line = 0

        def finalize_line():
            nonlocal current_line, x_local, y_local, current_line_height
            line_heights[current_line] = max(line_heights[current_line], current_line_height)
            y_local += line_heights[current_line]
            current_line += 1
            x_local = 0
            current_line_height = get_font_for_style(default_style).get_height()
            line_tops.append(y_local)
            line_heights.append(current_line_height)
            line_widths.append(0)
            return current_line_height

        for idx, ch in enumerate(text_body):
            style = styles[idx] if idx < len(styles) else default_style
            font = get_font_for_style(style)
            ch_w, ch_h = font.size(ch)
            if ch == "\n":
                if idx == caret_pos:
                    caret_coords_local = (x_local, y_local)
                    caret_line = current_line
                current_line_height = max(current_line_height, ch_h)
                finalize_line()
                continue
            if x_local > 0 and x_local + ch_w > text_width:
                finalize_line()
            entry = {
                "line": current_line,
                "x": x_local,
                "y": y_local,
                "font": font,
                "char": ch,
                "w": ch_w,
                "h": ch_h,
                "align": style.get("align", "left"),
            }
            entries.append(entry)
            line_widths[current_line] = max(line_widths[current_line], x_local + ch_w)
            current_line_height = max(current_line_height, ch_h)
            if idx == caret_pos:
                caret_coords_local = (x_local, y_local)
                caret_line = current_line
            x_local += ch_w
        line_heights[current_line] = max(line_heights[current_line], current_line_height)
        content_height = line_tops[current_line] + line_heights[current_line]
        if caret_pos == len(text_body):
            caret_coords_local = (x_local, y_local)
            caret_line = current_line

        offsets = []
        for i, width in enumerate(line_widths):
            if entries:
                # Determine alinhamento da linha pelo primeiro caractere da linha
                try:
                    first_entry = next(e for e in entries if e["line"] == i)
                    align_mode = first_entry.get("align") or "left"
                except StopIteration:
                    align_mode = "left"
            else:
                align_mode = "left"
            if align_mode == "center":
                offsets.append(max(0, (text_width - width) / 2))
            elif align_mode == "right":
                offsets.append(max(0, text_width - width))
            else:
                offsets.append(0)

        clip_rect = pygame.Rect(
            body_rect.x + 2,
            body_rect.y + 2,
            body_rect.width - scrollbar_width - 4,
            body_rect.height - 4,
        )
        prev_clip = surface.get_clip()
        surface.set_clip(clip_rect)
        for entry in entries:
            draw_y = body_rect.y + 4 + entry["y"] - scroll
            if draw_y + entry["h"] < body_rect.y or draw_y > body_rect.bottom:
                continue
            draw_x = body_rect.x + 4 + offsets[entry["line"]] + entry["x"]
            surface.blit(entry["font"].render(entry["char"], True, WHITE), (draw_x, draw_y))
        surface.set_clip(prev_clip)
        max_scroll = max(0, content_height - visible_height)
        state["body_scroll_max"] = max_scroll
        scroll = max(0, min(state.get("body_scroll", 0), max_scroll))
        caret_line_height = line_heights[min(caret_line, len(line_heights) - 1)] if line_heights else get_font_for_style(default_style).get_height()
        if state.get("focus") == "body":
            caret_top = caret_coords_local[1]
            caret_bottom = caret_coords_local[1] + caret_line_height
            if caret_bottom - scroll > visible_height:
                scroll = caret_bottom - visible_height
            elif caret_top - scroll < 0:
                scroll = caret_top
            scroll = max(0, min(max_scroll, scroll))
        state["body_scroll"] = scroll
        caret_screen_y = body_rect.y + 4 + caret_coords_local[1] - scroll
        caret_screen_x = body_rect.x + 4 + offsets[min(caret_line, len(offsets) - 1)] + caret_coords_local[0]
        if state.get("focus") == "body" and (pygame.time.get_ticks() // 400) % 2 == 0:
            if body_rect.y <= caret_screen_y <= body_rect.bottom:
                pygame.draw.line(
                    surface,
                    WHITE,
                    (caret_screen_x, caret_screen_y),
                    (caret_screen_x, caret_screen_y + caret_line_height),
                    1,
                )
        bar_rect = pygame.Rect(
            body_rect.right - scrollbar_width + 2,
            body_rect.y + 2,
            scrollbar_width - 4,
            body_rect.height - 4,
        )
        pygame.draw.rect(surface, GRAY_30, bar_rect)
        pygame.draw.rect(surface, WHITE, bar_rect, 1)
        if max_scroll > 0:
            thumb_h = max(20, int(bar_rect.height * visible_height / (content_height + 1e-5)))
            track = bar_rect.height - thumb_h
            thumb_y = bar_rect.y + int(track * (scroll / max_scroll))
            thumb_rect = pygame.Rect(bar_rect.x + 1, thumb_y, bar_rect.width - 2, thumb_h)
            pygame.draw.rect(surface, GRAY_70, thumb_rect)
            pygame.draw.rect(surface, WHITE, thumb_rect, 1)
        rects["fields"]["body"] = body_rect

    else:
        placeholder = "Clique em ADICIONAR ou selecione uma anotacao"
        draw_text(surface, placeholder, FONTS["sm"], WHITE, inner_right.center, center=True)

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
            state["body_styles"] = [default_style.copy() for _ in state["form"]["body"]]
            state["show_form"] = True
            state["focus"] = None
            state["body_scroll"] = 0
            state["number_sequence"] = None
            return
    state["focus"] = None


def handle_mousewheel(delta_y, rects, state, pos=None):
    body_rect = rects.get("fields", {}).get("body") if rects else None
    if not body_rect:
        return False
    if pos is None:
        pos = pygame.mouse.get_pos()
    if not body_rect.collidepoint(pos):
        return False
    if not (state.get("show_form") or state.get("selected") is not None):
        return False
    max_scroll = state.get("body_scroll_max", 0)
    if max_scroll <= 0:
        state["body_scroll"] = 0
        return True
    step = 40
    new_scroll = state.get("body_scroll", 0) - delta_y * step
    new_scroll = max(0, min(max_scroll, new_scroll))
    state["body_scroll"] = new_scroll
    return True


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
            seq = state.get("number_sequence")
            buf = buf[:cur] + "\n" + buf[cur:]
            styles = state.get("body_styles", [])
            styles = styles[:cur] + [state["style_flags"].copy()] + styles[cur:]
            cur += 1
            if seq:
                number_text = f"{seq + 1}. "
                style_snap = state["style_flags"].copy()
                buf = buf[:cur] + number_text + buf[cur:]
                insert_styles = [style_snap for _ in number_text]
                styles = styles[:cur] + insert_styles + styles[cur:]
                cur += len(number_text)
                state["number_sequence"] = seq + 1
            else:
                state["number_sequence"] = None
            state["body_styles"] = styles
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
            elif event.type == pygame.MOUSEWHEEL:
                handle_mousewheel(event.y, rects, NOTES_STATE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    handle_key(event, NOTES_STATE)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
