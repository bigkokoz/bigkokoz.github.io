import math, cadquery as cq

# ---------- parámetros (mm) ----------
t   = 2.4      # espesor paredes torre
a   = 5.5      # mitad ancho interior pared trasera
b   = 16.0     # mitad de la cuerda frontal (donde se engancha la lámina)
d   = 14.0     # profundidad de las paredes laterales
s   = 6.0      # flecha de la curva de la lámina
ts  = 0.8      # espesor lámina
ws  = 1.4      # ancho ranura (lámina + juego)
ins = 5.0      # cuánto entra la lámina en cada ranura
H   = 152.0    # altura torre sobre la tapa
G   = 5.0      # profundidad de encaje en la tapa
TP  = 0.0      # sin tapa: la cierra la tapa superior con los touch
BW, BD = 64.0, 80.0   # base ancho (x) y fondo (y)
LID = 3.0             # espesor tapa base (placa delgada)
TH  = 36.0            # altura bandeja
BT  = 2.4             # pared bandeja
FL  = 2.0             # piso bandeja
RF  = 8.0             # radio esquinas base

R  = (2*b)**2/(8*s) + s/2
yc = d + s - R
al = math.asin(b/R)
de = ins/R
DY = -9.0   # desplazamiento torre en y para centrarla en la base

def pt(r, ang):          # ang medido desde +y, positivo hacia +x
    return (r*math.sin(ang), yc + r*math.cos(ang))

def annulus(r0, r1, a0, a1, h, z0):
    """sector de anillo entre a0 y a1 (rad), extruido h desde z0"""
    am = (a0+a1)/2
    w = (cq.Workplane("XY").workplane(offset=z0)
         .moveTo(*pt(r1, a0)).threePointArc(pt(r1, am), pt(r1, a1))
         .lineTo(*pt(r0, a1)).threePointArc(pt(r0, am), pt(r0, a0)).close())
    return w.extrude(h)

def tower():
    z0, h = -G, H + G
    th = math.atan((b-a)/d); off = t/math.cos(th)
    inner = [(-a,0),(a,0),(b,d),(-b,d)]
    outer = [(-a-t*math.tan(math.pi/4-th/2), -t), (a+t*math.tan(math.pi/4-th/2), -t),
             (b+off+ (t)*math.tan(th), d+t), (-b-off-(t)*math.tan(th), d+t)]
    # paredes = trapecio exterior - interior, recortado en y<d
    outer_s = cq.Workplane("XY").workplane(offset=z0).polyline(outer).close().extrude(h)
    inner_s = cq.Workplane("XY").workplane(offset=z0-1).polyline(inner).close().extrude(h+2)
    front_cut = cq.Workplane("XY").workplane(offset=z0-1).center(0, d+50).rect(300, 100).extrude(h+2)
    walls = outer_s.cut(inner_s).cut(front_cut)
    # orejas con la ranura curva
    bossR = annulus(R-2.7, R+2.7, al-math.radians(6), al+de+2.5/R, h, z0)
    bossL = annulus(R-2.7, R+2.7, -(al+de+2.5/R), -al+math.radians(6), h, z0)
    body = walls.union(bossR).union(bossL)
    # tapa superior: interior + zona hasta la curva
    ext = [(outer[0][0], outer[0][1]), (outer[1][0], outer[1][1]),
           (outer[1][0] + 80*math.tan(th), outer[1][1] + 80), (outer[0][0] - 80*math.tan(th), outer[0][1] + 80)]
    trap_ext = cq.Workplane("XY").workplane(offset=H-2).polyline(ext).close().extrude(2)
    disc = cq.Workplane("XY").workplane(offset=H-2).center(0, yc).circle(R-ws/2).extrude(2)
    if TP > 0:
        body = body.union(trap_ext.intersect(disc))
    # ranura de la lámina (pasante, se inserta desde arriba)
    slot = annulus(R-ws/2, R+ws/2, -(al+de), al+de, h+2, z0-1)
    body = body.cut(slot)
    # canal para la tira LED en la pared trasera
    ch = cq.Workplane("XY").workplane(offset=z0-1).center(0, -0.4).rect(10.4, 0.8+0.02).extrude(H-TP-z0+1)
    body = body.cut(ch)
    return body.translate((0, DY, 0))

def sheet_flat():
    L = R*2*(al+de) - 0.6
    return cq.Workplane("XY").box(L, H+G-0.2, ts, centered=(True, True, False)), L

def sheet_curved():
    return annulus(R-ts/2, R+ts/2, -(al+de)+0.3/R, (al+de)-0.3/R, H+G-0.2, -G).translate((0, DY, 0))

