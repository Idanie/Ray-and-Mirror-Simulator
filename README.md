# ☀️ Sun Rays & Mirrors — Pro Edition

An interactive 2D ray tracing and light reflection simulator built entirely in Python using the `tkinter` canvas. Users can dynamically draw mirrors, position a light source, and observe high-fidelity, animated light propagation and vector reflection in real time.

---

## 🚀 Key Features

* **Interactive Mirror Placement:** Click and drag anywhere on the canvas to dynamically spawn reflective mirror segments.
* **Light Source Deployment:** Toggle to "Source" mode to reposition the primary light emitter.
* **12-Ray Fan Animation:** Instantly cast a 360-degree radial fan of 12 independent rays (spaced every 30°) with real-time flight physics.
* **Single Ray Sniper:** Fire a targeted, precise ray from the source toward any clicked point on the canvas.
* **Dynamic Speed Multipliers:** Accelerate or decelerate the propagation speed on the fly using internal tick scaling (×1, ×2, ×3).
* **Robust Physics Engine:** Employs precise segment-to-segment intersection formulas and law-of-reflection normal vectors, handling up to 1,000,000 steps per ray.
* **Immersive Visuals:** Seamless fullscreen support (Toggle via UI button or `Escape` key).

---

## 🛠️ Technology Stack & Architecture

* **Language:** Python 3
* **GUI / Graphics:** Standard `tkinter` Library (Canvas API)
* **Design Patterns:** Object-oriented architecture leveraging `dataclasses` and explicit typing hints for pristine scalability.

---

## 📦 Getting Started

### Prerequisites
Make sure you have Python 3.7+ installed. No external package installations or pip packages are required, as it utilizes Python's built-in standard library.

### Execution
Clone the repository and launch the application directly:

```bash
git clone https://github.com
cd Ray-and-Mirror-Simulator
python sun_mirrors_pro.py
```

---

## 🤝 Roadmap & Contribution Ideas (How You Can Help)

This project is fully open for community improvements! If you want to contribute, feel free to pick up any of the following tasks, refactor the code, or open an issue:

1. **Performance Improvements (Spatial Partitioning):** Currently, the ray collision system checks every segment sequentially ($O(N)$ complexity per step). Implementing a **Quadtree** or **Bounding Volume Hierarchy (BVH)** will drastically optimize calculation speeds for maps with hundreds of mirrors.
2. **Advanced Optical Elements:** Introduce complex physics models such as convex/concave parabolic surfaces, lenses with refraction indices (Snell's Law), or semi-transparent beam splitters.
3. **Graphics Modernization:** Help port the core rendering system to a hardware-accelerated pipeline like `pygame` or `ModernGL` for smoother framerates at high mirror counts.

---

## 📝 License
This project is open-source and available under the MIT License.
