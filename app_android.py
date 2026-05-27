# -*- coding: utf-8 -*-
"""
训练我的第一个分类器 · Android / Huawei Tablet 版 (Kivy)
================================================================================
完整移植自 app_trainable.py（已同步以下改动）：
  · 导航③ "样本小挑战"（原"大挑战"）
  · 导航⑦ "读懂AI心思"
  · 训练动画：root.after() → Clock.schedule_once()，逻辑完全一致
  · KNN算法、数据集、挑战集、8题小测验——与原版逐行对应

平板运行：python app_android.py
打包APK：buildozer android debug
"""

# ── Kivy 环境最先配置
from kivy.config import Config
Config.set('graphics', 'minimum_width',  '800')
Config.set('graphics', 'minimum_height', '600')
Config.set('kivy', 'keyboard_mode', 'systemanddock')

from kivy.app               import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout     import BoxLayout
from kivy.uix.gridlayout    import GridLayout
from kivy.uix.scrollview    import ScrollView
from kivy.uix.label         import Label
from kivy.uix.button        import Button
from kivy.uix.spinner        import Spinner
from kivy.uix.textinput     import TextInput
from kivy.uix.progressbar   import ProgressBar
from kivy.uix.popup         import Popup
from kivy.uix.widget        import Widget
from kivy.clock             import Clock
from kivy.metrics           import dp, sp
from kivy.utils             import platform
from kivy.core.window       import Window
from kivy.graphics          import Color, Rectangle, RoundedRectangle

import json, os, copy, random
from collections import Counter, defaultdict
from datetime    import datetime

# ────────────────────────────────────────────────
# 颜色（与 tkinter 版完全一致）
# ────────────────────────────────────────────────
def hx(h):
    h = h.lstrip('#')
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return r/255, g/255, b/255, 1

C_BG   = hx('FFF7E8')
C_HDR  = hx('FF8A3D')
C_NAV  = hx('FFE9C7')
C_OK   = hx('38B26D')
C_ERR  = hx('E74C3C')
C_WARN = hx('F39C12')
C_TEXT = hx('2C3E50')
C_SOFT = hx('6B4F3A')
C_HL   = hx('FFF3C4')
C_WHITE = (1,1,1,1)
C_INFO = hx('FFB74D')

def mk_hex(rgba):
    r,g,b,_ = rgba
    return '%02x%02x%02x' % (int(r*255),int(g*255),int(b*255))

MK_HDR  = mk_hex(C_HDR)
MK_OK   = mk_hex(C_OK)
MK_ERR  = mk_hex(C_ERR)
MK_SOFT = mk_hex(C_SOFT)
MK_VOTE = '5B2D8E'
MK_MEM  = '1F4E79'
MK_MATCH= '1A6B3A'
MK_DIFF = '999999'

# ────────────────────────────────────────────────
# 数据存储路径（Android私有目录）
# ────────────────────────────────────────────────
def _data_dir():
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            return app_storage_path()
        except Exception:
            pass
    return os.path.dirname(os.path.abspath(__file__))

def CUSTOM_DATA_FILE(): return os.path.join(_data_dir(), 'my_training_data.json')
def HISTORY_FILE():     return os.path.join(_data_dir(), 'my_train_history.json')

TEACHER_PIN = '0000'
TASK_NAME   = '校园垃圾分类'

# ════════════════════════════════════════════════
# 数据集（与 app_trainable.py 完全一致）
# ════════════════════════════════════════════════
DATASETS = {
    '校园垃圾分类': {
        'intro':      '训练一个会判断上海垃圾四分类的小模型。',
        'name_field': '物品名称',
        'features':   ['主要材料', '可回收', '含有害成分', '容易腐烂'],
        'label':      '类别',
        'labels':     ['可回收物', '厨余垃圾', '有害垃圾', '其他垃圾'],
        'name_suggestions': [
            '金属罐头盒','旧塑料盆','玻璃瓶','旧衬衫','快递纸箱','废杂志',
            '旧荧光灯','废墨盒','过期农药瓶','废杀虫剂',
            '香蕉皮','茶叶渣','花卉枯叶','玉米芯',
            '餐巾纸','旧棉手套','泡沫包装盒','一次性纸杯',
        ],
        'train_records': [
            {'物品名称':'废报纸',    '主要材料':'纸质',   '可回收':'是','含有害成分':'否','容易腐烂':'否','类别':'可回收物'},
            {'物品名称':'苹果核',    '主要材料':'食物残余','可回收':'否','含有害成分':'否','容易腐烂':'是','类别':'厨余垃圾'},
            {'物品名称':'剩饭菜',    '主要材料':'食物残余','可回收':'否','含有害成分':'否','容易腐烂':'是','类别':'厨余垃圾'},
            {'物品名称':'废旧电池',  '主要材料':'化学品', '可回收':'否','含有害成分':'是','容易腐烂':'否','类别':'有害垃圾'},
            {'物品名称':'用过的纸巾','主要材料':'纸质',   '可回收':'否','含有害成分':'否','容易腐烂':'否','类别':'其他垃圾'},
            {'物品名称':'破旧书包',  '主要材料':'纺织物', '可回收':'否','含有害成分':'否','容易腐烂':'否','类别':'其他垃圾'},
            {'物品名称':'旧雨伞',    '主要材料':'纺织物', '可回收':'否','含有害成分':'否','容易腐烂':'否','类别':'其他垃圾'},
            {'物品名称':'污损塑料袋','主要材料':'塑料',   '可回收':'否','含有害成分':'否','容易腐烂':'否','类别':'其他垃圾'},
        ],
        'challenge_records': [
            {'物品名称':'易拉罐',      '主要材料':'金属',   '可回收':'是','含有害成分':'否','容易腐烂':'否','类别':'可回收物'},
            {'物品名称':'矿泉水瓶',    '主要材料':'塑料',   '可回收':'是','含有害成分':'否','容易腐烂':'否','类别':'可回收物'},
            {'物品名称':'玻璃罐',      '主要材料':'玻璃',   '可回收':'是','含有害成分':'否','容易腐烂':'否','类别':'可回收物'},
            {'物品名称':'旧衣物',      '主要材料':'纺织物', '可回收':'是','含有害成分':'否','容易腐烂':'否','类别':'可回收物'},
            {'物品名称':'西瓜皮',      '主要材料':'食物残余','可回收':'否','含有害成分':'否','容易腐烂':'是','类别':'厨余垃圾'},
            {'物品名称':'鱼骨头',      '主要材料':'食物残余','可回收':'否','含有害成分':'否','容易腐烂':'是','类别':'厨余垃圾'},
            {'物品名称':'废荧光灯管',  '主要材料':'化学品', '可回收':'否','含有害成分':'是','容易腐烂':'否','类别':'有害垃圾'},
            {'物品名称':'废温度计',    '主要材料':'化学品', '可回收':'否','含有害成分':'是','容易腐烂':'否','类别':'有害垃圾'},
            {'物品名称':'过期药品',    '主要材料':'化学品', '可回收':'否','含有害成分':'是','容易腐烂':'否','类别':'有害垃圾'},
            {'物品名称':'湿纸巾',      '主要材料':'纸质',   '可回收':'否','含有害成分':'否','容易腐烂':'否','类别':'其他垃圾'},
            {'物品名称':'一次性塑料杯','主要材料':'塑料',   '可回收':'否','含有害成分':'否','容易腐烂':'否','类别':'其他垃圾'},
            {'物品名称':'废旧毛巾',    '主要材料':'纺织物', '可回收':'否','含有害成分':'否','容易腐烂':'否','类别':'其他垃圾'},
        ],
    }
}

