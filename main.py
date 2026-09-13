"""
main.py —— “一箭又一箭”游戏主程序（Pygame 实现界面、交互与动画）

运行方式：
    pip install pygame
    python main.py

游戏流程：开始界面 -> 游戏界面（多关）-> 通关/失败界面。
核心规则与算法在 game.py 中，本文件只负责“画出来”和“接收鼠标点击”。
"""

import os

import pygame

from game import Game, Arrow, find_hint
from levels import LEVELS

# ---------- 布局与配色 ----------
CELL = 84          # 每格的像素边长
MARGIN_X = 50      # 棋盘到窗口左右边的距离
TOP_UI = 96        # 顶部信息栏高度
FPS = 60
MIN_W = 600        # 窗口最小宽度（避免开始/结果界面文字被裁切）
MIN_H = 440        # 窗口最小高度
FLY_SPEED = 16     # 箭头飞出动画速度（像素/帧）

C_BG = (28, 32, 48)
C_BOARD = (40, 46, 66)
C_CELL = (54, 62, 88)
C_GRID = (72, 82, 116)
C_ARROW = (92, 200, 250)
C_ARROW_FLY = (120, 230, 160)
C_BLOCK = (240, 92, 92)
C_HINT = (250, 210, 90)
C_TEXT = (235, 240, 255)
C_TEXT_DIM = (150, 160, 190)
C_BTN = (70, 130, 200)
C_BTN_HOVER = (98, 162, 236)


