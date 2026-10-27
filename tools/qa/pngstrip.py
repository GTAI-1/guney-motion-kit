# Drop colour-management chunks (cICP, cHRM, gAMA, iCCP, sRGB) from PNGs that ffmpeg extracts from our renders.
# ffmpeg tags them BT.709 (cICP 1/1/0/1 + gAMA 0.4545); Chrome honours that and crushes the darks when a still is
# shown as a "previous frame" layer, so the cut pops. Untagged, Chrome treats the pixels as sRGB like the live frames.
# Usage: python3 qa/pngstrip.py file.png [...]
import struct, sys, zlib
DROP = {b'cICP', b'cHRM', b'gAMA', b'iCCP', b'sRGB'}
for p in sys.argv[1:]:
    b = open(p, 'rb').read(); out = [b[:8]]; i = 8; n_drop = 0
    while i < len(b):
        n, = struct.unpack('>I', b[i:i + 4]); t = b[i + 4:i + 8]
        if t in DROP: n_drop += 1
        else: out.append(b[i:i + 12 + n])
        i += 12 + n
    if n_drop: open(p, 'wb').write(b''.join(out))
    print(p, 'dropped', n_drop)