# ════════════════════════════════════════════════
# KNN 算法（与 app_trainable.py 逐行对应）
# ════════════════════════════════════════════════
def feature_match_count(sample, record, features):
    return sum(1 for f in features
               if str(sample.get(f,'')).strip() == str(record.get(f,'')).strip())

def knn_predict(records, features, label, sample, k=3):
    if not records:
        return None, [], Counter()
    scored = [(feature_match_count(sample, r, features), r) for r in records]
    scored.sort(key=lambda x: x[0], reverse=True)
    near  = scored[:min(k, len(scored))]
    votes = Counter(r[label] for _, r in near)
    return votes.most_common(1)[0][0], near, votes

def explain_match(sample, record, features):
    same, diff = [], []
    for f in features:
        v1 = str(sample.get(f,'')).strip()
        v2 = str(record.get(f,'')).strip()
        if v1 == v2: same.append(f'{f}={v1}')
        else:        diff.append(f'{f}（{v1}↔{v2}）')
    return same, diff

# ════════════════════════════════════════════════
# 持久化
# ════════════════════════════════════════════════
def load_custom_data():
    p = CUSTOM_DATA_FILE()
    if not os.path.exists(p): return {TASK_NAME:[]}
    try:
        with open(p, encoding='utf-8') as f: d = json.load(f)
        return {TASK_NAME: d.get(TASK_NAME,[])}
    except: return {TASK_NAME:[]}

def save_custom_data(d):
    try:
        with open(CUSTOM_DATA_FILE(),'w',encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except: pass

def load_train_history():
    p = HISTORY_FILE()
    if not os.path.exists(p): return {TASK_NAME:[]}
    try:
        with open(p, encoding='utf-8') as f: d = json.load(f)
        return {TASK_NAME: d.get(TASK_NAME,[])}
    except: return {TASK_NAME:[]}

def save_train_history(d):
    try:
        with open(HISTORY_FILE(),'w',encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except: pass

# ════════════════════════════════════════════════
# 通用 UI 组件
# ════════════════════════════════════════════════
class BgBox(BoxLayout):
    def __init__(self, bg=C_WHITE, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*bg)
            self._r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._u, size=self._u)
    def _u(self,*a):
        self._r.pos=self.pos; self._r.size=self.size

def lbl(text, size=None, bold=False, color=C_TEXT, halign='left', markup=False):
    l = Label(text=text, font_name='Chinese', font_size=size or sp(16),
               bold=bold, color=color, halign=halign, markup=markup,
               size_hint_y=None)
    l.bind(width=lambda *a: setattr(l,'text_size',(l.width,None)))
    l.bind(texture_size=lambda *a: setattr(l,'height',l.texture_size[1]+dp(6)))
    return l

def btn(text, cb, bg=C_HDR, h=dp(52)):
    b = Button(text=text, font_name='Chinese', font_size=sp(16), bold=True,
               background_normal='', background_color=bg, color=C_WHITE,
               size_hint_y=None, height=h)
    b.bind(on_press=lambda x: cb())
    return b

def mk_spinner(values, default=''):
    s = Spinner(text=default or (values[0] if values else ''),
                values=values, font_name='Chinese', font_size=sp(15),
                size_hint_y=None, height=dp(46),
                background_normal='', background_color=C_NAV, color=C_TEXT)
    return s

def divider():
    w = Widget(size_hint_y=None, height=dp(1))
    with w.canvas:
        Color(0.85,0.85,0.85,1)
        Rectangle(pos=w.pos, size=w.size)
    w.bind(pos=lambda *a: _rdiv(w), size=lambda *a: _rdiv(w))
    return w

def _rdiv(w):
    w.canvas.clear()
    with w.canvas:
        Color(0.85,0.85,0.85,1)
        Rectangle(pos=w.pos, size=w.size)

def show_info(title, msg, on_close=None):
    box = BgBox(orientation='vertical', bg=C_WHITE, padding=dp(16), spacing=dp(12))
    box.add_widget(lbl(msg, size=sp(15)))
    ok = btn('确定', lambda: None, bg=C_HDR, h=dp(46))
    box.add_widget(ok)
    pop = Popup(title=title, content=box, size_hint=(0.85,None),
                height=dp(240), title_font='Chinese')
    ok.bind(on_press=lambda x: (pop.dismiss(), on_close() if on_close else None))
    pop.open()

def show_confirm(title, msg, on_yes, on_no=None):
    box = BgBox(orientation='vertical', bg=C_WHITE, padding=dp(16), spacing=dp(12))
    box.add_widget(lbl(msg, size=sp(15)))
    row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
    y = btn('确定', lambda: None, bg=C_ERR, h=dp(44))
    n = btn('取消', lambda: None, bg=hx('AAAAAA'), h=dp(44))
    row.add_widget(y); row.add_widget(n)
    box.add_widget(row)
    pop = Popup(title=title, content=box, size_hint=(0.85,None),
                height=dp(260), title_font='Chinese')
    y.bind(on_press=lambda x: (pop.dismiss(), on_yes()))
    n.bind(on_press=lambda x: (pop.dismiss(), on_no() if on_no else None))
    pop.open()

def ask_pin(title, on_ok):
    box = BgBox(orientation='vertical', bg=C_WHITE, padding=dp(16), spacing=dp(12))
    box.add_widget(lbl('请输入教师密码（PIN）：', size=sp(15)))
    ti = TextInput(hint_text='0000', password=True, font_name='Chinese',
                   font_size=sp(15), size_hint_y=None, height=dp(46), multiline=False)
    box.add_widget(ti)
    row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
    ok = btn('确定', lambda: None, h=dp(44))
    ca = btn('取消', lambda: None, bg=hx('AAAAAA'), h=dp(44))
    row.add_widget(ok); row.add_widget(ca)
    box.add_widget(row)
    pop = Popup(title=title, content=box, size_hint=(0.8,None),
                height=dp(280), title_font='Chinese')
    ok.bind(on_press=lambda x: (pop.dismiss(), on_ok(ti.text)))
    ca.bind(on_press=lambda x: pop.dismiss())
    pop.open()

def card_widget(title, body_text, bg=C_WHITE):
    box = BgBox(orientation='vertical', bg=bg, size_hint_y=None,
                padding=dp(12), spacing=dp(4))
    with box.canvas.before:
        Color(0.9,0.85,0.8,1)
        RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(6)])
    box.bind(pos=lambda *a: _rcard(box), size=lambda *a: _rcard(box))
    box.add_widget(lbl(title, bold=True, size=sp(15), color=C_TEXT))
    box.add_widget(lbl(body_text, size=sp(14), color=hx('34495E')))
    def _h(*a):
        h = dp(12)*2 + dp(4)
        for c in box.children: h += c.height
        box.height = h
    Clock.schedule_once(lambda dt: _h(), 0.05)
    return box