MAG_Y = (-22.0, 24.0)          # posiciones de los imanes a lo largo de las paredes laterales
TRAY_SLOT = (-16.8, -4.8)       # z global ranura imán bandeja (abajo, arriba)
LID_SLOT = (-18.2, -6.2)        # z global ranura imán lengüeta tapa
TAB_BOT = -19.4                 # z global punta de la lengüeta
usb_x = 26.67 - 37.8      # centro USB-B (Uno girado, USB hacia atrás)
pcb_y0 = -BD/2 + 6.35     # borde trasero PCB (conector al ras de la pared)
z_floor = -LID - TH + FL
z_pcb = z_floor + 3.0      # pilares de 3 mm + piso 2 mm = 5 mm de rosca para M3x6
usb_top = z_pcb + 1.6 + 10.9

def tray():
    z0 = -LID - TH
    body = (cq.Workplane("XY").workplane(offset=z0).rect(BW, BD).extrude(TH)
            .edges("|Z").fillet(RF))
    cav = (cq.Workplane("XY").workplane(offset=z0+FL).rect(BW-2*BT, BD-2*BT).extrude(TH)
           .edges("|Z").fillet(RF-BT))
    body = body.cut(cav)
    # muesca USB en la pared trasera (abierta arriba)
    nz0 = z_pcb + 1.6 - 0.5
    notch = (cq.Workplane("XY").workplane(offset=nz0).center(usb_x, -BD/2 + BT/2)
             .rect(18.0, BT + 2).extrude(-LID - nz0 + 1))
    body = body.cut(notch)
    # pilares + pines para los agujeros del Uno
    holes = [(13.97, 2.54), (15.24, 50.8), (66.04, 7.62), (66.04, 35.56)]
    for ax, ay in holes:
        x, y = 26.67 - ay, pcb_y0 + ax
        body = body.union(cq.Workplane("XY").workplane(offset=z_floor - 0.1).center(x, y).circle(3.25).extrude(3.1))
        body = body.cut(cq.Workplane("XY").workplane(offset=z_floor - FL - 0.5).center(x, y).circle(1.35).extrude(FL + 3.0 + 1.0))  # agujero pasante 2,7 mm para M3 autorroscante
    # imanes 11.5 x 1.7 mm parados dentro de la pared lateral (se meten en una pausa)
    top = -LID
    xin = BW/2 - BT                     # cara interior pared (29.6)
    for sx in (1, -1):
        for yc_m in MAG_Y:
            bump = (cq.Workplane("XY").workplane(offset=top - 15).center(sx*(xin - 0.8 + 0.6), yc_m)
                    .rect(1.2, 16).extrude(15))
            body = body.union(bump)
            slot = (cq.Workplane("XY").workplane(offset=TRAY_SLOT[0]).center(sx*(xin - 0.8 + 0.5 + 1.05), yc_m)
                    .rect(2.1, 12.2).extrude(TRAY_SLOT[1] - TRAY_SLOT[0]))
            body = body.cut(slot)
    return body

def lid(tw):
    body = (cq.Workplane("XY").workplane(offset=-LID).rect(BW, BD).extrude(LID)
            .edges("|Z").fillet(RF).faces(">Z").edges().chamfer(1.2))
    # refuerzo bajo la torre para que los canales tengan 5 mm de profundidad
    pad = cq.Workplane("XY").workplane(offset=-G - 2).polyline(outline_pts(2.0)).close().extrude(G + 2 - LID + 0.01)
    body = body.union(pad)
    # labio perimetral ajustado (0.15 mm de juego)
    c = BT + 0.15
    lip_o = cq.Workplane("XY").workplane(offset=-LID-3).rect(BW-2*c, BD-2*c).extrude(3.01).edges("|Z").fillet(RF-c)
    lip_i = cq.Workplane("XY").workplane(offset=-LID-4).rect(BW-2*c-2.4, BD-2*c-2.4).extrude(5).edges("|Z").fillet(RF-c-1.2)
    lip = lip_o.cut(lip_i)
    xin = BW/2 - BT
    for sx in (1, -1):
        for yc_m in MAG_Y:
            lip = lip.cut(cq.Workplane("XY").workplane(offset=-LID-4).center(sx*(xin-1), yc_m).rect(4, 18).extrude(5))
    body = body.union(lip)
    # lengüetas con imán (enfrentan a los imanes de la bandeja)
    for sx in (1, -1):
        for yc_m in MAG_Y:
            xo = xin - 0.8 - 0.15            # cara exterior lengüeta
            tab = (cq.Workplane("XY").workplane(offset=TAB_BOT).center(sx*(xo - 1.55), yc_m)
                   .rect(3.1, 14).extrude(-LID - TAB_BOT + 0.01))
            body = body.union(tab)
            slot = (cq.Workplane("XY").workplane(offset=LID_SLOT[0]).center(sx*(xo - 0.5 - 1.05), yc_m)
                    .rect(2.1, 12.2).extrude(LID_SLOT[1] - LID_SLOT[0]))
            body = body.cut(slot)
    # lengüeta que tapa la muesca del USB por arriba
    tab_h = -LID - (usb_top + 0.6)
    tab = (cq.Workplane("XY").workplane(offset=-LID+0.01).center(usb_x, -BD/2 + BT/2 + 0.1)
           .rect(18.0 - 0.3, BT - 0.2).extrude(-tab_h - 0.01))
    body = body.union(tab)
    # canal para las paredes de la torre (huella + 0.18 mm)
    foot = tw.intersect(cq.Workplane("XY").workplane(offset=-G-0.5).rect(400, 400).extrude(G + 1.5))
    groove = foot
    for k in range(8):
        ang = k*math.pi/4
        groove = groove.union(foot.translate((0.18*math.cos(ang), 0.18*math.sin(ang), 0)))
    body = body.cut(groove)
    # canal para la lámina
    sg = annulus(R-ws/2-0.05, R+ws/2+0.05, -(al+de), al+de, G+1, -G).translate((0, DY, 0))
    body = body.cut(sg)
    # agujero para los cables de la tira
    hole = cq.Workplane("XY").workplane(offset=-G-3).center(0, DY + 3.0).rect(12, 10).extrude(G + 4)
    body = body.cut(hole)
    return body


