#!/usr/bin/env python3
"""Anúncio único (não-carrossel) — Serra Montenegro.

Uso:  python3 render_anuncio.py /caminho/lote.json /caminho/saida
- Foto SEMPRE no topo, nunca atravessada por texto (preserva a autoridade do rosto).
- Sem botão de WhatsApp falso na arte (o Meta desenha o botão real).
- Gera os 3 estilos x 2 formatos (feed 1080x1350, stories 1080x1920) em JPG.
- Antes de renderizar, confere o texto contra as palavras vedadas (Provimento 205).
"""
import html, json, math, random, re, sys, unicodedata
from pathlib import Path

C = {"verde": "#829173", "musgo": "#5f694e", "dourado": "#c2a066", "carvao": "#333236", "creme": "#f3ebe4"}
W, H = 1080, 1350
M = 92
KIT = Path("/home/claude/kit-serra")

# ---------- Checagem de compliance (Provimento 205/2021) ----------
# Termos comparados sem acento e em minúsculas. Qualquer ocorrência = lote bloqueado.
VEDADOS = [
    "gratis", "gratuit", "sem custo", "de graca", "desconto", "promocao", "honorario",
    "parcel", "pix", "boleto gratis", "garantid", "garantia", "certeza", "100%",
    "com certeza", "vai receber", "vai ganhar", "ganhe", "o melhor", "a melhor",
    "os melhores", "unico", "numero 1", "n 1", "lider", "especialista n",
    "nao perca", "ultima chance", "ultimo dia", "so hoje", "corra", "imperdivel",
    "agora mesmo", "processe", "acione seu plano", "indenizacao garantida",
]

def _norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.lower())

def checar_compliance(textos):
    """Devolve a lista de (texto, termo) que violam a lista de vedados."""
    falhas = []
    for t in textos:
        n = _norm(re.sub(r"\*", "", t))
        for termo in VEDADOS:
            # início de palavra obrigatório ("unico" não pega "comunicou"; "garantid" pega garantido/a)
            if re.search(r"(?<![a-z0-9])" + re.escape(termo), n):
                falhas.append((t, termo))
    return falhas

def set_canvas(w, h):
    global W, H
    W, H = w, h

def e(s): return html.escape(str(s or ""))
def rich(s):
    s = re.sub(r"\*(.+?)\*", r"<strong>\1</strong>", e(s))
    return s.replace("\n", "<br>")

def achar_fonte(italic=False):
    pasta = KIT / "fontes"
    alvo = "Newsreader-Italic" if italic else "Newsreader["
    for p in pasta.glob("*.ttf"):
        if p.name.startswith(alvo): return p
    return None

def achar_inter():
    for p in (KIT / "fontes").glob("Inter*.ttf"): return p
    return None

def borda_rasgada(larg, seed, amp=16, passo=14):
    rnd = random.Random(seed)
    pts, x, y = [], 0, 0.0
    while x <= larg + passo:
        y += rnd.uniform(-amp * .45, amp * .45)
        y = max(-amp, min(amp, y * .85 + math.sin(x / 260.0) * amp * .35))
        pts.append((x, y)); x += rnd.randint(passo - 6, passo + 8)
    return pts

def svg_rasgo(larg, y_borda, seed, cor):
    pts = borda_rasgada(larg, seed)
    alt = 90
    def caminho(dy, fundo):
        linha = " ".join(f"L{x:.0f},{alt/2 + y + dy:.1f}" for x, y in pts)
        return f"M0,{fundo} {linha} L{larg},{fundo} Z"
    topo = y_borda - alt / 2
    sombra, fibra, papel = caminho(-9, alt), caminho(-5, alt + 60), caminho(0, alt + 60)
    return (f'<div style="position:absolute;top:{topo:.0f}px;left:0;width:{larg}px;height:{alt}px;z-index:3;'
            f'pointer-events:none"><svg width="{larg}" height="{alt}" style="display:block;overflow:visible">'
            f'<filter id="rb{seed}" x="-5%" y="-50%" width="110%" height="200%"><feGaussianBlur stdDeviation="5"/></filter>'
            f'<path d="{sombra}" fill="rgba(35,33,26,.32)" filter="url(#rb{seed})"/>'
            f'<path d="{fibra}" fill="#fbf8f3"/><path d="{papel}" fill="{cor}"/></svg></div>')