def _rcard(b):
    b.canvas.before.clear()
    with b.canvas.before:
        Color(0.9,0.85,0.8,1)
        RoundedRectangle(pos=b.pos, size=b.size, radius=[dp(6)])

# ════════════════════════════════════════════════
# 主布局
# ════════════════════════════════════════════════
class MainLayout(BgBox):
    def __init__(self, app_ref, **kw):
        super().__init__(orientation='vertical', bg=C_BG, **kw)
        self.app = app_ref
        self._build_header()
        self.sm = ScreenManager(transition=FadeTransition(duration=0.12))
        self.add_widget(self.sm)

    def _build_header(self):
        hdr = BgBox(orientation='horizontal', bg=C_HDR,
                    size_hint_y=None, height=dp(56), padding=[dp(10),dp(6)])
        # 导航菜单按钮
        mb = Button(text='☰', font_name='Chinese', font_size=sp(24),
                    size_hint=(None,1), width=dp(48),
                    background_normal='', background_color=C_HDR, color=C_WHITE)
        mb.bind(on_press=lambda x: self._nav_popup())
        hdr.add_widget(mb)
        # 标题（与 app_trainable.py 一致）
        hdr.add_widget(Label(text='🗑️ 训练我的第一个分类器',
                              font_name='Chinese', font_size=sp(18), bold=True,
                              color=C_WHITE, halign='left'))
        # 积分
        self.score_lbl = Label(text='⭐ 0', font_name='Chinese', font_size=sp(16),
                                size_hint=(None,1), width=dp(90),
                                color=hx('FFF6A3'), bold=True)
        hdr.add_widget(self.score_lbl)
        self.add_widget(hdr)

    def update_score(self, s):
        self.score_lbl.text = f'⭐ {s}'

    def _nav_popup(self):
        # 与 app_trainable.py 导航顺序完全一致
        nav_items = [
            ('🏠 首页',         'home'),
            ('① 打开样本盒',   'data'),
            ('② 发现小线索',   'clue'),
            ('③ 样本小挑战',   'challenge'),   # ← 已同步改名
            ('④ 给它贴标签',   'add'),
            ('⑤ 训练小模型',   'train'),
            ('⑥ 查看测试题',   'testlist'),
            ('⑦ 读懂AI心思',   'quiz'),        # ← 已同步改名
        ]
        box = BgBox(orientation='vertical', bg=C_NAV, padding=dp(6), spacing=dp(3))
        pop = Popup(title='📋 导航菜单', title_font='Chinese',
                    content=box, size_hint=(0.65, 0.88))
        for lbl_txt, key in nav_items:
            b = Button(text=lbl_txt, font_name='Chinese', font_size=sp(15),
                       size_hint_y=None, height=dp(52),
                       background_normal='', background_color=C_WHITE, color=C_TEXT)
            def _go(k=key, p=pop):
                p.dismiss(); self.app.goto(k)
            b.bind(on_press=lambda x, cb=_go: cb())
            box.add_widget(b)
        pop.open()

    def goto(self, name):
        self.sm.current = name

# ════════════════════════════════════════════════
# 页面基类
# ════════════════════════════════════════════════
class BaseScreen(Screen):
    def __init__(self, app_ref, **kw):
        super().__init__(**kw)
        self.app = app_ref
        self.outer = BgBox(orientation='vertical', bg=C_BG)
        self.add_widget(self.outer)
        self.sv = ScrollView(bar_width=dp(6))
        self.box = BgBox(orientation='vertical', bg=C_BG, size_hint_y=None,
                          spacing=dp(8), padding=[dp(14),dp(10),dp(14),dp(14)])
        self.box.bind(minimum_height=self.box.setter('height'))
        self.sv.add_widget(self.box)
        self.outer.add_widget(self.sv)

    def reset(self):
        self.box.clear_widgets()

    def h_title(self, text):
        self.box.add_widget(lbl(text, size=sp(20), bold=True, color=C_TEXT))
        self.box.add_widget(divider())

    def add_card(self, title, text, bg=C_WHITE):
        self.box.add_widget(card_widget(title, text, bg))

    def add_btn(self, text, cb, bg=C_HDR):
        self.box.add_widget(btn(text, cb, bg=bg))

    def add_btn_row(self, specs):
        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        for t, c, col in specs:
            row.add_widget(btn(t, c, bg=col))
        self.box.add_widget(row)