# ---------------- tapa superior de la torre con 2 módulos touch ----------------
CAP_G   = 3.0     # profundidad de los canales que reciben la torre
CAP_FL  = 1.2     # piso sobre los canales
MOD_T   = 4.0     # alto del bolsillo: PCB + chip + puntas de pines cortadas
CAP_SK  = 0.8     # piel sobre los módulos (4 capas de 0,2)
MOD_W, MOD_D = 11.0, 14.3     # un módulo TTP223 (lado de los pines = 11 mm)
CAP_OFF = 3.0     # cuánto sobresale la tapa del contorno de la torre

def _tower_outline_poly():
    import trimesh, numpy as np
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    v, f = tower().val().tessellate(0.05, 0.1)
    m = trimesh.Trimesh(np.array([[p.x, p.y, p.z] for p in v]), np.array(f))
    sec = m.section(plane_origin=[0, 0, 100], plane_normal=[0, 0, 1])
    polys = [Polygon(e[:, :2]) for e in sec.discrete]
    u = unary_union([p.buffer(0) for p in polys])
    return u

_OUTLINE_CACHE = {}
def outline_pts(off):
    """contorno torre+lámina agrandado 'off' mm (lista de puntos xy)"""
    if off in _OUTLINE_CACHE: return _OUTLINE_CACHE[off]
    from shapely.geometry import Polygon, Point
    from shapely.ops import unary_union
    walls = _tower_outline_poly()
    c = (0, yc + DY)
    ring = Point(c).buffer(R + ws/2 + 0.2, 256).difference(Point(c).buffer(R - ws/2 - 0.2, 256))
    wedge = Polygon([c, (c[0] + 80*math.sin(-(al+de)), c[1] + 80*math.cos(-(al+de))), (c[0], c[1] + 90), (c[0] + 80*math.sin(al+de), c[1] + 80*math.cos(al+de))])
    out = unary_union([walls.buffer(off, join_style=1), ring.intersection(wedge).buffer(off, join_style=1)])
    if out.geom_type != "Polygon":
        out = max(out.geoms, key=lambda g: g.area)
    pts = list(Polygon(out.exterior).simplify(0.05).exterior.coords)[:-1]
    _OUTLINE_CACHE[off] = pts
    return pts