def get_font(size, bold=False):
    """获取字体。直接加载系统自带的中文字体文件，避免依赖系统字体枚举（某些环境会崩溃）。

    优先顺序：黑体(simhei) -> 微软雅黑(msyh) -> 宋体(simsun) -> pygame 默认字体。
    """
    candidates = [
        r'C:\Windows\Fonts\simhei.ttf',
        r'C:\Windows\Fonts\msyh.ttc',
        r'C:\Windows\Fonts\simsun.ttc',
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                continue
    try:
        return pygame.font.SysFont('simhei', size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


def draw_text(surface, text, x, y, font, color, center=False):
    img = font.render(text, True, color)
    if center:
        surface.blit(img, img.get_rect(center=(x, y)))
    else:
        surface.blit(img, (x, y))


def wrap_text(text, font, max_width):
    """按字符宽度折行（兼容中文无空格文本），返回行列表。"""
    lines = []
    buf = ''
    for ch in text:
        if ch == '\n':
            lines.append(buf)
            buf = ''
            continue
        if font.size(buf + ch)[0] <= max_width:
            buf += ch
        else:
            if buf:
                lines.append(buf)
            buf = ch
    if buf:
        lines.append(buf)
    return lines


def draw_arrow(surface, cx, cy, direction, color):
    """在 (cx, cy) 处画一个指向 direction 的三角形箭头。"""
    s = CELL * 0.32
    if direction == 'R':
        pts = [(cx + s, cy), (cx - s * 0.8, cy - s * 0.8), (cx - s * 0.8, cy + s * 0.8)]
    elif direction == 'L':
        pts = [(cx - s, cy), (cx + s * 0.8, cy - s * 0.8), (cx + s * 0.8, cy + s * 0.8)]
    elif direction == 'U':
        pts = [(cx, cy - s), (cx - s * 0.8, cy + s * 0.8), (cx + s * 0.8, cy + s * 0.8)]
    else:  # 'D'
        pts = [(cx, cy + s), (cx - s * 0.8, cy - s * 0.8), (cx + s * 0.8, cy - s * 0.8)]
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.polygon(surface, (0, 0, 0), pts, 2)


class Button:
    def __init__(self, x, y, w, h, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label

    def draw(self, surface, font, hover):
        col = C_BTN_HOVER if hover else C_BTN
        pygame.draw.rect(surface, col, self.rect, border_radius=10)
        draw_text(surface, self.label, self.rect.centerx, self.rect.centery, font, C_TEXT, center=True)

    def hit(self, pos):
        return self.rect.collidepoint(pos)


class App:
    """游戏主程序，管理窗口、状态、动画与输入。"""

    def __init__(self):
        pygame.init()
        self.fonts = {
            'small': get_font(20),
            'mid': get_font(26),
            'big': get_font(42, bold=True),
        }
        self.level_index = 0
        self.game = Game(LEVELS[0])
        self.state = 'start'        # start / playing / level_clear / all_clear / lost
        self.flying = []            # 正在飞出的箭头动画: {'arrow', 'dist'}
        self.shaking = {}           # 正在晃动的箭头: (row,col) -> 剩余帧数
        self.hint_cell = None       # 提示高亮的格子
        self.screen = None
        self._setup_window()

    # ---------- 窗口与按钮布局 ----------
    def _setup_window(self):
        lv = LEVELS[self.level_index]
        w = max(MARGIN_X * 2 + lv['cols'] * CELL, MIN_W)
        h = max(TOP_UI + lv['rows'] * CELL + 80, MIN_H)
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption('一箭又一箭')
        bw, bh = lv['cols'] * CELL, lv['rows'] * CELL
        # 棋盘在窗口中水平居中，紧贴顶部信息栏下方
        self.board_x = (w - bw) // 2
        self.board_y = TOP_UI
        by = self.board_y
        cx = w // 2
        mid_y = by + bh // 2
        # 底部两个常驻按钮：左对齐窗口左边、右对齐窗口右边（棋盘下方左右分布）
        self.btn_restart = Button(MARGIN_X, by + bh + 18, 150, 46, '重新开始')
        self.btn_hint = Button(w - MARGIN_X - 150, by + bh + 18, 150, 46, '提示')
        # 结果界面按钮（与棋盘同宽居中）
        self.btn_start = Button(cx - 100, mid_y - 28, 200, 56, '开始游戏')
        self.btn_next = Button(cx - 100, mid_y - 28, 200, 56, '下一关 →')
        self.btn_retry = Button(cx - 100, mid_y - 28, 200, 56, '重新开始')
        self.btn_restart_all = Button(cx - 100, mid_y - 28, 200, 56, '再玩一次')

    # ---------- 输入处理 ----------
    def handle_click(self, pos):
        if self.state == 'start':
            if self.btn_start.hit(pos):
                self.state = 'playing'
            return

        if self.state == 'playing':
            if self.btn_restart.hit(pos):
                self._reset_level()
                return
            if self.btn_hint.hit(pos):
                self.hint_cell = find_hint(self.game)
                return
            lv = LEVELS[self.level_index]
            c = (pos[0] - self.board_x) // CELL
            r = (pos[1] - self.board_y) // CELL
            if 0 <= r < lv['rows'] and 0 <= c < lv['cols']:
                res = self.game.click(r, c)
                if res is None:
                    return
                kind, arrow = res
                if kind == 'fly':
                    self.flying.append({'arrow': arrow, 'dist': 0})
                else:  # block
                    self.shaking[(arrow.row, arrow.col)] = 18
                    self.hint_cell = None
                if self.game.state == 'won':
                    self.state = 'level_clear' if self.level_index < len(LEVELS) - 1 else 'all_clear'
                elif self.game.state == 'lost':
                    self.state = 'lost'
            return

        if self.state == 'level_clear' and self.btn_next.hit(pos):
            self.level_index += 1
            self.game = Game(LEVELS[self.level_index])
            self._reset_anim()
            self._setup_window()
            self.state = 'playing'
            return

        if self.state == 'all_clear' and self.btn_restart_all.hit(pos):
            self.level_index = 0
            self.game = Game(LEVELS[0])
            self._reset_anim()
            self._setup_window()
            self.state = 'playing'
            return

        if self.state == 'lost' and self.btn_retry.hit(pos):
            self._reset_level()
            self.state = 'playing'
            return

    def _reset_level(self):
        self.game.restart()
        self._reset_anim()

    def _reset_anim(self):
        self.flying = []
        self.shaking = {}
        self.hint_cell = None

    # ---------- 每帧更新动画 ----------
    def update(self):
        lv = LEVELS[self.level_index]
        board_right = self.board_x + lv['cols'] * CELL
        board_bottom = self.board_y + lv['rows'] * CELL
        new_flying = []
        for f in self.flying:
            f['dist'] += FLY_SPEED
            a = f['arrow']
            dr, dc = Arrow.DIRS[a.direction]
            cx = self.board_x + a.col * CELL + CELL / 2 + dc * f['dist']
            cy = self.board_y + a.row * CELL + CELL / 2 + dr * f['dist']
            off = cx < -CELL or cx > board_right + CELL or cy < -CELL or cy > board_bottom + CELL
            if not off:
                new_flying.append(f)
        self.flying = new_flying

        for k in list(self.shaking.keys()):
            self.shaking[k] -= 1
            if self.shaking[k] <= 0:
                del self.shaking[k]

    # ---------- 绘制 ----------
    def draw(self):
        self.screen.fill(C_BG)
        w = self.screen.get_width()
        h = self.screen.get_height()
        m = pygame.mouse.get_pos()

        if self.state == 'start':
            draw_text(self.screen, '一箭又一箭', w // 2, 70, self.fonts['big'], C_TEXT, center=True)
            tips = [
                '点击箭头，让它沿指向飞出棋盘',
                '前方有阻挡时箭头会晃动变红，并消耗一次失误',
                '清空全部箭头即可进入下一关，失误用尽则失败',
            ]
            y = 128
            for t in tips:
                for line in wrap_text(t, self.fonts['small'], w - 100):
                    draw_text(self.screen, line, w // 2, y, self.fonts['small'], C_TEXT_DIM, center=True)
                    y += 32
            btn_y = y + 26
            self.btn_start.rect = pygame.Rect(w // 2 - 100, btn_y, 200, 56)
            self.btn_start.draw(self.screen, self.fonts['mid'], self.btn_start.hit(m))
            return

        self._draw_board()
        self._draw_top_ui()
        self._draw_flying()

        if self.state == 'playing':
            self.btn_restart.draw(self.screen, self.fonts['mid'], self.btn_restart.hit(m))
            self.btn_hint.draw(self.screen, self.fonts['mid'], self.btn_hint.hit(m))
        elif self.state == 'level_clear':
            self._draw_overlay('本关通关！', f'剩余失误 {self.game.mistakes_allowed - self.game.mistakes} 次', self.btn_next)
        elif self.state == 'lost':
            self._draw_overlay('失败', '失误次数已用尽', self.btn_retry)
        elif self.state == 'all_clear':
            self._draw_overlay('全部通关！', f'你已通关全部 {len(LEVELS)} 关', self.btn_restart_all)

    def _draw_board(self):
        lv = LEVELS[self.level_index]
        bx, by = self.board_x, self.board_y
        bw, bh = lv['cols'] * CELL, lv['rows'] * CELL
        pygame.draw.rect(self.screen, C_BOARD, (bx, by, bw, bh), border_radius=8)
        for r in range(lv['rows']):
            for c in range(lv['cols']):
                x = bx + c * CELL
                y = by + r * CELL
                pygame.draw.rect(self.screen, C_CELL, (x + 3, y + 3, CELL - 6, CELL - 6), border_radius=6)
                pygame.draw.rect(self.screen, C_GRID, (x + 3, y + 3, CELL - 6, CELL - 6), 2, border_radius=6)
        for (r, c), a in self.game.arrows.items():
            cx = bx + c * CELL + CELL / 2
            cy = by + r * CELL + CELL / 2
            color = C_ARROW
            if (r, c) in self.shaking:
                off = 6 * ((self.shaking[(r, c)] % 6) - 3) / 3.0
                cx += off
                color = C_BLOCK
            elif self.hint_cell == (r, c):
                color = C_HINT
            draw_arrow(self.screen, cx, cy, a.direction, color)

    def _draw_top_ui(self):
        lv = LEVELS[self.level_index]
        w = self.screen.get_width()
        draw_text(self.screen, lv['name'], MARGIN_X, 22, self.fonts['mid'], C_TEXT)
        draw_text(self.screen, f'剩余箭头: {self.game.remaining()}', MARGIN_X, 60, self.fonts['small'], C_TEXT_DIM)
        left = self.game.mistakes_allowed - self.game.mistakes
        col = C_BLOCK if left <= 1 else C_TEXT_DIM
        txt = f'剩余失误: {left}'
        fw, _ = self.fonts['small'].size(txt)
        draw_text(self.screen, txt, w - MARGIN_X - fw, 60, self.fonts['small'], col)

    def _draw_flying(self):
        for f in self.flying:
            a = f['arrow']
            dr, dc = Arrow.DIRS[a.direction]
            cx = self.board_x + a.col * CELL + CELL / 2 + dc * f['dist']
            cy = self.board_y + a.row * CELL + CELL / 2 + dr * f['dist']
            draw_arrow(self.screen, cx, cy, a.direction, C_ARROW_FLY)

    def _draw_overlay(self, title, sub, btn):
        dim = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        dim.fill((10, 12, 20, 180))
        self.screen.blit(dim, (0, 0))
        w, h = self.screen.get_width(), self.screen.get_height()
        cx = w // 2
        # 标题居中偏上，副标题在其后换行显示，按钮放在最下方，三者互不重叠
        draw_text(self.screen, title, cx, h * 0.40, self.fonts['big'], C_TEXT, center=True)
        sub_lines = wrap_text(sub, self.fonts['mid'], w - 120)
        sy = h * 0.40 + 52
        for line in sub_lines:
            draw_text(self.screen, line, cx, sy, self.fonts['mid'], C_TEXT_DIM, center=True)
            sy += 34
        btn.rect = pygame.Rect(cx - 100, sy + 18, 200, 56)
        m = pygame.mouse.get_pos()
        btn.draw(self.screen, self.fonts['mid'], btn.hit(m))

    # ---------- 主循环 ----------
    def run(self):
        clock = pygame.time.Clock()
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.handle_click(ev.pos)
            self.update()
            self.draw()
            pygame.display.flip()
            clock.tick(FPS)


if __name__ == '__main__':
    App().run()
