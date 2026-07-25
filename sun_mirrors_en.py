#!/usr/bin/env python3
"""
Sun Rays & Mirrors – Interactive Simulation (English, Clean Code)
=================================================================
- Draw mirrors by dragging on the canvas.
- Place a light source with a single click.
- Fire a single directed ray (purple) by clicking in "Single Ray" mode.
- Emit a 12‑ray fan (30° spacing) using the "Render" button.
- All rays are animated step‑by‑step; collisions are computed in real time.
- Up to 1 000 000 steps per ray.
- Speed control: ×1, ×2, ×3.
- Full‑screen toggle (button or Escape key).
"""

import tkinter as tk
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# ----------------------------------------------------------------------
#  Geometry helpers
# ----------------------------------------------------------------------

def line_intersection(p1: Tuple[float, float],
                      p2: Tuple[float, float],
                      p3: Tuple[float, float],
                      p4: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    """
    Compute the intersection point of two line segments.
    Returns (x, y) if they intersect, otherwise None.
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:          # Parallel or nearly parallel
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:   # Intersection lies on both segments
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return (ix, iy)
    return None

def reflect(vx: float, vy: float,
            nx: float, ny: float) -> Tuple[float, float]:
    """
    Reflect the incoming direction (vx, vy) off a surface with
    unit normal (nx, ny).  Formula:  v' = v - 2*(v·n)*n
    """
    dot = vx * nx + vy * ny
    return (vx - 2 * dot * nx, vy - 2 * dot * ny)

def segment_normal(p1: Tuple[float, float],
                   p2: Tuple[float, float]) -> Tuple[float, float]:
    """
    Return a unit normal vector perpendicular to the segment p1->p2.
    The normal is obtained by rotating the direction vector by +90°.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 1e-12:
        return (0.0, 0.0)
    return (-dy / length, dx / length)

def distance(p1: Tuple[float, float],
             p2: Tuple[float, float]) -> float:
    """Euclidean distance between two points."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

# ----------------------------------------------------------------------
#  Ray – the flying photon
# ----------------------------------------------------------------------

@dataclass
class Ray:
    """
    Represents one animated light ray.
    It moves step by step, reflects off mirrors, and draws its own trail.
    """
    color: str
    max_steps: int = 1_000_000

    # Current position and direction
    x: float = 0.0
    y: float = 0.0
    vx: float = 1.0
    vy: float = 0.0

    alive: bool = True
    steps_taken: int = 0
    bounces: int = 0
    last_mirror_idx: int = -1       # avoid bouncing back and forth on the same mirror

    # Internal drawing state
    prev_x: float = 0.0
    prev_y: float = 0.0
    current_segment: List[Tuple[float, float]] = field(default_factory=list)
    current_line_id: Optional[int] = None
    tip_id: Optional[int] = None
    line_ids: List[int] = field(default_factory=list)

    SEGMENT_MAX_POINTS: int = 50    # how many points before we finalise a canvas line segment

    def start(self, x: float, y: float, vx: float, vy: float) -> None:
        """Initialise (or re‑initialise) the ray from a given origin and direction."""
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

    def advance(self, canvas: tk.Canvas, nx: float, ny: float) -> None:
        """
        Move the ray to a new position (nx, ny) and draw the line segment.
        The trail is kept smooth by updating a canvas polyline.
        """
        self._add_point_to_segment(canvas, self.prev_x, self.prev_y)
        self._add_point_to_segment(canvas, nx, ny)

        self.prev_x = nx
        self.prev_y = ny
        self.x = nx
        self.y = ny
        self.steps_taken += 1

    def _add_point_to_segment(self, canvas: tk.Canvas, x: float, y: float) -> None:
        """Append a point to the current trail segment, redrawing the polyline."""
        self.current_segment.append((x, y))
        if self.current_line_id is not None:
            canvas.delete(self.current_line_id)
            self.current_line_id = None
        if len(self.current_segment) >= 2:
            flat = [coord for point in self.current_segment for coord in point]
            self.current_line_id = canvas.create_line(
                *flat, fill=self.color, width=1.5, tags="ray",
                joinstyle=tk.ROUND, capstyle=tk.ROUND)
        if len(self.current_segment) >= self.SEGMENT_MAX_POINTS:
            self._finalize_segment()

    def _finalize_segment(self) -> None:
        """Lock the current polyline segment and start a fresh one."""
        if self.current_line_id is not None:
            self.line_ids.append(self.current_line_id)
            self.current_line_id = None
            # carry over the last point as the first point of the next segment
            if self.current_segment:
                last = self.current_segment[-1]
                self.current_segment = [last]

    def finalize_all(self) -> None:
        """Called when the ray stops – ensure all drawing is finished."""
        self._finalize_segment()
        if self.current_line_id is not None:
            self.line_ids.append(self.current_line_id)
            self.current_line_id = None

    def draw_tip(self, canvas: tk.Canvas) -> None:
        """Draw a small glowing dot at the current ray head."""
        if self.tip_id is not None:
            canvas.delete(self.tip_id)
        r = 3
        self.tip_id = canvas.create_oval(
            self.x - r, self.y - r, self.x + r, self.y + r,
            fill=self.color, outline='', tags="ray_tip")

    def erase_tip(self, canvas: tk.Canvas) -> None:
        if self.tip_id is not None:
            canvas.delete(self.tip_id)
            self.tip_id = None

    def erase_all(self, canvas: tk.Canvas) -> None:
        """Remove every canvas item belonging to this ray."""
        self.erase_tip(canvas)
        for lid in self.line_ids:
            canvas.delete(lid)
        if self.current_line_id is not None:
            canvas.delete(self.current_line_id)
        self.line_ids.clear()
        self.current_line_id = None
        self.current_segment.clear()

# ----------------------------------------------------------------------
#  Main application window
# ----------------------------------------------------------------------

class SunMirrorsApp:
    """Tkinter application that manages the canvas, UI and animation loop."""

    # ------------------------------------------------------------------
    #  Constants
    # ------------------------------------------------------------------
    DEFAULT_RAY_SPEED = 4.0            # pixels per frame at speed ×1
    ANIM_DELAY = 16                    # ms ≈ 60 fps
    NUM_RAYS_FAN = 12                  # number of rays in the full‑circle fan
    RAY_MAX_STEPS = 1_000_000
    SINGLE_RAY_COLOR = "#E040FB"       # purple for manually fired rays

    # 12 distinct colours for the fan
    FAN_COLORS = ["#FF6B6B", "#FF8E53", "#FEC85C", "#A8E6CF",
                  "#4ECDC4", "#45B7D1", "#6C5CE7", "#A29BFE",
                  "#FD79A8", "#E17055", "#00CEC9", "#FDCB6E"]

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sun Rays & Mirrors Pro")

        # Model state
        self.mirrors: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
        self.source: Optional[Tuple[float, float]] = None
        self.mode: str = "mirrors"           # "mirrors" | "source" | "single_ray"

        # Temporary drawing state (mirror drag)
        self._drag_start: Optional[Tuple[float, float]] = None
        self._drag_line_id: Optional[int] = None

        # Ray animation state
        self.rays: List[Ray] = []
        self._animating = False
        self._after_id: Optional[str] = None
        self.speed_multiplier: int = 1       # ×1, ×2, ×3
        self.is_fullscreen: bool = False

        # Build the UI and configure window
        self._build_ui()
        self._configure_window()

    # ------------------------------------------------------------------
    #  Window configuration
    # ------------------------------------------------------------------
    def _configure_window(self) -> None:
        """Set initial size and switch to full‑screen."""
        self.root.geometry("1200x800")
        self.root.update_idletasks()
        self.toggle_fullscreen()          # start in full‑screen

    # ------------------------------------------------------------------
    #  UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Create the control bar and the drawing canvas."""
        # ---- Control bar ----
        ctrl = tk.Frame(self.root, bg='#f0f0f0')
        ctrl.pack(side=tk.TOP, fill=tk.X, pady=2)

        # Mode buttons
        self.btn_mirror = tk.Button(ctrl, text="🪞 Mirrors",
                                    command=self._set_mode_mirrors,
                                    relief=tk.SUNKEN, width=12)
        self.btn_mirror.pack(side=tk.LEFT, padx=3, pady=2)

        self.btn_source = tk.Button(ctrl, text="☀️ Source",
                                    command=self._set_mode_source, width=12)
        self.btn_source.pack(side=tk.LEFT, padx=3, pady=2)

        self.btn_single = tk.Button(ctrl, text="🔫 Single Ray",
                                    command=self._set_mode_single_ray, width=14)
        self.btn_single.pack(side=tk.LEFT, padx=3, pady=2)

        # Separator
        tk.Frame(ctrl, width=2, bg='#aaa').pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        # Speed selector
        tk.Label(ctrl, text="Speed:", bg='#f0f0f0').pack(side=tk.LEFT, padx=2)
        self.speed_var = tk.IntVar(value=1)
        for mult, lbl in [(1, "×1"), (2, "×2"), (3, "×3")]:
            rb = tk.Radiobutton(ctrl, text=lbl, variable=self.speed_var,
                                value=mult, command=self._on_speed_change,
                                indicatoron=False, width=4)
            rb.pack(side=tk.LEFT, padx=1)

        # Separator
        tk.Frame(ctrl, width=2, bg='#aaa').pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        # Action buttons
        self.btn_render = tk.Button(ctrl, text="✨ Render 12 Rays",
                                    command=self.render_rays,
                                    bg="#4d6bfe", fg="white", width=16)
        self.btn_render.pack(side=tk.LEFT, padx=3, pady=2)

        self.btn_stop = tk.Button(ctrl, text="⏹️ Stop",
                                  command=self.stop_animation, width=6)
        self.btn_stop.pack(side=tk.LEFT, padx=3, pady=2)

        self.btn_clear = tk.Button(ctrl, text="🧹 Clear All",
                                   command=self.clear_all, width=14)
        self.btn_clear.pack(side=tk.LEFT, padx=3, pady=2)

        # Full‑screen toggle
        self.btn_fullscreen = tk.Button(ctrl, text="⛶ Fullscreen",
                                        command=self.toggle_fullscreen, width=14)
        self.btn_fullscreen.pack(side=tk.RIGHT, padx=3, pady=2)

        # Status label
        self.lbl_status = tk.Label(ctrl, text="Mode: Draw mirrors",
                                   fg="#555", bg='#f0f0f0')
        self.lbl_status.pack(side=tk.LEFT, padx=20)

        # ---- Canvas ----
        self.canvas = tk.Canvas(self.root, bg='white', cursor="crosshair")
        self.canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.root.bind("<Escape>", lambda e: self._exit_fullscreen_if_on())

    # ------------------------------------------------------------------
    #  Mode switching
    # ------------------------------------------------------------------
    def _set_mode_mirrors(self) -> None:
        self.mode = "mirrors"
        self._update_mode_button_states()
        self.btn_mirror.config(relief=tk.SUNKEN)
        self.lbl_status.config(text="Mode: Draw mirrors (click & drag)")
        self.canvas.config(cursor="crosshair")

    def _set_mode_source(self) -> None:
        self.mode = "source"
        self._update_mode_button_states()
        self.btn_source.config(relief=tk.SUNKEN)
        self.lbl_status.config(text="Mode: Click to place the light source")
        self.canvas.config(cursor="dotbox")

    def _set_mode_single_ray(self) -> None:
        self.mode = "single_ray"
        self._update_mode_button_states()
        self.btn_single.config(relief=tk.SUNKEN)
        self.lbl_status.config(text="Mode: Click to fire a single ray from the source")
        self.canvas.config(cursor="cross")

    def _update_mode_button_states(self) -> None:
        """Reset all mode buttons to raised, then set the active one in the caller."""
        self.btn_mirror.config(relief=tk.RAISED)
        self.btn_source.config(relief=tk.RAISED)
        self.btn_single.config(relief=tk.RAISED)

    # ------------------------------------------------------------------
    #  Speed control
    # ------------------------------------------------------------------
    def _on_speed_change(self) -> None:
        """User selected a new speed multiplier."""
        self.speed_multiplier = self.speed_var.get()
        self.lbl_status.config(text=f"Animation speed: ×{self.speed_multiplier}")

    # ------------------------------------------------------------------
    #  Full‑screen handling
    # ------------------------------------------------------------------
    def toggle_fullscreen(self) -> None:
        """Toggle the full‑screen state and update the button label."""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        self.btn_fullscreen.config(
            text="⊠ Exit Fullscreen" if self.is_fullscreen else "⛶ Fullscreen")
        # Refresh canvas dimensions after the change
        self.root.update_idletasks()
        self._update_canvas_size()

    def _exit_fullscreen_if_on(self) -> None:
        """Escape key handler."""
        if self.is_fullscreen:
            self.toggle_fullscreen()

    def _update_canvas_size(self) -> None:
        """Keep a local record of the canvas size for boundary checks."""
        self.canvas_width = self.canvas.winfo_width()
        self.canvas_height = self.canvas.winfo_height()

    # ------------------------------------------------------------------
    #  Mouse event handlers
    # ------------------------------------------------------------------
    def _on_mouse_down(self, event: tk.Event) -> None:
        if self.mode == "mirrors":
            self._drag_start = (event.x, event.y)
        elif self.mode == "source":
            self._place_source(event.x, event.y)
        elif self.mode == "single_ray":
            self._fire_single_ray(event.x, event.y)

    def _on_mouse_move(self, event: tk.Event) -> None:
        """Show a dashed preview line while dragging a mirror."""
        if self.mode == "mirrors" and self._drag_start is not None:
            if self._drag_line_id is not None:
                self.canvas.delete(self._drag_line_id)
            x1, y1 = self._drag_start
            self._drag_line_id = self.canvas.create_line(
                x1, y1, event.x, event.y,
                fill='gray', dash=(5, 5), width=2)

    def _on_mouse_up(self, event: tk.Event) -> None:
        """Finalise the mirror segment."""
        if self.mode == "mirrors" and self._drag_start is not None:
            x1, y1 = self._drag_start
            x2, y2 = event.x, event.y
            if distance((x1, y1), (x2, y2)) > 5:          # ignore accidental clicks
                self.mirrors.append(((x1, y1), (x2, y2)))
                self.canvas.create_line(x1, y1, x2, y2,
                                        fill='black', width=3,
                                        capstyle=tk.ROUND, tags="mirror")
            self._drag_start = None
            if self._drag_line_id is not None:
                self.canvas.delete(self._drag_line_id)
                self._drag_line_id = None

    def _place_source(self, x: float, y: float) -> None:
        """Set the light source position and draw its marker."""
        self.canvas.delete("source_marker")
        self.source = (x, y)
        r = 8
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill='#ffaa00', outline='#cc8800',
                                width=2, tags="source_marker")
        self.canvas.create_text(x, y - 14, text="☀️",
                                font=("Arial", 14), tags="source_marker")
        self.lbl_status.config(text=f"Source placed at ({x}, {y})")

    def _fire_single_ray(self, target_x: float, target_y: float) -> None:
        """Shoot a single ray from the source toward the clicked position."""
        if not self.source:
            self.lbl_status.config(text="⚠️ Place the source first!")
            return
        sx, sy = self.source
        dx = target_x - sx
        dy = target_y - sy
        dist = math.hypot(dx, dy)
        if dist < 2:
            return
        vx = dx / dist
        vy = dy / dist

        ray = Ray(color=self.SINGLE_RAY_COLOR, max_steps=self.RAY_MAX_STEPS)
        ray.start(sx, sy, vx, vy)
        self.rays.append(ray)

        self._ensure_animation_running()
        self.lbl_status.config(text="Single ray launched! (keep clicking for more)")

    # ------------------------------------------------------------------
    #  Ray rendering (fan & animation loop)
    # ------------------------------------------------------------------
    def render_rays(self) -> None:
        """Emit a full‑circle fan of 12 rays from the source."""
        if not self.source:
            self.lbl_status.config(text="⚠️ Place the source first!")
            return

        sx, sy = self.source
        for i in range(self.NUM_RAYS_FAN):
            angle_deg = i * 360.0 / self.NUM_RAYS_FAN
            angle_rad = math.radians(angle_deg)
            vx = math.cos(angle_rad)
            vy = math.sin(angle_rad)

            ray = Ray(color=self.FAN_COLORS[i % len(self.FAN_COLORS)],
                      max_steps=self.RAY_MAX_STEPS)
            ray.start(sx, sy, vx, vy)
            self.rays.append(ray)

        self.lbl_status.config(
            text=f"Added {self.NUM_RAYS_FAN} rays. Total rays: {len(self.rays)}")
        self._ensure_animation_running()

    def _ensure_animation_running(self) -> None:
        if not self._animating:
            self._animating = True
            self._animate_loop()

    def stop_animation(self) -> None:
        """Pause the animation loop and hide all ray tips."""
        self._animating = False
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        for ray in self.rays:
            ray.erase_tip(self.canvas)

    def _animate_loop(self) -> None:
        """Main animation callback – advances all rays every ~16 ms."""
        if not self._animating:
            return

        alive_count = 0
        for ray in self.rays:
            if not ray.alive:
                continue
            alive_count += 1
            self._step_ray(ray)
            ray.draw_tip(self.canvas)

        if alive_count == 0:
            self.lbl_status.config(text="All rays have finished their journey.")
            self._animating = False
            return

        self._after_id = self.root.after(self.ANIM_DELAY, self._animate_loop)

    def _step_ray(self, ray: Ray) -> None:
        """
        Advance a single ray by one simulation step.
        Checks for mirror collisions and canvas boundaries.
        """
        x, y = ray.x, ray.y
        vx, vy = ray.vx, ray.vy
        step_size = self.DEFAULT_RAY_SPEED * self.speed_multiplier

        # Proposed next position
        nx = x + vx * step_size
        ny = y + vy * step_size

        # ---- Canvas boundary check ----
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        in_bounds = (0 <= nx <= cw and 0 <= ny <= ch)
        if not in_bounds:
            # Clamp to canvas edge and kill the ray
            nx = max(0, min(cw, nx))
            ny = max(0, min(ch, ny))
            ray.advance(self.canvas, nx, ny)
            ray.finalize_all()
            ray.alive = False
            ray.erase_tip(self.canvas)
            return

        # ---- Mirror intersection test ----
        hit_point: Optional[Tuple[float, float]] = None
        hit_idx: int = -1
        for i, (p1, p2) in enumerate(self.mirrors):
            if i == ray.last_mirror_idx:
                continue  # skip the mirror we just bounced off
            pt = line_intersection((x, y), (nx, ny), p1, p2)
            if pt is None:
                continue
            if hit_point is None or distance((x, y), pt) < distance((x, y), hit_point):
                hit_point = pt
                hit_idx = i

        if hit_point is not None:
            # Move ray exactly to the hit point, then reflect
            ray.advance(self.canvas, hit_point[0], hit_point[1])
            p1, p2 = self.mirrors[hit_idx]
            nx_norm, ny_norm = segment_normal(p1, p2)

            # Make sure the normal points against the incoming direction
            if vx * nx_norm + vy * ny_norm > 0:
                nx_norm, ny_norm = -nx_norm, -ny_norm

            new_vx, new_vy = reflect(vx, vy, nx_norm, ny_norm)
            ray.vx, ray.vy = new_vx, new_vy
            ray.last_mirror_idx = hit_idx
            ray.bounces += 1

            # Tiny offset to avoid self‑intersection
            ray.x += new_vx * 1e-3
            ray.y += new_vy * 1e-3
            ray.prev_x, ray.prev_y = ray.x, ray.y
        else:
            # No collision – free flight
            ray.advance(self.canvas, nx, ny)

        # Safety cap: stop the ray after too many steps
        if ray.steps_taken >= ray.max_steps:
            ray.finalize_all()
            ray.alive = False
            ray.erase_tip(self.canvas)

    # ------------------------------------------------------------------
    #  Clean‑up
    # ------------------------------------------------------------------
    def clear_rays(self) -> None:
        """Remove all rays (visuals + state)."""
        for ray in self.rays:
            ray.erase_all(self.canvas)
        self.rays.clear()

    def clear_all(self) -> None:
        """Reset the whole simulation: mirrors, source, rays, canvas."""
        self.stop_animation()
        self.clear_rays()
        self.mirrors.clear()
        self.source = None
        self.canvas.delete("all")
        self.lbl_status.config(text="Canvas cleared. Mode: Draw mirrors")
        self._set_mode_mirrors()

# ----------------------------------------------------------------------
#  Entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SunMirrorsApp(root)
    root.mainloop()