def top_cap():
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from shapely.geometry import Point
    walls = _tower_outline_poly()
    c = (0, yc + DY)
    ring = Point(c).buffer(R + ws/2 + 0.2, 256).difference(Point(c).buffer(R - ws/2 - 0.2, 256))
    import shapely.affinity as aff
    wedge = Polygon([c, (c[0] + 80*math.sin(-(al+de)), c[1] + 80*math.cos(-(al+de))), (c[0], c[1] + 90), (c[0] + 80*math.sin(al+de), c[1] + 80*math.cos(al+de))])
    sheet = ring.intersection(wedge)
    out = unary_union([walls.buffer(CAP_OFF, join_style=1), sheet.buffer(CAP_OFF, join_style=1)])
    if out.geom_type != "Polygon":
        out = max(out.geoms, key=lambda g: g.area)
    out = Polygon(out.exterior).simplify(0.05)
    pts = list(out.exterior.coords)[:-1]
    Hc = CAP_G + CAP_FL + MOD_T + CAP_SK
    z0 = H
    body = cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(Hc)
    body = body.faces(">Z").edges().chamfer(0.8)
    # canales para las paredes de la torre (+0.18) y la lámina
    tw = tower()
    foot = tw.intersect(cq.Workplane("XY").workplane(offset=H - CAP_G - 0.5).rect(400, 400).extrude(CAP_G + 0.5)).translate((0, 0, CAP_G))
    groove = foot
    for k in range(8):
        ang = k*math.pi/4
        groove = groove.union(foot.translate((0.18*math.cos(ang), 0.18*math.sin(ang), 0)))
    body = body.cut(groove)
    body = body.cut(annulus(R-ws/2-0.05, R+ws/2+0.05, -(al+de), al+de, CAP_G + 0.01, z0 - 0.01).translate((0, DY, 0)))
    # un bolsillo para 2 módulos lado a lado (sueltos o todavía pegados en el panel)
    zp = z0 + CAP_G + CAP_FL
    PW, PD = 2*MOD_W + 0.6, MOD_D + 0.5
    pcx, pcy = 0.0, DY + 2.0 + PD/2
    body = body.cut(cq.Workplane("XY").workplane(offset=zp).center(pcx, pcy).rect(PW, PD).extrude(MOD_T))
    # sin pausa: el bolsillo queda abierto por abajo; los módulos se meten desde abajo después de imprimir
    body = body.cut(cq.Workplane("XY").workplane(offset=z0 - 0.5).center(pcx, pcy).rect(PW, PD).extrude(zp - z0 + 0.6))
    # abertura hacia el interior de la torre (para pines/cables), dentro de las paredes
    from shapely.geometry import box as sbox, Polygon as SPoly
    walls = _tower_outline_poly()
    inner = SPoly(walls.interiors[0]) if len(walls.interiors) else None
    if inner is None:   # torre abierta adelante: interior = casco convexo menos paredes
        inner = walls.convex_hull.difference(walls.buffer(0.01))
        inner = max(inner.geoms, key=lambda g: g.area) if inner.geom_type != "Polygon" else inner
    from shapely.geometry import Point as SPt
    disc_in = SPt(0, yc + DY).buffer(R - ws/2 - 0.5, 256)
    op = inner.buffer(-0.6).intersection(disc_in).intersection(sbox(pcx - PW/2 + 1.0, pcy - PD/2 + 1.0, pcx + PW/2 - 1.0, pcy + PD/2))
    op = op if op.geom_type == "Polygon" else max(op.geoms, key=lambda g: g.area)
    body = body.cut(cq.Workplane("XY").workplane(offset=z0 - 0.5).polyline(list(op.simplify(0.05).exterior.coords)[:-1]).close().extrude(CAP_G + CAP_FL + 1))
    # marcas de toque: anillo grabado 0,3 mm sobre cada módulo
    for sx in (1, -1):
        ring = cq.Workplane("XY").workplane(offset=z0 + Hc - 0.3).center(sx*(MOD_W/2 + 0.15), pcy).circle(4.0).circle(3.2).extrude(0.4)
        body = body.cut(ring)
    return body, Hc

if __name__ == "__main__":
    import sys
    tw = tower()
    sc = sheet_curved()
    lf, L = sheet_flat()
    tr = tray()
    ld = lid(tw)
    print("R=%.2f yc=%.2f alpha=%.1fdeg  sheet flat L=%.1f x %.1f x %.1f" % (R, yc, math.degrees(al), L, H+G-0.2, ts))
    for n, p in [("torre", tw), ("lamina_curva", sc), ("bandeja", tr), ("tapa_base", ld)]:
        bb = p.val().BoundingBox(); print(n, "valid", p.val().isValid(), "bbox x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]" % (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax), "vol %.0f" % p.val().Volume())
    # ensamblaje para Fusion (STEP)
    asm = cq.Assembly(name="lampara_sonido")
    asm.add(tr, name="bandeja", color=cq.Color(0.45, 0.25, 0.6))
    asm.add(ld, name="tapa_base", color=cq.Color(0.55, 0.35, 0.7))
    asm.add(tw, name="torre", color=cq.Color(0.08, 0.08, 0.08))
    asm.add(sc, name="lamina", color=cq.Color(0.97, 0.97, 0.97, 0.6))
    out = "/home/claude/lampara/out"; import os; os.makedirs(out, exist_ok=True)
    asm.save(f"{out}/lampara_sonido.step")
    # STL orientados para imprimir
    cq.exporters.export(tw.rotate((0,0,0),(1,0,0),180), f"{out}/1_torre_NEGRO_boca_abajo.stl")
    cq.exporters.export(lf, f"{out}/2_lamina_BLANCO_plana.stl")
    cq.exporters.export(tr, f"{out}/3_bandeja_base.stl")
    cq.exporters.export(ld.rotate((0,0,0),(1,0,0),180), f"{out}/4_tapa_base_boca_abajo.stl")
    print("ok")
