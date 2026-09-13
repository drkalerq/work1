"""
game.py —— “一箭又一箭”小游戏的核心逻辑（纯 Python，不依赖 Pygame）

把游戏规则、路径检测、关卡状态都放在这里，方便单独测试和复用。
界面渲染在 main.py 中完成。
"""


class Arrow:
    """表示棋盘上的一个带方向的箭头。"""

    # 四个方向对应的位移：(行变化, 列变化)
    DIRS = {
        'U': (-1, 0),   # 上
        'D': (1, 0),    # 下
        'L': (0, -1),   # 左
        'R': (0, 1),    # 右
    }

    def __init__(self, row, col, direction):
        self.row = row
        self.col = col
        self.direction = direction  # 'U' / 'D' / 'L' / 'R'

    def __repr__(self):
        return f"Arrow({self.row},{self.col},{self.direction})"


class Game:
    """一局游戏的状态机：负责棋盘、点击判定、失误次数、关卡流程。"""

    def __init__(self, level):
        self.rows = level['rows']
        self.cols = level['cols']
        self.name = level.get('name', '')
        self.mistakes_allowed = level.get('mistakes', 5)
        self.mistakes = 0
        # 用字典 (row, col) -> Arrow 保存当前棋盘上的箭头
        self.arrows = {}
        for (r, c, d) in level['arrows']:
            self.arrows[(r, c)] = Arrow(r, c, d)
        # 保存初始布局，用于“重新开始”
        self._initial = list(level['arrows'])
        self.state = 'playing'  # 'playing' / 'won' / 'lost'

    # ---------- 路径检测：核心算法 ----------
    def is_path_clear(self, arrow):
        """判断 arrow 前进方向上、到边界之间是否没有其他箭头。

        没有阻挡返回 True（可以飞出棋盘），有阻挡返回 False。
        检测方式：从箭头所在格出发，沿其方向一格一格走，只要还在棋盘内
        就检查该格是否有别的箭头；遇到则返回 False，走到棋盘外都没遇到则返回 True。
        """
        dr, dc = Arrow.DIRS[arrow.direction]
        r = arrow.row + dr
        c = arrow.col + dc
        while 0 <= r < self.rows and 0 <= c < self.cols:
            if (r, c) in self.arrows:
                return False  # 路上有别的箭头，被挡住
            r += dr
            c += dc
        return True  # 一路畅通直到边界

    # ---------- 点击处理 ----------
    def click(self, row, col):
        """点击 (row, col) 处的箭头。

        返回：
            ('fly',   arrow) —— 前方无阻挡，箭头飞出并被消除
            ('block', arrow) —— 前方有阻挡，失误次数 +1，箭头不消失
            None             —— 游戏已结束，或点到空格
        """
        if self.state != 'playing':
            return None
        arrow = self.arrows.get((row, col))
        if arrow is None:
            return None  # 点到空格，无反应

        if self.is_path_clear(arrow):
            del self.arrows[(row, col)]
            if not self.arrows:
                self.state = 'won'  # 本关全部清空
            return ('fly', arrow)
        else:
            self.mistakes += 1
            if self.mistakes >= self.mistakes_allowed:
                self.state = 'lost'  # 失误次数耗尽
            return ('block', arrow)

    def remaining(self):
        """剩余箭头数量。"""
        return len(self.arrows)

    def restart(self):
        """把当前关卡恢复到初始状态（重新开始）。"""
        self.arrows = {}
        self.mistakes = 0
        self.state = 'playing'
        for (r, c, d) in self._initial:
            self.arrows[(r, c)] = Arrow(r, c, d)


def is_level_solvable(level):
    """用贪心法判断关卡是否可通关（也用于自动生成关卡时校验）。

    原理：反复移除当前“前方无阻挡”的任意一个箭头。
    因为移除一个箭头只会减少阻挡、永远不会增加阻挡，所以：
    只要该关卡存在某种通关顺序，贪心就一定能找到；
    若某一步“没有任何箭头能飞出”却仍有箭头剩余，则本关确实不可通关。
    """
    remaining = {(r, c): d for (r, c, d) in level['arrows']}
    rows, cols = level['rows'], level['cols']

    def clear(r, c, d):
        dr, dc = Arrow.DIRS[d]
        r2, c2 = r + dr, c + dc
        while 0 <= r2 < rows and 0 <= c2 < cols:
            if (r2, c2) in remaining:
                return False
            r2 += dr
            c2 += dc
        return True

    while remaining:
        progressed = False
        for (r, c), d in list(remaining.items()):
            if clear(r, c, d):
                del remaining[(r, c)]
                progressed = True
                break
        if not progressed:
            return False
    return True


def find_hint(game):
    """扩展功能：找出当前棋盘上一个“前方无阻挡”的箭头，用于提示。"""
    for (r, c), a in game.arrows.items():
        if game.is_path_clear(a):
            return (r, c)
    return None