def grao(opac=.14):
    return (f'<div style="position:absolute;inset:0;z-index:20;pointer-events:none;mix-blend-mode:multiply;opacity:{opac}">'
            f'<svg width="{W}" height="{H}"><filter id="g"><feTurbulence type="fractalNoise" baseFrequency=".85" '
            f'numOctaves="3" seed="7" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .2  0 0 0 0 .19  0 0 0 0 .17  0 0 0 .55 0"/>'
            f'</filter><rect width="100%" height="100%" filter="url(#g)"/></svg></div>')

def css():
    faces = []
    nf, ni, inter = achar_fonte(False), achar_fonte(True), achar_inter()
    if nf: faces.append(f"@font-face{{font-family:'Newsreader';src:url('{nf.as_uri()}');font-weight:100 900}}")
    if ni: faces.append(f"@font-face{{font-family:'NewsreaderI';src:url('{ni.as_uri()}');font-weight:100 900}}")
    if inter: faces.append(f"@font-face{{font-family:'Inter';src:url('{inter.as_uri()}');font-weight:100 900}}")
    serif, serif_i = "'Newsreader',Georgia,serif", "'NewsreaderI',Georgia,serif"
    sans = "'Inter',system-ui,sans-serif"
    return "\n".join(faces) + f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{C['creme']}}}
body{{font-family:{sans};color:{C['carvao']};-webkit-font-smoothing:antialiased}}
.slide{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:{C['creme']}}}
.foto{{position:absolute;top:0;left:0;width:100%;object-fit:cover;filter:contrast(1.1) saturate(1.1) brightness(1.03)}}
.foto-grad{{position:absolute;left:0;right:0;bottom:0;height:46%;z-index:2;pointer-events:none;
      background:linear-gradient(to bottom, rgba(51,50,54,0) 0%, rgba(32,30,22,.24) 100%)}}
.foto-duo{{position:absolute;inset:0;z-index:2;pointer-events:none;mix-blend-mode:soft-light;opacity:.16;
      background:linear-gradient(125deg, {C['dourado']} 0%, {C['verde']} 100%)}}
.topo-marca{{position:absolute;top:40px;left:{M}px;right:{M}px;z-index:10;display:flex;justify-content:space-between;
      align-items:center;color:#fff;font-size:16px;letter-spacing:.18em;text-transform:uppercase;font-weight:600;opacity:.95;
      text-shadow:0 2px 10px rgba(0,0,0,.35)}}
.kicker{{font-size:24px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:{C['dourado']}}}
.headline{{font-family:{serif};font-weight:500;line-height:1.08;letter-spacing:-.015em;color:{C['carvao']}}}
.headline strong{{font-family:{serif_i};font-style:italic;font-weight:500;color:{C['musgo']}}}
.sub{{font-size:34px;line-height:1.3;color:rgba(51,50,54,.86);font-weight:400}}
.sub strong{{font-weight:700;color:{C['musgo']}}}
.rodape{{display:flex;justify-content:space-between;align-items:center;font-size:21px;color:{C['carvao']};opacity:.9;font-weight:500;
        border-top:1.5px solid rgba(51,50,54,.14);padding-top:22px}}