# ════════════════════════════════════════════════
# 🏠 首页
# ════════════════════════════════════════════════
class HomeScreen(BaseScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(app_ref, name='home', **kw)

    def on_enter(self): self._build()

    def _build(self):
        self.reset()
        app = self.app
        m = app.meta()
        hist = app.train_history.get(TASK_NAME, [])
        last = f'\n📊 上次准确率：{hist[-1]["acc"]:.0%}（{hist[-1].get("time","")}）' if hist else ''

        self.h_title('🗑️ 训练我的第一个分类器')
        self.add_card(
            f'今天的任务：{m["intro"]}',
            f'样本盒：默认 {len(m["train_records"])} 条 + 你加的 {app.custom_count()} 条 '
            f'= {len(app.train_records())} 条\n'
            f'挑战池：{len(app.challenge_records())} 道小模型没见过的新题\n\n'
            f'🎯 目标：初始约 42% 准确率，补充样本后逐步推到 100%，三个明显台阶。'
            + last, C_HL
        )
        self.add_card(
            '今天我们要做的事',
            '① 打开样本盒，看小模型要学的例子\n'
            '② 发现小线索，找出帮助分类的特征\n'
            '③ 样本小挑战，先考一考小模型\n'
            '④ 给它贴标签，补充数据帮它改进\n'
            '⑤ 训练小模型，看准确率如何提升\n'
            '⑥ 查看测试题，逐题看推理过程\n'
            '⑦ 读懂AI心思，完成小测验'
        )
        # 重置按钮靠右
        row = BoxLayout(size_hint_y=None, height=dp(52))
        row.add_widget(Widget())
        row.add_widget(btn('🔄 重置', app.reset_session,
                           bg=C_ERR, h=dp(44)))
        row.size_hint_x = None; row.width = dp(160)
        wrap = BoxLayout(size_hint_y=None, height=dp(52))
        wrap.add_widget(Widget())
        wrap.add_widget(btn('🔄 重置', app.reset_session, bg=C_ERR, h=dp(44)))
        # 简单实现：右对齐
        self.box.add_widget(wrap)

# ════════════════════════════════════════════════
# ① 打开样本盒
# ════════════════════════════════════════════════
class DataScreen(BaseScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(app_ref, name='data', **kw)

    def on_enter(self): self._build()

    def _build(self):
        self.reset()
        app = self.app; m = app.meta()
        self.h_title('① 打开样本盒：小模型要学习的例子')
        self.add_card(
            '样本盒里有什么？',
            '每一行是一个「样本」（一个例子）。\n'
            '样本里的特征（主要材料等）是「线索」；'
            '最后的「类别」是「正确答案牌（标签）」。\n'
            '★ = 你加入的样本'
        )
        feats = m['features']
        col_names = ['物品名称'] + feats + ['类别']
        # 表头
        hrow = GridLayout(cols=len(col_names), size_hint_y=None,
                           height=dp(40), spacing=1)
        for c in col_names:
            hrow.add_widget(_tcell(c, bg=C_HDR, tc=C_WHITE, bold=True))
        self.box.add_widget(hrow)
        for i, r in enumerate(app.train_records()):
            is_custom = i >= len(m['train_records'])
            bg = hx('E8F5EE') if is_custom else C_WHITE
            drow = GridLayout(cols=len(col_names), size_hint_y=None,
                               height=dp(38), spacing=1)
            nm = r.get(m['name_field'],'') + (' ★' if is_custom else '')
            drow.add_widget(_tcell(nm, bg=bg))
            for f in feats:
                drow.add_widget(_tcell(r.get(f,''), bg=bg))
            drow.add_widget(_tcell(r.get(m['label'],''), bg=bg))
            self.box.add_widget(drow)

def _tcell(text, bg=C_WHITE, tc=C_TEXT, bold=False):
    cell = BgBox(bg=bg, size_hint_y=None, height=dp(38), padding=[dp(3),dp(2)])
    cell.add_widget(Label(text=str(text), font_name='Chinese', font_size=sp(13),
                           bold=bold, color=tc, halign='center', valign='middle'))
    return cell

# ════════════════════════════════════════════════
# ② 发现小线索
# ════════════════════════════════════════════════
class ClueScreen(BaseScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(app_ref, name='clue', **kw)

    def on_enter(self): self._build()

    def _build(self):
        self.reset()
        app = self.app; m = app.meta()
        self.h_title('② 发现小线索：小模型靠什么来判断？')
        self.add_card(
            '什么是「小线索」？',
            '小线索就是帮助分类的特点。比如垃圾分类时，「主要材料」「是否可回收」'
            '「含有害成分」「容易腐烂」都是小线索。\n\n'
            '哪个线索最有区分力？看看不同类别的样本在该线索上的值是否明显不同。', C_HL
        )
        for f in m['features']:
            vals = {}
            for r in app.train_records():
                v = r.get(f,'?'); cat = r.get(m['label'],'?')
                vals.setdefault(v, Counter())[cat] += 1
            lines = [f'[b][color={MK_HDR}]线索：{f}[/color][/b]']
            for v, cc in sorted(vals.items()):
                detail = '  '.join(f'{cat}×{n}' for cat,n in cc.most_common())
                lines.append(f'  · {v}：{detail}')
            self.box.add_widget(lbl('\n'.join(lines), size=sp(14),
                                     markup=True, color=C_TEXT))
            self.box.add_widget(divider())
        self.add_btn_row([
            ('④ 去贴标签', lambda: app.goto('add'), C_HDR),
            ('⑤ 直接训练', lambda: app.goto('train'), C_OK),
        ])

# ════════════════════════════════════════════════
# ③ 样本小挑战（原"大挑战"，已同步改名）
# ════════════════════════════════════════════════
class ChallengeScreen(BaseScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(app_ref, name='challenge', **kw)
        self._order = []; self._idx = 0

    def on_enter(self): self._build()

    def _build(self):
        self.reset()
        app = self.app; m = app.meta()
        self.h_title('③ 样本小挑战：猜一猜它属于哪一类')
        self.add_card(
            '玩法',
            '👀 看下方的「神秘样本」线索，先你来猜\n'
            '🔵 再看小模型怎么判断\n'
            '✨ 这些题来自挑战池，小模型完全没见过，所以可能会答错', C_HL
        )
        self._order = list(app.challenge_records())
        random.shuffle(self._order)
        self._idx = 0
        self._sample_box = BgBox(orientation='vertical', bg=C_WHITE,
                                  size_hint_y=None, padding=dp(12), spacing=dp(6))
        self.box.add_widget(self._sample_box)
        self.box.add_widget(lbl('我认为它是：', size=sp(15), bold=True,
                                  color=C_TEXT, size_hint_y=None))
        self._choice = mk_spinner(m['labels'])
        self.box.add_widget(self._choice)
        self.add_btn_row([
            ('✅ 提交判断', self._check,  C_OK),
            ('🎲 换一题',   self._next,   C_INFO),
        ])
        self._result_lbl = lbl('', size=sp(14), markup=True)
        self.box.add_widget(self._result_lbl)
        self._render_sample()

    def _render_sample(self):
        self._sample_box.clear_widgets()
        if not self._order: return
        s = self._order[self._idx % len(self._order)]
        m = self.app.meta()
        self._sample_box.add_widget(
            lbl(f'🕵 神秘样本：{s.get(m["name_field"],"?")}',
                size=sp(18), bold=True, color=C_HDR))
        for f in m['features']:
            row = BoxLayout(size_hint_y=None, height=dp(34))
            row.add_widget(lbl(f'  🔍 {f}', size=sp(14), bold=True,
                                color=C_SOFT))
            row.add_widget(lbl(str(s.get(f,'')), size=sp(15), color=C_TEXT))
            self._sample_box.add_widget(row)
        self._sample_box.height = dp(12)*2 + dp(24) + dp(34)*len(m['features'])
        self._result_lbl.text = ''

    def _next(self):
        self._idx += 1; self._render_sample()

    def _check(self):
        if not self._order: return
        app = self.app; m = app.meta()
        s = self._order[self._idx % len(self._order)]
        true_label = s[m['label']]
        pred, near, votes = knn_predict(app.train_records(), m['features'], m['label'], s)
        my = self._choice.text
        lines = [
            f'[b]你的判断：{my}[/b]',
            f'[b]正确答案：{true_label}[/b]',
            f'[b][color={MK_OK if pred==true_label else MK_ERR}]小模型判断：{pred}[/color][/b]', '',
        ]
        if my == true_label:
            lines.append(f'[color={MK_OK}]✅ 你判断对了！+10分[/color]')
            app.score += 10; app.main_layout.update_score(app.score)
        if pred != true_label:
            lines.append(f'[color={MK_ERR}]❌ 小模型答错了——想想为什么？[/color]')
        lines += ['', '🔎 小模型参考的 3 个最近记忆：']
        for sc, r in near:
            rn = r.get(m['name_field'],'?'); rl = r[m['label']]
            same, diff = explain_match(s, r, m['features'])
            lines.append(f'  · {rn}（{rl}）  匹配{sc}/{len(m["features"])}个线索')
            if same: lines.append(f'[color={MK_MATCH}]    ✔ 相同：{"、".join(same)}[/color]')
            if diff: lines.append(f'[color={MK_DIFF}]    ✘ 不同：{"、".join(diff)}[/color]')
        vote_str = '  '.join(f'{k} {v}票' for k,v in votes.most_common())
        lines.append(f'\n[color={MK_VOTE}][b]投票：{vote_str} → 选了 {pred}[/b][/color]')
        if pred != true_label:
            lines.append(f'\n💡 到「④给它贴标签」补一条「{true_label}」的样本，再训练看看。')
        self._result_lbl.text = '\n'.join(lines)

# ════════════════════════════════════════════════
# ④ 给它贴标签
# ════════════════════════════════════════════════
class AddScreen(BaseScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(app_ref, name='add', **kw)
        self._entries = {}

    def on_enter(self): self._build()

    def build_with_prefill(self, feats=None, label=None, hint=''):
        self._build(feats, label, hint)

    def _build(self, prefill_feats=None, prefill_label=None, hint=''):
        self.reset(); self._entries = {}
        app = self.app; m = app.meta()
        self.h_title('④ 给它贴标签：教小模型认识新例子')
        if hint:
            self.add_card('💡 提示', hint, C_HL)
        self.add_card(
            '填写说明',
            '物品名称：点击下拉选择，或直接在输入框里输入新名称\n'
            '各线索：从下拉列表选择\n'
            '正确答案牌：选择该物品对应的垃圾类别'
        )
        existing = (
            {r.get(m['name_field'],'') for r in app.train_records()}
            | {r.get(m['name_field'],'') for r in app.challenge_records()}
        )
        sugg = [s for s in m.get('name_suggestions',[]) if s not in existing]
        # 名称输入
        self.box.add_widget(lbl('物品名称', size=sp(15), bold=True, color=C_TEXT))
        name_in = TextInput(hint_text='从下方下拉选，或直接输入',
                             font_name='Chinese', font_size=sp(15),
                             size_hint_y=None, height=dp(46), multiline=False)
        self.box.add_widget(name_in)
        name_sp = mk_spinner(sugg)
        name_sp.bind(text=lambda sp,v: setattr(name_in,'text',v))
        self.box.add_widget(name_sp)
        self._entries[m['name_field']] = name_in
        # 线索
        all_recs = m['train_records'] + app.user_records.get(TASK_NAME,[])
        for f in m['features']:
            self.box.add_widget(lbl(f'线索：{f}', size=sp(15), bold=True, color=C_TEXT))
            vals = sorted(set(str(r.get(f,'')) for r in all_recs if r.get(f)))
            sp_w = mk_spinner(vals)
            if prefill_feats and f in prefill_feats and prefill_feats[f] in vals:
                sp_w.text = prefill_feats[f]
            self.box.add_widget(sp_w)
            self._entries[f] = sp_w
        # 标签
        self.box.add_widget(lbl('正确答案牌（类别）', size=sp(15), bold=True, color=C_TEXT))
        lab_sp = mk_spinner(m['labels'])
        if prefill_label and prefill_label in m['labels']:
            lab_sp.text = prefill_label
        self.box.add_widget(lab_sp)
        self._entries[m['label']] = lab_sp
        self.add_btn_row([
            ('💾 加入样本盒', self._save,               C_OK),
            ('⑤ 去训练',     lambda: app.goto('train'), C_HDR),
        ])

    def _save(self):
        app = self.app; m = app.meta(); item = {}
        for k, w in self._entries.items():
            val = w.text.strip() if isinstance(w, TextInput) else w.text
            if not val:
                show_info('提示', f'「{k}」不能为空'); return
            item[k] = val
        app.user_records.setdefault(TASK_NAME,[]).append(item)
        save_custom_data(app.user_records)
        show_info('成功', f'已加入！现在可以去训练了。',
                  on_close=lambda: app.goto('train'))

# ════════════════════════════════════════════════
# ⑤ 训练小模型（训练动画完整对应 app_trainable.py）
# ════════════════════════════════════════════════
class TrainScreen(BaseScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(app_ref, name='train', **kw)
        # 训练状态
        self._prog_bar   = None
        self._prog_lbl   = None
        self._prog_total = 0
        self._prog_done  = 0
        self._output_lbl = None   # markup Label 显示训练过程
        self._lines      = []
        self._records    = []
        self._challenge  = []
        self._meta       = None
        self._exam_results  = []
        self._mem_idx    = 0
        self._exam_idx   = 0

    def on_enter(self): self._build()

    def _build(self):
        self.reset()
        app = self.app; m = app.meta()
        hist = app.train_history.get(TASK_NAME,[])
        last = f'\n📊 上次准确率：{hist[-1]["acc"]:.0%}（{hist[-1].get("time","")}）' if hist else ''
        self.h_title('⑤ 训练小模型：一步一步看它学习')
        self.add_card(
            '训练前看一看',
            f'样本盒：{len(app.train_records())} 条（默认 + 你加的 {app.custom_count()} 条）\n'
            f'挑战池：{len(app.challenge_records())} 道题（小模型完全没见过）\n'
            '小模型只能从样本盒里学规律，准确率是真实计算的。'
            + last, C_HL
        )
        self.add_btn('🌱 开始训练 + 自动考试', self._start, bg=C_OK)
        # 进度条（与 tkinter 版相同布局）
        prog_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        prog_row.add_widget(lbl('训练进度：', size=sp(14), bold=True))
        self._prog_bar = ProgressBar(max=100, value=0)
        prog_row.add_widget(self._prog_bar)
        self._prog_lbl = lbl('0%', size=sp(14))
        prog_row.add_widget(self._prog_lbl)
        self.box.add_widget(prog_row)
        # 训练输出文字（markup Label，对应 tkinter 的 tk.Text）
        self._lines = []
        self._output_lbl = lbl('', size=sp(13), markup=True)
        self.box.add_widget(self._output_lbl)

    # ── 对应 app_trainable.py start_training_animation ──
    def _start(self):
        app = self.app; m = app.meta()
        train = app.train_records(); challenge = app.challenge_records()
        if not train:
            show_info('提示', '样本盒是空的，请先添加例子。'); return
        if not challenge:
            show_info('提示', '挑战池是空的，无法考试。'); return
        self._records = train; self._challenge = challenge
        self._meta = m; self._exam_results = []
        self._lines = []; self._mem_idx = 0; self._exam_idx = 0
        self._prog_total = len(train) + len(challenge)
        self._prog_done  = 0
        self._prog_bar.max = self._prog_total
        self._prog_bar.value = 0
        self._prog_lbl.text = '0%'
        # 阶段1说明（与 tkinter 版文字完全一致）
        self._w(f'[b][color={MK_HDR}]【第一步：记忆阶段】[/color][/b]')
        self._w('[color=' + MK_SOFT + ']小模型不会思考，它只是把所有例子都「记」下来。')
        self._w(f'考试时，它会在这些记忆里找最像的 3 个，看看它们是哪一类，然后投票。[/color]')
        self._w(f'[color={MK_MEM}]📥 正在把 {len(train)} 条样本放进记忆库……[/color]')
        self._w('')
        # 对应 root.after(200, ...) → Clock.schedule_once
        Clock.schedule_once(lambda dt: self._mem_step(), 0.2)

    def _w(self, line):
        self._lines.append(line)
        self._output_lbl.text = '\n'.join(self._lines)

    def _upd_prog(self):
        self._prog_done += 1
        self._prog_bar.value = self._prog_done
        pct = int(self._prog_done / self._prog_total * 100) if self._prog_total else 0
        self._prog_lbl.text = f'{pct}%'

    # ── 对应 _anim_memorize_step ──
    def _mem_step(self):
        i = self._mem_idx
        if i >= len(self._records):
            self._w(f'[color={MK_OK}]✅ 全部 {len(self._records)} 条样本已记进记忆库！[/color]')
            self._w('')
            self._w(f'[b][color={MK_HDR}]【第二步：考试阶段】[/color][/b]')
            self._w('[color=' + MK_SOFT + ']用挑战池里 '
                    + str(len(self._challenge)) + ' 道题考一考它。')
            self._w('每道题：找最像的 3 个记忆→看哪个类别票多→给出答案。[/color]')
            self._w('')
            # 对应 root.after(400, ...)
            Clock.schedule_once(lambda dt: self._exam_step(), 0.4)
            return
        r = self._records[i]
        name = r.get(self._meta['name_field'], '?')
        cat  = r.get(self._meta['label'], '?')
        self._w(f'[color={MK_MEM}]   📦 记住第 {i+1} 条：{name}  →  类别：{cat}[/color]')
        self._upd_prog()
        self._mem_idx += 1
        # 对应 root.after(80, ...)
        Clock.schedule_once(lambda dt: self._mem_step(), 0.08)

    # ── 对应 _anim_exam_step ──
    def _exam_step(self):
        i = self._exam_idx
        if i >= len(self._challenge):
            self._finish(); return
        item = self._challenge[i]
        true_label = item[self._meta['label']]
        pred, near, votes = knn_predict(
            self._records, self._meta['features'], self._meta['label'], item)
        ok   = (pred == true_label)
        mark = '✅' if ok else '❌'
        name = item.get(self._meta['name_field'], '?')
        # 题目标题（与 tkinter 版一致）
        color = MK_OK if ok else MK_ERR
        self._w(f'\n[b][color={color}]{mark} 第 {i+1} 题：{name}[/color][/b]'
                f'[color={MK_SOFT}]  （正确答案：{true_label}）[/color]')
        self._w('   找到最像的 3 个记忆：')
        for rank, (score, r) in enumerate(near, 1):
            rn   = r.get(self._meta['name_field'], '?')
            rl   = r[self._meta['label']]
            same, diff = explain_match(item, r, self._meta['features'])
            self._w(f'     第{rank}个：{rn}（{rl}）  '
                    f'匹配 {score}/{len(self._meta["features"])} 个线索')
            if same:
                self._w(f'[color={MK_MATCH}]           ✔ 相同：{"、".join(same)}[/color]')
            if diff:
                self._w(f'[color={MK_DIFF}]           ✘ 不同：{"、".join(diff)}[/color]')
        vote_str = '  |  '.join(f'{cat} {cnt}票' for cat,cnt in votes.most_common())
        self._w(f'[color={MK_VOTE}][b]   📊 投票结果：{vote_str}[/b][/color]')
        if ok:
            self._w(f'[color={MK_OK}]   → 票数最多的是「{pred}」✅ 答对了！[/color]')
        else:
            self._w(f'[color={MK_ERR}]   → 票数最多的是「{pred}」❌ 答错了，'
                    f'正确答案是「{true_label}」[/color]')
        self._upd_prog()
        rec = item.copy()
        rec.update({'__pred':pred, '__ok':ok,
                    '__near':list(near), '__votes':dict(votes)})
        self._exam_results.append(rec)
        self._exam_idx += 1
        # 对应 root.after(500, ...)
        Clock.schedule_once(lambda dt: self._exam_step(), 0.5)

    # ── 对应 _finish_training ──
    def _finish(self):
        results = self._exam_results; m = self._meta
        train = self._records
        right = sum(1 for r in results if r['__ok'])
        wrong = len(results) - right; total = len(results)
        acc   = right / total if total else 0
        # 进度条跑满
        self._prog_bar.value = self._prog_total
        self._prog_lbl.text  = '100%'
        # 分类别统计（与 tkinter 版一致）
        cat_right = defaultdict(int); cat_total = defaultdict(int)
        for r in results:
            cat = r.get(m['label'], '?'); cat_total[cat] += 1
            if r['__ok']: cat_right[cat] += 1
        self._w(f'\n[color={MK_SOFT}]{"═"*40}[/color]')
        self._w(f'[b][color={MK_HDR}]🏁 考试结束！[/color][/b]')
        self._w(f'   一共 {total} 道题，答对 {right} 道，答错 {wrong} 道')
        self._w(f'[b][color={MK_VOTE}]   准确率：{acc:.0%}[/color][/b]')
        self._w('')
        self._w(f'[b][color={MK_HDR}]📂 各类别成绩：[/color][/b]')
        for cat in m['labels']:
            rc = cat_right[cat]; tc = cat_total[cat]
            if tc == 0: continue
            bar   = '█'*rc + '░'*(tc-rc)
            emoji = '✅' if rc==tc else ('🟡' if rc>0 else '❌')
            c     = MK_OK if rc==tc else (MK_SOFT if rc>0 else MK_ERR)
            self._w(f'[color={c}]   {emoji} {cat}  {bar}  {rc}/{tc}[/color]')
        # 记入历史
        hist = self.app.train_history.setdefault(TASK_NAME,[])
        prev_acc = hist[-1]['acc'] if hist else None
        hist.append({'time': datetime.now().strftime('%H:%M:%S'),
                     'train_n': len(train), 'custom_n': self.app.custom_count(),
                     'right': right, 'total': total, 'acc': acc})
        save_train_history(self.app.train_history)
        # 与上次对比
        if prev_acc is not None:
            diff = acc - prev_acc
            if diff > 0:
                self._w(f'[color={MK_OK}]📈 比上一次（{prev_acc:.0%}）提高了 {diff*100:.0f} 个百分点！加油！[/color]')
                self.app.score += 5; self.app.main_layout.update_score(self.app.score)
            elif diff < 0:
                self._w(f'[color={MK_ERR}]📉 比上一次（{prev_acc:.0%}）下降了 {abs(diff)*100:.0f} 个百分点。\n'
                        f'   想一想：是不是新加的例子标签填错了？[/color]')
            else:
                self._w(f'[color={MK_SOFT}]➖ 和上一次一样（{prev_acc:.0%}）。[/color]')
        else:
            self.app.score += 5; self.app.main_layout.update_score(self.app.score)
        # 保存 last_test_results
        self.app.last_test_results = []
        for r in results:
            row = {k:v for k,v in r.items() if not k.startswith('__')}
            row.update({'题号': f'第{results.index(r)+1}题',
                        '正确答案': r[m['label']], '小模型答案': r['__pred'],
                        '答题结果': '答对 ✅' if r['__ok'] else '答错 ❌',
                        '__near': r['__near']})
            self.app.last_test_results.append(row)
        self.app.last_train_summary = {
            'task': TASK_NAME, 'train_n': len(train),
            'custom_n': self.app.custom_count(), 'total': total,
            'right': right, 'wrong': wrong, 'acc': acc,
            'features': m['features'], 'label': m['label'],
            'name_field': m['name_field'],
        }
        # 错题一键补救
        wrong_items = [r for r in self.app.last_test_results
                       if str(r.get('答题结果','')).startswith('答错')]
        if wrong_items:
            ex = wrong_items[0]; cl = ex.get('正确答案','?')
            nm = ex.get(m['name_field'],'?')
            pf = {f: ex.get(f,'') for f in m['features']}
            self._w(f'\n[b][color={MK_ERR}]🤔 「{nm}」答错了——'
                    f'补一条「{cl}」的样本帮它改正[/color][/b]')
            def _fix(pf_=pf, lab_=cl, nm_=nm):
                add = self.app.main_layout.sm.get_screen('add')
                add.build_with_prefill(pf_, lab_,
                    hint=f'小模型答错了「{nm_}」，加一条「{lab_}」的样本帮它改正')
                self.app.goto('add')
            self.box.add_widget(btn(f'🛠 一键补救：加「{cl}」', _fix, bg=C_OK))
        else:
            self._w(f'[color={MK_OK}]🎉 全部答对了！[/color]')
        self.add_btn_row([
            ('⑥ 查看每道题', lambda: self.app.goto('testlist'), C_HDR),
            ('③ 样本小挑战', lambda: self.app.goto('challenge'), C_OK),
        ])

# ════════════════════════════════════════════════
# ⑥ 查看测试题
# ════════════════════════════════════════════════
class TestListScreen(BaseScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(app_ref, name='testlist', **kw)

    def on_enter(self): self._build()

    def _build(self):
        self.reset()
        app = self.app; m = app.meta()
        self.h_title('⑥ 查看测试题：小模型每题答得怎么样？')
        if not getattr(app, 'last_test_results', None):
            self.add_card('还没有测试结果',
                          '请先到「⑤ 训练小模型」点击「开始训练 + 自动考试」。')
            self.add_btn('去训练 →', lambda: app.goto('train'), C_OK)
            return
        s = app.last_train_summary or {}
        self.add_card('总体结果',
            f'共 {s.get("total",0)} 道  答对 {s.get("right",0)} 道  '
            f'答错 {s.get("wrong",0)} 道  准确率 {s.get("acc",0):.0%}')
        feats = s.get('features', m['features'])
        nf    = s.get('name_field', m['name_field'])
        for i, row in enumerate(app.last_test_results, 1):
            ok = str(row.get('答题结果','')).startswith('答对')
            name = row.get(nf,'?')
            clue_str = '  |  '.join(f'{f}={row.get(f,"")}' for f in feats)
            lines = [
                f'[b][color={MK_OK if ok else MK_ERR}]'
                f'{"✅" if ok else "❌"} 第{i}题：{name}[/color][/b]',
                f'正确答案：{row.get("正确答案","")}',
                f'小模型答：{row.get("小模型答案","")}',
                f'题目线索：{clue_str}',
                '', '参考的 3 个最近记忆：',
            ]
            for sc, r in row.get('__near', []):
                rn = r.get(nf,'?'); rl = r.get(m['label'],'?')
                same, diff = explain_match(row, r, feats)
                lines.append(f'  · {rn}（{rl}）  匹配{sc}/{len(feats)}线索')
                if same: lines.append(f'[color={MK_MATCH}]    ✔ 相同：{"、".join(same)}[/color]')
                if diff: lines.append(f'[color={MK_DIFF}]    ✘ 不同：{"、".join(diff)}[/color]')
            bg = hx('E8F5EE') if ok else hx('FDE8E8')
            item_box = BgBox(orientation='vertical', bg=bg,
                              size_hint_y=None, padding=dp(10), spacing=dp(3))
            item_box.bind(minimum_height=item_box.setter('height'))
            item_box.add_widget(lbl('\n'.join(lines), size=sp(13), markup=True))
            self.box.add_widget(item_box)
            self.box.add_widget(divider())
        self.add_btn_row([
            ('回到训练',     lambda: app.goto('train'),     C_HDR),
            ('③ 样本小挑战', lambda: app.goto('challenge'), C_OK),
        ])

# ════════════════════════════════════════════════
# ⑦ 读懂AI心思（8题小测验，与原版完全一致）
# ════════════════════════════════════════════════
QUIZ = [
    {'q':'1. 小模型为什么要先看很多例子？',
     'opts':['A. 从大量例子里找出分类规律',
             'B. 例子越多，做题速度就越快',
             'C. 必须把所有例子背下来才能用'],
     'ans':0,
     'exp':'小模型需要先看例子，从中找规律。例子越多越准，它学到的判断方法就越好。'},
    {'q':'2. 在垃圾分类里，「是否有害」属于什么？',
     'opts':['A. 正确答案牌（标签）','B. 判断线索（特征）','C. 训练得分'],
     'ans':1,
     'exp':'「是否有害」帮助小模型判断类别，所以它是「线索（特征）」。「类别」才是答案牌。'},
    {'q':'3. 「可回收物」「厨余垃圾」这些是什么？',
     'opts':['A. 判断线索','B. 神秘样本','C. 正确答案牌（标签）'],
     'ans':2,
     'exp':'这些是提前贴好的「答案牌」，告诉小模型「这条样本属于哪一类」，也叫「标签」。'},
    {'q':'4. 如果给小模型加了一条「错误」的例子（标签贴错），可能会怎样？',
     'opts':['A. 可能影响它后面的判断',
             'B. 它一定会变得更准',
             'C. 它会自动发现错误并删掉'],
     'ans':0,
     'exp':'错误的例子会让小模型学到错误的规律。这正是「数据决定模型」的意思。'},
    {'q':'5. 用「找最像的3个例子再投票」的方法判断，哪种情况最容易答错？',
     'opts':['A. 样本盒里有上百条例子',
             'B. 样本盒里某一类只有1-2条例子',
             'C. 新样本和某条已有例子完全相同'],
     'ans':1,
     'exp':'某一类例子太少，新样本很容易被其他类「淹没」。解决办法：给少的那类多加几条。'},
    {'q':'6. 测试准确率50%表示什么？',
     'opts':['A. 小模型已经完全学会了',
             'B. 测试题里大约一半答对一半答错',
             'C. 小模型没做题'],
     'ans':1,
     'exp':'准确率 = 答对题数 ÷ 总题数。50%说明小模型还不够准，需要继续改进数据。'},
    {'q':'7. 小模型答错了，最应该做的是什么？',
     'opts':['A. 关掉程序，小模型没用',
             'B. 补充更准确的同类样本，再重新训练',
             'C. 永远相信小模型的判断'],
     'ans':1,
     'exp':'小模型的结果需要人来检查。补充准确的例子，帮助它改进，这是「以人为主、数据驱动」的理念。'},
    {'q':'8. 小模型是一种魔法吗？',
     'opts':['A. 是的，它无所不知',
             'B. 不是，它是根据数据和线索学习的',
             'C. 是的，不需要任何例子就能判断'],
     'ans':1,
     'exp':'理解小模型如何学习、如何判断，以及为什么需要人来检查和改进——这是这节课的核心。'},
]

class QuizScreen(BaseScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(app_ref, name='quiz', **kw)
        self._idx = 0; self._answers = []; self._q_btns = []
        self._res_lbl = None

    def on_enter(self):
        self._idx = 0; self._answers = []; self._build()

    def _build(self):
        self.reset()
        self.h_title('⑦ 读懂AI心思：分类小测验')
        self.add_card('说明',
            '共8题，每题选好后立刻看到对错和解释。', C_HL)
        self._show_q()

    def _show_q(self):
        # 清除之前的题目相关控件（保留标题和说明卡）
        to_remove = []
        for w in self.box.children[:]:
            # 保留前2个（标题+说明卡）
            pass
        # 简单重置题目区域
        children = list(self.box.children)
        keep = children[-2:] if len(children) >= 2 else children
        self.box.clear_widgets()
        for w in reversed(keep):
            self.box.add_widget(w)

        if self._idx >= len(QUIZ):
            self._final(); return
        q = QUIZ[self._idx]
        self.box.add_widget(
            lbl(f'[b]{q["q"]}[/b]', size=sp(16), markup=True))
        self._q_btns = []
        for i, opt in enumerate(q['opts']):
            b = Button(text=opt, font_name='Chinese', font_size=sp(15),
                       size_hint_y=None, height=dp(58),
                       background_normal='', background_color=C_NAV, color=C_TEXT,
                       halign='left')
            b.bind(on_press=lambda x, idx=i: self._select(idx))
            self.box.add_widget(b); self._q_btns.append(b)
        self._res_lbl = lbl('', size=sp(14), markup=True)
        self.box.add_widget(self._res_lbl)

    def _select(self, choice):
        q = QUIZ[self._idx]; ok = (choice == q['ans'])
        self._answers.append(ok)
        for i, b in enumerate(self._q_btns):
            if i == q['ans']: b.background_color = C_OK; b.color = C_WHITE
            elif i == choice and not ok: b.background_color = C_ERR; b.color = C_WHITE
            b.disabled = True
        self._res_lbl.text = (
            f'[b][color={MK_OK if ok else MK_ERR}]'
            f'{"✅ 答对了！" if ok else "❌ 答错了。"}[/color][/b]\n'
            f'[color=888888]{q["exp"]}[/color]'
        )
        if ok:
            self.app.score += 5
            self.app.main_layout.update_score(self.app.score)
        Clock.schedule_once(lambda dt: self._next_q(), 1.5)

    def _next_q(self):
        self._idx += 1; self._show_q()

    def _final(self):
        correct = sum(self._answers); total = len(QUIZ)
        acc = correct / total
        if acc >= 0.875:
            comment = '🌟 全部理解！你真正读懂了小模型的判断方式。'
        elif acc >= 0.625:
            comment = '👍 基本理解，再看看错题解释会更稳。'
        else:
            comment = '💪 还需复习，重点看每道题的解释。'
        self.add_card('测验完成！',
                       f'答对 {correct}/{total}  准确率 {acc:.0%}\n\n{comment}')
        self.add_btn('🔁 再做一遍', self.on_enter, bg=C_HDR)
        self.add_btn('🏠 回首页', lambda: self.app.goto('home'), bg=C_OK)

# ════════════════════════════════════════════════
# 主 App
# ════════════════════════════════════════════════
class GarbageApp(App):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.score = 0
        self.user_records       = load_custom_data()
        self.train_history      = load_train_history()
        self.last_test_results  = []
        self.last_train_summary = None
        self.main_layout        = None

    def build(self):
        self._reg_font()
        Window.clearcolor = C_BG
        self.main_layout = MainLayout(self)
        sm = self.main_layout.sm
        for cls, name in [
            (HomeScreen,      'home'),
            (DataScreen,      'data'),
            (ClueScreen,      'clue'),
            (ChallengeScreen, 'challenge'),
            (AddScreen,       'add'),
            (TrainScreen,     'train'),
            (TestListScreen,  'testlist'),
            (QuizScreen,      'quiz'),
        ]:
            sm.add_widget(cls(self, name=name))
        sm.current = 'home'
        Window.bind(on_keyboard=self._kbd)
        return self.main_layout

    def _reg_font(self):
        from kivy.core.text import LabelBase
        here = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(here, 'NotoSansCJKsc-Regular.otf'),
            os.path.join(here, 'NotoSansCJK-Regular.ttc'),
            '/system/fonts/NotoSansCJK-Regular.ttc',
            '/system/fonts/DroidSansFallback.ttf',
        ]
        for p in candidates:
            if os.path.exists(p):
                LabelBase.register('Chinese', p); return
        LabelBase.register('Chinese', 'Roboto')

    def _kbd(self, window, key, *a):
        if key == 27:
            if self.main_layout.sm.current != 'home':
                self.main_layout.sm.current = 'home'; return True
        return False

    def meta(self):         return DATASETS[TASK_NAME]
    def train_records(self): return self.meta()['train_records'] + self.user_records.get(TASK_NAME,[])
    def challenge_records(self): return self.meta()['challenge_records']
    def custom_count(self):  return len(self.user_records.get(TASK_NAME,[]))
    def goto(self, name):    self.main_layout.goto(name)

    def reset_session(self):
        def _do():
            self.user_records       = {TASK_NAME:[]}
            self.train_history      = {TASK_NAME:[]}
            self.score              = 0
            self.last_test_results  = []
            self.last_train_summary = None
            save_custom_data(self.user_records)
            save_train_history(self.train_history)
            self.main_layout.update_score(0)
            self.goto('home')
            show_info('已重置', '样本盒已恢复默认，积分清零。')
        show_confirm('重置确认',
                     '确定要重置吗？已加的样本和积分会清空。',
                     on_yes=_do)

if __name__ == '__main__':
    GarbageApp().run()
