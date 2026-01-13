import sys
import ctypes
from ctypes import wintypes
import pygame

# Dimensoes base alinhadas com outros paineis
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
pygame.display.set_caption("Painel de Mesa (demo)")
WINDOW = None
CLOCK = pygame.time.Clock()

try:
    from pygame._sdl2 import Window, Renderer, Texture
    SDL2_AVAILABLE = True
except Exception:
    Window = None
    Renderer = None
    Texture = None
    SDL2_AVAILABLE = False

if sys.platform == "win32":
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    SRCCOPY = 0x00CC0020
    BI_RGB = 0
    DIB_RGB_COLORS = 0

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [
            ("bmiHeader", BITMAPINFOHEADER),
            ("bmiColors", wintypes.DWORD * 3),
        ]

FONTS = {
    "xs": pygame.font.SysFont("arial", 12),
    "sm": pygame.font.SysFont("arial", 14),
    "sm_b": pygame.font.SysFont("arial", 14, bold=True),
    "md": pygame.font.SysFont("arial", 18, bold=True),
    "lg": pygame.font.SysFont("arial", 26, bold=True),
}


def draw_text(surface, text, font, color, pos, center=False):
    render = font.render(str(text), True, color)
    rect = render.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(render, rect)
    return rect


def clamp_text(text, font, max_width):
    if font.size(text)[0] <= max_width:
        return text
    trimmed = text
    while trimmed and font.size(trimmed + "...")[0] > max_width:
        trimmed = trimmed[:-1]
    return trimmed + "..." if trimmed else "..."


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


def get_available_displays():
    sizes = []
    if hasattr(pygame.display, "get_desktop_sizes"):
        try:
            sizes = pygame.display.get_desktop_sizes()
        except pygame.error:
            sizes = []
    if not sizes:
        info = pygame.display.Info()
        if info.current_w and info.current_h:
            sizes = [(info.current_w, info.current_h)]
    return sizes


def get_display_rects():
    if sys.platform != "win32":
        return []
    monitors = []
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM
    )

    def enum_callback(hmonitor, hdc, lprect, lparam):
        rect = lprect.contents
        monitors.append((rect.left, rect.top, rect.right, rect.bottom))
        return True

    try:
        user32.EnumDisplayMonitors(0, 0, callback_type(enum_callback), 0)
    except Exception:
        return []
    return monitors


def refresh_display_list(transmission):
    rects = get_display_rects()
    if rects:
        transmission["display_rects"] = rects
        transmission["displays"] = [(r - l, b - t) for (l, t, r, b) in rects]
    else:
        transmission["displays"] = get_available_displays()
        transmission["display_rects"] = []


def get_available_windows():
    if sys.platform != "win32":
        return [], "Somente Windows"
    try:
        user32 = ctypes.windll.user32
        enum_windows = user32.EnumWindows
        get_window_text_length = user32.GetWindowTextLengthW
        get_window_text = user32.GetWindowTextW
        is_window_visible = user32.IsWindowVisible
        shell_window = user32.GetShellWindow()
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        windows = []
        skip_titles = {"Painel de Mesa (demo)", "Transmissao"}

        def enum_callback(hwnd, lparam):
            if hwnd == shell_window:
                return True
            if not is_window_visible(hwnd):
                return True
            length = get_window_text_length(hwnd)
            if length == 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            get_window_text(hwnd, buffer, length + 1)
            title = buffer.value.strip()
            if not title or title in skip_titles:
                return True
            windows.append((hwnd, title))
            return True

        enum_windows(callback_type(enum_callback), 0)
        windows.sort(key=lambda item: item[1].lower())
        return windows, None
    except Exception:
        return [], "Erro ao listar janelas"


def capture_from_dc(src_dc, width, height, src_x=0, src_y=0):
    if sys.platform != "win32":
        return None
    if width <= 0 or height <= 0:
        return None
    mem_dc = gdi32.CreateCompatibleDC(src_dc)
    bmp = gdi32.CreateCompatibleBitmap(src_dc, width, height)
    old = gdi32.SelectObject(mem_dc, bmp)
    gdi32.BitBlt(mem_dc, 0, 0, width, height, src_dc, src_x, src_y, SRCCOPY)

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB

    buffer = ctypes.create_string_buffer(width * height * 4)
    bits = gdi32.GetDIBits(
        mem_dc, bmp, 0, height, buffer, ctypes.byref(bmi), DIB_RGB_COLORS
    )
    gdi32.SelectObject(mem_dc, old)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem_dc)
    if bits == 0:
        return None
    surface = pygame.image.frombuffer(buffer, (width, height), "BGRA")
    return surface.copy()