.rodape span:first-child{{font-weight:700;opacity:1}}
.aviso{{font-size:17px;color:{C['carvao']};opacity:.62}}
.cta-linha{{font-size:22px;font-weight:700;color:{C['musgo']};letter-spacing:.01em}}
.selo{{display:flex;gap:18px;align-items:flex-start}}
.selo svg{{flex-shrink:0;margin-top:3px}}
.selo span{{font-size:27px;line-height:1.3;color:{C['carvao']};font-weight:500}}
"""

def icone_check():
    return (f'<svg width="34" height="34" viewBox="0 0 34 34" fill="none">'
            f'<circle cx="17" cy="17" r="16" fill="{C["dourado"]}" fill-opacity=".14"/>'
            f'<circle cx="17" cy="17" r="15.5" stroke="{C["dourado"]}" stroke-width="1.5"/>'
            f'<path d="M9.5 17.5l5 5 10-11" stroke="{C["musgo"]}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/></svg>')

def doc_base(foto_rel, foto_altura, foco, corpo_html, seed=11, zoom=1.0):
    foto_path = (KIT / "fotos" / foto_rel).resolve().as_uri()
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{css()}</style></head>
    <body><div class="slide">
      <div style="position:absolute;top:0;left:0;width:{W}px;height:{foto_altura+70}px;overflow:hidden">
        <img class="foto" src="{foto_path}" style="height:{(foto_altura+70)}px;object-position:{foco[0]*100:.0f}% {foco[1]*100:.0f}%;
             transform:scale({zoom});transform-origin:{foco[0]*100:.0f}% {foco[1]*100:.0f}%">
        <div class="foto-duo"></div>
        <div class="foto-grad"></div>
        <div style="position:absolute;inset:0;z-index:2;pointer-events:none;
             background:radial-gradient(ellipse 60% 78% at {foco[0]*100:.0f}% {max(foco[1]*100-6,8):.0f}%,
             rgba(20,22,18,0) 40%, rgba(18,20,16,.52) 100%)"></div>
        <div style="position:absolute;inset:0;z-index:2;pointer-events:none;
             background:linear-gradient(to right, rgba(14,16,12,.42) 0%, rgba(14,16,12,0) 34%)"></div>
      </div>
      <div class="topo-marca"><span>Serra Montenegro Advocacia</span><span style="opacity:.8">@serramontenegro</span></div>
      {grao(.12)}
      {svg_rasgo(W, foto_altura, seed, C['creme'])}
      <div style="position:absolute;left:0;right:0;top:{foto_altura}px;bottom:0;padding:52px {M}px 44px;
                  display:flex;flex-direction:column;gap:22px;background:{C['creme']}">{corpo_html}</div>
      <div style="position:absolute;inset:14px;z-index:30;pointer-events:none;border:2px solid rgba(194,160,102,.55)"></div>
    </div></body></html>"""

def shot(html_doc, saida):
    """Renderiza em 2x e reduz para o tamanho final em JPG (nitidez + arquivo leve)."""
    from playwright.sync_api import sync_playwright
    from PIL import Image
    tmp = Path("/tmp/anuncio.html"); tmp.write_text(html_doc, encoding="utf-8")
    png = Path("/tmp/anuncio_2x.png")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        pg.goto(tmp.as_uri()); pg.wait_for_timeout(300)
        pg.screenshot(path=str(png)); b.close()
    Image.open(png).convert("RGB").resize((W, H), Image.LANCZOS).save(saida, "JPEG", quality=90, optimize=True, progressive=True)
    print("gerado:", saida)

def _cta(cfg):
    return cfg.get("cta") or "Entenda se você pode pagar menos."

def _rodape(advogado, oab, aviso_extra=""):
    return (f'<div class="rodape"><span>{e(advogado)} — OAB/AP {e(oab)}</span><span>serramontenegro.com</span></div>'
            f'<div class="aviso">Conteúdo informativo. Cada contrato exige análise própria.{aviso_extra}</div>')

# ---------- Estilo 1: Autoridade direta ----------
def estilo_autoridade(saida, titulo, sub, advogado, oab, foto_rel, foco=(0.5, 0.28), foto_altura=760, zoom=1.0, cta=None):
    fs = 82 if len(re.sub(r"\*","",titulo)) <= 44 else 66
    corpo = (f'<div class="kicker">Plano de saúde</div>'
             f'<h1 class="headline" style="font-size:{fs}px">{rich(titulo)}</h1>'
             f'<div class="sub">{rich(sub)}</div>'
             f'<div style="flex:1"></div>'
             f'<div class="cta-linha">{e(cta or "Entenda se você pode pagar menos.")}</div>'
             + _rodape(advogado, oab))
    shot(doc_base(foto_rel, foto_altura, foco, corpo, seed=11, zoom=zoom), saida)

