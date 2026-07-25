import tkinter as tk
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

def line_intersection(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None

def reflect(vx, vy, nx, ny):
    dot = vx * nx + vy * ny
    return (vx - 2 * dot * nx, vy - 2 * dot * ny)

def normal_of_segment(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 1e-12:
        return (0.0, 0.0)
    return (-dy / length, dx / length)

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

@dataclass
class Ray:
    color: str
    max_steps: int = 1_000_000
    x: float = 0.0
    y: float = 0.0
    vx: float = 1.0
    vy: float = 0.0
    alive: bool = True
    steps_taken: int = 0
    bounces: int = 0
    last_mirror_idx: int = -1
    prev_x: float = 0.0
    prev_y: float = 0.0
    current_segment: List = field(default_factory=list)
    current_line_id: Optional[int] = None
    tip_id: Optional[int] = None
    line_ids: List[int] = field(default_factory=list)
    SEGMENT_MAX_POINTS: int = 50

    def start(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.prev_x = x
        self.prev_y = y
        self.vx = vx
        self.vy = vy
        self.alive = True
        self.steps_taken = 0
        self.bounces = 0
        self.last_mirror_idx = -1

    def advance(self, canvas, nx, ny):
        self._add_point_to_segment(canvas, self.prev_x, self.prev_y)
        self._add_point_to_segment(canvas, nx, ny)
        self.prev_x = nx
        self.prev_y = ny
        self.x = nx
        self.y = ny
        self.steps_taken += 1

    def _add_point_to_segment(self, canvas, x, y):
        self.current_segment.append((x, y))
        if self.current_line_id is not None:
            canvas.delete(self.current_line_id)
            self.current_line_id = None
        if len(self.current_segment) >= 2:
            flat = [c for p in self.current_segment for c in p]
            self.current_line_id = canvas.create_line(
                *flat, fill=self.color, width=1.5, tags="ray",
                joinstyle=tk.ROUND, capstyle=tk.ROUND)
        if len(self.current_segment) >= self.SEGMENT_MAX_POINTS:
            self._finalize_segment()

    def _finalize_segment(self):
        if self.current_line_id is not None:
            self.line_ids.append(self.current_line_id)
            self.current_line_id = None
            if self.current_segment:
                last = self.current_segment[-1]
                self.current_segment = [last]

    def finalize_all(self):
        self._finalize_segment()
        if self.current_line_id is not None:
            self.line_ids.append(self.current_line_id)
            self.current_line_id = None

    def draw_tip(self, canvas):
        if self.tip_id is not None:
            canvas.delete(self.tip_id)
        r = 3
        self.tip_id = canvas.create_oval(
            self.x - r, self.y - r, self.x + r, self.y + r,
            fill=self.color, outline='', tags="ray_tip")

    def erase_tip(self, canvas):
        if self.tip_id is not None:
            canvas.delete(self.tip_id)
            self.tip_id = None

    def erase_all(self, canvas):
        self.erase_tip(canvas)
        for lid in self.line_ids:
            canvas.delete(lid)
        if self.current_line_id is not None:
            canvas.delete(self.current_line_id)
        self.line_ids.clear()
        self.current_line_id = None
        self.current_segment.clear()

class SunMirrorsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sun Rays & Mirrors Pro")
        self.canvas_width = 1200
        self.canvas_height = 800
        self.mirrors = []
        self.source = None
        self.mode = "mirrors"
        self.drawing_line = None
        self.temp_line_id = None
        self.rays = []
        self.animating = False
        self.after_id = None
        self.ray_speed = 4.0
        self.speed_multiplier = 1
        self.anim_delay = 16
        self.num_rays = 12
        self.is_fullscreen = False

        control_frame = tk.Frame(root, bg='#f0f0f0')
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=2)

        self.mirror_btn = tk.Button(control_frame, text="Mirrors",
                                    command=self.set_mode_mirrors, relief=tk.SUNKEN, width=12)
        self.mirror_btn.pack(side=tk.LEFT, padx=3, pady=2)

        self.source_btn = tk.Button(control_frame, text="Source",
                                    command=self.set_mode_source, width=12)
        self.source_btn.pack(side=tk.LEFT, padx=3, pady=2)

        self.single_btn = tk.Button(control_frame, text="Single Ray",
                                    command=self.set_mode_single_ray, width=14)
        self.single_btn.pack(side=tk.LEFT, padx=3, pady=2)

        tk.Frame(control_frame, width=2, bg='#aaa').pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        tk.Label(control_frame, text="Speed:", bg='#f0f0f0').pack(side=tk.LEFT, padx=2)
        self.speed_var = tk.IntVar(value=1)
        self.speed1_btn = tk.Radiobutton(control_frame, text="x1", variable=self.speed_var,
                                         value=1, command=self.set_speed, indicatoron=False, width=4)
        self.speed1_btn.pack(side=tk.LEFT, padx=1)
        self.speed2_btn = tk.Radiobutton(control_frame, text="x2", variable=self.speed_var,
                                         value=2, command=self.set_speed, indicatoron=False, width=4)
        self.speed2_btn.pack(side=tk.LEFT, padx=1)
        self.speed3_btn = tk.Radiobutton(control_frame, text="x3", variable=self.speed_var,
                                         value=3, command=self.set_speed, indicatoron=False, width=4)
        self.speed3_btn.pack(side=tk.LEFT, padx=1)

        tk.Frame(control_frame, width=2, bg='#aaa').pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        self.render_btn = tk.Button(control_frame, text="Render 12",
                                    command=self.render_rays, bg="#4d6bfe", fg="white", width=16)
        self.render_btn.pack(side=tk.LEFT, padx=3, pady=2)

        self.stop_btn = tk.Button(control_frame, text="Stop",
                                  command=self.stop_animation, width=6)
        self.stop_btn.pack(side=tk.LEFT, padx=3, pady=2)

        self.clear_btn = tk.Button(control_frame, text="Clear All",
                                   command=self.clear_all, width=14)
        self.clear_btn.pack(side=tk.LEFT, padx=3, pady=2)

        self.fs_btn = tk.Button(control_frame, text="Fullscreen",
                                command=self.toggle_fullscreen, width=14)
        self.fs_btn.pack(side=tk.RIGHT, padx=3, pady=2)

        self.status_label = tk.Label(control_frame, text="Mode: draw mirrors",
                                     fg="#555", bg='#f0f0f0')
        self.status_label.pack(side=tk.LEFT, padx=20)

        self.canvas = tk.Canvas(root, bg='white', cursor="crosshair")
        self.canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.root.bind("<Escape>", lambda e: self.exit_fullscreen_if())

        self.root.update_idletasks()
        self.toggle_fullscreen()

    def _update_mode_buttons(self):
        self.mirror_btn.config(relief=tk.RAISED)
        self.source_btn.config(relief=tk.RAISED)
        self.single_btn.config(relief=tk.RAISED)

    def set_mode_mirrors(self):
        self.mode = "mirrors"
        self._update_mode_buttons()
        self.mirror_btn.config(relief=tk.SUNKEN)
        self.status_label.config(text="Mode: draw mirrors")
        self.canvas.config(cursor="crosshair")

    def set_mode_source(self):
        self.mode = "source"
        self._update_mode_buttons()
        self.source_btn.config(relief=tk.SUNKEN)
        self.status_label.config(text="Mode: click to set light source")
        self.canvas.config(cursor="dotbox")

    def set_mode_single_ray(self):
        self.mode = "single_ray"
        self._update_mode_buttons()
        self.single_btn.config(relief=tk.SUNKEN)
        self.status_label.config(text="Mode: click to fire single ray from source")
        self.canvas.config(cursor="cross")

    def set_speed(self):
        self.speed_multiplier = self.speed_var.get()
        self.status_label.config(text=f"Speed: x{self.speed_multiplier}")

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        if self.is_fullscreen:
            self.fs_btn.config(text="Exit FS")
        else:
            self.fs_btn.config(text="Fullscreen")
        self.root.update_idletasks()
        self.canvas_width = self.canvas.winfo_width()
        self.canvas_height = self.canvas.winfo_height()

    def exit_fullscreen_if(self):
        if self.is_fullscreen:
            self.toggle_fullscreen()

    def on_mouse_down(self, event):
        if self.mode == "mirrors":
            self.drawing_line = (event.x, event.y)
        elif self.mode == "source":
            self.set_source(event.x, event.y)
        elif self.mode == "single_ray":
            self.fire_single_ray(event.x, event.y)

    def on_mouse_move(self, event):
        if self.mode == "mirrors" and self.drawing_line is not None:
            if self.temp_line_id is not None:
                self.canvas.delete(self.temp_line_id)
            x1, y1 = self.drawing_line
            self.temp_line_id = self.canvas.create_line(
                x1, y1, event.x, event.y, fill='gray', dash=(5, 5), width=2)

    def on_mouse_up(self, event):
        if self.mode == "mirrors" and self.drawing_line is not None:
            x1, y1 = self.drawing_line
            x2, y2 = event.x, event.y
            if distance((x1, y1), (x2, y2)) > 5:
                self.mirrors.append(((x1, y1), (x2, y2)))
                self.canvas.create_line(x1, y1, x2, y2,
                                        fill='black', width=3,
                                        capstyle=tk.ROUND, tags="mirror")
            self.drawing_line = None
            if self.temp_line_id is not None:
                self.canvas.delete(self.temp_line_id)
                self.temp_line_id = None

    def set_source(self, x, y):
        self.canvas.delete("source_marker")
        self.source = (x, y)
        r = 8
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill='#ffaa00', outline='#cc8800',
                                width=2, tags="source_marker")
        self.canvas.create_text(x, y - 14, text="*",
                                font=("Arial", 14), tags="source_marker")
        self.status_label.config(text=f"Source at ({x}, {y})")

    def fire_single_ray(self, target_x, target_y):
        if not self.source:
            self.status_label.config(text="Set source first!")
            return
        sx, sy = self.source
        dx = target_x - sx
        dy = target_y - sy
        dist = math.hypot(dx, dy)
        if dist < 2:
            return
        vx = dx / dist
        vy = dy / dist
        ray = Ray(color="#E040FB", max_steps=1_000_000)
        ray.start(sx, sy, vx, vy)
        self.rays.append(ray)
        if not self.animating:
            self.start_animation()
        self.status_label.config(text="Single ray fired!")

    def render_rays(self):
        if not self.source:
            self.status_label.config(text="Set source first!")
            return
        sx, sy = self.source
        colors = ["#FF6B6B", "#FF8E53", "#FEC85C", "#A8E6CF",
                  "#4ECDC4", "#45B7D1", "#6C5CE7", "#A29BFE",
                  "#FD79A8", "#E17055", "#00CEC9", "#FDCB6E"]
        for i in range(self.num_rays):
            angle_deg = i * 360.0 / self.num_rays
            angle_rad = math.radians(angle_deg)
            vx = math.cos(angle_rad)
            vy = math.sin(angle_rad)
            ray = Ray(color=colors[i % len(colors)], max_steps=1_000_000)
            ray.start(sx, sy, vx, vy)
            self.rays.append(ray)
        self.status_label.config(text=f"Added {self.num_rays} rays. Total: {len(self.rays)}")
        if not self.animating:
            self.start_animation()

    def start_animation(self):
        if not self.animating:
            self.animating = True
            self._animate_loop()

    def stop_animation(self):
        self.animating = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        for ray in self.rays:
            ray.erase_tip(self.canvas)

    def _animate_loop(self):
        if not self.animating:
            return
        alive_count = 0
        for ray in self.rays:
            if not ray.alive:
                continue
            alive_count += 1
            self._step_ray(ray)
            ray.draw_tip(self.canvas)
        if alive_count == 0:
            self.status_label.config(text="All rays done.")
            self.animating = False
            return
        self.after_id = self.root.after(self.anim_delay, self._animate_loop)

    def _step_ray(self, ray):
        x, y = ray.x, ray.y
        vx, vy = ray.vx, ray.vy
        step = self.ray_speed * self.speed_multiplier
        nx = x + vx * step
        ny = y + vy * step
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        in_bounds = (0 <= nx <= cw and 0 <= ny <= ch)
        if not in_bounds:
            nx = max(0, min(cw, nx))
            ny = max(0, min(ch, ny))
            ray.advance(self.canvas, nx, ny)
            ray.finalize_all()
            ray.alive = False
            ray.erase_tip(self.canvas)
            return
        hit = None
        hit_mirror_idx = -1
        for i, (p1, p2) in enumerate(self.mirrors):
            if i == ray.last_mirror_idx:
                continue
            pt = line_intersection((x, y), (nx, ny), p1, p2)
            if pt is None:
                continue
            if hit is None or distance((x, y), pt) < distance((x, y), hit):
                hit = pt
                hit_mirror_idx = i
        if hit is not None:
            ray.advance(self.canvas, hit[0], hit[1])
            p1, p2 = self.mirrors[hit_mirror_idx]
            nx_norm, ny_norm = normal_of_segment(p1, p2)
            if vx * nx_norm + vy * ny_norm > 0:
                nx_norm, ny_norm = -nx_norm, -ny_norm
            new_vx, new_vy = reflect(vx, vy, nx_norm, ny_norm)
            ray.vx, ray.vy = new_vx, new_vy
            ray.last_mirror_idx = hit_mirror_idx
            ray.bounces += 1
            ray.x += new_vx * 1e-3
            ray.y += new_vy * 1e-3
            ray.prev_x, ray.prev_y = ray.x, ray.y
        else:
            ray.advance(self.canvas, nx, ny)
        if ray.steps_taken >= ray.max_steps:
            ray.finalize_all()
            ray.alive = False
            ray.erase_tip(self.canvas)

    def clear_rays(self):
        for ray in self.rays:
            ray.erase_all(self.canvas)
        self.rays.clear()

    def clear_all(self):
        self.stop_animation()
        self.clear_rays()
        self.mirrors.clear()
        self.source = None
        self.canvas.delete("all")
        self.status_label.config(text="Cleared. Mode: draw mirrors")
        self.set_mode_mirrors()

if __name__ == "__main__":
    root = tk.Tk()
    app = SunMirrorsApp(root)
    root.mainloop()