def capture_display(display_rect=None):
    if sys.platform != "win32":
        return None
    if display_rect:
        left, top, right, bottom = display_rect
        width = right - left
        height = bottom - top
        src_x, src_y = left, top
    else:
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        src_x, src_y = 0, 0
    hdc = user32.GetDC(0)
    try:
        return capture_from_dc(hdc, width, height, src_x, src_y)
    finally:
        user32.ReleaseDC(0, hdc)


def capture_window(hwnd):
    if sys.platform != "win32" or not hwnd:
        return None
    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width <= 0 or height <= 0:
        return None
    hdc_window = user32.GetWindowDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(hdc_window)
    bmp = gdi32.CreateCompatibleBitmap(hdc_window, width, height)
    old = gdi32.SelectObject(mem_dc, bmp)

    captured = False
    if hasattr(user32, "PrintWindow"):
        PW_RENDERFULLCONTENT = 0x00000002
        if user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT):
            captured = True
    if not captured:
        gdi32.BitBlt(mem_dc, 0, 0, width, height, hdc_window, 0, 0, SRCCOPY)

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB

    buffer = ctypes.create_string_buffer(width * height * 4)
    bits = gdi32.GetDIBits(
        mem_dc, bmp, 0, height, buffer, ctypes.byref(bmi), DIB_RGB_COLORS
    )
    gdi32.SelectObject(mem_dc, old)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hwnd, hdc_window)
    if bits == 0:
        return None
    surface = pygame.image.frombuffer(buffer, (width, height), "BGRA")
    return surface.copy()