# ---------- Estilo 2: Confiança com selos ----------
def estilo_selos(saida, titulo, selos, advogado, oab, foto_rel, foco=(0.5, 0.28), foto_altura=620, zoom=1.0, cta=None):
    fs = 70 if len(re.sub(r"\*","",titulo)) <= 40 else 58
    itens = "".join(f'<div class="selo">{icone_check()}<span>{rich(s)}</span></div>' for s in selos)
    corpo = (f'<div class="kicker">Reajuste de plano de saúde</div>'
             f'<h1 class="headline" style="font-size:{fs}px">{rich(titulo)}</h1>'
             f'<div style="display:flex;flex-direction:column;gap:22px;margin-top:14px">{itens}</div>'
             f'<div style="flex:1"></div>'
             f'<div class="cta-linha">{e(cta or "Entenda se você pode pagar menos.")}</div>'
             + _rodape(advogado, oab))
    shot(doc_base(foto_rel, foto_altura, foco, corpo, seed=23, zoom=zoom), saida)

# ---------- Estilo 3: Editorial com boleto ilustrativo (sem foto real/IA) ----------
def boleto_ilustrativo(largura=720, altura=460):
    """Maquete de boleto DESENHADA (não mostra operadora, CPF ou valor real).
    Blocos cinza = texto bloqueado de propósito, para não inventar dado."""
    linha = lambda w, h=22: f'<div style="width:{w}px;height:{h}px;border-radius:4px;background:rgba(51,50,54,.16)"></div>'
    barras = "".join(f'<div style="width:{random.Random(i).choice([3,5,7])}px;height:64px;background:{C["carvao"]}"></div>' for i in range(46))
    return f"""
    <div style="position:absolute;left:50%;top:54%;transform:translate(-50%,-50%) rotate(-3deg);
                width:{largura}px;background:#fff;border-radius:10px;box-shadow:0 30px 60px rgba(30,28,22,.28);
                padding:40px 44px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:26px">
        <div style="display:flex;flex-direction:column;gap:10px">{linha(230,26)}{linha(150)}</div>
        <div style="font-family:'Inter';font-size:15px;letter-spacing:.12em;text-transform:uppercase;color:rgba(51,50,54,.4);
                    font-weight:700">Plano de saúde</div>
      </div>
      <div style="display:flex;flex-direction:column;gap:14px;margin-bottom:30px">
        {linha(largura-88)}{linha(largura-160)}{linha(largura-230)}
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;border-top:2px dashed rgba(51,50,54,.18);
                  padding-top:26px">
        <div style="display:flex;flex-direction:column;gap:8px">
          <div style="font-family:'Inter';font-size:15px;letter-spacing:.1em;text-transform:uppercase;color:rgba(51,50,54,.42);font-weight:700">Valor do reajuste</div>
          {linha(170,34)}
        </div>
        <div style="width:118px;height:118px;border-radius:50%;border:3px solid {C['dourado']};display:flex;align-items:center;
                    justify-content:center;transform:rotate(11deg);flex-shrink:0;margin-left:20px">
          <span style="font-family:'Inter';font-size:16px;font-weight:800;letter-spacing:.02em;color:{C['musgo']};text-align:center;
                      line-height:1.15">ACIMA<br>DO TETO?</span>
        </div>
      </div>
      <div style="display:flex;gap:3px;margin-top:30px;height:64px;align-items:flex-end;opacity:.88">{barras}</div>
    </div>"""

