/* Cerita: lapisan adegan bergambar (vektor) untuk kisah bertokoh, digambar ulang tiap frame dari SPEC.cerita.
   SPEC.cerita = { shot: [ {at, kamera:{z:[z0,z1], x, y}, langit:[panas0,panas1], matahari:{x,y,r:[r0,r1]},
     horizon, kerumunan:{n, y0, y1, seed}, debu, panas, teks:[{at, teks, sub, y}], boneka:[{x,y,s, naik, arah, wajah, mata, lengan, keringat, jalan}]} ] }
   Nilai angka boleh kunci waktu [[t,v],[t,v]] (relatif awal shot, diinterpolasi); teks boleh [[t,"nilai"],...] (berganti). */
(function () {
  const C = window.SPEC && window.SPEC.cerita; if (!C) return;
  const CERAH = !!C.cerah; // gaya cerah (6 Nov): Mahsyar keemasan, kerumunan berwarna lembut, vinyet tipis, kitab di meja kayu
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const halus = (x) => { x = clamp(x); return x * x * (3 - 2 * x); };
  const mix = (a, b, p) => a + (b - a) * p;
  const hex = (h) => { const m = /^rgb\((\d+),(\d+),(\d+)\)$/.exec(String(h).replace(/\s/g, "")); // warna hasil campur juga diterima
    return m ? m.slice(1, 4).map(Number) : [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)); };
  const warna = (a, b, p) => { const A = hex(a), B = hex(b); return `rgb(${A.map((v, i) => Math.round(mix(v, B[i], p))).join(",")})`; };
  const rng = (seed) => () => { seed |= 0; seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  // nilai bisa angka, [a,b] (dari awal ke akhir shot), atau kunci [[t,v],...]
  function v(x, t, dur, bawaan) {
    if (x == null) return bawaan;
    if (!Array.isArray(x)) return x;
    if (!Array.isArray(x[0])) { if (typeof x[0] !== "number") return x[0]; return mix(x[0], x[1], halus(t / dur)); }
    if (typeof x[0][1] !== "number") { let r = x[0][1]; x.forEach(([k, val]) => { if (t >= k) r = val; }); return r; }
    if (t <= x[0][0]) return x[0][1];
    for (let i = 1; i < x.length; i++) if (t <= x[i][0]) return mix(x[i - 1][1], x[i][1], halus((t - x[i - 1][0]) / (x[i][0] - x[i - 1][0])));
    return x[x.length - 1][1];
  }

  const SH = C.shot.slice().sort((a, b) => a.at - b.at);
  SH.forEach((s, i) => (s.akhir = i + 1 < SH.length ? SH[i + 1].at : 1e9));
  const lapis = document.createElement("div");
  lapis.id = "cerita"; lapis.style.cssText = "position:absolute;inset:0;overflow:hidden";
  document.getElementById("latar").after(lapis);
  const pf = document.createElement("div"); pf.textContent = "Aa"; pf.style.cssText = "position:absolute;left:-999px;font:700 40px Tangan"; document.body.appendChild(pf);
  const dek = document.getElementById("dekor"); if (dek) dek.style.display = "none";
  const INK = "#1d1520", KULIT = "#f2dcc2"; let BAYANG = "#3b2a40", BADAN = "#3b2a40";
  let RIM = "#ffb347", PANAS = 0;

  let MALAM = 0, PAL = null;
  // palet tempat (selain Padang Mahsyar): langit [atas, bawah], tanah [atas, bawah]
  const PALET = {
    siang: { langit: ["#4f9fe0", "#cfe9ff"], tanah: ["#8cbf6a", "#4f7d3a"] },
    gurun: { langit: ["#5fa8e3", "#fde9c8"], tanah: ["#efcd8a", "#c9964f"] },
    kota: { langit: ["#6cb6ea", "#e8f5ff"], tanah: ["#dcc9a6", "#b39a74"] },
    senja: { langit: ["#3b2a5a", "#ff9a5a"], tanah: ["#6a4a4a", "#33242c"] },
    malam: { langit: ["#070d24", "#1c2a52"], tanah: ["#2a3352", "#46506e"] },
    gua: { langit: ["#241d19", "#43362c"], tanah: ["#3d3229", "#211a15"] },
    pagi: { langit: ["#8fd0f5", "#fff1d6"], tanah: ["#9ccf6a", "#5f9a3a"] },
    sore: { langit: ["#f39a4a", "#ffe2a8"], tanah: ["#b9a45a", "#7a6a3a"] },
    subuh: { langit: ["#4a5a9a", "#f2b8a8"], tanah: ["#5a6a52", "#3a4636"] },
    mendung: { langit: ["#7f8b97", "#c4cad0"], tanah: ["#7a9a6a", "#4f6a46"] },
    neraka: { langit: ["#120403", "#5a1608"], tanah: ["#2a0e08", "#0c0403"] },
    gelap_malam: { langit: ["#05060f", "#1a1530"], tanah: ["#15121c", "#08070c"] },
  };
  const campur = (a, b, p) => { const A = a.match(/\d+/g).map(Number), B = hex(b); return `rgb(${A.map((x, i) => Math.round(mix(x, B[i], p))).join(",")})`; };
  function langit(p) {
    const L0 = CERAH ? ["#f6c26a", "#f39a3c"] : ["#2b1d3d", "#b8321c"], L1 = CERAH ? ["#fff3d6", "#ffe0a0"] : ["#8a5a6a", "#ffb04a"], T0 = CERAH ? ["#f2d6a2", "#f0c584"] : ["#b89a9a", "#e9a77d"], T1 = CERAH ? ["#d9a86a", "#cf9555"] : ["#e8d8cf", "#f4d9c2"];
    const a = campur(PAL ? warna(PAL.langit[0], PAL.langit[0], 0) : warna(L0[0], L0[1], p), "#070d24", MALAM), b = campur(PAL ? warna(PAL.langit[1], PAL.langit[1], 0) : warna(L1[0], L1[1], p), "#1c2a52", MALAM);
    return `<defs><linearGradient id="lg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>
      <radialGradient id="mg"><stop offset="0" stop-color="#fffbe6"/><stop offset=".55" stop-color="#ffd27a"/><stop offset=".75" stop-color="#ff8a2a" stop-opacity=".9"/><stop offset="1" stop-color="#ff5a1a" stop-opacity="0"/></radialGradient>
      <linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${campur(PAL ? warna(PAL.tanah[0], PAL.tanah[0], 0) : warna(T0[0], T0[1], p), "#2a3352", MALAM)}"/><stop offset="1" stop-color="${campur(PAL ? warna(PAL.tanah[1], PAL.tanah[1], 0) : warna(T1[0], T1[1], p), "#46506e", MALAM)}"/></linearGradient>
      <radialGradient id="vg" cx=".5" cy=".45" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="${CERAH ? "#5a2a10" : "#000"}" stop-opacity="${CERAH ? 0.22 : 0.55}"/></radialGradient></defs>
      <rect x="-2000" y="-2000" width="5080" height="5920" fill="url(#lg)"/>`;
  }
  function matahari(m, t, d) {
    const r = v(m.r, t, d, 80), x = v(m.x, t, d, 540), y = v(m.y, t, d, 600);
    let s = `<circle cx="${x}" cy="${y}" r="${r * 2.6}" fill="url(#mg)" opacity=".55"/>`;
    for (let i = 0; i < 12; i++) { const a = (i / 12) * Math.PI * 2 + t * 0.15, r1 = r * 1.15, r2 = r * (1.6 + 0.12 * Math.sin(t * 3 + i)); s += `<line x1="${x + Math.cos(a) * r1}" y1="${y + Math.sin(a) * r1}" x2="${x + Math.cos(a) * r2}" y2="${y + Math.sin(a) * r2}" stroke="#ffe08a" stroke-width="${r * 0.08}" stroke-linecap="round" opacity=".7"/>`; }
    return s + `<circle cx="${x}" cy="${y}" r="${r}" fill="#fff4cf" stroke="#ff9a3a" stroke-width="${Math.max(6, r * 0.06)}"/>`;
  }
  // gaya cerah: cahaya lembut di langit + berkas sinar + bukit pasir berlapis di cakrawala
  function cakrawala(h, t) {
    let s = `<defs><radialGradient id="ckg"><stop offset="0" stop-color="#fffbe8" stop-opacity=".9"/><stop offset="1" stop-color="#fff3d0" stop-opacity="0"/></radialGradient></defs><ellipse cx="540" cy="${h - 520}" rx="900" ry="620" fill="url(#ckg)" opacity="${0.7 * (1 - MALAM)}"/>`;
    for (let i = 0; i < 6; i++) { const a = -40 + i * 16 + Math.sin(t * 0.3 + i) * 3; s += `<path d="M 540 ${h - 1400} L ${540 + Math.tan((a - 6) * Math.PI / 180) * 1500} ${h + 100} L ${540 + Math.tan((a + 6) * Math.PI / 180) * 1500} ${h + 100} Z" fill="#fffbe8" opacity="${0.07 * (1 - MALAM)}"/>`; }
    const lap = [["#efc488", 70, 0.9, 3], ["#e7b475", 40, 1.3, 7]];
    lap.forEach(([w, tinggi, fr, sd]) => { const R = rng(sd); let d = `M -400 ${h + 2}`; for (let x = -400; x <= 1500; x += 120) d += ` Q ${x + 60} ${h - tinggi * (0.4 + R())} ${x + 120} ${h - tinggi * 0.3 * R()}`; s += `<path d="${d} L 1500 ${h + 4} Z" fill="${campur(warna(w, w, 0), "#2a3352", MALAM)}" opacity=".9"/>`; });
    return s;
  }
  function tanah(h, p) {
    let s = `<rect x="-2000" y="${h}" width="5080" height="4000" fill="url(#tg)"/>`;
    const r = rng(11);
    for (let i = 0; i < 26; i++) { const y = h + 30 + Math.pow(r(), 1.6) * 900, x = r() * 1080, w = 40 + (y - h) * 0.25 * r(); s += `<path d="M${x - w} ${y} q ${w * 0.5} ${-6} ${w} 0 t ${w} 0" fill="none" stroke="${INK}" stroke-width="${2 + (y - h) / 300}" opacity=".18"/>`; }
    return s;
  }

  // ---- ruang dalam (6 Nov): shot.ruang = {kosong:true} = tanpa perabot bawaan (pakai benda kasur/sofa/kursi...); "tamu"|"dapur"|"kampung"|"teras" atau {jenis, waktu: siang|sore|malam, sofa: warna, gaya}
  // lantai mulai y 1380 (kaki tokoh di 1600-1800 agar tampak berdiri di lantai). Digambar menggantikan langit+tanah.
  function ruang(R, t) {
    if (typeof R === "string") R = { jenis: R };
    const j = R.jenis || "tamu", w = R.waktu || (j === "dapur" ? "malam" : "sore"), L = 1380;
    const kaca = w === "malam" ? ["#0d1838", "#26355f"] : w === "siang" ? ["#9fd3f2", "#e6f5ff"] : ["#f7b27a", "#ffe3b8"];
    let s = `<defs><linearGradient id="rkc" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${kaca[0]}"/><stop offset="1" stop-color="${kaca[1]}"/></linearGradient>
      <radialGradient id="rlp"><stop offset="0" stop-color="#fff1c4" stop-opacity=".55"/><stop offset="1" stop-color="#fff1c4" stop-opacity="0"/></radialGradient></defs>`;
    const garis = (x1, y1, x2, y2, c = INK, w2 = 4, o = 1) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w2}" opacity="${o}"/>`;
    const jendela = (x0, y0, W, H, bingkai = "#f6efe2", tirai) => {
      let g = `<rect x="${x0}" y="${y0}" width="${W}" height="${H}" fill="url(#rkc)" stroke="${INK}" stroke-width="8"/>`;
      if (w === "malam") g += `<circle cx="${x0 + W * 0.72}" cy="${y0 + H * 0.25}" r="34" fill="#fff4cf"/>` + [0.2, 0.45, 0.8].map((a, i) => `<circle cx="${x0 + W * a}" cy="${y0 + H * (0.15 + i * 0.12)}" r="4" fill="#fff"/>`).join("");
      else g += `<path d="M ${x0} ${y0 + H * 0.78} Q ${x0 + W * 0.3} ${y0 + H * 0.6} ${x0 + W * 0.55} ${y0 + H * 0.72} T ${x0 + W} ${y0 + H * 0.66} L ${x0 + W} ${y0 + H} L ${x0} ${y0 + H} Z" fill="${j === "kampung" ? "#7fae5e" : "#9fbf8a"}" opacity=".9"/>`;
      g += `<rect x="${x0}" y="${y0}" width="${W}" height="${H}" fill="none" stroke="${bingkai}" stroke-width="22"/><rect x="${x0 - 11}" y="${y0 - 11}" width="${W + 22}" height="${H + 22}" fill="none" stroke="${INK}" stroke-width="6"/>`;
      g += garis(x0 + W / 2, y0, x0 + W / 2, y0 + H, bingkai, 16) + garis(x0, y0 + H * 0.45, x0 + W, y0 + H * 0.45, bingkai, 14);
      g += `<rect x="${x0 - 40}" y="${y0 + H + 4}" width="${W + 80}" height="26" rx="8" fill="${bingkai}" stroke="${INK}" stroke-width="6"/>`;
      if (tirai) [[x0 - 70, 1], [x0 + W - 40, -1]].forEach(([tx, a]) => { const ay = Math.sin(t * 0.9 + a) * 6;
        g += `<path d="M ${tx} ${y0 - 40} L ${tx + 110} ${y0 - 40} Q ${tx + 95 + ay} ${y0 + H * 0.5} ${tx + 120} ${y0 + H + 30} L ${tx - 10} ${y0 + H + 30} Q ${tx + 15 + ay} ${y0 + H * 0.5} ${tx} ${y0 - 40} Z" fill="${tirai}" stroke="${INK}" stroke-width="6"/>` + [30, 60, 85].map((dx) => garis(tx + dx, y0 - 30, tx + dx + 6 + ay, y0 + H + 20, INK, 3, 0.25)).join(""); });
      g += `<rect x="${x0 - 90}" y="${y0 - 56}" width="${W + 180}" height="16" rx="8" fill="#8a6a4a" stroke="${INK}" stroke-width="5"/>`;
      return g;
    };
    const lampu = (x, y, c = "#e9d2a0") => `<circle cx="${x}" cy="${y + 120}" r="${w === "malam" ? 520 : 300}" fill="url(#rlp)"/>` + garis(x, -400, x, y, INK, 5) + `<path d="M ${x - 90} ${y + 90} L ${x - 40} ${y} L ${x + 40} ${y} L ${x + 90} ${y + 90} Z" fill="${c}" stroke="${INK}" stroke-width="6"/><circle cx="${x}" cy="${y + 96}" r="16" fill="#fff6cf"/>`;
    const lantaiKayu = (c1, c2) => { let g = `<rect x="-600" y="${L}" width="2280" height="1400" fill="${c1}"/>`;
      for (let i = -14; i <= 14; i++) g += garis(540 + i * 46, L, 540 + i * 300, L + 1400, c2, 4, 0.6);
      [60, 150, 280, 460, 700].forEach((dy) => { g += garis(-600, L + dy, 1680, L + dy, c2, 3, 0.35); }); return g; };
    const ubin = (c1, c2, u = 120) => { let g = `<rect x="-600" y="${L}" width="2280" height="1400" fill="${c1}"/>`;
      for (let r = 0; r < 9; r++) { const y0 = L + Math.pow(r / 9, 1.5) * 1400, y1 = L + Math.pow((r + 1) / 9, 1.5) * 1400;
        for (let c = -10; c < 10; c++) if ((r + c) % 2 === 0) { const sx = (y) => (y - L) / 1400 * 2.6 + 1, xa = 540 + c * u * 0.5 * sx(y0), xb = 540 + (c + 1) * u * 0.5 * sx(y0), xc = 540 + (c + 1) * u * 0.5 * sx(y1), xd = 540 + c * u * 0.5 * sx(y1);
          g += `<path d="M ${xa} ${y0} L ${xb} ${y0} L ${xc} ${y1} L ${xd} ${y1} Z" fill="${c2}"/>`; } }
      return g; };
    if (j === "tamu") {
      const sofa = R.sofa || "#c66f4f", dind = R.dinding || ["#f6ead8", "#ead6bc"];
      s += `<defs><linearGradient id="rdw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${dind[0]}"/><stop offset="1" stop-color="${dind[1]}"/></linearGradient></defs><rect x="-600" y="-600" width="2280" height="${L + 600}" fill="url(#rdw)"/>`;
      s += `<rect x="-600" y="1150" width="2280" height="${L - 1150}" fill="${R.lis || "#a9b89a"}"/>` + garis(-600, 1150, 1680, 1150, INK, 6) + garis(-600, L, 1680, L, INK, 8);
      s += lantaiKayu("#c9976a", "#8e6440");
      s += jendela(640, 440, 340, 560, "#f6efe2", R.tirai || "#d98a62");
      if (w !== "malam") s += `<path d="M 640 1000 L 980 1000 L 1180 1900 L 380 1900 Z" fill="#fff3d6" opacity=".22"/>`;
      s += `<rect x="150" y="620" width="300" height="230" fill="#f3e3c6" stroke="${INK}" stroke-width="10"/><rect x="172" y="642" width="256" height="186" fill="#bcd3c8"/><path d="M 172 828 L 250 720 L 300 780 L 360 690 L 428 828 Z" fill="#7f9a86"/><circle cx="380" cy="680" r="18" fill="#ffd27a"/>`;
      if (!R.kosong) s += `<g><rect x="30" y="1080" width="540" height="200" rx="60" fill="${sofa}" stroke="${INK}" stroke-width="8"/><rect x="40" y="1230" width="520" height="140" rx="30" fill="${sofa}" stroke="${INK}" stroke-width="8"/>` + garis(300, 1240, 300, 1360, INK, 5, 0.5) +
        `<rect x="-10" y="1150" width="90" height="230" rx="40" fill="${sofa}" stroke="${INK}" stroke-width="8"/><rect x="520" y="1150" width="90" height="230" rx="40" fill="${sofa}" stroke="${INK}" stroke-width="8"/><rect x="60" y="1370" width="22" height="40" fill="${INK}"/><rect x="520" y="1370" width="22" height="40" fill="${INK}"/>` +
        `<rect x="110" y="1130" width="130" height="110" rx="30" fill="#f2d48a" stroke="${INK}" stroke-width="6" transform="rotate(-8 175 1185)"/></g>`;
      if (!R.kosong) s += `<path d="M 1040 1380 L 1010 1250 L 1130 1250 L 1100 1380 Z" fill="#c8693f" stroke="${INK}" stroke-width="6"/>` + [[-60, -260], [-20, -330], [30, -300], [70, -240], [0, -200]].map(([dx, dy], i) => `<path d="M 1070 1250 Q ${1070 + dx * 0.4} ${1250 + dy * 0.5} ${1070 + dx + Math.sin(t + i) * 6} ${1250 + dy}" stroke="#4f7d4a" stroke-width="${16 - i}" fill="none" stroke-linecap="round"/>`).join("");
      s += lampu(330, 240);
    } else if (j === "dapur") {
      s += `<rect x="-600" y="-600" width="2280" height="${L + 600}" fill="#ece6d3"/><rect x="-600" y="880" width="2280" height="360" fill="#c9d6bf"/>`;
      for (let x = -600; x < 1680; x += 80) s += garis(x, 880, x, 1240, "#a7b79c", 3);
      for (let y = 880; y < 1240; y += 80) s += garis(-600, y, 1680, y, "#a7b79c", 3);
      s += `<rect x="-60" y="460" width="760" height="330" fill="#7f9a86" stroke="${INK}" stroke-width="8"/>` + [130, 320, 510].map((x) => `<rect x="${x - 70}" y="480" width="160" height="290" fill="none" stroke="${INK}" stroke-width="4" opacity=".5"/><rect x="${x + 70}" y="600" width="10" height="50" rx="4" fill="#e9d2a0"/>`).join("");
      s += jendela(770, 470, 280, 400, "#f6efe2", null);
      s += `<rect x="-600" y="1240" width="2280" height="30" fill="#efe7d6" stroke="${INK}" stroke-width="6"/><rect x="-600" y="1270" width="2280" height="${L - 1270}" fill="#6f8a76"/>` + [-200, 120, 440, 760, 1080].map((x) => `<rect x="${x}" y="1285" width="300" height="80" fill="none" stroke="${INK}" stroke-width="4" opacity=".45"/><rect x="${x + 130}" y="1300" width="40" height="8" rx="4" fill="#e9d2a0"/>`).join("");
      if (!R.kosong) s += `<rect x="120" y="1200" width="220" height="40" rx="6" fill="#3a3a44" stroke="${INK}" stroke-width="5"/><path d="M 150 1200 L 160 1120 L 300 1120 L 310 1200 Z" fill="#b9c2c8" stroke="${INK}" stroke-width="6"/><rect x="140" y="1110" width="180" height="16" rx="6" fill="#8e979e" stroke="${INK}" stroke-width="4"/>`;
      if (!R.kosong) for (let i = 0; i < 3; i++) { const ph = (t * 0.6 + i / 3) % 1; s += `<path d="M ${200 + i * 30} ${1100 - ph * 160} q 14 -20 0 -40" stroke="#fff" stroke-width="6" fill="none" opacity="${0.5 * (1 - ph)}"/>`; }
      if (!R.kosong) s += `<rect x="470" y="1130" width="130" height="110" rx="36" fill="#f3efe6" stroke="${INK}" stroke-width="6"/><rect x="490" y="1115" width="90" height="22" rx="10" fill="#d0c8b8" stroke="${INK}" stroke-width="5"/><circle cx="535" cy="1200" r="8" fill="#ff6b6b"/>`;
      s += ubin("#e3d6bd", "#cdbd9f");
      s += lampu(540, 200, "#e9b26a");
    } else if (j === "kampung") {
      s += `<rect x="-600" y="-600" width="2280" height="${L + 600}" fill="#a8744a"/>`;
      for (let x = -600, i = 0; x < 1680; x += 72, i++) s += `<rect x="${x}" y="-600" width="72" height="${L + 600}" fill="${["#a8744a", "#9c6a42", "#b07c52"][i % 3]}"/>` + garis(x, -600, x, L, "#6e4a2e", 4, 0.7);
      s += garis(-600, L, 1680, L, INK, 8);
      s += jendela(620, 520, 320, 440, "#6e4a2e", null);
      const jm = t * 0.4, jj = t * 0.033; s += `<circle cx="300" cy="560" r="88" fill="#f6efe2" stroke="#4a3320" stroke-width="14"/>` + garis(300, 560, 300 + Math.sin(jj) * 40, 560 - Math.cos(jj) * 40, INK, 8) + garis(300, 560, 300 + Math.sin(jm) * 62, 560 - Math.cos(jm) * 62, INK, 5) + `<circle cx="300" cy="560" r="8" fill="${INK}"/>`;
      s += `<rect x="150" y="740" width="300" height="220" fill="#e9dcc0" stroke="#4a3320" stroke-width="12"/><rect x="170" y="760" width="260" height="180" fill="#c9b48a"/>` + [[230, 0.9], [300, 1], [370, 0.8]].map(([x, k]) => `<circle cx="${x}" cy="${850 - 30 * k}" r="${22 * k}" fill="#8a6a4a"/><rect x="${x - 26 * k}" y="${850}" width="${52 * k}" height="${70 * k}" rx="18" fill="#6a5040"/>`).join("");
      s += ubin("#c98d5f", "#b47a4f", 140);
      if (!R.kosong) s += `<g><rect x="60" y="1100" width="440" height="200" rx="30" fill="#c79a5a" stroke="${INK}" stroke-width="8"/>` + [0, 1, 2, 3, 4, 5].map((i) => garis(90 + i * 70, 1110, 90 + i * 70, 1290, "#8e6a3a", 4, 0.7)).join("") + `<rect x="40" y="1280" width="480" height="70" rx="20" fill="#b8884a" stroke="${INK}" stroke-width="8"/><rect x="70" y="1340" width="22" height="70" fill="${INK}"/><rect x="470" y="1340" width="22" height="70" fill="${INK}"/></g>`;
      s += lampu(820, 160, "#f2d48a");
    } else if (j === "kamar") { // kamar pemuda; R.tutup 0-1 = tirai ditutup
      const tp = clamp(R.tutup || 0);
      s += `<rect x="-600" y="-600" width="2280" height="${L + 600}" fill="${w === "malam" ? "#46527a" : "#dfe6ee"}"/>`;
      s += `<rect x="560" y="420" width="400" height="520" fill="url(#rkc)" stroke="${INK}" stroke-width="8"/>`;
      if (w === "malam") s += `<circle cx="850" cy="540" r="34" fill="#fff4cf"/>`; else s += `<path d="M 560 760 Q 760 700 960 760 L 960 940 L 560 940 Z" fill="#a9cfa0"/>`;
      s += `<rect x="560" y="420" width="400" height="520" fill="none" stroke="#f6efe2" stroke-width="20"/>` + garis(760, 420, 760, 940, "#f6efe2", 14);
      const tw = 120 + tp * 100; [[520, 1], [1000, -1]].forEach(([tx, a]) => { const x0 = a > 0 ? tx : tx - tw; s += `<path d="M ${x0} 380 L ${x0 + tw} 380 Q ${x0 + tw - 10} 700 ${x0 + tw + 8} 980 L ${x0 - 8} 980 Q ${x0 + 10} 700 ${x0} 380 Z" fill="#5b6f9e" stroke="${INK}" stroke-width="6"/>` + [0.3, 0.6].map((f) => garis(x0 + tw * f, 390, x0 + tw * f, 970, INK, 3, 0.3)).join(""); });
      s += `<rect x="440" y="360" width="640" height="16" rx="8" fill="#8a6a4a" stroke="${INK}" stroke-width="5"/>`;
      s += `<rect x="110" y="600" width="200" height="260" fill="#f2d48a" stroke="${INK}" stroke-width="8"/><circle cx="210" cy="700" r="50" fill="#e8835a"/><rect x="140" y="790" width="140" height="18" fill="#3b4a6b"/>`;
      s += lantaiKayu("#8e6a4f", "#5e4430");
      if (!R.kosong) s += `<rect x="-200" y="1120" width="640" height="260" rx="20" fill="#e9e2d6" stroke="${INK}" stroke-width="8"/><rect x="-200" y="1080" width="640" height="70" rx="20" fill="#6a8ac8" stroke="${INK}" stroke-width="8"/><rect x="250" y="1040" width="170" height="80" rx="30" fill="#fbf6ea" stroke="${INK}" stroke-width="7"/><rect x="-230" y="980" width="60" height="400" rx="14" fill="#6e4a2e" stroke="${INK}" stroke-width="7"/>`;
      if (!R.kosong) s += `<rect x="820" y="1150" width="320" height="30" fill="#b07c52" stroke="${INK}" stroke-width="6"/><rect x="840" y="1180" width="22" height="200" fill="#6e4a2e"/><rect x="1100" y="1180" width="22" height="200" fill="#6e4a2e"/><path d="M 900 1150 L 920 1060 L 980 1060" stroke="${INK}" stroke-width="7" fill="none"/><path d="M 960 1040 L 1020 1040 L 1000 1080 L 980 1080 Z" fill="#f2d48a" stroke="${INK}" stroke-width="5"/>`;
      if (!R.kosong && w === "malam") s += `<circle cx="1000" cy="1100" r="200" fill="url(#rlp)"/>`;
    } else if (j === "kantor") { // ruang kantor: dinding abu muda, jendela kaca besar dengan gedung kota, karpet, jam dinding
      s += `<rect x="-600" y="-600" width="2280" height="${L + 600}" fill="${w === "malam" ? "#3a4258" : "#e6e9ec"}"/><rect x="-600" y="1300" width="2280" height="80" fill="${w === "malam" ? "#2e3446" : "#cfd5da"}"/>`;
      s += jendela(80, 380, 920, 640, "#d8dde2", null);
      const R3 = rng(12); for (let i = 0; i < 9; i++) { const gx = 90 + i * 102, gh = 160 + R3() * 300; s += `<rect x="${gx}" y="${1020 - gh}" width="88" height="${gh}" fill="${w === "malam" ? "#1a2240" : "#9fb4c8"}" opacity=".9"/>`; for (let yy = 1030 - gh; yy < 1000; yy += 34) for (let xx = gx + 10; xx < gx + 80; xx += 22) if (R3() > 0.4) s += `<rect x="${xx}" y="${yy}" width="10" height="14" fill="${w === "malam" ? "#ffd27a" : "#e6f2fb"}" opacity="${w === "malam" ? 0.8 : 0.5}"/>`; }
      s += garis(540, 380, 540, 1020, "#d8dde2", 16) + `<rect x="80" y="380" width="920" height="640" fill="none" stroke="#d8dde2" stroke-width="22"/>`;
      const jm = t * 0.4; s += `<circle cx="1000" cy="250" r="60" fill="#fff" stroke="${INK}" stroke-width="8"/>` + garis(1000, 250, 1000 + Math.sin(jm) * 40, 250 - Math.cos(jm) * 40, INK, 6) + garis(1000, 250, 1028, 238, INK, 8);
      s += `<rect x="-600" y="${L}" width="2280" height="1400" fill="${w === "malam" ? "#4a5068" : "#9aa6b2"}"/>`; for (let i = -14; i <= 14; i++) s += garis(540 + i * 60, L, 540 + i * 380, L + 1400, "#8a96a2", 3, 0.4);
      s += lampu(540, 160, "#eef4fb");
    } else if (j === "rumah_sakit") { // kamar rumah sakit: dinding hijau muda, tirai rel, jendela, lantai ubin putih
      s += `<rect x="-600" y="-600" width="2280" height="${L + 600}" fill="${w === "malam" ? "#3e5a56" : "#d6ebe4"}"/><rect x="-600" y="1180" width="2280" height="200" fill="${w === "malam" ? "#36504c" : "#bcdcd2"}"/>`;
      s += jendela(640, 420, 320, 440, "#f6f6f2", null);
      s += garis(-600, 330, 600, 330, "#aab4c0", 8); for (let i = 0; i < 6; i++) { const tx = -80 + i * 70; s += `<path d="M ${tx} 336 Q ${tx + 35} ${700 + Math.sin(t + i) * 8} ${tx + 10} 1150 L ${tx + 70} 1150 Q ${tx + 95} 700 ${tx + 70} 336 Z" fill="${i % 2 ? "#8fc4d8" : "#a8d4e4"}" stroke="${INK}" stroke-width="4"/>`; }
      s += `<rect x="620" y="1000" width="150" height="110" rx="8" fill="#2a3036" stroke="${INK}" stroke-width="5"/><path d="M 632 1060 L 660 1060 L 672 1030 L 690 1090 L 704 1050 L 758 1050" stroke="#5aff9a" stroke-width="4" fill="none"/>`;
      s += ubin("#eef2f2", "#dde4e4", 140);
      s += lampu(300, 140, "#eef4fb");
    } else if (j === "mobil") { // bagian dalam mobil tampak samping (7 Nov): pemandangan bergeser di jendela {gerak px/dtk, waktu siang|sore|malam}
      const W2 = R.waktu || "sore", sp = R.gerak ?? 320, off = (t * sp) % 1200;
      const LG = W2 === "malam" ? ["#1b2440", "#3a4670"] : W2 === "siang" ? ["#8fd0f2", "#dff2fb"] : ["#f7b267", "#fde2b8"];
      s += `<defs><linearGradient id="rml" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${LG[0]}"/><stop offset="1" stop-color="${LG[1]}"/></linearGradient></defs><rect x="-600" y="-600" width="2280" height="2400" fill="url(#rml)"/>`;
      for (let k = -1; k < 4; k++) { const bx = k * 1200 - off; // gedung jauh (lambat) + pohon & tiang dekat (cepat)
        [[60, 260, "#c98a6a"], [260, 340, "#b07a6a"], [520, 220, "#d9a07a"], [760, 300, "#a8706a"], [980, 250, "#c99a7a"]].forEach(([x, h, c]) => { s += `<rect x="${bx * 0.5 + x}" y="${1060 - h}" width="170" height="${h}" fill="${W2 === "malam" ? "#2a3150" : c}" opacity=".85"/>`; }); }
      for (let k = -1; k < 5; k++) { const x = k * 600 - (t * sp * 1.6) % 600;
        s += `<rect x="${x}" y="760" width="14" height="340" fill="#5a4a3a"/><circle cx="${x + 300}" cy="900" r="110" fill="${W2 === "malam" ? "#22402e" : "#4f9a5a"}"/><rect x="${x + 292}" y="960" width="16" height="140" fill="#6a4a2a"/>`; }
      s += `<rect x="-600" y="1080" width="2280" height="60" fill="#6f6f78"/>`;
      // badan mobil: atap, tiang, pintu, jendela berlubang
      const IN = "#3b3f48", IN2 = "#2c3038";
      s += `<path d="M -600 -600 H 1680 V 2000 H -600 Z M 0 560 L 980 560 L 1130 1010 L 0 1010 Z" fill="${IN}" fill-rule="evenodd"/>`;
      s += `<rect x="-600" y="460" width="2280" height="100" fill="${IN2}"/><rect x="470" y="560" width="46" height="450" fill="${IN2}"/><path d="M 980 560 L 1130 1010" stroke="${IN2}" stroke-width="40"/>`;
      s += `<rect x="0" y="560" width="1130" height="10" fill="#000" opacity=".25"/><rect x="-600" y="1010" width="2280" height="18" fill="${IN2}"/>`;
      s += `<rect x="-600" y="1028" width="2280" height="${L + 600 - 1028}" fill="#454a55"/><rect x="-600" y="1540" width="2280" height="900" fill="#2a2d33"/>`;
      // kursi depan & belakang (sandaran di belakang tokoh)
      [[260, "#6a5a4a"], [720, "#6a5a4a"]].forEach(([x, c]) => { s += `<path d="M ${x - 120} 1500 L ${x - 140} 1080 Q ${x - 150} 990 ${x - 60} 990 L ${x - 10} 990 Q ${x + 40} 990 ${x + 40} 1060 L ${x + 30} 1500 Z" fill="${c}" stroke="${INK}" stroke-width="6"/><rect x="${x - 120}" y="930" width="110" height="80" rx="24" fill="${c}" stroke="${INK}" stroke-width="6"/><rect x="${x - 96}" y="1450" width="190" height="110" fill="#26292f"/><rect x="${x - 150}" y="1396" width="300" height="66" rx="26" fill="${c}" stroke="${INK}" stroke-width="6"/><path d="M ${x - 120} 1414 Q ${x} 1404 ${x + 130} 1414" stroke="#fff" stroke-width="5" opacity=".18" fill="none"/>`; });
      // dasbor
      s += `<path d="M 1000 1060 Q 1150 1040 1400 1080 L 1400 1600 L 1040 1600 Q 980 1300 1000 1060 Z" fill="${IN2}" stroke="${INK}" stroke-width="6"/><rect x="1040" y="1110" width="120" height="70" rx="10" fill="#1a1d22" stroke="${INK}" stroke-width="4"/><text x="1100" y="1158" font-family="DejaVu Sans, sans-serif" font-size="30" font-weight="700" text-anchor="middle" fill="#7ad9a6">${Math.round(42 + 6 * Math.sin(t * 0.7))}</text>`;
    } else if (j === "studio") { // studio podcast (7 Nov): dinding gelap + panel peredam, lampu dinding hangat, rak, neon tulisan {papan}
      s += `<defs><linearGradient id="rst" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1f2a3c"/><stop offset="1" stop-color="#2c3a50"/></linearGradient>
        <radialGradient id="rsg"><stop offset="0" stop-color="#ffb86b" stop-opacity=".45"/><stop offset="1" stop-color="#ffb86b" stop-opacity="0"/></radialGradient></defs><rect x="-600" y="-600" width="2280" height="${L + 600}" fill="url(#rst)"/>`;
      for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) [[-150, 1], [880, -1]].forEach(([px]) => { const x = px + c * 92, y = 300 + r * 150;
        s += `<rect x="${x}" y="${y}" width="84" height="140" rx="10" fill="${(r + c) % 2 ? "#33445e" : "#3b4e6a"}" stroke="#141b28" stroke-width="5"/>` + [0, 1, 2].map((k) => `<path d="M ${x + 8} ${y + 30 + k * 40} Q ${x + 42} ${y + 14 + k * 40} ${x + 76} ${y + 30 + k * 40}" stroke="#2a384e" stroke-width="5" fill="none"/>`).join(""); });
      [[200, 360], [880, 360]].forEach(([x, y]) => { s += `<circle cx="${x}" cy="${y + 40}" r="260" fill="url(#rsg)"/><rect x="${x - 26}" y="${y}" width="52" height="70" rx="12" fill="#ffcf8a" stroke="#141b28" stroke-width="5"/>`; });
      const ny = 0.85 + 0.15 * Math.sin(t * 3.1) * Math.sin(t * 1.3);
      if (R.papan !== false) s += `<text x="540" y="245" font-family="Caveat, 'Tangan', DejaVu Sans, sans-serif" font-weight="800" font-size="78" text-anchor="middle" fill="#ff9ad5" opacity="${ny}" stroke="#ff4fae" stroke-width="2" style="filter:drop-shadow(0 0 14px #ff4fae)">${esc(R.papan || "Ngobrol bareng Aki")}</text>`;
      s += `<rect x="-600" y="1120" width="2280" height="${L - 1120}" fill="#18212f"/>` + garis(-600, 1120, 1680, 1120, "#ff9a3a", 6, 0.8);
      [[60, 1], [1010, -1]].forEach(([x, a]) => { s += `<rect x="${x - 70}" y="1000" width="140" height="120" fill="#5a4030" stroke="#141b28" stroke-width="5"/>` + [0, 1, 2, 3].map((k) => `<rect x="${x - 60 + k * 30}" y="${1010 + (k % 2) * 10}" width="24" height="${100 - (k % 2) * 10}" fill="${["#e06a6a", "#5a8ac9", "#e0a03a", "#3f9a9a"][k]}" stroke="#141b28" stroke-width="3"/>`).join("") + `<path d="M ${x} 1000 Q ${x - 50 * a} 900 ${x - 20 * a} 850 M ${x} 1000 Q ${x + 30 * a} 920 ${x + 60 * a} 880 M ${x} 1000 Q ${x} 910 ${x + 10 * a} 860" stroke="#4f9a5a" stroke-width="18" fill="none" stroke-linecap="round"/>`; });
      s += lantaiKayu("#3a2e2a", "#2a201c");
    } else if (j === "penjara") { // sel batu, jendela kecil berjeruji tinggi + berkas cahaya
      s += `<rect x="-600" y="-600" width="2280" height="${L + 600}" fill="#6b6460"/>`;
      for (let r = 0, y = -600; y < L; y += 90, r++) for (let x = -600 + (r % 2) * 80; x < 1680; x += 160) s += `<rect x="${x + 4}" y="${y + 4}" width="152" height="82" rx="10" fill="${["#7a726c", "#706864", "#857c75"][Math.abs(r * 7 + Math.round(x / 160)) % 3]}" stroke="#4a4440" stroke-width="4"/>`;
      s += `<rect x="620" y="420" width="240" height="190" fill="#e8f4ff" stroke="${INK}" stroke-width="10"/>` + [680, 740, 800].map((x) => garis(x, 420, x, 610, INK, 12)).join("");
      s += `<path d="M 620 610 L 860 610 L 760 ${L + 300} L 240 ${L + 300} Z" fill="#fff6d8" opacity=".22"/>`;
      s += `<rect x="-600" y="${L}" width="2280" height="1400" fill="#5a534f"/>`; for (let i = 0; i < 10; i++) s += garis(-600, L + i * i * 14, 1680, L + i * i * 14, "#3f3a37", 4, 0.6);
      s += `<rect x="40" y="${L - 260}" width="230" height="${260}" fill="#3a2e28" stroke="${INK}" stroke-width="8"/>` + [80, 130, 180, 230].map((x) => garis(x, L - 250, x, L, "#8e8a86", 10)).join("") + `<rect x="60" y="1500" width="420" height="60" rx="16" fill="#b8a070" stroke="${INK}" stroke-width="6"/>`;
    } else if (j === "istana") { // aula terang: tiang marmer, tirai emas, karpet
      s += `<rect x="-600" y="-600" width="2280" height="${L + 600}" fill="#f6eedc"/>`;
      [-80, 260, 820, 1160].forEach((x) => { s += `<rect x="${x}" y="300" width="120" height="${L - 300}" fill="#efe6d2" stroke="${INK}" stroke-width="7"/><rect x="${x - 20}" y="270" width="160" height="40" fill="#e3d4b0" stroke="${INK}" stroke-width="6"/>` + [30, 60, 90].map((dx) => garis(x + dx, 320, x + dx, L - 10, "#cfc2a6", 4)).join(""); });
      s += `<path d="M 380 260 Q 540 420 700 260 L 700 200 L 380 200 Z" fill="#d9a441" stroke="${INK}" stroke-width="6"/><rect x="-600" y="180" width="2280" height="40" fill="#c99a3a" stroke="${INK}" stroke-width="6"/>`;
      s += `<rect x="-600" y="${L}" width="2280" height="1400" fill="#e9dcc0"/><path d="M 420 ${L} L 660 ${L} L 900 ${L + 1400} L 180 ${L + 1400} Z" fill="#a83a3a" stroke="#7a2424" stroke-width="6"/>`;
      s += `<circle cx="540" cy="900" r="420" fill="url(#rlp)"/>`;
    } else if (j === "teras") {
      s += `<defs><linearGradient id="rts" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${w === "siang" ? "#5fa8e3" : "#4a3a6e"}"/><stop offset=".6" stop-color="${w === "siang" ? "#a9d6f5" : "#ff9a6a"}"/><stop offset="1" stop-color="${w === "siang" ? "#e6f5ff" : "#ffd8a0"}"/></linearGradient></defs><rect x="-600" y="-600" width="2280" height="${L + 600}" fill="url(#rts)"/>`;
      s += `<circle cx="880" cy="${w === "siang" ? 600 : 900}" r="70" fill="${w === "siang" ? "#fff6cf" : "#ffe7b0"}" opacity=".9"/><path d="M -600 1180 Q 200 1080 700 1160 T 1680 1140 L 1680 ${L} L -600 ${L} Z" fill="#6a7a5a"/>`;
      s += `<rect x="-600" y="420" width="1180" height="${L - 420}" fill="#efe1c8" stroke="${INK}" stroke-width="8"/><rect x="-640" y="380" width="1260" height="60" fill="#7a4a3a" stroke="${INK}" stroke-width="8"/>`;
      s += `<rect x="80" y="760" width="220" height="${L - 760}" fill="#8a5a3a" stroke="${INK}" stroke-width="8"/><circle cx="270" cy="1080" r="10" fill="#ffd27a"/><rect x="360" y="760" width="170" height="240" fill="#ffe2a0" stroke="${INK}" stroke-width="8"/>` + garis(445, 760, 445, 1000, INK, 6);
      s += ubin("#d8c3a0", "#c4ad88");
      [[620, "#c8693f"], [980, "#9a5a3a"]].forEach(([x, c], i) => { s += `<path d="M ${x - 40} ${L} L ${x - 60} ${L - 110} L ${x + 60} ${L - 110} L ${x + 40} ${L} Z" fill="${c}" stroke="${INK}" stroke-width="6"/>` + [-50, -10, 30].map((dx, k) => `<path d="M ${x} ${L - 110} q ${dx * 0.5} -60 ${dx + Math.sin(t + k + i) * 5} -150" stroke="#4f7d4a" stroke-width="12" fill="none" stroke-linecap="round"/>`).join(""); });
    }
    return s;
  }
  function kerumunan(k, h, t) {
    const r = rng(k.seed || 5), n = k.n || 200, y0 = h + (k.y0 || 4), y1 = h + (k.y1 || 260);
    const a = [];
    for (let i = 0; i < n; i++) { const d = Math.pow(r(), 2.2); a.push({ x: -100 + r() * 1280, y: y0 + d * (y1 - y0), ph: r() * 6, kepala: r() > 0.5 }); }
    a.sort((p, q) => p.y - q.y);
    if (CERAH) { // kerumunan berwarna lembut (tanah liat/pasir, bukan hitam); jauh = memudar ke warna kabut
      const TON = ["#c98f6a", "#b47a5c", "#d9a983", "#a58474", "#c4a28a", "#b8896a", "#d8b896", "#9f7f6a"], kab = "#ffe6b8";
      return a.map((o, i) => {
        const dd = (o.y - y0) / Math.max(1, y1 - y0), sk = 0.03 + dd * (k.besar || 0.2), hh = 520 * sk, w = 110 * sk, bob = Math.sin(t * 2 + o.ph) * 2 * sk * 10;
        const tn = TON[i % TON.length], hz = 0.65 * (1 - dd), bd = campur(warna(tn, tn, 0), kab, hz), kp = campur(warna("#e9c6a2", "#e9c6a2", 0), kab, hz), sd = campur(warna(tn, "#5a3320", 0.35), kab, hz);
        return `<g transform="translate(${o.x} ${o.y + bob})">${dd > 0.4 ? `<ellipse cx="0" cy="2" rx="${w * 0.8}" ry="${w * 0.18}" fill="#7a4a2a" opacity=".18"/>` : ""}<rect x="${-w / 2}" y="${-hh * 0.72}" width="${w}" height="${hh * 0.72}" rx="${w / 2}" fill="${bd}"/><rect x="${w * 0.12}" y="${-hh * 0.7}" width="${w * 0.36}" height="${hh * 0.68}" rx="${w * 0.18}" fill="${sd}" opacity=".45"/><circle cx="0" cy="${-hh * 0.84 - (o.kepala ? 3 * sk * 10 : 0)}" r="${hh * 0.13}" fill="${kp}"/></g>`;
      }).join("");
    }
    return a.map((o) => {
      const sk = 0.03 + ((o.y - y0) / Math.max(1, y1 - y0)) * (k.besar || 0.2), hh = 520 * sk, w = 110 * sk, bob = Math.sin(t * 2 + o.ph) * 2 * sk * 10;
      const op = 0.3 + 0.55 * ((o.y - y0) / Math.max(1, y1 - y0));
      return `<g opacity="${op.toFixed(2)}" transform="translate(${o.x} ${o.y + bob})"><rect x="${-w / 2}" y="${-hh * 0.72}" width="${w}" height="${hh * 0.72}" rx="${w / 2}" fill="${BAYANG}"/><circle cx="0" cy="${-hh * 0.84 - (o.kepala ? 3 * sk * 10 : 0)}" r="${hh * 0.13}" fill="${BAYANG}"/></g>`;
    }).join("");
  }
  function debu(t, n = 40) {
    const r = rng(3); let s = "";
    for (let i = 0; i < n; i++) { const x0 = r() * 1200, y0 = r() * 1920, sp = 20 + r() * 50, z = 1.2 + r() * 3.5; const x = ((x0 + t * sp) % 1240) - 80, y = y0 - t * sp * 0.3 + Math.sin(t + i) * 20; s += `<circle cx="${x}" cy="${((y % 1920) + 1920) % 1920}" r="${z}" fill="#fff3e0" opacity="${0.15 + r() * 0.3}"/>`; }
    return s;
  }
  function panas(t, h, p) {
    let s = "";
    for (let i = 0; i < 7; i++) { const y = h - 40 - ((t * 70 + i * 90) % 600); s += `<path d="M -50 ${y} q 135 ${-14} 270 0 t 270 0 t 270 0 t 270 0 t 270 0" fill="none" stroke="#fff2cc" stroke-width="5" opacity="${0.18 * p}"/>`; }
    return s;
  }


  // tanah retak dari titik {x, y, p:[0..1]}
  function retak(r, t, d) {
    const p = v(r.p, t, d, 1), x = r.x || 540, y = r.y || 1500, R = rng(21); let s = "";
    for (let i = 0; i < 9; i++) { let px = x, py = y, a = (i / 9) * Math.PI * 2, path = `M ${px} ${py}`; const n = 6;
      for (let j = 0; j < n * p; j++) { a += (R() - 0.5) * 0.9; const l = 40 + R() * 50; px += Math.cos(a) * l; py += Math.sin(a) * l * 0.35; path += ` L ${px} ${py}`; }
      s += `<path d="${path}" fill="none" stroke="${INK}" stroke-width="${10 - i % 3 * 2}" stroke-linecap="round" stroke-linejoin="round" opacity=".85"/>`; }
    return s + `<ellipse cx="${x}" cy="${y}" rx="${220 * p}" ry="${40 * p}" fill="${INK}" opacity="${0.5 * p}"/>`;
  }
  // penampang tanah: keringat meresap ke bawah {h (atas), p:[0..1], dalam}
  function resap(r, t, d, h) {
    const p = v(r.p, t, d, 1), dalam = r.dalam || 700; let s = `<rect x="-200" y="${h}" width="1480" height="${dalam + 400}" fill="#8c5a4a"/>`;
    for (let i = 1; i < 9; i++) { const y = h + i * dalam / 8; s += `<path d="M -200 ${y} q 270 ${(i % 2 ? 1 : -1) * 18} 540 0 t 540 0 t 540 0" fill="none" stroke="#5e3a32" stroke-width="5" opacity=".6"/>`; }
    const R = rng(8);
    for (let i = 0; i < 22; i++) { const x = 40 + i * 47 + R() * 20, panjang = dalam * p * (0.75 + R() * 0.25); s += `<path d="M ${x} ${h} q ${R() * 20 - 10} ${panjang / 2} 0 ${panjang}" fill="none" stroke="#ffb15a" stroke-width="${8 + R() * 6}" stroke-linecap="round" opacity=".85"/><circle cx="${x}" cy="${h + panjang}" r="8" fill="#ffd28a"/>`; }
    return s;
  }
  // naungan: cahaya sejuk {x, y, r, kuat}
  function naungan(n, t, d) {
    const k = v(n.kuat, t, d, 1), x = v(n.x, t, d, 540), y = v(n.y, t, d, 1100), r = v(n.r, t, d, 260);
    if (k <= 0.01 || r <= 1) return "";
    const atas = y - 1900, R = rng(31); let butir = "";
    for (let i = 0; i < 18; i++) { const bx = x + (R() - 0.5) * r * 2.4, h = 1500 * R(), by = y - ((h + t * 60 * (0.5 + R())) % 1500); butir += `<circle cx="${bx}" cy="${by}" r="${3 + R() * 4}" fill="#f2fdff" opacity="${(0.25 + 0.5 * R()) * k}"/>`; }
    return `<defs><radialGradient id="ng"><stop offset="0" stop-color="#e8fbff" stop-opacity="${0.95 * k}"/><stop offset=".5" stop-color="#7fd3e8" stop-opacity="${0.45 * k}"/><stop offset="1" stop-color="#3a8fb0" stop-opacity="0"/></radialGradient>
      <linearGradient id="nb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#dff8ff" stop-opacity="0"/><stop offset=".35" stop-color="#cdf3ff" stop-opacity="${0.22 * k}"/><stop offset="1" stop-color="#bfefff" stop-opacity="${0.5 * k}"/></linearGradient></defs>
      <ellipse cx="${x}" cy="${y}" rx="${r * 1.75}" ry="${r * 0.5}" fill="#123a5e" opacity="${0.5 * k}"/>
      <path d="M ${x - r * 0.75} ${atas} L ${x + r * 0.75} ${atas} L ${x + r * 1.7} ${y} L ${x - r * 1.7} ${y} Z" fill="url(#nb)"/>
      <ellipse cx="${x}" cy="${y}" rx="${r * 1.6}" ry="${r}" fill="url(#ng)"/>
      <ellipse cx="${x}" cy="${y}" rx="${r * 1.72}" ry="${r * 0.48}" fill="none" stroke="#d8f7ff" stroke-width="6" opacity="${0.55 * k * (0.75 + 0.25 * Math.sin(t * 3))}"/>${butir}`;
  }


  // benda sederhana: {jenis, x, y, s, at, warna, n}
  const garis2 = (x1, y1, x2, y2) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${INK}" stroke-width="4" opacity=".5"/>`;
  // ---- benda kaya detail (6 Nov) ----
  const bintik4 = (x, y, r, op, w = "#fff8d0") => `<path d="M ${x} ${y - r} Q ${x + r * 0.18} ${y - r * 0.18} ${x + r} ${y} Q ${x + r * 0.18} ${y + r * 0.18} ${x} ${y + r} Q ${x - r * 0.18} ${y + r * 0.18} ${x - r} ${y} Q ${x - r * 0.18} ${y - r * 0.18} ${x} ${y - r} Z" fill="${w}" opacity="${op}"/>`;
  // uang kertas generik (bukan tiruan uang asli): 300x140, pusat (0,0)
  function lembar(w, nilai = "100") {
    return `<rect x="-150" y="-70" width="300" height="140" rx="8" fill="${w}" stroke="${INK}" stroke-width="4"/><rect x="-150" y="-70" width="300" height="46" rx="8" fill="#fff" opacity=".18"/>
      <rect x="-138" y="-58" width="276" height="116" rx="5" fill="none" stroke="#fff" stroke-width="3" opacity=".55"/><circle cx="78" cy="2" r="40" fill="#fff" opacity=".28"/><circle cx="78" cy="2" r="28" fill="none" stroke="#fff" stroke-width="3" opacity=".5"/>
      <path d="M -120 30 q 20 -14 40 0 t 40 0 t 40 0" stroke="#fff" stroke-width="3" fill="none" opacity=".45"/><path d="M -120 44 q 20 -14 40 0 t 40 0 t 40 0" stroke="#fff" stroke-width="3" fill="none" opacity=".3"/>
      <text x="-122" y="-16" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" font-size="40" fill="#fff" opacity=".9">${nilai}</text>`;
  }
  // kitab terbuka di meja kayu, lampu hangat, tulisan tangan bertahap + stabilo. Pusat buku di (0,0).
  // o: {teks, sub ("HR Muslim 2581") atau judul+no, ukuran, buka, tulis_at, tulis (detik), stabilo: "frasa", stabilo_at, meja:false}
  function kitab(o, t, d) {
    const bk = clamp(v(o.buka, t, d, 1)), PW = 395, R = rng(o.seed || 21);
    let uk = o.ukuran ? o.ukuran * 1.3 : 66, baris = [], cw = 0, lh = 0;
    const kata = String(o.teks || "").replace(/\n/g, " ").replace(/\s+/g, " ").trim().split(" ").filter(Boolean);
    for (; uk >= 30; uk -= 3) {
      cw = uk * 0.42; lh = uk * 1.12; const maks = Math.max(8, Math.floor(PW / cw)); baris = []; let cur = "";
      kata.forEach((k) => { if (cur && (cur + " " + k).length > maks) { baris.push(cur); cur = k; } else cur = cur ? cur + " " + k : k; });
      if (cur) baris.push(cur);
      if (baris.length * lh <= 540) break;
    }
    const t0 = o.tulis_at != null ? o.tulis_at : (o.at || 0) + 0.45, tot = Math.max(1, baris.join("").length), dur = o.tulis != null ? o.tulis : Math.min(4.2, 0.8 + tot * 0.04);
    let maju = clamp((t - t0) / dur) * tot;
    let g = "";
    if (o.meja !== false) {
      g += `<defs><linearGradient id="kmj" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a86a3a"/><stop offset="1" stop-color="#5e3418"/></linearGradient>
        <radialGradient id="klp" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(-430 -820) scale(1250)"><stop offset="0" stop-color="#fff1c2" stop-opacity=".75"/><stop offset=".5" stop-color="#ffcf80" stop-opacity=".25"/><stop offset="1" stop-color="#ffcf80" stop-opacity="0"/></radialGradient></defs>
        <rect x="-1600" y="-1800" width="3200" height="3600" fill="url(#kmj)"/>`;
      for (let i = -6; i <= 6; i++) g += `<line x1="-1600" y1="${i * 270 + 40}" x2="1600" y2="${i * 270 + 40}" stroke="#3e200c" stroke-width="5" opacity=".45"/>`;
      for (let i = 0; i < 34; i++) { const yy = -1500 + R() * 3000, xx = -900 + R() * 1800, ww = 120 + R() * 380; g += `<path d="M ${xx} ${yy} q ${ww / 2} ${-10 - R() * 14} ${ww} 0" stroke="#4a260e" stroke-width="${2 + R() * 3}" fill="none" opacity="${0.15 + R() * 0.2}"/>`; }
      // cangkir teh + uap
      const cx = 330, cy = 560;
      g += `<ellipse cx="${cx}" cy="${cy + 52}" rx="150" ry="34" fill="#2a1406" opacity=".35"/><ellipse cx="${cx}" cy="${cy + 40}" rx="140" ry="34" fill="#f4efe6" stroke="${INK}" stroke-width="5"/>
        <path d="M ${cx - 80} ${cy - 40} L ${cx - 66} ${cy + 30} Q ${cx} ${cy + 56} ${cx + 66} ${cy + 30} L ${cx + 80} ${cy - 40} Z" fill="#fbf8f2" stroke="${INK}" stroke-width="5"/><path d="M ${cx + 78} ${cy - 22} q 50 0 40 34 q -8 22 -48 20" stroke="${INK}" stroke-width="12" fill="none"/><path d="M ${cx + 78} ${cy - 22} q 50 0 40 34 q -8 22 -48 20" stroke="#fbf8f2" stroke-width="5" fill="none"/>
        <ellipse cx="${cx}" cy="${cy - 40}" rx="80" ry="18" fill="#9a4a1c" stroke="${INK}" stroke-width="5"/><path d="M ${cx - 76} ${cy - 10} Q ${cx} ${cy + 6} ${cx + 76} ${cy - 10}" stroke="#4a8a7a" stroke-width="8" fill="none"/>`;
      for (let i = 0; i < 3; i++) { const fz = ((t * 0.35 + i / 3) % 1), sy = cy - 70 - fz * 260, sx = cx - 30 + i * 30 + Math.sin(t * 2 + i * 2) * 18; g += `<path d="M ${sx} ${sy} q 22 -40 0 -80 q -22 -40 0 -80" stroke="#fff" stroke-width="10" fill="none" stroke-linecap="round" opacity="${0.35 * Math.sin(fz * Math.PI)}"/>`; }
    }
    // bayangan + sampul kulit + tumpukan halaman
    g += `<ellipse cx="0" cy="370" rx="560" ry="70" fill="#2a1406" opacity=".4"/>
      <path d="M -490 -330 Q -240 -366 0 -342 Q 240 -366 490 -330 L 490 350 Q 240 322 0 350 Q -240 322 -490 350 Z" fill="#7b2a20" stroke="${INK}" stroke-width="7"/>
      <path d="M -470 -310 Q -240 -344 0 -322 Q 240 -344 470 -310 L 470 330 Q 240 302 0 330 Q -240 302 -470 330 Z" fill="none" stroke="#e8c26a" stroke-width="4" opacity=".8"/>`;
    for (let i = 3; i >= 1; i--) g += `<path d="M ${-455 - i * 2} ${-300 + i * 7} Q -240 ${-336 + i * 7} 0 ${-312 + i * 7} Q 240 ${-336 + i * 7} ${455 + i * 2} ${-300 + i * 7} L ${455 + i * 2} ${318 + i * 6} Q 240 ${292 + i * 6} 0 ${318 + i * 6} Q -240 ${292 + i * 6} ${-455 - i * 2} ${318 + i * 6} Z" fill="#efe0bd" stroke="#b89a68" stroke-width="2"/>`;
    g += `<defs><linearGradient id="khk" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e2cc9c"/><stop offset=".12" stop-color="#fbf2dc"/><stop offset="1" stop-color="#fff9ea"/></linearGradient>
      <linearGradient id="khr" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="#e2cc9c"/><stop offset=".12" stop-color="#fbf2dc"/><stop offset="1" stop-color="#fff9ea"/></linearGradient></defs>
      <g transform="scale(${bk} 1)"><path d="M 0 -310 Q -230 -346 -450 -302 L -450 312 Q -230 290 0 316 Z" fill="url(#khr)" stroke="#b89a68" stroke-width="3"/>
      <rect x="-420" y="-270" width="380" height="550" fill="none" stroke="#c9a46a" stroke-width="3" opacity=".7"/><rect x="-410" y="-260" width="360" height="530" fill="none" stroke="#c9a46a" stroke-width="1.5" opacity=".6"/></g>
      <path d="M 0 -310 Q 230 -346 450 -302 L 450 312 Q 230 290 0 316 Z" fill="url(#khk)" stroke="#b89a68" stroke-width="3"/>
      <rect x="40" y="-270" width="380" height="550" fill="none" stroke="#c9a46a" stroke-width="3" opacity=".7"/>
      <path d="M 0 -312 L 0 318" stroke="#a88a58" stroke-width="5" opacity=".7"/>`;
    for (let i = 0; i < 40; i++) g += `<circle cx="${(R() - 0.5) * 860}" cy="${(R() - 0.5) * 560}" r="${1 + R() * 2}" fill="#b89a68" opacity=".25"/>`;
    // halaman kiri: sumber (tulisan tangan merah bata + ornamen)
    let jd = o.judul, no = o.no;
    if (!jd && o.sub) { const m = String(o.sub).match(/^(.*?)\s*(\d[\d\s.,–-]*)$/); jd = m ? m[1] : o.sub; no = m ? "No. " + m[2].trim() : ""; }
    if (bk > 0.6 && jd) {
      const op2 = clamp((bk - 0.6) / 0.3);
      g += `<g opacity="${op2}" font-family="Tangan, DejaVu Sans, sans-serif" font-weight="700" text-anchor="middle">
        <path d="M -320 -150 L -130 -150 M -225 -172 l 14 22 l -14 22 l -14 -22 Z" stroke="#b07a2a" stroke-width="3" fill="#e8c26a"/>
        <text x="-225" y="-30" font-size="${Math.min(92, 760 / Math.max(6, jd.length))}" fill="#8a2e1f">${esc(jd)}</text>
        ${no ? `<text x="-225" y="60" font-size="66" fill="#8a2e1f">${esc(no)}</text>` : ""}
        <path d="M -320 130 L -130 130" stroke="#b07a2a" stroke-width="3"/>${bintik4(-225, 130, 16, 0.9, "#e8c26a")}</g>`;
    }
    // stabilo (di bawah tulisan)
    const gab = baris.join(" "), sel = [];
    if (o.stabilo) {
      const i0 = gab.toLowerCase().indexOf(String(o.stabilo).toLowerCase()), sa = o.stabilo_at != null ? o.stabilo_at : t0 + dur + 0.25, sp = clamp((t - sa) / 0.7);
      if (i0 >= 0 && sp > 0) {
        let pos = 0; const i1 = i0 + String(o.stabilo).length, tot2 = i1 - i0; let dulu = 0;
        baris.forEach((b, i) => { const a = Math.max(i0, pos), z = Math.min(i1, pos + b.length); if (z > a) { const n = z - a, f = clamp((sp * tot2 - dulu) / n); dulu += n; if (f > 0) sel.push([i, a - pos, n * f]); } pos += b.length + 1; });
      }
    }
    const y0 = -lh * (baris.length - 1) / 2 + uk * 0.32, X0 = 230 - PW / 2;
    sel.forEach(([i, a, n]) => { g += `<rect x="${X0 + a * cw - 4}" y="${y0 + i * lh - uk * 0.78}" width="${n * cw + 8}" height="${uk * 0.98}" rx="10" fill="#ffe14a" opacity=".62" transform="rotate(-0.8 ${X0} ${y0 + i * lh})"/>`; });
    // tulisan tangan muncul bertahap
    let pena = null;
    baris.forEach((b, i) => {
      const f = clamp(maju / b.length); maju -= b.length; if (f <= 0) return;
      const yy = y0 + i * lh, ww = b.length * cw;
      g += `<clipPath id="ktc${i}"><rect x="${X0 - 10}" y="${yy - uk * 1.2}" width="${ww * f + 12}" height="${uk * 1.6}"/></clipPath><text clip-path="url(#ktc${i})" x="${X0}" y="${yy}" textLength="${ww}" lengthAdjust="spacing" font-family="Tangan, DejaVu Sans, sans-serif" font-weight="700" font-size="${uk}" fill="#2b2140">${esc(b)}</text>`;
      if (f < 1) pena = [X0 + ww * f, yy];
    });
    if (pena) g += `<g transform="translate(${pena[0]} ${pena[1] + Math.sin(t * 40) * 3}) rotate(28)"><path d="M 0 0 L -10 -34 L 10 -34 Z" fill="#d9b25a" stroke="${INK}" stroke-width="3"/><rect x="-12" y="-300" width="24" height="268" rx="10" fill="#26476e" stroke="${INK}" stroke-width="4"/><rect x="-12" y="-120" width="24" height="18" fill="#d9b25a"/><rect x="-5" y="-290" width="6" height="150" rx="3" fill="#fff" opacity=".3"/></g>`;
    // pita pembatas
    g += `<path d="M 330 300 L 330 470 L 352 444 L 374 470 L 374 300 Z" fill="#c0392b" stroke="${INK}" stroke-width="4"/>`;
    if (o.meja !== false) { g += `<rect x="-1600" y="-1800" width="3200" height="3600" fill="url(#klp)" style="mix-blend-mode:screen"/>`; for (let i = 0; i < 14; i++) { const dx = (R() * 900 - 700 + t * (8 + R() * 10)) % 900, dy = -700 + R() * 700 + Math.sin(t + i) * 20; g += `<circle cx="${dx}" cy="${dy}" r="${2 + R() * 3}" fill="#fff6d0" opacity="${0.3 + 0.3 * Math.sin(t * 1.5 + i)}"/>`; } }
    return g;
  }
  // siluet sederhana (Ya'juj Ma'juj, kerumunan): menghadap kanan; ang = sudut lengan (14 turun, -75 menghantam, -160 terangkat), beliung, rot (rebah), langkah -1..1, rim = cahaya tepi
  function sosok(x, y, k, o = {}) {
    const c = o.warna || "#120e1a", rim = o.rim || 0, a = o.ang == null ? 14 : o.ang, lg = o.langkah || 0;
    let s = `<g transform="translate(${x} ${y}) scale(${k}) rotate(${o.rot || 0})">`;
    s += `<line x1="-16" y1="-70" x2="${-16 - lg * 26}" y2="0" stroke="${c}" stroke-width="26" stroke-linecap="round"/><line x1="16" y1="-70" x2="${16 + lg * 26}" y2="0" stroke="${c}" stroke-width="26" stroke-linecap="round"/>`;
    s += `<line x1="-30" y1="-196" x2="${-36 - lg * 12}" y2="-108" stroke="${c}" stroke-width="24" stroke-linecap="round"/><rect x="-40" y="-220" width="80" height="160" rx="36" fill="${c}"/><circle cx="0" cy="-258" r="36" fill="${c}"/>`;
    if (rim) s += `<path d="M -4 -294 A 36 36 0 0 1 34 -270" stroke="#ffb05a" stroke-width="6" fill="none" opacity="${rim}" stroke-linecap="round"/><path d="M 40 -196 L 40 -96" stroke="#ffb05a" stroke-width="5" opacity="${rim * 0.7}" stroke-linecap="round"/>`;
    s += `<g transform="translate(30 -196) rotate(${a})"><line x1="0" y1="0" x2="0" y2="92" stroke="${c}" stroke-width="24" stroke-linecap="round"/>` + (o.beliung ? `<g transform="translate(0 92)"><line x1="0" y1="-14" x2="0" y2="118" stroke="#3a2c22" stroke-width="11" stroke-linecap="round"/><path d="M -50 100 Q 0 126 50 100 L 42 118 Q 0 140 -42 118 Z" fill="#9aa0ad" stroke="#14151c" stroke-width="3"/></g>` : "") + `</g>`;
    return s + "</g>";
  }
  function lidah(x, y, w, h, ph, fill, op = 1) { // (16 Nov) satu lidah api berbentuk tetes, ujung bergoyang
    const sx = Math.sin(ph) * w * 0.18, sx2 = Math.sin(ph * 1.7 + 1) * w * 0.12;
    return `<path d="M ${x - w / 2} ${y} C ${x - w / 2} ${y - h * 0.45} ${x - w * 0.15 + sx2} ${y - h * 0.6} ${x + sx} ${y - h} C ${x + w * 0.2 + sx2} ${y - h * 0.62} ${x + w / 2} ${y - h * 0.45} ${x + w / 2} ${y} Q ${x} ${y + w * 0.25} ${x - w / 2} ${y} Z" fill="${fill}" opacity="${op}"/>`;
  }
  function figur(x, y, k, o = {}) { // (16 Nov) siluet diam dengan pose lengan: berdiri|telinga|wajah|angkat|tunduk|tolak; rim di sisi cahaya; bara/api/hangus
    const c = o.warna ? o.warna : campur(warna("#120e1a", "#000000", 0), "#000000", o.gelap || 0), rim = o.rim || 0, rw = o.rimwarna || "#ffb05a", sd = o.sisi || 1, t = o.t || 0, ps = o.pose || "berdiri";
    const sw = Math.sin(t * 1.3) * 2.5, tk = ps === "tunduk" ? 1 : 0;
    let s = `<g transform="translate(${x} ${y}) scale(${k}) rotate(${sw * 0.4 + (ps === "tolak" ? -6 * sd : 0)})">`;
    if (o.bara) s += `<ellipse cx="-20" cy="-4" rx="34" ry="11" fill="#ff7a2a" opacity="${o.bara}"/><ellipse cx="20" cy="-4" rx="34" ry="11" fill="#ff7a2a" opacity="${o.bara}"/><ellipse cx="0" cy="0" rx="110" ry="26" fill="#ff5a1a" opacity="${0.35 * o.bara}"/>`;
    s += `<line x1="-16" y1="-70" x2="-18" y2="0" stroke="${c}" stroke-width="26" stroke-linecap="round"/><line x1="16" y1="-70" x2="18" y2="0" stroke="${c}" stroke-width="26" stroke-linecap="round"/><rect x="-40" y="-220" width="80" height="160" rx="36" fill="${c}"/>`;
    const hx = tk ? 6 * sd : 0, hy = tk ? -244 : -258;
    s += `<circle cx="${hx}" cy="${hy}" r="36" fill="${c}"/>`;
    const lengan = (sx, arah) => { let p;
      if (ps === "telinga") p = [[sx, -196], [sx + arah * 46, -232], [sx + arah * 12, -262]];
      else if (ps === "wajah") p = [[sx, -196], [sx + arah * 40, -214], [arah * 8, -258]];
      else if (ps === "angkat") p = [[sx, -196], [sx + arah * 62, -292 + Math.sin(t * 3 + arah) * 8], [sx + arah * 84, -380 + Math.sin(t * 3 + arah) * 14]];
      else if (ps === "tolak") p = [[sx, -196], [sx + arah * 10, -150], [sx + arah * 16, -104]];
      else p = [[sx, -196], [sx + arah * 8, -150], [sx + arah * 10, -104]];
      return `<path d="M ${p.map((q) => q.join(" ")).join(" L ")}" stroke="${c}" stroke-width="24" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`; };
    s += lengan(-30, -1) + lengan(30, 1);
    if (ps === "wajah") s += `<path d="M -52 -280 Q 0 -310 52 -280 L 46 -226 Q 0 -212 -46 -226 Z" fill="${c}"/>`; // baju ditutupkan ke wajah
    if (rim) s += `<path d="M ${hx + sd * -4} ${hy - 36} A 36 36 0 0 ${sd > 0 ? 1 : 0} ${hx + sd * 34} ${hy + 12}" stroke="${rw}" stroke-width="6" fill="none" opacity="${rim}" stroke-linecap="round"/><path d="M ${sd * 40} -196 L ${sd * 40} -96" stroke="${rw}" stroke-width="5" opacity="${rim * 0.7}" stroke-linecap="round"/><path d="M ${sd * 18} -60 L ${sd * 18} -8" stroke="${rw}" stroke-width="4" opacity="${rim * 0.5}" stroke-linecap="round"/>`;
    if (o.hangus) { const R = rng(7); for (let i = 0; i < 9; i++) { const ax = -30 + R() * 60, ay = -210 + R() * 200; s += `<path d="M ${ax} ${ay} l ${R() * 20 - 10} ${14 + R() * 12} l ${R() * 16 - 8} ${12}" stroke="#ff8a3a" stroke-width="4" fill="none" opacity="${o.hangus}"/>`; } }
    if (o.api) { const fl = ["#ff4a12", "#ff8a2a", "#ffc061"]; for (let i = 0; i < 8; i++) { const sdx = i % 2 ? 1 : -1, ax = sdx * (38 + (i % 3) * 8), ay = -20 - Math.floor(i / 2) * 64; s += lidah(ax, ay, 46, 80 + 30 * Math.sin(t * 7 + i * 1.9), t * 8 + i, fl[i % 3], 0.9 * o.api); }
      s += lidah(0, -290, 60, 110 + 30 * Math.sin(t * 6), t * 7, "#ff6a1a", 0.9 * o.api) + lidah(0, -296, 34, 70 + 20 * Math.sin(t * 9), t * 9, "#ffd27a", o.api); }
    if (o.bara) for (let i = 0; i < 3; i++) { const fz = (t * 0.5 + i / 3) % 1; s += `<path d="M ${hx - 14 + i * 14} ${hy - 40} q ${Math.sin(t * 3 + i) * 14} -30 0 ${-60 * fz - 20}" stroke="#e8e0d8" stroke-width="${10 * (1 - fz)}" fill="none" opacity="${0.4 * o.bara * (1 - fz)}" stroke-linecap="round"/>`; }
    return s + "</g>";
  }
  function benda(o, t, d) {
    const tl = t - (o.at || 0); if (tl < 0) return "";
    const x = v(o.x, t, d, 540), y = v(o.y, t, d, 1000), sc = v(o.s, t, d, 1), miring = v(o.miring, t, d, 0), op = (o.at ? clamp(tl / 0.4) : 1) * v(o.op, t, d, 1), j = o.jenis;
    let g = "";
    if (j === "ngarai") { // dinding besi-tembaga Zulkarnain di celah dua gunung (QS 18:93-97). x,y = kaki dinding; lubang 0-1 (galian, inti terang = hampir tembus), jebol 0-1, kilap = detik dinding "utuh kembali"
      const lb = v(o.lubang, t, d, 0), jb = v(o.jebol, t, d, 0), lx = o.lx || 0, ly = o.ly == null ? -190 : o.ly, R = rng(o.seed || 3), kil = o.kilap != null ? t - o.kilap : -1, H = 1500, BATU = o.gaya === "batu_kapur";
      g = `<defs><linearGradient id="ngw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${BATU ? "#d7bd91" : "#626a7a"}"/><stop offset=".55" stop-color="${BATU ? "#a9875d" : "#3c404d"}"/><stop offset="1" stop-color="${BATU ? "#70563d" : "#1c1e27"}"/></linearGradient><linearGradient id="ngf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${BATU ? "#8b7053" : "#34305a"}"/><stop offset=".6" stop-color="${BATU ? "#5e4938" : "#1b1830"}"/><stop offset="1" stop-color="${BATU ? "#34291f" : "#0b0a14"}"/></linearGradient><radialGradient id="ngl"><stop offset="0" stop-color="#fffbe0"/><stop offset=".22" stop-color="#ffd27a"/><stop offset=".55" stop-color="#ff8a2a" stop-opacity=".5"/><stop offset="1" stop-color="#ff8a2a" stop-opacity="0"/></radialGradient></defs>`;
      g += `<rect x="-620" y="${-H}" width="1240" height="${H + 60}" fill="url(#ngw)"/><rect x="-620" y="${-H}" width="1240" height="16" fill="#b9c2d4" opacity=".7"/>`;
      if (BATU) { for (let r0 = 0; r0 < 10; r0++) { const yy = -r0 * 155, offset = (r0 % 2) * 105; g += `<line x1="-620" y1="${yy}" x2="620" y2="${yy}" stroke="#59432f" stroke-width="10"/><line x1="-620" y1="${yy + 10}" x2="620" y2="${yy + 10}" stroke="#f0d8aa" stroke-width="3" opacity=".55"/>`; for (let c0 = -5; c0 <= 5; c0++) { const xx = c0 * 210 + offset; g += `<path d="M ${xx} ${yy} L ${xx} ${yy - 155}" stroke="#59432f" stroke-width="9"/><path d="M ${xx + 8} ${yy - 12} L ${xx + 8} ${yy - 143}" stroke="#f0d8aa" stroke-width="3" opacity=".45"/>`; } } g += `<path d="M -620 -80 Q 0 -210 620 -80 M -620 -1180 Q 0 -1310 620 -1180" fill="none" stroke="#ead2a5" stroke-width="24" opacity=".8"/><path d="M -620 -80 Q 0 -210 620 -80 M -620 -1180 Q 0 -1310 620 -1180" fill="none" stroke="#70563d" stroke-width="7"/>`; } else { for (let r0 = 0; r0 < 13; r0++) { const yy = -r0 * 120; g += `<line x1="-620" y1="${yy}" x2="620" y2="${yy}" stroke="#13141b" stroke-width="7"/><line x1="-620" y1="${yy + 6}" x2="620" y2="${yy + 6}" stroke="#9aa3b6" stroke-width="2" opacity=".3"/>`; for (let c0 = -4; c0 <= 4; c0++) { const xx = c0 * 150 + (r0 % 2) * 75; g += `<line x1="${xx}" y1="${yy}" x2="${xx}" y2="${yy - 120}" stroke="#13141b" stroke-width="5"/><circle cx="${xx - 18}" cy="${yy - 20}" r="6.5" fill="#808a9b"/><circle cx="${xx + 18}" cy="${yy - 100}" r="6.5" fill="#808a9b"/>`; } } }
      for (let i = 0; i < 12; i++) { const xx = -520 + R() * 1040, L0 = 220 + R() * 600, y0 = -H + R() * 500; g += `<path d="M ${xx} ${y0} q ${R() * 30 - 15} ${L0 / 2} ${R() * 20 - 10} ${L0}" stroke="#c9752f" stroke-width="${8 + R() * 14}" fill="none" opacity=".38" stroke-linecap="round"/>`; } // lelehan tembaga
      if (kil >= 0 && kil < 0.7) g += `<path d="M ${-900 + kil * 2600} ${-H} l 160 0 l -420 ${H} l -160 0 Z" fill="#fff" opacity="${0.35 * (1 - kil / 0.7)}"/>`;
      if (lb > 0.01 && jb < 0.99) { const rp = 18 + 100 * lb, R2 = rng(8); let pts = "";
        g += `<circle cx="${lx}" cy="${ly}" r="${90 + 300 * lb}" fill="url(#ngl)" opacity="${0.35 + 0.5 * lb}"/>`;
        for (let i = 0; i < 9; i++) { const a = (i / 9) * 6.283 + R2() * 0.5, L1 = rp * (1.5 + R2() * 1.4); g += `<path d="M ${lx + Math.cos(a) * rp * 0.8} ${ly + Math.sin(a) * rp * 0.8} L ${lx + Math.cos(a) * L1 * 0.7 + (R2() - 0.5) * 30} ${ly + Math.sin(a) * L1 * 0.7 + (R2() - 0.5) * 30} L ${lx + Math.cos(a) * L1} ${ly + Math.sin(a) * L1}" stroke="#08070c" stroke-width="${6 * lb + 2}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`; }
        for (let i = 0; i < 14; i++) { const a = (i / 14) * 6.283, rr = rp * (0.82 + R2() * 0.36); pts += `${lx + Math.cos(a) * rr},${ly + Math.sin(a) * rr} `; }
        g += `<polygon points="${pts}" fill="#0a0910" stroke="#ff9a3a" stroke-width="${3 + 3 * lb}" stroke-opacity=".8"/>`;
        const ci = clamp((lb - 0.55) / 0.45); if (ci > 0) g += `<circle cx="${lx}" cy="${ly}" r="${rp * 0.62 * ci * (1 + 0.06 * Math.sin(t * 9))}" fill="#fff6cf"/><circle cx="${lx}" cy="${ly}" r="${rp * 1.5 * ci}" fill="url(#ngl)" opacity=".9"/>`; }
      if (jb > 0) { const rj = 110 + 560 * jb, cy = ly - rj * 0.55, R3 = rng(4); let pts = "";
        g += `<circle cx="${lx}" cy="${cy}" r="${rj * 2.2}" fill="url(#ngl)"/>`;
        for (let i = 0; i < 9; i++) { const a = -3.14 + (i / 8) * 3.14 + Math.sin(t * 0.7 + i) * 0.05; g += `<path d="M ${lx} ${cy} L ${lx + Math.cos(a - 0.05) * 2600} ${cy + Math.sin(a - 0.05) * 2600} L ${lx + Math.cos(a + 0.05) * 2600} ${cy + Math.sin(a + 0.05) * 2600} Z" fill="#ffe9a8" opacity="${0.16 * jb}"/>`; }
        for (let i = 0; i < 18; i++) { const a = (i / 18) * 6.283, rr = 0.8 + R3() * 0.4; pts += `${lx + Math.cos(a) * rj * 0.72 * rr},${Math.min(60, cy + Math.sin(a) * rj * 1.2 * rr)} `; }
        g += `<polygon points="${pts}" fill="#fff3c8" stroke="#ffb347" stroke-width="10"/>`;
        if (jb < 1) for (let i = 0; i < 18; i++) { const a = R3() * 6.283, sp = 300 + R3() * 900, sz = 30 + R3() * 80; g += `<rect x="${lx + Math.cos(a) * sp * jb - sz / 2}" y="${cy + Math.sin(a) * sp * jb + 900 * jb * jb - sz / 2}" width="${sz}" height="${sz * 0.7}" fill="#3a3e4a" stroke="#13141b" stroke-width="4" transform="rotate(${jb * 400 * (R3() - 0.5)} ${lx + Math.cos(a) * sp * jb} ${cy + Math.sin(a) * sp * jb + 900 * jb * jb})"/>`; }
        g += `<rect x="-3000" y="-4000" width="6000" height="8000" fill="#fff" opacity="${clamp(1 - jb * 5) * 0.85}"/>`; }
      [-1, 1].forEach((sg) => { const P = [[1500, 260], [1500, -2300], [600, -2300], [560, -1800], [470, -1500], [520, -1250], [410, -980], [450, -720], [360, -460], [400, -230], [300, 0], [350, 260]].map(([a, b]) => `${sg * a},${b}`).join(" ");
        g += `<polygon points="${P}" fill="url(#ngf)"/><path d="M ${sg * 470} -1500 L ${sg * 700} -1300 L ${sg * 620} -900 M ${sg * 410} -980 L ${sg * 640} -800 L ${sg * 560} -420 M ${sg * 360} -460 L ${sg * 560} -300" stroke="#4a4578" stroke-width="6" fill="none" opacity=".5"/>`;
        if (lb > 0 || jb > 0) g += `<path d="M ${sg * 300} 0 L ${sg * 400} -230 L ${sg * 360} -460 L ${sg * 450} -720" stroke="#ff9a3a" stroke-width="10" fill="none" opacity="${0.5 * Math.max(lb, jb)}" stroke-linecap="round" stroke-linejoin="round"/>`; });
    } else if (j === "penggali") { // siluet mengayun beliung ke satu titik. x,y = titik gali; aktif 0|1, pulang 0-1 (berbalik lalu pergi ke samping-depan), n, rim
      const n = o.n || 6, ak = v(o.aktif, t, d, 1), pl = v(o.pulang, t, d, 0), rim = v(o.rim, t, d, 0.8), R = rng(o.seed || 11);
      for (let i = 0; i < n; i++) { const sg = i % 2 ? 1 : -1, baris = Math.floor(i / 2), jx = 205 + baris * 150 + R() * 30, jy = 150 + baris * 48 + R() * 16, k = (0.95 + baris * 0.17) * (1 + pl * 0.45), ph = R(), kc = 1.25 + R() * 0.3;
        const s0 = (t * kc + ph) % 1, ang = ak > 0.5 && pl < 0.05 ? (s0 < 0.72 ? mix(-75, -160, halus(s0 / 0.72)) : mix(-160, -75, Math.pow((s0 - 0.72) / 0.28, 2))) : 14;
        const px = sg * (jx + pl * (520 + baris * 140)), py = jy + pl * 300, lg = pl > 0.02 && pl < 0.98 ? Math.sin(t * 9 + ph * 6) : 0;
        g += `<g transform="translate(${px} ${py}) scale(${-sg * (pl > 0.12 ? -1 : 1)} 1)">` + sosok(0, 0, k, { ang, beliung: true, rim: rim * (1 - pl), langkah: lg }) + `</g>`; }
      if (ak > 0.5 && pl < 0.05) { const b = Math.floor(t * 3.4), q = t * 3.4 - b, R2 = rng(b * 7 + 1); g += `<circle r="${80 * (1 - q)}" fill="#ffd27a" opacity="${0.55 * (1 - q)}"/>`;
        for (let i = 0; i < 14; i++) { const a = R2() * 6.283, sp = 70 + R2() * 260; g += `<circle cx="${Math.cos(a) * sp * q}" cy="${Math.sin(a) * sp * q + 170 * q * q}" r="${6 * (1 - q) + 1.5}" fill="${i % 3 ? "#ffd27a" : "#fff"}" opacity="${1 - q}"/>`; } }
    } else if (j === "pemimpin") { // siluet pemimpin di atas batu; angkat 0-1 = lengan terangkat
      g = `<path d="M -170 0 Q -130 -76 -40 -90 L 70 -86 Q 140 -64 175 0 Z" fill="#0b0912"/><g transform="translate(0 -84)">` + sosok(0, 0, 1.3, { ang: mix(14, -150, v(o.angkat, t, d, 0)), rim: v(o.rim, t, d, 0.8) }) + `</g>`;
    } else if (j === "arus") { // kerumunan siluet bergerak. mode lereng (turun dari dua punggung bukit ke (0,0)), cahaya (berlari masuk ke cahaya di (0,0)), lari (mendatar ke kanan); maju = kemajuan, rebah 0-1
      const n = o.n || 40, R = rng(o.seed || 21), mj = v(o.maju, t, d, t * 0.2), rb = v(o.rebah, t, d, 0), md = o.mode || "lereng", L = [];
      for (let i = 0; i < n; i++) { const r1 = R(), r2 = R(), r3 = R(), sg = i % 2 ? 1 : -1, p = md === "cahaya" ? clamp(mj * (0.7 + r2 * 0.6) - r1 * 0.5) : (mj + r1) % 1; let px, py, k;
        if (md === "lereng") { px = sg * mix(640, 50 + r2 * 330, p) + (r3 - 0.5) * 120; py = mix(-860, 240, Math.pow(p, 1.25)) + (r2 - 0.5) * 60; k = mix(0.14, 1.0, p); }
        else if (md === "cahaya") { px = mix((r3 - 0.5) * 1150, (r3 - 0.5) * 70, p); py = mix(430 + r2 * 220, -10, Math.pow(p, 0.8)); k = mix(1.3, 0.1, Math.pow(p, 0.7)); }
        else { px = mix(-760, 760, p); py = (r2 - 0.5) * 170; k = 0.5 + r2 * 0.28; }
        L.push({ px, py, k, ph: r1 * 6, sg, p }); }
      L.sort((a, b) => a.k - b.k);
      L.forEach((f) => { if (md === "cahaya" && (f.p >= 1 || f.p <= 0)) return; const fx = md === "lari" ? 1 : md === "cahaya" ? (f.px > 0 ? -1 : 1) : -f.sg;
        g += `<g transform="translate(${f.px} ${f.py}) scale(${fx} 1)" opacity="${md === "lereng" ? clamp(f.p * 6) * clamp((1 - f.p) * 8) : md === "lari" ? clamp(f.p * 8) * clamp((1 - f.p) * 8) : 1}">` + sosok(0, 0, f.k, { ang: rb > 0 ? 10 : 20 + Math.sin(t * 10 + f.ph) * 40, langkah: rb > 0 ? 0 : Math.sin(t * 10 + f.ph), rot: rb * 86 * (f.ph > 3 ? 1 : -1), rim: o.rim || 0, warna: o.warna }) + `</g>`; });
    } else if (j === "ombak") { // banjir / laut badai berlapis (15 Nov): y = permukaan air; tinggi = amplitudo px (300 = "laksana gunung"); lapis, jarak, panjang, cepat, warna [atas, bawah], buih
      const A = v(o.tinggi, t, d, 40), n = o.lapis || 3, L = o.panjang || 260, sd = o.seed || 0, id = "om" + sd + "_" + Math.round(y), ca = o.warna || ["#2b4a78", "#0b1832"], kc = o.cepat || 1;
      g = `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${ca[0]}"/><stop offset=".35" stop-color="${ca[1]}"/><stop offset="1" stop-color="#03060f"/></linearGradient></defs>`;
      for (let i = 0; i < n; i++) { const yy = i * (o.jarak || 70), ph = i * 1.9 + sd, sp = kc * (0.9 + i * 0.25) * (i % 2 ? -1 : 1), a = A * (0.75 + i * 0.2);
        const f = (xx) => yy - a * (0.62 * Math.sin(xx / L + t * sp + ph) + 0.28 * Math.sin(xx / (L * 0.41) - t * sp * 1.6 + ph * 2) + 0.1 * Math.sin(xx / (L * 0.17) + t * 2.3));
        let dd = `M -1400 ${f(-1400).toFixed(1)}`; for (let xx = -1360; xx <= 1400; xx += 40) dd += ` L ${xx} ${f(xx).toFixed(1)}`;
        g += `<path d="${dd} L 1400 2600 L -1400 2600 Z" fill="url(#${id})"/><path d="${dd}" stroke="${o.buih || "#ffe9b8"}" stroke-width="${5 + i * 1.5}" fill="none" opacity="${(0.55 - i * 0.08) * v(o.kilap, t, d, 1)}" stroke-linecap="round" stroke-dasharray="${90 + i * 30} ${70 + i * 25}" stroke-dashoffset="${(t * 40 * sp).toFixed(1)}"/>`; }
    } else if (j === "bahtera") { // kapal Nabi Nuh dari papan dan pasak (QS 54:13), tampak samping; (0,0) = lunas. jadi 0-1 (rusuk -> papan -> rumah geladak), goyang (derajat), cahaya 0-1, orang n (siluet kecil di geladak), pintu 0-1 (+titian), darat (penyangga + bayangan)
      const jd = v(o.jadi, t, d, 1), gy = v(o.goyang, t, d, 0), ch = v(o.cahaya, t, d, 0.8), pt = v(o.pintu, t, d, 0), W = 460, H = 250, R = rng(11);
      const pp = clamp((jd - 0.12) / 0.55), rh = clamp((jd - 0.7) / 0.3), lamb = `M ${-W} ${-H} Q ${-W + 20} ${-50} ${-W + 190} 0 L ${W - 170} 0 Q ${W + 10} ${-70} ${W + 70} ${-H - 46} L ${W - 20} ${-H} Z`;
      g = `<defs><linearGradient id="bhk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9a6638"/><stop offset=".6" stop-color="#5e3a20"/><stop offset="1" stop-color="#2a180e"/></linearGradient><linearGradient id="bhs" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".5"/></linearGradient><clipPath id="bhc"><path d="${lamb}"/></clipPath><radialGradient id="bhl"><stop offset="0" stop-color="#fff3c8"/><stop offset=".5" stop-color="#ffc45a" stop-opacity=".8"/><stop offset="1" stop-color="#ff9a3a" stop-opacity="0"/></radialGradient></defs>`;
      if (o.darat) { g += `<ellipse cx="20" cy="14" rx="560" ry="30" fill="#000" opacity=".4"/>`; [-330, -150, 60, 250].forEach((px) => { g += `<path d="M ${px - 46} 14 L ${px} ${-64} L ${px + 46} 14" stroke="#3a2416" stroke-width="16" fill="none" stroke-linecap="round"/><path d="M ${px - 50} 10 L ${px - 4} ${-68}" stroke="#c08a50" stroke-width="4" fill="none" opacity=".5"/>`; }); }
      g += `<g transform="translate(0 ${(gy * 3 * Math.sin(t * 0.9 + 1)).toFixed(1)}) rotate(${(gy * Math.sin(t * 1.3)).toFixed(2)})">`;
      if (pp < 0.99) for (let i = 0; i <= 11; i++) { const xx = -W + 70 + i * ((2 * W - 150) / 11), kl = (xx / W) * 34; g += `<path d="M ${xx} -4 Q ${xx + kl * 0.3} ${-H * 0.5} ${xx + kl} ${-H - 8}" stroke="#7a4f2b" stroke-width="13" fill="none" stroke-linecap="round"/><path d="M ${xx - 5} -6 Q ${xx + kl * 0.3 - 5} ${-H * 0.5} ${xx + kl - 5} ${-H - 8}" stroke="#e0a868" stroke-width="3" fill="none" opacity=".55"/>`; }
      g += `<path d="M ${-W + 150} 0 L ${W - 150} 0" stroke="#3a2416" stroke-width="22" stroke-linecap="round"/>`;
      if (pp > 0.01) { const yt = -(H + 60) * pp; g += `<g clip-path="url(#bhc)"><rect x="${-W - 20}" y="${yt}" width="${2 * W + 140}" height="${-yt + 20}" fill="url(#bhk)"/>`;
        for (let r0 = 0; r0 * 36 < -yt; r0++) { const yy = -r0 * 36; g += `<line x1="${-W - 20}" y1="${yy}" x2="${W + 100}" y2="${yy}" stroke="#1d120b" stroke-width="5"/><line x1="${-W - 20}" y1="${yy + 5}" x2="${W + 100}" y2="${yy + 5}" stroke="#e0a868" stroke-width="2" opacity=".25"/>`;
          for (let c0 = 0; c0 < 9; c0++) { const xx = -W + 40 + c0 * 118 + (r0 % 2) * 59 + R() * 20; g += `<line x1="${xx}" y1="${yy}" x2="${xx}" y2="${yy - 36}" stroke="#1d120b" stroke-width="3"/><circle cx="${xx - 12}" cy="${yy - 18}" r="4.5" fill="#1a100a"/><circle cx="${xx + 12}" cy="${yy - 18}" r="4.5" fill="#1a100a"/>`; } }
        g += `<rect x="${-W - 20}" y="${yt}" width="${2 * W + 140}" height="${-yt + 20}" fill="url(#bhs)"/>`;
        if (pt > 0.01) g += `<rect x="-70" y="-190" width="140" height="170" rx="10" fill="#1a0f08"/><rect x="-58" y="-180" width="116" height="160" rx="8" fill="#ffd27a" opacity="${pt}"/>`;
        g += `</g>`;
        if (pt > 0.01) g += `<circle cx="0" cy="-100" r="${230 * pt}" fill="url(#bhl)" opacity="${0.55 * pt}"/><path d="M -72 -22 L 72 -22 L 250 96 L -250 96 Z" fill="#4a2e1a" opacity="${pt}"/><path d="M -72 -22 L 72 -22" stroke="#e0a868" stroke-width="5" opacity="${0.7 * pt}"/>`;
        if (pp >= 0.99) g += `<path d="M ${-W} ${-H} L ${W - 20} ${-H} L ${W + 70} ${-H - 46}" stroke="#2a180e" stroke-width="20" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M ${-W + 4} ${-H - 8} L ${W - 24} ${-H - 8}" stroke="#ffd98a" stroke-width="5" fill="none" opacity="${0.35 + 0.4 * ch}" stroke-linecap="round"/><path d="M ${-W - 4} ${-H + 6} Q ${-W + 14} ${-56} ${-W + 180} -6" stroke="#ffd98a" stroke-width="5" fill="none" opacity="${0.25 + 0.3 * ch}" stroke-linecap="round"/>`; }
      if (rh > 0.01) { const hh = 150 * rh, y0 = -H - 10; g += `<rect x="-250" y="${y0 - hh}" width="470" height="${hh}" fill="#6b4324"/><rect x="-250" y="${y0 - hh}" width="470" height="${hh}" fill="url(#bhs)"/>`;
        for (let r0 = 1; r0 * 34 < hh; r0++) g += `<line x1="-250" y1="${y0 - r0 * 34}" x2="220" y2="${y0 - r0 * 34}" stroke="#1d120b" stroke-width="4"/>`;
        if (rh > 0.9) { g += `<path d="M -290 ${y0 - hh} L -15 ${y0 - hh - 96} L 260 ${y0 - hh} Z" fill="#3a2416"/><path d="M -290 ${y0 - hh} L -15 ${y0 - hh - 96}" stroke="#ffd98a" stroke-width="6" opacity="${0.4 + 0.4 * ch}" stroke-linecap="round"/>`;
          [-180, -70, 40, 150].forEach((wx) => { g += `<rect x="${wx - 26}" y="${y0 - 108}" width="52" height="62" rx="8" fill="#1a0f08"/><rect x="${wx - 20}" y="${y0 - 102}" width="40" height="50" rx="6" fill="#ffd27a" opacity="${ch}"/><circle cx="${wx}" cy="${y0 - 78}" r="70" fill="url(#bhl)" opacity="${0.35 * ch}"/>`; }); } }
      for (let i = 0; i < (o.orang || 0); i++) { const ox = 262 + i * 44 + (i % 2) * 8, oh = 62 + (i % 3) * 8; g += `<g transform="translate(${ox} ${-H - 10})"><rect x="-13" y="${-oh}" width="26" height="${oh}" rx="12" fill="#2b2238"/><circle cy="${-oh - 13}" r="14" fill="#2b2238"/><path d="M -13 ${-oh + 6} Q -15 ${-oh - 24} 0 ${-oh - 28}" stroke="#ffcf7a" stroke-width="4" fill="none" opacity=".7"/></g>`; }
      g += `</g>`;
    } else if (j === "hewan") { // siluet hewan berpasangan berjalan ke kanan (QS 11:40); macam gajah|jerapah|unta|rusa|burung; pasang:false = satu; jalan 0-1; cahaya dari kiri-atas (garis tepi emas)
      const mc = o.macam || "gajah", jl = v(o.jalan, t, d, 1), ink = o.warna || "#2a2138", rimc = o.rim || "#ffcf7a";
      const kk = (xx, pj, lb, f) => { const a = (jl * 15 * Math.sin(t * 5 + f) * Math.PI) / 180; return `<line x1="${xx}" y1="${-pj}" x2="${(xx + Math.sin(a) * pj).toFixed(1)}" y2="${(-pj + Math.cos(a) * pj).toFixed(1)}" stroke-width="${lb}" stroke-linecap="round"/>`; };
      const satu = (f) => mc === "gajah" ? `<ellipse cx="0" cy="-160" rx="112" ry="76"/><circle cx="112" cy="-186" r="56"/><ellipse cx="86" cy="-190" rx="34" ry="50"/><path d="M 150 -170 Q 196 -150 184 -86 Q 178 -58 196 -52" stroke-width="24" fill="none" stroke-linecap="round"/><path d="M -108 -180 Q -140 -150 -132 -110" stroke-width="7" fill="none" stroke-linecap="round"/>${kk(-72, 100, 38, f)}${kk(-30, 100, 38, f + 3.14)}${kk(40, 100, 38, f + 1.6)}${kk(80, 100, 38, f + 4.7)}`
        : mc === "jerapah" ? `<ellipse cx="0" cy="-200" rx="78" ry="44"/><path d="M 40 -215 L 86 -420 L 118 -416 L 80 -200 Z"/><ellipse cx="118" cy="-428" rx="34" ry="17"/><path d="M 96 -440 l -4 -26 M 110 -442 l 2 -26" stroke-width="6" stroke-linecap="round"/><path d="M -74 -210 Q -96 -180 -90 -140" stroke-width="6" fill="none" stroke-linecap="round"/>${kk(-56, 170, 16, f)}${kk(-34, 170, 16, f + 3.14)}${kk(40, 170, 16, f + 1.6)}${kk(60, 170, 16, f + 4.7)}`
        : mc === "unta" ? `<ellipse cx="0" cy="-176" rx="98" ry="48"/><ellipse cx="-6" cy="-226" rx="46" ry="38"/><path d="M 78 -180 Q 120 -190 124 -270" stroke-width="30" fill="none" stroke-linecap="round"/><ellipse cx="140" cy="-282" rx="34" ry="18"/><path d="M -94 -186 Q -112 -160 -108 -130" stroke-width="6" fill="none" stroke-linecap="round"/>${kk(-66, 136, 18, f)}${kk(-40, 136, 18, f + 3.14)}${kk(46, 136, 18, f + 1.6)}${kk(70, 136, 18, f + 4.7)}`
        : mc === "rusa" ? `<ellipse cx="0" cy="-124" rx="68" ry="34"/><path d="M 44 -134 Q 70 -150 76 -196" stroke-width="22" fill="none" stroke-linecap="round"/><ellipse cx="90" cy="-204" rx="26" ry="14"/><path d="M 74 -214 q -10 -34 -30 -44 M 70 -234 q 0 -22 16 -34 M 86 -216 q 14 -30 34 -36 M 96 -236 q -4 -20 8 -32" stroke-width="5" fill="none" stroke-linecap="round"/>${kk(-48, 96, 11, f)}${kk(-30, 96, 11, f + 3.14)}${kk(30, 96, 11, f + 1.6)}${kk(48, 96, 11, f + 4.7)}`
        : `<path d="M -46 ${(-14 * Math.sin(t * 7 + f)).toFixed(1)} Q -20 -30 0 0 Q 20 -30 46 ${(-14 * Math.sin(t * 7 + f)).toFixed(1)}" stroke-width="9" fill="none" stroke-linecap="round"/><ellipse rx="12" ry="7"/>`;
      const bentuk = (f) => `<g stroke="${rimc}" fill="${rimc}" transform="translate(-6 -7)" opacity=".85">${satu(f)}</g><g stroke="${ink}" fill="${ink}">${satu(f)}</g>`;
      g = (mc === "burung" ? "" : `<ellipse cx="-20" cy="6" rx="${o.pasang === false ? 110 : 170}" ry="14" fill="#000" opacity=".35"/>`) + (o.pasang === false ? "" : `<g transform="translate(${mc === "burung" ? "-90 -50" : "-96 -16"}) scale(.9)" opacity=".92">${bentuk(1.6)}</g>`) + bentuk(0);
    } else if (j === "petir") { // kilat bercabang + kilasan langit; saat = [detik relatif shot, ...]; (0,0) = pangkal di atas
      (o.saat || [0]).forEach((ts, n) => { const q = t - ts; if (q < 0 || q > 0.42) return; const R = rng(31 + n * 7 + (o.seed || 0)), k = q < 0.08 ? 1 : q < 0.14 ? 0.25 : Math.max(0, 1 - (q - 0.14) / 0.28); let px = 0, py = 0, dd = "M 0 0", cb = "";
        for (let i = 0; i < 9; i++) { px += (R() - 0.5) * 170; py += 90 + R() * 70; dd += ` L ${px.toFixed(0)} ${py.toFixed(0)}`; if (i === 3 || i === 5) cb += `<path d="M ${px.toFixed(0)} ${py.toFixed(0)} l ${(R() - 0.5) * 260} ${120 + R() * 80} l ${(R() - 0.5) * 120} ${90}" stroke="#fff6d8" stroke-width="5" fill="none" opacity="${0.8 * k}"/>`; }
        g += `<rect x="-3000" y="-3000" width="6000" height="6000" fill="#ffe9b8" opacity="${0.22 * k}"/><path d="${dd}" stroke="#ffd98a" stroke-width="26" fill="none" opacity="${0.35 * k}" stroke-linejoin="round"/><path d="${dd}" stroke="#fffdf2" stroke-width="9" fill="none" opacity="${k}" stroke-linejoin="round"/>${cb}`; });
    } else if (j === "pancar") { // mata air memancar dari bumi (QS 54:12): kuat 0-1, tinggi px
      const ku = v(o.kuat, t, d, 1), Hh = (o.tinggi || 420) * ku, R = rng(o.seed || 9); if (ku > 0.01) { g = `<ellipse cy="4" rx="${120 * ku}" ry="${22 * ku}" fill="#8fc0f0" opacity=".55"/><path d="M -34 0 Q -18 ${-Hh * 0.6} -10 ${-Hh} L 10 ${-Hh} Q 18 ${-Hh * 0.6} 34 0 Z" fill="#7fb4ea" opacity=".9"/><path d="M -22 0 Q -12 ${-Hh * 0.6} -6 ${-Hh}" stroke="#fff3d0" stroke-width="6" fill="none" opacity=".8"/>`;
        for (let i = 0; i < 16; i++) { const u = (t * (0.9 + R() * 0.6) + R()) % 1, vx = (R() - 0.5) * 520, px = vx * u, py = -Hh + (Hh + 30) * u * u - 60 * Math.sin(u * 3.14); g += `<circle cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="${6 + R() * 9}" fill="#bfe0ff" opacity="${(0.85 * (1 - u)).toFixed(2)}"/>`; } }
    } else if (j === "tebing") { // puncak batu curam; (0,0) = pijakan di puncak; cahaya dari kiri-atas
      g = `<path d="M -330 1000 L -150 300 L -110 110 L -64 0 L 70 0 L 104 130 L 190 330 L 380 1000 Z" fill="${o.warna || "#120e1c"}"/><path d="M 70 0 L 104 130 L 190 330 L 380 1000 L 150 1000 L 60 400 Z" fill="#000" opacity=".35"/><path d="M -150 300 L -110 110 L -64 0 L 70 0" stroke="#ffd98a" stroke-width="6" fill="none" opacity=".45" stroke-linejoin="round" stroke-linecap="round"/><path d="M -60 60 L -20 240 L -70 420 M 30 80 L 60 260" stroke="#000" stroke-width="5" fill="none" opacity=".4"/>`;
    } else if (j === "danau") { const isi = v(o.isi, t, d, 1), R = rng(5), q = Math.sqrt(Math.max(0, isi));
      g = `<ellipse rx="480" ry="156" fill="#2a2018"/><ellipse rx="446" ry="136" fill="#5c4732"/>`;
      for (let i = 0; i < 16; i++) { const a = R() * 6.283, r0 = 40 + R() * 340; g += `<path d="M ${Math.cos(a) * r0} ${Math.sin(a) * r0 * 0.3} l ${R() * 80 - 40} ${R() * 30 - 15} l ${R() * 60 - 30} ${R() * 24 - 12}" stroke="#241a12" stroke-width="5" fill="none" opacity="${clamp(1.3 - isi * 2.2)}"/>`; }
      if (isi > 0.01) { g += `<ellipse rx="${446 * q}" ry="${136 * q}" fill="#2a6fb8"/><ellipse rx="${404 * q}" ry="${114 * q}" cy="-7" fill="#62b0ee"/>`; for (let i = 0; i < 9; i++) { const xx = (R() - 0.5) * 620 * q, yy = (R() - 0.5) * 150 * q; g += `<path d="M ${xx - 30} ${yy} q 15 -8 30 0 q 15 8 30 0" stroke="#eef8ff" stroke-width="4" fill="none" opacity="${0.4 + 0.4 * Math.sin(t * 3 + i)}"/>`; } }
    } else if (j === "batu") { // batu gelap latar depan (pakai kabur:true agar tampak dekat kamera)
      g = `<path d="M -340 40 Q -320 -170 -140 -210 Q 30 -270 190 -170 Q 320 -120 350 40 Z" fill="${o.warna || "#06050a"}"/>`;
    } else if (j === "masjid") { const w = o.warna || "#1d1520";
      g = `<rect x="-260" y="-200" width="520" height="200" fill="${w}"/><path d="M -150 -200 Q -150 -390 0 -420 Q 150 -390 150 -200 Z" fill="${w}"/><rect x="-6" y="-470" width="12" height="55" fill="${w}"/><path d="M 0 -500 a 16 16 0 1 0 12 26 a 12 12 0 1 1 -12 -26 Z" fill="#ffd27a"/>`;
      [-330, 330].forEach((mx) => { g += `<rect x="${mx - 26}" y="-470" width="52" height="470" fill="${w}"/><path d="M ${mx - 34} -470 L ${mx} -560 L ${mx + 34} -470 Z" fill="${w}"/>`; });
      [-170, -85, 0, 85, 170].forEach((wx, i) => { g += `<path d="M ${wx - 22} -40 L ${wx - 22} -110 Q ${wx} -145 ${wx + 22} -110 L ${wx + 22} -40 Z" fill="#ffcf6a" opacity="${0.6 + 0.4 * Math.sin(t * 2 + i)}"/>`; });
    } else if (j === "timbangan") { // timbangan emas berornamen
      const mir = v(o.miring, t, d, Math.sin(t * 1.3) * 4);
      g = `<defs><linearGradient id="tbg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#a87420"/><stop offset=".45" stop-color="#ffe9a0"/><stop offset="1" stop-color="#b8821e"/></linearGradient><radialGradient id="tbp" cx=".4" cy=".2" r=".9"><stop offset="0" stop-color="#fff2bc"/><stop offset="1" stop-color="#c8901e"/></radialGradient></defs>
        <circle cx="0" cy="-300" r="190" fill="#ffd27a" opacity=".16"/><ellipse cx="0" cy="12" rx="150" ry="20" fill="#000" opacity=".22"/>
        <path d="M -120 0 L 120 0 L 90 -36 L -90 -36 Z" fill="url(#tbg)" stroke="${INK}" stroke-width="5"/><rect x="-60" y="-56" width="120" height="22" rx="6" fill="url(#tbg)" stroke="${INK}" stroke-width="4"/>
        <rect x="-14" y="-300" width="28" height="248" fill="url(#tbg)" stroke="${INK}" stroke-width="4"/><circle cx="0" cy="-200" r="9" fill="#a87420"/><circle cx="0" cy="-130" r="9" fill="#a87420"/>
        <g transform="rotate(${mir} 0 -296)"><rect x="-190" y="-306" width="380" height="20" rx="10" fill="url(#tbg)" stroke="${INK}" stroke-width="4"/>
        ${[-1, 1].map((sd) => { const px = sd * 172; return `<g transform="rotate(${-mir} ${px} -296)"><path d="M ${px} -296 L ${px - 62} -168 M ${px} -296 L ${px + 62} -168" stroke="#a87420" stroke-width="4" stroke-dasharray="10 6"/><circle cx="${px}" cy="-296" r="9" fill="#ffe9a0" stroke="${INK}" stroke-width="3"/><path d="M ${px - 78} -170 Q ${px} -96 ${px + 78} -170 Z" fill="url(#tbp)" stroke="${INK}" stroke-width="5"/><ellipse cx="${px}" cy="-170" rx="78" ry="12" fill="#ffe9a0" stroke="${INK}" stroke-width="4"/></g>`; }).join("")}</g>
        <circle cx="0" cy="-322" r="24" fill="url(#tbp)" stroke="${INK}" stroke-width="4"/>${bintik4(-10, -332, 12, 0.6 + 0.4 * Math.sin(t * 3))}`;
    } else if (j === "bulan") {
      g = `<circle r="220" fill="#fff6d8" opacity=".12"/><circle r="140" fill="#fff6d8" opacity=".14"/><path d="M 0 -90 A 90 90 0 1 0 0 90 A 70 70 0 1 1 0 -90 Z" fill="#fff4cf"/>`;
    } else if (j === "bintang") { const R = rng(o.seed || 9);
      for (let i = 0; i < (o.n || 60); i++) { const bx = R() * 1080 - 540, by = R() * (o.tinggi || 900), r = 1.5 + R() * 3.5; g += `<circle cx="${bx}" cy="${by}" r="${r}" fill="#fff" opacity="${0.35 + 0.5 * Math.abs(Math.sin(t * 1.5 + i))}"/>`; }
    } else if (j === "kantong") { // kantong pahala: kain keemasan, tali, koin mengintip, berkilau
      const pl = 1 + 0.06 * Math.sin(t * 3);
      g = `<defs><radialGradient id="kgr" cx=".38" cy=".35" r=".8"><stop offset="0" stop-color="#fff0b8"/><stop offset=".45" stop-color="#e8b85a"/><stop offset="1" stop-color="#9a6a24"/></radialGradient><radialGradient id="kgl"><stop offset="0" stop-color="#fff3b0" stop-opacity=".85"/><stop offset="1" stop-color="#ffd27a" stop-opacity="0"/></radialGradient></defs>
        <circle cx="0" cy="-60" r="${150 * pl}" fill="url(#kgl)" opacity=".6"/><ellipse cx="0" cy="8" rx="62" ry="12" fill="#000" opacity=".2"/>
        <ellipse cx="-10" cy="-128" rx="20" ry="9" fill="#f2c24a" stroke="${INK}" stroke-width="3"/><ellipse cx="14" cy="-134" rx="20" ry="9" fill="#ffd970" stroke="${INK}" stroke-width="3"/>
        <path d="M -60 -6 C -84 -52 -64 -94 -32 -102 L 32 -102 C 64 -94 84 -52 60 -6 C 40 18 -40 18 -60 -6 Z" fill="url(#kgr)" stroke="${INK}" stroke-width="5"/>
        <path d="M -30 -98 Q -42 -52 -26 -4 M 18 -100 Q 32 -60 22 -4" stroke="#a8752a" stroke-width="4" fill="none" opacity=".6"/>
        <path d="M -36 -102 Q -48 -128 -22 -122 Q 0 -140 22 -122 Q 48 -128 36 -102 Z" fill="#e2ad52" stroke="${INK}" stroke-width="4"/>
        <path d="M -38 -102 Q 0 -90 38 -102" stroke="#7a3b1a" stroke-width="9" fill="none" stroke-linecap="round"/><path d="M 4 -96 q 12 22 -2 38 M 4 -96 q 24 14 22 34" stroke="#7a3b1a" stroke-width="6" fill="none" stroke-linecap="round"/>
        ${bintik4(-4, -50, 16, 0.85)}${bintik4(-74, -110, 14, 0.5 + 0.5 * Math.sin(t * 4))}${bintik4(78, -80, 11, 0.5 + 0.5 * Math.sin(t * 4 + 2))}${bintik4(46, -150, 9, 0.5 + 0.5 * Math.sin(t * 4 + 4))}`;
    } else if (j === "hati") { const k = 1 + 0.08 * Math.sin(t * 4);
      g = `<g transform="scale(${k})"><path d="M 0 30 C -90 -30 -60 -110 0 -70 C 60 -110 90 -30 0 30 Z" fill="#ff7a8a" stroke="#1d1520" stroke-width="7"/></g>`;
    } else if (j === "sajadah") {
      g = `<path d="M -170 0 L 170 0 L 140 -60 L -140 -60 Z" fill="#7a2a3a" stroke="#1d1520" stroke-width="6"/><path d="M -120 -8 L 120 -8 L 100 -52 L -100 -52 Z" fill="none" stroke="#ffd27a" stroke-width="4"/>`;
    } else if (j === "telaga") { const w = o.w || 560, h = o.h || 130, R = rng(o.seed || 17);
      g = `<defs><radialGradient id="tlg"><stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#eefcff"/><stop offset="1" stop-color="#a8e6f5"/></radialGradient></defs>
        <ellipse rx="${w * 1.25}" ry="${h * 1.6}" fill="#fff6d8" opacity="${0.22 + 0.06 * Math.sin(t * 2)}"/>
        <ellipse rx="${w}" ry="${h}" fill="url(#tlg)" stroke="#e8d9a8" stroke-width="16"/>`;
      for (let i = 0; i < 4; i++) { const q = ((t * 0.25 + i / 4) % 1); g += `<ellipse rx="${w * (0.15 + 0.8 * q)}" ry="${h * (0.15 + 0.8 * q)}" fill="none" stroke="#7fd3e8" stroke-width="4" opacity="${0.5 * (1 - q)}"/>`; }
      for (let i = 0; i < (o.kilau || 14); i++) { const a = R() * 6.28, rr = R() * 0.85, x0 = Math.cos(a) * w * rr, y0 = Math.sin(a) * h * rr, k = 0.4 + 0.6 * Math.abs(Math.sin(t * 2.5 + i)); g += `<path transform="translate(${x0} ${y0}) scale(${0.6 + k * 0.6})" d="M 0 -14 L 3 -3 L 14 0 L 3 3 L 0 14 L -3 3 L -14 0 L -3 -3 Z" fill="#ffffff" opacity="${k}"/>`; }
    } else if (j === "api") { // (16 Nov, diperhalus) api unggun: lidah api bergradasi berkedip + kayu + pendar lembut
      const id = "ap" + Math.round(x * 3 + y);
      g = `<defs><radialGradient id="${id}p"><stop offset="0" stop-color="#ff9a3a" stop-opacity=".55"/><stop offset="1" stop-color="#ff6a1a" stop-opacity="0"/></radialGradient><linearGradient id="${id}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ff4a12"/><stop offset=".55" stop-color="#ff9a2a"/><stop offset="1" stop-color="#ffe7a0"/></linearGradient></defs>`;
      g += `<circle cx="0" cy="-90" r="${260 + 14 * Math.sin(t * 9)}" fill="url(#${id}p)"/>`;
      g += `<path d="M -110 0 L 100 -34" stroke="#3a2418" stroke-width="30" stroke-linecap="round"/><path d="M -100 -30 L 110 6" stroke="#2a1a12" stroke-width="30" stroke-linecap="round"/>`;
      g += lidah(0, -10, 150, 230 + 30 * Math.sin(t * 7), t * 6, `url(#${id})`) + lidah(-50, -14, 80, 150 + 25 * Math.sin(t * 8 + 1), t * 7 + 2, `url(#${id})`) + lidah(52, -14, 80, 160 + 25 * Math.sin(t * 9 + 3), t * 6.5 + 4, `url(#${id})`) + lidah(0, -18, 70, 120 + 18 * Math.sin(t * 11), t * 9 + 1, "#fff2c4");
    } else if (j === "pohon") { const ay = Math.sin(t * 1.2 + x) * 4, w = o.warna || "#3f8a4a";
      g = `<path d="M 0 0 Q -30 -260 10 -520" fill="none" stroke="#7a5432" stroke-width="44" stroke-linecap="round"/><path d="M 0 0 Q -30 -260 10 -520" fill="none" stroke="${INK}" stroke-width="5" stroke-dasharray="6 38" opacity=".5"/>`;
      [-150, -100, -45, 10, 60, 120, 170, 215].forEach((a, i) => { const r = (a + ay) * Math.PI / 180, L = 230 - (i % 2) * 40, ex = 10 + Math.sin(r) * L, ey = -520 - Math.cos(r) * L * 0.55; g += `<path d="M 10 -520 Q ${10 + Math.sin(r) * L * 0.5} ${-520 - Math.cos(r) * L * 0.6 - 40} ${ex} ${ey + 40}" fill="none" stroke="${w}" stroke-width="30" stroke-linecap="round"/>`; });
      g += `<circle cx="-14" cy="-500" r="16" fill="#c9762e"/><circle cx="20" cy="-496" r="16" fill="#c9762e"/><circle cx="4" cy="-478" r="16" fill="#b5652a"/>`;
    } else if (j === "menara") { // menara putih (pilot tanda kiamat): badan pucat, satu sisi tersinari emas, balkon dua tingkat, kubah kecil; o.cahaya 0-1 = pendar di sekelilingnya
      const c = o.warna || "#efe9da", gl = v(o.cahaya, t, d, 0.6), id = "mn" + Math.round(x);
      g = `<defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6f6a66"/><stop offset=".5" stop-color="${c}"/><stop offset="1" stop-color="#ffdf9a"/></linearGradient><radialGradient id="${id}g"><stop offset="0" stop-color="#ffe6a8" stop-opacity=".55"/><stop offset="1" stop-color="#ffe6a8" stop-opacity="0"/></radialGradient></defs>`;
      g += `<ellipse cx="20" cy="-560" rx="520" ry="760" fill="url(#${id}g)" opacity="${gl}"/>`;
      g += `<path d="M -78 0 L -62 -640 L 62 -640 L 78 0 Z" fill="url(#${id})" stroke="#2a2430" stroke-width="5"/><rect x="-100" y="-672" width="200" height="40" rx="8" fill="url(#${id})" stroke="#2a2430" stroke-width="5"/>`;
      for (let i = -3; i <= 3; i++) g += `<rect x="${i * 28 - 5}" y="-712" width="10" height="42" fill="${c}" opacity=".85"/>`;
      g += `<rect x="-100" y="-722" width="200" height="12" rx="5" fill="${c}"/><path d="M -46 -712 L -40 -930 L 40 -930 L 46 -712 Z" fill="url(#${id})" stroke="#2a2430" stroke-width="5"/><rect x="-62" y="-952" width="124" height="28" rx="6" fill="url(#${id})" stroke="#2a2430" stroke-width="5"/>`;
      g += `<path d="M -36 -952 Q -40 -1010 0 -1070 Q 40 -1010 36 -952 Z" fill="url(#${id})" stroke="#2a2430" stroke-width="5"/><line x1="0" y1="-1070" x2="0" y2="-1120" stroke="#ffdf9a" stroke-width="6" stroke-linecap="round"/><circle cx="0" cy="-1128" r="9" fill="#ffdf9a"/>`;
      [[-520, 30], [-330, 26], [-150, 24], [-820, 20]].forEach(([yy, w2]) => { g += `<path d="M ${-w2 / 2} ${yy} v ${-w2 * 1.3} a ${w2 / 2} ${w2 / 2} 0 0 1 ${w2} 0 v ${w2 * 1.3} Z" fill="#1a1622"/>`; });
    } else if (j === "kota") { // siluet kota tua (kubah, menara kecil, rumah bertingkat) dengan beberapa jendela menyala; o.w lebar, o.seed
      const R = rng(o.seed || 3), w = o.w || 1400, c = o.warna || "#16121f"; let xx = -w / 2;
      while (xx < w / 2) { const bw = 70 + R() * 110, bh = 120 + R() * 240, kub = R() < 0.28;
        g += `<rect x="${xx}" y="${-bh}" width="${bw}" height="${bh}" fill="${c}"/>` + (kub ? `<path d="M ${xx + bw * 0.1} ${-bh} a ${bw * 0.4} ${bw * 0.4} 0 0 1 ${bw * 0.8} 0 Z" fill="${c}"/>` : "");
        for (let r = 0; r < bh / 60 - 1; r++) if (R() < 0.3) g += `<rect x="${xx + 14 + R() * (bw - 40)}" y="${-bh + 26 + r * 56}" width="14" height="22" rx="7" fill="#ffcf7a" opacity="${0.35 + R() * 0.5}"/>`;
        xx += bw + R() * 14; }
    } else if (j === "gapura") { // gerbang batu (gerbang Ludd): dua tiang + lengkung, cahaya emas dari dalam; o.cahaya 0-1
      const gl = v(o.cahaya, t, d, 0.5), id = "gp" + Math.round(x), bt = o.warna || "#2a2533";
      g = `<defs><radialGradient id="${id}"><stop offset="0" stop-color="#fff3cf" stop-opacity=".95"/><stop offset=".6" stop-color="#ffcf7a" stop-opacity=".45"/><stop offset="1" stop-color="#ffcf7a" stop-opacity="0"/></radialGradient></defs>`;
      g += `<ellipse cx="0" cy="-330" rx="${300 + 260 * gl}" ry="${460 + 300 * gl}" fill="url(#${id})" opacity="${0.35 + 0.65 * gl}"/>`;
      g += `<path d="M -330 0 L -330 -640 Q -330 -700 -270 -700 L 270 -700 Q 330 -700 330 -640 L 330 0 L 170 0 L 170 -360 A 170 170 0 0 0 -170 -360 L -170 0 Z" fill="${bt}" stroke="#0f0c14" stroke-width="7"/>`;
      for (let r = 0; r < 9; r++) g += `<path d="M -330 ${-70 * r - 60} H -170 M 170 ${-70 * r - 60} H 330" stroke="#0f0c14" stroke-width="4" opacity=".55"/>`;
      g += `<path d="M -170 -360 A 170 170 0 0 1 170 -360" stroke="#ffd98a" stroke-width="6" fill="none" opacity="${0.35 + 0.65 * gl}"/><path d="M -330 -640 Q -330 -700 -270 -700 L 270 -700 Q 330 -700 330 -640" stroke="#ffd98a" stroke-width="4" fill="none" opacity=".35"/>`;
      [-250, -90, 90, 250].forEach((px) => { g += `<rect x="${px - 34}" y="-770" width="68" height="70" fill="${bt}" stroke="#0f0c14" stroke-width="6"/>`; });
    } else if (j === "saf") { // barisan orang tampak belakang (siluet, cahaya tepi emas dari depan); o.n per baris, o.baris, o.jarak
      const n = o.n || 6, br = o.baris || 2, jr = o.jarak || 150, c = o.warna || "#15111c";
      for (let r = br - 1; r >= 0; r--) for (let i = 0; i < n; i++) { const px = (i - (n - 1) / 2) * jr + (r % 2) * jr * 0.5, py = -r * 120, k = 1 - r * 0.14;
        g += `<g transform="translate(${px} ${py}) scale(${k})"><path d="M -62 0 L -62 -150 Q -62 -212 0 -216 Q 62 -212 62 -150 L 62 0 Z" fill="${c}"/><circle cx="0" cy="-258" r="44" fill="${c}"/><path d="M -62 -150 Q -62 -212 0 -216 Q 62 -212 62 -150" stroke="#ffd98a" stroke-width="5" fill="none" opacity=".55"/><path d="M -40 -276 A 44 44 0 0 1 40 -276" stroke="#ffd98a" stroke-width="5" fill="none" opacity=".55"/></g>`; }
    } else if (j === "surya") { // matahari besar di cakrawala (piringan + pendar emas + sinar tipis); o.r jari-jari, o.terang 0-1
      const r = v(o.r, t, d, 300), tr = v(o.terang, t, d, 1), id = "sy" + Math.round(x);
      g = `<defs><radialGradient id="${id}"><stop offset="0" stop-color="#fff6d8"/><stop offset=".55" stop-color="#ffd27a"/><stop offset="1" stop-color="#ff9a3a"/></radialGradient><radialGradient id="${id}g"><stop offset="0" stop-color="#ffcf7a" stop-opacity=".7"/><stop offset=".5" stop-color="#ff9a3a" stop-opacity=".22"/><stop offset="1" stop-color="#ff9a3a" stop-opacity="0"/></radialGradient></defs>`;
      g += `<circle r="${r * 3.4}" fill="url(#${id}g)" opacity="${tr}"/>`;
      for (let i = 0; i < 14; i++) { const a2 = (i / 14) * Math.PI * 2 + t * 0.03; g += `<path d="M ${Math.cos(a2) * r * 1.08} ${Math.sin(a2) * r * 1.08} L ${Math.cos(a2 + 0.05) * r * 2.6} ${Math.sin(a2 + 0.05) * r * 2.6} L ${Math.cos(a2 - 0.05) * r * 2.6} ${Math.sin(a2 - 0.05) * r * 2.6} Z" fill="#ffd98a" opacity="${0.1 * tr}"/>`; }
      g += `<circle r="${r}" fill="url(#${id})" opacity="${0.55 + 0.45 * tr}"/>`;
    } else if (j === "gunung") { const w = o.warna || "#8a6a5a";
      g = `<path d="M -700 0 L -260 -520 L 60 -140 L 330 -420 L 760 0 Z" fill="${w}" opacity=".9"/><path d="M -260 -520 L -170 -410 L -260 -430 L -330 -400 Z M 330 -420 L 400 -330 L 330 -350 L 270 -330 Z" fill="#fff" opacity=".35"/>`;
      if (o.kilau) { // gunung amal bercahaya: garis tepi, sisi bayangan keemasan, kilau berkedip
        g = `<circle cx="-100" cy="-300" r="700" fill="#fff6c8" opacity=".35"/><path d="M -700 0 L -260 -520 L 60 -140 L 330 -420 L 760 0 Z" fill="${w}" stroke="${INK}" stroke-width="7" stroke-linejoin="round"/>
          <path d="M -260 -520 L -120 0 L -700 0 Z" fill="#f2c96a" opacity=".55"/><path d="M 330 -420 L 470 0 L 120 0 L 60 -140 Z" fill="#f2c96a" opacity=".5"/><path d="M -260 -520 L -200 -440 L -260 -455 L -320 -430 Z M 330 -420 L 380 -350 L 330 -365 L 280 -345 Z" fill="#fff"/>`;
        for (let i = 0; i < 9; i++) g += bintik4(-560 + i * 140, -60 - ((i * 97) % 380), 22, 0.4 + 0.6 * Math.abs(Math.sin(t * 2.4 + i)));
      }
    } else if (j === "rumah") { const w = o.warna || "#e9d6b0";
      g = `<rect x="-170" y="-260" width="340" height="260" fill="${w}" stroke="${INK}" stroke-width="7"/><rect x="-190" y="-280" width="380" height="28" fill="#b89a6e" stroke="${INK}" stroke-width="6"/><path d="M -40 0 L -40 -120 Q 0 -160 40 -120 L 40 0 Z" fill="#6a4a30" stroke="${INK}" stroke-width="6"/><rect x="-130" y="-200" width="56" height="56" fill="#3a5a7a" stroke="${INK}" stroke-width="5"/><rect x="74" y="-200" width="56" height="56" fill="#3a5a7a" stroke="${INK}" stroke-width="5"/>`;
    } else if (j === "awan") { const dx = (t * 12) % 200;
      g = `<g transform="translate(${dx} 0)" fill="#fff" opacity=".85"><ellipse cx="0" cy="0" rx="130" ry="46"/><ellipse cx="-70" cy="10" rx="80" ry="36"/><ellipse cx="80" cy="12" rx="90" ry="34"/><ellipse cx="10" cy="-30" rx="70" ry="44"/></g>`;
    } else if (j === "gua") { const w = o.warna || "#2b221c";
      g = `<path fill-rule="evenodd" d="M -1400 -1800 H 1400 V 1800 H -1400 Z M -430 300 C -470 -300 -300 -820 0 -840 C 300 -820 470 -300 430 300 Z" fill="${w}" stroke="${INK}" stroke-width="10"/><path d="M -430 300 C -470 -300 -300 -820 0 -840 C 300 -820 470 -300 430 300" fill="none" stroke="#5a4a3c" stroke-width="22" opacity=".7"/>`;
    } else if (j === "unta") { const w = o.warna || "#c99a5a", ay = Math.sin(t * 3) * 6;
      g = `<g fill="${w}" stroke="${INK}" stroke-width="6"><ellipse cx="0" cy="-230" rx="150" ry="70"/><path d="M -60 -290 Q -20 -380 30 -290 Z"/><path d="M 120 -250 Q 190 -330 190 -400 L 230 -410 Q 250 -390 230 -370 L 210 -360 Q 200 -300 150 -220 Z"/></g><g stroke="${w}" stroke-width="22" stroke-linecap="round"><line x1="-100" y1="-200" x2="${-110 + ay}" y2="0"/><line x1="-60" y1="-200" x2="${-50 - ay}" y2="0"/><line x1="70" y1="-200" x2="${60 + ay}" y2="0"/><line x1="110" y1="-200" x2="${120 - ay}" y2="0"/></g>`;
    } else if (j === "gedung") { // deretan gedung pencakar langit; o.tumbuh 0-1 = gedung naik dari tanah (berlomba meninggikan bangunan)
      const R = rng(o.seed || 3), n = o.n || 9, tb = v(o.tumbuh, t, d, 1), lebar = o.lebar || 1300, malam = o.malam != null ? o.malam : 0.6;
      for (let i = 0; i < n; i++) {
        const w = 90 + R() * 70, x0 = -lebar / 2 + (i + 0.5) * (lebar / n) - w / 2, hMax = 380 + R() * 620 * (o.tinggi || 1), k = clamp(tb * 1.4 - i * (0.4 / n) - R() * 0.2), h = hMax * halus(k);
        if (h < 2) continue;
        const siang = malam < 0.4, war = siang ? ["#6fa6d6", "#8bb8de", "#5b8fc0", "#a7c8e3", "#7aa9b8", "#e2d4bc"][i % 6] : ["#2c3550", "#35405e", "#28304a", "#3b4566"][i % 4];
        g += `<rect x="${x0}" y="${-h}" width="${w}" height="${h}" fill="${war}" stroke="${INK}" stroke-width="4"/><rect x="${x0 + w * 0.7}" y="${-h}" width="${w * 0.3}" height="${h}" fill="#000" opacity=".16"/><rect x="${x0 - 5}" y="${-h - 14}" width="${w + 10}" height="14" fill="${war}" stroke="${INK}" stroke-width="3"/>`;
        if (siang) { for (let yy = -h + 22; yy < -20; yy += 30) g += `<rect x="${x0 + 8}" y="${yy}" width="${w - 16}" height="16" fill="#eaf6ff" opacity="${0.35 + 0.25 * R()}"/>`; g += `<path d="M ${x0} ${-h * 0.35} L ${x0 + w * 0.55} ${-h} L ${x0 + w * 0.8} ${-h} L ${x0} ${-h * 0.1} Z" fill="#fff" opacity=".18"/>`; continue; }
        if (R() > 0.5) g += `<rect x="${x0 + w / 2 - 3}" y="${-h - 40}" width="6" height="40" fill="${war}"/><circle cx="${x0 + w / 2}" cy="${-h - 42}" r="6" fill="#ff5a5a" opacity="${0.5 + 0.5 * Math.sin(t * 4 + i)}"/>`;
        for (let yy = -h + 24; yy < -18; yy += 34) for (let xx = x0 + 14; xx < x0 + w - 18; xx += 26) if (R() > 0.35) g += `<rect x="${xx}" y="${yy}" width="12" height="18" fill="#ffd27a" opacity="${malam * (0.5 + 0.5 * R())}"/>`;
      }
      if (o.derek) { const dx = o.derek; g += `<g stroke="#f2b544" stroke-width="7" fill="none"><line x1="${dx}" y1="0" x2="${dx}" y2="-1150"/><line x1="${dx - 60}" y1="-1120" x2="${dx + 320}" y2="-1120"/><line x1="${dx}" y1="-1150" x2="${dx + 320}" y2="-1120"/><line x1="${dx + 250}" y1="-1120" x2="${dx + 250}" y2="${-1000 + 30 * Math.sin(t)}"/></g>`; }
    } else if (j === "hp") { // ponsel menyala di tangan
      g = `<rect x="-38" y="-70" width="76" height="140" rx="12" fill="#1d1520" stroke="${INK}" stroke-width="5"/><rect x="-30" y="-58" width="60" height="112" rx="6" fill="#7fb6ff"/><rect x="-24" y="-30" width="10" height="70" fill="#2c3550"/><rect x="-8" y="-50" width="12" height="90" fill="#2c3550"/><rect x="10" y="-10" width="14" height="50" fill="#2c3550"/><ellipse cx="0" cy="-40" rx="110" ry="140" fill="#9fd0ff" opacity=".18"/>`;
    } else if (j === "gerbang") { // gerbang bercahaya (pintu surga): o.buka 0-1 = daun pintu terbuka
      const bk = v(o.buka, t, d, 1), wn = o.warna || "#ffe2a0", id = "gb" + Math.round(x);
      g = `<defs><radialGradient id="${id}"><stop offset="0" stop-color="#ffffff" stop-opacity=".95"/><stop offset=".5" stop-color="${wn}" stop-opacity=".6"/><stop offset="1" stop-color="${wn}" stop-opacity="0"/></radialGradient></defs>
        <ellipse cx="0" cy="-330" rx="${380 * (0.3 + 0.7 * bk)}" ry="460" fill="url(#${id})" opacity="${0.4 + 0.6 * bk}"/>
        <path d="M -170 0 L -170 -420 Q -170 -620 0 -640 Q 170 -620 170 -420 L 170 0 Z" fill="#fff6dc" opacity="${0.25 + 0.65 * bk}"/>`;
      const dw = 170 * (1 - bk); // daun pintu menutup dari kiri & kanan
      if (dw > 1) g += `<path d="M -170 0 L -170 -420 Q -170 -620 0 -640 L ${-170 + dw} -630 L ${-170 + dw} 0 Z" fill="#6b4a2a" stroke="${INK}" stroke-width="6"/><path d="M 170 0 L 170 -420 Q 170 -620 0 -640 L ${170 - dw} -630 L ${170 - dw} 0 Z" fill="#6b4a2a" stroke="${INK}" stroke-width="6"/>`;
      g += `<path d="M -230 0 L -230 -430 Q -230 -690 0 -710 Q 230 -690 230 -430 L 230 0 L 170 0 L 170 -420 Q 170 -620 0 -640 Q -170 -620 -170 -420 L -170 0 Z" fill="#e8c56a" stroke="${INK}" stroke-width="8"/>`;
      for (let i = 0; i < 7; i++) { const a = Math.PI * (1.08 + i * 0.14); g += `<circle cx="${Math.cos(a) * 200}" cy="${-430 + Math.sin(a) * 240}" r="9" fill="#fff4cf"/>`; }
      if (o.nama) { const w2 = o.nama.length * 25 + 60; g += `<g font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" text-anchor="middle"><rect x="${-w2 / 2}" y="30" width="${w2}" height="74" rx="37" fill="#1d1520" opacity=".78"/><text y="80" font-size="44" fill="#ffe6a0">${esc(o.nama)}</text></g>`; }
    } else if (j === "jembatan_desa") { // jembatan desa: badan jembatan kayu/beton melintasi sungai, dengan pagar dan tiang penyangga
      const dek = o.warna || "#8a7257", pagar = o.warna_pagar || "#66513f", air = o.air || "#5b9aa0";
      const lebar = o.lebar || 1050, bentang = lebar / 2;
      // Sungai di bawah bentang; bentuk dan tepi jembatan tetap terlihat di atas tanah.
      g = `<path d="M ${-bentang - 120} 220 Q 0 130 ${bentang + 120} 220 L ${bentang + 120} 650 L ${-bentang - 120} 650 Z" fill="${air}" opacity=".92"/>
        <path d="M ${-bentang} 80 L ${bentang} 80 L ${bentang + 70} 170 L ${-bentang - 70} 170 Z" fill="${dek}" stroke="${INK}" stroke-width="10"/>
        <path d="M ${-bentang - 70} 170 L ${bentang + 70} 170" stroke="#4d4035" stroke-width="18"/>
        <path d="M ${-bentang} 70 L ${bentang} 70" stroke="${pagar}" stroke-width="22"/>
        <path d="M ${-bentang} 70 L ${-bentang} -115 M ${bentang} 70 L ${bentang} -115" stroke="${pagar}" stroke-width="18"/>
        <path d="M ${-bentang} -115 Q 0 -65 ${bentang} -115" stroke="${pagar}" stroke-width="18" fill="none"/>
        <path d="M ${-bentang} -25 L ${bentang} -25" stroke="${pagar}" stroke-width="14"/>
        <path d="M ${-bentang} 70 L ${-bentang} -115 M ${-bentang / 2} 70 L ${-bentang / 2} -90 M 0 70 L 0 -78 M ${bentang / 2} 70 L ${bentang / 2} -90 M ${bentang} 70 L ${bentang} -115" stroke="${pagar}" stroke-width="12"/>
        <path d="M ${-bentang - 35} 170 L ${-bentang - 35} 360 M ${bentang + 35} 170 L ${bentang + 35} 360" stroke="#625345" stroke-width="34"/>
        <path d="M ${-bentang - 80} 360 L ${bentang + 80} 360" stroke="#625345" stroke-width="28"/> `;
      for (let i = -4; i <= 4; i++) g += `<path d="M ${i * 115} 83 L ${i * 115 + 18} 166" stroke="#594938" stroke-width="7" opacity=".7"/>`;
    } else if (j === "jembatan") { // shirath: jembatan sangat tipis di atas jurang api
      let f = ""; for (let i = 0; i < 9; i++) { const ph = t * 5 + i * 1.3, h = 160 + 60 * Math.sin(ph), dx = (i - 4) * 120 + 20 * Math.sin(ph * 0.6); f += `<path d="M ${dx - 80} 260 Q ${dx - 40} ${260 - h * 0.6} ${dx} ${260 - h} Q ${dx + 40} ${260 - h * 0.6} ${dx + 80} 260 Z" fill="${["#ff5a1a", "#ff8a2a", "#ffb347"][i % 3]}" opacity=".85"/>`; }
      g = `<rect x="-700" y="40" width="1400" height="900" fill="#2a0a08"/><ellipse cx="0" cy="260" rx="760" ry="200" fill="#ff5a1a" opacity="${0.35 + 0.08 * Math.sin(t * 6)}"/>` + f +
        `<path d="M -700 -10 Q 0 ${30 + 4 * Math.sin(t * 2)} 700 -10" stroke="#e8d9c8" stroke-width="5" fill="none"/><path d="M -700 -10 Q 0 ${30 + 4 * Math.sin(t * 2)} 700 -10" stroke="#fff" stroke-width="1.5" fill="none" opacity=".8"/>`;
    } else if (j === "laut") { // permukaan laut malam: o.y = garis permukaan; o.pantul = x pantulan bulan (relatif)
      const id = "lt" + Math.round(y), px = o.pantul != null ? o.pantul : 0;
      g = `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1d3560"/><stop offset="1" stop-color="#040916"/></linearGradient></defs><rect x="-900" y="0" width="1800" height="1600" fill="url(#${id})"/>`;
      for (let i = 0; i < 9; i++) { const yy = 14 + i * i * 9, a = 30 + i * 6, ph = t * (1.2 - i * 0.06) + i; let dd = `M -900 ${yy}`; for (let xx = -900; xx <= 900; xx += 60) dd += ` L ${xx} ${yy + Math.sin(xx / a + ph) * (3 + i * 1.6)}`; g += `<path d="${dd}" stroke="#7fa6d8" stroke-width="${2 + i * 0.5}" fill="none" opacity="${0.35 - i * 0.025}"/>`; }
      for (let i = 0; i < 14; i++) { const yy = 10 + i * 26, w = 120 - i * 5 + 30 * Math.sin(t * 2 + i); g += `<ellipse cx="${px + 14 * Math.sin(t * 1.5 + i * 0.8)}" cy="${yy}" rx="${Math.max(10, w)}" ry="4" fill="#fff4cf" opacity="${0.55 - i * 0.035}"/>`; }
    } else if (j === "bawah_laut") { // kedalaman laut: berkas cahaya samar, gelembung naik, partikel
      const id = "bl" + Math.round(x), R = rng(o.seed || 21), terang = o.terang != null ? v(o.terang, t, d, 1) : 1;
      g = `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b4470"/><stop offset=".55" stop-color="#0a1f3a"/><stop offset="1" stop-color="#01040b"/></linearGradient></defs><rect x="-900" y="-1100" width="1800" height="2300" fill="url(#${id})"/>`;
      for (let i = 0; i < 5; i++) { const bx = -400 + i * 200 + 60 * Math.sin(t * 0.4 + i), w = 50 + 30 * Math.sin(t * 0.7 + i * 2); g += `<path d="M ${bx - w} -1100 L ${bx + w} -1100 L ${bx + w * 3 + 120} 300 L ${bx - w * 3 + 120} 300 Z" fill="#9fd0ff" opacity="${0.06 * terang}"/>`; }
      for (let i = 0; i < 26; i++) { const bx = (R() - 0.5) * 1000, sp = 40 + R() * 70, hh = ((R() * 1800 + t * sp) % 1800), r = 3 + R() * 8; g += `<circle cx="${bx + 10 * Math.sin(t * 2 + i)}" cy="${700 - hh}" r="${r}" fill="none" stroke="#cfe8ff" stroke-width="2" opacity="${0.45 * terang}"/>`; }
      for (let i = 0; i < 40; i++) { const bx = (R() - 0.5) * 1080, by = (R() - 0.5) * 2000; g += `<circle cx="${bx + 6 * Math.sin(t * 0.5 + i)}" cy="${by + 6 * Math.cos(t * 0.4 + i)}" r="${1.5 + R() * 2.5}" fill="#d8ecff" opacity="${(0.15 + 0.25 * Math.abs(Math.sin(t + i))) * terang}"/>`; }
    } else if (j === "ikan") { // ikan besar (paus) siluet berenang pelan; o.arah -1 = menghadap kiri
      const w = o.warna || "#1f3a5c", ek = Math.sin(t * 1.6) * 10, bob = Math.sin(t * 0.8) * 12, ar = o.arah || 1;
      g = `<g transform="translate(0 ${bob}) scale(${ar} 1)"><g transform="rotate(${ek} -440 0)"><path d="M -430 0 L -640 -150 Q -600 0 -640 150 Z" fill="${w}" stroke="${INK}" stroke-width="8" stroke-linejoin="round"/></g>
        <path d="M -450 0 Q -320 -190 80 -170 Q 400 -140 480 20 Q 400 160 80 150 Q -280 150 -450 0 Z" fill="${w}" stroke="${INK}" stroke-width="9"/>
        <path d="M -300 60 Q 80 160 420 70" stroke="#5f7fa6" stroke-width="10" fill="none" opacity=".55"/><path d="M -240 95 Q 80 175 380 100" stroke="#5f7fa6" stroke-width="6" fill="none" opacity=".4"/>
        <path d="M 40 60 Q 0 170 -90 190 Q -40 120 -40 70 Z" fill="${w}" stroke="${INK}" stroke-width="7"/>
        <path d="M 300 70 Q 380 60 470 30" stroke="${INK}" stroke-width="7" fill="none"/>
        <circle cx="330" cy="-20" r="16" fill="#e8f2ff"/><circle cx="334" cy="-20" r="8" fill="${INK}"/></g>`;
    } else if (j === "gelap") { // kegelapan menutup layar, menyisakan lingkaran cahaya kecil di (x,y) berjari-jari o.r
      const id = "gl" + Math.round(x * 7 + y), r = v(o.r, t, d, 160);
      g = `<defs><radialGradient id="${id}" cx="0" cy="0" r="${r}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset=".55" stop-color="#000" stop-opacity=".35"/><stop offset="1" stop-color="#000" stop-opacity="${o.pekat != null ? o.pekat : 0.97}"/></radialGradient></defs><rect x="-3000" y="-3000" width="6000" height="6000" fill="url(#${id})"/>`;
    } else if (j === "makam") { // gundukan tanah + nisan; o.n = jumlah makam berjejer, o.baru = gundukan segar
      const n = o.n || 1, w = o.warna || "#5a4636";
      for (let i = 0; i < n; i++) { const dx = (i - (n - 1) / 2) * (o.jarak || 300), k = i === Math.floor(n / 2) ? 1 : 0.75;
        g += `<g transform="translate(${dx} 0) scale(${k})"><path d="M -150 0 Q -140 -70 0 -80 Q 140 -70 150 0 Z" fill="${o.baru && k === 1 ? "#6e5440" : w}" stroke="${INK}" stroke-width="6"/>
          <path d="M -30 -70 L -30 -230 Q 0 -260 30 -230 L 30 -70 Z" fill="#cfc6b8" stroke="${INK}" stroke-width="6"/><path d="M -14 -190 L 14 -190 M -14 -160 L 14 -160" stroke="#8a8070" stroke-width="5"/>`;
        if (o.baru && k === 1) for (let f = 0; f < 6; f++) g += `<circle cx="${-100 + f * 40}" cy="${-40 - (f % 2) * 14}" r="9" fill="#e8a0b0" stroke="${INK}" stroke-width="3"/>`;
        g += `</g>`; }
    } else if (j === "jendela") { // jendela kamar dengan cahaya Subuh masuk; o.terang 0-1
      const tr = v(o.terang, t, d, 1);
      g = `<rect x="-1400" y="-2400" width="2800" height="4000" fill="#2b2a3a"/><path d="M -150 -380 L 150 -380 L 520 900 L -380 900 Z" fill="#ffe7b8" opacity="${0.18 * tr}"/>
        <rect x="-170" y="-400" width="340" height="420" fill="${tr > 0.05 ? "#ffd9a0" : "#1a2040"}" opacity="${0.4 + 0.6 * tr}" stroke="#6b4a30" stroke-width="18"/>
        <path d="M 0 -400 L 0 20 M -170 -190 L 170 -190" stroke="#6b4a30" stroke-width="12"/><rect x="-1400" y="420" width="2800" height="800" fill="#3d3446"/>`;
    } else if (j === "sapu") { // sapu ijuk; o.rot = sudut (derajat), pangkal di (0,0)
      const r = v(o.rot, t, d, 0);
      g = `<g transform="rotate(${r})"><rect x="-8" y="-420" width="16" height="360" rx="6" fill="#b07a3a" stroke="${INK}" stroke-width="5"/>
        <path d="M -60 -60 L 60 -60 L 85 70 L -85 70 Z" fill="#6b4a2a" stroke="${INK}" stroke-width="6"/><rect x="-62" y="-78" width="124" height="26" rx="6" fill="#c0392b" stroke="${INK}" stroke-width="5"/>`;
      for (let i = -70; i <= 70; i += 14) g += `<line x1="${i * 0.8}" y1="-50" x2="${i}" y2="68" stroke="#3d2a18" stroke-width="3"/>`;
      g += `</g>`;
    } else if (j === "nur") { // cahaya lembut setinggi orang menandai nabi (TIDAK digambar sosoknya): fokus, tidak silau, nama di bawah
      const wn = o.warna || "#fff1c4", den = 0.92 + 0.08 * Math.sin(t * 2.2), id = "nur" + Math.round(x);
      g = `<defs><radialGradient id="${id}a"><stop offset="0" stop-color="#ffffff" stop-opacity=".95"/><stop offset=".35" stop-color="${wn}" stop-opacity=".75"/><stop offset="1" stop-color="${wn}" stop-opacity="0"/></radialGradient>
        <linearGradient id="${id}b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${wn}" stop-opacity="0"/><stop offset=".55" stop-color="${wn}" stop-opacity=".45"/><stop offset="1" stop-color="${wn}" stop-opacity=".15"/></linearGradient></defs>
        <ellipse cx="0" cy="0" rx="260" ry="54" fill="${wn}" opacity="${0.35 * den}"/>
        <path d="M -70 -1300 L 70 -1300 L 150 0 L -150 0 Z" fill="url(#${id}b)"/>
        <ellipse cx="0" cy="-300" rx="${150 * den}" ry="${330 * den}" fill="url(#${id}a)"/>
        <ellipse cx="0" cy="-300" rx="46" ry="200" fill="#ffffff" opacity="${0.55 * den}"/>`;
      const R = rng(o.seed || 5); for (let i = 0; i < 14; i++) { const h = ((R() * 700 + t * (40 + R() * 40)) % 700), bx = (R() - 0.5) * 220; g += `<circle cx="${bx}" cy="${-h}" r="${2 + R() * 4}" fill="#fff" opacity="${0.6 * (1 - h / 700)}"/>`; }
      if (o.nama) { const nm = esc(o.nama), w2 = o.nama.length * 25 + 60; g += `<g transform="scale(${o.nama_s || 1})" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" text-anchor="middle"><rect x="${-w2 / 2}" y="40" width="${w2}" height="74" rx="37" fill="#1d1520" opacity=".78"/><text y="90" font-size="44" fill="#ffe6a0">${nm}</text></g>`; }
    } else if (j === "jenazah") { // jenazah berkafan putih di atas keranda kayu (sopan, tanpa wajah); o.kain = warna kain penutup opsional
      const kw = "#7a5432";
      g = `<ellipse cx="0" cy="40" rx="430" ry="34" fill="#000" opacity=".25"/>
        <line x1="-470" y1="-60" x2="470" y2="-60" stroke="${kw}" stroke-width="26" stroke-linecap="round"/><line x1="-470" y1="-60" x2="470" y2="-60" stroke="${INK}" stroke-width="4" opacity=".4"/>
        <rect x="-360" y="-60" width="22" height="90" fill="${kw}" stroke="${INK}" stroke-width="5"/><rect x="338" y="-60" width="22" height="90" fill="${kw}" stroke="${INK}" stroke-width="5"/>
        <rect x="-370" y="-88" width="740" height="34" rx="8" fill="#9a7048" stroke="${INK}" stroke-width="6"/>`;
      if (o.kain) g += `<path d="M -350 -88 Q -360 -230 -200 -238 L 230 -238 Q 360 -230 350 -88 Z" fill="${o.kain}" stroke="${INK}" stroke-width="7"/><path d="M -300 -120 L 300 -120" stroke="#ffd27a" stroke-width="6" opacity=".7"/>`;
      else { g += `<path d="M -330 -88 Q -350 -190 -250 -196 L 220 -186 Q 350 -176 340 -88 Z" fill="#f6f1e6" stroke="${INK}" stroke-width="7"/><ellipse cx="-262" cy="-150" rx="70" ry="54" fill="#fbf8f1" stroke="${INK}" stroke-width="6"/>`;
        [-262 - 64, -150, 40, 250].forEach((bx, i) => { g += `<path d="M ${bx} ${i ? -184 : -176} q 8 50 0 ${i ? 96 : 84}" stroke="#d9cfbf" stroke-width="12" fill="none"/>`; });
        g += `<path d="M -200 -170 Q 0 -150 300 -150" stroke="#e2d9c8" stroke-width="5" fill="none"/>`; }
    } else if (j === "kitab" || (j === "buku" && CERAH)) { // kitab di meja (buku lama otomatis jadi kitab pada gaya cerah, dipusatkan di 540,1000)
      g = j === "kitab" ? kitab(o, t, d) : `<g transform="scale(${1 / sc}) translate(${540 - x} ${1000 - y}) scale(.92)">${kitab(o, t, d)}</g>`;
    } else if (j === "buku") { // kitab terbuka + label sumber: {teks (baris di halaman), sub (pil sumber), buka 0-1}
      const bk = clamp(v(o.buka, t, d, 1));
      g = `<ellipse cx="0" cy="40" rx="330" ry="30" fill="#000" opacity=".25"/><path d="M -320 20 L 0 0 L 320 20 L 320 -360 L 0 -380 L -320 -360 Z" fill="#6b2a2a" stroke="${INK}" stroke-width="7"/>
        <path d="M 0 -10 L -${300 * bk} 8 L -${300 * bk} -350 L 0 -372 Z" fill="#fbf3dc" stroke="${INK}" stroke-width="6"/><path d="M 0 -10 L 300 8 L 300 -350 L 0 -372 Z" fill="#fbf3dc" stroke="${INK}" stroke-width="6"/><line x1="0" y1="-372" x2="0" y2="-10" stroke="#c9b48a" stroke-width="6"/>`;
      for (let i = 0; i < 7; i++) { const yy = -320 + i * 40; if (bk > 0.5) g += `<line x1="${-260}" y1="${yy + 2}" x2="${-40}" y2="${yy - 4}" stroke="#b9a882" stroke-width="5" opacity="${o.teks ? 0.35 : 0.7}"/>`; g += `<line x1="40" y1="${yy - 4}" x2="260" y2="${yy + 2}" stroke="#b9a882" stroke-width="5" opacity="${o.teks ? 0.35 : 0.7}"/>`; }
      if (o.teks) { // (27 Nov) teks dibungkus dan dikecilkan agar selalu di dalam halaman (lebar 560, maks 5 baris)
        const lebarMaks = 560, kar = 0.6;
        let fs = o.ukuran || 54, baris = [];
        for (; fs >= 26; fs -= 4) {
          const maksKar = Math.floor(lebarMaks / (fs * kar)); baris = [];
          String(o.teks).split("\n").forEach((p0) => { let cur = "";
            p0.split(/\s+/).forEach((w) => { if (cur && (cur + " " + w).length > maksKar) { baris.push(cur); cur = w; } else cur = cur ? cur + " " + w : w; });
            if (cur) baris.push(cur); });
          if (baris.length * fs * 1.25 <= 300 && Math.max(...baris.map((b) => b.length)) <= maksKar) break;
        }
        const y0 = -190 - (baris.length - 1) * fs * 1.25 / 2;
        baris.forEach((tx, i) => { g += `<text x="0" y="${y0 + i * fs * 1.25}" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" font-size="${fs}" text-anchor="middle" fill="#3a1f1a">${esc(tx)}</text>`; });
      };
      if (o.sub) { const w2 = o.sub.length * 25 + 70; g += `<g font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" text-anchor="middle"><rect x="${-w2 / 2}" y="60" width="${w2}" height="80" rx="40" fill="#1d1520" opacity=".85"/><text y="114" font-size="46" fill="#ffd27a">${esc(o.sub)}</text></g>`; }
    } else if (j === "kartu_dalil") { // kartu dalil 2D: {kitab:"HR. Bukhari", no:"6507", teks, sorot:"frasa", arab:"teks Arab terverifikasi", label:"DALIL", ukuran, sorot_at}
      const W = 780, tt = tl, masuk = halus(tt / 0.45), ov = tt < 0.45 ? 1 + (1 - masuk) * 0.0 : 1;
      const k = 0.55 + 0.45 * masuk + (tt > 0.45 && tt < 0.7 ? Math.sin((tt - 0.45) / 0.25 * Math.PI) * 0.03 : 0);
      const rot = (1 - masuk) * -9 + Math.sin(tt * 1.3) * 0.6, melayang = Math.sin(tt * 1.6) * 8;
      let uk = o.ukuran || 54, baris = [], cw, lh;
      const kata = String(o.teks || "").replace(/\s+/g, " ").trim().split(" ").filter(Boolean);
      for (; uk >= 30; uk -= 2) { cw = uk * 0.6; lh = uk * 1.3; const mk = Math.floor((W - 90) / cw); baris = []; let cur = ""; kata.forEach((w) => { if (cur && (cur + " " + w).length > mk) { baris.push(cur); cur = w; } else cur = cur ? cur + " " + w : w; }); if (cur) baris.push(cur); if (baris.length * lh <= (o.arab ? 380 : 520)) break; }
      const adaArab = !!o.arab, au = o.arab_ukuran || 56, alh = au * 1.35;
      let abaris = [];
      if (adaArab) { const akata = String(o.arab).replace(/\s+/g, " ").trim().split(" ").filter(Boolean), acw = au * 0.62, amaxw = W - 90; let acur = "";
        akata.forEach((w) => { const test = acur ? acur + " " + w : w; if (acur && test.length * acw > amaxw) { abaris.push(acur); acur = w; } else acur = test; });
        if (acur) abaris.push(acur); }
      const arabH = adaArab ? abaris.length * alh + 70 : 0, H = 330 + arabH + baris.length * lh + 80, top = -H / 2;
      g = `<g transform="translate(0 ${melayang}) rotate(${rot}) scale(${k})" opacity="${clamp(tt / 0.15)}">
        <defs><linearGradient id="kdk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fffaf0"/><stop offset="1" stop-color="#f1e3c3"/></linearGradient>
        <linearGradient id="kdh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#0d4a3a"/><stop offset="1" stop-color="#1b7a5c"/></linearGradient>
        <clipPath id="kdc"><rect x="${-W / 2}" y="${top}" width="${W}" height="${H}" rx="34"/></clipPath></defs>
        <rect x="${-W / 2 + 10}" y="${top + 16}" width="${W}" height="${H}" rx="34" fill="#000" opacity=".35"/>
        <rect x="${-W / 2}" y="${top}" width="${W}" height="${H}" rx="34" fill="url(#kdk)" stroke="#e8c26a" stroke-width="12"/>
        <rect x="${-W / 2 + 22}" y="${top + 22}" width="${W - 44}" height="${H - 44}" rx="22" fill="none" stroke="#b07a2a" stroke-width="3" opacity=".8"/>`;
      // pola bintang delapan samar + sudut berornamen
      for (let i = 0; i < 5; i++) for (let j2 = 0; j2 < 7; j2++) { const px = -W / 2 + 60 + i * 165, py = top + 200 + j2 * ((H - 260) / 6); g += `<path d="M ${px} ${py - 18} L ${px + 6} ${py - 6} L ${px + 18} ${py} L ${px + 6} ${py + 6} L ${px} ${py + 18} L ${px - 6} ${py + 6} L ${px - 18} ${py} L ${px - 6} ${py - 6} Z" fill="#b07a2a" opacity=".07"/>`; }
      [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([sx, sy]) => { const cx = sx * (W / 2 - 40), cy = (sy < 0 ? top + 40 : top + H - 40); g += `<path d="M ${cx} ${cy} q ${-sx * 50} 0 ${-sx * 50} ${sy * 50}" stroke="#b07a2a" stroke-width="5" fill="none"/><circle cx="${cx - sx * 22}" cy="${cy + sy * 22}" r="7" fill="#e8c26a" stroke="#b07a2a" stroke-width="2"/>`; });
      // pita hijau + label
      g += `<g clip-path="url(#kdc)"><rect x="${-W / 2}" y="${top}" width="${W}" height="150" fill="url(#kdh)"/><path d="M ${-W / 2} ${top + 150} H ${W / 2}" stroke="#e8c26a" stroke-width="8"/></g>
        <text x="0" y="${top + 62}" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" font-size="34" data-hias="1" letter-spacing="8" text-anchor="middle" fill="#e8c26a">${esc(o.label || "DALIL")}</text>
        <text x="0" y="${top + 124}" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" font-size="${Math.min(60, 640 / Math.max(8, String(o.kitab || "").length * 0.62))}" text-anchor="middle" fill="#fffaf0">${esc(o.kitab || "")}</text>`;
      // stempel nomor menghentak di 0.5 dtk
      const ts = tt - 0.5, ks = ts < 0 ? 0 : ts < 0.2 ? 2.2 - 1.2 * halus(ts / 0.2) : 1, gx = ts > 0 && ts < 0.25 ? Math.sin(ts * 120) * 6 * (1 - ts / 0.25) : 0;
      if (ts > 0 && o.no) g += `<g transform="translate(${W / 2 - 170 + gx} ${top + H - 20}) rotate(-8) scale(${ks})" opacity="${clamp(ts / 0.08)}"><rect x="-130" y="-52" width="260" height="104" rx="16" fill="#fffaf0" fill-opacity=".9" stroke="#b3261e" stroke-width="9"/><text x="0" y="22" font-family="Tangan, DejaVu Sans, sans-serif" font-weight="700" font-size="${String(o.no).length > 6 ? 54 : 70}" text-anchor="middle" fill="#b3261e">${/^\d/.test(String(o.no)) ? "No. " : ""}${esc(o.no)}</text></g>`;
      let yy = top + 190 + 36;
      if (adaArab) { const ap = halus((tt - 0.7) / 0.5), ay0 = yy + 70;
        g += `<g opacity="${ap}" direction="rtl" unicode-bidi="bidi-override" font-family="Noto Naskh Arabic, Noto Sans Arabic, serif" font-weight="700" font-size="${au}" text-anchor="middle" fill="#0d4a3a">` +
          abaris.map((b, i) => `<text x="0" y="${ay0 + i * alh}">${esc(b)}</text>`).join("") + `</g>`;
        const garisY = ay0 + (abaris.length - 1) * alh + 48;
        g += `<path d="M -200 ${garisY} H 200" stroke="#b07a2a" stroke-width="3" opacity="${ap}"/><circle cx="0" cy="${garisY}" r="8" fill="#e8c26a" stroke="#b07a2a" stroke-width="2"/>`;
        yy = garisY + 72; }
      // isi: tulisan muncul kiri-ke-kanan, sorot kuning
      const tot = Math.max(1, baris.join("").length), t0 = o.tulis_at != null ? o.tulis_at : (adaArab ? 1.3 : 0.9), dur = o.tulis != null ? o.tulis : Math.min(4, 0.8 + tot * 0.035);
      let maju = clamp((tt - t0) / dur) * tot; const gab = baris.join(" "), X0 = -((W - 90) / 2), sel = [];
      if (o.sorot) { const i0 = gab.toLowerCase().indexOf(String(o.sorot).toLowerCase()), sa = o.sorot_at != null ? o.sorot_at : t0 + dur + 0.2 - (o.at || 0) * 0, sp = clamp((tt - sa) / 0.6);
        if (i0 >= 0 && sp > 0) { let pos = 0, dulu = 0; const i1 = i0 + String(o.sorot).length, tl2 = i1 - i0; baris.forEach((b, i) => { const a = Math.max(i0, pos), z = Math.min(i1, pos + b.length); if (z > a) { const n = z - a, f = clamp((sp * tl2 - dulu) / n); dulu += n; if (f > 0) sel.push([i, a - pos, n * f]); } pos += b.length + 1; }); } }
      const yb = yy + uk * 0.9;
      sel.forEach(([i, a, n]) => { g += `<rect x="${X0 + a * cw - 5}" y="${yb + i * lh - uk * 0.85}" width="${n * cw + 10}" height="${uk * 1.1}" rx="10" fill="#ffd93a" opacity=".75"/>`; });
      baris.forEach((b, i) => { const f = clamp(maju / b.length); maju -= b.length; if (f <= 0) return; const ww = b.length * cw, ly = yb + i * lh;
        g += `<clipPath id="kdt${i}"><rect x="${X0 - 8}" y="${ly - uk}" width="${ww * f + 10}" height="${uk * 1.4}"/></clipPath><text clip-path="url(#kdt${i})" x="${X0}" y="${ly}" textLength="${ww}" lengthAdjust="spacing" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" font-size="${uk}" fill="#2b2140">${esc(b)}</text>`; });
      // kilau emas menyapu kartu
      const sw = clamp((tt - 0.35) / 0.7); if (sw > 0 && sw < 1) g += `<g clip-path="url(#kdc)"><path d="M ${-W / 2 - 200 + sw * (W + 500)} ${top - 20} l 90 0 l -140 ${H + 40} l -90 0 Z" fill="#fff6c8" opacity=".55"/></g>`;
      g += `</g>`;
    } else if (j === "ponsel") { // HP besar (bidikan dekat) dengan notifikasi: {judul, teks, jam, getar 0-1, notif_at (detik relatif shot), merah}
      const gt = v(o.getar, t, d, 0), dx = Math.sin(t * 70) * 14 * gt, rot = Math.sin(t * 55) * 2.2 * gt, na = o.notif_at != null ? o.notif_at : 0, np = o.notif === false ? 0 : clamp((t - na) / 0.25);
      g = `<g transform="translate(${dx} 0) rotate(${rot})"><rect x="-270" y="-540" width="540" height="1080" rx="64" fill="#15121a" stroke="${INK}" stroke-width="10"/><rect x="-244" y="-512" width="488" height="1024" rx="44" fill="#1c2340"/>
        <rect x="-60" y="-498" width="120" height="26" rx="13" fill="#0b0a10"/>
        <text x="0" y="-330" font-family="DejaVu Sans, Arial, sans-serif" font-weight="300" font-size="130" text-anchor="middle" fill="#e8ecff">${esc(o.jam || "07.00")}</text>
        <text x="0" y="-268" font-family="DejaVu Sans, Arial, sans-serif" font-size="34" text-anchor="middle" fill="#b9c0e0">${esc(o.tanggal || "Kamis, 5 November")}</text>`;
      if (np > 0) { const yy = -200 + (1 - np) * -60, mr = o.merah !== false;
        g += `<g opacity="${np}"><rect x="-236" y="${yy}" width="472" height="190" rx="30" fill="#f6f2ea"/><rect x="-200" y="${yy + 28}" width="56" height="56" rx="14" fill="${mr ? "#e03131" : "#2f6fd6"}"/><text x="-172" y="${yy + 68}" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" font-size="34" text-anchor="middle" fill="#fff">!</text>
          <text x="-126" y="${yy + 52}" font-family="DejaVu Sans, Arial, sans-serif" font-size="26" fill="#6a6470">${esc(o.aplikasi || "Pengingat")} · sekarang</text>
          <text x="-126" y="${yy + 96}" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" font-size="31" fill="${mr ? "#c92a2a" : INK}">${esc(o.judul || "Jatuh tempo HARI INI")}</text>
          <text x="-126" y="${yy + 140}" font-family="DejaVu Sans, Arial, sans-serif" font-size="30" fill="#3a3440">${esc(o.teks || "Cicilan belum dibayar")}</text></g>`;
        if (gt > 0.05) for (let i = 0; i < 3; i++) g += `<path d="M ${290 + i * 26} ${-120 - i * 20} q 18 40 0 80 M ${-290 - i * 26} ${-120 - i * 20} q -18 40 0 80" stroke="#fff" stroke-width="7" fill="none" opacity="${gt * (0.8 - i * 0.2)}"/>`; }
      g += `</g>`;
    } else if (j === "chat") { // HP layar chat: {nama, pesan:[[at, teks, waktu, kanan]], bisu, ketik:{at, teks, kirim}}
      const F = "DejaVu Sans, Arial, sans-serif";
      g = `<rect x="-270" y="-540" width="540" height="1080" rx="64" fill="#15121a" stroke="${INK}" stroke-width="10"/><rect x="-244" y="-512" width="488" height="1024" rx="44" fill="#efe7dc"/><rect x="-244" y="-512" width="488" height="140" rx="44" fill="#2f6f5e"/><rect x="-244" y="-420" width="488" height="48" fill="#2f6f5e"/>
        <circle cx="-170" cy="-430" r="34" fill="#f2d48a" stroke="#fff" stroke-width="4"/><text x="-120" y="-420" font-family="${F}" font-weight="800" font-size="36" fill="#fff">${esc(o.nama || "Teman")}</text>` + (o.bisu ? `<text x="-120" y="-386" font-family="${F}" font-size="24" fill="#cfe6de">dibisukan</text>` : "");
      let yy = -330;
      (o.pesan || []).forEach(([at, tx, wkt, kanan]) => { const pp = clamp((t - at) / 0.3); if (pp <= 0) return; const W = Math.min(400, String(tx).length * 19 + 60), x0 = kanan ? 220 - W : -220;
        g += `<g opacity="${pp}" transform="translate(0 ${(1 - pp) * 30})"><rect x="${x0}" y="${yy}" width="${W}" height="92" rx="22" fill="${kanan ? "#d6f5c8" : "#fff"}" stroke="#c9bfb2" stroke-width="2"/><text x="${x0 + 24}" y="${yy + 44}" font-family="${F}" font-size="30" fill="${INK}">${esc(tx)}</text><text x="${x0 + W - 18}" y="${yy + 78}" font-family="${F}" font-size="20" text-anchor="end" fill="#8a8078">${esc(wkt || "")}${kanan ? " ✓✓" : ""}</text></g>`; yy += 120; });
      const K = o.ketik; let isi = "";
      if (K) { const kt = t - K.at; if (kt > 0) isi = String(K.teks).slice(0, Math.floor(kt * 16)); }
      g += `<rect x="-224" y="400" width="370" height="76" rx="38" fill="#fff" stroke="#c9bfb2" stroke-width="2"/><text x="-196" y="450" font-family="${F}" font-size="28" fill="${isi ? INK : "#a09890"}">${esc(isi || "Ketik pesan…")}</text><circle cx="196" cy="438" r="38" fill="#2f6f5e"/><path d="M 180 420 L 216 438 L 180 456 Z" fill="#fff"/>`;
      if (K && K.kirim != null && t > K.kirim) { const W = Math.min(400, String(K.teks).length * 19 + 60), pp = clamp((t - K.kirim) / 0.3); g += `<g opacity="${pp}"><rect x="${220 - W}" y="${yy}" width="${W}" height="92" rx="22" fill="#d6f5c8" stroke="#c9bfb2" stroke-width="2"/><text x="${244 - W}" y="${yy + 44}" font-family="${F}" font-size="30" fill="${INK}">${esc(K.teks)}</text><text x="202" y="${yy + 78}" font-family="${F}" font-size="20" text-anchor="end" fill="#3b8fd9">${esc(K.waktu || "")} ✓✓</text></g>`; }
    } else if (j === "kue") { // kue ulang tahun kecil + lilin menyala: {nyala 0-1}
      const ny = clamp(v(o.nyala, t, d, 1)), fl = 1 + 0.12 * Math.sin(t * 13) + 0.06 * Math.sin(t * 29);
      g = `<ellipse cx="0" cy="10" rx="190" ry="26" fill="#000" opacity=".25"/><rect x="-160" y="-150" width="320" height="160" rx="24" fill="#f3d9e4" stroke="${INK}" stroke-width="7"/><path d="M -160 -110 q 40 30 80 0 t 80 0 t 80 0 t 80 0" fill="none" stroke="#e88aa8" stroke-width="14"/><rect x="-160" y="-170" width="320" height="40" rx="20" fill="#fff6f0" stroke="${INK}" stroke-width="6"/>
        <rect x="-12" y="-270" width="24" height="100" rx="6" fill="#7fb3e8" stroke="${INK}" stroke-width="5"/>`;
      if (ny > 0) g += `<circle cx="0" cy="-300" r="${120 * ny}" fill="#ffd27a" opacity="${0.18 * ny}"/><g transform="translate(0 -300) scale(${ny * fl})"><path d="M 0 -36 q 24 32 0 60 q -24 -28 0 -60 Z" fill="#ffb347" stroke="#e8743a" stroke-width="3"/></g>`;
    } else if (j === "kalender") { // kalender dinding, tanggal dilingkari merah: {bulan, tgl, mulai (indeks hari tgl 1, 0=Sen), lingkar 0-1, teks}
      const lk = clamp(v(o.lingkar, t, d, 1)), mulai = o.mulai || 0, hari = o.hari || 30, tg = o.tgl || 5, sel = 104;
      g = `<rect x="-400" y="-560" width="800" height="900" rx="20" fill="#fbf7ee" stroke="${INK}" stroke-width="8"/><rect x="-400" y="-560" width="800" height="150" rx="20" fill="#c0392b"/><rect x="-400" y="-440" width="800" height="30" fill="#c0392b"/>
        <text x="0" y="-460" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" font-size="70" text-anchor="middle" fill="#fff">${esc(o.bulan || "NOVEMBER")}</text>`;
      ["S", "S", "R", "K", "J", "S", "M"].forEach((h, i) => { g += `<text x="${-312 + i * sel}" y="-350" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" font-size="34" text-anchor="middle" fill="${i === 6 ? "#c0392b" : "#6a6470"}">${h}</text>`; });
      for (let n = 1; n <= hari; n++) { const k = n - 1 + mulai, cx = -312 + (k % 7) * sel, cy = -270 + Math.floor(k / 7) * 110; g += `<text x="${cx}" y="${cy}" font-family="DejaVu Sans, Arial, sans-serif" font-weight="${n === tg ? 800 : 400}" font-size="44" text-anchor="middle" fill="${n === tg ? "#c0392b" : INK}">${n}</text>`;
        if (n === tg && lk > 0) { const L = 2 * Math.PI * 58; g += `<ellipse cx="${cx}" cy="${cy - 14}" rx="60" ry="50" fill="none" stroke="#e03131" stroke-width="10" stroke-linecap="round" stroke-dasharray="${L}" stroke-dashoffset="${L * (1 - lk)}" transform="rotate(-20 ${cx} ${cy - 14})"/>`;
          if (o.teks && lk > 0.9) g += `<text x="${cx}" y="${cy - 80}" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" font-size="34" stroke="#fbf7ee" stroke-width="10" paint-order="stroke" text-anchor="middle" fill="#e03131">${esc(o.teks)}</text>`; } }
    } else if (j === "koin") { // koin emas (dinar): {n, jatuh 0-1}
      const n = o.n || 3, jt = clamp(v(o.jatuh, t, d, 1));
      g = `<defs><radialGradient id="kng" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#fff6c8"/><stop offset=".5" stop-color="#f2c24a"/><stop offset="1" stop-color="#c08a1a"/></radialGradient></defs>`;
      for (let i = 0; i < n; i++) { const cx = (i - (n - 1) / 2) * 150, cy = -60 - (1 - halus(clamp(jt * 1.6 - i * 0.25))) * 700, kl = 0.7 + 0.3 * Math.abs(Math.sin(t * 2 + i)), ks = 0.6 + 0.4 * Math.sin(t * 3 + i * 2);
        let tt = ""; for (let k = 0; k < 16; k++) { const a = (k / 16) * Math.PI * 2; tt += `<circle cx="${Math.cos(a) * 60}" cy="${Math.sin(a) * 60}" r="3.4" fill="#fff0b0" opacity=".9"/>`; }
        g += `<g transform="translate(${cx} ${cy})"><circle r="125" fill="#ffd27a" opacity="${0.18 * kl}"/><circle cy="9" r="68" fill="#9a6a10" stroke="${INK}" stroke-width="6"/><circle r="68" fill="url(#kng)" stroke="${INK}" stroke-width="6"/><circle r="53" fill="none" stroke="#b07a12" stroke-width="4"/>${tt}
          <rect x="-24" y="-24" width="48" height="48" fill="none" stroke="#a06a0e" stroke-width="4"/><rect x="-24" y="-24" width="48" height="48" fill="none" stroke="#a06a0e" stroke-width="4" transform="rotate(45)"/><circle r="10" fill="#c8901e"/>
          <path d="M -44 -30 a 54 54 0 0 1 34 -22" stroke="#fffbe6" stroke-width="7" fill="none" stroke-linecap="round" opacity="${kl}"/>${bintik4(46, -46, 18 * ks, ks)}</g>`; }
    } else if (j === "uang") { // tumpukan uang kertas generik dikipas: {n, kipas 0-1, nilai}
      const n = o.n || 5, kp = clamp(v(o.kipas, t, d, 1)), W = ["#e57f8a", "#6f9fd8", "#e57f8a", "#7fbf8a", "#e57f8a", "#6f9fd8"];
      g = `<ellipse cx="0" cy="110" rx="200" ry="24" fill="#000" opacity=".2"/>`;
      for (let i = 0; i < n; i++) g += `<g transform="rotate(${(i - (n - 1) / 2) * 13 * kp} 0 140) translate(0 ${-i * 3})">${lembar(W[i % W.length], o.nilai || "100")}</g>`;
      g += `<rect x="-26" y="-74" width="52" height="148" fill="#c9a24a" opacity="${1 - kp}" stroke="${INK}" stroke-width="3"/>`;
    } else if (j === "amplop") { // amplop uang
      g = `<rect x="-95" y="-60" width="190" height="120" rx="10" fill="#fbf6ea" stroke="${INK}" stroke-width="6"/><path d="M -95 -60 L 0 10 L 95 -60" fill="none" stroke="${INK}" stroke-width="5"/>` + (o.uang !== false ? `<rect x="-70" y="-82" width="120" height="40" rx="4" fill="#7fbf8a" stroke="${INK}" stroke-width="4" transform="rotate(-6)"/>` : "");
    } else if (j === "dompet") { // dompet terbuka; o.isi = jumlah lembar 0-3 (tipis = 1)
      const n = Math.round(v(o.isi, t, d, 1));
      g = [...Array(n)].map((_, i) => `<g transform="translate(${-5 + i * 16} ${-85 + i * 6}) rotate(${-8 + i * 5}) scale(.5)">${lembar(["#7fbf8a", "#6f9fd8", "#e57f8a"][i % 3])}</g>`).join("") +
        `<rect x="-120" y="-80" width="240" height="150" rx="22" fill="#7a4a32" stroke="${INK}" stroke-width="7"/><rect x="-120" y="-80" width="240" height="60" rx="22" fill="#8e5a3e" stroke="${INK}" stroke-width="6"/><circle cx="85" cy="-48" r="10" fill="#e9d2a0"/>`;
    } else if (j === "obat") { // botol obat + strip
      g = `<rect x="-60" y="-130" width="90" height="130" rx="16" fill="#f3efe6" stroke="${INK}" stroke-width="6"/><rect x="-66" y="-150" width="102" height="34" rx="8" fill="#ff8a6a" stroke="${INK}" stroke-width="5"/><path d="M -40 -70 h 50 M -15 -95 v 50" stroke="#ff6b6b" stroke-width="10"/><rect x="50" y="-60" width="110" height="60" rx="8" fill="#cfd8e0" stroke="${INK}" stroke-width="5"/>` + [0, 1, 2].map((i) => `<circle cx="${75 + i * 30}" cy="-30" r="10" fill="#fff"/>`).join("");
    } else if (j === "kasur") { // kasur dilihat dari kaki ranjang; permukaan duduk y -130 (pas dengan pose duduk). {w, seprai, selimut, kayu}
      const W = o.w || 540, K = o.kayu || "#8a5a36", S = o.seprai || "#e9eef6", B = o.selimut || "#3f5f9a", gl = (c, f) => warna(c, "#000000", f);
      g = `<ellipse cx="0" cy="6" rx="${W * 0.56}" ry="18" fill="#000" opacity=".22"/>
        <rect x="${-W / 2 + 14}" y="-360" width="${W - 28}" height="240" rx="14" fill="${K}" stroke="${INK}" stroke-width="6"/><rect x="${-W / 2 + 36}" y="-336" width="${W - 72}" height="160" rx="8" fill="${gl(K, 0.15)}"/>
        <ellipse cx="${-W * 0.2}" cy="-176" rx="${W * 0.2}" ry="34" fill="#fbfbf6" stroke="${INK}" stroke-width="5"/><ellipse cx="${W * 0.2}" cy="-176" rx="${W * 0.2}" ry="34" fill="#f2efe6" stroke="${INK}" stroke-width="5"/>
        <path d="M ${-W / 2} -150 L ${W / 2} -150 L ${W / 2} -70 L ${-W / 2} -70 Z" fill="${S}" stroke="${INK}" stroke-width="6"/>
        <path d="M ${-W / 2} -150 Q 0 -168 ${W / 2} -150 L ${W / 2 + 6} -96 Q ${W * 0.2} -84 0 -90 Q ${-W * 0.25} -96 ${-W / 2 - 6} -88 Z" fill="${B}" stroke="${INK}" stroke-width="5"/>
        <path d="M ${-W * 0.3} -146 q 30 18 60 4 M ${W * 0.1} -150 q 30 20 70 6" stroke="${gl(B, 0.3)}" stroke-width="5" fill="none"/>
        <rect x="${-W / 2 - 8}" y="-72" width="${W + 16}" height="44" rx="10" fill="${K}" stroke="${INK}" stroke-width="6"/>
        <rect x="${-W / 2 + 4}" y="-30" width="26" height="30" fill="${gl(K, 0.25)}" stroke="${INK}" stroke-width="5"/><rect x="${W / 2 - 30}" y="-30" width="26" height="30" fill="${gl(K, 0.25)}" stroke="${INK}" stroke-width="5"/>`;
    } else if (j === "kursi") { // kursi kayu; dudukan y -125. {warna, sandaran:false}
      const K = o.warna || "#9c6a42", gl = (f) => warna(K, "#000000", f);
      g = `<ellipse cx="0" cy="6" rx="110" ry="14" fill="#000" opacity=".2"/>` + (o.sandaran === false ? "" : `<rect x="-86" y="-360" width="22" height="240" rx="6" fill="${gl(0.15)}" stroke="${INK}" stroke-width="5"/><rect x="64" y="-360" width="22" height="240" rx="6" fill="${gl(0.15)}" stroke="${INK}" stroke-width="5"/><rect x="-92" y="-372" width="184" height="58" rx="12" fill="${K}" stroke="${INK}" stroke-width="5"/><rect x="-70" y="-300" width="140" height="18" rx="6" fill="${K}" stroke="${INK}" stroke-width="4"/>`) +
        `<rect x="-80" y="-108" width="18" height="108" fill="${gl(0.25)}" stroke="${INK}" stroke-width="5"/><rect x="62" y="-108" width="18" height="108" fill="${gl(0.25)}" stroke="${INK}" stroke-width="5"/><path d="M -100 -132 L 100 -132 L 92 -104 L -92 -104 Z" fill="${K}" stroke="${INK}" stroke-width="5"/><line x1="-80" y1="-126" x2="80" y2="-126" stroke="#fff" stroke-width="4" opacity=".25"/>`;
    } else if (j === "sofa") { // sofa; dudukan y -125. {w, warna, bantal}
      const W = o.w || 620, K = o.warna || "#c96a4a", gl = (f) => warna(K, "#000000", f), tr = (f) => warna(K, "#ffffff", f);
      g = `<ellipse cx="0" cy="8" rx="${W * 0.55}" ry="18" fill="#000" opacity=".22"/><rect x="${-W / 2 + 40}" y="-330" width="${W - 80}" height="200" rx="40" fill="${gl(0.08)}" stroke="${INK}" stroke-width="6"/>
        <line x1="0" y1="-320" x2="0" y2="-140" stroke="${gl(0.25)}" stroke-width="5"/>
        <rect x="${-W / 2 + 40}" y="-150" width="${W - 80}" height="40" rx="14" fill="${tr(0.12)}" stroke="${INK}" stroke-width="5"/><line x1="0" y1="-148" x2="0" y2="-112" stroke="${gl(0.25)}" stroke-width="4"/>
        <rect x="${-W / 2 + 30}" y="-114" width="${W - 60}" height="80" rx="12" fill="${K}" stroke="${INK}" stroke-width="6"/>
        <rect x="${-W / 2}" y="-230" width="70" height="196" rx="30" fill="${K}" stroke="${INK}" stroke-width="6"/><rect x="${W / 2 - 70}" y="-230" width="70" height="196" rx="30" fill="${K}" stroke="${INK}" stroke-width="6"/>
        <rect x="${-W / 2 + 40}" y="-36" width="22" height="34" fill="#4a3020"/><rect x="${W / 2 - 62}" y="-36" width="22" height="34" fill="#4a3020"/>` +
        (o.bantal !== false ? `<rect x="${-W / 2 + 70}" y="-250" width="110" height="100" rx="26" fill="${o.bantal || "#f2c14e"}" stroke="${INK}" stroke-width="5" transform="rotate(-10 ${-W / 2 + 125} -200)"/>` : "");
    } else if (j === "lemari") { // lemari pakaian dua pintu; {w, warna, buka 0-1}
      const W = o.w || 320, K = o.warna || "#a8764a", gl = (f) => warna(K, "#000000", f), bk = clamp(v(o.buka, t, d, 0));
      g = `<ellipse cx="0" cy="6" rx="${W * 0.56}" ry="14" fill="#000" opacity=".2"/><rect x="${-W / 2}" y="-660" width="${W}" height="650" rx="10" fill="${K}" stroke="${INK}" stroke-width="6"/><rect x="${-W / 2 - 10}" y="-680" width="${W + 20}" height="28" rx="6" fill="${gl(0.15)}" stroke="${INK}" stroke-width="5"/>
        <rect x="${-W / 2 + 18}" y="-636" width="${W / 2 - 24}" height="560" rx="6" fill="${gl(0.06)}" stroke="${gl(0.35)}" stroke-width="4"/>
        <g transform="translate(${6} 0) scale(${1 - bk * 0.85} 1)"><rect x="0" y="-636" width="${W / 2 - 24}" height="560" rx="6" fill="${gl(0.06)}" stroke="${gl(0.35)}" stroke-width="4"/></g>
        ${bk > 0.1 ? `<rect x="${6 + (W / 2 - 24) * (1 - bk * 0.85)}" y="-636" width="${(W / 2 - 24) * bk * 0.85}" height="560" fill="#3a2a22"/>` + [0, 1, 2].map((i) => `<rect x="${14 + i * 36}" y="-600" width="30" height="${200 + i * 30}" rx="8" fill="${["#d9534f", "#6aa6a0", "#f2c14e"][i]}" opacity="${bk}"/>`).join("") : ""}
        <circle cx="-14" cy="-360" r="8" fill="#f2d28a" stroke="${INK}" stroke-width="3"/><circle cx="20" cy="-360" r="8" fill="#f2d28a" stroke="${INK}" stroke-width="3"/>
        <rect x="${-W / 2 + 10}" y="-60" width="${W - 20}" height="44" rx="6" fill="${gl(0.12)}" stroke="${gl(0.35)}" stroke-width="4"/><line x1="-30" y1="-38" x2="30" y2="-38" stroke="#f2d28a" stroke-width="6" stroke-linecap="round"/>`;
    } else if (j === "rak_buku") { // rak buku 4 susun berisi buku warna-warni; {w, warna, seed}
      const W = o.w || 280, K = o.warna || "#8a5a36", R = rng(o.seed || 4), WB = ["#d9534f", "#5a7a9a", "#f2c14e", "#6aa6a0", "#e9e4d8", "#7b2a20", "#9a7ac9", "#3f8a4a"];
      g = `<ellipse cx="0" cy="6" rx="${W * 0.56}" ry="12" fill="#000" opacity=".2"/><rect x="${-W / 2}" y="-600" width="${W}" height="600" rx="6" fill="${warna(K, "#000000", 0.35)}" stroke="${INK}" stroke-width="6"/>`;
      for (let r = 0; r < 4; r++) { const y0 = -590 + r * 148; let xx = -W / 2 + 16; while (xx < W / 2 - 34) { const bw = 16 + R() * 18, bh = 90 + R() * 40; if (R() > 0.9) { xx += 20; continue; } g += `<rect x="${xx}" y="${y0 + 136 - bh}" width="${bw}" height="${bh}" rx="3" fill="${WB[Math.floor(R() * WB.length)]}" stroke="${INK}" stroke-width="3"/>`; xx += bw + 2; }
        g += `<rect x="${-W / 2}" y="${y0 + 136}" width="${W}" height="14" fill="${K}" stroke="${INK}" stroke-width="4"/>`; }
      g += `<rect x="${-W / 2}" y="-600" width="16" height="600" fill="${K}" stroke="${INK}" stroke-width="4"/><rect x="${W / 2 - 16}" y="-600" width="16" height="600" fill="${K}" stroke="${INK}" stroke-width="4"/><rect x="${-W / 2 - 6}" y="-612" width="${W + 12}" height="20" rx="4" fill="${K}" stroke="${INK}" stroke-width="4"/>`;
    } else if (j === "tv") { // meja TV + televisi; {nyala 0-1, warna_layar}
      const ny = clamp(v(o.nyala, t, d, 1)), L = o.warna_layar || "#7fc4ff";
      g = `<ellipse cx="0" cy="6" rx="260" ry="14" fill="#000" opacity=".2"/><rect x="-230" y="-150" width="460" height="140" rx="10" fill="#7a5236" stroke="${INK}" stroke-width="6"/><line x1="0" y1="-146" x2="0" y2="-14" stroke="#4a3020" stroke-width="4"/><circle cx="-20" cy="-80" r="6" fill="#f2d28a"/><circle cx="20" cy="-80" r="6" fill="#f2d28a"/>
        <rect x="-30" y="-180" width="60" height="32" fill="#2a2430" stroke="${INK}" stroke-width="4"/><rect x="-210" y="-440" width="420" height="260" rx="12" fill="#15121a" stroke="${INK}" stroke-width="6"/>
        <rect x="-194" y="-424" width="388" height="228" rx="6" fill="${warna("#20263a", L, ny * (0.7 + 0.3 * Math.abs(Math.sin(t * 2.3))))}"/>${ny > 0.2 ? `<path d="M -194 -280 L -90 -330 L 20 -290 L 120 -350 L 194 -310 L 194 -196 L -194 -196 Z" fill="#fff" opacity="${0.18 * ny}"/>` : ""}`;
    } else if (j === "kipas") { // kipas angin berdiri, baling-baling berputar; {putar 0-1}
      const pt = v(o.putar, t, d, 1), a = (t * 900 * pt) % 360;
      g = `<ellipse cx="0" cy="-8" rx="90" ry="20" fill="#e9eef6" stroke="${INK}" stroke-width="5"/><rect x="-10" y="-330" width="20" height="320" fill="#d8dde6" stroke="${INK}" stroke-width="4"/><circle cx="0" cy="-400" r="110" fill="#eef4fb" opacity=".55" stroke="${INK}" stroke-width="5"/>
        <g transform="translate(0 -400) rotate(${a})">${[0, 120, 240].map((r) => `<path d="M 0 0 Q 40 -50 0 -96 Q -36 -50 0 0 Z" fill="#7fc4ff" stroke="${INK}" stroke-width="3" transform="rotate(${r})" opacity=".85"/>`).join("")}</g><circle cx="0" cy="-400" r="16" fill="#5a7a9a" stroke="${INK}" stroke-width="4"/>` +
        [...Array(6)].map((_, i) => `<line x1="${-104 + i * 41.6}" y1="-${400 - Math.sqrt(Math.max(0, 110 * 110 - Math.pow(-104 + i * 41.6, 2)))}" x2="${-104 + i * 41.6}" y2="-${400 + Math.sqrt(Math.max(0, 110 * 110 - Math.pow(-104 + i * 41.6, 2)))}" stroke="${INK}" stroke-width="2" opacity=".35"/>`).join("");
    } else if (j === "kulkas") { // kulkas dua pintu + magnet
      g = `<ellipse cx="0" cy="6" rx="140" ry="14" fill="#000" opacity=".2"/><rect x="-120" y="-560" width="240" height="550" rx="20" fill="#e6ecf2" stroke="${INK}" stroke-width="6"/><line x1="-120" y1="-380" x2="120" y2="-380" stroke="${INK}" stroke-width="5"/>
        <rect x="84" y="-520" width="12" height="100" rx="6" fill="#aab4c0"/><rect x="84" y="-350" width="12" height="160" rx="6" fill="#aab4c0"/><rect x="88" y="-550" width="22" height="540" fill="#000" opacity=".06"/>
        <rect x="-80" y="-330" width="60" height="70" fill="#fff" stroke="${INK}" stroke-width="3" transform="rotate(-6 -50 -295)"/><circle cx="20" cy="-300" r="12" fill="#d9534f"/><rect x="-60" y="-220" width="50" height="40" fill="#f2c14e" stroke="${INK}" stroke-width="3"/>`;
    } else if (j === "kompor") { // meja dapur + kompor gas; {nyala 0-1}
      const ny = clamp(v(o.nyala, t, d, 0));
      g = `<rect x="-200" y="-260" width="400" height="250" rx="8" fill="#c9b49a" stroke="${INK}" stroke-width="6"/><rect x="-190" y="-200" width="180" height="170" rx="6" fill="#b49c80" stroke="${INK}" stroke-width="4"/><rect x="10" y="-200" width="180" height="170" rx="6" fill="#b49c80" stroke="${INK}" stroke-width="4"/>
        <rect x="-150" y="-310" width="300" height="50" rx="10" fill="#2a2430" stroke="${INK}" stroke-width="5"/>${[-70, 70].map((cx) => `<ellipse cx="${cx}" cy="-312" rx="44" ry="10" fill="#4a4450" stroke="${INK}" stroke-width="3"/>` + (ny > 0 ? [...Array(7)].map((_, i) => `<path d="M ${cx - 36 + i * 12} -314 q 4 ${-14 - 10 * Math.abs(Math.sin(t * 9 + i))} 8 0 Z" fill="#5ab4ff" opacity="${ny}"/>`).join("") : "")).join("")}
        <circle cx="-100" cy="-285" r="8" fill="#ddd"/><circle cx="100" cy="-285" r="8" fill="#ddd"/>`;
    } else if (j === "motor") { // motor matic tampak samping; {warna, arah -1}. Titik kait: KAIT.motor (jok, setang, dek kaki)
      const K = o.warna || "#d9534f", ar = o.arah === -1 ? -1 : 1;
      g = `<g transform="scale(${ar} 1)"><ellipse cx="0" cy="6" rx="230" ry="16" fill="#000" opacity=".22"/>${[-150, 150].map((cx) => `<circle cx="${cx}" cy="-62" r="62" fill="#2a2430" stroke="${INK}" stroke-width="6"/><circle cx="${cx}" cy="-62" r="30" fill="#aab4c0" stroke="${INK}" stroke-width="4"/>`).join("")}
        <path d="M -200 -110 Q -210 -190 -120 -200 L 40 -200 Q 70 -150 110 -140 L 150 -140 L 190 -300 L 214 -296 L 180 -120 Q 120 -90 60 -100 L -100 -100 Q -170 -90 -200 -110 Z" fill="${K}" stroke="${INK}" stroke-width="6"/>
        <path d="M -150 -200 Q -150 -244 -80 -244 L 30 -244 Q 50 -230 40 -200 Z" fill="#2a2430" stroke="${INK}" stroke-width="5"/><path d="M 150 -62 L 184 -300" stroke="#3a3540" stroke-width="16" stroke-linecap="round"/><path d="M 150 -62 L 184 -300" stroke="#8a93a0" stroke-width="6" stroke-linecap="round"/>
        <path d="M 172 -312 L 158 -392" stroke="${INK}" stroke-width="6" stroke-linecap="round"/><ellipse cx="156" cy="-400" rx="20" ry="13" fill="#aab4c0" stroke="${INK}" stroke-width="5"/>
        <path d="M 196 -300 Q 190 -330 160 -334 L 126 -338" fill="none" stroke="#2a2430" stroke-width="16" stroke-linecap="round"/><rect x="104" y="-348" width="40" height="22" rx="10" fill="#1d1a22" stroke="${INK}" stroke-width="4"/>
        <path d="M 176 -318 Q 200 -326 214 -302 L 204 -292 Q 192 -308 172 -306 Z" fill="${K}" stroke="${INK}" stroke-width="5"/><ellipse cx="210" cy="-250" rx="18" ry="24" fill="#fff6c8" stroke="${INK}" stroke-width="4"/><path d="M -160 -150 L 60 -150" stroke="#fff" stroke-width="5" opacity=".35"/></g>`;
    } else if (j === "pot") { // tanaman pot; {jenis: monstera|palem|bunga, warna_pot}
      const jp = o.tanaman || "monstera", P2 = o.warna_pot || "#c96a4a", ay = Math.sin(t * 1.4 + x) * 2;
      g = `<ellipse cx="0" cy="6" rx="80" ry="12" fill="#000" opacity=".2"/>`;
      if (jp === "bunga") g += [...Array(7)].map((_, i) => { const a = -60 + i * 20, L = 120 + (i % 3) * 30; const ex = Math.sin(a * Math.PI / 180) * L, ey = -110 - Math.cos(a * Math.PI / 180) * L; return `<line x1="0" y1="-110" x2="${ex}" y2="${ey}" stroke="#3f8a4a" stroke-width="6"/><circle cx="${ex}" cy="${ey}" r="18" fill="${["#ff7a8a", "#f2c14e", "#fff"][i % 3]}" stroke="${INK}" stroke-width="3"/><circle cx="${ex}" cy="${ey}" r="6" fill="#d9534f"/>`; }).join("");
      else if (jp === "palem") g += [...Array(9)].map((_, i) => { const a = -80 + i * 20; return `<path d="M 0 -110 Q ${Math.sin(a * Math.PI / 180) * 120} ${-180 - Math.cos(a * Math.PI / 180) * 160} ${Math.sin(a * Math.PI / 180) * 220 + ay} ${-110 - Math.cos(a * Math.PI / 180) * 230}" stroke="#3f8a4a" stroke-width="12" fill="none" stroke-linecap="round"/>`; }).join("");
      else g += [...Array(6)].map((_, i) => { const a = -75 + i * 30, L = 130 + (i % 2) * 40, ex = Math.sin(a * Math.PI / 180) * L, ey = -100 - Math.cos(a * Math.PI / 180) * L * 1.1; return `<line x1="0" y1="-100" x2="${ex}" y2="${ey}" stroke="#2f6a3a" stroke-width="6"/><ellipse cx="${ex}" cy="${ey}" rx="54" ry="38" fill="${i % 2 ? "#3f8a4a" : "#4f9a56"}" stroke="${INK}" stroke-width="4" transform="rotate(${a + ay} ${ex} ${ey})"/><line x1="${ex - 30}" y1="${ey}" x2="${ex + 30}" y2="${ey}" stroke="#2f6a3a" stroke-width="3" transform="rotate(${a + ay} ${ex} ${ey})"/>`; }).join("");
      g += `<path d="M -70 -110 L 70 -110 L 54 0 L -54 0 Z" fill="${P2}" stroke="${INK}" stroke-width="6"/><rect x="-78" y="-124" width="156" height="22" rx="6" fill="${warna(P2, "#000000", 0.15)}" stroke="${INK}" stroke-width="5"/>`;
    } else if (j === "meja_belajar") { // meja + lampu + buku + laptop; {lampu 0-1, laptop}
      const lp = clamp(v(o.lampu, t, d, 1)), K = o.warna || "#a8764a";
      g = `<ellipse cx="0" cy="6" rx="250" ry="14" fill="#000" opacity=".2"/><rect x="-230" y="-250" width="460" height="28" rx="6" fill="${K}" stroke="${INK}" stroke-width="6"/><rect x="-216" y="-222" width="24" height="222" fill="${warna(K, "#000000", 0.25)}" stroke="${INK}" stroke-width="5"/><rect x="120" y="-222" width="96" height="140" fill="${warna(K, "#000000", 0.12)}" stroke="${INK}" stroke-width="5"/><rect x="192" y="-82" width="24" height="82" fill="${warna(K, "#000000", 0.25)}" stroke="${INK}" stroke-width="5"/><circle cx="168" cy="-152" r="6" fill="#f2d28a"/>
        <circle cx="-150" cy="-380" r="${150}" fill="#fff1c2" opacity="${0.35 * lp}"/><path d="M -170 -250 L -130 -250 L -146 -330 L -100 -380" stroke="#2f6a3a" stroke-width="10" fill="none" stroke-linecap="round"/><path d="M -150 -410 L -60 -400 L -80 -350 L -140 -360 Z" fill="#3f8a4a" stroke="${INK}" stroke-width="5"/><ellipse cx="-110" cy="-352" rx="26" ry="8" fill="#fff6c8" opacity="${lp}"/>
        ${[0, 1, 2].map((i) => `<rect x="${-40 + i * 4}" y="${-276 - i * 18}" width="110" height="18" rx="3" fill="${["#d9534f", "#5a7a9a", "#f2c14e"][i]}" stroke="${INK}" stroke-width="3"/>`).join("")}` + (o.laptop !== false ? `<path d="M 80 -252 L 210 -252 L 220 -244 L 70 -244 Z" fill="#aab4c0" stroke="${INK}" stroke-width="4"/><path d="M 90 -252 L 100 -340 L 200 -340 L 190 -252 Z" fill="#2a2430" stroke="${INK}" stroke-width="4"/><path d="M 100 -258 L 108 -332 L 194 -332 L 186 -258 Z" fill="#7fc4ff" opacity="${0.5 + 0.3 * Math.sin(t * 2)}"/>` : "");
    } else if (j === "rumah_kampung") { // rumah kampung: dinding, atap genteng, pintu, jendela, teras; {w, dinding, atap, pintu, lampu 0-1, buka 0-1}
      const W = o.w || 720, D = o.dinding || "#f2e2c4", A = o.atap || "#b5523a", PT = o.pintu || "#7a4a2e", lp = clamp(v(o.lampu, t, d, 0)), gl = (c, f) => warna(c, "#000000", f);
      const H = 440, jdl = (x0) => `<rect x="${x0}" y="-330" width="130" height="150" fill="${lp > 0.3 ? "#ffe9a8" : "#a8d4ee"}" stroke="${INK}" stroke-width="6"/><line x1="${x0 + 65}" y1="-330" x2="${x0 + 65}" y2="-180" stroke="#f6efe2" stroke-width="8"/><line x1="${x0}" y1="-255" x2="${x0 + 130}" y2="-255" stroke="#f6efe2" stroke-width="8"/><rect x="${x0 - 14}" y="-184" width="158" height="16" fill="${gl(D, 0.12)}" stroke="${INK}" stroke-width="4"/>`;
      g = `<ellipse cx="0" cy="8" rx="${W * 0.56}" ry="20" fill="#000" opacity=".2"/><rect x="${-W / 2}" y="${-H}" width="${W}" height="${H}" fill="${D}" stroke="${INK}" stroke-width="7"/><rect x="${-W / 2}" y="-60" width="${W}" height="60" fill="${gl(D, 0.18)}" stroke="${INK}" stroke-width="5"/>
        <rect x="${W / 2 - 120}" y="${-H}" width="120" height="${H}" fill="#000" opacity=".06"/>`;
      g += jdl(-W / 2 + 60) + jdl(W / 2 - 200);
      const bk = clamp(v(o.buka, t, d, 0));
      g += `<rect x="-75" y="-300" width="150" height="300" fill="#2a1e18" stroke="${INK}" stroke-width="6"/><rect x="-75" y="-300" width="${150 * (1 - bk * 0.8)}" height="300" fill="${PT}" stroke="${INK}" stroke-width="6"/><circle cx="${-75 + 150 * (1 - bk * 0.8) - 20}" cy="-150" r="8" fill="#f2d28a"/>`;
      g += `<path d="M ${-W / 2 - 70} ${-H} L ${W / 2 + 70} ${-H} L ${W / 2 - 40} ${-H - 230} L ${-W / 2 + 40} ${-H - 230} Z" fill="${A}" stroke="${INK}" stroke-width="7"/>`;
      for (let r = 1; r < 5; r++) { const y = -H - r * 46, k = r * 46 / 230; g += `<line x1="${-W / 2 - 70 + k * 110}" y1="${y}" x2="${W / 2 + 70 - k * 110}" y2="${y}" stroke="${gl(A, 0.3)}" stroke-width="4"/>`; }
      for (let i = -8; i <= 8; i++) g += `<line x1="${i * (W + 140) / 17}" y1="${-H}" x2="${i * (W - 80) / 17}" y2="${-H - 230}" stroke="${gl(A, 0.22)}" stroke-width="3"/>`;
      g += `<rect x="${-W / 2 - 70}" y="${-H - 8}" width="${W + 140}" height="16" fill="${gl(A, 0.35)}" stroke="${INK}" stroke-width="4"/>`;
      if (lp > 0) g += `<circle cx="0" cy="-330" r="160" fill="#ffe9a8" opacity="${0.3 * lp}"/><circle cx="0" cy="-330" r="12" fill="#fff6c8" opacity="${lp}"/>`;
    } else if (j === "warung") { // warung kelontong: etalase, kanopi garis, toples, papan nama {nama}
      const W = o.w || 640, KN = o.kanopi || "#d9534f";
      g = `<ellipse cx="0" cy="8" rx="${W * 0.56}" ry="18" fill="#000" opacity=".2"/><rect x="${-W / 2}" y="-460" width="${W}" height="460" fill="#e9d6b0" stroke="${INK}" stroke-width="7"/>
        <rect x="${-W / 2 + 30}" y="-360" width="${W - 60}" height="200" fill="#5a4030" stroke="${INK}" stroke-width="5"/>`;
      for (let r = 0; r < 2; r++) for (let i = 0; i < 8; i++) g += `<rect x="${-W / 2 + 46 + i * (W - 92) / 8}" y="${-344 + r * 92}" width="${(W - 92) / 8 - 10}" height="72" rx="6" fill="${["#f2c14e", "#d9534f", "#6aa6a0", "#e9e4d8", "#9a7ac9", "#3f8a4a"][(i + r * 3) % 6]}" stroke="${INK}" stroke-width="3"/>`;
      g += `<rect x="${-W / 2 + 20}" y="-150" width="${W - 40}" height="150" fill="#c9a87a" stroke="${INK}" stroke-width="6"/>` + [0, 1, 2, 3].map((i) => `<rect x="${-W / 2 + 50 + i * 130}" y="-210" width="70" height="66" rx="16" fill="#dff3ff" stroke="${INK}" stroke-width="4" opacity=".9"/><rect x="${-W / 2 + 56 + i * 130}" y="-180" width="58" height="30" rx="6" fill="${["#f2c14e", "#d9534f", "#7a4a2e", "#3f8a4a"][i]}"/>`).join("");
      for (let i = 0; i < 8; i++) g += `<path d="M ${-W / 2 - 40 + i * (W + 80) / 8} -460 L ${-W / 2 - 40 + (i + 1) * (W + 80) / 8} -460 L ${-W / 2 - 40 + (i + 1) * (W + 80) / 8} -400 Q ${-W / 2 - 40 + (i + 0.5) * (W + 80) / 8} -380 ${-W / 2 - 40 + i * (W + 80) / 8} -400 Z" fill="${i % 2 ? "#fff" : KN}" stroke="${INK}" stroke-width="4"/>`;
      g += `<rect x="${-W / 2 + 40}" y="-560" width="${W - 80}" height="90" rx="10" fill="#2f6a8a" stroke="${INK}" stroke-width="6"/><text x="0" y="-500" font-family="DejaVu Sans, sans-serif" font-weight="800" font-size="48" text-anchor="middle" fill="#fff">${esc(o.nama || "WARUNG")}</text>`;
    } else if (j === "masjid_kampung") { // masjid kampung berwarna: kubah hijau, menara, pagar
      const KB = o.kubah || "#3f8a5a", D = o.dinding || "#f6f0e2";
      g = `<ellipse cx="0" cy="8" rx="460" ry="20" fill="#000" opacity=".2"/><rect x="-360" y="-380" width="720" height="380" fill="${D}" stroke="${INK}" stroke-width="7"/>` +
        [-240, -80, 80, 240].map((x0) => `<path d="M ${x0 - 50} 0 L ${x0 - 50} -200 Q ${x0} -270 ${x0 + 50} -200 L ${x0 + 50} 0 Z" fill="#7aa88a" stroke="${INK}" stroke-width="5"/><path d="M ${x0 - 36} -12 L ${x0 - 36} -196 Q ${x0} -250 ${x0 + 36} -196 L ${x0 + 36} -12" fill="none" stroke="#fff" stroke-width="3" opacity=".4"/>`).join("") +
        `<rect x="-380" y="-400" width="760" height="30" fill="#e2d6b8" stroke="${INK}" stroke-width="5"/><rect x="-140" y="-470" width="280" height="80" fill="${D}" stroke="${INK}" stroke-width="6"/>
        <path d="M -200 -460 Q -200 -720 0 -760 Q 200 -720 200 -460 Z" fill="${KB}" stroke="${INK}" stroke-width="7"/><path d="M -120 -500 Q -110 -680 0 -720" stroke="#fff" stroke-width="10" fill="none" opacity=".3"/><line x1="0" y1="-760" x2="0" y2="-830" stroke="#d9b25a" stroke-width="8"/><path d="M 0 -870 a 22 22 0 1 0 16 36 a 16 16 0 1 1 -16 -36 Z" fill="#f2c14e"/>
        <rect x="420" y="-900" width="80" height="900" fill="${D}" stroke="${INK}" stroke-width="6"/><rect x="404" y="-640" width="112" height="24" fill="#e2d6b8" stroke="${INK}" stroke-width="4"/><path d="M 410 -900 Q 410 -980 460 -1010 Q 510 -980 510 -900 Z" fill="${KB}" stroke="${INK}" stroke-width="6"/><line x1="460" y1="-1010" x2="460" y2="-1060" stroke="#d9b25a" stroke-width="6"/>`;
    } else if (j === "sekolah") { // gedung sekolah dua lantai + tiang bendera + papan nama
      const D = o.dinding || "#f6efe2", A = o.atap || "#b5523a";
      g = `<ellipse cx="0" cy="8" rx="560" ry="20" fill="#000" opacity=".2"/><rect x="-500" y="-560" width="1000" height="560" fill="${D}" stroke="${INK}" stroke-width="7"/><rect x="-500" y="-300" width="1000" height="20" fill="#c9d6bf" stroke="${INK}" stroke-width="4"/>`;
      for (let r = 0; r < 2; r++) for (let i = 0; i < 6; i++) g += `<rect x="${-460 + i * 160}" y="${-520 + r * 270}" width="110" height="${r ? 200 : 170}" fill="${r && i === 2 ? "#7a4a2e" : "#a8d4ee"}" stroke="${INK}" stroke-width="5"/>`;
      g += `<path d="M -560 -560 L 560 -560 L 500 -680 L -500 -680 Z" fill="${A}" stroke="${INK}" stroke-width="7"/><rect x="-180" y="-650" width="360" height="70" fill="#2f6a3a" stroke="${INK}" stroke-width="5"/><text x="0" y="-602" font-family="DejaVu Sans, sans-serif" font-weight="800" font-size="40" text-anchor="middle" fill="#fff">${esc(o.nama || "SEKOLAH")}</text>
        <line x1="640" y1="0" x2="640" y2="-760" stroke="#aab4c0" stroke-width="12"/><path d="M 646 -756 L ${760 + Math.sin(t * 4) * 10} -740 L ${756 + Math.sin(t * 4 + 1) * 10} -700 L 646 -700 Z" fill="#d9534f"/><path d="M 646 -700 L ${756 + Math.sin(t * 4 + 1) * 10} -700 L ${752 + Math.sin(t * 4 + 2) * 10} -660 L 646 -660 Z" fill="#fff" stroke="#ddd" stroke-width="2"/>`;
    } else if (j === "toko") { // ruko/toko kota: rolling door, papan nama {nama, warna}
      const K = o.warna || "#5a7a9a";
      g = `<ellipse cx="0" cy="8" rx="380" ry="18" fill="#000" opacity=".2"/><rect x="-340" y="-760" width="680" height="760" fill="#e6e0d6" stroke="${INK}" stroke-width="7"/><rect x="-340" y="-420" width="680" height="90" fill="${K}" stroke="${INK}" stroke-width="6"/><text x="0" y="-360" font-family="DejaVu Sans, sans-serif" font-weight="800" font-size="50" text-anchor="middle" fill="#fff">${esc(o.nama || "TOKO")}</text>
        <rect x="-300" y="-320" width="600" height="320" fill="#b8c2cc" stroke="${INK}" stroke-width="6"/>` + [...Array(10)].map((_, i) => `<line x1="-300" y1="${-300 + i * 30}" x2="300" y2="${-300 + i * 30}" stroke="#8a96a2" stroke-width="4"/>`).join("") +
        [-200, 0, 200].map((x0) => `<rect x="${x0 - 70}" y="-700" width="140" height="200" fill="#a8d4ee" stroke="${INK}" stroke-width="5"/><rect x="${x0 - 84}" y="-506" width="168" height="16" fill="#cfc8bc" stroke="${INK}" stroke-width="3"/>`).join("");
    } else if (j === "pagar") { // pagar besi/kayu sepanjang w; {w, warna, model: kayu|tembok}
      const W = o.w || 900, K = o.warna || (o.model === "tembok" ? "#e9dcc0" : "#f6efe2");
      if (o.model === "tembok") g = `<rect x="${-W / 2}" y="-160" width="${W}" height="160" fill="${K}" stroke="${INK}" stroke-width="6"/><rect x="${-W / 2 - 6}" y="-176" width="${W + 12}" height="20" fill="${warna(K, "#000000", 0.15)}" stroke="${INK}" stroke-width="5"/>` + [...Array(Math.floor(W / 160))].map((_, i) => `<rect x="${-W / 2 + i * 160 + 70}" y="-150" width="20" height="150" fill="#000" opacity=".06"/>`).join("");
      else { g = `<rect x="${-W / 2}" y="-130" width="${W}" height="18" fill="${K}" stroke="${INK}" stroke-width="4"/><rect x="${-W / 2}" y="-60" width="${W}" height="18" fill="${K}" stroke="${INK}" stroke-width="4"/>`; for (let x = -W / 2; x <= W / 2; x += 48) g += `<path d="M ${x - 14} 0 L ${x - 14} -170 L ${x} -196 L ${x + 14} -170 L ${x + 14} 0 Z" fill="${K}" stroke="${INK}" stroke-width="4"/>`; }
    } else if (j === "tiang_listrik") { // tiang listrik + kabel menjuntai ke kanan/kiri
      const kb = o.kabel !== false;
      g = `<rect x="-14" y="-1000" width="28" height="1000" fill="#8a8a92" stroke="${INK}" stroke-width="5"/><rect x="-90" y="-940" width="180" height="16" fill="#6a6a72" stroke="${INK}" stroke-width="4"/>` + [-80, -30, 30, 80].map((x0) => `<rect x="${x0 - 6}" y="-956" width="12" height="16" fill="#e9e4d8"/>`).join("") +
        `<rect x="-40" y="-860" width="80" height="60" rx="8" fill="#7a7a82" stroke="${INK}" stroke-width="4"/>` + (kb ? [-80, -30, 30, 80].map((x0, i) => `<path d="M ${x0} -948 Q ${x0 + 600} ${-820 + i * 14} ${x0 + 1300} -950 M ${x0} -948 Q ${x0 - 600} ${-830 + i * 12} ${x0 - 1300} -950" stroke="${INK}" stroke-width="3" fill="none"/>`).join("") : "");
    } else if (j === "jalan") { // jalan aspal + garis tengah putus-putus + trotoar; {w, y_lebar}
      const W = o.w || 2400, L2 = o.lebar || 220;
      g = `<rect x="${-W / 2}" y="${-L2}" width="${W}" height="${L2}" fill="#5a5a62"/><rect x="${-W / 2}" y="${-L2 - 30}" width="${W}" height="30" fill="#cfc8bc" stroke="${INK}" stroke-width="4"/>` + [...Array(Math.ceil(W / 160))].map((_, i) => `<rect x="${-W / 2 + i * 160}" y="${-L2 / 2 - 5}" width="90" height="10" fill="#f6efe2"/>`).join("");
    } else if (j === "pisang") { // pohon pisang
      const ay = Math.sin(t * 1.3 + x) * 4;
      g = `<path d="M -22 0 L -16 -380 L 16 -380 L 22 0 Z" fill="#8aa05a" stroke="${INK}" stroke-width="5"/><path d="M -10 -40 L -8 -360 M 8 -60 L 6 -340" stroke="#6a8040" stroke-width="4"/>` +
        [[-60, 1], [-25, 1], [10, 1], [45, 1], [80, -1], [-95, -1]].map(([a, f], i) => { const A = (a + ay) * Math.PI / 180, ex = Math.sin(A) * 300, ey = -380 - Math.cos(A) * 300; return `<path d="M 0 -380 Q ${ex * 0.5 - 60 * Math.cos(A)} ${(ey - 380) / 2 - 40} ${ex} ${ey} Q ${ex * 0.5 + 40 * Math.cos(A)} ${(ey - 380) / 2 + 30} 0 -380 Z" fill="${i % 2 ? "#4f9a46" : "#5fb04f"}" stroke="${INK}" stroke-width="4"/><path d="M 0 -380 L ${ex} ${ey}" stroke="#3a7a36" stroke-width="3"/>`; }).join("") +
        (o.buah ? `<ellipse cx="34" cy="-300" rx="26" ry="40" fill="#c9b030" stroke="${INK}" stroke-width="4"/>` : "");
    } else if (j === "kelapa") { // pohon kelapa melengkung
      const ay = Math.sin(t * 1.1 + x) * 5, lg = o.lengkung || 1;
      g = `<path d="M -26 0 Q ${60 * lg} -400 ${120 * lg} -760 L ${150 * lg} -756 Q ${90 * lg} -400 26 0 Z" fill="#a07a50" stroke="${INK}" stroke-width="5"/>`;
      for (let i = 1; i < 14; i++) { const yy = -i * 54, xx = (yy / -760) * 130 * lg * (yy / -760); g += `<line x1="${xx - 22}" y1="${yy}" x2="${xx + 26}" y2="${yy + 4}" stroke="${INK}" stroke-width="3" opacity=".45"/>`; }
      const cx = 135 * lg, cy = -770;
      g += [-150, -110, -60, -20, 20, 60, 110, 150].map((a, i) => { const A = (a + ay) * Math.PI / 180, ex = cx + Math.sin(A) * 340, ey = cy - Math.cos(A) * 220 + 120; return `<path d="M ${cx} ${cy} Q ${(cx + ex) / 2} ${cy - 120 + Math.abs(a) * 0.4} ${ex} ${ey}" stroke="${i % 2 ? "#3f8a3f" : "#4f9a46"}" stroke-width="30" fill="none" stroke-linecap="round"/><path d="M ${cx} ${cy} Q ${(cx + ex) / 2} ${cy - 120 + Math.abs(a) * 0.4} ${ex} ${ey}" stroke="#2f6a2f" stroke-width="4" fill="none"/>`; }).join("") +
        [-20, 14, 0].map((dx, i) => `<circle cx="${cx + dx}" cy="${cy + 16 + (i === 2 ? 22 : 0)}" r="22" fill="#6a8a3a" stroke="${INK}" stroke-width="4"/>`).join("");
    } else if (j === "mangga") { // pohon rindang (mangga/beringin kecil), opsional buah
      const ay = Math.sin(t * 1.2 + x) * 3, W2 = o.lebar || 1;
      g = `<ellipse cx="0" cy="6" rx="${220 * W2}" ry="22" fill="#000" opacity=".18"/><path d="M -36 0 Q -20 -200 -50 -330 M 36 0 Q 20 -200 60 -330 M 0 -150 L 0 -340" stroke="#7a5236" stroke-width="40" fill="none" stroke-linecap="round"/>` +
        [[-170, -420, 150], [0, -520, 190], [170, -420, 150], [-90, -620, 140], [90, -620, 140], [0, -380, 170]].map(([cx, cy, r], i) => `<circle cx="${cx * W2 + ay}" cy="${cy}" r="${r * W2}" fill="${["#3f8a3f", "#4f9a46", "#3a7a36"][i % 3]}" stroke="${INK}" stroke-width="6"/>`).join("") +
        [[-120, -460], [60, -560], [140, -380], [-40, -620], [20, -420]].map(([cx, cy]) => `<circle cx="${cx * W2 + ay}" cy="${cy}" r="42" fill="#5fb04f" opacity=".6"/>`).join("") +
        (o.buah ? [[-100, -400], [80, -470], [150, -330], [-30, -560]].map(([cx, cy]) => `<ellipse cx="${cx * W2 + ay}" cy="${cy}" rx="16" ry="22" fill="#f2b544" stroke="${INK}" stroke-width="3"/>`).join("") : "");
    } else if (j === "bambu") { // rumpun bambu
      const R2 = rng(o.seed || 8); g = "";
      for (let i = 0; i < 7; i++) { const bx = -120 + i * 40 + R2() * 20, h = 700 + R2() * 300, ay = Math.sin(t * 1.4 + i) * 8, cl = i % 2 ? "#8ab04a" : "#7aa040";
        g += `<path d="M ${bx} 0 Q ${bx + ay} ${-h / 2} ${bx + ay * 2 + (i - 3) * 20} ${-h}" stroke="${cl}" stroke-width="22" fill="none"/>`;
        for (let k = 1; k < 8; k++) { const yy = -k * h / 8; g += `<line x1="${bx - 12 + ay * k / 8}" y1="${yy}" x2="${bx + 12 + ay * k / 8}" y2="${yy}" stroke="#4a6a2a" stroke-width="4"/>`; }
        for (let k = 0; k < 5; k++) { const yy = -h + k * 60, lx = bx + ay * 2 + (i - 3) * 20 * (1 - k * 0.1); g += `<path d="M ${lx} ${yy} q ${(k % 2 ? 1 : -1) * 70} 10 ${(k % 2 ? 1 : -1) * 110} 40" stroke="#5f9a3a" stroke-width="12" fill="none" stroke-linecap="round"/>`; } }
    } else if (j === "semak") { // semak/perdu, opsional bunga
      const W2 = o.w || 260, R2 = rng(o.seed || 6);
      g = `<ellipse cx="0" cy="4" rx="${W2 * 0.55}" ry="14" fill="#000" opacity=".18"/>` + [...Array(6)].map((_, i) => `<circle cx="${-W2 / 2 + 30 + i * (W2 - 60) / 5}" cy="${-50 - R2() * 40}" r="${50 + R2() * 25}" fill="${["#4f9a46", "#3f8a3f", "#5fb04f"][i % 3]}" stroke="${INK}" stroke-width="5"/>`).join("") +
        (o.bunga ? [...Array(7)].map(() => `<circle cx="${-W2 / 2 + 20 + R2() * (W2 - 40)}" cy="${-30 - R2() * 90}" r="10" fill="${o.bunga === true ? "#ff7a8a" : o.bunga}" stroke="${INK}" stroke-width="2"/>`).join("") : "");
    } else if (j === "rumput") { // rumpun rumput bergoyang; {n, w}
      const R2 = rng(o.seed || 2), n = o.n || 14, W2 = o.w || 300; g = "";
      for (let i = 0; i < n; i++) { const bx = -W2 / 2 + R2() * W2, h = 40 + R2() * 60, ay = Math.sin(t * 2 + i) * 8; g += `<path d="M ${bx - 6} 0 Q ${bx + ay / 2} ${-h / 2} ${bx + ay} ${-h} Q ${bx + 4} ${-h / 2} ${bx + 6} 0 Z" fill="${i % 2 ? "#5fb04f" : "#4f9a46"}"/>`; }
    } else if (j === "sawah") { // hamparan sawah bertingkat dari cakrawala (y=0) ke depan; {w, gubuk, hijau 0-1 (0 = menguning)}
      const W = o.w || 2400, hj = v(o.hijau, t, d, 1), c1 = warna("#d9b84a", "#6abf4a", hj), c2 = warna("#c9a43a", "#4f9a3a", hj), R2 = rng(o.seed || 9);
      g = `<rect x="${-W / 2}" y="0" width="${W}" height="900" fill="${c2}"/>`;
      for (let r = 0; r < 8; r++) { const y0 = Math.pow(r / 8, 1.6) * 900, y1 = Math.pow((r + 1) / 8, 1.6) * 900; g += `<rect x="${-W / 2}" y="${y0}" width="${W}" height="${y1 - y0}" fill="${r % 2 ? c1 : c2}"/><rect x="${-W / 2}" y="${y1 - 6 - r}" width="${W}" height="${6 + r * 1.5}" fill="#8a6a3a" opacity=".7"/>`;
        for (let i = 0; i < 26 + r * 4; i++) { const px = -W / 2 + R2() * W, py = y0 + R2() * (y1 - y0), sz = 3 + r * 2.4, ay = Math.sin(t * 2 + px * 0.01) * sz * 0.6; g += `<path d="M ${px} ${py} q ${ay} ${-sz * 2} ${ay * 1.5} ${-sz * 3.4} M ${px} ${py} q ${-sz + ay} ${-sz * 1.6} ${-sz * 1.6 + ay} ${-sz * 2.6} M ${px} ${py} q ${sz + ay} ${-sz * 1.6} ${sz * 1.6 + ay} ${-sz * 2.6}" stroke="${campur(c1, "#1d3a1d", 0.5)}" stroke-width="${2 + r * 0.9}" fill="none"/>`; } }
      for (let i = 0; i < 6; i++) g += `<rect x="${-W / 2 + R2() * W}" y="${60 + R2() * 600}" width="${60 + R2() * 120}" height="6" rx="3" fill="#cfe9ff" opacity=".35"/>`;
      if (o.gubuk) g += `<g transform="translate(${o.gubuk === true ? 260 : o.gubuk} 140) scale(.6)"><rect x="-90" y="-120" width="180" height="120" fill="#c9a26a" stroke="${INK}" stroke-width="6"/><path d="M -140 -110 L 0 -210 L 140 -110 Z" fill="#9a7a3a" stroke="${INK}" stroke-width="6"/>${[-80, 80].map((px) => `<rect x="${px - 6}" y="-120" width="12" height="160" fill="#7a5236"/>`).join("")}</g>`;
    } else if (j === "lapak") { // lapak pasar: meja + terpal + dagangan; {terpal, isi: buah|sayur|ikan}
      const TP = o.terpal || "#2f8ab0", isi = o.isi || "buah", R2 = rng(o.seed || 3);
      g = `<ellipse cx="0" cy="6" rx="260" ry="16" fill="#000" opacity=".2"/>${[-210, 210].map((px) => `<rect x="${px - 8}" y="-470" width="16" height="470" fill="#7a5236" stroke="${INK}" stroke-width="4"/>`).join("")}
        <path d="M -260 -470 L 260 -470 L 290 -400 L -290 -400 Z" fill="${TP}" stroke="${INK}" stroke-width="6"/>${[...Array(6)].map((_, i) => `<path d="M ${-290 + i * 97} -400 q 48 30 97 0" fill="${TP}" stroke="${INK}" stroke-width="4"/>`).join("")}
        <rect x="-240" y="-180" width="480" height="30" fill="#b07c52" stroke="${INK}" stroke-width="5"/><rect x="-230" y="-150" width="460" height="150" fill="#9c6a42" stroke="${INK}" stroke-width="5"/>`;
      const W2 = isi === "sayur" ? ["#3f8a3f", "#d9534f", "#f2b544", "#5fb04f"] : isi === "ikan" ? ["#9fb4c8", "#c8d6e2", "#aab4c0"] : ["#f2b544", "#d9534f", "#5fb04f", "#e88a2a"];
      for (let k = 0; k < 3; k++) { const cx = -150 + k * 150; g += `<ellipse cx="${cx}" cy="-186" rx="66" ry="16" fill="#c9a26a" stroke="${INK}" stroke-width="4"/>`;
        for (let i = 0; i < 9; i++) { const bx = cx - 44 + (i % 4) * 28 + (Math.floor(i / 4) % 2) * 14, by = -196 - Math.floor(i / 4) * 22, c = W2[(k + i) % W2.length]; g += isi === "ikan" ? `<path d="M ${bx - 18} ${by} q 18 -14 36 0 l 10 -8 l 0 16 l -10 -8 q -18 14 -36 0 Z" fill="${c}" stroke="${INK}" stroke-width="2"/>` : `<circle cx="${bx}" cy="${by}" r="15" fill="${c}" stroke="${INK}" stroke-width="3"/>`; } }
    } else if (j === "rumah_sakit_gedung") { // gedung rumah sakit (tampak luar)
      g = `<ellipse cx="0" cy="8" rx="560" ry="20" fill="#000" opacity=".2"/><rect x="-500" y="-760" width="1000" height="760" fill="#f4f6f6" stroke="${INK}" stroke-width="7"/><rect x="200" y="-760" width="300" height="760" fill="#000" opacity=".05"/>`;
      for (let r = 0; r < 4; r++) for (let i = 0; i < 7; i++) if (!(r === 3 && i > 1 && i < 5)) g += `<rect x="${-460 + i * 134}" y="${-720 + r * 160}" width="96" height="110" fill="#a8d4ee" stroke="${INK}" stroke-width="4"/>`;
      g += `<rect x="-170" y="-200" width="340" height="200" fill="#a8d4ee" stroke="${INK}" stroke-width="6"/><line x1="0" y1="-200" x2="0" y2="0" stroke="${INK}" stroke-width="5"/><path d="M -260 -200 L 260 -200 L 230 -250 L -230 -250 Z" fill="#2f8a6a" stroke="${INK}" stroke-width="5"/>
        <rect x="-240" y="-860" width="480" height="90" rx="10" fill="#2f8a6a" stroke="${INK}" stroke-width="6"/><text x="30" y="-800" font-family="DejaVu Sans, sans-serif" font-weight="800" font-size="46" text-anchor="middle" fill="#fff">${esc(o.nama || "RUMAH SAKIT")}</text><path d="M -200 -830 h 16 v -16 h 16 v 16 h 16 v 16 h -16 v 16 h -16 v -16 h -16 Z" fill="#fff"/>`;
    } else if (j === "ranjang_rs") { // ranjang rumah sakit + selimut; dudukan/permukaan y -150
      g = `<ellipse cx="0" cy="6" rx="300" ry="16" fill="#000" opacity=".2"/><rect x="-250" y="-330" width="30" height="330" fill="#aab4c0" stroke="${INK}" stroke-width="5"/><rect x="220" y="-250" width="30" height="250" fill="#aab4c0" stroke="${INK}" stroke-width="5"/>
        <rect x="-240" y="-170" width="480" height="40" rx="10" fill="#f4f6f6" stroke="${INK}" stroke-width="5"/><rect x="-240" y="-130" width="480" height="30" fill="#c8d0d8" stroke="${INK}" stroke-width="4"/><path d="M -60 -168 Q 80 -186 240 -168 L 246 -120 L -60 -124 Z" fill="#8fc4d8" stroke="${INK}" stroke-width="4"/>
        <ellipse cx="-160" cy="-180" rx="70" ry="24" fill="#fff" stroke="${INK}" stroke-width="4"/>${[-200, 200].map((px) => `<rect x="${px - 6}" y="-100" width="12" height="80" fill="#8a96a2"/><circle cx="${px}" cy="-14" r="14" fill="#2a2430"/>`).join("")}
        <path d="M -230 -230 L 230 -230" stroke="#aab4c0" stroke-width="8" opacity="${o.pagar === false ? 0 : 1}"/>`;
    } else if (j === "infus") { // tiang infus dengan kantong cairan menetes
      const q = (t * 1.2) % 1;
      g = `<rect x="-6" y="-560" width="12" height="560" fill="#aab4c0" stroke="${INK}" stroke-width="3"/><path d="M -60 6 L 60 6 M 0 0 L -40 6 M 0 0 L 40 6" stroke="${INK}" stroke-width="6"/><path d="M -50 -560 L 50 -560" stroke="#aab4c0" stroke-width="8"/><rect x="-36" y="-540" width="72" height="110" rx="16" fill="#dff3ff" stroke="${INK}" stroke-width="4" opacity=".9"/><rect x="-30" y="-490" width="60" height="54" rx="10" fill="#bfe3ff"/>
        <path d="M 0 -430 Q 30 -300 80 -200" stroke="#cfd5da" stroke-width="5" fill="none"/><circle cx="${q * 30}" cy="${-430 + q * 60}" r="4" fill="#7fc4ff"/>`;
    } else if (j === "meja_kantor") { // meja kerja + monitor + kursi kantor; {layar}
      g = `<ellipse cx="0" cy="6" rx="260" ry="14" fill="#000" opacity=".2"/><rect x="-240" y="-230" width="480" height="24" rx="6" fill="#e9e4d8" stroke="${INK}" stroke-width="5"/><rect x="-230" y="-206" width="20" height="206" fill="#aab4c0"/><rect x="210" y="-206" width="20" height="206" fill="#aab4c0"/><rect x="100" y="-206" width="110" height="150" fill="#d8d2c4" stroke="${INK}" stroke-width="4"/>
        <rect x="-20" y="-250" width="40" height="22" fill="#2a2430"/><rect x="-150" y="-430" width="300" height="190" rx="10" fill="#15121a" stroke="${INK}" stroke-width="5"/><rect x="-136" y="-416" width="272" height="160" rx="4" fill="${o.layar || "#7fc4ff"}" opacity="${0.7 + 0.2 * Math.sin(t * 2)}"/>${[0, 1, 2, 3].map((i) => `<rect x="-120" y="${-400 + i * 30}" width="${180 - i * 30}" height="12" rx="4" fill="#fff" opacity=".6"/>`).join("")}
        <rect x="-110" y="-224" width="160" height="14" rx="4" fill="#2a2430"/><path d="M 150 -232 q 10 -24 30 -22 q 8 18 -10 22 Z" fill="#fff" stroke="${INK}" stroke-width="3"/>`;
    } else if (j === "pantai") { // pantai: laut dari cakrawala (y=-ting) ke garis pantai (y=0) + pasir; ombak bergerak; {tinggi}
      const H = o.tinggi || 360; g = `<defs><linearGradient id="ptl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3f8ac9"/><stop offset="1" stop-color="#6ac9d9"/></linearGradient></defs><rect x="-1600" y="${-H}" width="3200" height="${H + 40}" fill="url(#ptl)"/>`;
      for (let i = 0; i < 6; i++) { const yy = -H + 30 + i * (H / 6), ph = t * (0.6 + i * 0.15) + i; let dd = `M -1600 ${yy}`; for (let xx = -1600; xx <= 1600; xx += 80) dd += ` Q ${xx + 40} ${yy - 6 - i} ${xx + 80} ${yy + Math.sin(ph + xx * 0.01) * 3}`; g += `<path d="${dd}" stroke="#fff" stroke-width="${2 + i}" fill="none" opacity=".35"/>`; }
      const om = Math.sin(t * 1.2) * 30; g += `<path d="M -1600 ${10 + om * 0.3} ${[...Array(41)].map((_, i) => `Q ${-1600 + i * 80 + 40} ${-14 + om * 0.3} ${-1600 + (i + 1) * 80} ${10 + om * 0.3}`).join(" ")} L 1600 900 L -1600 900 Z" fill="#f2deb0"/><path d="M -1600 ${10 + om * 0.3} ${[...Array(41)].map((_, i) => `Q ${-1600 + i * 80 + 40} ${-14 + om * 0.3} ${-1600 + (i + 1) * 80} ${10 + om * 0.3}`).join(" ")}" stroke="#fff" stroke-width="12" fill="none" opacity=".85"/>`;
      const R2 = rng(5); for (let i = 0; i < 30; i++) g += `<circle cx="${-800 + R2() * 1600}" cy="${80 + R2() * 700}" r="${2 + R2() * 4}" fill="#d9c08a" opacity=".6"/>`;
    } else if (j === "kamboja") { // pohon kamboja (kuburan) berbunga putih-kuning
      const ay = Math.sin(t * 1.1 + x) * 3;
      g = `<ellipse cx="0" cy="6" rx="180" ry="18" fill="#000" opacity=".18"/><path d="M -20 0 Q -10 -160 -80 -260 M 0 -140 Q 40 -220 90 -300 M -40 -220 Q -120 -280 -150 -330 M 50 -230 Q 120 -260 160 -320" stroke="#8a7a6a" stroke-width="26" fill="none" stroke-linecap="round"/>` +
        [[-80, -270], [90, -310], [-150, -340], [160, -330], [0, -360]].map(([cx, cy]) => `<ellipse cx="${cx + ay}" cy="${cy - 10}" rx="70" ry="40" fill="#5f9a46" stroke="${INK}" stroke-width="4"/>` + [0, 1, 2].map((k) => { const fx = cx + ay - 30 + k * 30, fy = cy - 30 + (k % 2) * 14; return [0, 72, 144, 216, 288].map((a) => `<ellipse cx="${fx + Math.cos(a * Math.PI / 180) * 8}" cy="${fy + Math.sin(a * Math.PI / 180) * 8}" rx="8" ry="5" fill="#fff" transform="rotate(${a} ${fx + Math.cos(a * Math.PI / 180) * 8} ${fy + Math.sin(a * Math.PI / 180) * 8})"/>`).join("") + `<circle cx="${fx}" cy="${fy}" r="4" fill="#f2c14e"/>`; }).join("")).join("");
    } else if (j === "kantor_gedung") { // gedung kantor kaca (tampak luar) {nama}
      g = `<ellipse cx="0" cy="8" rx="340" ry="18" fill="#000" opacity=".2"/><rect x="-300" y="-1100" width="600" height="1100" fill="#6f9fc9" stroke="${INK}" stroke-width="7"/><rect x="120" y="-1100" width="180" height="1100" fill="#000" opacity=".12"/>`;
      for (let yy = -1070; yy < -120; yy += 60) g += garis2(-300, yy, 300, yy);
      for (let xx = -240; xx < 300; xx += 80) g += `<line x1="${xx}" y1="-1100" x2="${xx}" y2="-120" stroke="#9fc4e2" stroke-width="3"/>`;
      g += `<path d="M -300 -500 L 0 -1100 L 120 -1100 L -300 -260 Z" fill="#fff" opacity=".15"/><rect x="-300" y="-120" width="600" height="120" fill="#cfd5da" stroke="${INK}" stroke-width="6"/><rect x="-80" y="-110" width="160" height="110" fill="#a8d4ee" stroke="${INK}" stroke-width="5"/><text x="0" y="-1130" font-family="DejaVu Sans, sans-serif" font-weight="800" font-size="50" text-anchor="middle" fill="#2a3036">${esc(o.nama || "")}</text>`;
    } else if (j === "monitor") { // layar besar di dinding (7 Nov): {w, h, judul (layar diam), nama, teks, komentar (detik relatif benda), suka}; komentar muncul membesar + teks diketik
      const W = o.w || 640, H = o.h || 400, kt = o.komentar == null ? -1 : tl - o.komentar;
      g = `<rect x="${-W / 2 - 18}" y="${-H - 18}" width="${W + 36}" height="${H + 36}" rx="18" fill="#0d1118" stroke="${INK}" stroke-width="7"/><rect x="${-W / 2}" y="${-H}" width="${W}" height="${H}" rx="8" fill="#16243a"/>`;
      g += `<rect x="-18" y="18" width="36" height="60" fill="#0d1118"/><rect x="-90" y="74" width="180" height="16" rx="8" fill="#0d1118"/>`;
      if (kt < 0) g += `<text x="0" y="${-H / 2 + 10}" font-family="DejaVu Sans, sans-serif" font-weight="800" font-size="${Math.min(64, W / 9)}" text-anchor="middle" fill="#8fb4e0" opacity="${0.6 + 0.4 * Math.sin(t * 2)}">${esc(o.judul || "Sahabat bertanya…")}</text>`;
      else { const k = kt < 0.3 ? 0.6 + 0.4 * halus(kt / 0.3) : 1, F = o.ukuran || 40, maks = Math.floor((W - 80) / (F * 0.56));
        const kata = String(o.teks || "").split(" "), baris = []; let b0 = ""; kata.forEach((w2) => { if ((b0 + " " + w2).trim().length > maks) { baris.push(b0.trim()); b0 = w2; } else b0 += " " + w2; }); if (b0.trim()) baris.push(b0.trim());
        const nTampil = Math.floor(clamp((kt - 0.3) / Math.max(0.6, kata.length * 0.06)) * String(o.teks || "").length); let sisa = nTampil;
        const tinggi = 120 + baris.length * F * 1.25;
        g += `<g transform="translate(0 ${-H / 2}) scale(${k})"><rect x="${-W / 2 + 26}" y="${-tinggi / 2}" width="${W - 52}" height="${tinggi}" rx="22" fill="#ffffff"/>`;
        g += `<circle cx="${-W / 2 + 80}" cy="${-tinggi / 2 + 52}" r="30" fill="${o.warna || "#5a8ac9"}"/><text x="${-W / 2 + 80}" y="${-tinggi / 2 + 64}" font-family="DejaVu Sans, sans-serif" font-weight="800" font-size="32" text-anchor="middle" fill="#fff">${esc((o.nama || "S").replace("@", "").charAt(0).toUpperCase())}</text>`;
        g += `<text x="${-W / 2 + 126}" y="${-tinggi / 2 + 62}" font-family="DejaVu Sans, sans-serif" font-weight="700" font-size="30" fill="#6b7280">${esc(o.nama || "@sahabat")}</text>`;
        baris.forEach((bt, i) => { const tampil = bt.slice(0, Math.max(0, sisa)); sisa -= bt.length + 1;
          g += `<text x="${-W / 2 + 60}" y="${-tinggi / 2 + 120 + i * F * 1.25 + F * 0.4}" font-family="DejaVu Sans, sans-serif" font-weight="700" font-size="${F}" fill="#111827">${esc(tampil)}</text>`; });
        g += `<path d="M ${W / 2 - 80} ${-tinggi / 2 + 40} c -14 -18 -40 -6 -30 14 l 30 26 l 30 -26 c 10 -20 -16 -32 -30 -14 z" fill="none" stroke="#9ca3af" stroke-width="4"/>` + (o.suka ? `<text x="${W / 2 - 80}" y="${-tinggi / 2 + 104}" font-family="DejaVu Sans, sans-serif" font-size="24" text-anchor="middle" fill="#9ca3af">${esc(o.suka)}</text>` : "") + `</g>`; }
      g += `<rect x="${-W / 2}" y="${-H}" width="${W}" height="${H * 0.35}" fill="#fff" opacity=".04"/>`;
    } else if (j === "mobil_luar") { // mobil taksi online tampak samping + stiker pintu (7 Nov): {warna, aksen, stiker, sub, arah ±1, jalan px/dtk roda berputar}
      const K = o.warna || "#f4f1ea", A = o.aksen || "#6b3fa0", ar = o.arah === -1 ? -1 : 1, rr = (t * v(o.jalan, tl, d, 0) / 70) * 57.3;
      g = `<ellipse cx="0" cy="8" rx="470" ry="22" fill="#000" opacity=".22"/><g transform="scale(${ar} 1)">
        <path d="M -440 -110 Q -450 -250 -380 -270 L -320 -280 L -240 -430 Q -230 -446 -200 -446 L 190 -446 Q 220 -446 236 -428 L 340 -290 L 410 -270 Q 452 -256 452 -190 L 452 -110 Q 452 -76 420 -76 L -410 -76 Q -440 -76 -440 -110 Z" fill="${K}" stroke="${INK}" stroke-width="7"/>
        <path d="M -296 -290 L -226 -414 L -20 -414 L -20 -290 Z" fill="#bfe3f5" stroke="${INK}" stroke-width="5"/><path d="M 4 -290 L 4 -414 L 196 -414 L 300 -290 Z" fill="#bfe3f5" stroke="${INK}" stroke-width="5"/>
        <path d="M -200 -400 L -150 -400 L -230 -300 L -270 -300 Z M 60 -404 L 100 -404 L 40 -300 L 10 -300 Z" fill="#fff" opacity=".45"/>
        <line x1="-8" y1="-290" x2="-8" y2="-90" stroke="${INK}" stroke-width="4" opacity=".6"/><line x1="-330" y1="-200" x2="440" y2="-200" stroke="${INK}" stroke-width="3" opacity=".25"/>
        <rect x="-60" y="-262" width="34" height="10" rx="5" fill="${INK}" opacity=".6"/><rect x="250" y="-262" width="34" height="10" rx="5" fill="${INK}" opacity=".6"/>
        <path d="M 412 -230 Q 450 -230 450 -200 L 412 -200 Z" fill="#fff6c8" stroke="${INK}" stroke-width="4"/><rect x="-444" y="-232" width="20" height="40" rx="6" fill="#e03131" stroke="${INK}" stroke-width="4"/>
        ${[-270, 270].map((cx) => `<path d="M ${cx - 96} -80 A 96 96 0 0 1 ${cx + 96} -80 Z" fill="#2a2430"/><g transform="translate(${cx} -72) rotate(${rr})"><circle r="70" fill="#2a2430" stroke="${INK}" stroke-width="6"/><circle r="36" fill="#c8ced8" stroke="${INK}" stroke-width="4"/>${[0, 72, 144, 216, 288].map((q) => `<line x1="0" y1="0" x2="0" y2="-32" stroke="#7a828e" stroke-width="7" transform="rotate(${q})"/>`).join("")}</g>`).join("")}
        <rect x="-438" y="-140" width="886" height="26" fill="${A}"/></g>`;
      if (o.stiker) { const cx = ar * -150, F = 74; g += `<g transform="translate(${cx} -205)"><rect x="-128" y="-56" width="256" height="112" rx="26" fill="${A}" stroke="${INK}" stroke-width="5"/><path d="M -100 -18 l 18 -18 l 18 18 l -18 30 Z" fill="${o.aksen2 || "#ffc83d"}"/><circle cx="-82" cy="-18" r="7" fill="${A}"/><text x="14" y="${F * 0.32}" font-size="${F}" font-weight="900" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" fill="${o.aksen2 || "#ffc83d"}">${esc(o.stiker)}</text>${o.sub ? `<text x="0" y="40" font-size="20" font-weight="700" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" fill="#fff">${esc(o.sub)}</text>` : ""}</g>`; }
    } else if (j === "logo_app") { // logo aplikasi fiktif (7 Nov): {teks, sub, warna, aksen}
      const A = o.warna || "#6b3fa0", Y = o.aksen || "#ffc83d", F = o.ukuran || 150;
      g = `<rect x="-190" y="-190" width="380" height="380" rx="90" fill="${A}" stroke="${INK}" stroke-width="8"/><g transform="translate(0 -95)"><path d="M -40 -10 a 40 40 0 1 1 80 0 c 0 34 -40 70 -40 70 c 0 0 -40 -36 -40 -70 Z" fill="${Y}" stroke="${INK}" stroke-width="5"/><circle cy="-10" r="15" fill="${A}"/></g><text y="${F * 0.8}" font-size="${F}" font-weight="900" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" fill="${Y}" letter-spacing="4">${esc(o.teks || "OTW")}</text>` + (o.sub ? `<text y="280" font-size="56" font-weight="800" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" fill="${A}" stroke="#fff" stroke-width="10" paint-order="stroke">${esc(o.sub)}</text>` : "");
    } else if (j === "setir") { // setir mobil di depan pengemudi (7 Nov): {putar derajat|[[t,v]]}
      const r = v(o.putar, tl, d, 0) + 3 * Math.sin(t * 1.7);
      g = `<path d="M 10 30 L 70 160" stroke="#22252b" stroke-width="30" stroke-linecap="round"/><g transform="rotate(${r})"><ellipse cx="0" cy="0" rx="34" ry="120" fill="none" stroke="#1d2026" stroke-width="26"/><ellipse cx="0" cy="0" rx="14" ry="40" fill="#30343c" stroke="${INK}" stroke-width="4"/></g>`;
    } else if (j === "mik") { // mikrofon podcast di meja (7 Nov): {arah ±1 = arah mulut, tinggi}; pangkal di (0,0) = permukaan meja
      const a = o.arah || 1, T = o.tinggi || 240;
      g = `<ellipse cx="0" cy="4" rx="60" ry="12" fill="#000" opacity=".3"/><rect x="-46" y="-14" width="92" height="18" rx="8" fill="#2a2f38" stroke="${INK}" stroke-width="5"/>` +
        `<path d="M 0 -10 L ${-a * 30} ${-T * 0.55} L ${a * 40} ${-T * 0.8}" stroke="#3a404a" stroke-width="12" fill="none" stroke-linejoin="round"/><circle cx="${-a * 30}" cy="${-T * 0.55}" r="10" fill="#565e6c" stroke="${INK}" stroke-width="3"/>` +
        `<g transform="translate(${a * 40} ${-T * 0.8}) rotate(${a * 60})"><rect x="-26" y="-80" width="52" height="96" rx="24" fill="#1e2228" stroke="${INK}" stroke-width="5"/><rect x="-30" y="-92" width="60" height="70" rx="28" fill="#3a3f48" stroke="${INK}" stroke-width="5"/>` + [0, 1, 2].map((k) => `<line x1="-22" y1="${-78 + k * 18}" x2="22" y2="${-78 + k * 18}" stroke="#565e6c" stroke-width="3"/>`).join("") + `<circle cx="0" cy="0" r="5" fill="${Math.sin(t * 4) > 0 ? "#ff4f4f" : "#7a2a2a"}"/></g>`;
    } else if (j === "meja") { // meja di depan (pakai depan:true); o.w lebar
      const W = o.w || 640; g = `<rect x="${-W / 2}" y="-30" width="${W}" height="40" rx="8" fill="#b07c52" stroke="${INK}" stroke-width="7"/><rect x="${-W / 2 + 30}" y="10" width="${W - 60}" height="300" fill="#9c6a42" stroke="${INK}" stroke-width="7"/>` + garis2(-W / 2 + 30, 160, W / 2 - 30, 160);
    } else if (j === "rincian") { // kartu rincian gaji terpotong (gaya Papan): {judul, gaji, baris:[[detik,"label",nominal]], akhir:"teks", ukuran}
      const F = "DejaVu Sans, Arial, sans-serif", W = 800, rows = o.baris || [], RH = 96, H = 250 + rows.length * RH + 40, top = -H / 2, masuk = halus(tl / 0.4);
      const rp = (n) => "Rp " + String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
      let sisa = o.gaji || 0; rows.forEach(([at, , n]) => { sisa -= n * halus((tl - at) / 0.45); });
      const frac = clamp(sisa / (o.gaji || 1)), wr = warna("#d9342b", "#2f9e44", frac);
      g = `<g transform="rotate(${(1 - masuk) * 6}) scale(${0.7 + 0.3 * masuk})" opacity="${clamp(tl / 0.2)}"><rect x="${-W / 2 + 10}" y="${top + 16}" width="${W}" height="${H}" rx="30" fill="#000" opacity=".35"/>
        <rect x="${-W / 2}" y="${top}" width="${W}" height="${H}" rx="30" fill="#fffaf0" stroke="${INK}" stroke-width="8"/><rect x="${-W / 2}" y="${top}" width="${W}" height="170" rx="30" fill="#1f3a5f"/><rect x="${-W / 2}" y="${top + 120}" width="${W}" height="50" fill="#1f3a5f"/>
        <text x="${-W / 2 + 40}" y="${top + 56}" font-family="${F}" font-weight="800" font-size="32" letter-spacing="4" fill="#ffd27a">${esc(o.judul || "GAJI BULAN INI")}</text>
        <text x="${-W / 2 + 40}" y="${top + 136}" font-family="${F}" font-weight="800" font-size="74" fill="${wr}" stroke="#fffaf0" stroke-width="1">${rp(sisa)}</text>`;
      rows.forEach(([at, label, n], i) => { const pp = halus((tl - at) / 0.3); if (pp <= 0) return; const yy = top + 200 + i * RH;
        g += `<g opacity="${pp}" transform="translate(${(1 - pp) * 70} 0)"><rect x="${-W / 2 + 28}" y="${yy}" width="${W - 56}" height="${RH - 14}" rx="18" fill="#ffe9e6" stroke="#d9342b" stroke-width="3"/>
          <text x="${-W / 2 + 56}" y="${yy + 52}" font-family="${F}" font-weight="700" font-size="36" fill="${INK}">${esc(label)}</text>
          <text x="${W / 2 - 56}" y="${yy + 52}" font-family="${F}" font-weight="800" font-size="38" text-anchor="end" fill="#c92a2a">- ${rp(n).slice(3)}</text></g>`; });
      if (o.akhir) { const aa = o.akhir_at != null ? o.akhir_at : (rows.length ? rows[rows.length - 1][0] + 0.9 : 1), pa = halus((tl - aa) / 0.3);
        if (pa > 0) g += `<g transform="translate(0 ${top + H + 40}) scale(${0.8 + 0.2 * pa})" opacity="${pa}"><rect x="-340" y="-44" width="680" height="88" rx="22" fill="#d9342b" stroke="${INK}" stroke-width="6"/><text x="0" y="14" font-family="${F}" font-weight="800" font-size="36" text-anchor="middle" fill="#fff">${esc(o.akhir)}</text></g>`; }
      g += `</g>`;
    } else if (j === "rantai") { // rantai tanggungan (gaya Papan): {node:[{teks,warna}], jeda, loop:true}
      const F = "DejaVu Sans, Arial, sans-serif", N = o.node || [], je = o.jeda || 0.9, gap = Math.min(210, 640 / Math.max(1, N.length - 1)), x0 = -gap * (N.length - 1) / 2;
      N.forEach((nd, i) => { if (i > 0) { const pa = clamp((tl - (i - 1) * je - 0.25) / 0.5); if (pa > 0) { const xa = x0 + (i - 1) * gap + 62, xb = x0 + i * gap - 62, xe = xa + (xb - xa) * pa;
          g += `<path d="M ${xa} 0 L ${xe} 0" stroke="#e8c26a" stroke-width="10" stroke-linecap="round"/>`; if (pa >= 1) g += `<path d="M ${xb - 20} -18 L ${xb} 0 L ${xb - 20} 18" stroke="#e8c26a" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
          const cx = xa + (xb - xa) * ((tl * 0.9) % 1); if (pa >= 1) g += `<circle cx="${cx}" cy="-34" r="20" fill="#ffd93a" stroke="${INK}" stroke-width="4"/><text x="${cx}" y="-27" font-family="${F}" font-weight="800" font-size="18" text-anchor="middle" fill="${INK}">Rp</text>`; } }
        const pp = halus((tl - i * je) / 0.35); if (pp <= 0) return; const cx = x0 + i * gap, kl = nd.warna || (i === 0 ? "#f2a54a" : "#7fb3e8"), bounce = (1 - pp) * -40;
        g += `<g transform="translate(${cx} ${bounce}) scale(${0.6 + 0.4 * pp})" opacity="${pp}"><circle cx="0" cy="-30" r="44" fill="#f2dcc2" stroke="${INK}" stroke-width="7"/><path d="M -58 90 Q -58 22 0 22 Q 58 22 58 90 Z" fill="${kl}" stroke="${INK}" stroke-width="7"/>
          <circle cx="-14" cy="-34" r="5" fill="${INK}"/><circle cx="14" cy="-34" r="5" fill="${INK}"/><path d="M -14 -14 Q 0 -4 14 -14" stroke="${INK}" stroke-width="5" fill="none" stroke-linecap="round"/>
          <text x="0" y="146" font-family="${F}" font-weight="800" font-size="30" text-anchor="middle" fill="#fffaf0" stroke="${INK}" stroke-width="6" paint-order="stroke">${esc(nd.teks || "")}</text></g>`; });
    } else if (j === "stempel") { // stempel merah dicap: membesar lalu menghentak ke ukuran normal
      const k = tl < 0.22 ? 1.9 - 0.9 * halus(tl / 0.22) : 1, F = o.ukuran || 96, W = String(o.teks).length * F * 0.66 + 80;
      g = `<g transform="rotate(${o.rot ?? -10}) scale(${k})" opacity="${clamp(tl / 0.12)}"><rect x="${-W / 2}" y="${-F * 0.85}" width="${W}" height="${F * 1.6}" rx="18" fill="#fff" fill-opacity=".1" stroke="#e03131" stroke-width="12"/><rect x="${-W / 2 + 16}" y="${-F * 0.85 + 16}" width="${W - 32}" height="${F * 1.6 - 32}" rx="10" fill="none" stroke="#e03131" stroke-width="4"/><text x="0" y="${F * 0.34}" font-size="${F}" font-weight="900" text-anchor="middle" fill="#e03131" font-family="DejaVu Sans, Arial, sans-serif">${esc(o.teks)}</text></g>`;
    } else if (j === "tanda") { // lencana besar ✓ / ✗
      const ok = o.ok !== false, k = tl < 0.25 ? 0.4 + 0.6 * halus(tl / 0.25) : 1;
      g = `<g transform="scale(${k})"><circle r="90" fill="${ok ? "#2f9e44" : "#e03131"}" stroke="${INK}" stroke-width="8"/>` + (ok ? `<path d="M -42 4 L -10 36 L 46 -30" stroke="#fff" stroke-width="22" fill="none" stroke-linecap="round" stroke-linejoin="round"/>` : `<path d="M -36 -36 L 36 36 M 36 -36 L -36 36" stroke="#fff" stroke-width="22" stroke-linecap="round"/>`) + `</g>`;
    } else if (j === "retakan") { // tanah merekah: celah gelap bercahaya dari dalam + debu naik. o.buka 0-1 (lebar celah), o.cahaya warna pijar, o.goyang getaran halus, o.seed varian bentuk
      const bk = v(o.buka, t, d, 1), cwarna = o.cahaya || "#ff8a3c", gy = (o.goyang ? Math.sin(t * 37) * o.goyang : 0);
      const RT = rng(o.seed || 3);
      g = `<g transform="translate(${gy} 0)">`;
      // tanah: dasar gelap bertekstur (gumpalan acak, bukan rata) supaya bukan blok polos
      g += `<rect x="-540" y="-40" width="1080" height="720" fill="#161210"/>`;
      for (let i = 0; i < 46; i++) { const tx = -520 + RT() * 1040, ty = -30 + RT() * 700, tr = 6 + RT() * 22, tl2 = 0.08 + RT() * 0.1;
        g += `<ellipse cx="${tx}" cy="${ty}" rx="${tr}" ry="${tr * (0.5 + RT() * 0.4)}" fill="#0c0a09" opacity="${tl2}"/>`; }
      g += `<defs><radialGradient id="rtg" cx=".5" cy=".42" r=".65"><stop offset="0" stop-color="${cwarna}" stop-opacity=".92"/><stop offset=".55" stop-color="${cwarna}" stop-opacity=".4"/><stop offset="1" stop-color="${cwarna}" stop-opacity="0"/></radialGradient></defs>`;
      // jalur retak utama: titik acak berjalan ke bawah, melebar tak simetris (zig-zag organik, bukan cermin kiri-kanan)
      const n = 11, kiri = [], kanan = [];
      for (let i = 0; i <= n; i++) { const py = -30 + (700 / n) * i, prog = i / n;
        const lebar = (8 + 165 * bk) * (0.35 + 0.65 * Math.sin(prog * Math.PI)) * (0.7 + 0.5 * RT());
        const geser = (RT() - 0.5) * 70 * prog;
        kiri.push([geser - lebar * (0.6 + RT() * 0.5), py]); kanan.push([geser + lebar * (0.6 + RT() * 0.5), py]); }
      const jalur = (arr) => arr.map((p, i) => (i === 0 ? "M" : "L") + ` ${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
      g += `<path d="${jalur(kiri)} L ${kanan[n][0].toFixed(1)} ${kanan[n][1].toFixed(1)} ${jalur(kanan.slice().reverse()).replace("M", "L")} Z" fill="url(#rtg)"/>`;
      g += `<path d="${jalur(kiri)}" fill="none" stroke="${cwarna}" stroke-width="${2.5 + bk}" opacity=".85" stroke-linejoin="round"/>`;
      g += `<path d="${jalur(kanan)}" fill="none" stroke="${cwarna}" stroke-width="${2.5 + bk}" opacity=".85" stroke-linejoin="round"/>`;
      // cabang retak tipis (rambut) menjalar dari pinggir jalur utama, acak
      for (let c = 0; c < 5; c++) { const base = (kiri[2 + (c % (n - 3))] || kiri[2]), sisi = c % 2 ? 1 : -1, len = 60 + RT() * 160, ang = sisi * (30 + RT() * 50) * (Math.PI / 180);
        let bx = base[0], by = base[1], path = `M ${bx.toFixed(1)} ${by.toFixed(1)}`;
        for (let s = 0; s < 3; s++) { bx += Math.sin(ang + (RT() - 0.5)) * (len / 3); by += Math.cos(ang) * (len / 3) * 0.4 + 30; path += ` L ${bx.toFixed(1)} ${by.toFixed(1)}`; }
        if (bk > 0.15) g += `<path d="${path}" fill="none" stroke="${cwarna}" stroke-width="${1 + bk}" opacity="${0.3 + 0.3 * bk}"/>`; }
      // kerikil/bongkah gelap tak beraturan di bibir retakan
      for (let i = 0; i < 10; i++) { const side = i % 2 ? 1 : -1, ref = (side < 0 ? kiri : kanan)[1 + (i % (n - 2))], rx = ref[0] - side * (8 + RT() * 10), ry = ref[1] + (RT() - 0.5) * 20, rs = 8 + RT() * 16;
        g += `<path d="M ${rx - rs} ${ry} L ${rx} ${ry - rs * 0.8} L ${rx + rs} ${ry - rs * 0.1} L ${rx + rs * 0.3} ${ry + rs * 0.7} Z" fill="#241c17" opacity=".85"/>`; }
      for (let i = 0; i < 14; i++) { const rr = RT(), dy = 660 - ((t * (40 + rr * 60) + i * 70) % 760), dx = (rr - 0.5) * (40 + 150 * bk) * 2.4, da = clamp(1 - dy / 700) * 0.6;
        g += `<circle cx="${dx}" cy="${dy - 30}" r="${4 + rr * 10}" fill="#d8c8b8" opacity="${da}"/>`; }
      g += `</g>`;
    } else if (j === "bayang_misteri") { // massa gelap ambigu: bentuk TIDAK dipastikan (bukan tokoh/monster) - hanya siluet bergeser, berdenyut, dikelilingi cahaya retakan. o.besar skala, o.nafas amplitudo denyut, o.cahaya warna rim
      const bss = v(o.besar, t, d, 1), nf = 1 + (o.nafas ?? 0.05) * Math.sin(t * 1.6), cw = o.cahaya || "#ff8a3c";
      g = `<g transform="scale(${bss * nf})">`;
      g += `<defs><radialGradient id="bmg" cx=".5" cy=".65" r=".75"><stop offset="0" stop-color="${cw}" stop-opacity=".35"/><stop offset="1" stop-color="${cw}" stop-opacity="0"/></radialGradient></defs>`;
      g += `<ellipse cx="0" cy="40" rx="260" ry="90" fill="url(#bmg)"/>`;
      const R2 = rng(7); let pts = [];
      for (let i = 0; i < 10; i++) { const ang = (i / 10) * Math.PI * 2, rad = 120 + R2() * 70 + Math.sin(t * 0.9 + i) * 14;
        pts.push([Math.cos(ang) * rad * 0.8, -60 + Math.sin(ang) * rad]); }
      g += `<path d="M ${pts.map((p) => p.join(",")).join(" L ")} Z" fill="#0b0a10" opacity=".96"/>`;
      g += `<path d="M ${pts.map((p) => p.join(",")).join(" L ")} Z" fill="none" stroke="${cw}" stroke-width="3" opacity="${0.4 + 0.3 * Math.sin(t * 2.2)}"/>`;
      g += `</g>`;
    } else if (j === "kerumunan") { // (16 Nov) kerumunan siluet DIAM menghadap cahaya. n, w sebar, baris, k skala, seed, rim 0-1 (+rimwarna), sisi 1 = cahaya dari kanan / -1 kiri (bawaan: ke arah tengah), pose berdiri|telinga|wajah|angkat|tunduk|tolak, bara 0-1 (bara di telapak + uap kepala), api 0-1 (jubah api), hangus 0-1 (retak bara di badan)
      const n = o.n || 12, w = o.w == null ? 900 : o.w, R = rng(o.seed || 5), dk = o.baris || 3, L = [];
      for (let i = 0; i < n; i++) { const r1 = R(), r2 = R(), r3 = R(), row = n === 1 ? 0 : Math.floor(r2 * dk); L.push({ px: n === 1 ? 0 : (r1 - 0.5) * w * (1 - row * 0.12), py: -row * 40 + (r3 - 0.5) * 18, k: (o.k || 1) * (1 - row * 0.15) * (n === 1 ? 1 : 0.86 + r3 * 0.28), ph: r1 * 6, row }); }
      L.sort((a, b) => b.row - a.row || a.k - b.k);
      L.forEach((f) => { g += figur(f.px, f.py, f.k, { pose: o.pose || "berdiri", rim: v(o.rim, t, d, 0.6), rimwarna: o.rimwarna, sisi: o.sisi == null ? (f.px < 0 ? 1 : -1) : o.sisi, t: t + f.ph, bara: v(o.bara, t, d, 0), api: v(o.api, t, d, 0), hangus: v(o.hangus, t, d, 0), warna: o.warna, gelap: f.row * 0.12 }); });
    } else if (j === "belah") { // (16 Nov) bumi terbelah dalam PERSPEKTIF (tampak samping): (0,0) = ujung celah di cakrawala; celah melebar ke arah kamera sampai y = H. buka 0-1, lebar px di bawah, cahaya warna, goyang px, seed
      const bk = v(o.buka, t, d, 1), H = o.H || 900, Wb = (o.lebar || 820) * bk, cw = o.cahaya || "#ff7a2a", R = rng(o.seed || 7), gy = o.goyang ? Math.sin(t * 41) * o.goyang * Math.min(1, bk * 2) : 0, id = "bl" + Math.round(x * 3 + y);
      g = `<defs><radialGradient id="${id}g" cx="0" cy="${H * 0.8}" r="${900 * (0.4 + bk)}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="${cw}" stop-opacity="${0.55 * Math.min(1, bk * 1.6)}"/><stop offset=".45" stop-color="${cw}" stop-opacity="${0.18 * Math.min(1, bk * 1.6)}"/><stop offset="1" stop-color="${cw}" stop-opacity="0"/></radialGradient>
        <linearGradient id="${id}i" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff5a1a"/><stop offset=".5" stop-color="${cw}"/><stop offset="1" stop-color="#ffe7a8"/></linearGradient><filter id="${id}f" x="-50%" y="-20%" width="200%" height="140%"><feGaussianBlur stdDeviation="14"/></filter></defs>`;
      if (o.tanah !== false) g += `<defs><linearGradient id="${id}t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${o.tanah_atas || "#2a2230"}"/><stop offset=".35" stop-color="#17121a"/><stop offset="1" stop-color="#0a080c"/></linearGradient></defs><rect x="-1800" y="0" width="3600" height="${H + 900}" fill="url(#${id}t)"/>` + (() => { let q = ""; const RR = rng(31); for (let i = 0; i < 60; i++) { const pz = RR(), yy = H * pz * pz, xx = (RR() - 0.5) * (300 + 2600 * pz); q += `<ellipse cx="${xx}" cy="${yy}" rx="${(8 + RR() * 30) * (0.2 + pz)}" ry="${(3 + RR() * 8) * (0.2 + pz)}" fill="#000" opacity=".35"/>`; } return q; })();
      g += `<g transform="translate(${gy} 0)"><rect x="-1800" y="-700" width="3600" height="${H + 1400}" fill="url(#${id}g)"/>`;
      const N = 26, kiri = [], kanan = [], inti = [];
      for (let i = 0; i <= N; i++) { const p = i / N, yy = H * Math.pow(p, 1.15), cx = Math.sin(p * 9 + (o.seed || 7)) * 34 * p + (R() - 0.5) * 10 * p, hw = (Wb / 2) * p * (0.82 + R() * 0.36);
        kiri.push([cx - hw - R() * 18 * p, yy]); kanan.push([cx + hw + R() * 18 * p, yy]); inti.push([cx, yy, hw]); }
      const poly = (A, B) => "M " + A.map((q) => q.join(" ")).join(" L ") + " L " + B.slice().reverse().map((q) => q.join(" ")).join(" L ") + " Z";
      if (bk > 0.005) {
        g += `<path d="${poly(kiri, kanan)}" fill="#0b0605" stroke="#050303" stroke-width="6"/>`; // bibir celah
        const dl = kiri.map((q, i) => [mix(q[0], inti[i][0], 0.32), q[1] + 26 * (i / N)]), dr = kanan.map((q, i) => [mix(q[0], inti[i][0], 0.32), q[1] + 26 * (i / N)]);
        g += `<path d="${poly(kiri, dl)}" fill="#2a130b"/><path d="${poly(dr, kanan)}" fill="#1c0d08"/>`; // dinding dalam (kiri lebih terang)
        const ci = inti.map((q) => [q[0] - q[2] * 0.42, q[1] + 12]), cj = inti.map((q) => [q[0] + q[2] * 0.42, q[1] + 12]);
        g += `<path d="${poly(ci, cj)}" fill="url(#${id}i)" filter="url(#${id}f)" opacity="${0.75 + 0.25 * Math.sin(t * 5)}"/><path d="${poly(ci.map((q, i) => [mix(q[0], inti[i][0], 0.6), q[1]]), cj.map((q, i) => [mix(q[0], inti[i][0], 0.6), q[1]]))}" fill="#fff3c8" opacity=".8"/>`;
        for (let s = 0; s < 9; s++) { const i = 3 + Math.floor(R() * (N - 4)), sd = R() < 0.5 ? kiri : kanan, q = sd[i], dir = sd === kiri ? -1 : 1, L0 = (60 + R() * 160) * (i / N);
          g += `<path d="M ${q[0]} ${q[1]} l ${dir * L0 * 0.6} ${-L0 * 0.12} l ${dir * L0 * 0.4} ${L0 * 0.1}" stroke="#070404" stroke-width="${3 + 5 * i / N}" fill="none"/><path d="M ${q[0]} ${q[1]} l ${dir * L0 * 0.6} ${-L0 * 0.12}" stroke="${cw}" stroke-width="2" opacity="${0.5 * bk}" fill="none"/>`; }
        for (let s = 0; s < 6; s++) { const i = 6 + Math.floor(R() * (N - 7)), sd = R() < 0.5 ? kiri : kanan, q = sd[i], dir = sd === kiri ? -1 : 1, k = i / N * (0.6 + R() * 0.6);
          g += `<path d="M ${q[0]} ${q[1]} l ${dir * 70 * k} ${-26 * k} l ${dir * 40 * k} ${36 * k} l ${-dir * 100 * k} ${10 * k} Z" fill="#1d1410" stroke="#050303" stroke-width="3"/><path d="M ${q[0]} ${q[1]} l ${dir * 70 * k} ${-26 * k}" stroke="${cw}" stroke-width="3" opacity=".7"/>`; } // bongkah terangkat
        const m = Math.round(34 * bk);
        for (let s = 0; s < m; s++) { const p0 = 0.15 + R() * 0.85, sp = 0.25 + R() * 0.35, ph = R(), q = inti[Math.round(p0 * N)], fz = ((t * sp + ph) % 1), ex = q[0] + (R() - 0.5) * q[2] + Math.sin(t * 2 + ph * 9) * 20, ey = q[1] - fz * 520 * (0.4 + p0);
          g += `<circle cx="${ex}" cy="${ey}" r="${(2 + R() * 4) * (0.5 + p0)}" fill="${R() < 0.6 ? "#ffcf7a" : "#ff7a2a"}" opacity="${(1 - fz) * 0.9}"/>`; } // bara naik
        if (o.debu !== false) for (let s = 0; s < 8; s++) { const p0 = 0.3 + R() * 0.7, ph = R(), q = inti[Math.round(p0 * N)], fz = ((t * 0.12 + ph) % 1);
          g += `<ellipse cx="${q[0] + (R() - 0.5) * 120}" cy="${q[1] - fz * 380}" rx="${(80 + fz * 160) * p0}" ry="${(40 + fz * 70) * p0}" fill="#5a3a2c" opacity="${0.22 * (1 - fz) * bk}"/>`; } // debu coklat
      }
      g += `</g>`;
    } else if (j === "jurang") { // (16 Nov) jurang neraka dilihat dari tepi atas: cincin tebing mengecil ke dasar membara. jatuh 0-1 (batu dari atas ke dasar), dasar 0-1 terang, cahaya warna
      const jt = v(o.jatuh, t, d, -1), ds = v(o.dasar, t, d, 1), cw = o.cahaya || "#ff6a24", R = rng(o.seed || 9), id = "jr" + Math.round(x + y);
      g = `<defs><radialGradient id="${id}"><stop offset="0" stop-color="#fff0c0"/><stop offset=".25" stop-color="${cw}"/><stop offset="1" stop-color="#3a0d05" stop-opacity="0"/></radialGradient></defs>`;
      const K = 14;
      for (let k = 0; k < K; k++) { const p = k / K, r = 900 * Math.pow(1 - p, 1.35) + 30, cy = 380 * Math.pow(p, 0.8), c = campur(warna("#140806", "#000000", 0), cw, Math.pow(p, 1.6) * 0.9 * ds);
        let pts = ""; for (let a = 0; a <= 36; a++) { const ang = (a / 36) * Math.PI * 2, jj = 1 + (R() - 0.5) * 0.12; pts += `${a ? "L" : "M"} ${Math.cos(ang) * r * jj} ${cy + Math.sin(ang) * r * 0.42 * jj} `; }
        g += `<path d="${pts}Z" fill="${c}" stroke="#070302" stroke-width="${5 * (1 - p) + 1}" stroke-opacity=".6"/>`; }
      g += `<ellipse cx="0" cy="380" rx="180" ry="80" fill="url(#${id})" opacity="${0.6 + 0.4 * ds * (0.85 + 0.15 * Math.sin(t * 4))}"/>`;
      if (jt >= 0 && jt <= 1) { const q = Math.pow(jt, 1.6), bx = Math.sin(jt * 3) * 40, by = mix(-900, 370, q), bs = mix(1.4, 0.04, q);
        g += `<g transform="translate(${bx} ${by}) scale(${bs}) rotate(${jt * 720})"><path d="M -60 -40 L 10 -70 L 70 -20 L 55 45 L -20 60 L -70 15 Z" fill="#241712" stroke="#060303" stroke-width="6"/><path d="M -60 -40 L 10 -70 L 70 -20" stroke="${cw}" stroke-width="7" fill="none" opacity="${0.3 + 0.6 * q}"/></g>`; }
      if (jt > 1 && jt < 1.25) g += `<ellipse cx="0" cy="380" rx="${260 * (jt - 1) * 4 + 60}" ry="${110 * (jt - 1) * 4 + 30}" fill="#fff4cf" opacity="${(1.25 - jt) * 4 * 0.8}"/>`;
    } else if (j === "zaqqum") { // (16 Nov) pohon zaqqum: batang hitam berpilin, dahan berduri, buah bara menyala (QS 44:43-46). tumbuh 0-1, nyala 0-1
      const tb = v(o.tumbuh, t, d, 1), ny = v(o.nyala, t, d, 1), R = rng(o.seed || 13), ay = Math.sin(t * 1.4) * 3;
      g += `<defs><radialGradient id="zq${Math.round(x)}"><stop offset="0" stop-color="#ff5a1a" stop-opacity="${0.35 * ny}"/><stop offset="1" stop-color="#ff5a1a" stop-opacity="0"/></radialGradient></defs><ellipse cx="0" cy="-380" rx="${620 * tb}" ry="${560 * tb}" fill="url(#zq${Math.round(x)})"/>`;
      g += `<path d="M -40 0 C -70 -150 30 -260 -10 -420 C -40 -540 40 -620 10 -${720 * tb}" stroke="#0a0606" stroke-width="${70 * tb}" fill="none" stroke-linecap="round"/><path d="M -40 0 C -70 -150 30 -260 -10 -420" stroke="#ff7a2a" stroke-width="5" fill="none" opacity="${0.35 * ny}"/>`;
      const D = [[-420, -0.9], [-500, 0.8], [-590, -0.6], [-650, 0.55], [-330, 0.75], [-260, -0.7]];
      D.forEach(([hy, dir], i) => { if (tb < 0.3 + i * 0.1) return; const L0 = (220 + R() * 160) * tb, a = ay * dir;
        g += `<path d="M 0 ${hy} Q ${dir * L0 * 0.5} ${hy - 90 + a} ${dir * L0} ${hy - 30 - R() * 120 + a}" stroke="#0a0606" stroke-width="${22 * tb}" fill="none" stroke-linecap="round"/>`;
        for (let s = 0; s < 6; s++) { const u = 0.2 + s * 0.14, sx = dir * L0 * u, sy = hy - 60 * u + a * u; g += `<path d="M ${sx} ${sy} l ${dir * 14} ${-38 - R() * 22} l ${dir * 10} 34 Z" fill="#0a0606"/>`; }
        const fx = dir * L0, fy = hy - 30 - R() * 120 + a, fl = 0.75 + 0.25 * Math.sin(t * 7 + i);
        g += `<circle cx="${fx}" cy="${fy + 34}" r="${46 * tb}" fill="#ff7a2a" opacity="${0.35 * ny * fl}"/><path d="M ${fx - 26} ${fy + 20} q 26 -50 52 0 q 6 40 -26 52 q -32 -12 -26 -52 Z" fill="#1a0a06" stroke="#ff8a3a" stroke-width="${3 * ny}"/><circle cx="${fx}" cy="${fy + 40}" r="${12 * ny * fl}" fill="#ffd27a" opacity="${ny}"/>`; });
    } else if (j === "cawan") { // (16 Nov) periuk/bejana berisi cairan mendidih: gelembung + uap (QS 47:15; HR Bukhari 6562 'seperti periuk'). didih 0-1, warna cairan, uap 0-1
      const dd = v(o.didih, t, d, 1), cc = o.warna || "#ff8a3a", R = rng(o.seed || 17), uap = v(o.uap, t, d, 1);
      g += `<ellipse cx="0" cy="-10" rx="300" ry="50" fill="${cc}" opacity="${0.15 * dd}"/><path d="M -230 -260 Q -250 -40 -120 0 L 120 0 Q 250 -40 230 -260 Z" fill="#1f1714" stroke="#060404" stroke-width="10"/><path d="M -230 -260 Q -250 -40 -120 0" stroke="${cc}" stroke-width="5" fill="none" opacity=".45"/>`;
      g += `<ellipse cx="0" cy="-260" rx="236" ry="52" fill="#2a1f1a" stroke="#060404" stroke-width="10"/><ellipse cx="0" cy="-256" rx="206" ry="40" fill="${cc}"/><ellipse cx="0" cy="-260" rx="150" ry="24" fill="#ffe3a0" opacity="${0.5 + 0.3 * Math.sin(t * 9)}"/>`;
      for (let s = 0; s < 14; s++) { const ph = R(), sp = 1.2 + R() * 1.6, fz = (t * sp + ph) % 1, bx = (R() - 0.5) * 340, r0 = (6 + R() * 16) * dd;
        if (fz < 0.7) g += `<circle cx="${bx}" cy="${-252 - fz * 18}" r="${r0 * (0.4 + fz)}" fill="none" stroke="#fff1c8" stroke-width="3" opacity="${dd * (0.9 - fz)}"/>`; }
      for (let s = 0; s < 5; s++) { const ph = R(), fz = (t * 0.35 + ph) % 1, bx = (R() - 0.5) * 260, sw = Math.sin(t * 2 + s) * 40;
        g += `<path d="M ${bx} -290 q ${sw} ${-120 * fz} ${-sw * 0.5} ${-260 * fz - 40}" stroke="#e8e0d8" stroke-width="${26 * (1 - fz)}" fill="none" stroke-linecap="round" opacity="${0.22 * uap * (1 - fz)}"/>`; }
    } else if (j === "rantai_tarik") { // (16 Nov) puluhan rantai tegang dari luar layar menuju (0,0); tarik = jarak geser mata rantai (px, boleh [[t,v]]); n; malaikat TIDAK digambar
      const n = o.n || 14, tr = v(o.tarik, t, d, t * 40), R = rng(o.seed || 19), r0 = o.r0 || 230;
      for (let i = 0; i < n; i++) { const a = -Math.PI * (0.08 + 0.84 * (i + R() * 0.6) / n) + (o.putar || 0), ca = Math.cos(a), sa = Math.sin(a), L0 = 1700, far = 0.55 + R() * 0.45;
        const c1 = campur(warna("#5c5660", "#000000", 0), "#120a0a", 1 - far), step = 46;
        for (let s = r0; s < L0; s += step) { const ss = s + (tr % (step * 2)), px = ca * ss, py = sa * ss * 0.95, rot = Math.atan2(sa, ca) * 180 / Math.PI, alt = Math.floor((s - r0) / step) % 2;
          g += alt ? `<rect x="${px - 24}" y="${py - 6}" width="48" height="12" rx="6" fill="${c1}" transform="rotate(${rot} ${px} ${py})"/>` : `<ellipse cx="${px}" cy="${py}" rx="27" ry="14" fill="none" stroke="${c1}" stroke-width="9" transform="rotate(${rot} ${px} ${py})"/>`; }
        g += `<line x1="${ca * r0}" y1="${sa * r0}" x2="${ca * L0}" y2="${sa * L0}" stroke="#ffb05a" stroke-width="2" opacity="${0.18 * far}"/>`; }
    } else if (j === "massa_api") { // (16 Nov) massa api raksasa berdenyut (neraka didatangkan); r jari-jari, kuat 0-1
      const r = v(o.r, t, d, 260), kk = v(o.kuat, t, d, 1), id = "ma" + Math.round(x + y);
      g = `<defs><radialGradient id="${id}"><stop offset="0" stop-color="#fff2c4"/><stop offset=".3" stop-color="#ffb347"/><stop offset=".65" stop-color="#ff4a12"/><stop offset="1" stop-color="#5a0a02" stop-opacity="0"/></radialGradient></defs>`;
      g += `<circle r="${r * 3}" fill="#ff4a12" opacity="${0.12 * kk}"/>`;
      for (let i = 0; i < 18; i++) { const a = (i / 18) * Math.PI * 2, h = r * (0.55 + 0.35 * Math.sin(t * 6 + i * 1.7)), ca = Math.cos(a), sa = Math.sin(a);
        g += `<path d="M ${ca * r * 0.8 - sa * 50} ${sa * r * 0.8 + ca * 50} Q ${ca * (r + h * 0.6)} ${sa * (r + h * 0.6)} ${ca * (r + h)} ${sa * (r + h)} Q ${ca * (r + h * 0.6)} ${sa * (r + h * 0.6)} ${ca * r * 0.8 + sa * 50} ${sa * r * 0.8 - ca * 50} Z" fill="#ff6a1a" opacity="${0.7 * kk}"/>`; }
      g += `<circle r="${r * (1 + 0.04 * Math.sin(t * 5))}" fill="url(#${id})" opacity="${kk}"/>`;
    } else if (j === "lahar") { // (16 Nov) dataran batu hitam berurat lava dalam perspektif: (0,0) = tengah cakrawala, sampai y = H. seed, cahaya warna, kuat 0-1
      const H = o.H || 900, cw = o.cahaya || "#ff6a24", kk = v(o.kuat, t, d, 1), R = rng(o.seed || 23), id = "lh" + Math.round(x + y);
      g = `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a120a"/><stop offset=".25" stop-color="#1a0a07"/><stop offset="1" stop-color="#0c0605"/></linearGradient></defs><rect x="-1800" y="0" width="3600" height="${H + 400}" fill="url(#${id})"/><rect x="-1800" y="0" width="3600" height="10" fill="${cw}" opacity="${0.5 * kk}"/>`;
      const P = (gx, gz) => { const sy = H * (1 / (1 + 6 * gz) - 1 / 7) / (1 - 1 / 7); return [gx * (60 + 1900 * sy / H), sy]; };
      for (let i = 0; i < 34; i++) { let gx = (R() - 0.5) * 2.4, gz = 0.12 + R() * 0.88, pts = [], wdt = 0; const ph = R() * 6;
        for (let s = 0; s < 6; s++) { const q = P(gx, gz); pts.push(q.join(" ")); wdt = Math.max(wdt, q[1] / H); gx += (R() - 0.5) * 0.25; gz += (R() - 0.5) * 0.12; gz = Math.max(0.1, clamp(gz)); }
        const fl = 0.7 + 0.3 * Math.sin(t * 2.5 + ph);
        g += `<path d="M ${pts.join(" L ")}" stroke="${cw}" stroke-width="${(2 + 6 * wdt) * 2.4}" fill="none" opacity="${0.2 * kk * fl}" stroke-linejoin="round"/><path d="M ${pts.join(" L ")}" stroke="#ffd27a" stroke-width="${1.2 + 2.6 * wdt}" fill="none" opacity="${0.8 * kk * fl}" stroke-linejoin="round"/>`; }
    } else if (j === "bingkai") { // (16 Nov) foto/gambar beredar: bingkai miring berisi bentuk gelap kabur + tanda tanya (bukan gambaran makhluk). rot derajat
      const id = "bk" + Math.round(x + y);
      g = `<g transform="rotate(${o.rot || 0})"><defs><filter id="${id}"><feGaussianBlur stdDeviation="10"/></filter></defs><rect x="-170" y="-220" width="340" height="440" rx="10" fill="#f2ead8" stroke="${INK}" stroke-width="8"/><rect x="-146" y="-196" width="292" height="330" fill="#2a2230"/>
        <path d="M -90 120 Q -110 -40 -10 -80 Q 90 -60 100 120 Z" fill="#0c0a10" filter="url(#${id})"/><text x="0" y="40" text-anchor="middle" font-size="150" font-weight="800" fill="#ffd27a" font-family="sans-serif" data-hias="1">?</text>
        <rect x="-120" y="160" width="240" height="18" rx="9" fill="#cfc6b4"/></g>`;
    } else if (j === "cahaya") { // berkas cahaya turun dari atas
      g = `<defs><linearGradient id="cb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8fbff" stop-opacity=".0"/><stop offset=".4" stop-color="#e8fbff" stop-opacity=".35"/><stop offset="1" stop-color="#bfefff" stop-opacity=".05"/></linearGradient></defs><path d="M -90 -1400 L 90 -1400 L 260 0 L -260 0 Z" fill="url(#cb)"/>`;
    }
    return `<g data-j="${j}" opacity="${op}" transform="translate(${x} ${y}) rotate(${miring} 0 -62) scale(${sc})"${o.kabur ? ` filter="url(#kb${o.kabur === true ? 8 : o.kabur})"` : ""}>${g}</g>`;
  }

  // ---- TITIK KAIT (27 Nov): benda/ruang menyediakan dudukan, pegangan, pijakan, dan sudut pandang tokoh.
  // Koordinat lokal benda menghadap kanan (sebelum translate/scale benda). Boneka {kait: id benda | "jok_depan" | "jok_belakang"}
  // ditempelkan: pinggul ke dudukan, kaki ke pijakan, tangan ke pegangan (IK dua tulang), sudut tokoh mengikuti benda.
  const KAIT = {
    motor: { sudut: "samping", duduk: [-36, -250], pegang: [[118, -334], [110, -330]], pijak: [[44, -108], [56, -108]], skala: 0.85 },
    kursi: { sudut: "depan", duduk: [0, -125], skala: 1 },
    sofa: { sudut: "depan", duduk: [0, -125], skala: 1 },
    kasur: { sudut: "depan", duduk: [0, -130], skala: 1 },
  };
  const JOK_MOBIL = { jok_belakang: 260, jok_depan: 720 }; // ruang "mobil": x kursi (tampak samping, menghadap kanan)
  function kaitDunia(S, b, tl, d) {
    const kid = b.kait != null ? b.kait : b.kendaraan_id;
    if (kid == null) return null;
    const R = S.ruang && (typeof S.ruang === "string" ? { jenis: S.ruang } : S.ruang);
    if (R && R.jenis === "mobil" && JOK_MOBIL[kid] != null) {
      const jx = JOK_MOBIL[kid], st = (S.benda || []).find((o) => o.jenis === "setir");
      const pegang = kid === "jok_depan" && st ? [[v(st.x, tl, d, 0) - 10, v(st.y, tl, d, 0) - 60], [v(st.x, tl, d, 0) + 6, v(st.y, tl, d, 0) + 40]] : null;
      return { sudut: "samping", arah: 1, skala: 1, duduk: [jx + 10, 1402], pijak: [[jx + 128, 1556], [jx + 142, 1556]], pegang };
    }
    const o = (S.benda || []).find((q) => q.id != null && String(q.id) === String(kid));
    const K = o && KAIT[o.jenis];
    if (!K) return null;
    const ox = v(o.x, tl, d, 540), oy = v(o.y, tl, d, 1500), os = v(o.s, tl, d, 1), ar = o.arah === -1 ? -1 : 1;
    const W = (p) => [ox + ar * p[0] * os, oy + p[1] * os];
    return { sudut: K.sudut, arah: ar, skala: os * K.skala, duduk: W(K.duduk), pijak: K.pijak && K.pijak.map(W), pegang: K.pegang && K.pegang.map(W) };
  }
  // IK dua tulang: sendi tengah dari pangkal A ke sasaran P (panjang l1, l2); atas=true pilih sendi yang lebih tinggi (lutut duduk)
  function ik2(A, P, l1, l2, atas) {
    const dx = P[0] - A[0], dy = P[1] - A[1], D = Math.min(l1 + l2 - 0.5, Math.max(Math.abs(l1 - l2) + 0.5, Math.hypot(dx, dy)));
    const b0 = Math.atan2(dy, dx), a = Math.acos(clamp((l1 * l1 + D * D - l2 * l2) / (2 * l1 * D), -1, 1));
    const J1 = [A[0] + Math.cos(b0 + a) * l1, A[1] + Math.sin(b0 + a) * l1], J2 = [A[0] + Math.cos(b0 - a) * l1, A[1] + Math.sin(b0 - a) * l1];
    const J = (J1[1] < J2[1]) === !!atas ? J1 : J2, E = [A[0] + Math.cos(b0) * D, A[1] + Math.sin(b0) * D];
    return [J, E];
  }

  // ---- RANGKA BERSENDI (6 Nov): boneka.pose = nama | {sendi...} | [[t, nama|{...}], ...] (relatif shot; transisi `lama` 0,45 dtk)
  // sendi: turun (pinggul turun, px), badan (condong, derajat), kepala (miring), la/ra = [lengan atas, lengan bawah] sudut dari arah bawah (+ = keluar/naik ke samping),
  // lk/rk = [paha, betis] (+ = keluar), pp/pk = panjang paha/betis (0-1; paha pendek = menghadap kamera saat duduk), guling (rebah, derajat), depan (tangan di depan wajah),
  // pegang (hp|buku|gelas di tangan kanan), lambai (0-1). Pose bebas: tulis sendi langsung, atau {dari:"duduk", ra:[..]}.
  const POSE = {
    berdiri: { turun: 0, badan: 0, kepala: 0, la: [8, 4], ra: [8, 4], lk: [0, 0], rk: [0, 0], pp: 1, pk: 1, pp_ka: 1, pp_ki: 1, pk_ka: 1, pk_ki: 1, geser: 0, toleh: 0, angguk: 0, guling: 0, depan: 0, lambai: 0 },
    duduk: { turun: 70, pp: 0.34, lk: [40, -6], rk: [40, -6], la: [14, -34], ra: [14, -34] },
    // Pengendara duduk stabil, lutut menekuk dan kedua tangan menjangkau setang.
    mengendarai_motor: { turun: 70, pp: 0.3, lk: [18, 34], rk: [18, 34], la: [88, 88], ra: [88, 88], badan: -3 },
    duduk_samping: { turun: 70, badan: 4 }, // dipakai tokoh berkait tampak samping: kaki/tangan diatur titik kait
    // Penolong merendahkan pusat tubuh dan menjulurkan kedua lengan ke arah korban.
    menolong: { turun: 70, badan: 22, kepala: 8, la: [15, 20], ra: [88, 35], depan: 1 },
    peluk_lutut: { turun: 70, pp: 0.3, lk: [8, 2], rk: [8, 2], la: [-4, -22], ra: [-4, -22], badan: 0 },
    tutup_wajah: { la: [136, -118], ra: [136, -118], depan: 1 },
    duduk_tutup_wajah: { turun: 70, pp: 0.3, lk: [12, 3], rk: [12, 3], la: [136, -118], ra: [136, -118], depan: 1 },
    pegang_hp: { la: [14, -132], ra: [14, -150], pegang: "hp" },
    duduk_hp: { turun: 70, pp: 0.3, lk: [12, 3], rk: [12, 3], la: [14, -132], ra: [14, -150], pegang: "hp" },
    telepon: { ra: [140, -175], la: [8, 4], pegang: "hp" },
    lambai: { ra: [92, 150], lambai: 1, depan: 1 },
    tangan_dada: { ra: [10, -160] },
    doa: { la: [24, -150], ra: [24, -150] },
    tunjuk: { ra: [88, 92] },
    berkacak: { la: [45, -45], ra: [45, -45] },
    tepuk: { ra: [108, 96] },
    kaget: { la: [42, 70], ra: [42, 70], badan: 0 },
    rebahan: { guling: -90 },
    rebahan_hp: { guling: -90, la: [168, -170], ra: [168, -170], pegang: "hp", depan: 1 },
    // gestur bicara (13 Nov, tokoh hidup): dipakai lewat pose kunci waktu; sisi kanan tokoh = ra, kiri = la
    jelaskan: { ra: [42, 112] }, jelaskan_kiri: { la: [42, 112] }, buka2: { la: [46, 116], ra: [46, 116] },
    angkat_bahu: { la: [34, 128], ra: [34, 128], kepala: 7 },
    tunjuk_atas: { ra: [118, 176], depan: 1 }, tunjuk_kiri: { la: [88, 92] }, tunjuk_bawah: { ra: [30, 20] },
    stop: { ra: [84, 172], depan: 1 }, stop2: { la: [84, 172], ra: [84, 172], depan: 1 },
    dua_naik: { la: [128, 172], ra: [128, 172] }, kepal: { ra: [118, 168], badan: -3 },
    silang: { la: [20, -100], ra: [20, -100], depan: 1 }, pinggang1: { la: [45, -45] },
    tepuk_dahi: { ra: [150, -165], depan: 1, kepala: -6 }, garuk_kepala: { ra: [150, -178], depan: 1, kepala: 8, lambai: 0.35 },
    condong: { badan: 7, la: [14, 10], ra: [14, 10] }, mundur: { badan: -7, la: [26, 40], ra: [26, 40] },
    lemas: { badan: 4, kepala: 10, la: [4, 2], ra: [4, 2] },
  };
  // ---- TOKOH HIDUP (13 Nov 2026): cerita.hidup:true (atau boneka.hidup) -> pose loncat + tahan, wajah berganti, lip-sync vokal, idle, reaksi ----
  const balik = (u, c = 2.0) => { u = clamp(u); const q = u - 1; return 1 + (c + 1) * q * q * q + c * q * q; }; // kebablasan lalu mengendap
  const sentak = (u) => { u = clamp(u); return u < 0.18 ? -0.1 * Math.sin((Math.PI * u) / 0.18) : balik((u - 0.18) / 0.82, 1.9); }; // ancang-ancang -> loncat -> endap
  function vs(x, t, bawaan, lama = 0.13) { // kunci [[t,angka]]: nilai pindah cepat tepat di waktu kunci lalu DITAHAN (bukan meluncur pelan)
    if (x == null) return bawaan; if (!Array.isArray(x)) return x; if (!Array.isArray(x[0])) return x[0];
    let cur = x[0][1]; for (let i = 1; i < x.length; i++) { if (t < x[i][0]) break; cur = mix(cur, x[i][1], balik((t - x[i][0]) / lama, 1.3)); }
    return cur;
  }
  const kunciAkhir = (x, t) => { let r = -9; if (Array.isArray(x) && Array.isArray(x[0])) x.forEach(([k], i) => { if (i > 0 && t >= k) r = k; }); return r; };
  // wajah: a = alis [dalam, luar] (+ = turun), ay = tinggi alis, mr = skala mata, pu = skala pupil, kl = kelopak 0-1, lirik [x,y], mu = mulut; L/R menimpa satu sisi (L = kiri layar)
  const WJ = {
    netral: { a: [0, 0], mu: "garis" }, senang: { a: [-3, 1], ay: -5, mu: "senyum_buka", sen: 1 }, lega: { a: [-2, 2], ay: -2, mu: "senyum", sen: 1 },
    nyengir: { a: [-3, 1], ay: -4, mu: "gigi", sen: 1 }, tawa: { a: [-2, 2], ay: -8, mata: "lengkung", mu: "tawa", sen: 1 },
    kaget: { a: [-3, -3], ay: -17, mr: 1.28, pu: 0.55, mu: "o_besar" }, takut: { a: [-10, 7], ay: -9, mr: 1.15, pu: 0.6, mu: "gelombang", sen: -1 },
    bingung: { a: [0, 0], L: { ay: -12 }, mu: "o_kecil" }, ragu: { a: [2, -1], L: { a: [-3, -5], ay: -14 }, R: { a: [7, 0], ay: 3, kl: 0.42 }, mu: "miring" },
    mikir: { a: [0, 0], L: { ay: -12 }, lirik: [9, -7], mu: "miring" }, licik: { a: [7, -5], ay: 1, kl: 0.4, mu: "senyum_miring", sen: 1 },
    sinis: { a: [3, 3], ay: 4, kl: 0.5, mu: "garis" }, kesal: { a: [11, -6], ay: 3, kl: 0.22, mu: "cemberut", sen: -1 },
    marah: { a: [14, -9], ay: 5, pu: 0.85, mu: "geram", sen: -1 }, sedih: { a: [-9, 7], ay: -2, kl: 0.25, lirik: [0, 4], mu: "cemberut", sen: -1 },
    lelah: { a: [-8, 8], kl: 0.55, mu: "o_lelah" }, malu: { a: [-6, 5], ay: -2, lirik: [-6, 6], mu: "senyum_kecil", sen: 1 },
  };
  function mulutH(nm, mx, my, amp, sen, t) {
    const L = (d, w = 5) => `<path d="${d}" fill="none" stroke="${INK}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round"/>`, cs = -3 * sen;
    const lidah = (y, rx = 7, ry = 4) => `<ellipse cx="${mx}" cy="${y}" rx="${rx}" ry="${ry}" fill="#d96a6a"/>`;
    const buka = (w, top, bot, gigi) => { const b2 = bot * amp; return `<path d="M ${mx - w} ${my + cs} Q ${mx} ${my - top} ${mx + w} ${my + cs} Q ${mx} ${my + 2 * b2 - cs} ${mx - w} ${my + cs} Z" fill="${INK}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/>` + (b2 > 9 ? lidah(my + b2 * 0.72, w * 0.5, Math.min(5, b2 * 0.24)) : "") + (gigi ? `<path d="M ${mx - w + 4} ${my + cs + 1} Q ${mx} ${my - top + 3} ${mx + w - 4} ${my + cs + 1} Q ${mx} ${my + Math.min(6, b2 * 0.5)} ${mx - w + 4} ${my + cs + 1} Z" fill="#fff"/>` : ""); };
    switch (nm) {
      case "a": return buka(15, 4, 20, true); case "e": return buka(16, 3, 12, true); case "i": return buka(17, 2, 7.5, true); case "k": return buka(13, 2, 5, false);
      case "f": return buka(13, 2, 6, true);
      case "o": return `<ellipse cx="${mx}" cy="${my + 5}" rx="9.5" ry="${12 * amp}" fill="${INK}"/>` + lidah(my + 5 + 7 * amp, 5, 3);
      case "u": return `<ellipse cx="${mx}" cy="${my + 4}" rx="6" ry="7.5" fill="${INK}"/>`;
      case "m": return L(`M ${mx - 11} ${my + 1 + cs} Q ${mx} ${my + 1 - cs} ${mx + 11} ${my + 1 + cs}`, 6);
      case "senyum": return L(`M ${mx - 16} ${my - 2} Q ${mx} ${my + 14} ${mx + 16} ${my - 2}`);
      case "senyum_kecil": return L(`M ${mx - 9} ${my} Q ${mx} ${my + 9} ${mx + 9} ${my}`);
      case "senyum_miring": return L(`M ${mx - 14} ${my + 5} Q ${mx + 4} ${my + 9} ${mx + 17} ${my - 7}`) + L(`M ${mx + 14} ${my - 11} q 6 3 5 9`, 3);
      case "senyum_buka": return `<path d="M ${mx - 17} ${my - 3} Q ${mx} ${my + 2} ${mx + 17} ${my - 3} Q ${mx + 14} ${my + 19} ${mx} ${my + 20} Q ${mx - 14} ${my + 19} ${mx - 17} ${my - 3} Z" fill="${INK}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/><path d="M ${mx - 13} ${my - 1} Q ${mx} ${my + 3} ${mx + 13} ${my - 1} L ${mx + 11} ${my + 4} Q ${mx} ${my + 7} ${mx - 11} ${my + 4} Z" fill="#fff"/>` + lidah(my + 14, 8, 4);
      case "tawa": return `<path d="M ${mx - 21} ${my - 5} Q ${mx} ${my + 1} ${mx + 21} ${my - 5} Q ${mx + 18} ${my + 27} ${mx} ${my + 28} Q ${mx - 18} ${my + 27} ${mx - 21} ${my - 5} Z" fill="${INK}" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/><path d="M ${mx - 16} ${my - 2} Q ${mx} ${my + 3} ${mx + 16} ${my - 2} L ${mx + 14} ${my + 4} Q ${mx} ${my + 8} ${mx - 14} ${my + 4} Z" fill="#fff"/>` + lidah(my + 20 + Math.sin(t * 22) * 1.5, 10, 5);
      case "gigi": return `<rect x="${mx - 18}" y="${my - 6}" width="36" height="16" rx="7" fill="#fff" stroke="${INK}" stroke-width="4"/><path d="M ${mx - 16} ${my + 2} L ${mx + 16} ${my + 2} M ${mx - 6} ${my - 5} v 14 M ${mx + 6} ${my - 5} v 14" stroke="${INK}" stroke-width="2" opacity=".55"/>`;
      case "cemberut": return L(`M ${mx - 14} ${my + 8} Q ${mx} ${my - 6} ${mx + 14} ${my + 8}`);
      case "geram": return `<path d="M ${mx - 18} ${my + 8} Q ${mx} ${my - 4} ${mx + 18} ${my + 8} L ${mx + 14} ${my + 14} Q ${mx} ${my + 6} ${mx - 14} ${my + 14} Z" fill="${INK}"/><path d="M ${mx - 12} ${my + 6} L ${mx + 12} ${my + 6}" stroke="#fff" stroke-width="4"/>`;
      case "o_besar": return `<ellipse cx="${mx}" cy="${my + 7}" rx="12" ry="17" fill="${INK}"/>` + lidah(my + 16, 6, 4);
      case "o_kecil": return `<ellipse cx="${mx + 6}" cy="${my + 2}" rx="7" ry="9" fill="${INK}"/>`;
      case "miring": return L(`M ${mx - 11} ${my + 5} L ${mx + 12} ${my - 3}`);
      case "gelombang": return L(`M ${mx - 16} ${my + 6} q 8 -12 16 0 q 8 12 16 0`);
      case "o_lelah": return `<ellipse cx="${mx}" cy="${my + 4}" rx="${13 + Math.sin(t * 5) * 3}" ry="${11 + Math.sin(t * 5) * 5}" fill="${INK}"/>` + lidah(my + 10, 7, 4);
      default: return L(`M ${mx - 12} ${my} L ${mx + 12} ${my}`);
    }
  }
  // lip-sync dari teks: boneka.ucap = [[t0, t1, "kata"(, kuat)], ...] (relatif shot). Ejaan Indonesia hampir fonetis: vokal -> bentuk mulut, m/b/p -> tutup.
  function bentukKata(k) {
    const s = String(k).toLowerCase().replace(/[^a-z]/g, ""), L = []; let sela = false;
    for (const c of s) { let f = "aiueo".includes(c) ? c : "mbp".includes(c) ? "m" : "fv".includes(c) ? "f" : c === "w" ? "u" : null;
      if (!f) { sela = true; continue; }
      if (L[L.length - 1] === f) { if (!sela) continue; L.push("k"); } L.push(f); sela = false; }
    return L.length ? L : ["e"];
  }
  function susunUcap(U) {
    const S = []; (U || []).forEach(([a, b2, k, kuat]) => { let L = bentukKata(k); const maks = Math.max(1, Math.floor((b2 - a) / 0.066));
      if (L.length > maks) { const V = L.filter((x) => x !== "m" && x !== "f" && x !== "k"); if (V.length) L = V; }
      if (L.length > maks) L = Array.from({ length: maks }, (_, i) => L[Math.floor((i * L.length) / maks)]);
      const dd = (b2 - a) / L.length; L.forEach((f, i) => S.push([a - 0.04 + i * dd, a - 0.04 + (i + 1) * dd, f, (kuat || 1) * (i === 0 ? 1.1 : 0.92)])); });
    return S;
  }
  function mukaHidup(b, o) { // alis, mata, mulut gaya hidup
    const { wajah, mata, ex, ey, arah, tunduk, t, H, kl } = o, W = WJ[wajah] || WJ.netral, id = b.id || 0; let k = "";
    const cw = b.rambut === "kerudung" || b.wanita === true || /^(wanita|perempuan)$/.test(b.jenis_kelamin || "");
    [-1, 1].forEach((sg) => {
      const Ws = Object.assign({}, W, sg < 0 ? W.L : W.R), a = Ws.a || [0, 0], r = 15 * (Ws.mr || 1), cx = ex + sg * 28, cy = 2 + ey, by = -25 + ey + (Ws.ay || 0) - (r - 15) - 9 * H.pop * 10;
      k += cw ? `<path d="M ${cx - sg * 14} ${by + a[0] + 2} Q ${cx} ${by - 6 + (a[0] + a[1]) / 2} ${cx + sg * 16} ${by + a[1] + 3}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`
        : `<line x1="${cx - sg * 14}" y1="${by + a[0]}" x2="${cx + sg * 14}" y2="${by + a[1]}" stroke="${INK}" stroke-width="11" stroke-linecap="round"/>`;
      if (mata === "tutup" || H.kedip) { k += `<path d="M ${cx - 12} ${cy} q 12 7 24 0" fill="none" stroke="${INK}" stroke-width="5.5" stroke-linecap="round"/>`; return; }
      if (Ws.mata === "lengkung") { k += `<path d="M ${cx - 13} ${cy + 4} Q ${cx} ${cy - 13} ${cx + 13} ${cy + 4}" fill="none" stroke="${INK}" stroke-width="6.5" stroke-linecap="round"/>`; return; }
      const pr = 9 * (Ws.pu || 1), lr = Ws.lirik || [0, 0], kel = Ws.kl || 0, yl = cy - r + 2 * r * kel;
      const px = cx + clamp(arah * 5 + lr[0] + H.lx, -(r - pr - 1), r - pr - 1), py = cy + clamp(lr[1] + H.ly + (mata === "atas" ? -5 : mata === "bawah" ? 5 : 0) + kel * 6, -(r - pr - 1), r - pr - 1);
      k += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="#fff" stroke="${INK}" stroke-width="3.5"/><circle cx="${px}" cy="${py}" r="${pr}" fill="${INK}"/><circle cx="${px + 2.8}" cy="${py - 3.2}" r="${Math.max(1.6, pr * 0.28)}" fill="#fff"/>`;
      if (kel > 0) { const hw = Math.sqrt(Math.max(0, r * r - (yl - cy) * (yl - cy)));
        k += `<clipPath id="ek${id}${sg > 0 ? "r" : "l"}"><circle cx="${cx}" cy="${cy}" r="${r + 1.6}"/></clipPath><rect clip-path="url(#ek${id}${sg > 0 ? "r" : "l"})" x="${cx - r - 3}" y="${cy - r - 3}" width="${2 * r + 6}" height="${yl - cy + r + 3}" fill="${kl}"/><path d="M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}" fill="none" stroke="${INK}" stroke-width="3.5"/><line x1="${cx - hw}" y1="${yl}" x2="${cx + hw}" y2="${yl}" stroke="${INK}" stroke-width="4.5" stroke-linecap="round"/>`; }
    });
    const mx = arah * 18, my = 38 + tunduk * 8, sen = W.sen || 0;
    if (!b._uc) b._uc = susunUcap(b.ucap);
    let bt = null, amp = 1; for (const sgm of b._uc) { if (t >= sgm[0] && t < sgm[1]) { bt = sgm[2]; amp = sgm[3]; break; } }
    if (!bt && (b.bicara || []).some(([a0, a1]) => t >= a0 && t <= a1)) { const R = rng(Math.floor(t * 7.5) * 31 + id); bt = ["a", "e", "o", "m", "a", "i", "u", "e"][Math.floor(R() * 8)]; }
    if (cw && !bt && (wajah === "netral" || wajah === "lega" || wajah === "senang")) // bibir perempuan saat diam
      return k + `<path d="M ${mx - (wajah === "netral" ? 9 : 13)} ${my} Q ${mx} ${my + (wajah === "netral" ? 5 : 11)} ${mx + (wajah === "netral" ? 9 : 13)} ${my}" fill="none" stroke="#7a3a3a" stroke-width="4.5" stroke-linecap="round"/>`;
    return k + mulutH(bt || W.mu, mx, my, amp, sen, t);
  }
  function simbolH(S, t) { // penanda emosi di samping kepala: [[t, "tanya"|"seru"|"urat"|"tetes"|"kejut"]], tampil 0,9 dtk
    let s = ""; (S || []).forEach(([ts, jn, lama = 0.9]) => { const q = t - ts; if (q < 0 || q > lama) return;
      const sc = balik(q / 0.13, 2.4) * clamp((lama - q) / 0.12), T = `transform="translate(78 -92) scale(${sc}) rotate(12)"`, F = `font-family="DejaVu Sans, Arial, sans-serif" font-weight="900" text-anchor="middle" stroke="${INK}" stroke-width="9" paint-order="stroke" stroke-linejoin="round"`;
      if (jn === "tanya") s += `<text ${T} ${F} font-size="84" fill="#ffd93a" y="26">?</text>`;
      else if (jn === "seru") s += `<text ${T} ${F} font-size="84" fill="#ff5a4a" y="26">!</text>`;
      else if (jn === "urat") s += `<g ${T}><path d="M -20 -6 Q -6 -6 -6 -20 M 6 -20 Q 6 -6 20 -6 M 20 6 Q 6 6 6 20 M -6 20 Q -6 6 -20 6" fill="none" stroke="#e03131" stroke-width="9" stroke-linecap="round"/></g>`;
      else if (jn === "tetes") s += `<path transform="translate(-86 ${-46 + q * 46}) scale(${sc})" d="M 0 -22 Q 16 4 0 14 Q -16 4 0 -22 Z" fill="#9fdcff" stroke="${INK}" stroke-width="4"/>`;
      else if (jn === "kejut") s += `<g ${T}><path d="M -26 10 L -8 2 M -6 -30 L 0 -10 M 28 -20 L 12 -6" stroke="${INK}" stroke-width="8" stroke-linecap="round"/></g>`; });
    return s;
  }
  // Evaluator gerak karakter tunggal. Python hanya mengirim nama aksi dan jadwal;
  // seluruh sudut rangka dihitung di sini agar tidak ada solver sendi kedua.
  function poseGerak(nama, t) {
    const f = 2 * Math.PI * t, s = Math.sin(f), c = Math.cos(f);
    if (nama === "tergelincir") {
      const u = clamp(t / 0.85);
      return { guling: -78 * u, turun: 8 * Math.sin(Math.PI * u), badan: 10 * u,
        pp: 1 - 0.18 * u, ra: [28 + 32 * u, 42 + 48 * u], la: [28 + 32 * u, -42 - 48 * u] };
    }
    if (nama === "bangkit") {
      const u = clamp(t / 1.0);
      return { guling: -78 * (1 - u), turun: 70 * (1 - u), pp: 0.3 + 0.7 * u,
        lk: [12 * (1 - u), 3 * (1 - u)], rk: [12 * (1 - u), 3 * (1 - u)],
        ra: [145 * (1 - u) + 8, 165 * (1 - u) + 4],
        la: [145 * (1 - u) + 8, -165 * (1 - u) - 4] };
    }
    if (nama === "menenangkan") {
      return { badan: -4, kepala: 5, ra: [74, 94], la: [18, 22], depan: 1 };
    }
    if (nama === "jalan") { const ka = Math.max(0, s), ki = Math.max(0, -s);
      return { turun: -4 * Math.abs(c), badan: 1.5 * s, kepala: -1.5 * s,
        pp_ka: 1 - .3 * ka, pp_ki: 1 - .3 * ki, rk: [4 + 3 * ka, -18 * ka + 2], lk: [4 + 3 * ki, -18 * ki + 2],
        ra: [10 + 8 * ki, 6 + 30 * ki], la: [10 + 8 * ka, 6 + 30 * ka] };
    }
    if (nama === "lari") { const ka = Math.max(0, s), ki = Math.max(0, -s);
      return { turun: -10 * Math.abs(c) - 4, badan: 3 * s, kepala: -2 * s,
        pp_ka: 1 - .5 * ka, pp_ki: 1 - .5 * ki, rk: [6 + 6 * ka, -40 * ka + 4], lk: [6 + 6 * ki, -40 * ki + 4],
        ra: [22 + 20 * ki, 70 + 40 * ki], la: [22 + 20 * ka, 70 + 40 * ka] };
    }
    if (nama === "joget") return { geser: 12 * s, badan: -6 * s, kepala: 6 * Math.sin(f + .6), turun: -6 * Math.abs(s),
      ra: [140 + 25 * s, 165 + 20 * Math.sin(f + 1)], la: [140 - 25 * s, 165 - 20 * Math.sin(f + 1)],
      rk: [8 + 4 * s, -6 * Math.max(0, s)], lk: [8 - 4 * s, -6 * Math.max(0, -s)] };
    if (nama === "lompat") { const u = ((t % 1.2) + 1.2) % 1.2 / 1.2;
      if (u < .2) { const k = Math.sin(Math.PI * u / .4); return { turun: 22 * k, pp: 1 - .25 * k, rk: [8, -10 * k], lk: [8, -10 * k] }; }
      if (u < .75) { const k = (u - .2) / .55; return { turun: -120 * Math.sin(Math.PI * k), pp: .75, rk: [10, -25], lk: [10, -25], ra: [150, 170], la: [150, 170] }; }
      const k = 1 - (u - .75) / .25; return { turun: 18 * k, pp: 1 - .2 * k, rk: [8, -8 * k], lk: [8, -8 * k] };
    }
    if (nama === "melambai") return { ra: [150, 160 + 25 * Math.sin(t * 2 * Math.PI * 1.6)], kepala: 4 };
    if (nama === "menggeleng") return { toleh: .8 * Math.sin(t * 2 * Math.PI * 1.6) };
    if (nama === "mengangguk") return { angguk: .8 * Math.max(0, Math.sin(t * 2 * Math.PI * 1.2)) };
    if (nama === "tertawa") return { turun: -3 * Math.abs(Math.sin(t * 7)), badan: 2 * Math.sin(t * 7), kepala: -8, ra: [8, 4], la: [8, 4] };
    if (nama === "palu") { const u = (Math.sin(t * 2 * Math.PI * 1.4) + 1) / 2;
      return { ra: [40 + 85 * u, 60 + 115 * u], badan: -3 + 4 * u, turun: 2 * (1 - u), la: [20, -30], pegang: "palu" }; }
    if (nama === "gali") return { ra: [40, 80], la: [20, 40], pegang: "beliung" };
    if (nama === "ulurkan") return { ra: [82, 24], kepala: 1 };
    if (nama === "angkat") return { ra: [165, 178] };
    if (nama === "tutup") return { ra: [-36, -32], kepala: -4 };
    if (nama === "tutup_telinga") return { ra: [-4, -50], la: [-4, -50] };
    if (nama === "berdoa") return { ra: [-14, 40], la: [-14, 40], kepala: -6, angguk: .4 };
    if (nama === "menengadah") return { ra: [26, -46], la: [26, -46], kepala: -10, angguk: -.6 };
    if (nama === "pinggang") return { ra: [-6, 96], la: [-6, 96] };
    if (nama === "dagu") return { ra: [-30, -18], la: [-50, 52], kepala: 6 };
    if (nama === "kepala") return { ra: [-10, -78], kepala: -6 };
    return null;
  }
  function isiPose(p, t = 0) {
    const q = typeof p === "string" ? (poseGerak(p, t) || POSE[p] || {})
      : p.dari || p.pakai ? Object.assign({}, POSE[p.dari], p, POSE[p.pakai]) : p;
    return Object.assign({}, POSE.berdiri, q);
  } // pose aksi dievaluasi oleh renderer JS, bukan dikirim sebagai sudut dari Python
  function paduPose(a, b, f) {
    const r = {}; for (const k in b) { const A = a[k], B = b[k];
      r[k] = typeof B === "number" ? mix(typeof A === "number" ? A : B, B, f) : Array.isArray(B) ? B.map((x, i) => mix(A ? A[i] : x, x, f)) : f > 0.5 ? B : A; }
    return r;
  }
  function poseKini(b, t, hd) { // hd (tokoh hidup): pindah pose 0,2 dtk dengan ancang-ancang + kebablasan, lalu ditahan
    let kf = b.pose == null ? "berdiri" : b.pose; if (!Array.isArray(kf) || !Array.isArray(kf[0])) kf = [[0, kf]];
    let cur = isiPose(kf[0][1], t - kf[0][0]), tk0 = -9, aksiKini = kf[0][1];
    for (let i = 1; i < kf.length; i++) { const [tk, pk] = kf[i]; if (t < tk) break; aksiKini = pk; const L = (pk && pk.lama) || (hd && !b._gabungan ? 0.2 : 0.45); const f = hd && !b._gabungan ? sentak((t - tk) / L) : halus((t - tk) / L); cur = paduPose(cur, isiPose(pk, t - tk), f); tk0 = tk; }
    cur._tk = tk0; cur._aksi = typeof aksiKini === "string" ? aksiKini : null; return cur;
  }
  // gambar badan bersendi (kaki di tanah, badan + lengan dalam bingkai T). Mengembalikan {g, depan, T, kepala, guling}
  // detail baju (7 Nov, akun komedi): kaus|koko|gamis|jaket{logo,aksen}|kemeja{motif batik}|daster|hoodie|blazer + handuk leher; gm = gemuk 0-1
  function bajuDetail(P, BD, n, gm) {
    const G = (f) => warna(BD, "#000000", f), W = 70 + 30 * gm, j = P.jenis;
    let s = "";
    if (j === "kaus") s += `<path d="M -26 ${-393 + n} Q 0 ${-360 + n} 26 ${-393 + n}" fill="none" stroke="${G(0.3)}" stroke-width="6"/>`;
    else if (j === "jaket") {
      const A = P.aksen || "#ffc83d";
      s += `<rect x="${-W}" y="${-322 + n}" width="${2 * W}" height="24" fill="${A}"/><rect x="${-W}" y="${-214 + n}" width="${2 * W}" height="18" rx="6" fill="${G(0.25)}"/>`;
      s += `<line x1="0" y1="${-392 + n}" x2="0" y2="${-196 + n}" stroke="${G(0.4)}" stroke-width="5"/><path d="M -44 ${-400 + n} L 0 ${-376 + n} L 44 ${-400 + n} L 36 ${-414 + n} L 0 ${-394 + n} L -36 ${-414 + n} Z" fill="${G(0.15)}" stroke="${G(0.45)}" stroke-width="3"/>`;
      if (P.logo) s += `<rect x="${-W + 16}" y="${-382 + n}" width="64" height="34" rx="9" fill="${A}" stroke="${G(0.4)}" stroke-width="2"/><text x="${-W + 48}" y="${-357 + n}" font-size="22" font-weight="900" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" fill="${BD}">${esc(P.logo)}</text>`;
    } else if (j === "kemeja") {
      if (P.motif === "batik") for (let r = 0; r < 4; r++) for (let c = -1; c <= 1; c++) { const cx = c * 44 + (r % 2) * 22 - 11, cy = -360 + r * 46 + n; s += `<path d="M ${cx - 12} ${cy} q 6 -14 12 0 q 6 14 12 0" stroke="${P.motif_warna || G(0.45)}" stroke-width="4" fill="none"/><circle cx="${cx}" cy="${cy + 16}" r="3.5" fill="${P.motif_warna || G(0.45)}"/>`; }
      s += `<path d="M -36 ${-404 + n} L 0 ${-372 + n} L -10 ${-352 + n} L -44 ${-390 + n} Z M 36 ${-404 + n} L 0 ${-372 + n} L 10 ${-352 + n} L 44 ${-390 + n} Z" fill="${warna(BD, "#ffffff", 0.25)}" stroke="${G(0.45)}" stroke-width="3"/><line x1="0" y1="${-372 + n}" x2="0" y2="${-190 + n}" stroke="${G(0.3)}" stroke-width="3"/>`;
      for (let i = 0; i < 4; i++) s += `<circle cx="0" cy="${-350 + i * 40 + n}" r="4.5" fill="${G(0.5)}"/>`;
    } else if (j === "daster") {
      for (let r = 0; r < 4; r++) for (let c = -1; c <= 1; c++) { const cx = c * 42 + (r % 2) * 20 - 10, cy = -368 + r * 48 + n; s += [0, 72, 144, 216, 288].map((a) => `<circle cx="${cx + Math.cos(a * Math.PI / 180) * 8}" cy="${cy + Math.sin(a * Math.PI / 180) * 8}" r="6" fill="${P.bunga || "#ffffff"}" opacity=".85"/>`).join("") + `<circle cx="${cx}" cy="${cy}" r="4" fill="#f2c14e"/>`; }
      s += `<path d="M -30 ${-398 + n} Q 0 ${-362 + n} 30 ${-398 + n}" fill="none" stroke="${G(0.3)}" stroke-width="6"/>`;
    } else if (j === "hoodie") {
      s += `<path d="M -66 ${-396 + n} Q 0 ${-446 + n} 66 ${-396 + n} Q 40 ${-372 + n} 0 ${-376 + n} Q -40 ${-372 + n} -66 ${-396 + n} Z" fill="${G(0.2)}" stroke="${G(0.45)}" stroke-width="3"/>`;
      s += `<path d="M -14 ${-378 + n} L -18 ${-318 + n} M 14 ${-378 + n} L 18 ${-318 + n}" stroke="#f4f1ea" stroke-width="4" stroke-linecap="round"/><path d="M -46 ${-262 + n} L 46 ${-262 + n} L 56 ${-206 + n} L -56 ${-206 + n} Z" fill="${G(0.12)}" stroke="${G(0.4)}" stroke-width="3"/>`;
    } else if (j === "blazer") {
      s += `<path d="M -30 ${-398 + n} L 30 ${-398 + n} L 0 ${-300 + n} Z" fill="${P.dalam || "#f4f1ea"}"/><path d="M -30 ${-400 + n} L -6 ${-300 + n} L -40 ${-330 + n} L -50 ${-392 + n} Z M 30 ${-400 + n} L 6 ${-300 + n} L 40 ${-330 + n} L 50 ${-392 + n} Z" fill="${G(0.15)}" stroke="${G(0.45)}" stroke-width="3"/><circle cx="0" cy="${-262 + n}" r="6" fill="${G(0.5)}"/>`;
    } else if (j === "jubah") { // jubah Arab (thobe): kerah bulat kecil + celah dada, tanpa kancing
      s += `<path d="M -24 ${-404 + n} Q 0 ${-388 + n} 24 ${-404 + n}" fill="none" stroke="${G(0.3)}" stroke-width="5"/><line x1="0" y1="${-392 + n}" x2="0" y2="${-330 + n}" stroke="${G(0.3)}" stroke-width="4"/>`;
    } else {
      s += `<rect x="-27" y="${-404 + n}" width="54" height="20" rx="7" fill="${BD}" stroke="${G(0.35)}" stroke-width="4"/><line x1="0" y1="${-384 + n}" x2="0" y2="${(j === "gamis" ? -240 : -260) + n}" stroke="${G(0.25)}" stroke-width="4"/>`;
      for (let i = 0; i < 4; i++) s += `<circle cx="0" cy="${-370 + i * 30 + n}" r="5" fill="${G(0.45)}"/>`;
      if (P.motif === "bordir") for (let i = 0; i < 4; i++) s += `<path d="M -16 ${-372 + i * 30 + n} q 6 -8 12 0 M 4 ${-372 + i * 30 + n} q 6 -8 12 0" stroke="${P.bordir || "#c9a24a"}" stroke-width="3" fill="none"/>`;
    }
    if (P.handuk) { const H = P.handuk; s += `<path d="M -56 ${-398 + n} Q 0 ${-366 + n} 56 ${-398 + n}" stroke="${H}" stroke-width="24" fill="none" stroke-linecap="round"/><rect x="28" y="${-402 + n}" width="30" height="104" rx="8" fill="${H}" stroke="${warna(H, "#000000", 0.3)}" stroke-width="3" transform="rotate(-6 43 ${-400 + n})"/><path d="M 28 ${-310 + n} l 30 -3" stroke="#e03131" stroke-width="5" transform="rotate(-6 43 ${-400 + n})"/>`; }
    return s;
  }

  function keT(p, J) { // titik lokal boneka -> bingkai lengan (kebalikan T = translate(0 turun) rotate(badan 0 -200))
    const a = -(J.badan || 0) * Math.PI / 180, x0 = p[0], y0 = p[1] - J.turun + 200;
    return [x0 * Math.cos(a) - y0 * Math.sin(a), x0 * Math.sin(a) + y0 * Math.cos(a) - 200];
  }
  function rangka(J, o) {
    const { P, BD, WC, KLB, nafas, ayun, bawahP, t, aksi, id, offset } = o, GM = o.gm || 0, R = Math.PI / 180, hy0 = -200 + J.turun;
    const pakaiP = !!P, wKaki = !P ? 44 : bawahP === "celana" ? 46 : bawahP === "gamis" ? 72 : 64, wnK = !P ? BADAN : bawahP === "gamis" ? BD : WC;
    const titik = [];
    let kaki = "", geserY = 0; // geserY: badan ikut turun/naik bila kaki samping digeser ke tanah
    if (o.profilMotor && o.kait) {
      // Kaki tampak samping menempel di pijakan benda: paha sepanjang dudukan, lutut menekuk (IK).
      const pj = o.kait.pijak || [[150, hy0 + 150], [162, hy0 + 150]];
      [[-1, pj[0]], [1, pj[1] || pj[0]]].forEach(([sg, F0]) => {
        const H = [sg < 0 ? -6 : 10, hy0], [K, F] = ik2(H, F0, 104, 100, true);
        titik.push([H, K, F]);
        kaki += `<polyline points="${H} ${K} ${F}" fill="none" stroke="${sg < 0 ? warna(wnK, "#000000", 0.24) : wnK}" stroke-width="${wKaki}" stroke-linecap="round" stroke-linejoin="round"/>`;
        kaki += `<path d="M ${F[0] - 22} ${F[1] - 8} q 30 -12 62 4 l 10 14 q -36 10 -72 -2 Z" fill="#2a2024"/>`;
      });
    } else if (o.profilMotor) {
      // (27 Nov) Kaki tampak samping umum. Pose ditulis untuk tampak depan; dipetakan ke bidang samping:
      // paha yang memendek (pp) di tampak depan = paha terangkat ke depan (acos pp); kaki lawan mengayun ke belakang;
      // betis menekuk ke belakang menurut pk dan tekukan lutut (s[1] negatif). Sudut + = ke depan (arah hadap).
      const angkat = (q) => (1 - clamp(q == null ? 1 : q, 0, 1)) * 120 * R; // linear: acos curam di dekat 1 membuat langkah tersentak
      const ppKi = Math.min(J.pp, J.pp_ki == null ? 1 : J.pp_ki), ppKa = Math.min(J.pp, J.pp_ka == null ? 1 : J.pp_ka);
      [[-1, ppKi, ppKa, J.lk, J.pk_ki == null ? J.pk : J.pk_ki], [1, ppKa, ppKi, J.rk, J.pk_ka == null ? J.pk : J.pk_ka]].forEach(([sg, pp, ppLawan, s2, pk]) => {
        const sw = (sg < 0 ? ayun : -ayun) * R;
        const p1 = angkat(pp) - 0.5 * Math.max(0, angkat(ppLawan) - angkat(pp)) + sw, p2 = p1 - (pk < 1 ? angkat(pk) : 0) - Math.max(0, -(s2 ? s2[1] : 0)) * 1.4 * R;
        const tekuk = pp <= 0.6 && J.turun >= 50 ? Math.min(p2, 0.12) : p2; // duduk: betis turun tegak
        const H = [sg < 0 ? -6 : 10, hy0], K = [H[0] + Math.sin(p1) * 100, H[1] + Math.cos(p1) * 100], F = [K[0] + Math.sin(tekuk) * 100, K[1] + Math.cos(tekuk) * 100];
        titik.push([H, K, F]);
      });
      // berdiri/jalan: kaki yang menapak tepat di tanah (langkah miring memendekkan jangkauan vertikal)
      const tapak = J.turun < 50 && aksi !== "lompat" ? -Math.max(...titik.map(([, , F]) => F[1])) : 0;
      if (tapak) { titik.forEach((tk) => tk.forEach((q) => { q[1] += tapak; })); geserY = tapak; }
      titik.forEach(([H, K, F], i) => { const sg = i ? 1 : -1;
        kaki += `<polyline points="${H} ${K} ${F}" fill="none" stroke="${sg < 0 ? warna(wnK, "#000000", 0.24) : wnK}" stroke-width="${wKaki}" stroke-linecap="round" stroke-linejoin="round"/>`;
        kaki += `<path d="M ${F[0] - 24} ${F[1] - 8} q 30 -12 62 4 l 10 14 q -36 10 -72 -2 Z" fill="#2a2024"/>`;
      });
      if (P && bawahP !== "celana") { // gamis/sarung tampak samping: kain dari pinggul menutup kaki
        const xs = titik.flatMap(([, K, F]) => [K[0], F[0]]), yb = Math.max(...titik.map(([, , F]) => F[1])) - (bawahP === "gamis" ? 6 : 30);
        const top = hy0 + geserY - (bawahP === "gamis" ? 160 : 25);
        kaki += `<path d="M -40 ${top + nafas} L 50 ${top + nafas} L ${Math.max(...xs) + 26} ${yb} Q ${(Math.max(...xs) + Math.min(...xs)) / 2} ${yb + 10} ${Math.min(...xs) - 26} ${yb} Z" fill="${wnK}" stroke="${warna(wnK, "#000000", 0.25)}" stroke-width="3"/>`;
      }
    } else {
      [-1, 1].forEach((sg) => {
        const s = sg < 0 ? J.lk : J.rk, sw = sg < 0 ? ayun : -ayun;
        const a1 = (sg * s[0] + sw) * R, a2 = (sg * s[1] + sw) * R;
        const pp = sg < 0 ? (J.pp_ki == null ? J.pp : J.pp_ki) : (J.pp_ka == null ? J.pp : J.pp_ka), pk = sg < 0 ? (J.pk_ki == null ? J.pk : J.pk_ki) : (J.pk_ka == null ? J.pk : J.pk_ka); const H = [sg * 26, hy0], K = [H[0] + Math.sin(a1) * 100 * pp, H[1] + Math.cos(a1) * 100 * pp], F = [K[0] + Math.sin(a2) * 100 * pk, K[1] + Math.cos(a2) * 100 * pk];
        titik.push([H, K, F]);
        const dudukDepan = J.turun >= 50 && J.pp <= 0.6 && !J.guling && (!P || bawahP === "celana");
        kaki += `<polyline points="${H} ${K} ${F}" fill="none" stroke="${dudukDepan ? warna(wnK, "#000000", 0.12) : wnK}" stroke-width="${wKaki}" stroke-linecap="round" stroke-linejoin="round"/>`;
        if (pakaiP) kaki += `<ellipse cx="${F[0] + sg * 4}" cy="${F[1] - 6}" rx="30" ry="14" fill="#2a2024"/>`;
      });
    }
    if (!o.profilMotor && J.turun >= 50 && J.pp <= 0.6 && !J.guling && titik.length === 2 && (!P || bawahP === "celana")) {
      // Duduk tampak depan (27 Nov): paha menghadap kamera terbaca sebagai pangkuan + lutut, bukan kaki lurus berdiri.
      const [[, KL], [, KR]] = titik, w2 = wKaki / 2;
      const atas = warna(wnK, "#ffffff", 0.2), yb = Math.max(KL[1], KR[1]);
      kaki += `<ellipse cx="0" cy="${yb + 20}" rx="${Math.abs(KR[0] - KL[0]) / 2 + w2 + 8}" ry="16" fill="#000" opacity=".22"/>`; // bayang di bawah pangkuan
      kaki += `<path d="M -78 ${hy0 - 20} L 78 ${hy0 - 20} L ${KR[0] + w2 + 6} ${yb} Q ${KR[0] + w2 + 6} ${yb + 18} ${KR[0]} ${yb + 18} L ${KL[0]} ${yb + 18} Q ${KL[0] - w2 - 6} ${yb + 18} ${KL[0] - w2 - 6} ${yb} Z" fill="${atas}" stroke="${warna(wnK, "#000000", 0.3)}" stroke-width="4" stroke-linejoin="round"/>`;
      kaki += `<path d="M 0 ${hy0 - 4} L 0 ${yb + 14}" stroke="${warna(wnK, "#000000", 0.25)}" stroke-width="4"/>`; // celah antar paha
    }
    if (P && bawahP !== "celana" && !o.profilMotor) { // kain sarung/gamis mengikuti paha & betis
      const [[, KL, FL], [, KR, FR]] = titik, top = hy0 - (bawahP === "gamis" ? 160 : 25), panjang = bawahP === "gamis" ? 1 : 0.85;
      const bl = [mix(KL[0], FL[0], panjang) - 32, mix(KL[1], FL[1], panjang) - 8], br = [mix(KR[0], FR[0], panjang) + 32, mix(KR[1], FR[1], panjang) - 8];
      kaki += `<path d="M -74 ${top + nafas} L 74 ${top + nafas} L ${KR[0] + 40} ${KR[1]} L ${br} Q 0 ${Math.max(bl[1], br[1]) + 10} ${bl} L ${KL[0] - 40} ${KL[1]} Z" fill="${wnK}" stroke="${warna(wnK, "#000000", 0.25)}" stroke-width="3"/>`;
      if (bawahP === "sarung" && P.motif !== "polos") for (let i = 1; i < 4; i++) { const yy = mix(top, Math.max(bl[1], br[1]), i / 4); kaki += `<line x1="${mix(-74, bl[0], i / 4)}" y1="${yy}" x2="${mix(74, br[0], i / 4)}" y2="${yy}" stroke="${warna(wnK, "#ffffff", 0.35)}" stroke-width="7" opacity=".45"/>`; }
    }
    // Torso samping: dada dan pinggul mengarah ke depan perjalanan.
    let bdn = o.profilMotor
      ? `<path d="M -30 ${-396 + nafas} Q 22 ${-420 + nafas} 52 ${-382 + nafas} L 68 ${-270 + nafas} Q 56 ${-222 + nafas} 8 ${-206 + nafas} L -28 ${-244 + nafas} Z" fill="${BD}" stroke="${warna(BD, "#000000", 0.18)}" stroke-width="4"/>`
      : `<rect x="${-70 - 30 * GM}" y="${-395 + nafas}" width="${140 + 60 * GM}" height="215" rx="${58 + 20 * GM}" fill="${BD}"/>`;
    if (P && !o.profilMotor) bdn += bajuDetail(P, BD, nafas, GM);
    if (P && P.bisht) { // bisht: jubah luar terbuka berlis emas, dari bahu sampai betis
      const BS = P.bisht, lis = "#c9a24a", yb = hy0 + geserY + 150;
      bdn += o.profilMotor
        ? `<path d="M -26 ${-400 + nafas} Q -62 ${-300 + nafas} -70 ${yb} L -14 ${yb} Q -6 ${-250 + nafas} 14 ${-398 + nafas} Z" fill="${BS}" stroke="${INK}" stroke-width="4"/><path d="M 14 ${-398 + nafas} Q -6 ${-250 + nafas} -14 ${yb}" fill="none" stroke="${lis}" stroke-width="6"/>`
        : [-1, 1].map((sg) => `<path d="M ${sg * 30} ${-404 + nafas} L ${sg * (78 + 30 * GM)} ${-392 + nafas} L ${sg * (104 + 30 * GM)} ${yb} L ${sg * 40} ${yb} Z" fill="${BS}" stroke="${INK}" stroke-width="4"/><path d="M ${sg * 30} ${-404 + nafas} L ${sg * 40} ${yb}" stroke="${lis}" stroke-width="6"/>`).join("");
    }
    // lengan
    const lengan = (sg, s) => {
      let a1 = s[0], a2 = s[1]; if (sg > 0 && J.lambai) a2 += Math.sin(t * 9) * 26 * J.lambai;
      const sw = ayun * 0.6 * -sg, S = o.profilMotor ? [34 + (sg < 0 ? -8 : 8), -360 + nafas] : [sg * (62 + 26 * GM), -360 + nafas];
      // Bahu dan kedua lengan berada di bidang samping torso; lengan jauh sedikit lebih tinggi.
      let E = o.profilMotor ? [112 + (sg < 0 ? -8 : 8), -320 + nafas] : [S[0] + sg * Math.sin((a1 + sw) * R) * 85, S[1] + Math.cos((a1 + sw) * R) * 85];
      let H = o.profilMotor ? [218, -284 + nafas + (sg < 0 ? -7 : 0)] : [E[0] + sg * Math.sin((a2 + sw) * R) * 80, E[1] + Math.cos((a2 + sw) * R) * 80];
      if (o.profilMotor && !o.kait) { // (27 Nov) lengan tampak samping: angkat ke samping (depan) = angkat ke depan; ayun jalan berlawanan kaki
        const ayunSisi = sg * ((J.pp_ki == null ? J.pp : J.pp_ki) - (J.pp_ka == null ? J.pp : J.pp_ka)) * 80 + ayun * 0.6 * sg;
        const b1 = (Math.abs(a1) + ayunSisi) * R, b2 = (Math.abs(a2) + ayunSisi) * R;
        E = [S[0] + Math.sin(b1) * 85, S[1] + Math.cos(b1) * 85];
        H = [E[0] + Math.sin(b2) * 80, E[1] + Math.cos(b2) * 80];
      }
      if (o.profilMotor && o.kait) {
        // Tangan ke pegangan benda (setang/setir); tanpa pegangan: bertumpu di paha.
        const tg = o.kait.pegang ? o.kait.pegang[sg < 0 ? 0 : 1] || o.kait.pegang[0] : [78 + (sg < 0 ? -8 : 8), hy0 - 30];
        const q = keT(tg, J);
        [E, H] = ik2(S, q, 85, 80, false);
      }
      return { ats: `<line x1="${S[0]}" y1="${S[1]}" x2="${E[0]}" y2="${E[1]}" stroke="${BD}" stroke-width="36" stroke-linecap="round"/>`,
               bwh: `<line x1="${E[0]}" y1="${E[1]}" x2="${H[0]}" y2="${H[1]}" stroke="${BD}" stroke-width="34" stroke-linecap="round"/><circle cx="${H[0]}" cy="${H[1]}" r="19" fill="${pakaiP ? KLB : BD}" stroke="${INK}" stroke-width="4"/>`, S, E, H };
    };
    const L = lengan(-1, J.la), Rk = lengan(1, J.ra);
    let barang = "";
    if (J.pegang === "hp") barang = `<g transform="translate(${Rk.H[0] - 14} ${Rk.H[1] - 30}) rotate(-8)"><rect x="-24" y="-44" width="48" height="84" rx="9" fill="#15121a" stroke="${INK}" stroke-width="4"/><rect x="-19" y="-38" width="38" height="70" rx="5" fill="#8fd0ff" opacity="${0.8 + 0.2 * Math.sin(t * 3)}"/></g>`;
    else if (J.pegang === "buku") barang = `<g transform="translate(${Rk.H[0] - 20} ${Rk.H[1] - 20})"><rect x="-40" y="-50" width="80" height="96" rx="6" fill="#7b2a20" stroke="${INK}" stroke-width="4"/><rect x="-32" y="-42" width="64" height="80" fill="#fbf2dc"/></g>`;
    else if (J.pegang === "gelas") barang = `<g transform="translate(${Rk.H[0]} ${Rk.H[1] - 26})"><path d="M -20 -30 L 20 -30 L 16 30 L -16 30 Z" fill="#dff3ff" stroke="${INK}" stroke-width="4" opacity=".9"/></g>`;
    else if (J.pegang === "beliung") {
      // Satu gagang mengikuti kedua titik genggam, bukan menempel pada satu tangan.
      const dx = Rk.H[0] - L.H[0], dy = Rk.H[1] - L.H[1];
      const len = Math.max(1, Math.hypot(dx, dy)), ux = dx / len, uy = dy / len;
      const hx = Rk.H[0] + ux * 112, hy = Rk.H[1] + uy * 112;
      const sudut = Math.atan2(ux, -uy) * 180 / Math.PI;
      barang = `<g transform="translate(${hx} ${hy}) rotate(${sudut})">
        <path d="M 0 0 L 0 ${len + 126}" stroke="#4c3322" stroke-width="22" stroke-linecap="round"/>
        <path d="M 0 0 L 0 ${len + 126}" stroke="#9a6b3e" stroke-width="14" stroke-linecap="round"/>
        <path d="M -76 -8 Q -42 -24 0 -9 Q 42 -24 76 -8 L 68 12 Q 0 0 -68 12 Z" fill="#aeb8c2" stroke="#34333a" stroke-width="7" stroke-linejoin="round"/>
        <path d="M -60 -7 Q -30 -14 -8 -7" stroke="#eef3f5" stroke-width="5" fill="none" stroke-linecap="round"/>
      </g>
      <circle cx="${L.H[0]}" cy="${L.H[1]}" r="17" fill="${KLB}" stroke="#34333a" stroke-width="4"/>
      <circle cx="${Rk.H[0]}" cy="${Rk.H[1]}" r="17" fill="${KLB}" stroke="#34333a" stroke-width="4"/>`;
      // Efek benturan mengikuti siklus gali Python (1,15 dtk), tepat saat beliung menyentuh dinding.
      if (aksi === "gali") {
        const fase = ((t + (offset || 0)) % 1.15 + 1.15) % 1.15 / 1.15;
        if (fase >= 0.52 && fase <= 0.72) {
          const q = (fase - 0.52) / 0.20, R2 = rng((id || 0) * 97 + Math.floor(t / 1.15) * 31 + 7);
          const rr = 34 + 72 * q, op = 1 - q;
          barang += `<circle cx="${hx}" cy="${hy}" r="${rr}" fill="none" stroke="#ffd27a" stroke-width="${10 * op + 2}" opacity="${0.62 * op}"/>`;
          barang += `<circle cx="${hx}" cy="${hy}" r="${18 * (1 - q) + 3}" fill="#fff6cf" opacity="${0.7 * op}"/>`;
          for (let i = 0; i < 14; i++) {
            const a = R2() * Math.PI * 2, sp = 38 + R2() * 125, sz = 5 + R2() * 7;
            const px = hx + Math.cos(a) * sp * q, py = hy + Math.sin(a) * sp * q + 68 * q * q;
            barang += `<circle cx="${px}" cy="${py}" r="${sz * (1 - 0.45 * q)}" fill="${i % 3 ? "#ffd27a" : "#fff"}" opacity="${op}"/>`;
          }
        }
      }
    }
    if (J.pegang === "palu") {
      const sudut = J.ra[1] * 0.45 - 10;
      barang = `<g transform="translate(${Rk.H[0]} ${Rk.H[1]}) rotate(${sudut})"><path d="M 0 42 L 0 -86" stroke="#76502f" stroke-width="15" stroke-linecap="round"/><path d="M -32 -86 L 32 -86 L 26 -58 L -26 -58 Z" fill="#7d8790" stroke="#34333a" stroke-width="6" stroke-linejoin="round"/></g>`;
    }
    const T = `translate(0 ${J.turun + geserY}) rotate(${J.badan} 0 -200)`;
    const g = o.profilMotor && J.depan <= 0.5
      ? kaki + `<g transform="${T}">${L.ats}${L.bwh}${bdn}${Rk.ats}${Rk.bwh}${barang}</g>` // samping: lengan jauh di balik badan
      : kaki + `<g transform="${T}">${bdn}${L.ats}${Rk.ats}${J.depan > 0.5 ? "" : L.bwh + Rk.bwh + barang}</g>`;
    const depan = J.depan > 0.5 ? `<g transform="${T}">${L.bwh}${Rk.bwh}${barang}</g>` : "";
    // sendi (koordinat lokal, sebelum T untuk lengan) dipakai alat uji tokoh (mesin-video/papan/uji_tokoh.py)
    const sendi = { kaki: titik, lengan: [[L.S, L.E, L.H], [Rk.S, Rk.E, Rk.H]], turun: J.turun, badan: J.badan };
    return { g, depan, T, kepala: J.kepala, guling: J.guling, sendi };
  }

  // ---- tokoh boneka: kepala detail, badan siluet gelap (sopan), kaki di (0,0) ----
  function boneka(b, t, d) {
    if (b.npc != null && !b._npc) { // figuran berwarna acak tetap (seed = b.npc); kunci yang diisi manual menimpa
      const R = rng(b.npc * 97 + 13), pk = (arr) => arr[Math.floor(R() * arr.length)], BJ = ["#5a7a9a", "#d9534f", "#6aa6a0", "#f2c14e", "#9a7ac9", "#e9e4d8", "#3f8a4a", "#c96a4a", "#4a6a8a"];
      const pr = R() < 0.45, tua = R() < 0.2; let kulit = pk(["#f2dcc2", "#e9c6a2", "#d9b48c", "#c99a72", "#a87a56"]);
      const gen = pr ? { rambut: "kerudung", kerudung: pk(["#6aa6a0", "#d98a9a", "#f2c14e", "#5a7a9a", "#e9e4d8", "#9a7ac9", "#3a3a4a"]), pakaian: { jenis: "gamis", warna: pk(BJ) } }
        : { rambut: tua ? "tipis" : pk(["pendek", "belah", "keriting", "pendek"]), warna_rambut: tua ? "#cfcac2" : pk(["#1d1520", "#3a2a20", "#1d1520"]), janggut: tua || R() < 0.2 ? (tua ? "#d8d2c8" : true) : false,
            pakaian: { jenis: pk(["kaus", "koko", "kaus"]), warna: pk(BJ), bawah: pk(["celana", "celana", "sarung"]), bawah_warna: pk(["#2f3a4a", "#3b3f4a", "#6a4a3a", "#4a5a3a"]), peci: R() < 0.25 ? pk([true, "putih"]) : false } };
      if (tua) gen.keriput = true;
      if ((b.suku || C.suku) === "arab") { // (27 Nov) figuran Arab: jubah, bisht, imamah/ghutrah/peci; perempuan berabaya
        const R2 = rng(b.npc * 131 + 7), pk2 = (arr) => arr[Math.floor(R2() * arr.length)];
        Object.assign(gen, pr
          ? { rambut: "kerudung", kerudung: pk2(["#2a2430", "#3a3440", "#4a3a30", "#5a4a3a", "#e9e4d8"]), pakaian: { jenis: "gamis", warna: pk2(["#2a2430", "#3a3440", "#4a3a30", "#6a5a48"]) } }
          : { rambut: "pendek", warna_rambut: tua ? "#cfcac2" : "#1d1520", janggut: tua ? "#d8d2c8" : R2() < 0.7,
              penutup_kepala: pk2(["imamah", "imamah", "kain", "kopiah"]),
              warna_penutup: pk2(["#ffffff", "#f4f1ea", "#ece2cc", "#ffffff"]),
              pakaian: { jenis: "jubah", warna: pk2(["#f4f1ea", "#ece2cc", "#d8c9a8", "#b89a74", "#8a7a6a", "#ffffff"]), bawah: "gamis",
                bisht: tua || R2() < 0.3 ? pk2(["#2a2024", "#4a3426", "#6a4a2a"]) : false } });
        kulit = pk2(["#d9b48c", "#c99a72", "#b8865e", "#e0bf98"]);
      }
      Object.keys(gen).forEach((k) => { if (b[k] == null) b[k] = gen[k]; }); if (b.kulit == null) b.kulit = kulit; if (!b.gaya) b.gaya = "umum"; b._npc = 1;
    }
    const HD = (b.hidup != null ? b.hidup : C.hidup) && b.gaya !== "siluet" && b.gaya !== "dajjal";
    const ta = HD && (b.dua != null ? b.dua : C.dua !== false) ? Math.floor(t * 15 + 0.001) / 15 : t; // akting "on twos" (15 fps): loncatan tegas; posisi & kamera tetap 30 fps
    const kunci = (x0) => Array.isArray(x0) && Array.isArray(x0[0]) && typeof x0[0][1] === "number";
    let x = v(b.x, t, d, 540), y = v(b.y, t, d, 1500), s = v(b.s, t, d, 1) * (b.skala_usia || 1); const naik = v(b.naik, t, d, 1);
    let arah = HD && kunci(b.arah) ? vs(b.arah, ta, 0) : v(b.arah, t, d, 0), tunduk = HD && kunci(b.tunduk) ? vs(b.tunduk, ta, 0) : v(b.tunduk, t, d, 0);
    const wajah = v(b.wajah, HD ? ta : t, d, "netral"), mata = v(b.mata, HD ? ta : t, d, "buka"), lengan = v(b.lengan, t, d, "turun"), keringat = v(b.keringat, t, d, 0), jalan = v(b.jalan, t, d, 0);
    const ayun = jalan ? Math.sin(t * 7) * 22 * jalan : 0, nafas = Math.sin(t * 2.2) * 3;
    let kedip = mata === "buka" && ((t + (b.ph != null ? b.ph : ((+b.x || 0) * 0.0017) % 1.2)) % 3.1) > 2.98; // tidak pernah kedip di awal potongan (frame 0 mata terbuka), kedip tidak serempak
    let H = null;
    if (HD) { // idle (kedip acak, goyang, lirikan), reaksi, anggukan per kata, masuk dengan hentakan
      const id = b.id || 0, ph = id * 1.37 + (b.ph || 0);
      if (!b._kd) { const R = rng(id * 31 + 5); b._kd = []; let q = 0.7 + R() * 2.2; while (q < 300) { b._kd.push(q); if (R() < 0.15) b._kd.push(q + 0.27); q += 2 + R() * 4; } }
      const Rl = rng(Math.floor((t + ph) / 1.7) * 17 + id), lirik = Rl() < 0.55;
      H = { kedip: mata === "buka" && b._kd.some((q) => ta >= q && ta < q + 0.11), krot: 1.4 * Math.sin(t * 0.9 + ph) + 0.7 * Math.sin(t * 1.9 + ph * 2), ky: 0, brot: 0.7 * Math.sin(t * 0.7 + ph), dy: 0, dx: 0, sq: 0, sc: 1,
            lx: lirik ? (Rl() - 0.5) * 6 : 0, ly: lirik ? (Rl() - 0.5) * 4 : 0, pop: 0 };
      (b.reaksi || []).forEach(([tr, jn, kuat = 1]) => { const q = ta - tr; if (q < 0) return;
        if (jn === "angguk" && q < 0.5) tunduk += 0.9 * kuat * Math.max(0, Math.sin(q * 25.1));
        else if (jn === "geleng" && q < 0.5) arah += 0.45 * kuat * Math.sin(q * 31.4);
        else if (jn === "miring") H.krot += 9 * kuat * balik(q / 0.13) * clamp((1.0 - q) / 0.15);
        else if (jn === "kaget" && q < 0.6) { H.dy -= 26 * kuat * Math.sin(Math.min(q / 0.22, 1) * Math.PI); H.sq += 0.07 * kuat * Math.exp(-q * 10) * Math.sin(q * 30); }
        else if (jn === "lompat" && q < 0.3) H.dy -= 46 * kuat * Math.sin((q / 0.3) * Math.PI);
        else if (jn === "hentak" && q < 0.6) { H.sq += 0.08 * kuat * Math.exp(-q * 9) * Math.sin(q * 28 - 0.5); H.krot -= 5 * kuat * Math.exp(-q * 10); }
        else if (jn === "maju") H.brot += 6 * kuat * balik(q / 0.15) * clamp((1.1 - q) / 0.2);
        else if (jn === "mundur") H.brot -= 6 * kuat * balik(q / 0.15) * clamp((1.1 - q) / 0.2);
        else if (jn === "kedip" && q < 0.11) H.kedip = true; });
      if (!b._uw) b._uw = (b.ucap || []).map((u) => u[0]);
      let wi = -1; b._uw.forEach((tw, i) => { if (ta >= tw - 0.05) wi = i; });
      if (wi >= 0) { const q = ta - (b._uw[wi] - 0.05); H.ky += 4 * Math.exp(-q * 9) * Math.sin(q * 20 + 0.5); H.krot += (wi % 2 ? 1 : -1) * 1.8 * Math.exp(-q * 7); }
      const tw = kunciAkhir(b.wajah, ta); if (tw > 0) { H.pop = 0.075 * Math.exp(-(ta - tw) * 16); }
      if (Array.isArray(b.wajah) && Array.isArray(b.wajah[0]) && b.wajah.some(([k], i) => i > 0 && ta > k - 0.15 && ta < k + 0.6) && !(b.reaksi || []).some(([tr, jn]) => jn === "kedip" && ta >= tr && ta < tr + 0.11)) H.kedip = false; // kepala "pop" saat wajah berganti; kedipan acak tidak boleh menutupi wajah baru (0,6 dtk)
      if (b.masuk) { const M = b.masuk, q = (t - (M.at || 0)) / (M.lama || 0.3); if (q < 0) return ""; const f = balik(q, 2.2);
        if (M.dari === "kiri") H.dx -= (1 - f) * 760; else if (M.dari === "kanan") H.dx += (1 - f) * 760; else if (M.dari === "pop") H.sc *= Math.max(0.01, f); else H.dy += (1 - f) * 760;
        const q2 = t - (M.at || 0) - (M.lama || 0.3) * 0.55; if (q2 > 0 && q2 < 0.5) H.sq -= 0.09 * Math.exp(-q2 * 9) * Math.cos(q2 * 26); }
      kedip = H.kedip;
    }
    const tubuh = 520 * (1 - naik) * 1.1;
    // pakaian (5 Nov): b.pakaian = {jenis: koko|kaus|gamis, warna, bawah: sarung|celana|gamis, bawah_warna, motif: kotak|polos, peci: warna|false}
    const P = b.pakaian && b.gaya !== "siluet" ? b.pakaian : null, KLB = b.kulit || (b.gaya === "anwar" ? "#dca779" : KULIT);
    const BD = P ? (P.warna || "#ece6d6") : BADAN, WC = P ? (P.bawah_warna || "#2f4a6a") : BADAN, bawahP = P ? (P.bawah || (P.jenis === "gamis" || P.jenis === "daster" || P.jenis === "jubah" ? "gamis" : "sarung")) : "";
    const GM = v(b.gemuk, t, d, 0), SH = 62 + 26 * GM, KB = b.kepala_besar || 1;
    const kaki = (dx, a, w = BADAN, tb = 44) => `<line x1="${dx}" y1="-200" x2="${dx + Math.sin((a * Math.PI) / 180) * 200}" y2="${-200 + Math.cos((a * Math.PI) / 180) * 200}" stroke="${w}" stroke-width="${tb}" stroke-linecap="round"/>`;
    const RIG = b.pose != null || HD || b.profil ? poseKini(b, HD ? ta : t, HD) : null; // tampak samping selalu bersendi (badan ikut menyamping)
    if (RIG && b._gabungan) { x += RIG.geser || 0; arah += (RIG.toleh || 0) * 4; tunduk += (RIG.angguk || 0) * 3; }
    // AKSI GALI: pose kerja adalah aksi berulang, bukan pose statis.
    // Fase diberi offset per NPC agar pekerja tidak mengayun serempak.
    if (RIG && (RIG._aksi === "gali" || (!b._gabungan && (b.aksi === "gali" || b.pose === "kerja")))) {
      const fase = ((t * 1.35 + (((b.npc != null ? b.npc : b.id) || 0) * 0.381)) % 1 + 1) % 1;
      const ayunGali = Math.sin(fase * Math.PI * 2);
      const hantam = Math.pow(Math.max(0, Math.sin(fase * Math.PI * 2 + 0.35)), 5);
      RIG.ra = [132 + 18 * ayunGali, 212 + 28 * ayunGali - 12 * hantam];
      RIG.la = [112 + 12 * ayunGali, 198 + 18 * ayunGali];
      RIG.badan = 5 + 8 * hantam - 3 * ayunGali;
      RIG.turun = 3 + 9 * hantam;
      RIG.lk = [4, 0]; RIG.rk = [-4, 0];
      RIG.pegang = "beliung";
    }
    if (RIG && HD) { const ph = (b.id || 0) * 1.37, q = ta - RIG._tk; RIG.badan += H.brot; RIG.kepala += H.krot; RIG.la = [RIG.la[0], RIG.la[1] + 2 * Math.sin(t * 1.1 + ph)]; RIG.ra = [RIG.ra[0], RIG.ra[1] - 2 * Math.sin(t * 1.3 + ph)];
      if (q >= 0 && q < 0.6) H.sq += 0.05 * Math.exp(-q * 8) * Math.sin(q * 24 - 0.6); } // squash & stretch kecil tiap ganti pose
    let g;
    if (!P) g = kaki(-26, ayun) + kaki(26, -ayun) + `<rect x="-70" y="${-395 + nafas}" width="140" height="215" rx="60" fill="${BADAN}"/>`;
    else {
      const gelap = (h, f) => warna(h, "#000000", f), sepatu = (dx) => `<ellipse cx="${dx}" cy="-6" rx="30" ry="14" fill="#2a2024"/>`;
      if (bawahP === "celana") g = kaki(-26, ayun, WC, 46) + kaki(26, -ayun, WC, 46) + sepatu(-26 + Math.sin(ayun * Math.PI / 180) * 200) + sepatu(26 - Math.sin(ayun * Math.PI / 180) * 200);
      else {
        const top = bawahP === "gamis" ? -360 : -225, wn = bawahP === "gamis" ? BD : WC;
        g = sepatu(-32) + sepatu(32) + `<path d="M -74 ${top + nafas} L 74 ${top + nafas} L 92 -16 Q 0 -6 -92 -16 Z" fill="${wn}"/>`;
        if (bawahP === "sarung" && P.motif !== "polos") { // motif kotak sarung
          for (let i = -3; i <= 3; i++) g += `<line x1="${i * 24}" y1="${top + nafas + 4}" x2="${i * 28}" y2="-18" stroke="${gelap(wn, 0.35)}" stroke-width="${i % 2 ? 5 : 10}" opacity=".55"/>`;
          for (let yy = top + 30; yy < -20; yy += 42) g += `<line x1="-90" y1="${yy + nafas * (1 - (yy - top) / 230)}" x2="90" y2="${yy}" stroke="${warna(wn, "#ffffff", 0.35)}" stroke-width="7" opacity=".45"/>`;
          g += `<line x1="-74" y1="${top + nafas + 10}" x2="74" y2="${top + nafas + 10}" stroke="${gelap(wn, 0.45)}" stroke-width="8"/>`;
        }
      }
      if (bawahP !== "gamis") g += `<rect x="${-70 - 30 * GM}" y="${-395 + nafas}" width="${140 + 60 * GM}" height="${bawahP === "sarung" ? 190 : 215}" rx="${56 + 20 * GM}" fill="${BD}"/>`;
      g += bajuDetail(P, BD, nafas, GM);
      if (P.bisht) g += [-1, 1].map((sg) => `<path d="M ${sg * 30} ${-404 + nafas} L ${sg * (78 + 30 * GM)} ${-392 + nafas} L ${sg * (104 + 30 * GM)} -50 L ${sg * 40} -50 Z" fill="${P.bisht}" stroke="${INK}" stroke-width="4"/><path d="M ${sg * 30} ${-404 + nafas} L ${sg * 40} -50" stroke="#c9a24a" stroke-width="6"/>`).join(""); // bisht (tanpa rangka)
    }
    const tangan = (x2, y2) => (P ? `<circle cx="${x2}" cy="${y2}" r="19" fill="${KLB}" stroke="${INK}" stroke-width="4"/>` : "");
    const lenganKiri = `<line x1="${-SH}" y1="${-360 + nafas}" x2="${-SH - 22 - ayun * 0.3}" y2="${-200 + nafas}" stroke="${BD}" stroke-width="36" stroke-linecap="round"/>` + tangan(-SH - 22 - ayun * 0.3, -192 + nafas);
    g += lenganKiri;
    const kaitL = b._kaitDunia ? (() => { const cm = b.cermin || b.profil === "kiri" ? -1 : 1, L = (p) => [cm * (p[0] - x) / s, (p[1] - y) / s - tubuh], K = b._kaitDunia;
      return { pijak: K.pijak && K.pijak.map(L), pegang: K.pegang && K.pegang.map(L) }; })() : null;
    let RG = null; if (RIG) { RG = rangka(RIG, { P, BD, WC, KLB, nafas, ayun, bawahP, t: HD ? ta : t, gm: GM, aksi: RIG && RIG._aksi || b.aksi, id: b.npc != null ? b.npc : b.id, offset: b._gerak_offset, profilMotor: (b.profil === "kanan" || b.profil === true || b.profil === "kiri") && !!RIG && !RIG.guling,
      kait: kaitL }); g = RG.g; }
    let lenganKanan = RIG ? "" : `<line x1="${SH}" y1="${-360 + nafas}" x2="${SH + 22 + ayun * 0.3}" y2="${-200 + nafas}" stroke="${BD}" stroke-width="36" stroke-linecap="round"/>` + tangan(SH + 22 + ayun * 0.3, -192 + nafas);
    // kepala
    const hx = arah * 10, hy = -492 - (KB - 1) * 96 + nafas + tunduk * 14 + (H ? H.ky : 0), ex = arah * 24, ey = tunduk * 14 + (mata === "atas" ? -8 : mata === "bawah" ? 8 : 0);
    let k = b.profil === "kanan" || b.profil === true || b.profil === "kiri"
      ? `<path d="M -4 ${-414 + nafas} L 34 ${-414 + nafas} L 42 ${-374 + nafas} L 2 ${-370 + nafas} Z" fill="${P ? KLB : BADAN}"/>`
      : `<rect x="-22" y="${-410 + nafas}" width="44" height="40" fill="${P ? KLB : BADAN}"/>`;
    k += `<g transform="translate(${hx} ${hy}) rotate(${arah * 6 + tunduk * 8}) scale(${1.28 * KB * (1 + (H ? H.pop : 0))})">`;
    const gaya = b.gaya || "umum", ANW = gaya !== "siluet", KL = gaya === "anwar" ? "#dca779" : KULIT, belakang = v(b.belakang, t, d, false);
    const cewek = b.rambut === "kerudung" || b.wanita === true || /^(wanita|perempuan)$/.test(b.jenis_kelamin || ""); // (27 Nov) wajah perempuan
    if (gaya === "siluet") {
      k += `<circle r="78" fill="${BAYANG}"/>`;
    } else if (belakang && b.rambut === "kerudung") { // perempuan dari belakang: kain kerudung menjuntai sampai bahu
      k += `<path d="M -92 20 C -100 -110, 100 -110, 92 20 C 104 90, 96 130, 70 150 L -70 150 C -96 130, -104 90, -92 20 Z" fill="${BAYANG}" stroke="${INK}" stroke-width="6"/><path d="M -60 -50 C -20 -80, 30 -78, 62 -44" stroke="#ffffff" stroke-width="5" fill="none" opacity=".18"/>`;
    } else if (b.profil === "kanan" || b.profil === true || b.profil === "kiri") {
      // Tampak samping: wajah mengarah ke depan perjalanan, bukan ke kamera.
      // (27 Nov) kepala bulat sebesar tampak depan, hidung membulat, telinga di tengah sisi kepala
      const kp = b.kulit || KL;
      const k0 = k.length;
      k += cewek
        ? `<path d="M -36 74 Q -80 52 -80 -6 Q -78 -86 2 -86 Q 52 -84 58 -34 Q 62 -16 62 -4 Q 69 2 67 10 Q 65 16 60 18 Q 62 38 54 56 Q 42 80 18 84 Q -8 88 -36 74 Z" fill="${kp}" stroke="${INK}" stroke-width="7" stroke-linejoin="round"/>`
        : `<path d="M -36 72 Q -82 50 -80 -8 Q -78 -86 2 -86 Q 58 -84 64 -30 L 66 -8 Q 86 6 80 18 Q 76 26 64 26 Q 68 36 62 44 Q 60 72 34 82 Q 4 92 -36 72 Z" fill="${kp}" stroke="${INK}" stroke-width="7" stroke-linejoin="round"/>`;
      if (b.janggut) k += `<path d="M -8 38 Q 6 98 40 86 Q 62 76 62 54 Q 46 64 24 58 Q 6 52 -8 38 Z" fill="${b.janggut === true ? (b.warna_rambut || INK) : b.janggut}" stroke="${INK}" stroke-width="4"/>`;
      if (b.rambut === "kerudung") { // kerudung tampak samping: kain menutup rambut, telinga, dan leher; wajah terbuka
        const kd = b.kerudung || "#6aa6a0";
        // bentuk bulat membingkai wajah seperti tampak depan, menjuntai membulat di bawah dagu
        k += `<path d="M 56 -50 Q 38 -108 -22 -104 Q -96 -98 -98 -14 Q -100 58 -70 100 Q -34 128 26 122 Q 66 116 62 92 Q 54 82 30 80 Q 2 70 -4 38 Q -10 0 4 -24 Q 22 -48 56 -50 Z" fill="${kd}" stroke="${INK}" stroke-width="7" stroke-linejoin="round"/>`;
        k += `<path d="M -62 -46 Q -78 24 -52 96" fill="none" stroke="${warna(kd, "#000000", 0.16)}" stroke-width="5"/>`;
      } else {
        k += `<path d="M -84 14 Q -96 -92 4 -100 Q 70 -98 70 -42 Q 44 -64 10 -60 Q -22 -56 -40 -28 Q -50 -8 -58 16 Q -70 22 -84 14 Z" fill="${b.warna_rambut || INK}" stroke="${INK}" stroke-width="6"/>`;
        k += `<ellipse data-telinga="1" cx="-16" cy="10" rx="15" ry="20" fill="${kp}" stroke="${INK}" stroke-width="6"/><path d="M -12 2 Q -24 8 -14 20" fill="none" stroke="${INK}" stroke-width="4" stroke-linecap="round"/>`;
      }
      if (cewek) {
        // Selaras dengan tampak depan: mata bulat sebesar depan pada tinggi yang sama, alis tipis, senyum kecil.
        k += `<path d="M 22 -28 Q 36 -36 50 -28" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`;
        k += `<ellipse cx="38" cy="2" rx="11" ry="15" fill="#fff" stroke="${INK}" stroke-width="3"/><circle cx="42" cy="3" r="8.5" fill="${INK}"/><circle cx="44.5" cy="-0.5" r="2.4" fill="#fff"/><circle cx="40" cy="6" r="1.6" fill="#fff" opacity=".9"/>`;
        k += `<ellipse cx="18" cy="28" rx="13" ry="7" fill="#f2a0a0" opacity=".18"/>`;
        k += `<path d="M 44 42 Q 51 47 57 41" fill="none" stroke="#7a3a3a" stroke-width="4.5" stroke-linecap="round"/>`;
      } else {
        k += `<path d="M 18 -36 Q 34 -42 48 -34" fill="none" stroke="${INK}" stroke-width="7" stroke-linecap="round"/><circle cx="34" cy="-14" r="9" fill="#fff" stroke="${INK}" stroke-width="3"/><circle cx="38" cy="-14" r="5" fill="${INK}"/>`;
        k += `<path d="M 44 50 Q 54 54 60 48" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`;
      }
      // berkerudung: kepala+kain diperkecil agar sebesar tampak depan (kain depan top -75, bawah 122)
      if (b.rambut === "kerudung") k = k.slice(0, k0) + `<g transform="translate(2 10) scale(0.86)">` + k.slice(k0) + `</g>`;
    } else if (belakang) {
      k += `<circle data-telinga="1" cx="-76" cy="6" r="15" fill="${KL}" stroke="${INK}" stroke-width="6"/><circle data-telinga="1" cx="76" cy="6" r="15" fill="${KL}" stroke="${INK}" stroke-width="6"/><circle r="78" fill="${b.warna_rambut || INK}" stroke="${INK}" stroke-width="7"/><path d="M -60 50 Q 0 90 60 50 L 50 72 Q 0 96 -50 72 Z" fill="${KL}"/>`;
    } else if (gaya === "umum") {
      const kl = b.kulit || KL, rb = b.rambut || "pendek", RB = b.warna_rambut || INK;
      if (rb === "kerudung") { // perempuan: kepala tertutup kain gelap (sama dengan badan)
        k += `<path d="M -92 30 C -100 -110, 100 -110, 92 30 C 96 90, 60 120, 0 122 C -60 120, -96 90, -92 30 Z" fill="${b.kerudung || BAYANG}" stroke="${INK}" stroke-width="6"/>`;
        k += `<ellipse cx="0" cy="8" rx="62" ry="72" fill="${kl}" stroke="${INK}" stroke-width="6"/>`;
      } else {
        k += `<circle data-telinga="1" cx="-76" cy="6" r="15" fill="${kl}" stroke="${INK}" stroke-width="6"/><circle data-telinga="1" cx="76" cy="6" r="15" fill="${kl}" stroke="${INK}" stroke-width="6"/>`;
        k += `<ellipse rx="75" ry="82" fill="${kl}" stroke="${INK}" stroke-width="7"/>`;
        if (rb === "pendek") k += `<path d="M -76 -4 C -84 -98, 82 -106, 76 -4 C 68 -36, 52 -50, 30 -52 C 10 -40, -14 -56, -34 -46 C -54 -50, -70 -30, -76 -4 Z" fill="${RB}"/>`;
        else if (rb === "keriting") { for (let i = 0; i < 9; i++) { const a = Math.PI * (1.05 + i * 0.1), r = 70; k += `<circle cx="${Math.cos(a) * r}" cy="${Math.sin(a) * r - 6}" r="24" fill="${RB}"/>`; } }
        else if (rb === "tipis") k += `<path d="M -74 -18 C -70 -70, -40 -84, -20 -82 L -30 -60 C -50 -56, -64 -40, -74 -18 Z M 74 -18 C 70 -70, 40 -84, 20 -82 L 30 -60 C 50 -56, 64 -40, 74 -18 Z" fill="${RB}"/>`;
        else if (rb === "jambul") k += `<path d="M -76 -4 C -84 -70, -60 -104, -20 -112 C 10 -150, 80 -140, 84 -96 C 70 -110, 50 -112, 40 -104 C 70 -84, 80 -50, 76 -4 C 66 -40, 40 -58, 10 -58 C -24 -56, -60 -40, -76 -4 Z" fill="${RB}"/><path d="M -10 -110 C 20 -134, 56 -130, 70 -110" stroke="#ffffff" stroke-width="5" fill="none" opacity=".25"/>`;
        else if (rb === "botak") k += `<path d="M -76 -6 C -76 -40, -66 -54, -54 -60 L -50 -10 Z M 76 -6 C 76 -40, 66 -54, 54 -60 L 50 -10 Z" fill="${RB}"/><ellipse cx="-24" cy="-56" rx="22" ry="10" fill="#ffffff" opacity=".45" transform="rotate(-20 -24 -56)"/>`;
        else if (rb === "rol") k += `<path d="M -76 0 C -84 -96, 82 -104, 76 0 C 66 -40, 40 -52, 0 -54 C -40 -52, -66 -40, -76 0 Z" fill="${RB}"/>` + [[-50, -70], [-16, -88], [20, -88], [54, -70]].map(([cx, cy], i) => `<rect x="${cx - 18}" y="${cy - 16}" width="36" height="32" rx="12" fill="${["#ff8fb1", "#7fd0ff", "#ffd36b", "#a7e08a"][i]}" stroke="${INK}" stroke-width="4"/><line x1="${cx - 10}" y1="${cy}" x2="${cx + 10}" y2="${cy}" stroke="${INK}" stroke-width="3" opacity=".5"/>`).join("");
        else if (rb === "kuncir") k += `<path d="M 60 -40 C 120 -40, 128 40, 96 90 C 110 30, 92 -10, 60 -20 Z" fill="${RB}" stroke="${INK}" stroke-width="4"/><path d="M -76 -4 C -84 -98, 82 -106, 76 -4 C 70 -50, 30 -70, -10 -66 C -40 -60, -66 -40, -76 -4 Z" fill="${RB}"/><circle cx="64" cy="-36" r="9" fill="${b.ikat || "#e03131"}"/>`;
        else if (rb === "belah") k += `<path d="M -76 -2 C -86 -96, 84 -104, 76 -2 C 70 -50, 30 -66, 8 -70 L 0 -40 L -8 -70 C -30 -66, -70 -50, -76 -2 Z" fill="${RB}"/>`;
        if (b.janggut) {
          const jb = b.janggut_model || "pendek";
          const janggutD = jb === "tipis"
            ? "M -58 30 Q 0 58 58 30 Q 36 54 0 52 Q -36 54 -58 30 Z"
            : jb === "panjang"
              ? "M -58 30 C -50 92, 50 92, 58 30 L 46 92 Q 0 138 -46 92 Z"
              : "M -58 30 C -50 92, 50 92, 58 30 C 40 70, -40 70, -58 30 Z";
          k += `<path d="${janggutD}" fill="${b.janggut === true ? RB : b.janggut}"/>`;
        }
        if (b.keriput) k += `<path d="M -40 -46 q 10 -4 20 0 M 20 -46 q 10 -4 20 0 M -58 22 q 4 8 10 10 M 58 22 q -4 8 -10 10" fill="none" stroke="${INK}" stroke-width="3" opacity=".5"/>`;
      }
    } else if (gaya === "dajjal") { // hanya ciri dari hadits: muda, rambut sangat keriting, satu mata buta menonjol, tulisan ك ف ر di antara mata. Ekspresi: senyum licik.
      const kl = b.kulit || "#b9a88c", RB = "#120d10", tl = v(b.tulisan, t, d, 1), sen = v(b.senyum, t, d, 1), cb = v(b.cahaya_bawah, t, d, 0);
      for (let i = 0; i < 16; i++) { const a = Math.PI * (0.92 + i * 0.075), r = 74 + (i % 2) * 8; k += `<circle cx="${Math.cos(a) * r}" cy="${Math.sin(a) * r - 10}" r="${26 + (i % 3) * 4}" fill="${RB}"/>`; }
      k += `<circle data-telinga="1" cx="-78" cy="8" r="15" fill="${kl}" stroke="${INK}" stroke-width="6"/><circle data-telinga="1" cx="78" cy="8" r="15" fill="${kl}" stroke="${INK}" stroke-width="6"/>`;
      k += `<ellipse rx="74" ry="84" fill="${kl}" stroke="${INK}" stroke-width="7"/>`;
      for (let i = 0; i < 11; i++) { const a = Math.PI * (1.12 + i * 0.077); k += `<circle cx="${Math.cos(a) * 66}" cy="${Math.sin(a) * 66 - 28}" r="${20 + (i % 2) * 5}" fill="${RB}"/>`; }
      k += `<path d="M 4 -82 A 74 84 0 0 1 4 82 A 46 84 0 0 0 4 -82 Z" fill="#0b0710" opacity=".42"/>`; // bayangan separuh wajah
      k += `<path d="M -58 -40 Q -36 -46 -12 -32" stroke="${INK}" stroke-width="9" fill="none" stroke-linecap="round"/><path d="M 12 -22 L 52 -32" stroke="${INK}" stroke-width="11" stroke-linecap="round"/>`; // alis: kiri penonton terangkat, kanan rendah menekan
      // mata kanannya (kiri penonton): buta, menonjol keluar seperti buah anggur yang mengapung
      k += `<ellipse cx="-31" cy="6" rx="27" ry="24" fill="#c6ccad" stroke="${INK}" stroke-width="4"/><path d="M -52 -2 q 8 4 14 2 M -50 18 q 10 -2 16 4 M -10 12 q -6 4 -12 2 M -40 26 q 6 -6 14 -4" stroke="#a8473f" stroke-width="2" fill="none" opacity=".85"/><ellipse cx="-39" cy="-4" rx="8" ry="5" fill="#fff" opacity=".6"/><path d="M -60 24 Q -32 38 -4 24" stroke="#5a4a3a" stroke-width="5" fill="none" opacity=".7"/>`;
      // mata kiri: normal, setengah terpejam (menatap licik)
      k += `<path d="M 14 4 Q 31 -6 48 4 Q 31 12 14 4 Z" fill="#fff" stroke="${INK}" stroke-width="3"/><circle cx="${33 + arah * 3}" cy="5" r="6" fill="${INK}"/><path d="M 12 3 Q 31 -10 50 3 L 50 -2 Q 31 -14 12 -2 Z" fill="${kl}"/><path d="M 12 3 Q 31 -8 50 3" stroke="${INK}" stroke-width="5" fill="none" stroke-linecap="round"/>`;
      if (tl > 0) k += `<text x="0" y="-38" font-size="22" font-weight="700" text-anchor="middle" font-family="DejaVu Sans, sans-serif" fill="#ffcf6a" opacity="${tl}" stroke="#3a1a0a" stroke-width="1.5" paint-order="stroke">ك ف ر</text><ellipse cx="0" cy="-44" rx="34" ry="14" fill="#ffcf6a" opacity="${0.15 * tl}"/>`;
      // senyum licik: satu sudut naik tinggi, satu datar
      const nk = 12 * sen;
      k += `<path d="M -26 46 Q -2 ${50 + 2 * sen} 18 ${42 - nk * 0.6} Q 26 ${38 - nk} 32 ${34 - nk}" stroke="${INK}" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M 30 ${30 - nk} q 6 4 4 10" stroke="${INK}" stroke-width="3" fill="none" opacity=".7"/>`;
      if (cb > 0) k += `<defs><linearGradient id="cbw" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ffe2a8" stop-opacity="${0.45 * cb}"/><stop offset=".45" stop-color="#ffe2a8" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="${0.35 * cb}"/></linearGradient></defs><ellipse rx="74" ry="84" fill="url(#cbw)"/>`;
    } else if (gaya === "anwar") {
      k += `<circle data-telinga="1" cx="-76" cy="6" r="15" fill="${KL}" stroke="${INK}" stroke-width="6"/><circle data-telinga="1" cx="76" cy="6" r="15" fill="${KL}" stroke="${INK}" stroke-width="6"/>`; // telinga
      k += `<ellipse rx="74" ry="84" fill="${KL}" stroke="${INK}" stroke-width="7"/>`;
      k += `<path d="M -72 -8 C -76 -40, -70 -62, -58 -70 L -54 -20 Z M 72 -8 C 76 -40, 70 -62, 58 -70 L 54 -20 Z" fill="#4a4048" opacity=".55"/>`; // samping tipis
      k += `<path d="M -62 -40 C -70 -100, 10 -118, 60 -92 C 78 -80, 76 -56, 66 -44 C 40 -64, 10 -70, -18 -58 C -34 -52, -50 -48, -62 -40 Z" fill="${INK}"/>`; // rambut atas disisir ke samping
      k += `<path d="M ${arah * 14 - 12} 62 Q ${arah * 14} 96 ${arah * 14 + 12} 62 Q ${arah * 14} 70 ${arah * 14 - 12} 62 Z" fill="${INK}"/>`; // jenggot dagu
    }
    // Penutup kepala dari kontrak karakter gabungan Python.
    const pfl = b.profil === "kanan" || b.profil === true || b.profil === "kiri";
    if (pfl && gaya !== "siluet" && b.rambut !== "kerudung" && b.penutup_kepala && b.penutup_kepala !== "tanpa" && !(P && P.peci)) {
      const WPK = b.warna_penutup || "#e8dcc4", gr = warna(WPK, "#000000", 0.16);
      if (b.penutup_kepala === "imamah") // lilitan sorban dari samping: kubah berlapis, ekor kain di belakang
        k += `<path d="M -84 -10 Q -96 -96 -16 -114 Q 52 -122 70 -56 Q 74 -36 62 -30 Q 0 -54 -84 -10 Z" fill="${WPK}" stroke="${INK}" stroke-width="6"/><path d="M -78 -36 Q 0 -86 64 -58 M -70 -64 Q 0 -104 50 -88" fill="none" stroke="${gr}" stroke-width="6" stroke-linecap="round"/><path d="M -80 -16 Q -104 40 -90 96 L -66 92 Q -76 40 -60 0 Z" fill="${WPK}" stroke="${INK}" stroke-width="5"/>`;
      else if (b.penutup_kepala === "kain") // ghutrah: kain menutup kepala dan menjuntai ke punggung, iqal hitam melingkar
        k += `<path d="M 60 -46 Q 40 -118 -24 -112 Q -96 -100 -98 -6 Q -100 70 -80 118 L -30 118 Q -40 60 -30 20 Q -20 -20 0 -34 Q 30 -52 60 -46 Z" fill="${WPK}" stroke="${INK}" stroke-width="6"/><path d="M 62 -58 Q 0 -78 -86 -40" fill="none" stroke="#1d1a22" stroke-width="12" stroke-linecap="round"/>`;
      else if (b.penutup_kepala === "kopiah")
        k += `<path d="M -74 -46 Q 0 -66 62 -50 L 58 -86 Q 0 -110 -70 -90 Z" fill="${WPK}" stroke="${INK}" stroke-width="6"/><path d="M -64 -58 Q 0 -76 56 -62" stroke="${gr}" stroke-width="5" fill="none"/>`;
    } else if (!belakang && gaya !== "siluet" && b.rambut !== "kerudung" && b.penutup_kepala && b.penutup_kepala !== "tanpa" && !(P && P.peci)) {
      const WPK = b.warna_penutup || "#e8dcc4";
      if (b.penutup_kepala === "imamah") {
        k += `<path d="M -70 -42 Q -84 -92 -48 -112 Q 0 -138 48 -112 Q 84 -92 70 -42 Q 0 -58 -70 -42 Z" fill="${WPK}" stroke="${INK}" stroke-width="6"/><path d="M -64 -72 Q 0 -96 64 -72 M -58 -54 Q 0 -76 58 -54" fill="none" stroke="${warna(WPK, "#000000", 0.16)}" stroke-width="7" stroke-linecap="round"/>`;
      } else if (b.penutup_kepala === "kain") { // ghutrah: kain menjuntai di kedua sisi wajah sampai bahu + iqal hitam
        k += `<path d="M -74 -40 Q -84 -100 -40 -118 Q 0 -134 40 -118 Q 84 -100 74 -40 L 98 112 L 58 118 Q 72 40 64 -16 Q 0 -50 -64 -16 Q -72 40 -58 118 L -98 112 Z" fill="${WPK}" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/><path d="M -76 -72 Q 0 -100 76 -72" fill="none" stroke="#1d1a22" stroke-width="12" stroke-linecap="round"/>`;
      } else if (b.penutup_kepala === "kopiah") {
        k += `<path d="M -68 -48 Q 0 -68 68 -48 L 62 -88 Q 0 -110 -62 -88 Z" fill="${WPK}" stroke="${INK}" stroke-width="6"/><path d="M -58 -58 Q 0 -76 58 -58" stroke="${warna(WPK, "#000000", 0.18)}" stroke-width="5" fill="none"/>`;
      }
    }
    const muka = ANW && !belakang && !b.profil && gaya !== "dajjal";
    if (muka && gaya !== "siluet") k += `<path d="M 18 -80 A 75 82 0 0 1 18 80 A 58 82 0 0 0 18 -80 Z" fill="#3a1f2a" opacity=".13"/>`; // bayangan separuh wajah
    if (muka && (wajah === "lelah" || wajah === "takut" || wajah === "marah" || wajah === "malu" || keringat > 0) && gaya !== "siluet") k += `<ellipse cx="${ex - 44}" cy="${30 + ey}" rx="16" ry="9" fill="#ff6b6b" opacity="${0.25 + 0.3 * PANAS}"/><ellipse cx="${ex + 44}" cy="${30 + ey}" rx="16" ry="9" fill="#ff6b6b" opacity="${0.25 + 0.3 * PANAS}"/>`; // pipi memerah
    if (muka) {
    if (HD) k += mukaHidup(b, { wajah, mata, ex, ey, arah, tunduk, t: ta, H, kl: b.kulit || KL }); else {
    // alis
    const al = { netral: [0, 0], bingung: [0, 0], takut: [-9, 7], sedih: [-8, 6], lega: [-2, 2], lelah: [-8, 8], marah: [12, -8] }[wajah] || [0, 0]; // [dalam, luar]
    [-1, 1].forEach((sg) => { const cx = ex + sg * 28, cy = -26 + ey - (wajah === "takut" ? 6 : 0) + (wajah === "bingung" && sg < 0 ? -10 : 0); const xd = cx - sg * 13, xl = cx + sg * 13; k += cewek ? `<path d="M ${xd} ${cy + al[0] + 2} Q ${cx} ${cy - 7 + (al[0] + al[1]) / 2} ${xl + sg * 3} ${cy + al[1] + 3}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`
      : `<line x1="${xd}" y1="${cy + al[0]}" x2="${xl}" y2="${cy + al[1]}" stroke="${INK}" stroke-width="${ANW ? 10 : 6}" stroke-linecap="round"/>`; });
    // mata
    [-1, 1].forEach((sg) => { const cx = ex + sg * 28, cy = 2 + ey; if (mata === "tutup" || kedip) k += `<path d="M ${cx - 10} ${cy} q 10 6 20 0" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`; else k += (ANW ? `<circle cx="${cx}" cy="${cy}" r="15" fill="#fff" stroke="${INK}" stroke-width="3"/>` : "") + `<circle cx="${cx + (ANW ? arah * 4 : 0)}" cy="${cy + (ANW && mata === "atas" ? -4 : ANW && mata === "bawah" ? 4 : 0)}" r="${ANW ? (wajah === "takut" ? 7 : 9) : (wajah === "takut" ? 9 : 7.5)}" fill="${INK}"/><circle cx="${cx + 2.5}" cy="${cy - 3}" r="2.4" fill="#fff"/>`; });
    // mulut
    const mx = arah * 18, my = 38 + tunduk * 8;
    const bic = (b.bicara || []).some(([a0, a1]) => t >= a0 && t <= a1);
    if (bic) { const o = 0.35 + 0.65 * Math.abs(Math.sin(t * 17 + (b.ph || 0))); k += `<ellipse cx="${mx}" cy="${my + 4}" rx="${12 + 3 * o}" ry="${4 + 11 * o}" fill="${INK}"/><ellipse cx="${mx}" cy="${my + 8 + 4 * o}" rx="${6 + 2 * o}" ry="${2 + 2 * o}" fill="#c95b5b"/>`; } else
    if (cewek && (wajah === "netral" || wajah === "lega")) k += wajah === "lega"
      ? `<path d="M ${mx - 13} ${my - 1} Q ${mx} ${my + 11} ${mx + 13} ${my - 1}" fill="none" stroke="#7a3a3a" stroke-width="4.5" stroke-linecap="round"/>`
      : `<path d="M ${mx - 9} ${my} Q ${mx} ${my + 5} ${mx + 9} ${my}" fill="none" stroke="#7a3a3a" stroke-width="4.5" stroke-linecap="round"/>`;
    else k += { netral: `<line x1="${mx - 12}" y1="${my}" x2="${mx + 12}" y2="${my}" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`,
      bingung: `<ellipse cx="${mx + 8}" cy="${my}" rx="7" ry="9" fill="${INK}"/>`,
      takut: `<path d="M ${mx - 16} ${my + 6} q 8 -12 16 0 q 8 12 16 0" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`,
      sedih: `<path d="M ${mx - 14} ${my + 6} Q ${mx} ${my - 6} ${mx + 14} ${my + 6}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`,
      lega: `<path d="M ${mx - 16} ${my - 2} Q ${mx} ${my + 14} ${mx + 16} ${my - 2}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`,
      marah: `<path d="M ${mx - 18} ${my + 8} Q ${mx} ${my - 4} ${mx + 18} ${my + 8} L ${mx + 14} ${my + 14} Q ${mx} ${my + 6} ${mx - 14} ${my + 14} Z" fill="${INK}"/><path d="M ${mx - 12} ${my + 6} L ${mx + 12} ${my + 6}" stroke="#fff" stroke-width="4"/>`,
      lelah: `<ellipse cx="${mx}" cy="${my + 4}" rx="${13 + Math.sin(t * 5 + (b.ph || 0)) * 3}" ry="${11 + Math.sin(t * 5 + (b.ph || 0)) * 5}" fill="${INK}"/><ellipse cx="${mx}" cy="${my + 10}" rx="7" ry="4" fill="#c95b5b"/>` }[wajah] || "";
    if (wajah === "lelah") [-1, 1].forEach((sg) => { const cx = ex + sg * 28, cy = 2 + ey; k += `<path d="M ${cx - 17} ${cy - 1} Q ${cx} ${cy - 20} ${cx + 17} ${cy - 1} Z" fill="${b.kulit || KL}" stroke="${INK}" stroke-width="4"/>`; }); // kelopak berat
    }
    // keringat
    if (keringat > 0) [[-62, -20, 0], [58, -34, 0.7], [-50, 10, 1.4], [40, -60, 0.4], [-30, -64, 1.1], [64, 14, 0.9]].slice(0, keringat > 1 ? 6 : 3).forEach(([dx, dy, ph]) => { const q = ((t * 0.9 + ph) % 1.6) / 1.6; k += `<path transform="translate(${dx} ${dy + q * 70})" d="M 0 -12 Q 9 2 0 8 Q -9 2 0 -12 Z" fill="#9fdcff" stroke="${INK}" stroke-width="3" opacity="${Math.min(1, keringat) * (1 - q)}"/>`; });
    }
    if (muka && cewek && gaya !== "siluet") { // (27 Nov, sederhana & santun) tanpa bulu mata/riasan: sorot mata lembut + rona tipis alami
      [-1, 1].forEach((sg) => { const cx = ex + sg * 28, cy = 2 + ey;
        if (mata !== "tutup" && !HD) k += `<circle cx="${cx - 3}" cy="${cy + 4}" r="1.8" fill="#fff" opacity=".9"/>`; // sorot mata kedua, lembut
        k += `<ellipse cx="${ex + sg * 44}" cy="${26 + ey}" rx="13" ry="7" fill="#f2a0a0" opacity=".18"/>`; });
    }
    if (muka && gaya === "umum") { // aksesori akun komedi: kumis, kacamata, earphone, pipi
      const mx2 = arah * 18, my2 = 38 + tunduk * 8;
      if (b.pipi) k += `<ellipse cx="${ex - 46}" cy="${30 + ey}" rx="15" ry="9" fill="#ff8a8a" opacity=".45"/><ellipse cx="${ex + 46}" cy="${30 + ey}" rx="15" ry="9" fill="#ff8a8a" opacity=".45"/>`;
      if (b.kumis) k += `<path d="M ${mx2} ${my2 - 14} C ${mx2 - 14} ${my2 - 24}, ${mx2 - 40} ${my2 - 20}, ${mx2 - 46} ${my2 - 2} C ${mx2 - 30} ${my2 - 10}, ${mx2 - 14} ${my2 - 6}, ${mx2} ${my2 - 8} C ${mx2 + 14} ${my2 - 6}, ${mx2 + 30} ${my2 - 10}, ${mx2 + 46} ${my2 - 2} C ${mx2 + 40} ${my2 - 20}, ${mx2 + 14} ${my2 - 24}, ${mx2} ${my2 - 14} Z" fill="${b.kumis === true ? (b.warna_rambut || INK) : b.kumis}"/>`;
      if (b.kacamata) { const hit = b.kacamata === "hitam", tb = b.kacamata === "tebal" ? 8 : 5; [-1, 1].forEach((sg) => { k += `<circle cx="${ex + sg * 28}" cy="${2 + ey}" r="${hit ? 22 : 21}" fill="${hit ? "#1d1a22" : "#dff3ff"}" fill-opacity="${hit ? 0.95 : 0.25}" stroke="${INK}" stroke-width="${tb}"/>`; }); k += `<line x1="${ex - 7}" y1="${ey}" x2="${ex + 7}" y2="${ey}" stroke="${INK}" stroke-width="${tb}"/><line x1="${ex - 49}" y1="${ey}" x2="-74" y2="-6" stroke="${INK}" stroke-width="${tb - 1}"/><line x1="${ex + 49}" y1="${ey}" x2="74" y2="-6" stroke="${INK}" stroke-width="${tb - 1}"/>`; if (hit) k += `<path d="M ${ex - 40} ${ey - 8} l 10 -6 M ${ex + 16} ${ey - 8} l 10 -6" stroke="#fff" stroke-width="4" opacity=".6"/>`; }
      if (b.earphone) k += `<circle cx="-78" cy="14" r="10" fill="#ffffff" stroke="${INK}" stroke-width="3"/><circle cx="78" cy="14" r="10" fill="#ffffff" stroke="${INK}" stroke-width="3"/><path d="M -78 24 Q -70 90 -20 120 M 78 24 Q 70 90 20 120" stroke="#ffffff" stroke-width="3" fill="none"/>`;
    }
    if (HD && b.simbol) k += simbolH(b.simbol, ta);
    const pc = P && P.peci; // peci (kopiah) di kepala
    if (pc && !belakang && b.rambut !== "kerudung") k += `<path d="M -70 -44 L -64 -98 Q 0 -114 64 -98 L 70 -44 Q 0 -58 -70 -44 Z" fill="${pc === true ? "#1d1520" : pc === "putih" ? "#ffffff" : pc}" stroke="${INK}" stroke-width="6"/>` + (pc === "#ffffff" || pc === "putih" ? `<path d="M -60 -60 Q 0 -72 60 -60" stroke="#d8d2c4" stroke-width="4" fill="none"/>` : "");
    k += `</g>`;
    if (!RIG && (lengan === "doa" || lengan === "beri" || lengan === "tolak")) {
      const lk = (sg, ex2, ey2, ex3, ey3) => `<polyline points="${sg * 62},${-360 + nafas} ${ex2},${ey2 + nafas} ${ex3},${ey3 + nafas}" fill="none" stroke="${BD}" stroke-width="36" stroke-linecap="round" stroke-linejoin="round"/>`;
      if (lengan === "doa") { g = g.replace(lenganKiri, ""); lenganKanan = lk(-1, -96, -250, -56, -330) + lk(1, 96, -250, 56, -330) + `<ellipse cx="-50" cy="${-338 + nafas}" rx="26" ry="16" fill="${b.kulit || KL}" stroke="${INK}" stroke-width="5"/><ellipse cx="50" cy="${-338 + nafas}" rx="26" ry="16" fill="${b.kulit || KL}" stroke="${INK}" stroke-width="5"/>`; }
      if (lengan === "beri") lenganKanan = lk(1, 150, -300, 250, -300) + `<circle cx="262" cy="${-300 + nafas}" r="20" fill="${b.kulit || KL}" stroke="${INK}" stroke-width="5"/>`;
      if (lengan === "tolak") lenganKanan = lk(1, 160, -330, 170, -450) + `<ellipse cx="172" cy="${-470 + nafas}" rx="22" ry="32" fill="${b.kulit || KL}" stroke="${INK}" stroke-width="5"/>`;
      g += lenganKanan; lenganKanan = "";
    }
    const am = v(b.air_mata, t, d, 0);
    if (am > 0 && muka) { k = k.replace(/<\/g>$/, ""); [-1, 1].forEach((sg) => { const cx = ex + sg * 30, cy = 14 + ey, L = 70 * am; k += `<path d="M ${cx} ${cy} q ${sg * 4} ${L / 2} 0 ${L}" stroke="#9fdcff" stroke-width="9" fill="none" stroke-linecap="round" opacity=".9"/>`; const q = (t * 0.8 + (sg > 0 ? 0.5 : 0)) % 1; k += `<path transform="translate(${cx} ${cy + L + q * 60})" d="M 0 -10 Q 8 2 0 8 Q -8 2 0 -10 Z" fill="#9fdcff" opacity="${1 - q}"/>`; }); k += `</g>`; }
    if (!RIG && lengan === "lindungi") lenganKanan = `<polyline points="62,${-360 + nafas} 128,${-470 + nafas} ${hx + 30},${hy - 66}" fill="none" stroke="${BD}" stroke-width="36" stroke-linecap="round" stroke-linejoin="round"/><ellipse cx="${hx + 22}" cy="${hy - 66}" rx="42" ry="20" fill="${BD}"/>`;
    const fid = b.utama ? "rimU" : "rim";
    if (!P && b.gaya !== "siluet" && C.badan !== "siluet") { const R = rng(b.id * 7 + 3); for (let i = 0; i < 14; i++) g += `<circle cx="${-55 + R() * 110}" cy="${-380 + R() * 360 + nafas}" r="${2 + R() * 4}" fill="#e9d2b8" opacity=".35"/>`; } // debu tanah di badan
    if (!RIG && lengan === "lindungi") { k += lenganKanan; lenganKanan = ""; }
    if (RG) k = `<g transform="${RG.T}"><g transform="rotate(${RG.kepala} 0 -400)">${k}</g></g>` + RG.depan;
    let isi = (b.gaya === "siluet" ? g + lenganKanan : `<g filter="url(#${fid})">${g}${lenganKanan}</g>`) + k;
    const gen = v(b.genangan, t, d, 0); // tinggi cairan (px dari telapak): mata kaki 35, lutut 110, pinggang 210, mulut 440
    if (gen > 0) { const w = Math.sin(t * 3) * 6; isi += `<path d="M -105 0 L -105 ${-gen + w} Q -52 ${-gen - 10 - w} 0 ${-gen + w} T 105 ${-gen + w} L 105 0 Z" fill="#ff9a3a" opacity=".72"/><path d="M -105 ${-gen + w} Q -52 ${-gen - 10 - w} 0 ${-gen + w} T 105 ${-gen + w}" fill="none" stroke="#ffe3a8" stroke-width="6"/>`; }
    const potong = b.potong != null ? b.potong : 0; // garis tanah relatif kaki (untuk bangkit dari tanah)
    let label = ""; if (b.nama) { const w2 = b.nama.length * 25 + 60; label = `<g font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" text-anchor="middle"><rect x="${-w2 / 2}" y="30" width="${w2}" height="74" rx="37" fill="#1d1520" opacity=".8"/><text y="80" font-size="44" fill="#ffe6a0">${esc(b.nama)}</text></g>`; } // di luar clip (dulu terpotong)
    const opb = v(b.op, t, d, 1); if (opb <= 0.01) return "";
    if (H) { x += H.dx; y += H.dy; s *= H.sc; isi = `<g transform="scale(${1 - H.sq * 0.7} ${1 + H.sq})">${isi}</g>`; }
    const byg = (C.bayangan === false || b.bayangan === false || gaya === "siluet" || naik < 0.98 || potong > 0 || gen > 0 || (RG && RG.guling)) ? "" : `<ellipse cx="0" cy="6" rx="${b.bayangan > 0 ? b.bayangan : 92}" ry="15" fill="#000" opacity=".2"/>`; // standar visual butir 5: bayangan lembut di pijakan (matikan: bayangan:false di boneka atau cerita)
    if (window.__catatBoneka) { // hanya aktif saat alat uji tokoh menyiapkannya; tidak memengaruhi render biasa
      const pm = (b.profil === "kanan" || b.profil === true || b.profil === "kiri") && !!RIG && !RIG.guling;
      window.__catatBoneka.push({ id: b.id, t, x, y, s, tubuh, arah, tunduk, profil: b.profil || null, belakang: !!belakang,
        badan_samping: pm, rig: !!RIG, aksi: RIG && RIG._aksi || b.aksi || null, sendi: RG ? RG.sendi : null, guling: RG ? RG.guling || 0 : 0,
        telinga: (k.match(/data-telinga="1"/g) || []).length, kepala: [hx, hy],
        kait_galat: kaitL && RG && RG.sendi ? (() => { // jarak (px lokal) tangan/kaki ke titik kait benda; dipakai uji A6
          const jr = (a, q) => Math.hypot(a[0] - q[0], a[1] - q[1]), Sd = RG.sendi;
          const pg = kaitL.pegang ? Math.max(...Sd.lengan.map((Lg, i) => jr(Lg[2], keT(kaitL.pegang[i] || kaitL.pegang[0], RIG)))) : null;
          const pj = kaitL.pijak && Sd.kaki.length ? Math.max(...Sd.kaki.map((Kk, i) => jr(Kk[2], kaitL.pijak[i] || kaitL.pijak[0]))) : null;
          return { pegang: pg, pijak: pj }; })() : null });
    }
    const cermin = b.cermin || b.profil === "kiri"; // tampak samping menghadap kiri = cermin tampak kanan
    return `<g opacity="${opb}" transform="translate(${x} ${y}) scale(${cermin ? -s : s} ${s})">${byg}<clipPath id="kp${b.id || 0}"><rect x="-400" y="-1400" width="800" height="${1400 - potong}"/></clipPath><g clip-path="url(#kp${b.id || 0})"><g transform="translate(0 ${tubuh})${RG && RG.guling ? ` rotate(${RG.guling} 0 -200)` : ""}">${isi}</g></g>${cermin && label ? `<g transform="scale(-1 1)">${label}</g>` : label}</g>`;
  }

  // teks hook bergaya sampul "sapuan kuas": {gaya:"sapuan", teks:"A\nB\nC", warna:["#ffd93a","#fff","#e8141c"], y (tengah blok), ukuran, pita:["baris hitam","baris merah"], pita_y, garis:true, kilat:true}
  function sapuan(o, t) {
    const tl = t - (o.at || 0), R = rng(o.seed || 7), baris = String(o.teks).split("\n"), n = baris.length, uk0 = o.ukuran || 130, lh0 = 1.12;
    const WR = ["#ffd93a", "#ffffff", "#e8141c"], war = o.warna || WR, y = o.y || 420;
    const uk = baris.map((b) => Math.min(uk0, 900 / (0.7 * Math.max(4, b.length)))), tot = uk.reduce((a, b) => a + b * lh0, 0);
    const top = y - tot / 2, ya = top + uk[0] * 0.92;
    const masuk = o.at ? (tl < 0.25 ? 1.5 - 0.5 * halus(tl / 0.25) : 1) : 1, denyut = 1 + 0.012 * Math.sin(t * 4.5), op = o.at ? clamp(tl / 0.1) : 1;
    const blob = (x0, x1, y0, y1, j) => { let d = `M ${x0 + R() * j} ${y0 + R() * j}`; for (let x = x0; x < x1; x += 50) d += ` L ${x + R() * 16} ${y0 + (R() - 0.5) * j * 2}`; d += ` L ${x1 - R() * j} ${y0 + R() * j}`; for (let yy = y0; yy < y1; yy += 50) d += ` L ${x1 + (R() - 0.5) * j * 2} ${yy}`; d += ` L ${x1 - R() * j} ${y1 - R() * j}`; for (let x = x1; x > x0; x -= 50) d += ` L ${x - R() * 16} ${y1 + (R() - 0.5) * j * 2}`; d += ` L ${x0 + R() * j} ${y1 - R() * j}`; for (let yy = y1; yy > y0; yy -= 50) d += ` L ${x0 + (R() - 0.5) * j * 2} ${yy}`; return d + " Z"; };
    let g = `<g opacity="${op}" transform="translate(540 ${y}) scale(${masuk * denyut}) translate(-540 ${-y})" font-family="DejaVu Sans, Arial, sans-serif" font-weight="900" text-anchor="middle">`;
    g += `<path d="${blob(36, 1044, top - 14, top + tot + 22, 20)}" fill="#0b0a10" opacity=".93"/>`;
    if (o.kilat !== false) [[1, 1], [-1, 1]].forEach(([sx]) => { for (let k = 0; k < 3; k++) { const a = (-70 + k * 28) * Math.PI / 180, x0 = 540 + sx * 450 + Math.cos(a) * sx * 30, y0 = top - 30 + Math.sin(a) * 40; g += `<line x1="${x0}" y1="${y0}" x2="${x0 + sx * Math.cos(a) * 62}" y2="${y0 + Math.sin(a) * 62}" stroke="#ffd93a" stroke-width="13" stroke-linecap="round"/>`; } });
    let yy = ya;
    baris.forEach((b, i) => { g += `<text x="540" y="${yy}" font-size="${uk[i]}" fill="${war[Math.min(i, war.length - 1)]}" stroke="#0b0a10" stroke-width="${uk[i] * 0.1}" stroke-linejoin="round" paint-order="stroke">${esc(b)}</text>`; yy += uk[i] * (lh0 - 0.92) + (uk[i + 1] || 0) * 0.92; }); // (16 Nov) jarak baris memakai ukuran baris berikutnya (dulu baris kecil di atas baris besar bertumpuk)
    if (o.garis !== false) g += `<path d="M 270 ${top + tot + 14} Q 540 ${top + tot + 30} 810 ${top + tot + 12}" stroke="#ffd93a" stroke-width="11" fill="none" stroke-linecap="round"/>`;
    if (o.pita) { const py = o.pita_y || (top + tot + 160), L = o.pita, uk2 = Math.min(78, 900 / (0.7 * Math.max(...L.map((x) => x.length))));
      g += `<path d="${blob(30, 1050, py - uk2 * 0.95, py + uk2 * (L.length - 1) * 1.1 + uk2 * 0.55, 18)}" fill="#ffd93a" stroke="#0b0a10" stroke-width="5"/>`;
      L.forEach((x, i) => { g += `<text x="540" y="${py + i * uk2 * 1.1}" font-size="${uk2}" fill="${i === L.length - 1 ? "#d9141c" : "#0b0a10"}" ${i === L.length - 1 ? 'stroke="#0b0a10" stroke-width="2"' : ""}>${esc(x)}</text>`; });
      g += `<path d="M 250 ${py + uk2 * (L.length - 1) * 1.1 + uk2 * 0.32} Q 540 ${py + uk2 * (L.length - 1) * 1.1 + uk2 * 0.42} 830 ${py + uk2 * (L.length - 1) * 1.1 + uk2 * 0.3}" stroke="#d9141c" stroke-width="7" fill="none" stroke-linecap="round"/>`; }
    if (o.akun) { const ay = o.akun_y || 1660, w = o.akun.length * 24 + 70; g += `<rect x="${540 - w / 2}" y="${ay - 44}" width="${w}" height="66" rx="33" fill="#0b0a10" opacity=".88"/><text x="540" y="${ay + 4}" font-size="40" font-weight="800" fill="#ffd93a">${esc(o.akun)}</text>`; }
    return g + "</g>";
  }
  // lencana sumber bergaya neon: {gaya:"neon", teks:"HR. IBNU MAJAH 4080", sub?:"disahihkan Al-Albani", warna:"#ffd27a", y, ukuran, at, sampai}
  // masuk berkedip (tabung neon menyala), lalu denyut pelan; padam dengan meredup di ujung `sampai`.
  function neon(o, t) {
    const tl = t - (o.at || 0), F = o.ukuran || 36, c = o.warna || "#ffd27a", y = o.y || 240, L = String(o.teks || "");
    const kedip = tl < 0.55 ? ([1, 0.15, 1, 0.25, 0.9, 0.2, 1][Math.min(6, Math.floor(tl / 0.08))]) : 1;
    const padam = o.sampai != null ? clamp((o.sampai - t) / 0.35) : 1;
    const op = kedip * padam * (0.9 + 0.1 * Math.sin(t * 3.2)) * (tl < 0.55 ? 1 : 1);
    const W = Math.max(L.length, o.sub ? o.sub.length * 0.8 : 0) * F * 0.64 + 70, H = F * 1.9 + (o.sub ? F * 0.85 : 0), x0 = 540 - W / 2, y0 = y - F * 1.25;
    const id = "ng" + Math.round((o.at || 0) * 100);
    let g = `<g opacity="${clamp(op)}" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" text-anchor="middle">`;
    g += `<defs><filter id="${id}" x="-30%" y="-80%" width="160%" height="260%"><feGaussianBlur stdDeviation="12"/></filter></defs>`;
    g += `<rect x="${x0}" y="${y0}" width="${W}" height="${H}" rx="${H / 2}" fill="#07060d" fill-opacity=".72"/>`;
    g += `<rect x="${x0}" y="${y0}" width="${W}" height="${H}" rx="${H / 2}" fill="none" stroke="${c}" stroke-width="20" opacity=".95" filter="url(#${id})"/>`;
    g += `<rect x="${x0}" y="${y0}" width="${W}" height="${H}" rx="${H / 2}" fill="none" stroke="${c}" stroke-width="4"/>`;
    g += `<rect x="${x0 + 7}" y="${y0 + 7}" width="${W - 14}" height="${H - 14}" rx="${(H - 14) / 2}" fill="none" stroke="#ffffff" stroke-width="1.6" opacity=".55"/>`;
    g += `<text x="540" y="${y0 + F * 1.25}" font-size="${F}" fill="${c}" filter="url(#${id})" opacity=".8">${esc(L)}</text><text x="540" y="${y0 + F * 1.25}" font-size="${F}" fill="#fffaf0">${esc(L)}</text>`;
    if (o.sub) g += `<text x="540" y="${y0 + F * 2.1}" font-size="${F * 0.72}" font-weight="700" fill="${c}" opacity=".95">${esc(o.sub)}</text>`;
    return g + "</g>";
  }
  function teks(list, t) {
    return (list || []).map((o) => {
      const tl = t - (o.at || 0); if (tl < 0 || (o.sampai != null && t > o.sampai)) return "";
      if (o.gaya === "sapuan") return sapuan(o, t);
      if (o.gaya === "neon") return neon(o, t);
      const op = o.at ? clamp(tl / 0.3) : 1, y = o.y || 360, ukuran = o.ukuran || 82;
      const baris = String(o.teks).split("\n");
      let s = `<g opacity="${op}" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" text-anchor="middle">`;
      baris.forEach((b, i) => { const yy = y + i * ukuran * 1.15; s += `<text x="540" y="${yy}" font-size="${ukuran}" fill="none" stroke="${INK}" stroke-width="16" stroke-linejoin="round">${esc(b)}</text><text x="540" y="${yy}" font-size="${ukuran}" fill="${o.warna || "#fff"}">${esc(b)}</text>`; });
      if (o.sub) { const yy = y + baris.length * ukuran * 1.15 + 6; s += `<rect x="${540 - o.sub.length * 13}" y="${yy - 40}" width="${o.sub.length * 26}" height="56" rx="28" fill="${INK}" opacity=".75"/><text x="540" y="${yy}" font-size="40" font-weight="700" fill="#ffd27a">${esc(o.sub)}</text>`; }
      return s + "</g>";
    }).join("");
  }


  // teks besar tengah kata-per-kata: C.tengah = [{t0, t1, kata:[[t, kata]], y, ukuran, maks, sorot:{kata: warna}}] (waktu absolut)
  function tengah(L, t) {
    return (L || []).map((o) => {
      if (t < o.t0 - 0.05 || t > o.t1 + (o.tahan != null ? o.tahan : 0.25)) return "";
      const F = o.ukuran || 96, maks = o.maks || 13, y = o.y || 1240, kata = o.kata.filter((k) => t >= k[0] - 0.04);
      if (!kata.length) return "";
      const baris = [[]]; kata.forEach((k) => { const cur = baris[baris.length - 1], pj = cur.reduce((a, q) => a + q[1].length + 1, 0); if (cur.length && pj + k[1].length > maks) baris.push([k]); else cur.push(k); });
      const kini = kata[kata.length - 1], y0 = y - ((baris.length - 1) * F * 1.12) / 2;
      let s = `<g font-family="DejaVu Sans, Arial, sans-serif" font-weight="900" text-anchor="middle">`;
      baris.forEach((bs, bi) => {
        const yy = y0 + bi * F * 1.12;
        const isi = bs.map((k) => { const pol = k[1].replace(/[^\p{L}\p{N}]/gu, "").toLowerCase(), sw = o.sorot && o.sorot[pol]; const c = sw || (k === kini ? "#ffd23f" : "#ffffff"); const pop = k === kini ? 1 + 0.18 * clamp(1 - (t - k[0]) / 0.15) : 1; return `<tspan fill="${c}" font-size="${F * pop}">${esc(k[1])}</tspan>`; }).join(" ");
        s += `<text x="540" y="${yy}" font-size="${F}" stroke="${INK}" stroke-width="18" stroke-linejoin="round" paint-order="stroke">${isi}</text>`;
      });
      return s + "</g>";
    }).join("");
  }

  // meteran keringat di sisi kanan (waktu absolut): C.meteran = {at, sampai, nilai:[[t,0..1]], label, tanda:[..]}
  function meteran(M, t) {
    if (t < (M.at || 0) || (M.sampai != null && t > M.sampai)) return "";
    const tl = t - (M.at || 0), op = clamp(tl / 0.4) * (M.sampai != null ? clamp((M.sampai - t) / 0.4) : 1);
    const n = v(M.nilai, t, 1, 0), x = 930, y0 = 1180, y1 = 560, h = y0 - y1, yy = y0 - h * n;
    const tanda = M.tanda || ["mata kaki", "lutut", "pinggang", "mulut"], posisi = M.posisi || [0.08, 0.25, 0.48, 1];
    let s = `<g opacity="${op}" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800">`;
    s += `<rect x="${x - 34}" y="${y1 - 20}" width="68" height="${h + 40}" rx="34" fill="${INK}" opacity=".7"/>`;
    s += `<rect x="${x - 22}" y="${yy}" width="44" height="${y0 - yy + 8}" rx="22" fill="#ff9a3a"/>`;
    tanda.forEach((tk, i) => { const ty = y0 - h * posisi[i], aktif = n >= posisi[i] - 0.01; s += `<line x1="${x - 34}" y1="${ty}" x2="${x - 54}" y2="${ty}" stroke="#fff" stroke-width="4"/><text x="${x - 62}" y="${ty + 10}" font-size="30" text-anchor="end" fill="${aktif ? "#ffd27a" : "#fff"}" stroke="${INK}" stroke-width="8" paint-order="stroke">${esc(tk)}</text>`; });
    const tanya = n < 0.02 || M.tanya;
    s += `<text x="${x}" y="${y1 - 46}" font-size="34" text-anchor="middle" fill="#fff" stroke="${INK}" stroke-width="8" paint-order="stroke">${esc(M.label || "Keringatmu")}</text>`;
    if (tanya) s += `<text x="${x}" y="${(y0 + y1) / 2 + 30}" font-size="96" text-anchor="middle" fill="#fff" stroke="${INK}" stroke-width="10" paint-order="stroke" opacity="${0.6 + 0.4 * Math.sin(t * 4)}">?</text>`;
    return s + "</g>";
  }

  // penanda urutan: C.urutan = {at, sampai, n:7, aktif:[[t, k]], rahasia: indeks yang tampil "?" sampai aktif}
  function urutan(U, t) {
    if (t < (U.at || 0) || (U.sampai != null && t > U.sampai)) return "";
    const op = clamp((t - (U.at || 0)) / 0.4) * (U.sampai != null ? clamp((U.sampai - t) / 0.4) : 1);
    const n = U.n || 7, k = v(U.aktif, t, 1, 0), gap = 118, x0 = 540 - (gap * (n - 1)) / 2, y = 232;
    let s = `<g opacity="${op}" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800" text-anchor="middle">`;
    for (let i = 1; i <= n; i++) { const x = x0 + (i - 1) * gap, on = k >= i, kini = Math.round(k) === i && on, r = kini ? 46 + 4 * Math.sin(t * 6) : 40;
      s += `<circle cx="${x}" cy="${y}" r="${r}" fill="${on ? (kini ? "#ffd27a" : "#7fd3e8") : "#1d1520"}" stroke="${on ? "#fff" : "#7a6a80"}" stroke-width="5" opacity="${on ? 1 : 0.75}"/>`;
      s += `<text x="${x}" y="${y + 15}" font-size="42" fill="${on ? "#1d1520" : "#cbbfd0"}">${i === U.rahasia && !on ? "?" : i}</text>`; }
    return s + "</g>";
  }

  // gelembung percakapan: C.dialog = [{t0, t1, kata:[[t, kata]], x, y, ekor:[x, y], nama}] (waktu absolut)
  function gelembung(D, t) {
    return (D || []).map((o) => {
      if (t < o.t0 - 0.15 || t > o.t1 + 0.5 || (o.habis != null && t >= o.habis)) return "";
      const op = clamp((t - o.t0 + 0.15) / 0.2) * clamp((o.t1 + 0.5 - t) / 0.25), pop = 1 + 0.08 * clamp(1 - (t - o.t0 + 0.15) / 0.25);
      const kata = o.kata, F = o.ukuran || 54, maks = o.maks || 20, baris = [[]];
      kata.forEach((k, i) => { const cur = baris[baris.length - 1], pj = cur.reduce((a, j) => a + kata[j][1].length + 1, 0); if (cur.length && pj + k[1].length > maks) baris.push([i]); else cur.push(i); });
      let kini = -1; kata.forEach((k, i) => { if (t >= k[0]) kini = i; });
      const lebarBaris = baris.map((bs) => bs.reduce((a, j) => a + kata[j][1].length + 1, 0) * F * 0.62);
      const W = Math.min(960, Math.max(...lebarBaris) + 90), H = baris.length * F * 1.25 + 70, x = clamp(o.x, W / 2 + 30, 1050 - W / 2), y = o.y;
      const [ex, ey] = o.ekor || [x, y + H / 2 + 80], bx = clamp(ex, x - W / 2 + 60, x + W / 2 - 60);
      let s = `<g opacity="${op}" transform="translate(${x} ${y}) scale(${pop}) translate(${-x} ${-y})" font-family="DejaVu Sans, Arial, sans-serif" font-weight="800">`;
      s += `<path d="M ${bx - 34} ${y + H / 2 - 4} L ${ex} ${ey} L ${bx + 34} ${y + H / 2 - 4} Z" fill="#fffaf0" stroke="${INK}" stroke-width="7" stroke-linejoin="round"/>`;
      s += `<rect x="${x - W / 2}" y="${y - H / 2}" width="${W}" height="${H}" rx="${Math.min(60, H / 2)}" fill="#fffaf0" stroke="${INK}" stroke-width="7"/>`;
      s += `<rect x="${bx - 30}" y="${y + H / 2 - 12}" width="60" height="14" fill="#fffaf0"/>`;
      if (o.nama) s += `<rect x="${x - W / 2 + 24}" y="${y - H / 2 - 30}" width="${o.nama.length * 21 + 40}" height="54" rx="27" fill="${o.warna || "#ff9a3a"}" stroke="${INK}" stroke-width="5"/><text x="${x - W / 2 + 44}" y="${y - H / 2 + 8}" font-size="32" fill="${INK}">${esc(o.nama)}</text>`;
      baris.forEach((bs, bi) => {
        const yy = y - H / 2 + 35 + F * 0.95 + bi * F * 1.25;
        s += `<text x="${x}" y="${yy}" font-size="${F}" text-anchor="middle">` + bs.map((j) => `<tspan fill="${j === kini ? "#d9480f" : j < kini ? INK : "#8a7a80"}">${esc(kata[j][1])}</tspan>`).join(" ") + `</text>`;
      });
      return s + "</g>";
    }).join("");
  }

  function gambar(t) {
    let S = SH[0]; SH.forEach((s) => { if (t >= s.at) S = s; });
    const tl = t - S.at, d = Math.max(0.1, Math.min(S.akhir, window.__durasi || 1e9) - S.at);
    const p = v(S.langit, tl, d, 0), h = v(S.horizon, tl, d, 1150); MALAM = v(S.malam, tl, d, 0); PAL = PALET[S.palet] || null;
    RIM = warna("#8f9bff", "#ffb347", p); PANAS = p;
    BADAN = C.badan === "siluet" ? "#3b2a40" : warna("#6b5560", "#8a4a36", p); // tanah liat berdebu: kelabu saat bangkit, kemerahan terbakar saat terik
    BAYANG = PAL ? campur(warna(PAL.tanah[1], "#1d1520", 0.55), "#0b1030", MALAM) : CERAH ? campur(warna("#8a5a44", "#9a5a36", p), "#0b1030", MALAM) : warna("#4a3a48", "#5a3328", p);
    let z = v(S.kamera && S.kamera.z, tl, d, 1), kx = v(S.kamera && S.kamera.x, tl, d, 540), ky = v(S.kamera && S.kamera.y, tl, d, 960);
    ((S.kamera && S.kamera.hentak) || []).forEach(([th, bs]) => { if (tl >= th) z *= 1 + bs * balik((tl - th) / 0.16, 1.6); }); // zoom hentak: [[detik, besar 0.08-0.12]], lalu ditahan
    ((S.kamera && S.kamera.guncang) || []).forEach(([th, px]) => { const q = tl - th; if (q >= 0 && q < 0.4) { kx += (px * Math.exp(-q * 12) * Math.sin(q * 70)) / z; ky += (px * Math.exp(-q * 12) * Math.cos(q * 55)) / z; } });
    let isi = langit(p) + `<defs><filter id="rim" x="-20%" y="-20%" width="140%" height="140%"><feMorphology in="SourceAlpha" operator="dilate" radius="5" result="m"/><feFlood flood-color="${INK}"/><feComposite in2="m" operator="in"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter><filter id="rimU" x="-20%" y="-20%" width="140%" height="140%"><feMorphology in="SourceAlpha" operator="dilate" radius="5" result="m"/><feFlood flood-color="${INK}"/><feComposite in2="m" operator="in"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter><filter id="kb8" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="8"/></filter><filter id="kb4" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="4"/></filter></defs>`;
    (S.benda || []).filter((o) => o.jenis === "bintang" || o.jenis === "bulan" || o.belakang).forEach((o) => { isi += o.hias ? `<g data-hias="1">${benda(o, tl, d)}</g>` : benda(o, tl, d); });
    if (S.latar_gambar) { // lukisan latar (AI) penuh layar; S.redup 0-1 menggelapkan agar tokoh menonjol
      isi += `<image href="${S.latar_gambar}" x="0" y="0" width="1080" height="1920" preserveAspectRatio="xMidYMid slice"/>`;
      if (S.redup) isi += `<rect width="1080" height="1920" fill="#000" opacity="${v(S.redup, tl, d, 0)}"/>`;
    } else if (S.ruang) isi += ruang(S.ruang, t);
    else { if (S.matahari) isi += matahari(S.matahari, tl, d);
    if (CERAH && !PAL) isi += cakrawala(h, tl); isi += tanah(h, p); }
    if (S.panas) isi += panas(tl, h, v(S.panas, tl, d, 1));
    if (S.naungan) isi += naungan(S.naungan, tl, d);
    if (S.retak) isi += retak(S.retak, tl, d);
    if (S.resap) isi += resap(S.resap, tl, d, h);
    if (S.kerumunan) isi += kerumunan(S.kerumunan, h, tl);
    (S.benda || []).filter((o) => !(o.jenis === "bintang" || o.jenis === "bulan" || o.belakang) && !o.depan).forEach((o) => { isi += o.hias ? `<g data-hias="1">${benda(o, tl, d)}</g>` : benda(o, tl, d); });
    (S.boneka || []).forEach((b, i) => {
      // Ikatan kendaraan membuat pengendara mengikuti posisi motor setiap frame.
      // Setelah lepas_kendaraan_at, lintasan tubuh mengambil alih untuk adegan jatuh.
      const waktuLepas = b.lepas_kendaraan_at == null ? b.lepas : b.lepas_kendaraan_at;
      const K = waktuLepas != null && tl >= waktuLepas ? null : kaitDunia(S, b, tl, d);
      let tokoh = b;
      if (K) { // titik kait: pinggul di dudukan (pinggul boneka duduk = 130 px di atas kaki, skala s)
        const sb = b.s != null ? v(b.s, tl, d, 1) : K.skala;
        tokoh = Object.assign({}, b, { x: K.duduk[0], y: K.duduk[1] + 130 * sb, s: sb });
        if (K.sudut === "samping") Object.assign(tokoh, { profil: true, cermin: K.arah < 0, pose: b.pose || "duduk_samping", _kaitDunia: K });
        else tokoh.pose = b.pose || "duduk";
      }
      tokoh.id = i;
      const bd = BADAN, by = BAYANG;
      if (CERAH && tokoh.gaya === "siluet") { BADAN = ["#b98262", "#a7806e", "#c79a74", "#9c7a68"][i % 4]; BAYANG = "#d9b08a"; }
      if (tokoh.gaya === "dajjal") BADAN = tokoh.baju || "#201a26"; else if (PAL && (tokoh.baju || C.baju)) BADAN = tokoh.baju || C.baju;
      isi += boneka(tokoh, tl, d); BADAN = bd; BAYANG = by;
    });
    (S.benda || []).filter((o) => o.depan).forEach((o) => { isi += o.hias ? `<g data-hias="1">${benda(o, tl, d)}</g>` : benda(o, tl, d); });
    const nDebu = S.debu == null ? 40 : S.debu === false ? 0 : Math.round(v(S.debu, tl, d, 40)); if (nDebu > 0) isi += debu(t, nDebu);
    const hj = v(S.hujan, tl, d, 0); if (hj > 0) { // hujan: tirai gelap tipis + garis air jatuh + percikan
      const R4 = rng(77); isi += `<rect x="-600" y="-600" width="2280" height="3200" fill="#1c2a3a" opacity="${0.22 * hj}"/>`;
      for (let i = 0; i < 160 * hj; i++) { const x0 = R4() * 1400 - 160, sp = 1500 + R4() * 700, y = ((R4() * 2400 + t * sp) % 2400) - 300, L4 = 40 + R4() * 50; isi += `<line x1="${x0 + y * 0.12}" y1="${y}" x2="${x0 + (y + L4) * 0.12}" y2="${y + L4}" stroke="#dfeeff" stroke-width="${2 + R4() * 2}" opacity="${0.35 + 0.3 * R4()}"/>`; }
      for (let i = 0; i < 30 * hj; i++) { const px = R4() * 1200 - 60, py = 1420 + R4() * 500, q = (t * 2 + R4()) % 1; isi += `<ellipse cx="${px}" cy="${py}" rx="${4 + q * 22}" ry="${1.5 + q * 6}" fill="none" stroke="#dfeeff" stroke-width="2" opacity="${0.6 * (1 - q)}"/>`; }
    }
    const geser = `translate(${540 - kx * z} ${960 - ky * z}) scale(${z})`;
    const potong = S.glitch || C.glitch || C.kilat === false || S.kilat === false ? 0 : clamp(1 - tl / 0.18); // kilat hitam singkat saat pindah shot (cerita.kilat:false = potongan langsung)
    // transisi glitch: awal shot (S.glitch / C.glitch) atau detik absolut C.glitch_t = [t,...]; durasi 0,3 dtk
    let gl = 0; if ((S.glitch || C.glitch) && S.at > 0 && S.glitch !== false) gl = clamp(1 - tl / 0.3); (C.glitch_t || []).forEach((g0) => { if (t >= g0 && t < g0 + 0.3) gl = Math.max(gl, 1 - (t - g0) / 0.3); });
    let adegan = `<g transform="${geser}">${isi}</g>`;
    if (gl > 0.02) {
      const R = rng(Math.floor(t * 30) * 13 + 7), n = 9; let st = `<defs><g id="scn">${adegan}</g>`;
      for (let i = 0; i < n; i++) { const y0 = R() * 1920, h = 30 + R() * 220; st += `<clipPath id="gc${i}"><rect x="0" y="${y0}" width="1080" height="${h}"/></clipPath>`; }
      st += `</defs><use href="#scn"/>`;
      const R2 = rng(Math.floor(t * 30) * 13 + 7); for (let i = 0; i < n; i++) { R2(); R2(); const dx = (R() - 0.5) * 160 * gl; st += `<g clip-path="url(#gc${i})"><use href="#scn" transform="translate(${dx} 0)"/><rect width="1080" height="1920" fill="${i % 2 ? "#00e5ff" : "#ff2a6d"}" opacity="${0.22 * gl}"/></g>`; }
      st += `<use href="#scn" transform="translate(${-14 * gl} 0)" opacity="${0.35 * gl}" style="mix-blend-mode:screen"/>`;
      for (let i = 0; i < 40; i++) st += `<rect x="${R() * 1080}" y="${R() * 1920}" width="${20 + R() * 80}" height="${8 + R() * 30}" fill="${["#fff", "#ff2a6d", "#00e5ff", "#000"][i % 4]}" opacity="${0.6 * gl}"/>`;
      adegan = st;
    }
    lapis.innerHTML = `<svg width="1080" height="1920" viewBox="0 0 1080 1920">${adegan}
      <rect width="1080" height="1920" fill="url(#vg)"/>${S.at > 0 ? `<rect width="1080" height="1920" fill="#000" opacity="${potong * 0.85}"/>` : ""}${C.label ? `<g font-family="DejaVu Sans, Arial, sans-serif" font-weight="800"><rect x="${540 - C.label.length * 11}" y="118" width="${C.label.length * 22}" height="52" rx="26" fill="${INK}" opacity=".7"/><text x="540" y="154" font-size="32" text-anchor="middle" fill="#ffd27a">${esc(C.label)}</text></g>` : ""}${C.urutan ? urutan(C.urutan, t) : ""}${C.meteran ? [].concat(C.meteran).map((M) => meteran(M, t)).join("") : ""}${teks(S.teks, tl)}${tengah(C.tengah, t)}${gelembung(C.dialog, t)}</svg>`;
  }

  const lama = window.setT;
  window.setT = (t) => { lama(t); gambar(t); };
  window.setT(0);
})();
