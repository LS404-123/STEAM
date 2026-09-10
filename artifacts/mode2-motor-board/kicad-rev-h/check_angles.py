"""核對同層銅線端點：列出直角；焊盤內接合另行列出。"""
from pathlib import Path
import json
import math
import sys
import pcbnew as p


def audit(path):
    board = p.LoadBoard(str(path))
    nodes = {}
    for track in board.GetTracks():
        if type(track) is not p.PCB_TRACK:
            continue
        a, b = track.GetStart(), track.GetEnd()
        for start, end in ((a, b), (b, a)):
            key = (track.GetNetname(), track.GetLayer(), start.x, start.y)
            nodes.setdefault(key, []).append((end.x-start.x, end.y-start.y))
    corners, junctions = [], []
    for (net, layer, x, y), vectors in nodes.items():
        for i, a in enumerate(vectors):
            for c in vectors[i+1:]:
                norm = math.hypot(*a)*math.hypot(*c)
                if not norm or abs(a[0]*c[0]+a[1]*c[1])/norm > 1e-5:
                    continue
                pads = [f'{fp.GetReference()}.{pad.GetNumber()}' for fp in board.GetFootprints()
                        for pad in fp.Pads() if pad.IsOnLayer(layer) and pad.HitTest(p.VECTOR2I(x, y))]
                item = dict(net=net, layer=board.GetLayerName(layer), xy_mm=[p.ToMM(x), p.ToMM(y)], pads=pads)
                (junctions if pads or len(vectors)>2 else corners).append(item)
    return dict(board=str(path), right_angle_bends=corners, pad_or_branch_junctions=junctions)


if __name__ == '__main__':
    result = audit(Path(sys.argv[1]))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if '--assert' in sys.argv:
        assert not result['right_angle_bends'], result