def get_default_transmission_size(display_size):
    if not display_size:
        return 960, 540
    w, h = display_size
    if not w or not h:
        return 960, 540
    target_w = min(960, max(480, w // 2))
    target_h = max(270, int(target_w * h / w))
    return target_w, target_h


def get_window_size(win):
    size = getattr(win, "size", None)
    if size:
        return size
    w = getattr(win, "width", 0)
    h = getattr(win, "height", 0)
    if w and h:
        return w, h
    return 640, 360


def open_transmission_window(state):
    if not SDL2_AVAILABLE:
        state["transmission"]["window_error"] = "SDL2 indisponivel"
        return
    if state.get("transmission_window"):
        return
    display_size = state["transmission"].get("selected_size")
    init_size = get_default_transmission_size(display_size)
    win = Window("Transmissao", size=init_size, resizable=True)
    renderer = Renderer(win, vsync=True)
    state["transmission_window"] = win
    state["transmission_renderer"] = renderer
    state["transmission"]["window_error"] = None


def close_transmission_window(state):
    win = state.get("transmission_window")
    if win:
        try:
            win.destroy()
        except Exception:
            pass
    state["transmission_window"] = None
    state["transmission_renderer"] = None


def render_transmission_window(state):
    if not SDL2_AVAILABLE:
        return
    win = state.get("transmission_window")
    renderer = state.get("transmission_renderer")
    if not win or not renderer:
        return
    w, h = get_window_size(win)
    transmission = state["transmission"]
    source_mode = transmission.get("source_mode", "display")
    display_idx = transmission.get("selected_display")
    display_size = transmission.get("selected_size")
    selected_window = transmission.get("selected_window")
    capture_surface = transmission.get("capture_surface")
    renderer.draw_color = (18, 18, 18, 255)
    renderer.clear()

    if capture_surface:
        src_w, src_h = capture_surface.get_size()
        scale = min(w / src_w, h / src_h)
        draw_w = max(1, int(src_w * scale))
        draw_h = max(1, int(src_h * scale))
        dst_x = (w - draw_w) // 2
        dst_y = (h - draw_h) // 2
        texture = Texture.from_surface(renderer, capture_surface)
        dst_rect = pygame.Rect(dst_x, dst_y, draw_w, draw_h)
        if hasattr(renderer, "copy"):
            renderer.copy(texture, dstrect=dst_rect)
        elif hasattr(renderer, "blit"):
            try:
                renderer.blit(texture, dst_rect)
            except TypeError:
                renderer.blit(texture, dstrect=dst_rect)
        elif hasattr(texture, "draw"):
            try:
                texture.draw(dstrect=dst_rect)
            except TypeError:
                texture.draw()
    else:
        step = max(40, min(w, h) // 8)
        renderer.draw_color = (45, 45, 45, 255)
        for x in range(0, w, step):
            renderer.draw_line((x, 0), (x, h))
        for y in range(0, h, step):
            renderer.draw_line((0, y), (w, y))

        renderer.draw_color = (80, 80, 80, 255)
        renderer.draw_rect((10, 10, w - 20, h - 20))

    line_1 = "TRANSMISSAO ATIVA"
    if source_mode == "window":
        if selected_window:
            line_2 = f"Janela: {selected_window[1]}"
        else:
            line_2 = "Janela nao definida"
    else:
        if display_idx is not None and display_size:
            d_w, d_h = display_size
            line_2 = f"Tela {display_idx + 1} - {d_w}x{d_h}"
        else:
            line_2 = "Tela nao definida"
    line_3 = "Captura em tempo real" if capture_surface else "Previsualizacao local (placeholder)"

    lines = [line_1, line_2, line_3]
    y = 24
    for idx, line in enumerate(lines):
        font = FONTS["sm_b"] if idx == 0 else FONTS["sm"]
        surface = font.render(line, True, (230, 230, 230))
        texture = Texture.from_surface(renderer, surface)
        rect = surface.get_rect()
        rect.topleft = (24, y)
        if hasattr(renderer, "copy"):
            renderer.copy(texture, dstrect=rect)
        elif hasattr(renderer, "blit"):
            try:
                renderer.blit(texture, rect)
            except TypeError:
                renderer.blit(texture, dstrect=rect)
        elif hasattr(texture, "draw"):
            try:
                texture.draw(dstrect=rect)
            except TypeError:
                texture.draw()
        y += rect.height + 6

    renderer.present()


def update_transmission_window(state):
    transmission = state["transmission"]
    if not transmission.get("active"):
        if state.get("transmission_window"):
            close_transmission_window(state)
        return
    if not state.get("transmission_window"):
        open_transmission_window(state)
    if not state.get("transmission_window"):
        return
    now = pygame.time.get_ticks()
    interval = transmission.get("capture_interval_ms", 66)
    last_capture = transmission.get("last_capture_ms", 0)
    if now - last_capture >= interval:
        transmission["last_capture_ms"] = now
        transmission["capture_error"] = None
        surface = None
        if transmission.get("source_mode") == "window":
            selected_window = transmission.get("selected_window")
            if selected_window:
                surface = capture_window(selected_window[0])
                if surface is None:
                    transmission["capture_error"] = "Falha ao capturar janela"
            else:
                transmission["capture_error"] = "Janela nao definida"
        else:
            selected_rect = transmission.get("selected_rect")
            if not selected_rect and transmission.get("selected_display") is not None:
                rects = transmission.get("display_rects", [])
                idx = transmission["selected_display"]
                if 0 <= idx < len(rects):
                    selected_rect = rects[idx]
            surface = capture_display(selected_rect)
            if surface is None:
                transmission["capture_error"] = "Falha ao capturar tela"
        if surface:
            transmission["capture_surface"] = surface
    render_transmission_window(state)


def draw_button(surface, rect, label, bg, disabled=False):
    fill = GRAY_40 if disabled else bg
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, BLACK, rect, 1)
    draw_text(surface, label, FONTS["sm_b"], WHITE, rect.center, center=True)


def draw_tabs(surface, state):
    tab_h = 36
    tab_w = WIDTH // max(1, len(state["tabs"]))
    rects = []
    for idx, label in enumerate(state["tabs"]):
        rect = pygame.Rect(idx * tab_w, 0, tab_w, tab_h)
        active = label == state["active_tab"]
        pygame.draw.rect(surface, GRAY_60 if active else GRAY_40, rect)
        pygame.draw.rect(surface, BLACK, rect, 1)
        draw_text(surface, label, FONTS["md"], WHITE, rect.center, center=True)
        rects.append((label, rect))
    return rects, tab_h


MESA_STATE = {
    "tabs": ["GERAL", "INVENTARIO", "HABILIDADES", "ANOTACOES", "MESA"],
    "active_tab": "MESA",
    "players": [],
    "scene_title": "Sem cena definida",
    "scene_desc": "",
    "note": "",
    "transmission": {
        "active": False,
        "source_mode": "display",
        "selected_display": None,
        "selected_size": None,
        "selected_rect": None,
        "selected_window": None,
        "modal_open": False,
        "displays": [],
        "display_rects": [],
        "windows": [],
        "windows_error": None,
        "window_error": None,
        "capture_surface": None,
        "capture_error": None,
        "last_capture_ms": 0,
        "capture_interval_ms": 66,
    },
    "transmission_window": None,
    "transmission_renderer": None,
    "focus": None,  # "note"
    "cursor": {"note": 0},
    "rects": {"fields": {}, "buttons": {}},
}


def draw_transmission_panel(surface, inner, state, rects):
    transmission = state["transmission"]
    panel_rect = pygame.Rect(inner.x, inner.y + 24, 320, 170)
    pygame.draw.rect(surface, GRAY_20, panel_rect)
    pygame.draw.rect(surface, WHITE, panel_rect, 2)

    draw_text(
        surface, "TRANSMISSAO", FONTS["sm_b"], WHITE, (panel_rect.x + 10, panel_rect.y + 8)
    )

    status = "ativo" if transmission["active"] else "parado"
    draw_text(
        surface,
        f"Status: {status}",
        FONTS["sm"],
        GRAY_80,
        (panel_rect.x + 10, panel_rect.y + 40),
    )

    source_mode = transmission.get("source_mode", "display")
    source_label = "Tela" if source_mode == "display" else "Janela"
    draw_text(
        surface,
        f"Fonte: {source_label}",
        FONTS["sm"],
        GRAY_80,
        (panel_rect.x + 10, panel_rect.y + 58),
    )

    if source_mode == "window":
        selected_window = transmission.get("selected_window")
        if selected_window:
            detail_text = f"Janela: {selected_window[1]}"
        else:
            detail_text = "Janela: nenhuma"
    elif transmission["selected_size"]:
        idx = (transmission["selected_display"] or 0) + 1
        w, h = transmission["selected_size"]
        detail_text = f"Tela: {idx} ({w}x{h})"
    else:
        detail_text = "Tela: nenhuma"
    detail_text = clamp_text(detail_text, FONTS["sm"], panel_rect.w - 20)
    draw_text(
        surface,
        detail_text,
        FONTS["sm"],
        GRAY_80,
        (panel_rect.x + 10, panel_rect.y + 76),
    )
    if transmission.get("window_error"):
        draw_text(
            surface,
            transmission["window_error"],
            FONTS["xs"],
            RED,
            (panel_rect.x + 10, panel_rect.y + 96),
        )
    elif transmission.get("capture_error"):
        draw_text(
            surface,
            transmission["capture_error"],
            FONTS["xs"],
            RED,
            (panel_rect.x + 10, panel_rect.y + 96),
        )
    else:
        draw_text(
            surface,
            "Clique em PLAY para escolher a fonte.",
            FONTS["xs"],
            GRAY_80,
            (panel_rect.x + 10, panel_rect.y + 96),
        )

    play_rect = pygame.Rect(panel_rect.x + 10, panel_rect.bottom - 44, 90, 32)
    stop_rect = pygame.Rect(play_rect.right + 10, play_rect.y, 90, 32)
    rects["buttons"]["transmission_play"] = play_rect
    rects["buttons"]["transmission_stop"] = stop_rect
    draw_button(surface, play_rect, "PLAY", GREEN, disabled=transmission["modal_open"])
    draw_button(surface, stop_rect, "STOP", RED, disabled=False)


def draw_transmission_modal(surface, state, rects):
    transmission = state["transmission"]
    if not transmission["modal_open"]:
        return
    source_mode = transmission.get("source_mode", "display")
    if source_mode == "display" and not transmission["displays"]:
        refresh_display_list(transmission)
    if source_mode == "window" and not transmission["windows"]:
        windows, error = get_available_windows()
        transmission["windows"] = windows
        transmission["windows_error"] = error

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    modal_w, modal_h = 460, 300
    modal_rect = pygame.Rect(0, 0, modal_w, modal_h)
    modal_rect.center = (WIDTH // 2, HEIGHT // 2)
    pygame.draw.rect(surface, GRAY_20, modal_rect)
    pygame.draw.rect(surface, WHITE, modal_rect, 2)
    draw_text(
        surface,
        "ESCOLHA A FONTE",
        FONTS["sm_b"],
        WHITE,
        (modal_rect.x + 14, modal_rect.y + 12),
    )

    mode_display_rect = pygame.Rect(modal_rect.x + 14, modal_rect.y + 38, 90, 24)
    mode_window_rect = pygame.Rect(mode_display_rect.right + 8, modal_rect.y + 38, 90, 24)
    rects["buttons"]["transmission_modal_mode_display"] = mode_display_rect
    rects["buttons"]["transmission_modal_mode_window"] = mode_window_rect
    draw_button(
        surface,
        mode_display_rect,
        "TELA",
        GRAY_60 if source_mode == "display" else GRAY_40,
    )
    draw_button(
        surface,
        mode_window_rect,
        "JANELA",
        GRAY_60 if source_mode == "window" else GRAY_40,
    )

    start_y = modal_rect.y + 70
    button_h = 30
    spacing = 8
    list_bottom = modal_rect.bottom - 52
    available_h = max(0, list_bottom - start_y)
    max_items = max(1, available_h // (button_h + spacing))

    items = []
    prefix = ""
    if source_mode == "window":
        items = transmission.get("windows", [])
        prefix = "transmission_modal_window_"
    else:
        items = transmission.get("displays", [])
        prefix = "transmission_modal_display_"

    for idx, item in enumerate(items[:max_items]):
        if source_mode == "window":
            label = f"Janela {idx + 1} - {item[1]}"
        else:
            w, h = item
            label = f"Tela {idx + 1} - {w}x{h}"
        btn_rect = pygame.Rect(
            modal_rect.x + 14,
            start_y + idx * (button_h + spacing),
            modal_rect.w - 28,
            button_h,
        )
        rects["buttons"][f"{prefix}{idx}"] = btn_rect
        label = clamp_text(label, FONTS["sm_b"], btn_rect.w - 12)
        draw_button(surface, btn_rect, label, GRAY_60)

    if source_mode == "window" and transmission.get("windows_error"):
        draw_text(
            surface,
            transmission["windows_error"],
            FONTS["sm"],
            RED,
            (modal_rect.x + 14, start_y),
        )
    elif not items:
        empty_label = "Nenhuma janela detectada." if source_mode == "window" else "Nenhuma tela detectada."
        draw_text(
            surface,
            empty_label,
            FONTS["sm"],
            GRAY_80,
            (modal_rect.x + 14, start_y),
        )
    elif len(items) > max_items:
        draw_text(
            surface,
            "Mais itens disponiveis...",
            FONTS["xs"],
            GRAY_80,
            (modal_rect.x + 14, list_bottom + 6),
        )

    cancel_rect = pygame.Rect(modal_rect.right - 104, modal_rect.bottom - 42, 90, 30)
    rects["buttons"]["transmission_modal_cancel"] = cancel_rect
    draw_button(surface, cancel_rect, "CANCELAR", GRAY_40)


def draw_mesa_panel(surface, state):
    surface.fill(BLACK)
    rects = {"fields": {}, "buttons": {}}

    panel_rect = pygame.Rect(8, 8, WIDTH - 16, HEIGHT - 16)
    pygame.draw.rect(surface, BLACK, panel_rect)
    pygame.draw.rect(surface, WHITE, panel_rect, 2)

    inner = panel_rect.inflate(-12, -12)
    draw_text(surface, "MESA", FONTS["md"], WHITE, (inner.x, inner.y - 4))
    draw_transmission_panel(surface, inner, state, rects)
    draw_transmission_modal(surface, state, rects)

    state["rects"] = rects
    return rects


def insert_text(state, field, text):
    if field != "note":
        return
    buf = state.get("note", "")
    cur = state.get("cursor", {}).get(field, len(buf))
    cur = max(0, min(cur, len(buf)))
    state["note"] = buf[:cur] + text + buf[cur:]
    state["cursor"][field] = cur + len(text)


def handle_mouse(pos, rects, state):
    state["focus"] = None
    buttons = rects.get("buttons", {})
    transmission = state["transmission"]

    if transmission.get("modal_open"):
        for key, rect in buttons.items():
            if not rect.collidepoint(pos):
                continue
            if key == "transmission_modal_cancel":
                transmission["modal_open"] = False
                return True
            if key == "transmission_modal_mode_display":
                transmission["source_mode"] = "display"
                transmission["windows_error"] = None
                if not transmission["displays"]:
                    refresh_display_list(transmission)
                return True
            if key == "transmission_modal_mode_window":
                transmission["source_mode"] = "window"
                windows, error = get_available_windows()
                transmission["windows"] = windows
                transmission["windows_error"] = error
                return True
            if key.startswith("transmission_modal_display_"):
                idx = int(key.split("_")[-1])
                displays = transmission.get("displays", [])
                if 0 <= idx < len(displays):
                    transmission["selected_display"] = idx
                    transmission["selected_size"] = displays[idx]
                    rects = transmission.get("display_rects", [])
                    transmission["selected_rect"] = rects[idx] if idx < len(rects) else None
                    transmission["selected_window"] = None
                    transmission["source_mode"] = "display"
                    transmission["active"] = True
                    transmission["capture_surface"] = None
                    transmission["capture_error"] = None
                    open_transmission_window(state)
                transmission["modal_open"] = False
                return True
            if key.startswith("transmission_modal_window_"):
                idx = int(key.split("_")[-1])
                windows = transmission.get("windows", [])
                if 0 <= idx < len(windows):
                    transmission["selected_window"] = windows[idx]
                    transmission["selected_display"] = None
                    transmission["selected_size"] = None
                    transmission["selected_rect"] = None
                    transmission["source_mode"] = "window"
                    transmission["active"] = True
                    transmission["capture_surface"] = None
                    transmission["capture_error"] = None
                    open_transmission_window(state)
                transmission["modal_open"] = False
                return True
        return False

    play_rect = buttons.get("transmission_play")
    if play_rect and play_rect.collidepoint(pos):
        transmission["modal_open"] = True
        if transmission.get("source_mode", "display") == "window":
            windows, error = get_available_windows()
            transmission["windows"] = windows
            transmission["windows_error"] = error
        else:
            refresh_display_list(transmission)
        return True

    stop_rect = buttons.get("transmission_stop")
    if stop_rect and stop_rect.collidepoint(pos):
        transmission["active"] = False
        transmission["capture_surface"] = None
        transmission["capture_error"] = None
        close_transmission_window(state)
        return True

    note_rect = rects.get("fields", {}).get("note")
    if note_rect and note_rect.collidepoint(pos):
        state["focus"] = "note"
        state["cursor"]["note"] = len(state.get("note", ""))
        return True
    return False


def handle_key(event, state):
    if state.get("focus") != "note":
        return
    buf = state.get("note", "")
    cur = state.get("cursor", {}).get("note", len(buf))
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
        buf = buf[:cur] + "\n" + buf[cur:]
        cur += 1
    state["note"] = buf
    state["cursor"]["note"] = cur


def handle_text_input(event, state):
    if state.get("focus") != "note":
        return
    if event.text:
        insert_text(state, "note", event.text)


def handle_mousewheel(delta_y, rects, state, pos=None):
    return False


def main():
    global WINDOW
    WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Painel de Mesa (demo)")
    running = True
    while running:
        rects = draw_mesa_panel(WINDOW, MESA_STATE)
        pygame.display.flip()
        update_transmission_window(MESA_STATE)
        CLOCK.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif hasattr(pygame, "WINDOWEVENT") and event.type == pygame.WINDOWEVENT:
                if (
                    event.event == pygame.WINDOWEVENT_CLOSE
                    and MESA_STATE.get("transmission_window")
                ):
                    win = MESA_STATE["transmission_window"]
                    win_id = getattr(win, "id", None)
                    if win_id and event.windowID == win_id:
                        MESA_STATE["transmission"]["active"] = False
                        close_transmission_window(MESA_STATE)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_mouse(event.pos, rects, MESA_STATE)
            elif event.type == pygame.TEXTINPUT:
                handle_text_input(event, MESA_STATE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    handle_key(event, MESA_STATE)
            elif event.type == pygame.MOUSEWHEEL:
                handle_mousewheel(event.y, rects, MESA_STATE, getattr(event, "pos", None))
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