def doc_base_ilustrado(elemento_html, foto_altura, corpo_html, seed=41, fundo=None):
    fundo = fundo or C["creme"]
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{css()}</style></head>
    <body><div class="slide">
      <div style="position:absolute;top:0;left:0;width:{W}px;height:{foto_altura+70}px;overflow:hidden;background:{fundo}">
        {elemento_html}
      </div>
      <div class="topo-marca" style="color:{C['carvao']};text-shadow:none;opacity:.7"><span>Serra Montenegro Advocacia</span><span>@serramontenegro</span></div>
      {grao(.08)}
      {svg_rasgo(W, foto_altura, seed, C['creme'])}
      <div style="position:absolute;left:0;right:0;top:{foto_altura}px;bottom:0;padding:52px {M}px 44px;
                  display:flex;flex-direction:column;gap:22px;background:{C['creme']}">{corpo_html}</div>
      <div style="position:absolute;inset:14px;z-index:30;pointer-events:none;border:2px solid rgba(194,160,102,.55)"></div>
    </div></body></html>"""

def estilo_editorial_boleto(saida, titulo, sub, advogado, oab, foto_altura=760, largura_boleto=760, cta=None):
    fs = 80 if len(re.sub(r"\*","",titulo)) <= 40 else 66
    corpo = (f'<div class="kicker" style="color:{C["musgo"]}">Plano de saúde</div>'
             f'<h1 class="headline" style="font-size:{fs}px">{rich(titulo)}</h1>'
             f'<div class="sub" style="background:rgba(130,145,115,.14);border-radius:6px;padding:22px 26px">{rich(sub)}</div>'
             f'<div style="flex:1"></div>'
             f'<div class="cta-linha">{e(cta or "Entenda se você pode pagar menos.")}</div>'
             + _rodape(advogado, oab, " Valores ilustrativos."))
    shot(doc_base_ilustrado(boleto_ilustrativo(largura_boleto), foto_altura, corpo, seed=41, fundo="#e9dfd4"), saida)

def renderizar_lote(cfg, saida_dir):
    """cfg = lote.json (ver SKILL.md). Gera 6 JPGs em saida_dir e devolve a lista."""
    a, s, b = cfg["autoridade"], cfg["selos"], cfg["boleto"]
    textos = [a["titulo"], a["sub"], s["titulo"], *s["selos"], b["titulo"], b["sub"],
              a.get("cta", ""), s.get("cta", ""), b.get("cta", "")]
    textos += [x.get("texto_principal", "") for x in (a, s, b)]
    falhas = checar_compliance(textos)
    if falhas:
        for t, termo in falhas:
            print(f"BLOQUEADO (termo vedado '{termo}'): {t}", file=sys.stderr)
        sys.exit(2)
    saida_dir = Path(saida_dir); saida_dir.mkdir(parents=True, exist_ok=True)
    gerados = []
    for formato, w, h in [("feed", 1080, 1350), ("stories", 1080, 1920)]:
        set_canvas(w, h)
        fa1 = 760 if formato == "feed" else 1080
        fa2 = 620 if formato == "feed" else 880
        fa3 = 640 if formato == "feed" else 910
        p1 = saida_dir / f"E1-autoridade-{formato}.jpg"
        estilo_autoridade(str(p1), a["titulo"], a["sub"], "Mateus Serra", "6612", "mateus/010A3196-anuncio.jpg",
                          foco=(0.6, 0.19), foto_altura=fa1, zoom=1.18, cta=a.get("cta"))
        p2 = saida_dir / f"E2-selos-{formato}.jpg"
        estilo_selos(str(p2), s["titulo"], s["selos"], "Ana Rita Montenegro", "6619", "rita/010A3101-anuncio.jpg",
                     foco=(0.52, 0.15), foto_altura=fa2, zoom=1.15, cta=s.get("cta"))
        p3 = saida_dir / f"E3-boleto-{formato}.jpg"
        estilo_editorial_boleto(str(p3), b["titulo"], b["sub"], "Mateus Serra", "6612",
                                foto_altura=fa3 + (70 if formato == "feed" else 170),
                                largura_boleto=700 if formato == "feed" else 800, cta=b.get("cta"))
        gerados += [p1, p2, p3]
    return gerados

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("uso: render_anuncio.py lote.json pasta_saida", file=sys.stderr); sys.exit(1)
    renderizar_lote(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), sys.argv[2])
