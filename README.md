# 一箭又一箭（Arrow After Arrow）

> 软件工程课程第二次个人作业：利用 AIGC 完成一个“一箭又一箭”风格的小游戏。

## 项目简介

“一箭又一箭”是一款点击式箭头解谜小游戏。棋盘上分布着朝上、下、左、右四个方向的箭头：
观察箭头方向与相互阻挡关系，按顺序点击箭头，让所有箭头依次飞出棋盘即可通关；
点到被前方箭头挡住的箭头会消耗一次失误机会，失误用尽则本关失败。

本项目使用 **Python + Pygame** 实现，全部箭头用 Pygame 基础图形（三角形）绘制，**不依赖任何外部图片/音频素材**。
核心规则、路径检测与关卡可解性算法在 `game.py` 中以纯 Python 实现，便于单独测试与复用。

## 开发环境

- 操作系统：Windows 10 / 11（Linux、macOS 亦可运行）
- Python：3.10 及以上
- Pygame：2.5 及以上
- 辅助开发：WorkBuddy / ChatGPT 等 AIGC 编程工具（详见博客）

## 安装与运行

```bash
# 1. 克隆仓库
git clone <你的克隆仓库>
cd arrow-game

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行游戏
python main.py
```

> 提示：若 `pip install pygame` 速度慢，可使用国内镜像，例如
> `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

## 游戏操作说明

| 操作 | 效果 |
| --- | --- |
| 鼠标点击「开始游戏」 | 进入第 1 关 |
| 鼠标点击箭头 | 若前方无阻挡，箭头沿指向飞出棋盘并消失；若被挡住，箭头晃动变红、消耗 1 次失误 |
| 鼠标点击「提示」 | 高亮一个当前可以飞出的箭头（扩展功能） |
| 鼠标点击「重新开始」 | 把当前关卡恢复到初始状态 |
| 清空全部箭头 | 弹出“本关通关”，点击「下一关」继续 |
| 失误次数耗尽 | 弹出“失败”，点击「重新开始」重试 |

界面顶部显示：当前关卡名、剩余箭头数量、剩余失误次数。

## 游戏截图

> 请将运行后的截图放入 `screenshots/` 目录，并替换下面的占位说明：
> - `screenshots/start.png` —— 开始界面
> - `screenshots/playing.png` —— 游戏进行中（含箭头、信息栏、按钮）
> - `screenshots/win.png` —— 通关界面
> - `screenshots/lose.png` —— 失败界面
> - `screenshots/demo.gif` —— 演示动画（可用 ScreenToGif / LICEcap 录制）

## 目录结构

```
arrow-game/
├── main.py        # 游戏主程序：Pygame 界面、交互、动画
├── game.py        # 核心逻辑：Arrow / Game 类、路径检测、关卡可解性求解器
├── levels.py      # 关卡数据（4 关，已验证均可通关）
├── test_game.py   # 自动化测试（覆盖 T01~T06 + 关卡可解性 + 整关模拟）
├── requirements.txt
├── README.md
└── blog_draft.md  # 博客草稿（含 AIGC 记录、测试结果、PSP、心得体会）
```

## 关卡说明

| 关卡 | 棋盘 | 箭头数 | 失误上限 | 特点 |
| --- | --- | --- | --- | --- |
| 第 1 关 · 热身 | 3×3 | 4 | 5 | 四个角，最小演示 |
| 第 2 关 · 两行连锁 | 5×5 | 4 | 5 | 两行连锁让路 |
| 第 3 关 · 链条与列 | 5×5 | 8 | 5 | 横向链 + 纵向链 |
| 第 4 关 · 混合阵 | 6×6 | 12 | 6 | 多条链交错，需按顺序让路 |

所有关卡都用 `game.is_level_solvable()` 验证过存在合理通关顺序。

## 测试

```bash
python -m unittest test_game -v
```

测试覆盖作业要求的 T01~T06，以及“全部关卡可通关”“按策略能整关通关”。
## 游戏截图
<img width="541" height="686" alt="屏幕截图 2026-09-13 173514" src="https://github.com/user-attachments/assets/22363dfb-f7ed-4931-b4c9-78268f1538c8" />

<img width="775" height="926" alt="屏幕截图 2026-09-13 173531" src="https://github.com/user-attachments/assets/7e2ea325-de18-465e-a81c-2878b7aaf3b7" />

<img width="787" height="935" alt="屏幕截图 2026-09-13 173542" src="https://github.com/user-attachments/assets/46a29c1e-89e8-4607-b587-c7ac6909cac5" />
