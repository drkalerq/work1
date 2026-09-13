"""
test_game.py —— 自动化测试（不依赖 Pygame，纯逻辑测试）

覆盖作业要求的 T01~T06 测试用例 + 关卡可解性验证 + 整关通关模拟。

运行方式：
    python -m unittest test_game          # 逐条运行
    python test_game.py                    # 同上（含 __main__ 入口）
"""

import unittest

from game import Game, is_level_solvable
from levels import LEVELS


def make_level(rows, cols, arrows, mistakes=5):
    return {'rows': rows, 'cols': cols, 'arrows': arrows, 'mistakes': mistakes}


class TestT01FlyOut(unittest.TestCase):
    """T01：点击前方无阻挡的箭头，箭头飞出棋盘并消失。"""

    def test_fly(self):
        lv = make_level(3, 3, [(0, 2, 'R')], mistakes=5)  # 最右格朝右，前方无阻挡
        g = Game(lv)
        before = g.remaining()
        res = g.click(0, 2)
        self.assertEqual(res[0], 'fly')
        self.assertEqual(g.remaining(), before - 1)


class TestT02Blocked(unittest.TestCase):
    """T02：点击前方有阻挡的箭头，箭头不消失，失误次数 -1。"""

    def test_block(self):
        # (0,0) 朝右，但 (0,2) 挡在右侧
        lv = make_level(3, 3, [(0, 0, 'R'), (0, 2, 'R')], mistakes=5)
        g = Game(lv)
        res = g.click(0, 0)
        self.assertEqual(res[0], 'block')
        self.assertEqual(g.remaining(), 2)          # 没减少
        self.assertEqual(g.mistakes, 1)             # 失误 +1


class TestT03EdgeNoError(unittest.TestCase):
    """T03：点击位于边缘且朝向棋盘外的箭头，正常消失，不越界报错。"""

    def test_four_edges(self):
        # 5x5 棋盘，边缘（含四角）各放一个朝外的箭头；单格只放一个，避免冲突。
        # 这些箭头前方都是棋盘外，应全部能飞出且不越界报错。
        lv = make_level(5, 5, [
            (0, 0, 'U'), (0, 2, 'U'), (0, 4, 'R'),   # 上边
            (2, 0, 'L'),                (2, 4, 'R'),  # 左右边
            (4, 0, 'D'), (4, 2, 'D'), (4, 4, 'L'),   # 下边
        ], mistakes=5)
        g = Game(lv)
        for (r, c, d) in lv['arrows']:
            res = g.click(r, c)
            self.assertEqual(res[0], 'fly', f'边缘箭头 ({r},{c},{d}) 应可飞出')

    def test_no_index_error(self):
        # 直接验证路径检测不会越界
        lv = make_level(1, 1, [(0, 0, 'R')], mistakes=5)
        g = Game(lv)
        self.assertTrue(g.is_path_clear(g.arrows[(0, 0)]))


class TestT04ClearLevel(unittest.TestCase):
    """T04：消除本关全部箭头，显示通关（state 变为 won）。"""

    def test_win(self):
        lv = make_level(1, 1, [(0, 0, 'R')], mistakes=5)
        g = Game(lv)
        g.click(0, 0)
        self.assertEqual(g.state, 'won')
        self.assertEqual(g.remaining(), 0)


class TestT05Lose(unittest.TestCase):
    """T05：失误次数耗尽，显示失败（state 变为 lost）。"""

    def test_lose(self):
        lv = make_level(3, 3, [(0, 0, 'R'), (0, 2, 'R')], mistakes=1)
        g = Game(lv)
        g.click(0, 0)  # 被 (0,2) 挡住 -> 失误 1，达到上限 -> lost
        self.assertEqual(g.mistakes, 1)
        self.assertEqual(g.state, 'lost')


class TestT06Restart(unittest.TestCase):
    """T06：游戏进行中重新开始，箭头布局和失误次数恢复。"""

    def test_restart(self):
        lv = make_level(3, 3, [(0, 0, 'R'), (0, 2, 'R')], mistakes=5)
        g = Game(lv)
        g.click(0, 0)              # 制造一次失误
        self.assertEqual(g.mistakes, 1)
        g.restart()
        self.assertEqual(g.mistakes, 0)
        self.assertEqual(g.remaining(), 2)
        self.assertEqual(g.state, 'playing')


class TestLevelsSolvable(unittest.TestCase):
    """所有交付关卡都必须存在合理的通关顺序（用贪心求解器校验）。"""

    def test_all_levels(self):
        for lv in LEVELS:
            with self.subTest(name=lv['name']):
                self.assertTrue(is_level_solvable(lv), f"{lv['name']} 不可通关")


class TestPlayThrough(unittest.TestCase):
    """整关模拟：按“每次点一个前方无阻挡的箭头”的策略，应能通关每一关。"""

    def test_solve_all(self):
        for lv in LEVELS:
            with self.subTest(name=lv['name']):
                g = Game(lv)
                steps = 0
                while g.state == 'playing' and steps < 1000:
                    # 找一个能飞出的箭头并点击
                    target = None
                    for (r, c), a in g.arrows.items():
                        if g.is_path_clear(a):
                            target = (r, c)
                            break
                    self.assertIsNotNone(target, f"{lv['name']} 出现死局，无箭头可飞出")
                    g.click(*target)
                    steps += 1
                self.assertEqual(g.state, 'won', f"{lv['name']} 未能通关")


if __name__ == '__main__':
    unittest.main(verbosity=2)
