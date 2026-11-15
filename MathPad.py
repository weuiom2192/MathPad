#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MathPad · 简约数学题目编辑器
依赖：pip install PyQt5 PyQtWebEngine
运行：python mathpad.py
声明：本软件由AI制作，仅供便利和娱乐功能
"""

import sys
import os
import tempfile
import math
import json
import base64
import traceback
import re

# 解决 WebEngine 各种权限和缓存报错
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = f"--disable-gpu --disable-software-rasterizer --disk-cache-dir={tempfile.gettempdir()}/mathpad_cache"

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QSplitter, QGraphicsView, QGraphicsScene,
        QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsPolygonItem, QGraphicsPixmapItem,
        QTextEdit, QFontComboBox, QSpinBox, QToolButton, QGridLayout, QVBoxLayout,
        QHBoxLayout, QFileDialog, QMessageBox, QAction, QActionGroup, QToolBar, QFrame,
        QLabel, QTabWidget, QTabBar, QColorDialog, QComboBox, QInputDialog, QGraphicsTextItem,
        QMenu, QSizePolicy, QStackedWidget, QPushButton, QDialog
    )
    from PyQt5.QtGui import (
        QPainter, QPen, QBrush, QColor, QPixmap, QImage, QFont, QPolygonF,
        QTextCharFormat, QKeySequence, QTextDocument, QIcon, QPainterPath, QCursor,
        QTextCursor
    )
    from PyQt5.QtCore import (
        Qt, QRectF, QLineF, QPointF, QPoint, QSize, pyqtSignal, QTimer, 
        QBuffer, QIODevice, QByteArray, QEventLoop
    )
except ImportError as e:
    print("=" * 60)
    print(" 缺少 PyQt5，请先安装：")
    print("     pip install PyQt5")
    print("=" * 60)
    input("按回车键退出...")
    sys.exit(1)

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
except ImportError:
    print("=" * 60)
    print(" 缺少 PyQtWebEngine，请先在命令行运行：")
    print("     pip install PyQtWebEngine")
    print("=" * 60)
    input("按回车键退出...")
    sys.exit(1)


# ---------------------------------------------------------------- 常用数学符号
SYMBOLS = [
    "α", "β", "γ", "δ", "ε", "θ", "λ", "μ", "π", "ρ", "σ", "φ", "ω", "Ω",
    "∑", "∏", "∫", "√", "∞", "∂", "∇", "±", "×", "÷", "·", "≠", "≈", "≡",
    "≤", "≥", "∝", "∈", "∉", "⊂", "⊃", "∪", "∩", "∅", "→", "←", "↔", "⇒", "⇔",
    "∀", "∃", "∴", "∵", "∠", "⊥", "∥", "△", "□", "⊙", "°", "′", "″",
    "²", "³", "½", "ℝ", "ℕ", "ℤ", "ℚ",
]

SHAPE_COLOR = QColor("#d32f2f")
DEFAULT_PROJECT_EXT = ".mpad"

# ---------------------------------------------------------------- 全局样式模板
STYLE_TEMPLATE = """
QMainWindow, QWidget {{ background:#f3f3f3;
    font-family:"Microsoft YaHei","Segoe UI",sans-serif; font-size:{fs}; color: #333; }}
QMenuBar {{ background:#f3f3f3; border-bottom:1px solid #dcdcdc; }}
QMenuBar::item {{ padding:4px 10px; background:transparent; }}
QMenuBar::item:selected {{ background:#e2e2e2; }}
QMenu {{ background:#ffffff; border:1px solid #dcdcdc; }}
QMenu::item:selected {{ background:#cfe4ff; }}
QToolBar {{ background:#f3f3f3; border-bottom:1px solid #dcdcdc; spacing:2px; padding:2px; }}
QToolButton {{ border:none; padding:4px 8px; border-radius:3px; background:transparent; }}
QToolButton:hover {{ background:#e2e2e2; }}
QToolButton:checked {{ background:#cfe4ff; }}
QSplitter::handle {{ background:#dcdcdc; }}
QSplitter::handle:hover {{ background:#a9a9a9; }}
QStatusBar {{ background:#f3f3f3; border-top:1px solid #dcdcdc; color: #555; }}
QSpinBox, QFontComboBox, QComboBox {{ background:#ffffff; border:1px solid #d0d0d0; border-radius:3px; padding:2px 4px; }}
QLabel {{ color:#555; }}
QTabWidget::pane {{ border: 1px solid #dcdcdc; background: #ffffff; }}
QTabBar::tab {{ background: #e8e8e8; padding: 6px 16px; border: 1px solid #dcdcdc; border-bottom: none; border-top-left-radius: 3px; border-top-right-radius: 3px; margin-right: 2px; }}
QTabBar::tab:selected {{ background: #ffffff; border-bottom: 1px solid #ffffff; }}
QTabBar::tab:hover {{ background: #f0f0f0; }}
QPushButton {{ background: #f3f3f3; border: 1px solid #dcdcdc; border-radius: 4px; padding: 8px 16px; color: #333; }}
QPushButton:hover {{ background: #e8e8e8; }}
"""

def make_icon(kind, size=20):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor("#3c3c3c"))
    pen.setWidthF(1.5)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    dark = QColor("#3c3c3c")

    if kind == "select":
        path = QPainterPath()
        path.moveTo(5, 3)
        path.lineTo(5, 16)
        path.lineTo(8.5, 12.5)
        path.lineTo(11, 17)
        path.lineTo(13, 16)
        path.lineTo(10.5, 11.5)
        path.lineTo(15, 11.5)
        path.closeSubpath()
        p.setBrush(QBrush(dark))
        p.drawPath(path)
    elif kind == "line":
        p.drawLine(QPointF(4, 16), QPointF(16, 4))
        p.setBrush(QBrush(dark))
        p.drawEllipse(QPointF(4, 16), 1.6, 1.6)
        p.drawEllipse(QPointF(16, 4), 1.6, 1.6)
    elif kind == "polygon":
        path = QPainterPath()
        path.moveTo(10, 3.5)
        path.lineTo(17, 15.5)
        path.lineTo(3, 15.5)
        path.closeSubpath()
        p.setBrush(QBrush(QColor(60, 60, 60, 50)))
        p.drawPath(path)
    elif kind == "circle":
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(3.5, 3.5, 13, 13))
        p.setBrush(QBrush(dark))
        p.drawEllipse(QPointF(10, 10), 1.3, 1.3)
    elif kind == "text":
        font = QFont("Times New Roman", 14)
        font.setBold(True)
        p.setFont(font)
        p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, "T")
    elif kind == "pan":
        p.drawLine(QPointF(10, 4), QPointF(10, 16))
        p.drawLine(QPointF(4, 10), QPointF(16, 10))
        for (x1, y1), (x2, y2) in [
            ((10, 4), (7.5, 6.5)), ((10, 4), (12.5, 6.5)),
            ((10, 16), (7.5, 13.5)), ((10, 16), (12.5, 13.5)),
            ((4, 10), (6.5, 7.5)), ((4, 10), (6.5, 12.5)),
            ((16, 10), (13.5, 7.5)), ((16, 10), (13.5, 12.5)),
        ]:
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    p.end()
    return QIcon(pix)

def _vdist(a, b):
    return math.hypot(a.x() - b.x(), a.y() - b.y())

def seg_seg_intersect(p1, p2, p3, p4):
    x1, y1 = p1.x(), p1.y()
    x2, y2 = p2.x(), p2.y()
    x3, y3 = p3.x(), p3.y()
    x4, y4 = p4.x(), p4.y()
    d = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    if abs(d) < 1e-12: return []
    t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / d
    u = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / d
    if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
        return [QPointF(x1 + t * (x2 - x1), y1 + t * (y2 - y1))]
    return []

def seg_circle_intersect(a, b, c, r):
    dx, dy = b.x() - a.x(), b.y() - a.y()
    fx, fy = a.x() - c.x(), a.y() - c.y()
    A = dx * dx + dy * dy
    if A < 1e-12: return []
    B = 2 * (fx * dx + fy * dy)
    C = fx * fx + fy * fy - r * r
    disc = B * B - 4 * A * C
    if disc < 0: return []
    s = math.sqrt(disc)
    out = []
    for t in ((-B - s) / (2 * A), (-B + s) / (2 * A)):
        if -1e-9 <= t <= 1 + 1e-9:
            out.append(QPointF(a.x() + t * dx, a.y() + t * dy))
    return out

def circle_circle_intersect(c1, r1, c2, r2):
    dx, dy = c2.x() - c1.x(), c2.y() - c1.y()
    d = math.hypot(dx, dy)
    if d < 1e-12 or d > r1 + r2 + 1e-9 or d < abs(r1 - r2) - 1e-9: return []
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h2 = r1 * r1 - a * a
    if h2 < 0: return []
    h = math.sqrt(h2)
    mx = c1.x() + a * dx / d
    my = c1.y() + a * dy / d
    rx, ry = -dy / d * h, dx / d * h
    if h < 1e-9: return [QPointF(mx, my)]
    return [QPointF(mx + rx, my + ry), QPointF(mx - rx, my - ry)]

def closest_on_seg(p, a, b):
    dx, dy = b.x() - a.x(), b.y() - a.y()
    ll = dx * dx + dy * dy
    if ll < 1e-12: return QPointF(a)
    t = ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / ll
    t = max(0.0, min(1.0, t))
    return QPointF(a.x() + t * dx, a.y() + t * dy)

def closest_on_circle(p, c, r):
    dx, dy = p.x() - c.x(), p.y() - c.y()
    d = math.hypot(dx, dy)
    if d < 1e-12: return QPointF(c.x() + r, c.y())
    return QPointF(c.x() + dx / d * r, c.y() + dy / d * r)

class GeoShape:
    def __init__(self, item, kind):
        self.item = item
        self.kind = kind
        self.key_points = []
        self.segments = []
        self.circles = []

    def move_by(self, dx, dy):
        if abs(dx) < 0.001 and abs(dy) < 0.001: return
        if self.kind == "line":
            line = self.item.line()
            line.setLine(line.x1() + dx, line.y1() + dy, line.x2() + dx, line.y2() + dy)
            self.item.setLine(line)
        elif self.kind == "circle":
            rect = self.item.rect()
            rect.translate(dx, dy)
            self.item.setRect(rect)
        elif self.kind == "polygon":
            poly = QPolygonF([QPointF(p.x() + dx, p.y() + dy) for p in self.item.polygon()])
            self.item.setPolygon(poly)
        elif self.kind == "text":
            self.item.setPos(self.item.pos() + QPointF(dx, dy))
        
        self.key_points = [QPointF(p.x() + dx, p.y() + dy) for p in self.key_points]
        self.segments = [(QPointF(a.x() + dx, a.y() + dy), QPointF(b.x() + dx, b.y() + dy)) for a, b in self.segments]
        self.circles = [(QPointF(c.x() + dx, c.y() + dy), r) for c, r in self.circles]

class MathCanvas(QGraphicsView):
    toolChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setBackgroundBrush(QBrush(QColor("#eceef1")))
        self.setFrameShape(QFrame.NoFrame)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._scene.setSceneRect(QRectF(-2000, -2000, 4000, 4000))

        self.tool = "select"
        self.image_item = None
        self._shapes = []
        self._redo = []
        self._pending_pts = []

        self._drag_shape = None
        self._last_drag_pos = None

        self._poly_fixed_items = []
        self._dynamic_line_a = None
        self._dynamic_line_b = None
        self._dynamic_circle = None

        self._snap_marker = None
        self._snap_target = None
        self._snap_kind = None
        self._panning = False
        self._pan_start = None

        self.pen = QPen(SHAPE_COLOR)
        self.pen.setWidth(2)
        self.pen.setCosmetic(True)
        self.pen.setCapStyle(Qt.RoundCap)
        self.pen.setJoinStyle(Qt.RoundJoin)

        self._update_cursor()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        widget = self
        while widget:
            if hasattr(widget, 'main_window'):
                widget.main_window.active_canvas = self
                widget.main_window.sync_toolbar()
                break
            widget = widget.parent()

    def set_tool(self, name):
        self._cancel_drawing()
        self.tool = name
        self._update_cursor()
        self.toolChanged.emit(name)

    def _update_cursor(self):
        if self.tool in ("line", "polygon", "circle"):
            self.viewport().setCursor(Qt.CrossCursor)
        elif self.tool == "pan":
            self.viewport().setCursor(Qt.OpenHandCursor)
        elif self.tool == "text":
            self.viewport().setCursor(Qt.IBeamCursor)
        else:
            self.viewport().setCursor(Qt.ArrowCursor)

    def _snap_threshold(self):
        return 12.0 / max(self.transform().m11(), 1e-9)

    def _collect_point_candidates(self):
        pts = []
        for s in self._shapes: pts.extend(s.key_points)
        pts.extend(self._pending_pts)
        for i, s1 in enumerate(self._shapes):
            for s2 in self._shapes[i + 1:]:
                pts.extend(self._intersections(s1, s2))
        return pts

    def _intersections(self, s1, s2):
        out = []
        for a1, b1 in s1.segments:
            for a2, b2 in s2.segments: out.extend(seg_seg_intersect(a1, b1, a2, b2))
        for a, b in s1.segments:
            for c, r in s2.circles: out.extend(seg_circle_intersect(a, b, c, r))
        for c, r in s1.circles:
            for a, b in s2.segments: out.extend(seg_circle_intersect(a, b, c, r))
        for c1, r1 in s1.circles:
            for c2, r2 in s2.circles: out.extend(circle_circle_intersect(c1, r1, c2, r2))
        return out

    def _snap(self, pos):
        thr = self._snap_threshold()
        best_p = None
        best_d = thr
        for p in self._collect_point_candidates():
            d = _vdist(pos, p)
            if d < best_d:
                best_d = d
                best_p = p
        if best_p is not None:
            self._snap_target = best_p
            self._snap_kind = "point"
            return QPointF(best_p)

        best_d = thr
        self._snap_kind = None
        for s in self._shapes:
            for a, b in s.segments:
                cp = closest_on_seg(pos, a, b)
                d = _vdist(pos, cp)
                if d < best_d:
                    best_d = d
                    best_p = cp
                    self._snap_kind = "segment"
            for c, r in s.circles:
                cp = closest_on_circle(pos, c, r)
                d = _vdist(pos, cp)
                if d < best_d:
                    best_d = d
                    best_p = cp
                    self._snap_kind = "circle"
        self._snap_target = best_p
        return best_p if best_p is not None else QPointF(pos)

    def _update_snap_marker(self):
        if self._snap_target is None:
            if self._snap_marker is not None: self._snap_marker.hide()
            return
        r = 5.0 / max(self.transform().m11(), 1e-9)
        p = self._snap_target
        if self._snap_marker is None:
            item = QGraphicsEllipseItem()
            pen = QPen(QColor("#1976d2"), 1.4)
            pen.setCosmetic(True)
            item.setPen(pen)
            item.setBrush(QBrush(QColor(25, 118, 210, 110)))
            item.setZValue(1000)
            self._scene.addItem(item)
            self._snap_marker = item
        self._snap_marker.setRect(QRectF(p.x() - r, p.y() - r, 2 * r, 2 * r))
        self._snap_marker.show()

    def _find_tangent_snap(self, p1, scene_pos):
        best_t = None
        best_dist = self._snap_threshold() * 2.0
        best_target = None
        for s in self._shapes:
            for c, r in s.circles:
                d = _vdist(p1, c)
                if d < r - 1e-5: continue
                if abs(d - r) <= 1e-5:
                    vx, vy = p1.x() - c.x(), p1.y() - c.y()
                    vlen = math.hypot(vx, vy)
                    if vlen > 1e-9:
                        tx, ty = -vy / vlen, vx / vlen
                        u = (scene_pos.x() - p1.x()) * tx + (scene_pos.y() - p1.y()) * ty
                        if u > 0:
                            proj_pt = QPointF(p1.x() + u * tx, p1.y() + u * ty)
                            if _vdist(scene_pos, proj_pt) < self._snap_threshold():
                                if _vdist(scene_pos, proj_pt) < best_dist:
                                    best_dist = _vdist(scene_pos, proj_pt)
                                    best_t, best_target = p1, proj_pt
                    continue
                theta = math.acos(max(-1.0, min(1.0, r / d)))
                alpha = math.atan2(p1.y() - c.y(), p1.x() - c.x())
                for ang in (alpha + theta, alpha - theta):
                    t = QPointF(c.x() + r * math.cos(ang), c.y() + r * math.sin(ang))
                    dx, dy = t.x() - p1.x(), t.y() - p1.y()
                    len2 = dx * dx + dy * dy
                    if len2 < 1e-9: continue
                    u = ((scene_pos.x() - p1.x()) * dx + (scene_pos.y() - p1.y()) * dy) / len2
                    if u > 0:
                        proj_pt = QPointF(p1.x() + u * dx, p1.y() + u * dy)
                        score = min(_vdist(scene_pos, t), _vdist(scene_pos, proj_pt))
                        if score < self._snap_threshold():
                            if score < best_dist:
                                best_dist = score
                                best_t, best_target = t, proj_pt
        return (best_target, best_t) if best_t else None

    def mousePressEvent(self, e):
        self.setFocus()
        if e.button() == Qt.MiddleButton or (self.tool == "pan" and e.button() == Qt.LeftButton):
            self._panning = True
            self._pan_start = e.pos()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            e.accept()
            return
        if e.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(e.pos())
            if self.tool in ("line", "polygon", "circle"):
                self._on_click(scene_pos)
                e.accept()
                return
            elif self.tool == "text":
                self._add_text(scene_pos)
                e.accept()
                return
            elif self.tool == "select":
                self._handle_select_press(scene_pos, self.mapToGlobal(e.pos()))
                e.accept()
                return
        super().mousePressEvent(e)

    def _handle_select_press(self, scene_pos, global_pos):
        items = self._scene.items(QRectF(scene_pos.x() - 4, scene_pos.y() - 4, 8, 8))
        candidate_shapes = []
        for it in items:
            for s in self._shapes:
                if s.item == it:
                    candidate_shapes.append(s)
                    break
        if not candidate_shapes: return
        if len(candidate_shapes) == 1:
            self._begin_drag(candidate_shapes[0], scene_pos)
        else:
            menu = QMenu(self)
            menu.setTitle("选择要拖动的对象")
            for i, s in enumerate(candidate_shapes):
                txt = {"line": "直线", "circle": "圆", "polygon": "多边形", "text": "文本"}.get(s.kind, "图形")
                if s.kind == "text": txt += f" \"{s.item.toPlainText()[:6]}\""
                else: txt += f" {i+1}"
                act = menu.addAction(txt)
                act.triggered.connect(lambda _=False, sh=s: self._begin_drag(sh, scene_pos))
            menu.exec_(global_pos)

    def _begin_drag(self, shape, scene_pos):
        self._drag_shape = shape
        self._last_drag_pos = scene_pos
        self.viewport().setCursor(Qt.SizeAllCursor)

    def mouseMoveEvent(self, e):
        if self._panning:
            delta = e.pos() - self._pan_start
            self._pan_start = e.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            e.accept()
            return

        scene_pos = self.mapToScene(e.pos())
        if self.tool == "select":
            if self._drag_shape:
                dx = scene_pos.x() - self._last_drag_pos.x()
                dy = scene_pos.y() - self._last_drag_pos.y()
                if abs(dx) > 0.001 or abs(dy) > 0.001:
                    self._drag_shape.move_by(dx, dy)
                    self._last_drag_pos = scene_pos
                self.viewport().setCursor(Qt.SizeAllCursor)
                e.accept()
                return
            else:
                rect = QRectF(scene_pos.x() - 4, scene_pos.y() - 4, 8, 8)
                items = self._scene.items(rect)
                has_shape = any(any(s.item == it for s in self._shapes) for it in items)
                self.viewport().setCursor(Qt.SizeAllCursor if has_shape else Qt.ArrowCursor)

        if self.tool in ("line", "polygon", "circle"):
            snapped = self._snap(scene_pos)
            self._update_snap_marker()
            if self.tool == "line" and len(self._pending_pts) == 1:
                tangent_info = self._find_tangent_snap(self._pending_pts[0], scene_pos)
                if tangent_info:
                    snapped = tangent_info[0]
                    self._snap_target = tangent_info[1]
                    self._snap_kind = "tangent"
                    self._update_snap_marker()
            if self._pending_pts: self._refresh_preview(snapped)
            else: self._clear_dynamic()
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self.tool == "select" and self._drag_shape:
            self._drag_shape = None
            self.viewport().setCursor(Qt.ArrowCursor)
            e.accept()
            return
        if self._panning:
            self._panning = False
            self._update_cursor()
            e.accept()
            return
        super().mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        if e.modifiers() & Qt.ControlModifier and e.key() == Qt.Key_Z:
            self.redo() if (e.modifiers() & Qt.ShiftModifier) else self.undo()
            e.accept()
            return
        if e.key() == Qt.Key_Escape:
            self._cancel_drawing()
            return
        if e.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            if self.tool == "polygon" and len(self._pending_pts) >= 3:
                self._finish_polygon()
                return
        super().keyPressEvent(e)

    def _add_text(self, scene_pos):
        text, ok = QInputDialog.getText(self, "输入文本", "请输入要插入的文字：")
        if ok and text.strip():
            item = QGraphicsTextItem(text.strip())
            item.setDefaultTextColor(self.pen.color())
            item.setPos(scene_pos)
            item.setZValue(50)
            item.setFont(QFont("Microsoft YaHei", 16))
            self._scene.addItem(item)
            g = GeoShape(item, "text")
            g.key_points = [scene_pos]
            self._shapes.append(g)
            self._redo.clear()
            if hasattr(self, 'main_window'): self.main_window.mark_dirty()

    def _on_click(self, scene_pos):
        p = self._snap(scene_pos)
        if self.tool == "line":
            if len(self._pending_pts) == 1:
                tangent_info = self._find_tangent_snap(self._pending_pts[0], scene_pos)
                if tangent_info: p = tangent_info[0]
            self._pending_pts.append(p)
            if len(self._pending_pts) >= 2:
                self._commit_line(self._pending_pts[0], self._pending_pts[1])
                self._pending_pts = []
            self._clear_dynamic()
        elif self.tool == "circle":
            self._pending_pts.append(p)
            if len(self._pending_pts) >= 2:
                self._commit_circle(self._pending_pts[0], self._pending_pts[1])
                self._pending_pts = []
            self._clear_dynamic()
        elif self.tool == "polygon":
            if len(self._pending_pts) >= 3 and _vdist(p, self._pending_pts[0]) < self._snap_threshold() * 0.9:
                self._finish_polygon()
            else:
                if self._pending_pts:
                    item = QGraphicsLineItem(QLineF(self._pending_pts[-1], p))
                    item.setPen(QPen(self.pen))
                    item.setZValue(100)
                    self._scene.addItem(item)
                    self._poly_fixed_items.append(item)
                self._pending_pts.append(p)

    def _finish_polygon(self):
        pts = self._pending_pts[:]
        if len(pts) >= 2 and _vdist(pts[-1], pts[0]) < 1e-6: pts.pop()
        self._pending_pts = []
        self._clear_dynamic()
        self._clear_poly_fixed()
        if len(pts) >= 3: self._commit_polygon(pts)

    def _commit_line(self, p1, p2):
        if _vdist(p1, p2) < 2: return
        item = QGraphicsLineItem(QLineF(p1, p2))
        item.setPen(QPen(self.pen))
        item.setZValue(10)
        self._scene.addItem(item)
        g = GeoShape(item, "line")
        g.key_points = [QPointF(p1), QPointF(p2)]
        g.segments = [(QPointF(p1), QPointF(p2))]
        self._shapes.append(g)
        self._redo.clear()
        if hasattr(self, 'main_window'): self.main_window.mark_dirty()

    def _commit_circle(self, center, radius_pt):
        r = _vdist(center, radius_pt)
        if r < 3: return
        item = QGraphicsEllipseItem(QRectF(center.x() - r, center.y() - r, 2 * r, 2 * r))
        item.setPen(QPen(self.pen))
        item.setZValue(10)
        self._scene.addItem(item)
        g = GeoShape(item, "circle")
        g.key_points = [QPointF(center)]
        g.circles = [(QPointF(center), r)]
        self._shapes.append(g)
        self._redo.clear()
        if hasattr(self, 'main_window'): self.main_window.mark_dirty()

    def _commit_polygon(self, pts):
        poly = QPolygonF([QPointF(p) for p in pts])
        item = QGraphicsPolygonItem(poly)
        item.setPen(QPen(self.pen))
        item.setBrush(QBrush(QColor(self.pen.color().red(), self.pen.color().green(), self.pen.color().blue(), 22)))
        item.setZValue(10)
        self._scene.addItem(item)
        g = GeoShape(item, "polygon")
        g.key_points = [QPointF(p) for p in pts]
        n = len(pts)
        g.segments = [(QPointF(pts[i]), QPointF(pts[(i + 1) % n])) for i in range(n)]
        self._shapes.append(g)
        self._redo.clear()
        if hasattr(self, 'main_window'): self.main_window.mark_dirty()

    def _preview_pen(self):
        pen = QPen(self.pen)
        pen.setStyle(Qt.DashLine)
        pen.setColor(QColor(self.pen.color().red(), self.pen.color().green(), self.pen.color().blue(), 170))
        return pen

    def _ensure_line_a(self):
        if self._dynamic_line_a is None:
            item = QGraphicsLineItem()
            item.setPen(self._preview_pen())
            item.setZValue(100)
            self._scene.addItem(item)
            self._dynamic_line_a = item
        return self._dynamic_line_a

    def _ensure_line_b(self):
        if self._dynamic_line_b is None:
            item = QGraphicsLineItem()
            item.setPen(self._preview_pen())
            item.setZValue(100)
            self._scene.addItem(item)
            self._dynamic_line_b = item
        return self._dynamic_line_b

    def _ensure_circle(self):
        if self._dynamic_circle is None:
            item = QGraphicsEllipseItem()
            item.setPen(self._preview_pen())
            item.setZValue(100)
            self._scene.addItem(item)
            self._dynamic_circle = item
        return self._dynamic_circle

    def _clear_dynamic(self):
        if self._dynamic_line_a: self._dynamic_line_a.hide()
        if self._dynamic_line_b: self._dynamic_line_b.hide()
        if self._dynamic_circle: self._dynamic_circle.hide()

    def _clear_poly_fixed(self):
        for it in self._poly_fixed_items: self._scene.removeItem(it)
        self._poly_fixed_items = []

    def _refresh_preview(self, snapped):
        if not self._pending_pts: return
        preview_pen = self._preview_pen()
        if self.tool == "line" and len(self._pending_pts) == 1:
            a = self._ensure_line_a()
            a.setPen(preview_pen)
            a.setLine(QLineF(self._pending_pts[0], snapped))
            a.show()
            if self._dynamic_line_b: self._dynamic_line_b.hide()
            if self._dynamic_circle: self._dynamic_circle.hide()
        elif self.tool == "circle" and len(self._pending_pts) == 1:
            c = self._pending_pts[0]
            r = _vdist(c, snapped)
            circ = self._ensure_circle()
            circ.setPen(preview_pen)
            if r > 2:
                circ.setRect(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r))
                circ.show()
            else: circ.hide()
            if self._dynamic_line_a: self._dynamic_line_a.hide()
            if self._dynamic_line_b: self._dynamic_line_b.hide()
        elif self.tool == "polygon" and self._pending_pts:
            a = self._ensure_line_a()
            a.setPen(preview_pen)
            a.setLine(QLineF(self._pending_pts[-1], snapped))
            a.show()
            if len(self._pending_pts) >= 2:
                b = self._ensure_line_b()
                b.setPen(preview_pen)
                b.setLine(QLineF(snapped, self._pending_pts[0]))
                b.show()
            elif self._dynamic_line_b: self._dynamic_line_b.hide()
            if self._dynamic_circle: self._dynamic_circle.hide()

    def _cancel_drawing(self):
        self._pending_pts = []
        self._clear_dynamic()
        self._clear_poly_fixed()
        self._snap_target = None
        self._snap_kind = None
        if self._snap_marker: self._snap_marker.hide()

    def undo(self):
        if not self._shapes: return False
        g = self._shapes.pop()
        self._scene.removeItem(g.item)
        self._redo.append(g)
        if hasattr(self, 'main_window'): self.main_window.mark_dirty()
        return True

    def redo(self):
        if not self._redo: return False
        g = self._redo.pop()
        self._scene.addItem(g.item)
        self._shapes.append(g)
        if hasattr(self, 'main_window'): self.main_window.mark_dirty()
        return True

    def clear_shapes(self):
        if self._shapes and hasattr(self, 'main_window'): self.main_window.mark_dirty()
        for g in self._shapes: self._scene.removeItem(g.item)
        self._shapes.clear()
        self._redo.clear()
        self._cancel_drawing()

    def clear_all(self):
        self.clear_shapes()
        if self.image_item:
            self._scene.removeItem(self.image_item)
            self.image_item = None
        self.resetTransform()

    def load_image(self, path):
        pix = QPixmap(path)
        if pix.isNull(): return False
        if self.image_item: self._scene.removeItem(self.image_item)
        self.image_item = QGraphicsPixmapItem(pix)
        self.image_item.setZValue(-100)
        self.image_item.setPos(0, 0)
        self._scene.addItem(self.image_item)
        r = self.image_item.sceneBoundingRect()
        self._scene.setSceneRect(r.adjusted(-400, -400, 400, 400))
        self.fit_view()
        if hasattr(self, 'main_window'): self.main_window.mark_dirty()
        return True

    def zoom_in(self): self._zoom(1.25)
    def zoom_out(self): self._zoom(0.8)

    def _zoom(self, factor):
        cur = self.transform().m11()
        if not (0.03 < cur * factor < 60): return
        self.scale(factor, factor)

    def wheelEvent(self, e):
        dy = e.angleDelta().y()
        if dy == 0:
            super().wheelEvent(e)
            return
        self._zoom(1.15 if dy > 0 else 1 / 1.15)
        e.accept()

    def fit_view(self):
        rect = self._content_rect()
        if rect.isEmpty(): return
        self.fitInView(rect, Qt.KeepAspectRatio)
        s = self.transform().m11()
        if s > 2.0: self.scale(2.0 / s, 2.0 / s)

    def _content_rect(self):
        rect = QRectF()
        if self.image_item: rect = rect.united(self.image_item.sceneBoundingRect())
        for g in self._shapes: rect = rect.united(g.item.sceneBoundingRect())
        if not rect.isEmpty(): rect = rect.adjusted(-10, -10, 10, 10)
        return rect

    def render_image(self):
        rect = self._content_rect()
        if rect.isEmpty(): return QImage()
        w = max(1, int(round(rect.width())))
        h = max(1, int(round(rect.height())))
        img = QImage(w, h, QImage.Format_ARGB32)
        img.fill(Qt.white)
        p = QPainter(img)
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self._scene.render(p, QRectF(0, 0, w, h), rect)
        p.end()
        return img

    def get_data(self):
        data = {"shapes": [], "image_b64": None, "image_pos": [0, 0]}
        if self.image_item:
            pix = self.image_item.pixmap()
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.WriteOnly)
            if pix.save(buffer, "PNG"):
                data["image_b64"] = base64.b64encode(bytes(byte_array)).decode('utf-8')
            pos = self.image_item.pos()
            data["image_pos"] = [pos.x(), pos.y()]

        for g in self._shapes:
            if g.kind == "line":
                line = g.item.line()
                data["shapes"].append({"kind": "line", "color": g.item.pen().color().name(), "width": g.item.pen().width(), "style": int(g.item.pen().style()), "data": [line.x1(), line.y1(), line.x2(), line.y2()]})
            elif g.kind == "circle":
                rect = g.item.rect()
                r = rect.width() / 2
                c = rect.center()
                data["shapes"].append({"kind": "circle", "color": g.item.pen().color().name(), "width": g.item.pen().width(), "style": int(g.item.pen().style()), "data": [c.x(), c.y(), r]})
            elif g.kind == "polygon":
                poly = g.item.polygon()
                pts = [[p.x(), p.y()] for p in poly]
                data["shapes"].append({"kind": "polygon", "color": g.item.pen().color().name(), "width": g.item.pen().width(), "style": int(g.item.pen().style()), "data": pts})
            elif g.kind == "text":
                pos = g.item.pos()
                text = g.item.toPlainText()
                data["shapes"].append({"kind": "text", "color": g.item.defaultTextColor().name(), "data": [pos.x(), pos.y(), text]})
        return data

    def load_data(self, data):
        self.clear_all()
        if data.get("image_b64"):
            b64 = data["image_b64"]
            img_data = base64.b64decode(b64)
            pix = QPixmap()
            if pix.loadFromData(img_data):
                self.image_item = QGraphicsPixmapItem(pix)
                self.image_item.setZValue(-100)
                if "image_pos" in data:
                    self.image_item.setPos(data["image_pos"][0], data["image_pos"][1])
                self._scene.addItem(self.image_item)

        for s in data.get("shapes", []):
            kind = s["kind"]
            col = QColor(s["color"])
            if kind == "line":
                x1, y1, x2, y2 = s["data"]
                item = QGraphicsLineItem(x1, y1, x2, y2)
                pen = QPen(col)
                pen.setWidth(s["width"])
                pen.setStyle(s["style"])
                item.setPen(pen)
                item.setZValue(10)
                self._scene.addItem(item)
                g = GeoShape(item, "line")
                g.key_points = [QPointF(x1, y1), QPointF(x2, y2)]
                g.segments = [(QPointF(x1, y1), QPointF(x2, y2))]
                self._shapes.append(g)
            elif kind == "circle":
                cx, cy, r = s["data"]
                item = QGraphicsEllipseItem(cx - r, cy - r, 2 * r, 2 * r)
                pen = QPen(col)
                pen.setWidth(s["width"])
                pen.setStyle(s["style"])
                item.setPen(pen)
                item.setZValue(10)
                self._scene.addItem(item)
                g = GeoShape(item, "circle")
                g.key_points = [QPointF(cx, cy)]
                g.circles = [(QPointF(cx, cy), r)]
                self._shapes.append(g)
            elif kind == "polygon":
                pts = s["data"]
                poly = QPolygonF([QPointF(x, y) for x, y in pts])
                item = QGraphicsPolygonItem(poly)
                pen = QPen(col)
                pen.setWidth(s["width"])
                pen.setStyle(s["style"])
                item.setPen(pen)
                item.setBrush(QBrush(QColor(col.red(), col.green(), col.blue(), 22)))
                item.setZValue(10)
                self._scene.addItem(item)
                g = GeoShape(item, "polygon")
                g.key_points = [QPointF(x, y) for x, y in pts]
                n = len(pts)
                g.segments = [(QPointF(pts[i][0], pts[i][1]), QPointF(pts[(i + 1) % n][0], pts[(i + 1) % n][1])) for i in range(n)]
                self._shapes.append(g)
            elif kind == "text":
                x, y, text = s["data"]
                item = QGraphicsTextItem(text)
                item.setDefaultTextColor(col)
                item.setPos(x, y)
                item.setZValue(50)
                item.setFont(QFont("Microsoft YaHei", 16))
                self._scene.addItem(item)
                g = GeoShape(item, "text")
                g.key_points = [QPointF(x, y)]
                self._shapes.append(g)

        self.fit_view()


# ================================================================
#  文字面板 (原生中文 + Desmos 悬浮窗输入)
# ================================================================

class MathInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("插入 Desmos 公式")
        self.resize(500, 200)
        self.latex = ""
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = QWebEngineView(self)
        self.view.page().setHtml(self.get_html())
        self.layout.addWidget(self.view, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(10, 10, 10, 10)
        btn_ok = QPushButton("插入到文字")
        btn_ok.clicked.connect(self.accept_math)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch(1)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        
        self.layout.addLayout(btn_layout)
        
    def get_html(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/mathquill/0.10.1/mathquill.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/mathquill/0.10.1/mathquill.min.js"></script>
            <style>
                body { font-family: "Times New Roman", sans-serif; padding: 20px; margin: 0; background: #fff; font-size: 24px; }
                .mq-editable-field { border: none !important; box-shadow: none !important; width: 100%; min-height: 100px; outline: none !important; font-size: 2em; }
                #math-input { width: 100%; height: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }
            </style>
        </head>
        <body>
            <div id="math-input"></div>
            <script>
                var MQ = MathQuill.getInterface(2);
                var mathField = MQ.MathField(document.getElementById('math-input'), {
                    spaceBehavesLikeTab: true,
                });
                mathField.focus();
                function getLatex() {
                    return mathField.latex();
                }
            </script>
        </body>
        </html>
        """
        
    def accept_math(self):
        self.view.page().runJavaScript("getLatex();", self.on_latex_received)
        
    def on_latex_received(self, latex):
        self.latex = latex
        self.accept()


class SymbolBar(QWidget):
    insertRequested = pyqtSignal(str)
    def __init__(self, symbols, per_row=14, parent=None):
        super().__init__(parent)
        grid = QGridLayout(self)
        grid.setContentsMargins(4, 2, 4, 2)
        grid.setSpacing(4)
        for i, s in enumerate(symbols):
            b = QToolButton(self)
            b.setText(s)
            b.setAutoRaise(True)
            b.setFixedSize(QSize(32, 32))
            f = b.font()
            f.setPointSize(16)
            f.setFamily("Arial")
            b.setFont(f)
            b.setToolTip(s)
            b.clicked.connect(lambda _=False, ch=s: self.insertRequested.emit(ch))
            grid.addWidget(b, i // per_row, i % per_row)
        grid.setColumnStretch(per_row, 1)


class TextPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.editor = QTextEdit(self)
        self.editor.setAcceptRichText(True)
        self.editor.setPlaceholderText("在此输入题目文字… 点击上方按钮插入 Desmos 公式")
        base_font = QFont("Microsoft YaHei", 14)
        self.editor.setFont(base_font)
        self.editor.setStyleSheet("QTextEdit{background:#ffffff;border:none;padding:10px; line-height: 150%;}")

        top = QHBoxLayout()
        top.setContentsMargins(4, 3, 4, 3)
        top.setSpacing(4)
        
        self.font_box = QFontComboBox(self)
        self.font_box.setFont(base_font)
        self.font_box.setMaximumWidth(130)
        self.font_box.currentFontChanged.connect(self._on_font_changed)
        top.addWidget(self.font_box)

        self.size_box = QSpinBox(self)
        self.size_box.setRange(6, 120)
        self.size_box.setValue(14)
        self.size_box.setFixedWidth(50)
        self.size_box.valueChanged.connect(self._on_size_changed)
        top.addWidget(self.size_box)

        self.bold_btn = QToolButton(self)
        self.bold_btn.setText("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(QSize(24, 24))
        self.bold_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.bold_btn.clicked.connect(self._on_bold)
        top.addWidget(self.bold_btn)

        self.italic_btn = QToolButton(self)
        self.italic_btn.setText("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedSize(QSize(24, 24))
        self.italic_btn.setFont(QFont("Arial", 10, QFont.StyleItalic))
        self.italic_btn.clicked.connect(self._on_italic)
        top.addWidget(self.italic_btn)

        top.addSpacing(15)
        
        btn_desmos = QToolButton(self)
        btn_desmos.setText("插入 Desmos 公式")
        btn_desmos.setToolTip("调用 Desmos 同款输入引擎插入公式")
        btn_desmos.setStyleSheet("QToolButton { padding: 4px 8px; border-radius: 4px; background: #e8f0fe; border: 1px solid #d2e3fc; color: #1976d2; font-weight: bold; } QToolButton:hover { background: #d2e3fc; }")
        btn_desmos.clicked.connect(self.insert_desmos_formula)
        top.addWidget(btn_desmos)

        top.addStretch(1)

        self.sym_bar = SymbolBar(SYMBOLS)
        self.sym_bar.insertRequested.connect(self.insert_symbol)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addLayout(top)
        lay.addWidget(self.sym_bar)
        lay.addWidget(self.editor, 1)

        self._sync_editor_widget_font()
        self.editor.textChanged.connect(self._mark_dirty)

    def insert_desmos_formula(self):
        dlg = MathInputDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            latex = dlg.latex
            if not latex.strip():
                return
            
            html = self.latex_to_html(latex)
            
            cursor = self.editor.textCursor()
            base_size = self.size_box.value()
            fmt_normal = QTextCharFormat()
            fmt_normal.setFontPointSize(base_size)
            
            cursor.beginEditBlock()
            cursor.insertHtml(html)
            
            # 核心修复：插入零宽空格引导光标跳出表格，再正常插入普通空格
            cursor.insertText("\u200B", fmt_normal) 
            cursor.insertText(" ", fmt_normal)
            
            self.editor.setTextCursor(cursor)
            cursor.endEditBlock()
            self.editor.setFocus()

    # 使用 Span + CSS 块级布局模拟二维分数，彻底避开 Qt 表格光标锁死问题
    def latex_to_html(self, latex):
        size = self.size_box.value()
        
        def repl_frac(m):
            return f'''<span style="display:inline-block; vertical-align:middle; text-align:center; margin:0 2px; font-size:{size}pt;">
                <span style="display:block; border-bottom:1px solid #333; padding:0 4px;">{m.group(1)}</span>
                <span style="display:block; padding:0 4px;">{m.group(2)}</span>
            </span>'''
        
        latex = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', repl_frac, latex)
        
        def repl_sqrt(m):
            return f'<span style="font-size:{size*1.3}pt; vertical-align:middle;">√</span><span style="text-decoration:overline; font-size:{size}pt;">{m.group(1)}</span>'
        latex = re.sub(r'\\sqrt\{([^{}]+)\}', repl_sqrt, latex)
        
        def repl_sup(m):
            return f'<span style="vertical-align:super; font-size:{size*0.75}pt;">{m.group(1)}</span>'
        latex = re.sub(r'\^\{([^{}]+)\}', repl_sup, latex)
        
        def repl_sub(m):
            return f'<span style="vertical-align:sub; font-size:{size*0.75}pt;">{m.group(1)}</span>'
        latex = re.sub(r'_\{([^{}]+)\}', repl_sub, latex)
        
        sym_map = {
            '\\pi': 'π', '\\alpha': 'α', '\\beta': 'β', '\\theta': 'θ', '\\lambda': 'λ', '\\mu': 'μ', '\\sigma': 'σ', '\\omega': 'ω',
            '\\times': '×', '\\div': '÷', '\\pm': '±', '\\le': '≤', '\\ge': '≥', '\\ne': '≠', '\\infty': '∞',
            '\\angle': '∠', '\\triangle': '△', '\\odot': '⊙', '\\perp': '⊥', '\\parallel': '∥', '\\in': '∈', '\\notin': '∉',
            '\\sum': '∑', '\\prod': '∏', '\\int': '∫', '\\vec': '', '\\cdot': '·'
        }
        for k, v in sym_map.items():
            latex = latex.replace(k, v)
            
        return f'<span style="font-size:{size}pt; font-family:\'Times New Roman\';">{latex}</span>'

    def _mark_dirty(self):
        win = self.window()
        if hasattr(win, 'mark_dirty'):
            win.mark_dirty()

    def _apply(self, fmt: QTextCharFormat):
        cur = self.editor.textCursor()
        cur.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

    def _sync_editor_widget_font(self):
        family = self.font_box.currentFont().family()
        size = self.size_box.value()
        f = QFont(family, size)
        self.editor.setFont(f)
        self.editor.document().setDefaultFont(f)
        self.editor.setStyleSheet(f"QTextEdit{{background:#ffffff;border:none;padding:10px; font-family:'{family}'; font-size:{size}pt; line-height: 150%;}}")

    def _on_font_changed(self, f):
        fmt = QTextCharFormat()
        fmt.setFontFamily(f.family())
        self._apply(fmt)
        self._sync_editor_widget_font()

    def _on_size_changed(self, v):
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(v))
        self._apply(fmt)
        self._sync_editor_widget_font()

    def _on_bold(self, checked):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold if checked else QFont.Normal)
        self._apply(fmt)

    def _on_italic(self, checked):
        fmt = QTextCharFormat()
        fmt.setFontItalic(checked)
        self._apply(fmt)

    def insert_symbol(self, ch):
        self.editor.insertPlainText(ch)
        self.editor.setFocus()

    def get_data(self):
        return {"html": self.editor.toHtml()}
        
    def load_data(self, data):
        self.editor.setHtml(data.get("html", ""))
        self.editor.document().clearUndoRedoStacks()


class TabBar(QTabBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_widget = parent
        self._drag_start = None
        self._drag_index = -1

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_start = e.pos()
            self._drag_index = self.tabAt(e.pos())
        super().mousePressEvent(e)
        
    def mouseMoveEvent(self, e):
        if self._drag_start and self._drag_index != -1:
            if (e.pos() - self._drag_start).manhattanLength() > QApplication.startDragDistance():
                if not self.rect().contains(e.pos()):
                    win = self.window()
                    widget = self.parent_widget.widget(self._drag_index)
                    title = self.parent_widget.tabText(self._drag_index)
                    self.parent_widget.removeTab(self._drag_index)
                    fw = FloatingWindow(widget, self.parent_widget, title, win)
                    fw.move(e.globalPos() - QPoint(40, 16))
                    fw._drag_offset = e.globalPos() - fw.pos()
                    win.float_windows.append(fw)
                    win._detaching_fw = fw
                    fw.show()
                    fw.activateWindow()
                    self.grabMouse()
                    self._drag_index = -1
        
        win = self.window()
        if getattr(win, '_detaching_fw', None):
            fw = win._detaching_fw
            fw.move(e.globalPos() - fw._drag_offset)
            target = fw.source_tab
            if target.rect().contains(target.mapFromGlobal(e.globalPos())):
                if getattr(fw, '_has_left_target', False):
                    target.setStyleSheet("QTabWidget::pane { border: 2px dashed #1976d2; background: #e8f0fe; }")
            else:
                fw._has_left_target = True
                target.setStyleSheet("")
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self.releaseMouse()
        win = self.window()
        if getattr(win, '_detaching_fw', None):
            fw = win._detaching_fw
            win._detaching_fw = None
            target = fw.source_tab
            target.setStyleSheet("")
        self._drag_start = None
        self._drag_index = -1
        super().mouseReleaseEvent(e)
        
    def mouseDoubleClickEvent(self, e):
        index = self.tabAt(e.pos())
        if index != -1:
            self.parent_widget.rename_tab(index)
            win = self.window()
            if hasattr(win, 'mark_dirty'):
                win.mark_dirty()
        super().mouseDoubleClickEvent(e)
        
    def contextMenuEvent(self, e):
        index = self.tabAt(e.pos())
        menu = QMenu(self)
        if index == -1:
            win = self.window()
            if self.parent_widget == win.canvas_tabs:
                act = menu.addAction("新建画图")
                act.triggered.connect(win._new_canvas_tab)
            elif self.parent_widget == win.text_tabs:
                act = menu.addAction("新建文字框")
                act.triggered.connect(win._new_text_tab)
        else:
            act_rename = menu.addAction("重命名")
            act_rename.triggered.connect(lambda: self.parent_widget.rename_tab(index))
            act_close = menu.addAction("关闭")
            act_close.triggered.connect(lambda: self.parent_widget.close_tab(index))
        if not menu.isEmpty():
            menu.exec_(e.globalPos())
        e.accept()

class DetachableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(TabBar(self))
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self._empty_hint = QLabel("此处已空\n右键或双击此处新建，或将独立窗口拖回", self)
        self._empty_hint.setAlignment(Qt.AlignCenter)
        self._empty_hint.setStyleSheet("color: #888; font-size: 14px; font-weight: bold; background: transparent;")
        self._empty_hint.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._empty_hint.hide()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._empty_hint.setGeometry(0, 0, self.width(), self.height())
        
    def paintEvent(self, e):
        super().paintEvent(e)
        if self.count() == 0:
            self._empty_hint.show()
        else:
            self._empty_hint.hide()

    def rename_tab(self, index):
        title, ok = QInputDialog.getText(self, "重命名标签", "请输入新名称：", text=self.tabText(index))
        if ok and title.strip():
            self.setTabText(index, title.strip())

    def close_tab(self, index):
        w = self.widget(index)
        self.removeTab(index)
        w.deleteLater()
        win = self.window()
        if hasattr(win, 'mark_dirty'):
            win.mark_dirty()

    def mouseDoubleClickEvent(self, e):
        if self.count() == 0:
            win = self.window()
            if hasattr(win, '_new_canvas_tab') and self == win.canvas_tabs:
                win._new_canvas_tab()
            elif hasattr(win, '_new_text_tab') and self == win.text_tabs:
                win._new_text_tab()
        super().mouseDoubleClickEvent(e)
        
    def contextMenuEvent(self, e):
        if self.count() == 0 or not self.tabBar().geometry().contains(e.pos()):
            menu = QMenu(self)
            win = self.window()
            if self == win.canvas_tabs:
                act = menu.addAction("新建画图")
                act.triggered.connect(win._new_canvas_tab)
            elif self == win.text_tabs:
                act = menu.addAction("新建文字框")
                act.triggered.connect(win._new_text_tab)
            if not menu.isEmpty():
                menu.exec_(e.globalPos())
                e.accept()
                return
        super().contextMenuEvent(e)

class FloatingWindow(QWidget):
    def __init__(self, widget, source_tab, title, main_window):
        super().__init__(main_window, Qt.Window | Qt.FramelessWindowHint)
        self.widget = widget
        self.source_tab = source_tab
        self.main_window = main_window
        self.setWindowTitle(title)
        self.resize(600, 450)
        self.setStyleSheet(main_window.styleSheet())
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(32)
        self.title_bar.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #dcdcdc;")
        tl = QHBoxLayout(self.title_bar)
        tl.setContentsMargins(10, 0, 5, 0)
        tl.setSpacing(5)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #333; font-weight: bold; font-size: 12px;")
        self.close_btn = QToolButton()
        self.close_btn.setText("✕")
        self.close_btn.setToolTip("关闭并放回")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("QToolButton { border: none; padding: 2px 6px; color: #666; border-radius: 3px; } QToolButton:hover { background: #e81123; color: white; }")
        tl.addWidget(self.title_label)
        tl.addStretch(1)
        tl.addWidget(self.close_btn)
        self.layout.addWidget(self.title_bar)
        self.content_area = QWidget()
        cl = QVBoxLayout(self.content_area)
        cl.setContentsMargins(0,0,0,0)
        widget.setParent(None)
        cl.addWidget(widget)
        widget.show()
        self.layout.addWidget(self.content_area, 1)
        self._closing_by_dock = False
        self._drag_offset = QPoint()
        self._has_left_target = False
        self.title_bar.mousePressEvent = self._title_mouse_press
        self.title_bar.mouseMoveEvent = self._title_mouse_move
        self.title_bar.mouseReleaseEvent = self._title_mouse_release
        
    def _title_mouse_press(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_offset = e.globalPos() - self.pos()
            e.accept()
    def _title_mouse_move(self, e):
        if e.buttons() == Qt.LeftButton:
            self.move(e.globalPos() - self._drag_offset)
            target = self.main_window.canvas_tabs if self.source_tab == self.main_window.canvas_tabs else self.main_window.text_tabs
            if target.rect().contains(target.mapFromGlobal(e.globalPos())):
                if self._has_left_target:
                    target.setStyleSheet("QTabWidget::pane { border: 2px dashed #1976d2; background: #e8f0fe; }")
            else:
                self._has_left_target = True
                target.setStyleSheet("")
            e.accept()
    def _title_mouse_release(self, e):
        if e.button() == Qt.LeftButton:
            target = self.main_window.canvas_tabs if self.source_tab == self.main_window.canvas_tabs else self.main_window.text_tabs
            target.setStyleSheet("")
            if self._has_left_target and target.rect().contains(target.mapFromGlobal(e.globalPos())):
                self.main_window.dock_back(self)
            e.accept()
    def closeEvent(self, e):
        if not self._closing_by_dock:
            self.main_window.dock_back(self)
        super().closeEvent(e)

class WelcomePage(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setStyleSheet("background-color: #f3f3f3;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(80, 60, 80, 40)
        main_layout.setSpacing(30)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        logo_pix = QPixmap(48, 48)
        logo_pix.fill(Qt.transparent)
        p = QPainter(logo_pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#1976d2"), 3))
        p.setBrush(QBrush(QColor("#e8f0fe")))
        p.drawEllipse(6, 6, 36, 36)
        p.drawLine(6, 6, 42, 42)
        p.end()
        logo_label = QLabel()
        logo_label.setPixmap(logo_pix)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title = QLabel("MathPad")
        title.setStyleSheet("font-size: 32px; font-weight: 600; color: #222;")
        subtitle = QLabel("简约数学题目编辑器")
        subtitle.setStyleSheet("font-size: 14px; color: #666;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addWidget(logo_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch(1)
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)
        start_label = QLabel("开始")
        start_label.setStyleSheet("font-size: 18px; font-weight: 500; color: #333; margin-bottom: 5px;")
        main_layout.addWidget(start_label)
        btn_style = """
            QPushButton {
                text-align: left; padding: 10px; background: transparent;
                border: 1px solid transparent; font-size: 14px; color: #1976d2; border-radius: 4px;
            }
            QPushButton:hover { background: #e8f0fe; border: 1px solid #d2e3fc; }
        """
        btn_new = QPushButton("新建项目")
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.setStyleSheet(btn_style)
        btn_new.clicked.connect(main_window.new_project)
        btn_open = QPushButton("导入项目…")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet(btn_style)
        btn_open.clicked.connect(main_window.load_project_dialog)
        main_layout.addWidget(btn_new)
        main_layout.addWidget(btn_open)
        main_layout.addSpacing(20)
        tips_label = QLabel("快捷提示")
        tips_label.setStyleSheet("font-size: 18px; font-weight: 500; color: #333; margin-bottom: 5px;")
        main_layout.addWidget(tips_label)
        tips = [("Ctrl+S", "保存项目"), ("Ctrl+Z", "撤销操作"), ("Ctrl+O", "打开项目"), ("Ctrl+滚轮", "缩放画布")]
        for key, desc in tips:
            row = QHBoxLayout()
            row.setSpacing(10)
            row.setContentsMargins(10, 0, 0, 0)
            lbl_key = QLabel(key)
            lbl_key.setStyleSheet("background: #ffffff; border: 1px solid #dcdcdc; border-radius: 3px; padding: 2px 8px; font-family: Consolas, monospace; font-size: 12px; color: #333;")
            lbl_desc = QLabel(desc)
            lbl_desc.setStyleSheet("color: #555; font-size: 13px;")
            row.addWidget(lbl_key)
            row.addWidget(lbl_desc)
            row.addStretch(1)
            main_layout.addLayout(row)
        main_layout.addStretch(1)
        footer_layout = QHBoxLayout()
        version_label = QLabel("版本 1.0.0")
        version_label.setStyleSheet("color: #888; font-size: 12px;")
        copyright_label = QLabel("© 2023 MathPad. All rights reserved.")
        copyright_label.setStyleSheet("color: #888; font-size: 12px;")
        footer_layout.addWidget(version_label)
        footer_layout.addStretch(1)
        footer_layout.addWidget(copyright_label)
        main_layout.addLayout(footer_layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MathPad · 未命名项目")
        self.resize(1200, 780)
        self.setStyleSheet(STYLE_TEMPLATE.format(fs="12px"))
        self.float_windows = []
        self.active_canvas = None
        self._detaching_fw = None
        self.current_project_path = None
        self.is_dirty = False
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)
        self.welcome_page = WelcomePage(self)
        self.stacked_widget.addWidget(self.welcome_page)
        self.editor_widget = QWidget()
        self.stacked_widget.addWidget(self.editor_widget)
        self.editor_layout = QVBoxLayout(self.editor_widget)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_layout.setSpacing(0)
        self.canvas_tabs = DetachableTabWidget(self)
        self.text_tabs = DetachableTabWidget(self)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.canvas_tabs)
        self.splitter.addWidget(self.text_tabs)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([680, 500])
        self.splitter.setHandleWidth(4)
        self.splitter.setChildrenCollapsible(False)
        self.editor_layout.addWidget(self.splitter)
        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self.toolbar.setVisible(False)
        self.statusBar().showMessage("欢迎使用 MathPad")
        
    def mark_dirty(self):
        if not self.is_dirty:
            self.is_dirty = True
            self.update_title()
    def update_title(self):
        if self.current_project_path:
            base = os.path.basename(self.current_project_path)
        else:
            base = "未命名项目"
        if self.is_dirty: base += " *"
        self.setWindowTitle(f"{base} - MathPad")
    def start_editor(self):
        self.stacked_widget.setCurrentWidget(self.editor_widget)
        self.toolbar.setVisible(True)
    def new_project(self):
        self.current_project_path = None
        self.is_dirty = False
        self.update_title()
        while self.canvas_tabs.count() > 0: self.canvas_tabs.close_tab(0)
        while self.text_tabs.count() > 0: self.text_tabs.close_tab(0)
        self._new_canvas_tab()
        self._new_text_tab()
        self.start_editor()
        self.statusBar().showMessage("已新建项目")
        self.is_dirty = False
        self.update_title()
    def load_project_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入项目", "", f"MathPad 项目 (*{DEFAULT_PROJECT_EXT});;所有文件 (*)")
        if not path: return
        self.load_project(path)
    def load_project(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法读取项目文件：\n{e}")
            return
        self.current_project_path = path
        self.is_dirty = False
        self.update_title()
        while self.canvas_tabs.count() > 0: self.canvas_tabs.close_tab(0)
        while self.text_tabs.count() > 0: self.text_tabs.close_tab(0)
        for cv_data in data.get("canvases", []):
            canvas = MathCanvas(self)
            canvas.main_window = self
            canvas.set_tool("select")
            canvas.load_data(cv_data["content"])
            self.canvas_tabs.addTab(canvas, cv_data["title"])
        for txt_data in data.get("texts", []):
            panel = TextPanel(self)
            panel.load_data(txt_data["content"])
            self.text_tabs.addTab(panel, txt_data["title"])
        if self.canvas_tabs.count() > 0: self.active_canvas = self.canvas_tabs.widget(0)
        else: self._new_canvas_tab()
        if self.text_tabs.count() == 0: self._new_text_tab()
        self.start_editor()
        self.statusBar().showMessage(f"已载入项目：{path}")
        self.is_dirty = False
        self.update_title()
    def save_project(self):
        if not self.current_project_path: return self.save_project_as()
        for fw in list(self.float_windows): self.dock_back(fw)
        data = {"canvases": [], "texts": []}
        for i in range(self.canvas_tabs.count()):
            cv = self.canvas_tabs.widget(i)
            title = self.canvas_tabs.tabText(i)
            data["canvases"].append({"title": title, "content": cv.get_data()})
        for i in range(self.text_tabs.count()):
            txt = self.text_tabs.widget(i)
            title = self.text_tabs.tabText(i)
            data["texts"].append({"title": title, "content": txt.get_data()})
        try:
            with open(self.current_project_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.is_dirty = False
            self.update_title()
            self.statusBar().showMessage(f"已保存：{self.current_project_path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：\n{e}")
    def save_project_as(self):
        for fw in list(self.float_windows): self.dock_back(fw)
        path, _ = QFileDialog.getSaveFileName(self, "保存项目", "未命名项目" + DEFAULT_PROJECT_EXT, f"MathPad 项目 (*{DEFAULT_PROJECT_EXT})")
        if not path: return
        self.current_project_path = path
        self.is_dirty = True
        self.save_project()
    def get_canvas(self):
        if self.canvas_tabs.count() > 0:
            c = self.canvas_tabs.currentWidget()
            if isinstance(c, MathCanvas): return c
        for fw in self.float_windows:
            if isinstance(fw.widget, MathCanvas): return fw.widget
        return getattr(self, 'active_canvas', None)
    def _new_canvas_tab(self):
        canvas = MathCanvas(self)
        canvas.main_window = self
        canvas.set_tool("select")
        self.canvas_tabs.addTab(canvas, f"画图 {self.canvas_tabs.count() + 1}")
        self.canvas_tabs.setCurrentWidget(canvas)
        self.active_canvas = canvas
        self.sync_toolbar()
        self.mark_dirty()
    def _new_text_tab(self):
        panel = TextPanel(self)
        self.text_tabs.addTab(panel, f"文字 {self.text_tabs.count() + 1}")
        self.text_tabs.setCurrentWidget(panel)
        self.mark_dirty()
    def dock_back(self, fw):
        if fw._closing_by_dock: return
        fw._closing_by_dock = True
        widget = fw.widget
        widget.setParent(None)
        title = fw.title_label.text()
        if fw.source_tab == self.canvas_tabs:
            self.canvas_tabs.addTab(widget, title)
            self.canvas_tabs.setCurrentWidget(widget)
            self.active_canvas = widget
        else:
            self.text_tabs.addTab(widget, title)
            self.text_tabs.setCurrentWidget(widget)
        if fw in self.float_windows: self.float_windows.remove(fw)
        fw.close()
        fw.deleteLater()
    def sync_toolbar(self):
        c = self.get_canvas()
        if not c: return
        if hasattr(self, 'color_btn'):
            self.color_btn.setStyleSheet(f"background-color: {c.pen.color().name()}; color: white;")
            self.color_btn.setProperty("color", c.pen.color())
        if hasattr(self, 'width_box'):
            self.width_box.blockSignals(True)
            self.width_box.setValue(c.pen.width())
            self.width_box.blockSignals(False)
        if hasattr(self, 'style_box'):
            self.style_box.blockSignals(True)
            self.style_box.setCurrentText("虚线" if c.pen.style() == Qt.DashLine else "实线")
            self.style_box.blockSignals(False)
        if hasattr(self, 'tool_actions') and c.tool in self.tool_actions:
            self.tool_actions[c.tool].setChecked(True)
    def _act(self, text, slot=None, shortcut=None, checkable=False, tip=None):
        a = QAction(text, self)
        if shortcut: a.setShortcut(QKeySequence(shortcut))
        if checkable: a.setCheckable(True)
        if tip:
            a.setStatusTip(tip)
            a.setToolTip(tip)
        if slot: a.triggered.connect(slot)
        return a
    def _build_actions(self):
        self.act_new = self._act("新建项目", self.new_project, "Ctrl+N")
        self.act_load = self._act("打开项目…", self.load_project_dialog, "Ctrl+O")
        self.act_save = self._act("保存项目", self.save_project, "Ctrl+S")
        self.act_save_as = self._act("另存为…", self.save_project_as, "Ctrl+Shift+S")
        self.act_quit = self._act("退出", self.close, "Ctrl+Q")
        self.act_new_canvas = self._act("新建画布", self._new_canvas_tab)
        self.act_new_text = self._act("新建文字框", self._new_text_tab)
        self.act_import = self._act("导入图片…", self.import_image, "Ctrl+Shift+O")
        self.act_export = self._act("导出图片…", self.export_image, "Ctrl+Shift+E")
        self.act_export_all = self._act("导出图片+文字…", self.export_combined, "Ctrl+Shift+P")
        self.act_undo = self._act("撤销画图", self.do_undo)
        self.act_redo = self._act("重做画图", self.do_redo)
        self.act_clear_sh = self._act("清除当前辅助线", self.clear_shapes)
        self.act_clear_txt = self._act("清空当前文字", self.clear_text)
        self.act_zoom_in = self._act("放大", self.zoom_in)
        self.act_zoom_in.setShortcuts([QKeySequence("Ctrl+=")])
        self.act_zoom_out = self._act("缩小", self.zoom_out, "Ctrl+-")
        self.act_fit = self._act("适应窗口", self.fit_view, "Ctrl+0")
    def _build_menus(self):
        mb = self.menuBar()
        m = mb.addMenu("文件(&F)")
        m.addAction(self.act_new)
        m.addAction(self.act_load)
        m.addAction(self.act_save)
        m.addAction(self.act_save_as)
        m.addSeparator()
        m.addAction(self.act_new_canvas)
        m.addAction(self.act_new_text)
        m.addSeparator()
        for a in (self.act_import, self.act_export, self.act_export_all): m.addAction(a)
        m.addSeparator()
        m.addAction(self.act_quit)
        m = mb.addMenu("编辑(&E)")
        m.addAction(self.act_undo)
        m.addAction(self.act_redo)
        m.addSeparator()
        m.addAction(self.act_clear_sh)
        m.addAction(self.act_clear_txt)
        m = mb.addMenu("视图(&V)")
        m.addAction(self.act_zoom_in)
        m.addAction(self.act_zoom_out)
        m.addAction(self.act_fit)
        m.addSeparator()
        scale_menu = m.addMenu("界面缩放")
        for name, size in [("小", "11px"), ("中", "12px"), ("大", "14px"), ("特大", "16px")]:
            act = QAction(name, self)
            act.triggered.connect(lambda _=False, s=size: self.set_ui_scale(s))
            scale_menu.addAction(act)
        self._tool_menu = mb.addMenu("工具(&T)")
        mb.addMenu("帮助(&H)").addAction(self._act("关于", self.show_about))
    def set_ui_scale(self, font_size):
        self.setStyleSheet(STYLE_TEMPLATE.format(fs=font_size))
    def _build_toolbar(self):
        self.toolbar = QToolBar("主工具栏", self)
        tb = self.toolbar
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(tb)
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_actions = {}
        names = [("select", "拖动"), ("line", "直线"), ("polygon", "多边形"), ("circle", "圆"), ("text", "文本"), ("pan", "平移")]
        for key, label in names:
            a = QAction(make_icon(key), label, self)
            a.setCheckable(True)
            a.setToolTip(f"{label}工具")
            a.triggered.connect(lambda _c, k=key: self.set_tool(k))
            self.tool_group.addAction(a)
            tb.addAction(a)
            self.tool_actions[key] = a
            self._tool_menu.addAction(a)
        tb.addSeparator()
        tb.addAction(self.act_undo)
        tb.addAction(self.act_redo)
        tb.addSeparator()
        tb.addAction(self.act_zoom_in)
        tb.addAction(self.act_zoom_out)
        tb.addAction(self.act_fit)
        tb.addSeparator()
        tb.addWidget(QLabel(" 线宽 "))
        self.width_box = QSpinBox(self)
        self.width_box.setRange(1, 10)
        self.width_box.setValue(2)
        self.width_box.setFixedWidth(62)
        self.width_box.setSuffix(" px")
        self.width_box.valueChanged.connect(self.on_width_changed)
        tb.addWidget(self.width_box)
        tb.addWidget(QLabel(" 线型 "))
        self.style_box = QComboBox(self)
        self.style_box.addItems(["实线", "虚线"])
        self.style_box.setFixedWidth(60)
        self.style_box.currentIndexChanged.connect(self.on_style_changed)
        tb.addWidget(self.style_box)
        tb.addWidget(QLabel(" 颜色 "))
        self.color_btn = QToolButton(self)
        self.color_btn.setText("   ")
        self.color_btn.setFixedSize(QSize(24, 24))
        self.color_btn.setStyleSheet(f"background-color: {SHAPE_COLOR.name()}; border: 1px solid #999; border-radius: 3px;")
        self.color_btn.setProperty("color", SHAPE_COLOR)
        self.color_btn.clicked.connect(self.choose_color)
        tb.addWidget(self.color_btn)
    def choose_color(self):
        canvas = self.get_canvas()
        if not canvas: return
        color = QColorDialog.getColor(canvas.pen.color(), self, "选择线条颜色")
        if color.isValid():
            canvas.pen.setColor(color)
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #999; border-radius: 3px;")
            self.color_btn.setProperty("color", color)
    def on_width_changed(self, v):
        canvas = self.get_canvas()
        if canvas: canvas.pen.setWidth(v)
    def on_style_changed(self, idx):
        canvas = self.get_canvas()
        if canvas: canvas.pen.setStyle(Qt.DashLine if idx == 1 else Qt.SolidLine)
    def set_tool(self, name):
        canvas = self.get_canvas()
        if canvas: canvas.set_tool(name)
        if name in self.tool_actions: self.tool_actions[name].setChecked(True)
        tips = {"select": "拖动", "line": "直线", "polygon": "多边形", "circle": "圆", "text": "文本", "pan": "平移"}
        self.statusBar().showMessage(f"当前工具：{tips.get(name, name)}", 2000)
    def do_undo(self):
        canvas = self.get_canvas()
        if canvas and not canvas.undo(): self.statusBar().showMessage("没有可撤销的图形", 1500)
    def do_redo(self):
        canvas = self.get_canvas()
        if canvas and not canvas.redo(): self.statusBar().showMessage("没有可重做的图形", 1500)
    def clear_shapes(self):
        canvas = self.get_canvas()
        if canvas:
            canvas.clear_shapes()
            self.statusBar().showMessage("已清除当前画板的辅助线", 2000)
    def clear_text(self):
        t = self.text_tabs.currentWidget()
        if t: t.editor.clear()
    def zoom_in(self):
        canvas = self.get_canvas()
        if canvas: canvas.zoom_in()
    def zoom_out(self):
        canvas = self.get_canvas()
        if canvas: canvas.zoom_out()
    def fit_view(self):
        canvas = self.get_canvas()
        if canvas: canvas.fit_view()
    def import_image(self):
        if self.get_canvas() is None:
            QMessageBox.warning(self, "提示", "请先创建一个画图框！\n可以在左侧空白处双击或右键新建。")
            return
        canvas = self.get_canvas()
        path, _ = QFileDialog.getOpenFileName(self, "导入图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp)")
        if not path: return
        if canvas.load_image(path): 
            self.statusBar().showMessage(f"已导入：{path}", 4000)
            self.mark_dirty()
        else: 
            QMessageBox.warning(self, "提示", "无法读取该图片。")
    def export_image(self):
        canvas = self.get_canvas()
        if not canvas:
            QMessageBox.warning(self, "提示", "当前没有画图框，无法导出图片。")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出图片", "数学题配图.png", "PNG 图片 (*.png);;JPEG 图片 (*.jpg)")
        if not path: return
        img = canvas.render_image()
        if img.isNull():
            QMessageBox.warning(self, "提示", "画板上没有可导出的内容。")
            return
        if img.save(path): 
            self.statusBar().showMessage(f"已导出：{path}", 4000)
        else: 
            QMessageBox.warning(self, "提示", "保存失败。")
    def export_combined(self):
        canvas = self.get_canvas()
        if not canvas:
            QMessageBox.warning(self, "提示", "当前没有画图框，无法导出图文。")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出图片 + 文字", "数学题目.png", "PNG 图片 (*.png);;JPEG 图片 (*.jpg)")
        if not path: return
        img = canvas.render_image()
        img_w = 0 if img.isNull() else img.width()
        img_h = 0 if img.isNull() else img.height()
        t = self.text_tabs.currentWidget()
        html = ""
        if t:
            html = t.editor.toHtml()
        doc = QTextDocument()
        doc.setDefaultFont(t.editor.font() if t else QFont("Microsoft YaHei", 12))
        doc.setHtml(html)
        margin = 24
        content_w = max(img_w, 520)
        doc.setTextWidth(content_w - 2 * margin)
        text_h = doc.size().height()
        total_w = int(content_w)
        total_h = int(img_h + text_h + 3 * margin)
        out = QImage(total_w, total_h, QImage.Format_ARGB32)
        out.fill(Qt.white)
        p = QPainter(out)
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        if img_h: p.drawImage(int((total_w - img_w) / 2), margin, img)
        p.translate(margin, margin * 2 + img_h)
        doc.drawContents(p, QRectF(0, 0, content_w - 2 * margin, text_h))
        p.end()
        if out.save(path): 
            self.statusBar().showMessage(f"已导出：{path}", 4000)
        else: 
            QMessageBox.warning(self, "提示", "保存失败。")
    def show_about(self):
        QMessageBox.information(self, "关于 MathPad",
            "MathPad · 简约数学题目编辑器\n\n"
            "· 欢迎界面：新建或导入项目\n"
            "· Ctrl+S：保存项目\n"
            "· 拖出标签：按住画图或文字标签，向外拖动可独立成悬浮窗口\n"
            "· 拖回合并：拖动独立窗口顶部标题栏到原区域，可合入标签\n"
            "· 双击标签：可以重命名标签\n"
            "· 底部提示：当所有标签清空时，会提示新建或拖回\n")
    def closeEvent(self, e):
        if self.is_dirty:
            reply = QMessageBox.question(self, "未保存的项目", 
                "当前项目有未保存的修改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save)
            if reply == QMessageBox.Save:
                self.save_project()
            elif reply == QMessageBox.Cancel:
                e.ignore()
                return
        for fw in list(self.float_windows):
            if not fw._closing_by_dock:
                fw._closing_by_dock = True
                fw.close()
        super().closeEvent(e)

def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("MathPad")
        w = MainWindow()
        w.show()
        sys.exit(app.exec_())
    except Exception:
        traceback.print_exc()
        try:
            QMessageBox.critical(None, "启动失败",
                                 "程序启动时出错：\n\n" + traceback.format_exc())
        except Exception:
            pass
        input("按回车键退出...")

if __name__ == "__main__":
    main()
