import asyncio
import time
import math
import logging
import os
import random
from PIL import Image, ImageDraw
import numpy as np
from livekit import rtc

logger = logging.getLogger("visualizer")

class Ring:
    def __init__(self, radius, width, speed, color, dash_count=0, start_angle=0):
        self.radius = radius
        self.width = width
        self.base_speed = speed
        self.speed = speed
        self.color = color
        self.dash_count = dash_count
        self.angle = start_angle
        self.dash_span = 360 / (dash_count * 2) if dash_count > 0 else 360

    def update(self, loudness):
        # Spin faster with loudness
        current_speed = self.base_speed * (1.0 + loudness * 5.0) 
        self.angle += current_speed
        self.angle %= 360

    def draw(self, draw, center_x, center_y, scale_factor=1.0):
        r = self.radius * scale_factor
        bbox = [center_x - r, center_y - r, center_x + r, center_y + r]
        
        if self.dash_count == 0:
            draw.arc(bbox, start=self.angle, end=self.angle + 360, fill=self.color, width=int(self.width))
        else:
            for i in range(self.dash_count):
                s = self.angle + (i * self.dash_span * 2)
                e = s + self.dash_span
                draw.arc(bbox, start=s, end=e, fill=self.color, width=int(self.width))

class BurstLine:
    """A radial line that shoots out from the center"""
    def __init__(self, angle, speed, length, color, star_dist=50):
        self.angle = angle
        self.rad = math.radians(angle)
        self.dist = star_dist
        self.speed = speed
        self.length = length
        self.color = color # (r,g,b,a)
        self.alive = True

    def update(self):
        self.dist += self.speed
        self.length *= 0.95 # Shrink tail
        # Fade out
        r, g, b, a = self.color
        a = int(a * 0.9)
        self.color = (r, g, b, a)
        if a < 10 or self.length < 1:
            self.alive = False

    def draw(self, draw, cx, cy):
        # Calculate start and end points
        x1 = cx + math.cos(self.rad) * self.dist
        y1 = cy + math.sin(self.rad) * self.dist
        x2 = cx + math.cos(self.rad) * (self.dist + self.length)
        y2 = cy + math.sin(self.rad) * (self.dist + self.length)
        draw.line([x1, y1, x2, y2], fill=self.color, width=2)


class OrbVisualizer:
    def __init__(self, width=1280, height=720, fps=24):
        self.width = width
        self.height = height
        self.fps = fps
        self.interval = 1.0 / fps
        self.state = "listening" 
        self.is_running = False
        self.source = rtc.VideoSource(width, height)
        self._task = None
        
        self.tick = 0
        self.smoothed_amp = 0.0
        
        # Scaling factor based on height (baseline 360p)
        self.scale = self.height / 360.0
        
        # High Res Logo Loading
        self.logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "Arya.logo.png")
        self.base_image = None
        self._load_image()
        
        # Colors
        c_purple = (147, 51, 234, 255)
        c_cyan = (34, 211, 238, 200)
        c_white = (255, 255, 255, 150)
        
        # Rings - Initialized with scaled values
        s = self.scale
        self.rings = [
            Ring(65 * s, 2 * s, 3, c_cyan, 3, 0),
            Ring(80 * s, 4 * s, -1, c_purple, 0),
            Ring(95 * s, 1 * s, 1.5, c_white, 6, 45),
            Ring(110 * s, 6 * s, -0.5, (100, 50, 200, 100), 2, 90),
        ]
        
        # Burst Particles
        self.bursts = []

    def _load_image(self):
        try:
            if not os.path.exists(self.logo_path):
                # Placeholder
                self.base_image = Image.new("RGBA", (250, 250), (100, 100, 255, 255))
                return

            img = Image.open(self.logo_path).convert("RGBA")
            
            # Load at HIGHER resolution for sharpness
            # For 720p, center is ~260px. Load bigger for supersampling quality.
            target_size = 600 
            img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
            self.base_image = img
            logger.info(f"✅ Loaded High-Res logo (Thumbnail size: {target_size})")
            
        except Exception as e:
            logger.error(f"❌ Error loading image: {e}")
            self.base_image = Image.new("RGBA", (250, 250), (255, 0, 0, 255))
    
    def start(self):
        if self.is_running: return
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("🎨 Sharp Jarvis Visualizer started")

    async def stop(self):
        self.is_running = False
        if self._task: await self._task

    def set_state(self, state: str):
        self.state = state
        
    async def _run_loop(self):
        cx = self.width // 2
        cy = self.height // 2
        
        while self.is_running:
            start_time = time.time()
            self.tick += 0.05
            
            # Target Amp
            if self.state == "speaking":
                target_amp = 0.8
            elif self.state == "thinking":
                 target_amp = 0.4
            else: 
                target_amp = 0.0

            self.smoothed_amp += (target_amp - self.smoothed_amp) * 0.1
            
            # --- DYNAMICS ---
            
            # Pulse: Stronger expansion
            pulse = 1.0 + (math.sin(self.tick * 2) * 0.02)
            
            # Expansion factor for speaking
            speech_expansion = self.smoothed_amp * 0.5 
            
            total_scale = pulse + speech_expansion

            # Spawn Bursts
            if self.smoothed_amp > 0.4 and random.random() < (self.smoothed_amp * 0.3):
                # Spawn a radial line
                angle = random.randint(0, 360)
                speed = random.uniform(5, 15) * self.scale
                length = random.uniform(20, 50) * self.scale
                # Cyan or Purple bursts
                color = (34, 211, 238, 255) if random.random() > 0.5 else (147, 51, 234, 255)
                # Scale start distance
                start_dist = 80 * self.scale * total_scale
                self.bursts.append(BurstLine(angle, speed, length, color, star_dist=start_dist))

            # Update bursts
            self.bursts = [b for b in self.bursts if b.alive]
            for b in self.bursts: b.update()
            
            # Update Rings
            for r in self.rings: r.update(self.smoothed_amp)

            # --- RENDER ---
            image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 255))
            draw = ImageDraw.Draw(image)
            
            # 1. Draw Bursts (Background layer)
            for b in self.bursts: b.draw(draw, cx, cy)
            
            # 2. Draw Logo (Middle layer - BEHIND rings)
            if self.base_image:
                logo_scale = total_scale 
                
                # Base logo size at 360p was ~130px.
                # Scale it up by self.scale
                base_target_size = 130 * self.scale
                
                curr_w = int(base_target_size * logo_scale)
                curr_h = int(base_target_size * logo_scale) 
                
                # Resize for this frame using BILINEAR (faster than LANCZOS)
                logo_resized = self.base_image.resize((curr_w, curr_h), Image.Resampling.BILINEAR)
                
                lx = cx - (curr_w // 2)
                ly = cy - (curr_h // 2)
                
                image.paste(logo_resized, (lx, ly), logo_resized)

            # 3. Draw Rings (Foreground layer - ON TOP OF logo)
            for i, ring in enumerate(self.rings):
                # Progressive expansion: outer rings multiply effect
                ring_eff_scale = total_scale + (speech_expansion * (i * 0.2))
                ring.draw(draw, cx, cy, scale_factor=ring_eff_scale)
            
            # Output
            frame = rtc.VideoFrame(
                width=self.width,
                height=self.height,
                type=rtc.VideoBufferType.RGBA,
                data=image.tobytes()
            )
            self.source.capture_frame(frame)
            
            # Wait
            elapsed = time.time() - start_time
            delay = max(0, self.interval - elapsed)
            await asyncio.sleep(delay)

