import os

out_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(out_dir, "favicon.ico")

# Minimal 16x16 ICO
header = bytes([0,0, 1,0, 1,0, 16,16, 0,0, 1,0, 32,0])
size = 40 + 16*16*4 + 64
offset = 22
header += bytes([0x68, 0x04, 0, 0, 0x16, 0, 0, 0])

bmp = bytes([40,0,0,0, 16,0,0,0, 32,0,0,0, 1,0, 32,0] + [0]*24)

pixels = bytearray()
for y in range(16):
    for x in range(16):
        dx, dy = x - 7.5, y - 7.5
        dist = (dx*dx + dy*dy) ** 0.5
        if dist < 7:
            pixels.extend([255, int(max(0, min(255, 180 - dist*10))), 60, 255])
        else:
            pixels.extend([0, 0, 0, 0])

with open(out_path, "wb") as f:
    f.write(header + bmp + bytes(pixels) + bytes(64))

print(f"Created: {out_path}")
