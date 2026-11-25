/* Papan: perpustakaan komponen animasi 9:16 (1080x1920) yang digerakkan data (SPEC).
   Kontrak kartu.py: fungsi global setT(t) menggambar kondisi pada detik t.
   Juga mengumpulkan peristiwa suara di window.__sfx = [[detik, jenis, volume], ...] (dicampur oleh papan_buat.py).
   Spesifikasi: lihat papan/contoh/*.json dan bagian "Papan" di CLAUDE.md. */
(function () {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const ease = (x) => 1 - Math.pow(1 - clamp(x), 3);
  const back = (x) => { x = clamp(x); const c = 1.7; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const fm = (s) => esc(s == null ? "" : s).replace(/\*(.+?)\*/g, "<em>$1</em>");
  const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const rupiah = (n, d = 0) => Number(n).toLocaleString("id-ID", { minimumFractionDigits: d, maximumFractionDigits: d });
  const rng = (seed) => () => { seed |= 0; seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  let T = 0, DUR = 10;
  const kedip = () => (Math.sin(T * 10) > 0 ? 1 : 0);
  const ketikHTML = (teks, n, kursor) =>
    esc(teks.slice(0, n)) + (kursor ? `<span class="kursor" style="display:inline-block;width:0;overflow:visible;opacity:${kedip()}">▍</span>` : "") +
    `<span style="visibility:hidden">${esc(teks.slice(n))}</span>`;
  const jumlahKetik = (t, len, kec) => Math.floor(clamp(t / (len / kec)) * len);
  const ticks = (t0, dur, step, v) => { const a = []; for (let x = 0; x < dur && a.length < 70; x += step) a.push([t0 + x, "tick", v]); return a; };

  const K = {}; // registri komponen: K.tipe = (spec) => ({el, upd(t), sfx[], kids[], masuk, rot})

  function anak(list, induk) {
    const arr = (list || []).map((s) => bangun(s));
    arr.forEach((n) => induk.appendChild(n.el));
    return arr;
  }
  const updAnak = (arr, t) => arr.forEach((n) => perbarui(n, t));

  const IDLE = { kartu: 1, tempel: 1, ponsel: 1, jendela: 1, login: 1, tabel: 1, grafik: 1, bandingkan: 1 };
  let nomorN = 0;

  function bangun(s) {
    const f = K[s.tipe];
    if (!f) throw new Error("tipe komponen tidak dikenal: " + s.tipe);
    const c = f(s);
    const w = el("div", "k");
    w.style.display = "flex"; w.style.justifyContent = "center"; w.style.width = "100%";
    if (s.lebar) { w.style.width = s.lebar + "px"; }
    if (s.hias) w.dataset.hias = "1"; // teks hiasan (tiruan layar dsb.), dikecualikan periksa.py dari ukuran minimum; selalu dilaporkan
    w.appendChild(c.el);
    nomorN++;
    return {
      el: w, at: s.at || 0, masuk: s.masuk || c.masuk || "naik", rot: s.rot != null ? s.rot : (c.rot || 0), upd: c.upd, s,
      sfx: c.sfx || [], kids: c.kids || [], efek: s.efek || [], idle: s.idle != null ? s.idle : !!IDLE[s.tipe], ph: nomorN * 1.7,
    };
  }

  function perbarui(n, t) {
    const tl = t - n.at, w = n.el;
    if (tl < 0) { w.style.opacity = 0; w.style.visibility = "hidden"; return; }
    w.style.visibility = "visible";
    const p = back(tl / 0.55), o = clamp(tl / 0.22), r = n.rot;
    let tf = "";
    switch (n.masuk) {
      case "jatuh": tf = `translateY(${(1 - p) * -90}px) rotate(${r * (0.3 + 0.7 * p) + (1 - p) * 4}deg) scale(${0.9 + 0.1 * p})`; break;
      case "geser": tf = `translateX(${(1 - p) * -190}px) rotate(${r}deg)`; break;
      case "geserkanan": tf = `translateX(${(1 - p) * 190}px) rotate(${r}deg)`; break;
      case "zoom": tf = `scale(${0.5 + 0.5 * p}) rotate(${r + (1 - p) * -6}deg)`; break;
      case "ketuk": tf = `scale(${1.6 - 0.6 * p}) rotate(${r}deg)`; break;
      case "muncul": tf = `rotate(${r}deg)`; break;
      default: tf = `translateY(${(1 - p) * 60}px) rotate(${r}deg) scale(${0.96 + 0.04 * p})`; // naik
    }
    // gerak hidup: mengambang halus setelah mendarat
    if (n.idle && tl > 0.7) {
      const a = Math.min(1, (tl - 0.7) / 0.5);
      tf += ` translateY(${Math.sin(T * 1.7 + n.ph) * 4 * a}px) rotate(${Math.sin(T * 1.1 + n.ph) * 0.32 * a}deg)`;
    }
    // efek per komponen
    let filter = "";
    for (const e of n.efek) {
      if (e.jenis === "denyut") {
        const a = e.dari || 0, b = e.sampai != null ? e.sampai : a + 2;
        const k = tl >= a && tl <= b ? clamp(Math.min((tl - a) / 0.2, (b - tl) / 0.2)) : 0;
        if (k > 0) { tf += ` scale(${1 + 0.035 * k * (0.5 + 0.5 * Math.sin((tl - a) * 8))})`; filter += ` drop-shadow(0 0 ${24 * k}px rgba(255,122,47,.95))`; }
      } else if (e.jenis === "getar") {
        const d = tl - (e.at || 0);
        if (d >= 0 && d < 0.5) tf += ` translateX(${Math.sin(d * 70) * 14 * (1 - d / 0.5)}px)`;
      }
    }
    w.style.opacity = o; w.style.transform = tf; w.style.filter = filter;
    if (n.upd) n.upd(tl);
  }

  // ---------- komponen dasar ----------
  K.kartu = (s) => {
    const e = el("div", "kartu" + (s.polos ? " polos" : ""));
    if (s.paku !== false && !s.polos) e.appendChild(el("div", "paku"));
    if (s.judul || s.no) {
      const h = el("div", "kartu-judul");
      if (s.no) h.appendChild(el("span", "no", esc(s.no)));
      h.appendChild(el("span", "", fm(s.judul || "")));
      e.appendChild(h);
    }
    const b = el("div", "kartu-isi"); e.appendChild(b);
    const ch = anak(s.anak, b);
    return { el: e, masuk: "jatuh", kids: ch, upd: (t) => updAnak(ch, t) };
  };
  K.kolom = (s) => { const e = el("div", "kartu-isi"); e.style.width = "100%"; const ch = anak(s.anak, e); return { el: e, kids: ch, upd: (t) => updAnak(ch, t) }; };
  K.baris = (s) => { const e = el("div", "baris"); const ch = anak(s.anak, e); return { el: e, kids: ch, upd: (t) => updAnak(ch, t) }; };
  K.spasi = (s) => { const e = el("div"); e.style.height = (s.tinggi || 30) + "px"; return { el: e, masuk: "muncul" }; };

  K.tempel = (s) => ({ el: el("div", "tempel " + (s.warna || "kuning"), fm(s.teks) + (s.sub ? `<small>${fm(s.sub)}</small>` : "")), masuk: "jatuh" });

  K.stempel = (s) => {
    const e = el("div", "stempel", esc(s.teks || "ILUSTRASI"));
    e.style.position = "static"; e.style.display = "inline-block";
    if (s.warna) { e.style.color = s.warna; e.style.borderColor = s.warna; }
    return { el: e, masuk: "ketuk", rot: s.rot != null ? s.rot : -6, sfx: [[0.28, "thud", 0.55]] };
  };

  K.teks = (s) => {
    const e = el("div", "teks " + (s.ukuran || "") + (s.tengah ? " tengah" : ""));
    if (s.warna) e.style.color = s.warna;
    const plain = String(s.teks || "");
    if (!s.ketik) { e.innerHTML = fm(plain); return { el: e }; }
    const kec = s.kec || 30;
    return { el: e, sfx: ticks(s.mulai || 0, plain.length / kec, 0.085, 0.2), upd: (t) => { e.innerHTML = ketikHTML(plain, jumlahKetik(t - (s.mulai || 0), plain.length, kec), true); } };
  };

  K.sorot = (s) => {
    const e = el("div"); e.style.width = "100%";
    const a = el("div", "sorot-teks", esc(s.teks || "").replace(/\*(.+?)\*/g, '<span class="tanda">$1</span>'));
    if (s.warna) a.style.color = s.warna;
    e.appendChild(a);
    if (s.sub) e.appendChild(el("div", "sorot-sub", fm(s.sub)));
    const tn = a.querySelectorAll(".tanda");
    return { el: e, masuk: "ketuk", sfx: [...Array.from(tn).map((_, i) => [0.5 + i * 0.4, "swish", 0.35])],
      upd: (t) => tn.forEach((x, i) => { x.style.backgroundSize = ease((t - 0.5 - i * 0.4) / 0.5) * 100 + "% 100%"; }) };
  };

  K.pil = (s) => ({ el: el("div", "pil " + (s.warna || ""), (s.ikon ? `<span class="ik">${s.ikon}</span>` : "") + fm(s.teks || "")), masuk: s.masuk || "ketuk", sfx: [[0.15, "pop", 0.4]] });

  K.gambar = (s) => {
    const e = el("img", "gambar" + (s.bulat ? " bulat" : "") + (s.bingkai ? " bingkai" : "") + (s.logo ? " logo" : ""));
    e.src = s.src || ""; e.alt = s.alt || "";
    if (s.lebar) e.style.width = s.lebar + "px";
    if (s.tinggi) e.style.height = s.tinggi + "px";
    if (s.isi) e.style.objectFit = s.isi;
    return { el: e, masuk: s.masuk || "zoom" };
  };
  // ---------- penanda tulisan tangan di sekitar komponen: lingkar | garis | panah | coret ----------
  K.tanda = (s) => {
    const w = el("div", "tanda-w"), ch = anak([s.anak || { tipe: "teks", teks: s.teks || "" }], w);
    const ns = "http://www.w3.org/2000/svg", svg = document.createElementNS(ns, "svg"), path = document.createElementNS(ns, "path");
    svg.setAttribute("class", "tanda-svg"); svg.appendChild(path); w.appendChild(svg);
    path.setAttribute("fill", "none"); path.setAttribute("stroke", s.warna || "#E4572E"); path.setAttribute("stroke-width", s.tebal || 9);
    path.setAttribute("stroke-linecap", "round"); path.setAttribute("stroke-linejoin", "round");
    let siap = false, L = 0; const m = s.mulai == null ? 0.5 : s.mulai, R = rng(7);
    function bangunJalur() {
      const W = w.offsetWidth, H = w.offsetHeight, p = 26; svg.setAttribute("viewBox", `${-p} ${-p} ${W + 2 * p} ${H + 2 * p}`);
      svg.style.left = -p + "px"; svg.style.top = -p + "px"; svg.style.width = W + 2 * p + "px"; svg.style.height = H + 2 * p + "px";
      let d = "", j = s.jenis || "lingkar";
      if (j === "lingkar") {
        const cx = W / 2, cy = H / 2, rx = W / 2 + 34, ry = H / 2 + 22; const pts = [];
        for (let a = -0.5; a <= Math.PI * 2 + 0.6; a += 0.12) { const g = 1 + (R() - 0.5) * 0.04; pts.push([cx + Math.cos(a) * rx * g, cy + Math.sin(a) * ry * g + a * 1.5]); }
        d = "M" + pts.map((q) => q[0].toFixed(1) + " " + q[1].toFixed(1)).join(" L");
      } else if (j === "garis") {
        const y = H + 10; d = `M -6 ${y} Q ${W * 0.3} ${y + 9} ${W * 0.55} ${y + 2} T ${W + 8} ${y + 4}`;
      } else if (j === "coret") {
        d = `M -8 ${H * 0.55} Q ${W * 0.5} ${H * 0.45} ${W + 8} ${H * 0.5}`;
      } else if (j === "panah") {
        const y = H / 2; d = `M ${-150} ${y + 40} Q ${-70} ${y + 30} -14 ${y} M -34 ${y - 18} L -12 ${y} L -36 ${y + 14}`;
        svg.style.overflow = "visible";
      }
      path.setAttribute("d", d); L = path.getTotalLength(); path.style.strokeDasharray = L; siap = true;
    }
    return { el: w, kids: ch, masuk: "muncul", sfx: [[m, "swish", 0.35]], upd: (t) => {
      updAnak(ch, t); if (!siap) bangunJalur();
      path.style.strokeDashoffset = L * (1 - ease((t - m) / (s.lama || 0.45)));
    } };
  };

  // ---------- menu/tombol aplikasi yang diklik kursor berurutan ----------
  K.menu = (s) => {
    const e = el("div", "menu-w " + (s.arah === "h" ? "h" : "v"));
    const B = (s.item || []).map((x) => { const o = typeof x === "string" ? { teks: x } : x; const b = el("div", "menu-b", (o.ikon ? `<span class="ik">${o.ikon}</span>` : "") + `<span>${fm(o.teks)}</span>`); e.appendChild(b); return { b, o }; });
    const kur = el("div", "kursor", '<svg viewBox="0 0 24 24" width="64" height="64"><path d="M4 2 L4 20 L9 15 L12.5 22 L15.5 20.6 L12 13.8 L19 13.8 Z" fill="#1b1b1b" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg><i></i>');
    e.appendChild(kur);
    const T = B.map((x, i) => (x.o.at != null ? x.o.at : 0.6 + i * (s.jeda || 1.0)));
    return { el: e, sfx: T.map((t) => [t, "klik", 0.5]), upd: (t) => {
      let k = -1; T.forEach((x, i) => { if (t >= x - 0.45) k = i; });
      B.forEach(({ b }, i) => { b.classList.toggle("on", t >= T[i]); });
      if (k < 0) { kur.style.opacity = 0; return; }
      const tgt = B[k].b, prev = k ? B[k - 1].b : null;
      const pos = (n) => [n.offsetLeft + n.offsetWidth * 0.62, n.offsetTop + n.offsetHeight * 0.55];
      const [x1, y1] = pos(tgt), [x0, y0] = prev ? pos(prev) : [x1 + 160, y1 + 120];
      const q = ease((t - (T[k] - 0.45)) / 0.4);
      kur.style.opacity = 1; kur.style.transform = `translate(${x0 + (x1 - x0) * q}px,${y0 + (y1 - y0) * q}px) scale(${t >= T[k] && t < T[k] + 0.15 ? 0.85 : 1})`;
      const rip = kur.querySelector("i"), d = t - T[k]; rip.style.opacity = d >= 0 && d < 0.5 ? 1 - d / 0.5 : 0; rip.style.transform = `scale(${0.3 + d * 3})`;
    } };
  };
  // ---------- kartu produk + harga coret / promo ----------
  K.produk = (s) => {
    const e = el("div", "produk" + (s.mendatar ? " datar" : ""));
    e.innerHTML = (s.src ? `<div class="pf"><img src="${s.src}" alt=""></div>` : "") +
      `<div class="pi">${s.label ? `<span class="plabel">${fm(s.label)}</span>` : ""}<div class="pn">${fm(s.nama || "")}</div>` +
      (s.sub ? `<div class="ps">${fm(s.sub)}</div>` : "") +
      `<div class="ph">${s.lama ? `<s>${esc(s.lama)}</s>` : ""}<b>${esc(s.harga || "")}</b>${s.satuan ? `<small>${esc(s.satuan)}</small>` : ""}</div></div>`;
    const lama = e.querySelector("s"), b = e.querySelector(".ph b"), lab = e.querySelector(".plabel"), a0 = s.coret == null ? 0.8 : s.coret;
    return { el: e, masuk: "zoom", sfx: s.lama ? [[a0, "swish", 0.35], [a0 + 0.3, "ding", 0.4]] : [], upd: (t) => {
      if (lama) { lama.style.setProperty("--c", ease((t - a0) / 0.35)); b.style.opacity = s.lama ? clamp((t - a0 - 0.25) / 0.2) : 1; b.style.transform = `scale(${0.7 + 0.3 * back((t - a0 - 0.25) / 0.4)})`; }
      if (lab) lab.style.transform = `rotate(-8deg) scale(${1 + 0.06 * Math.sin(t * 6)})`;
    } };
  };

  // ---------- hitung mundur ----------
  K.hitung = (s) => {
    const e = el("div", "hitung"), n0 = s.dari == null ? 3 : s.dari, satuan = s.satuan || ["Hari", "Jam", "Menit", "Detik"];
    const nilai = s.nilai || [2, 14, 30, 0];
    const kot = satuan.map((u, i) => { const k = el("div", "hk", `<b>00</b><span>${esc(u)}</span>`); e.appendChild(k); return k.querySelector("b"); });
    if (s.teks) e.appendChild(el("div", "hlb", fm(s.teks)));
    return { el: e, sfx: ticks(0.3, Math.min(6, s.lama || 4), 1, 0.25), upd: (t) => {
      // detik terus berkurang mulai dari nilai awal
      let total = ((nilai[0] * 24 + nilai[1]) * 60 + nilai[2]) * 60 + (nilai[3] || 0) - Math.max(0, Math.floor(t - 0.3));
      total = Math.max(0, total);
      const v = [Math.floor(total / 86400), Math.floor(total / 3600) % 24, Math.floor(total / 60) % 60, total % 60];
      kot.forEach((k, i) => { const x = String(v[i]).padStart(2, "0"); if (k.textContent !== x) k.textContent = x; });
    } };
  };

  // ---------- peta rute skematis (titik + garis bergerak + ikon kendaraan) ----------
  K.rute = (s) => {
    const W = s.lebar_peta || 860, H = s.tinggi || 620, ns = "http://www.w3.org/2000/svg";
    const e = el("div", "rute"); e.style.width = W + "px"; e.style.height = H + "px";
    const titik = s.titik || []; // [{nama, x:0-1, y:0-1, at}]
    const svg = document.createElementNS(ns, "svg"); svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("width", W); svg.setAttribute("height", H); e.appendChild(svg);
    const P = titik.map((p) => [p.x * W, p.y * H]);
    let d = ""; P.forEach((q, i) => { if (!i) d = `M ${q[0]} ${q[1]}`; else { const a = P[i - 1], mx = (a[0] + q[0]) / 2, my = Math.min(a[1], q[1]) - 60; d += ` Q ${mx} ${my} ${q[0]} ${q[1]}`; } });
    const bayang = document.createElementNS(ns, "path"); bayang.setAttribute("d", d); bayang.setAttribute("class", "rute-bg"); svg.appendChild(bayang);
    const jalur = document.createElementNS(ns, "path"); jalur.setAttribute("d", d); jalur.setAttribute("class", "rute-jalan"); svg.appendChild(jalur);
    const L = () => jalur.getTotalLength();
    const node = titik.map((p, i) => { const n = el("div", "rute-titik", `<i></i><span>${fm(p.nama)}</span>`); n.style.left = P[i][0] + "px"; n.style.top = P[i][1] + "px"; e.appendChild(n); return n; });
    const mobil = el("div", "rute-mobil", s.ikon || "🚐"); e.appendChild(mobil);
    const m0 = s.mulai == null ? 0.4 : s.mulai, lama = s.lama || 3.5;
    let segL = null;
    return { el: e, sfx: [[m0, "whoosh", 0.25], ...titik.map((p, i) => [m0 + (i / Math.max(1, titik.length - 1)) * lama, "pop", 0.4])], upd: (t) => {
      const tot = L(); if (!segL) { segL = [0]; let acc = 0; for (let i = 1; i < P.length; i++) { /* perkiraan panjang tiap ruas */ acc += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]) * 1.15; segL.push(acc); } const k = tot / (segL[segL.length - 1] || 1); segL = segL.map((x) => x * k); }
      const q = ease((t - m0) / lama), panjang = tot * q;
      jalur.style.strokeDasharray = `${tot}`; jalur.style.strokeDashoffset = `${tot - panjang}`;
      const pt = jalur.getPointAtLength(Math.max(0.01, panjang)); mobil.style.transform = `translate(${pt.x}px,${pt.y}px)`; mobil.style.opacity = t >= m0 ? 1 : 0;
      node.forEach((n, i) => { const on = panjang >= segL[i] - 2; n.classList.toggle("on", on); n.style.opacity = clamp((t - m0 + 0.6 - i * 0.15) / 0.3); });
    } };
  };

  // ---------- terminal agen AI: banner ASCII, perintah diketik, panggilan alat, jawaban mengalir ----------
  const HURUF = {A:["  #  "," # # ","#####","#   #","#   #"],B:["#### ","#   #","#### ","#   #","#### "],C:[" ####","#    ","#    ","#    "," ####"],D:["#### ","#   #","#   #","#   #","#### "],E:["#####","#    ","#### ","#    ","#####"],F:["#####","#    ","#### ","#    ","#    "],G:[" ####","#    ","# ###","#   #"," ####"],H:["#   #","#   #","#####","#   #","#   #"],I:["#####","  #  ","  #  ","  #  ","#####"],J:["  ###","   # ","   # ","#  # "," ##  "],K:["#   #","#  # ","###  ","#  # ","#   #"],L:["#    ","#    ","#    ","#    ","#####"],M:["#   #","## ##","# # #","#   #","#   #"],N:["#   #","##  #","# # #","#  ##","#   #"],O:[" ### ","#   #","#   #","#   #"," ### "],P:["#### ","#   #","#### ","#    ","#    "],Q:[" ### ","#   #","# # #","#  # "," ## #"],R:["#### ","#   #","#### ","#  # ","#   #"],S:[" ####","#    "," ### ","    #","#### "],T:["#####","  #  ","  #  ","  #  ","  #  "],U:["#   #","#   #","#   #","#   #"," ### "],V:["#   #","#   #","#   #"," # # ","  #  "],W:["#   #","#   #","# # #","## ##","#   #"],X:["#   #"," # # ","  #  "," # # ","#   #"],Y:["#   #"," # # ","  #  ","  #  ","  #  "],Z:["#####","   # ","  #  "," #   ","#####"]," ":["   ","   ","   ","   ","   "]};
  K.terminal = (s) => {
    const e = el("div", "term", `<div class="tbar"><i></i><i></i><i></i><span>${esc(s.judul || "terminal")}</span></div><div class="tisi"></div>`);
    const isi = e.querySelector(".tisi"), sfx = [];
    const ban = String(s.banner || "").toUpperCase().split("").filter((c) => HURUF[c]);
    const banRows = ban.length ? [0, 1, 2, 3, 4].map((r) => ban.map((c) => HURUF[c][r].replace(/#/g, s.huruf || "█").replace(/ /g, " ")).join(" ")) : [];
    const pre = el("pre", "tban"); isi.appendChild(pre);
    const baris = (s.baris || []).map((b) => { const o = typeof b === "string" ? { teks: b } : b; const d = el("div", "tl " + (o.jenis || "jawab")); isi.appendChild(d); return { d, o }; });
    let t0 = 0.3; const jadwal = [];
    banRows.forEach((r, i) => sfx.push([t0 + i * 0.08, "tick", 0.2]));
    t0 += banRows.length ? banRows.length * 0.08 + 0.4 : 0;
    baris.forEach(({ o }) => {
      const at = o.at != null ? o.at : t0, kec = o.jenis === "perintah" ? 18 : o.jenis === "alat" ? 999 : 45;
      const dur = o.jenis === "alat" ? (o.lama || 1.2) : o.teks.length / kec;
      jadwal.push({ at, dur, kec }); if (o.jenis === "perintah") sfx.push(...ticks(at, dur, 0.07, 0.22)); if (o.jenis === "alat") sfx.push([at + dur, "ding", 0.35]);
      t0 = at + dur + 0.35;
    });
    const SP = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏";
    return { el: e, sfx, upd: (t) => {
      const nb = Math.floor(clamp((t - 0.3) / Math.max(0.01, banRows.length * 0.08)) * banRows.length);
      pre.textContent = banRows.slice(0, nb).join("\n");
      baris.forEach(({ d, o }, i) => {
        const j = jadwal[i]; if (t < j.at) { d.style.display = "none"; return; } d.style.display = "block";
        if (o.jenis === "alat") {
          const selesai = t >= j.at + j.dur;
          d.innerHTML = `<b>${selesai ? "✓" : SP[Math.floor(t * 12) % SP.length]}</b> ${esc(o.teks)}${selesai && o.hasil ? ` <em>→ ${esc(o.hasil)}</em>` : ""}`;
        } else {
          const n = jumlahKetik(t - j.at, o.teks.length, j.kec), kur = t < j.at + j.dur + 0.6 && (i === baris.length - 1 || t < jadwal[i + 1].at);
          d.innerHTML = (o.jenis === "perintah" ? '<span class="pr">❯</span> ' : "") + esc(o.teks.slice(0, n)) + (kur && kedip() ? '<span class="kr">▌</span>' : "");
        }
      });
    } };
  };

  // ---------- kanvas alur otomasi gaya simpul (umum, tanpa merek) ----------
  K.kanvas = (s) => {
    const W = s.lebar_kanvas || 900, H = s.tinggi || 640, ns = "http://www.w3.org/2000/svg";
    const e = el("div", "kanvas"); e.style.width = W + "px"; e.style.height = H + "px";
    const svg = document.createElementNS(ns, "svg"); svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("width", W); svg.setAttribute("height", H); e.appendChild(svg);
    const S = (s.simpul || []).map((o, i) => { const n = el("div", "ks " + (o.warna || ""), `<span class="ik">${o.ikon || ""}</span><span>${fm(o.teks)}</span><b class="ok">✓</b>`); n.style.left = o.x * W + "px"; n.style.top = o.y * H + "px"; e.appendChild(n); return { n, o }; });
    const jeda = s.jeda || 0.8, m0 = s.mulai == null ? 0.3 : s.mulai;
    const T = S.map(({ o }, i) => (o.at != null ? o.at : m0 + i * jeda));
    const kabel = (s.sambung || []).map(([a, b]) => {
      const p = document.createElementNS(ns, "path"); p.setAttribute("class", "kabel"); svg.appendChild(p);
      const dot = el("div", "kdot"); e.appendChild(dot); return { a, b, p, dot, siap: false };
    });
    return { el: e, sfx: T.map((t) => [t, "pop", 0.35]).concat(T.map((t) => [t + 0.45, "ding", 0.2])), upd: (t) => {
      S.forEach(({ n }, i) => { const p = back((t - T[i]) / 0.45); n.style.opacity = clamp((t - T[i]) / 0.2); n.style.transform = `translate(-50%,-50%) scale(${0.6 + 0.4 * p})`; n.classList.toggle("done", t >= T[i] + 0.45); });
      kabel.forEach((k) => {
        const A = S[k.a].n, B = S[k.b].n;
        if (!k.siap) { const x1 = A.offsetLeft + A.offsetWidth / 2, y1 = A.offsetTop, x2 = B.offsetLeft - B.offsetWidth / 2, y2 = B.offsetTop, dx = Math.max(60, (x2 - x1) / 2);
          k.p.setAttribute("d", `M ${x1} ${y1} C ${x1 + dx} ${y1} ${x2 - dx} ${y2} ${x2} ${y2}`); k.L = k.p.getTotalLength(); k.p.style.strokeDasharray = k.L; k.siap = true; }
        const t1 = T[k.a] + 0.3, t2 = T[k.b], q = ease((t - t1) / Math.max(0.2, t2 - t1));
        k.p.style.strokeDashoffset = k.L * (1 - q);
        const r = (t - t2) % 1.4, on = t > t2 + 0.3; k.dot.style.opacity = on ? 1 : 0;
        if (on) { const pt = k.p.getPointAtLength(k.L * ((t - t2) % 1.4) / 1.4); k.dot.style.transform = `translate(${pt.x}px,${pt.y}px)`; }
      });
    } };
  };

  // ---------- ulasan pelanggan (pakai hanya ulasan asli) ----------
  K.ulasan = (s) => {
    const e = el("div", "ulasan", `<div class="bintang"></div><div class="uq">“${fm(s.teks || "")}”</div><div class="un">${fm(s.nama || "")}${s.sumber ? ` · <small>${esc(s.sumber)}</small>` : ""}</div>`);
    const bt = e.querySelector(".bintang"), nb = s.bintang || 5;
    const B = [...Array(5)].map((_, i) => bt.appendChild(el("span", i < nb ? "on" : "", "★")));
    return { el: e, masuk: "naik", sfx: B.slice(0, nb).map((_, i) => [0.4 + i * 0.12, "pop", 0.3]), upd: (t) => {
      B.forEach((b, i) => { const p = back((t - 0.4 - i * 0.12) / 0.3); b.style.transform = `scale(${p})`; });
    } };
  };
  // ---------- layar meredup + kotak seleksi ditarik (tangkap layar sebagian) ----------
  K.seleksi = (s) => {
    const w = el("div", "seleksi-w"), ch = anak([s.anak || { tipe: "jendela", url: "dokumen", anak: [{ tipe: "teks", teks: "…" }] }], w);
    const redup = el("div", "sel-redup"), kot = el("div", "sel-kotak"); w.appendChild(redup); w.appendChild(kot);
    const a = s.mulai == null ? 0.6 : s.mulai, r = s.kotak || [0.15, 0.25, 0.7, 0.45]; // x,y,w,h pecahan
    return { el: w, kids: ch, sfx: [[a, "swish", 0.3], [a + 1.0, "klik", 0.5]], upd: (t) => {
      updAnak(ch, t);
      const d = clamp((t - a + 0.4) / 0.3); redup.style.opacity = 0.55 * d * (t < a + 1.6 ? 1 : clamp(1 - (t - a - 1.6) / 0.3));
      const q = ease((t - a) / 0.9); kot.style.opacity = t >= a && t < a + 1.9 ? 1 : 0;
      kot.style.left = r[0] * 100 + "%"; kot.style.top = r[1] * 100 + "%"; kot.style.width = r[2] * q * 100 + "%"; kot.style.height = r[3] * q * 100 + "%";
    } };
  };
  K.ikon = (s) => ({ el: el("div", "ikonbesar", `<div class="ik">${s.ikon || "⭐"}</div>${s.teks ? `<div class="lb">${fm(s.teks)}</div>` : ""}`), masuk: "zoom" });

  K.lencana = (s) => {
    const e = el("div", "lencana-w"), jeda = s.jeda || 0.3;
    const L = (s.item || []).map((x) => e.appendChild(el("span", "lencana " + (s.warna || ""), fm(x))));
    return { el: e, sfx: L.map((_, i) => [i * jeda + 0.1, "pop", 0.35]),
      upd: (t) => L.forEach((x, i) => { const p = back((t - i * jeda) / 0.4); x.style.opacity = clamp((t - i * jeda) / 0.2); x.style.transform = `scale(${0.5 + 0.5 * p})`; }) };
  };

  K.angka = (s) => {
    const e = el("div", "angka", `<div class="n"></div>${s.label ? `<div class="lb">${fm(s.label)}</div>` : ""}`);
    const n = e.querySelector(".n"), dur = s.dur || 1.4;
    return { el: e, masuk: "zoom", sfx: ticks(0.2, dur, 0.06, 0.2), upd: (t) => { const v = (s.nilai || 0) * ease((t - 0.2) / dur); n.textContent = (s.awalan || "") + rupiah(v, s.desimal || 0) + (s.akhiran || ""); n.style.transform = `scale(${1 + 0.04 * Math.sin(t * 20) * (1 - ease((t - 0.2) / dur))})`; } };
  };

  K.jam = (s) => ({ el: el("div", "jam", `<div class="j">${esc(s.jam || "07:00")}</div>${s.teks ? `<div class="lb">${fm(s.teks)}</div>` : ""}`), masuk: "zoom" });

  K.progress = (s) => {
    const e = el("div", "prog", `<div class="lb"><span>${fm(s.label || "")}</span><b class="v"></b></div><div class="tr"><i></i></div>`);
    const i = e.querySelector("i"), v = e.querySelector(".v");
    return { el: e, sfx: [[0.2, "swish", 0.22]], upd: (t) => { const x = (s.nilai == null ? 100 : s.nilai) * ease((t - 0.2) / (s.dur || 1.2)); i.style.width = x + "%"; v.textContent = Math.round(x) + "%"; } };
  };

  K.sensor = (s) => {
    const e = el("div", "sensor", `${esc(s.teks || "rahasia-123")}<div class="bar"></div>`);
    const b = e.querySelector(".bar"), a0 = s.sensorAt == null ? 0.8 : s.sensorAt;
    return { el: e, sfx: [[a0, "swish", 0.4]], upd: (t) => { b.style.width = ease((t - a0) / 0.4) * (e.offsetWidth + 12) + "px"; } };
  };

  K.notifikasi = (s) => {
    const e = el("div", "notif " + (s.gaya || ""), `<span class="ik">${s.ikon || "🔔"}</span><div>${s.sub ? `<small>${esc(s.sub)}</small>` : ""}${s.judul ? `<b>${fm(s.judul)}</b> ` : ""}${fm(s.teks || "")}</div>`);
    return { el: e, masuk: "naik", sfx: [[0.12, "notif", 0.6]] };
  };

  // ---------- chat ----------
  K.chat = (s) => {
    const e = el("div", "chat"), sfx = [];
    const B = (s.pesan || []).map((m) => {
      const b = el("div", "gel " + (m.dari || "kiri")); e.appendChild(b);
      const txt = String(m.teks || "");
      sfx.push([m.at || 0, "pop", 0.4]);
      if (m.ketik !== false) ticks((m.at || 0) + 0.15, txt.length / (m.kec || 32), 0.085, 0.2).forEach((x) => sfx.push(x));
      return { b, m };
    });
    return { el: e, sfx, upd: (t) => B.forEach(({ b, m }) => {
      const tl = t - (m.at || 0), txt = String(m.teks || "");
      if (tl < 0) { b.style.opacity = 0; return; }
      const nama = m.nama ? `<span class="nama">${esc(m.nama)}</span>` : "";
      const ketik = m.ketik !== false;
      const n = ketik ? jumlahKetik(tl - 0.15, txt.length, m.kec || 32) : txt.length;
      b.innerHTML = nama + ketikHTML(txt, Math.max(0, n), ketik && n < txt.length);
      const p = back(tl / 0.35); b.style.opacity = clamp(tl / 0.15);
      b.style.transform = `translateY(${(1 - p) * 28}px) scale(${0.85 + 0.15 * p})`;
    }) };
  };

  // ---------- daftar centang / bernomor ----------
  K.centang = (s) => {
    const e = el("div", "daftar"), jeda = s.jeda || 0.6, m = s.mulai || 0.3, sfx = [];
    const R = (s.item || []).map((x, i) => {
      const o = typeof x === "string" ? { teks: x } : x;
      const r = el("div", "baris-c", `<span class="kotak"></span><span>${fm(o.teks)}</span>`); e.appendChild(r);
      sfx.push([m + i * jeda, o.ok === false ? "buzz" : "ding", 0.45]);
      return { r, k: r.querySelector(".kotak"), o };
    });
    return { el: e, sfx, upd: (t) => R.forEach(({ r, k, o }, i) => {
      const t0 = m + i * jeda, ok = t >= t0;
      k.className = "kotak" + (ok ? (o.ok === false ? " x" : " ok") : "");
      k.textContent = ok ? (o.ok === false ? "✕" : "✓") : "";
      k.style.transform = ok ? `scale(${1 + 0.5 * Math.max(0, 1 - (t - t0) * 4)}) rotate(${(o.ok === false ? 1 : 0) * Math.sin((t - t0) * 40) * 8 * Math.max(0, 1 - (t - t0) * 4)}deg)` : "scale(1)";
      r.style.opacity = ok ? 1 : 0.5;
      r.style.transform = ok ? `translateX(${Math.max(0, 1 - (t - t0) * 5) * 14}px)` : "none";
    }) };
  };

  K.daftar = (s) => {
    const e = el("div", "daftar"), jeda = s.jeda || 0.6, m = s.mulai || 0.2;
    const R = (s.item || []).map((x, i) => {
      const r = el("div", "baris-c", (s.nomor ? `<span class="nomor-d">${i + 1}</span>` : '<span class="peluru"></span>') + `<span>${fm(x)}</span>`);
      e.appendChild(r); return r;
    });
    return { el: e, sfx: R.map((_, i) => [m + i * jeda, "pop", 0.3]),
      upd: (t) => R.forEach((r, i) => { const p = back((t - m - i * jeda) / 0.45); r.style.opacity = clamp((t - m - i * jeda) / 0.2); r.style.transform = `translateX(${(1 - p) * -70}px)`; }) };
  };

  // ---------- diagram alur ----------
  K.alur = (s) => {
    const e = el("div", "alur " + (s.arah === "h" ? "h" : "v"));
    const N = [], A = [], sfx = [], j = s.jeda || 0.9, m = s.mulai || 0.2;
    (s.simpul || []).forEach((x, i) => {
      const o = typeof x === "string" ? { teks: x } : x;
      if (i) { const p = el("div", "panah", "<i></i><b></b>"); e.appendChild(p); A.push(p); sfx.push([m + i * j - 0.4, "swish", 0.35]); }
      const n = el("div", "simpul " + (o.warna || ""), (o.ikon ? `<span class="ik">${o.ikon}</span>` : "") + `<span>${fm(o.teks)}</span>`);
      e.appendChild(n); N.push(n); sfx.push([m + i * j, "pop", 0.45]);
    });
    const pk = [0, 1, 2, 3].map((k) => { const d = el("div", "paket"); d.style.opacity = 0; e.appendChild(d); return d; });
    return { el: e, sfx, upd: (t) => {
      N.forEach((n, i) => {
        const t0 = m + i * j, p = back((t - t0) / 0.5), gl = clamp(1 - (t - t0 - 0.1) / 0.7) * (t >= t0 ? 1 : 0);
        n.style.opacity = clamp((t - t0) / 0.2); n.style.transform = `scale(${0.6 + 0.4 * p})`;
        n.style.boxShadow = `0 8px 14px rgba(40,25,10,.28), 0 0 0 ${16 * gl}px rgba(255,122,47,${0.35 * gl}), 0 0 ${40 * gl}px rgba(255,170,90,${0.8 * gl})`;
      });
      const kedudukan = [0, 0, 0, 0].map(() => null);
      A.forEach((a, i) => {
        const g0 = m + (i + 1) * j - 0.5, g = ease((t - g0) / 0.35);
        a.firstChild.style.transform = (s.arah === "h" ? `scaleX(${g})` : `scaleY(${g})`);
        a.style.opacity = t >= g0 ? 1 : 0;
        if (s.paket !== false) {
          const a1 = N[i], a2 = N[i + 1];
          const cx = (n) => n.offsetLeft + n.offsetWidth / 2 - 15, cy = (n) => n.offsetTop + n.offsetHeight / 2 - 15;
          pk.forEach((d, k) => {
            const q = (t - g0 - 0.1 - k * 0.06) / 0.55;
            if (q >= 0 && q <= 1) {
              const qq = ease(q);
              d.style.opacity = (1 - k * 0.28) * (k ? 0.8 : 1); d.style.transform = `translate(${cx(a1) + (cx(a2) - cx(a1)) * qq}px,${cy(a1) + (cy(a2) - cy(a1)) * qq}px) scale(${(1 + 0.25 * Math.sin(qq * Math.PI)) * (1 - k * 0.18)})`;
              kedudukan[k] = 1;
            }
          });
        }
      });
      pk.forEach((d, k) => { if (!kedudukan[k]) d.style.opacity = 0; });
    } };
  };

  // ---------- lembar kerja tiruan (spreadsheet generik) ----------
  // s: {kolom:["A","B"], lebar_kolom:[300,260], baris:[[..],[..]] (baris 1 = judul kolom), pilih:"B2",
  //     langkah:[{at, pilih:"B2"} | {at, ketik:"=TRIM(A2)", sel?, hasil?:"Budi", kec?} | {at, isi:[["B3","Ani"],...], jeda?, pratinjau?:true}]}
  K.lembar = (s) => {
    const kol = s.kolom || ["A", "B", "C"], lw = s.lebar_kolom || kol.map(() => 260), rows = s.baris || [];
    const e = el("div", "lembar");
    const fb = el("div", "fbar", `<span class="nm"></span><span class="fx">fx</span><span class="isi"></span>`); e.appendChild(fb);
    const nm = fb.querySelector(".nm"), fi = fb.querySelector(".isi");
    const tb = el("table", "grid"); e.appendChild(tb);
    const hr = el("tr"); hr.appendChild(el("th", "pojok")); kol.forEach((k, i) => { const th = el("th", "", k); th.style.width = lw[i] + "px"; hr.appendChild(th); }); tb.appendChild(hr);
    const sel = {}, awal = {};
    rows.forEach((r, ri) => {
      const tr = el("tr"); tr.appendChild(el("th", "nomor", String(ri + 1)));
      kol.forEach((k, ci) => { const id = k + (ri + 1), td = el("td", ri === 0 && s.judul !== false ? "jud" : ""); td.textContent = r[ci] == null ? "" : r[ci]; sel[id] = td; awal[id] = td.textContent; tr.appendChild(td); });
      tb.appendChild(tr);
    });
    const L = (s.langkah || []).slice().sort((a, b) => a.at - b.at), sfx = [];
    L.forEach((x) => {
      if (x.ketik) { const kec = x.kec || 14; sfx.push(...ticks(x.at, x.ketik.length / kec, 0.07, 0.22)); if (x.hasil != null) sfx.push([x.at + x.ketik.length / kec + 0.25, "pop", 0.4]); }
      if (x.isi) x.isi.forEach((_, i) => sfx.push([x.at + i * (x.jeda || 0.12), "pop", 0.3]));
      if (x.pilih) sfx.push([x.at, "tick", 0.3]);
      if (x.warna) x.warna.forEach((_, i) => sfx.push([x.at + i * (x.jeda || 0.1), "pop", 0.3]));
    });
    return { el: e, masuk: "naik", sfx, upd: (t) => {
      const v = Object.assign({}, awal), baru = {}, pra = {}, warna = {};
      let pilih = s.pilih || null, bar = null;
      L.forEach((x) => {
        if (t < x.at) return;
        if (x.pilih) { pilih = x.pilih; bar = null; }
        if (x.ketik) {
          const id = x.sel || pilih, kec = x.kec || 14, n = jumlahKetik(t - x.at, x.ketik.length, kec), selesai = t >= x.at + x.ketik.length / kec + 0.25;
          if (x.sel) pilih = x.sel;
          if (selesai && x.hasil != null) { v[id] = x.hasil; bar = x.ketik; baru[id] = t - (x.at + x.ketik.length / kec + 0.25); }
          else { v[id] = x.ketik.slice(0, n) + (kedip() ? "|" : ""); bar = x.ketik.slice(0, n); }
        }
        if (x.warna) x.warna.forEach(([id, w], i) => { if (t >= x.at + i * (x.jeda || 0.1)) warna[id] = w; });
        if (x.isi) x.isi.forEach(([id, val], i) => { const d = t - x.at - i * (x.jeda || 0.12); if (d >= 0) { v[id] = val; baru[id] = d; if (x.pratinjau && d < (x.lama || 0.9)) pra[id] = 1; } });
      });
      Object.keys(sel).forEach((id) => {
        const td = sel[id]; if (td.textContent !== v[id]) td.textContent = v[id];
        td.classList.toggle("pilih", id === pilih); td.classList.toggle("pra", !!pra[id]);
        ["merah", "kuning", "hijau"].forEach((w) => td.classList.toggle("w-" + w, warna[id] === w));
        const d = baru[id]; td.style.background = d != null && d < 0.6 ? `rgba(46,163,106,${0.35 * (1 - d / 0.6)})` : "";
      });
      nm.textContent = pilih || "";
      fi.textContent = bar != null ? bar : (pilih ? v[pilih] || "" : "");
    } };
  };

  // ---------- tombol keyboard ----------
  K.tombol = (s) => {
    const e = el("div", "tombol-w"), ks = (s.tombol || ["Ctrl", "E"]), tekan = s.tekan == null ? 0.5 : s.tekan;
    const B = ks.map((k, i) => { if (i) e.appendChild(el("span", "plus", "+")); return e.appendChild(el("span", "keycap", esc(k))); });
    if (s.teks) e.appendChild(el("div", "lb", fm(s.teks)));
    return { el: e, masuk: "zoom", sfx: [[tekan, "tick", 0.5], [tekan + 0.05, "pop", 0.35]], upd: (t) => {
      const d = t - tekan, k = d >= 0 && d < 0.35 ? 1 - Math.abs(d - 0.12) / 0.23 : 0;
      B.forEach((b) => { b.style.transform = `translateY(${8 * Math.max(0, k)}px)`; b.style.boxShadow = `0 ${10 - 8 * Math.max(0, k)}px 0 #1b1b1b`; b.classList.toggle("on", d >= 0 && d < 0.5); });
    } };
  };

  // ---------- tabel ----------
  K.tabel = (s) => {
    const t = el("table", "tabel");
    t.innerHTML = `<thead><tr>${(s.kolom || []).map((c) => `<th>${fm(c)}</th>`).join("")}</tr></thead>`;
    const tb = el("tbody"); t.appendChild(tb);
    const R = (s.baris || []).map((b) => { const r = el("tr", "b", b.map((c) => `<td>${fm(c)}</td>`).join("")); tb.appendChild(r); return r; });
    const jeda = s.jeda || 0.5, m = s.mulai || 0.3;
    const sfx = R.map((_, i) => [m + i * jeda, "tick", 0.35]).concat((s.sorot || []).map((o) => [o.at == null ? 1 : o.at, "ding", 0.5]));
    return { el: t, sfx, upd: (tt) => {
      R.forEach((r, i) => { const t0 = m + i * jeda; r.style.opacity = clamp((tt - t0) / 0.25); r.style.transform = `translateY(${(1 - ease((tt - t0) / 0.35)) * 24}px)`; });
      (s.sorot || []).forEach((o) => {
        const c = R[o.baris] && R[o.baris].children[o.kolom];
        if (!c) return;
        const a = o.at == null ? 1 : o.at, on = tt >= a, pul = on ? 0.5 + 0.5 * Math.sin((tt - a) * 8) : 0;
        c.style.background = on ? `rgba(255,122,47,${0.28 + 0.15 * pul})` : "transparent";
        c.style.fontWeight = on ? "700" : "400"; c.style.color = on ? "#b44a0a" : "";
        c.style.transform = on ? `scale(${1 + 0.06 * Math.max(0, 1 - (tt - a) * 4)})` : "none";
      });
    } };
  };

  // ---------- formulir / login (tiruan generik) ----------
  K.login = (s) => {
    const e = el("div", "form", `<h3>${fm(s.judul || "Masuk")}</h3>`), sfx = [];
    const m = s.mulai || 0.4, gap = s.jedaBidang || 1.3;
    const F = (s.bidang || []).map((b, i) => {
      const w = el("div", "bidang", `<label>${esc(b.label || "")}</label><div class="kolom"></div>`); e.appendChild(w);
      ticks(m + i * gap, String(b.nilai || "").length / (b.kec || 14), 0.07, 0.2).forEach((x) => sfx.push(x));
      return { k: w.querySelector(".kolom"), b };
    });
    const tb = el("div", "tombol", fm(s.tombol || "Masuk") + '<div class="riak"></div>'); e.appendChild(tb);
    const rk = tb.querySelector(".riak");
    const hs = el("div", "hasil" + (s.galat ? " galat" : ""), fm(s.hasil || "")); hs.style.opacity = 0; e.appendChild(hs);
    const ketuk = s.ketuk != null ? s.ketuk : m + F.length * gap + 0.3;
    sfx.push([ketuk, "klik", 0.6]); if (s.hasil) sfx.push([ketuk + 0.5, s.galat ? "buzz" : "ding", 0.5]);
    return { el: e, masuk: "naik", sfx, upd: (t) => {
      F.forEach(({ k, b }, i) => {
        const t0 = m + i * gap, v = String(b.nilai || ""), n = jumlahKetik(t - t0, v.length, b.kec || 14);
        const aktif = t >= t0 && t < t0 + gap, cur = aktif ? `<span class="kursor" style="opacity:${kedip()}">▍</span>` : "";
        k.className = "kolom" + (aktif ? " fokus" : "");
        k.innerHTML = b.sensor ? "•".repeat(Math.max(0, n)) + cur : esc(v.slice(0, Math.max(0, n))) + cur;
      });
      const q = clamp((t - ketuk) / 0.3);
      tb.style.transform = `scale(${1 - 0.08 * Math.sin(q * Math.PI)})`;
      tb.style.background = t >= ketuk ? "#e0601a" : "";
      const r = clamp((t - ketuk) / 0.6); rk.style.opacity = t >= ketuk ? 1 - r : 0; rk.style.transform = `scale(${1 + r * 14})`;
      hs.style.opacity = clamp((t - ketuk - 0.5) / 0.3);
      hs.style.transform = `translateY(${(1 - ease((t - ketuk - 0.5) / 0.4)) * 14}px)`;
    } };
  };

  // ---------- bingkai ponsel & jendela ----------
  K.ponsel = (s) => {
    const e = el("div", "ponsel"); e.style.width = (s.lebar || 560) + "px";
    const l = el("div", "layar"); e.appendChild(l);
    const ch = anak(s.anak, l);
    return { el: e, masuk: "naik", kids: ch, upd: (t) => updAnak(ch, t) };
  };
  K.jendela = (s) => {
    const e = el("div", "jendela", `<div class="bar"><i></i><i></i><i></i><span>${esc(s.url || s.judul || "aplikasi")}</span></div>`);
    const b = el("div", "badan"); e.appendChild(b);
    const ch = anak(s.anak, b);
    return { el: e, masuk: "naik", kids: ch, upd: (t) => updAnak(ch, t) };
  };

  // ---------- grafik ----------
  K.grafik = (s) => {
    const e = el("div", "grafik", s.judul ? `<h4>${fm(s.judul)}</h4>` : "");
    const nil = s.nilai || [], mx = s.maks || Math.max(...nil, 1), lab = s.label || [], sat = s.satuan || "";
    const fmt = (v) => (s.awalan || "") + rupiah(v, s.desimal || 0) + sat, m = s.mulai || 0.3;
    if (s.jenis === "garis") {
      const W = 840, H = 260, pad = 20, pts = nil.map((v, i) => [pad + (W - 2 * pad) * (nil.length === 1 ? 0.5 : i / (nil.length - 1)), H - pad - (H - 2 * pad) * (v / mx)]);
      const d = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
      const svg = el("div", "", `<svg viewBox="0 0 ${W} ${H}"><path d="${d}" fill="none" stroke="#ff7a2f" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>${pts.map((p) => `<circle cx="${p[0]}" cy="${p[1]}" r="11" fill="#14213d" opacity="0"/>`).join("")}</svg>`);
      e.appendChild(svg);
      const ls = el("div", "", lab.map((l) => `<span>${esc(l)}</span>`).join("")); ls.style.cssText = "display:flex;justify-content:space-between;font-size:25px;color:#7b6a52;margin-top:8px"; e.appendChild(ls);
      const path = svg.querySelector("path"), cs = svg.querySelectorAll("circle");
      return { el: e, masuk: "naik", sfx: [[m, "swish", 0.35]], upd: (t) => { const g = ease((t - m) / (s.dur || 1.6)); path.setAttribute("stroke-dashoffset", 1 - g); cs.forEach((c, i) => { const on = g >= (i / Math.max(1, nil.length - 1)) - 0.01; c.setAttribute("opacity", on ? 1 : 0); }); } };
    }
    const w = el("div", "batang-w"); e.appendChild(w);
    const Bs = nil.map((v, i) => {
      const b = el("div", "batang" + (s.sorot === i ? " hi" : ""), `<div class="nl"></div><div class="isi-b"></div><div class="lb">${esc(lab[i] || "")}</div>`);
      w.appendChild(b); return { b, v, ib: b.querySelector(".isi-b"), nl: b.querySelector(".nl") };
    });
    return { el: e, masuk: "naik", sfx: Bs.map((_, i) => [m + i * 0.18 + 0.1, "tick", 0.4]), upd: (t) => Bs.forEach(({ ib, nl, v }, i) => {
      const g = ease((t - m - i * 0.18) / (s.dur || 0.8));
      ib.style.height = (g * (v / mx) * 190) + "px"; nl.textContent = g > 0.5 ? fmt(v) : "";
    }) };
  };

  // ---------- cuplikan kode ----------
  const KW = /^(const|let|var|function|return|if|else|for|while|import|from|export|async|await|def|class|try|catch|new|true|false|null|SELECT|FROM|WHERE|INSERT|INTO|UPDATE|SET|VALUES|AND|OR|select|from|where|insert|into|update|set|values)$/;
  function tokenKode(line) {
    const out = []; const re = /(\/\/.*|#.*|--.*)|("[^"]*"|'[^']*'|`[^`]*`)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)|(\s+|.)/g; let m;
    while ((m = re.exec(line))) {
      if (m[1]) out.push([m[1], "cm"]); else if (m[2]) out.push([m[2], "st"]); else if (m[3]) out.push([m[3], "nm"]);
      else if (m[4]) out.push([m[4], KW.test(m[4]) ? "kw" : ""]); else out.push([m[5], ""]);
    }
    return out;
  }
  K.kode = (s) => {
    const e = el("div", "kode"); const lines = (s.baris || []).map((l) => ({ tok: tokenKode(l), len: l.length, w: e.appendChild(el("span", "ln")) }));
    const total = lines.reduce((a, l) => a + l.len, 0), kec = s.kec || 45;
    const hi = s.sorot || [], hiAt = s.sorotAt == null ? (total / kec + 0.4) : s.sorotAt;
    const sfx = ticks(0.3, total / kec, 0.055, 0.18); if (hi.length) sfx.push([hiAt, "ding", 0.4]);
    return { el: e, masuk: "naik", sfx, upd: (t) => {
      let sisa = Math.floor(Math.max(0, t - 0.3) * kec);
      lines.forEach((l, i) => {
        let h = "", n = Math.min(sisa, l.len); sisa -= n;
        for (const [txt, c] of l.tok) { if (n <= 0) break; const p = txt.slice(0, n); n -= p.length; h += c ? `<span class="${c}">${esc(p)}</span>` : esc(p); }
        l.w.innerHTML = h || " "; l.w.className = "ln" + (hi.includes(i) && t >= hiAt ? " hi" : "");
      });
    } };
  };

  // ---------- sebelum / sesudah ----------
  K.bandingkan = (s) => {
    const kol = (o, cls, tanda) => { const d = el("div", cls, `<h4>${fm(o.judul || (cls === "l" ? "Sebelum" : "Sesudah"))}</h4>`); const its = (o.item || []).map((x) => d.appendChild(el("div", "it", `<span style="color:${cls === "l" ? "#c8372d" : "#2ea36a"};font-weight:700">${tanda}</span><span>${fm(x)}</span>`))); return { d, its }; };
    const e = el("div", "band"), L = kol(s.kiri || {}, "l", "✕"), R = kol(s.kanan || {}, "r", "✓");
    e.appendChild(L.d); e.appendChild(R.d);
    const m = s.mulai || 0.2, jeda = s.jeda || 0.5, nL = L.its.length, rs = m + nL * jeda + 0.3;
    const sfx = L.its.map((_, i) => [m + i * jeda, "tick", 0.35]).concat(R.its.map((_, i) => [rs + i * jeda, "pop", 0.35]));
    return { el: e, masuk: "naik", sfx, upd: (t) => {
      L.its.forEach((x, i) => { const a = m + i * jeda; x.style.opacity = clamp((t - a) / 0.25); x.style.transform = `translateX(${(1 - ease((t - a) / 0.35)) * -36}px)`; });
      R.d.style.opacity = clamp((t - rs + 0.3) / 0.3);
      R.its.forEach((x, i) => { const a = rs + i * jeda; x.style.opacity = clamp((t - a) / 0.25); x.style.transform = `translateX(${(1 - ease((t - a) / 0.35)) * 36}px)`; });
    } };
  };

  // ---------- garis waktu ----------
  K.garis_waktu = (s) => {
    const e = el("div", "garis-w"), g = el("div", "g", "<i></i>"); e.appendChild(g);
    const P = (s.titik || []), n = P.length, jeda = s.jeda || 0.9, m = s.mulai || 0.3;
    const T_ = P.map((p, i) => {
      const x = n === 1 ? 50 : 6 + (88 * i) / (n - 1);
      const d = el("div", "titik"); d.style.left = x + "%"; g.appendChild(d);
      const l = el("div", "titik-t", `<b>${esc(p.jam || "")}</b>${fm(p.teks || "")}`); l.style.left = x + "%"; e.appendChild(l);
      return { d, l, x };
    });
    const bar = g.firstChild;
    return { el: e, masuk: "naik", sfx: T_.map((_, i) => [m + i * jeda, "pop", 0.4]), upd: (t) => {
      T_.forEach(({ d, l }, i) => { const t0 = m + i * jeda; d.className = "titik" + (t >= t0 ? " on" : ""); d.style.transform = t >= t0 ? `scale(${1 + 0.6 * Math.max(0, 1 - (t - t0) * 4)})` : "scale(1)"; l.style.opacity = clamp((t - t0) / 0.3); l.style.transform = `translateX(-50%) translateY(${(1 - ease((t - t0) / 0.4)) * 14}px)`; });
      const idx = n > 1 ? clamp((t - m) / (jeda * (n - 1))) : (t >= m ? 1 : 0);
      bar.style.width = (t >= m ? 6 + 88 * idx : 0) + "%";
    } };
  };

  // ---------- donat persen ----------
  K.donat = (s) => {
    const W = { hijau: "#2ea36a", merah: "#c8372d", cyan: "#22c3e6", navy: "#14213d" }[s.warna] || "#ff7a2f";
    const e = el("div", "donat", `<svg viewBox="0 0 300 300"><circle cx="150" cy="150" r="118" fill="none" stroke="#e8dfcd" stroke-width="40"/><circle class="arc" cx="150" cy="150" r="118" fill="none" stroke="${W}" stroke-width="40" stroke-linecap="round" pathLength="100" stroke-dasharray="0 100" transform="rotate(-90 150 150)"/></svg><div class="dn"><b></b>${s.teks ? `<span>${fm(s.teks)}</span>` : ""}</div>${s.label ? `<div class="dl">${fm(s.label)}</div>` : ""}`);
    const arc = e.querySelector(".arc"), b = e.querySelector(".dn b"), m = s.mulai || 0.3, v = s.nilai == null ? 75 : s.nilai;
    return { el: e, masuk: "zoom", sfx: ticks(m, s.dur || 1.3, 0.08, 0.18).concat([[m + (s.dur || 1.3), "ding", 0.35]]), upd: (t) => {
      const x = v * ease((t - m) / (s.dur || 1.3)); arc.setAttribute("stroke-dasharray", `${x} ${100 - x}`); b.textContent = Math.round(x) + (s.satuan == null ? "%" : s.satuan);
    } };
  };

  // ---------- kuis pilihan ganda (hitung mundur lalu jawaban benar menyala) ----------
  K.kuis = (s) => {
    const e = el("div", "kuis", `<div class="kq">${fm(s.tanya || "")}</div><div class="kt"><i></i></div>`);
    const jw = s.jawab == null ? 3 : s.jawab, bar = e.querySelector(".kt i"), H = "ABCDEF";
    const O = (s.opsi || []).map((o, i) => { const b = el("div", "ko", `<span class="kh">${H[i]}</span><span>${fm(o)}</span><span class="kx"></span>`); e.appendChild(b); return b; });
    const sfx = ticks(0.5, Math.max(0, jw - 0.6), 1, 0.3).concat([[jw, "ding", 0.55]]);
    const salah = s.pilih != null && s.pilih !== s.benar; if (salah) sfx.push([jw - 0.7, "buzz", 0.35]);
    return { el: e, masuk: "naik", sfx, upd: (t) => {
      bar.style.width = (100 * (1 - clamp((t - 0.4) / (jw - 0.4)))) + "%";
      O.forEach((b, i) => {
        const tl = t - 0.3 - i * 0.18; b.style.opacity = clamp(tl / 0.2); b.style.transform = `translateX(${(1 - ease(tl / 0.35)) * -40}px)`;
        let c = "ko";
        if (salah && i === s.pilih && t >= jw - 0.7) c += " salah";
        if (t >= jw) { if (i === s.benar) c += " benar"; else if (!(salah && i === s.pilih)) c += " redup"; }
        b.className = c; b.querySelector(".kx").textContent = c.includes("benar") ? "✓" : c.includes("salah") ? "✕" : "";
        if (t >= jw && i === s.benar) b.style.transform += ` scale(${1 + 0.05 * Math.max(0, 1 - (t - jw) * 3)})`;
      });
    } };
  };

  // ---------- tanya AI: ketik prompt, kirim, AI berpikir, jawaban mengalir per kata ----------
  K.tanya_ai = (s) => {
    const tanya = String(s.tanya || ""), kec = s.kec || 30, t0 = s.ketik_at || 0.3;
    const kirim = s.kirim != null ? s.kirim : t0 + tanya.length / kec + 0.3, ja = s.jawab_at != null ? s.jawab_at : kirim + 1.0;
    const jawab = Array.isArray(s.jawab) ? s.jawab.join("\n") : String(s.jawab || ""), kata = jawab.split(/(\s+)/), kpd = s.kec_jawab || 9;
    const e = el("div", "tai", `<div class="th"><span class="ik">${s.ikon || "✦"}</span>${esc(s.nama || "Asisten AI")}</div><div class="tc"><div class="gel kanan tq"></div><div class="mengetik">•••</div><div class="ta"></div></div><div class="tin"><div class="tx"></div><div class="tk">➤</div></div>`);
    const tq = e.querySelector(".tq"), dots = e.querySelector(".mengetik"), ta = e.querySelector(".ta"), tx = e.querySelector(".tx"), tk = e.querySelector(".tk");
    const nKata = kata.filter((k) => k.trim()).length, lama = nKata / kpd;
    const sfx = ticks(t0, tanya.length / kec, 0.085, 0.18).concat([[kirim, "swish", 0.4], [ja, "pop", 0.35]]).concat(ticks(ja, lama, 0.12, 0.1));
    return { el: e, masuk: "naik", sfx, upd: (t) => {
      const n = t < kirim ? Math.max(0, jumlahKetik(t - t0, tanya.length, kec)) : 0;
      tx.innerHTML = t < kirim ? (t >= t0 ? ketikHTML(tanya, n, true) : `<span class="ph">${esc(s.placeholder || "Tanya apa saja...")}</span>`) : `<span class="ph">${esc(s.placeholder || "Tanya apa saja...")}</span>`;
      tk.className = "tk" + (t >= kirim - 0.15 && t < kirim + 0.2 ? " on" : "");
      tq.style.display = t >= kirim ? "" : "none"; tq.textContent = tanya;
      tq.style.transform = `translateY(${(1 - back((t - kirim) / 0.35)) * 30}px)`;
      dots.style.display = t >= kirim + 0.25 && t < ja ? "" : "none"; dots.textContent = "•".repeat(1 + Math.floor(t * 4) % 3);
      if (t < ja) { ta.style.display = "none"; return; }
      ta.style.display = "";
      const k = Math.floor((t - ja) * kpd); let c = 0, out = "";
      for (const w of kata) { if (w.trim()) { if (c >= k) break; c++; } out += w; }
      ta.innerHTML = fm(out).replace(/\n/g, "<br>") + (c < nKata ? `<span class="kursor" style="opacity:${kedip()}">▍</span>` : "");
    } };
  };

  // ---------- email (tulis / baca) ----------
  K.email = (s) => {
    const isi = String(s.isi || ""), kec = s.kec || 40, m = s.mulai || 0.5, ketik = s.ketik !== false;
    const e = el("div", "email", `<div class="eh"><span class="d"></span><span class="d"></span><span class="d"></span><b>${esc(s.judul || "Pesan baru")}</b></div>` +
      (s.dari ? `<div class="ef"><span>Dari</span>${fm(s.dari)}</div>` : "") + (s.kepada ? `<div class="ef"><span>Kepada</span>${fm(s.kepada)}</div>` : "") +
      `<div class="ef"><span>Subjek</span><b>${fm(s.subjek || "")}</b></div><div class="eb"></div>` + (s.kirim != null ? `<div class="es"><span class="eb2">Kirim ➤</span><span class="ok">✓ Terkirim</span></div>` : ""));
    const eb = e.querySelector(".eb"), btn = e.querySelector(".eb2"), ok = e.querySelector(".ok");
    const sfx = ketik ? ticks(m, isi.length / kec, 0.085, 0.16) : []; if (s.kirim != null) sfx.push([s.kirim, "klik", 0.5], [s.kirim + 0.25, "ding", 0.4]);
    return { el: e, masuk: "naik", sfx, upd: (t) => {
      const n = ketik ? Math.max(0, jumlahKetik(t - m, isi.length, kec)) : isi.length;
      eb.innerHTML = ketikHTML(isi, n, ketik && n < isi.length && t >= m).replace(/\n/g, "<br>");
      if (btn) { btn.style.transform = `scale(${t >= s.kirim && t < s.kirim + 0.15 ? 0.9 : 1})`; ok.style.opacity = clamp((t - s.kirim - 0.2) / 0.2); }
    } };
  };

  // ---------- kalender bulan ----------
  K.kalender = (s) => {
    const hari = s.hari || 31, mulai = s.mulai || 0, nm = s.nama_hari || ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"];
    const e = el("div", "kal", `<div class="kalh">${fm(s.bulan || "")}</div><div class="kg">${nm.map((h) => `<span class="hn">${esc(h)}</span>`).join("")}${"<span></span>".repeat(mulai)}</div>`);
    const g = e.querySelector(".kg"), sel = {};
    for (let d = 1; d <= hari; d++) { const c = el("span", "kd", String(d)); g.appendChild(c); sel[d] = c; }
    const T_ = (s.tandai || []).map((x, i) => (typeof x === "number" ? { tgl: x } : x)).map((x, i) => Object.assign({ at: 0.6 + i * 0.4 }, x));
    const lab = el("div", "kl"); e.appendChild(lab);
    return { el: e, masuk: "naik", sfx: T_.map((x) => [x.at, "pop", 0.4]), upd: (t) => {
      let teks = "";
      T_.forEach((x) => { const c = sel[x.tgl]; if (!c) return; const on = t >= x.at; c.className = "kd" + (on ? " on " + (x.warna || "") : ""); c.style.transform = on ? `scale(${1 + 0.5 * Math.max(0, 1 - (t - x.at) * 4)})` : ""; if (on && x.teks) teks = `<b>${x.tgl}</b> ${fm(x.teks)}`; });
      lab.innerHTML = teks; lab.style.opacity = teks ? 1 : 0;
    } };
  };

  // ---------- meter / spidometer ----------
  K.meter = (s) => {
    const e = el("div", "meter", `<svg viewBox="0 0 400 230"><defs><linearGradient id="mg" x1="0" x2="1"><stop offset="0" stop-color="#c8372d"/><stop offset=".5" stop-color="#f2b705"/><stop offset="1" stop-color="#2ea36a"/></linearGradient></defs><path d="M40 200 A160 160 0 0 1 360 200" fill="none" stroke="url(#mg)" stroke-width="34" stroke-linecap="round"/><g class="jr"><path d="M200 200 L200 62" stroke="#14213d" stroke-width="10" stroke-linecap="round"/></g><circle cx="200" cy="200" r="20" fill="#14213d"/></svg><div class="ml"><span>${fm(s.kiri || "")}</span><b></b><span>${fm(s.kanan || "")}</span></div>${s.label ? `<div class="dl">${fm(s.label)}</div>` : ""}`);
    const j = e.querySelector(".jr"), b = e.querySelector(".ml b"), m = s.mulai || 0.3, a0 = s.dari || 0, v = s.nilai == null ? 80 : s.nilai;
    return { el: e, masuk: "zoom", sfx: [[m, "swish", 0.35], [m + (s.dur || 1.4), "ding", 0.3]], upd: (t) => {
      const g = back((t - m) / (s.dur || 1.4)), x = a0 + (v - a0) * g; j.setAttribute("transform", `rotate(${-90 + 1.8 * x + Math.sin(t * 25) * 0.6} 200 200)`);
      b.textContent = s.teks_nilai || Math.round(clamp(x, 0, 100)) + (s.satuan || "");
    } };
  };

  // ---------- ikon berkas (xlsx/pdf/doc/img/zip/ppt/mp4) ----------
  const WB = { xlsx: "#1f8a4c", csv: "#1f8a4c", pdf: "#d33b2c", doc: "#2b5fb3", docx: "#2b5fb3", ppt: "#d0662b", pptx: "#d0662b", img: "#7b4fc9", jpg: "#7b4fc9", png: "#7b4fc9", zip: "#6b5b45", mp4: "#c4306a", mp3: "#0f8f8f", txt: "#555" };
  K.berkas = (s) => {
    const e = el("div", "berkas-w"), m = s.mulai || 0.3, jd = s.jeda || 0.3;
    const B = (s.item || []).map((x) => { const o = typeof x === "string" ? { nama: x } : x; const ext = (o.jenis || (o.nama.split(".").pop())).toLowerCase();
      const b = el("div", "bk", `<div class="bf"><i style="background:${WB[ext] || "#555"}">${esc(ext.toUpperCase())}</i></div><span>${fm(o.nama)}</span>`); e.appendChild(b); return b; });
    return { el: e, masuk: "muncul", sfx: B.map((_, i) => [m + i * jd, "pop", 0.35]), upd: (t) => B.forEach((b, i) => {
      const tl = t - m - i * jd; b.style.opacity = clamp(tl / 0.15); b.style.transform = `translateY(${(1 - back(tl / 0.4)) * 50}px) rotate(${(i % 2 ? 3 : -3) * (1 - ease(tl / 0.5))}deg)`;
    }) };
  };

  // ---------- kolom pencarian + hasil ----------
  K.pencarian = (s) => {
    const q = String(s.kueri || ""), kec = s.kec || 22, m = s.mulai || 0.3, tc = s.cari != null ? s.cari : m + q.length / kec + 0.3;
    const e = el("div", "cari", `<div class="cb"><span class="ik">⌕</span><span class="cq"></span></div><div class="ch"></div>`);
    const cq = e.querySelector(".cq"), ch = e.querySelector(".ch");
    const H = (s.hasil || []).map((x) => { const o = typeof x === "string" ? { judul: x } : x; const r = el("div", "cr", `<b>${fm(o.judul)}</b>${o.sub ? `<span>${fm(o.sub)}</span>` : ""}`); ch.appendChild(r); return r; });
    return { el: e, masuk: "naik", sfx: ticks(m, q.length / kec, 0.09, 0.18).concat([[tc, "klik", 0.45]]).concat(H.map((_, i) => [tc + 0.3 + i * 0.25, "pop", 0.25])), upd: (t) => {
      const n = Math.max(0, jumlahKetik(t - m, q.length, kec)); cq.innerHTML = t >= m ? ketikHTML(q, n, t < tc) : `<span style="opacity:.45">${esc(s.placeholder || "Cari...")}</span>`;
      H.forEach((r, i) => { const tl = t - tc - 0.3 - i * 0.25; r.style.opacity = clamp(tl / 0.2); r.style.transform = `translateY(${(1 - ease(tl / 0.3)) * 20}px)`; r.classList.toggle("hi", s.sorot === i && t >= (s.sorot_at || tc + 1.2 + i * 0.25)); });
    } };
  };

  // ---------- baris pengaturan dengan sakelar ----------
  K.pengaturan = (s) => {
    const e = el("div", "atur", s.judul ? `<h4>${fm(s.judul)}</h4>` : "");
    const B = (s.item || []).map((x, i) => { const o = typeof x === "string" ? { teks: x } : x; const r = el("div", "ar", `<div><b>${fm(o.teks)}</b>${o.sub ? `<span>${fm(o.sub)}</span>` : ""}</div><i class="sk"><u></u></i>`); e.appendChild(r); return { r, o, sk: r.querySelector(".sk") }; });
    return { el: e, masuk: "naik", sfx: B.filter((x) => x.o.at != null).map((x) => [x.o.at, "klik", 0.5]), upd: (t) => B.forEach(({ r, o, sk }) => {
      const awal = !!o.awal, on = o.at != null && t >= o.at ? !awal : awal; sk.className = "sk" + (on ? " on" : "");
      r.classList.toggle("hi", o.at != null && t >= o.at - 0.4 && t < o.at + 0.9);
    }) };
  };

  // ---------- gelombang suara (pesan suara / narasi AI) ----------
  K.gelombang = (s) => {
    const N = s.batang || 34, R = rng(7), h = Array.from({ length: N }, () => 0.25 + R() * 0.75), m = s.mulai || 0.3, lama = s.lama || 3;
    const e = el("div", "gelo", `<span class="gp">▶</span><div class="gb">${h.map(() => "<i></i>").join("")}</div><span class="gw"></span>`);
    const I = e.querySelectorAll(".gb i"), gw = e.querySelector(".gw"), gp = e.querySelector(".gp");
    if (s.teks) e.appendChild(el("div", "gt", fm(s.teks)));
    return { el: e, masuk: "naik", sfx: [[m, "klik", 0.4]], upd: (t) => {
      const p = clamp((t - m) / lama), main = t >= m && p < 1; gp.textContent = main ? "❚❚" : "▶";
      I.forEach((b, i) => { const sudah = i / N < p; const amp = main ? h[i] * (0.6 + 0.4 * Math.sin(t * 14 + i)) : h[i]; b.style.height = (12 + 70 * amp) + "px"; b.style.background = sudah ? "var(--orange)" : "#cbbfa8"; });
      const d = Math.floor(lama * (main ? p : p >= 1 ? 1 : 0)); gw.textContent = `0:${String(t >= m ? d : Math.floor(lama)).padStart(2, "0")}`;
    } };
  };

  // ---------- kartu prompt siap salin: [isian] disorot, tombol Salin ditekan ----------
  K.prompt = (s) => {
    const teks = String(s.teks || ""), kec = s.kec || 0, m = s.mulai || 0.3;
    const html = (n) => { const x = esc(teks.slice(0, n)).replace(/\n/g, "<br>"); return x.replace(/\[([^\]]*)\]?/g, (a, b) => `<mark>[${b}${a.endsWith("]") ? "]" : ""}</mark>`); };
    const e = el("div", "prm", `<div class="ph2"><span>${fm(s.judul || "Prompt")}</span><span class="salin">⧉ Salin</span></div><div class="pb"></div>`);
    const pb = e.querySelector(".pb"), sl = e.querySelector(".salin"), ts = s.salin;
    const sfx = kec ? ticks(m, teks.length / kec, 0.085, 0.15) : [];
    if (ts != null) sfx.push([ts, "klik", 0.5], [ts + 0.2, "ding", 0.35]);
    return { el: e, masuk: "naik", sfx, upd: (t) => {
      const n = kec ? Math.max(0, jumlahKetik(t - m, teks.length, kec)) : teks.length;
      pb.innerHTML = html(n) + (kec && n < teks.length ? `<span class="kursor" style="opacity:${kedip()}">▍</span>` : "");
      pb.querySelectorAll("mark").forEach((k, i) => { k.style.backgroundSize = (100 * ease((t - (s.sorot_at || m + 0.5) - i * 0.25) / 0.4)) + "% 100%"; });
      if (ts != null) { const on = t >= ts; sl.textContent = on ? "✓ Tersalin" : "⧉ Salin"; sl.className = "salin" + (on ? " on" : ""); sl.style.transform = `scale(${t >= ts && t < ts + 0.15 ? 0.88 : 1})`; }
    } };
  };

  // ---------- stopwatch: waktu berjalan cepat sampai target (bandingkan manual vs AI) ----------
  K.stopwatch = (s) => {
    const W = (s.baris || [{ label: "Manual", detik: 1800 }, { label: "Pakai AI", detik: 120, warna: "hijau" }]);
    const e = el("div", "stw"), m = s.mulai || 0.3, dur = s.dur || 1.8, mx = Math.max(...W.map((w) => w.detik));
    const R = W.map((w) => { const r = el("div", "sr " + (w.warna || ""), `<span class="sl">${fm(w.label)}</span><div class="sb"><i></i></div><b>00:00</b>`); e.appendChild(r); return { r, w, i: r.querySelector("i"), b: r.querySelector("b") }; });
    const mmss = (x) => { x = Math.round(x); const h = Math.floor(x / 3600), mm = Math.floor(x / 60) % 60, ss = x % 60; return (h ? h + ":" + String(mm).padStart(2, "0") : String(mm).padStart(2, "0")) + ":" + String(ss).padStart(2, "0"); };
    return { el: e, masuk: "naik", sfx: ticks(m, dur, 0.1, 0.15).concat([[m + dur, "ding", 0.4]]), upd: (t) => R.forEach(({ w, i, b }) => {
      const g = clamp((t - m) / (dur * w.detik / mx)), x = w.detik * g; i.style.width = (100 * x / mx) + "%"; b.textContent = mmss(x);
    }) };
  };

  // ---------- layar HP berisi ikon: kepadatan berubah (sebelum/sesudah ubah DPI / lebar terkecil) ----------
  K.layarhp = (s) => {
    const W = s.lebar || 330, H = Math.round(W * 1.9), n = s.jumlah || 24, k0 = s.kolom_awal || 4, k1 = s.kolom_akhir || k0, tU = s.ubah;
    const warna = ["#ff7a2f", "#22c3e6", "#2ea36a", "#7b4fc9", "#e0457b", "#f2b705", "#14213d", "#d0662b"];
    const e = el("div", "lhp"); e.style.width = W + "px"; e.style.height = H + "px";
    e.innerHTML = `<div class="lhp-st"><span>09.41</span><span>▮▮ ◔</span></div><div class="lhp-cari"></div><div class="lhp-g"></div>${s.label ? `<div class="lhp-lb">${fm(s.label)}</div>` : ""}`;
    const g = e.querySelector(".lhp-g"), cari = e.querySelector(".lhp-cari"), lb = e.querySelector(".lhp-lb");
    const I = Array.from({ length: n }, (_, i) => { const d = el("i"); d.style.background = warna[i % warna.length]; d.appendChild(el("b")); g.appendChild(d); return d; });
    const lay = (k) => { const pad = W * 0.07, gw = W - pad * 2, cell = gw / k, sz = cell * 0.62; return I.map((_, i) => ({ x: pad + (i % k) * cell + (cell - sz) / 2, y: (Math.floor(i / k)) * cell * 1.18, sz })); };
    const A = lay(k0), B = lay(k1);
    return { el: e, masuk: s.masuk || "naik", sfx: tU != null ? [[tU, "swish", 0.4], [tU + 0.8, "ding", 0.35]] : [], upd: (t) => {
      const q = tU == null ? 0 : ease((t - tU) / 0.8);
      I.forEach((d, i) => { const a = A[i], b = B[i], x = a.x + (b.x - a.x) * q, y = a.y + (b.y - a.y) * q, z = a.sz + (b.sz - a.sz) * q;
        d.style.transform = `translate(${x}px,${y}px)`; d.style.width = d.style.height = z + "px"; d.style.borderRadius = z * 0.28 + "px"; d.firstChild.style.width = z * 0.7 + "px"; });
      cari.style.height = (W * (0.11 - 0.025 * q)) + "px";
      if (lb && s.label2) lb.innerHTML = fm(q > 0.5 ? s.label2 : s.label);
    } };
  };

  // ---------- perakitan halaman ----------
  const SPEC = window.SPEC || {};
  document.body.className = SPEC.latar || "gabus";
  document.body.innerHTML = '<div id="latar"><svg><filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" seed="4"/><feColorMatrix values="0 0 0 0 .35  0 0 0 0 .22  0 0 0 0 .1  0 0 0 .9 0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg></div><div id="dekor"></div><div id="papan"><div id="atas"></div><div id="isi"><div id="isi-dalam"></div></div><div id="bawah"></div><div id="fx"></div></div><div id="kilat"></div>';

  // latar hidup: bokeh + serpih kertas yang melayang pelan
  const dekor = document.getElementById("dekor"), R = rng(11), dk = [];
  const warnaBokeh = { gabus: "255,235,200", gelap: "120,180,255", kertas: "255,160,90", biru: "180,230,255" }[SPEC.latar || "gabus"] || "255,255,255";
  for (let i = 0; i < (SPEC.dekor === false ? 0 : 9); i++) {
    const d = el("i"), r = 50 + R() * 110; d.style.cssText = `width:${r}px;height:${r}px;left:${R() * 1000 - 40}px;top:${R() * 1800}px;background:rgba(${warnaBokeh},${0.05 + R() * 0.07});filter:blur(${6 + R() * 10}px)`;
    dekor.appendChild(d); dk.push({ d, a: 20 + R() * 40, w: 0.25 + R() * 0.35, ph: R() * 6, rot: 0 });
  }
  if ((SPEC.latar || "gabus") === "gabus") {
    const cs = ["#ffe27a", "#ffb4a8", "#bfeab0", "#b8e3f5"];
    [[-30, 1500, -12], [930, 1560, 9], [-40, 1180, 7], [960, 1380, -8], [900, 40, 10]].forEach(([x, y, r], i) => {
      const d = el("i", "serpih"); d.style.cssText = `width:${110 + R() * 60}px;height:${110 + R() * 60}px;left:${x}px;top:${y}px;background:${cs[i % 4]};opacity:.75`;
      dekor.appendChild(d); dk.push({ d, a: 10 + R() * 12, w: 0.3 + R() * 0.2, ph: R() * 6, rot: r, serpih: true });
    });
  }

  const ROT = [-1.2, 0.9, -0.7, 1.1];
  const jedaOto = SPEC.jeda || 1.5;
  let cur = 0.8;
  const siap = (list) => (list || []).map((s, i) => {
    const o = Object.assign({}, s);
    if (o.at == null) { o.at = cur; cur += (o.sela != null ? o.sela : jedaOto); } else { cur = Math.max(cur, o.at + jedaOto); }
    if (o.rot == null && (o.tipe === "kartu" || o.tipe === "tempel")) o.rot = ROT[i % ROT.length];
    return o;
  });

  const itemsAtas = [];
  if (SPEC.judul) {
    const j = typeof SPEC.judul === "string" ? { teks: SPEC.judul } : SPEC.judul;
    const n = bangun(Object.assign({ tipe: "tempel", at: 0.1, rot: -2.2, masuk: "jatuh" }, j));
    n.el.style.position = "absolute"; n.el.style.left = "60px"; n.el.style.top = "110px"; n.el.style.width = "auto";
    document.getElementById("atas").appendChild(n.el); itemsAtas.push(n);
  }
  if (SPEC.stempel !== null && SPEC.stempel !== false) {
    const n = bangun({ tipe: "stempel", teks: typeof SPEC.stempel === "string" ? SPEC.stempel : "ILUSTRASI", at: 0.5, rot: -8, masuk: "ketuk" });
    n.el.style.position = "absolute"; n.el.style.right = "50px"; n.el.style.top = SPEC.peta ? "135px" : "190px"; n.el.style.width = "auto";
    document.getElementById("atas").appendChild(n.el); itemsAtas.push(n);
  }
  const isi = siap(SPEC.isi).map(bangun);
  isi.forEach((n) => document.getElementById("isi-dalam").appendChild(n.el));
  const bawah = siap(SPEC.bawah).map(bangun);
  bawah.forEach((n) => document.getElementById("bawah").appendChild(n.el));

  // muat: kecilkan bila lebih tinggi dari area (330..1340), perbesar sedikit bila pendek
  const dalam = document.getElementById("isi-dalam"), tinggi = dalam.offsetHeight;
  if (tinggi) dalam.style.transform = `scale(${tinggi > 1010 ? 1010 / tinggi : Math.min(1.08, 1010 / tinggi)})`;

  // ---------- ADEGAN: layar berganti; komponen di dalam adegan memakai waktu relatif awal adegan ----------
  const latarAdg = el("div"); latarAdg.id = "latar-adegan"; document.getElementById("latar").after(latarAdg);
  const ADG = (SPEC.adegan || []).map((a, i, arr) => {
    cur = 0.3;
    let bg = null;
    if (a.latar_gambar) {
      bg = el("div", "bg-adegan"); const im = el("img"); im.src = a.latar_gambar; bg.appendChild(im);
      if (a.redup) { const r = el("div", "redup"); r.style.background = `rgba(8,24,32,${a.redup})`; bg.appendChild(r); }
      bg.style.opacity = 0; latarAdg.appendChild(bg);
    }
    const box = el("div", "adegan"), d = el("div", "adegan-dalam"); box.appendChild(d);
    document.getElementById("isi").appendChild(box);
    const items = siap(a.isi).map(bangun); items.forEach((n) => d.appendChild(n.el));
    const h = d.offsetHeight, mk = a.maks || 1.4;
    const lebar = (e) => Math.max(e.getBoundingClientRect().width, e.scrollWidth, ...Array.from(e.querySelectorAll(".alur,.baris,table")).map((x) => x.scrollWidth));
    const lb = Math.max(1, ...items.map((n) => lebar(n.el.firstChild)));
    d.style.transform = `scale(${Math.min(mk, 1010 / h, 960 / lb)})`;
    box.style.display = "none"; box.style.visibility = "visible";
    const VAR = ["geser", "zoom", "naik", "flip", "kanan", "pudar"];
    return { at: a.at || 0, akhir: i + 1 < arr.length ? arr[i + 1].at : 1e9, items, box, bg, transisi: a.transisi || (SPEC.transisi === "acak" ? VAR[i % VAR.length] : SPEC.transisi) };
  });
  function perbaruiAdegan(A, t) {
    const tl = t - A.at, ke = t - A.akhir;
    if (A.bg) {
      const vis = tl >= -0.01 && ke < 0.5;
      A.bg.style.opacity = vis ? Math.min(clamp(tl / 0.5 + (A.at === 0 ? 1 : 0)), 1 - clamp(ke / 0.5)) : 0;
      A.bg.firstChild.style.transform = `scale(${1.04 + 0.06 * clamp(tl / Math.max(1, A.akhir - A.at))})`;
    }
    if (tl < 0 || ke > 0.4) { A.box.style.display = "none"; return; }
    A.box.style.display = "flex";
    const p = ke > 0 ? ease(ke / 0.35) : 0, tr = A.transisi || "geser";
    let tf = `translateX(${-160 * p}px) scale(${1 - 0.06 * p})`;
    if (tr === "zoom") tf = `scale(${1 + 0.35 * p})`;
    else if (tr === "naik") tf = `translateY(${-220 * p}px)`;
    else if (tr === "flip") tf = `perspective(1600px) rotateY(${-85 * p}deg)`;
    else if (tr === "pudar") tf = "none";
    else if (tr === "kanan") tf = `translateX(${160 * p}px) scale(${1 - 0.06 * p})`;
    A.box.style.opacity = 1 - p; A.box.style.transform = tf;
    A.items.forEach((n) => perbarui(n, tl));
  }

  // ---------- PETA ISI: tab bernomor yang menyala bergantian ----------
  let PETA = null;
  if (SPEC.peta) {
    const P = SPEC.peta, w = el("div", "peta" + ((P.item || []).length > 4 ? " banyak" : ""));
    const tabs = (P.item || []).map((x, i) => w.appendChild(el("div", "tab", `<b>${i + 1}</b><span>${P.sembunyi ? "? ? ?" : fm(x)}</span>`)));
    document.getElementById("atas").appendChild(w);
    PETA = { w, tabs, at: P.at || 0, aktif: (P.aktif || []).slice().sort((a, b) => a[0] - b[0]) };
  }
  function perbaruiPeta(t) {
    if (!PETA) return;
    const tl = t - PETA.at;
    PETA.w.style.opacity = clamp(tl / 0.25); PETA.w.style.transform = `translateY(${(1 - back(tl / 0.5)) * -60}px)`;
    let a = null, a0 = 0; PETA.aktif.forEach(([s, k]) => { if (t >= s) { a = k; a0 = s; } });
    const buka = new Set(); PETA.aktif.forEach(([s, k]) => { if (t >= s) { if (k === -1) PETA.tabs.forEach((_, j) => buka.add(j)); else buka.add(k); } });
    PETA.tabs.forEach((x, i) => {
      if (SPEC.peta.sembunyi) { const sp = x.querySelector("span"), isi = buka.has(i) ? fm(SPEC.peta.item[i]) : "? ? ?"; if (sp.innerHTML !== isi) sp.innerHTML = isi; }
      const on = a === i || a === -1, d0 = (t - PETA.at) - i * 0.15;
      x.classList.toggle("on", on);
      const pop = on ? 1 + 0.12 * Math.max(0, 1 - (t - a0) / 0.35) : 1;
      x.style.transform = `scale(${(0.6 + 0.4 * back(d0 / 0.4)) * pop})`; x.style.opacity = clamp(d0 / 0.2);
    });
  }

  // ---------- SUBTITLE kata per kata ----------
  const SUB = (SPEC.subtitle || []).map((x) => (Array.isArray(x) ? { t0: x[0], t1: x[1], teks: x[2] } : x)).sort((a, b) => a.t0 - b.t0);
  let subEl = null;
  if (SUB.length) {
    subEl = el("div", "sub" + (SPEC.sub_kotak ? " sub-kotak" : "")); document.getElementById("papan").appendChild(subEl);
    SUB.forEach((f) => {
      f.kata = String(f.teks).split(/\s+/).filter(Boolean);
      const bobot = f.kata.map((k) => 1 + k.replace(/[^\p{L}\p{N}]/gu, "").length), tot = bobot.reduce((a, b) => a + b, 0);
      let acc = 0; f.mulai = bobot.map((b) => { const v = f.t0 + (acc / tot) * (f.t1 - f.t0); acc += b; return v; });
    });
  }
  let subAktif = -1;
  function perbaruiSub(t) {
    if (!subEl) return;
    let k = -1; SUB.forEach((f, i) => { if (t >= f.t0 - 0.05) k = i; });
    if (k >= 0) { const f = SUB[k], nx = SUB[k + 1]; if (t > f.t1 + 0.6 && (!nx || t < nx.t0 - 0.05)) k = -1; }
    if (k !== subAktif) {
      subAktif = k;
      subEl.innerHTML = k < 0 ? "" : SUB[k].kata.map((w) => `<span>${esc(w)}</span>`).join(" ");
    }
    subEl.style.opacity = k < 0 ? 0 : 1;
    if (k < 0) return;
    const f = SUB[k], sp = subEl.children;
    let cur = -1; f.mulai.forEach((m, i) => { if (t >= m) cur = i; });
    for (let i = 0; i < sp.length; i++) sp[i].className = i < cur ? "lalu" : i === cur ? "kini" : "nanti";
    subEl.style.transform = `translateX(-50%) scale(${1 + 0.03 * Math.max(0, 1 - (t - f.t0) / 0.2)})`;
  }

  // ---------- TOKOH bulat di pojok, mulut mengikuti suara (data dari papan_buat.py) ----------
  let TK = null;
  if (window.TOKOH) {
    const o = window.TOKOH, w = el("div", "tokoh"), im = el("img");
    w.appendChild(im); document.getElementById("papan").appendChild(w);
    TK = { w, im, o, last: -1 };
    if (o.ukuran) { w.style.width = w.style.height = o.ukuran + "px"; }
    if (o.x != null) w.style.left = o.x + "px";
    if (o.y != null) w.style.top = o.y + "px";
    if (o.tempel) {  // mulut digambar di atas satu gambar
      const p = o.tempel, m = el("div", "mulut-t");
      m.style.left = p.x * 100 + "%"; m.style.top = p.y * 100 + "%"; m.style.width = p.w * 100 + "%"; m.style.setProperty("--kulit", p.kulit); m.style.setProperty("--bibir", p.bibir);
      m.innerHTML = '<svg viewBox="-50 -30 100 60"><ellipse class="tutup-kulit" cx="0" cy="0" rx="46" ry="22"/><path class="m0" d="M -26 2 Q 0 10 26 2"/><ellipse class="m1" cx="0" cy="3" rx="11" ry="12"/><g class="m2"><path d="M -28 -4 Q 0 -8 28 -4 Q 22 26 0 26 Q -22 26 -28 -4 Z"/><ellipse cx="0" cy="17" rx="13" ry="7" class="lidah"/></g></svg>';
      w.appendChild(m); TK.mt = m; im.src = o.img[0];
    }
  }
  function perbaruiTokoh(t) {
    if (!TK) return;
    const f = Math.max(0, Math.floor(t * (TK.o.fps || 30))), m = TK.o.mulut[f] || 0;
    if (TK.mt) { if (m !== TK.last) { TK.mt.className = "mulut-t s" + m; TK.last = m; } }
    else {
      const kd = TK.o.img.length > 3 && (t % 3.7) > 3.55 && m === 0 ? 3 : m;
      if (kd !== TK.last) { TK.im.src = TK.o.img[kd]; TK.last = kd; }
    }
    const a = TK.o.amp ? TK.o.amp[f] || 0 : 0, p = back((t - (TK.o.at || 0.2)) / 0.5);
    TK.w.style.opacity = clamp((t - (TK.o.at || 0.2)) / 0.2);
    TK.w.style.transform = `translateY(${Math.sin(t * 2.1) * 4 - a * 6}px) rotate(${Math.sin(t * 1.3) * 1.2}deg) scale(${(0.5 + 0.5 * p) * (1 + 0.025 * a)})`;
  }

  // ---------- kumpulkan suara & ledakan efek ----------
  const MASUK_SFX = { jatuh: [[0.0, "whoosh", 0.22], [0.3, "thud", 0.5]], geser: [[0, "whoosh", 0.25]], geserkanan: [[0, "whoosh", 0.25]], naik: [[0, "swish", 0.14]], zoom: [[0.12, "pop", 0.45]], ketuk: [[0.18, "pop", 0.5]], muncul: [] };
  const SFX = [], LEDAK = [];
  function kumpul(n, off) {
    const base = off + n.at;
    if (n.s.bunyi !== false) (MASUK_SFX[n.masuk] || []).forEach(([t, j, v]) => SFX.push([base + t, j, v]));
    n.sfx.forEach(([t, j, v]) => SFX.push([base + t, j, v]));
    n.efek.forEach((e) => {
      if (e.jenis === "konfeti" || e.jenis === "kilau") { LEDAK.push({ t: base + (e.at || 0.3), node: n.el, jenis: e.jenis, ada: false, d: [] }); SFX.push([base + (e.at || 0.3), e.jenis === "konfeti" ? "konfeti" : "kilau", 0.55]); }
      if (e.jenis === "getar") SFX.push([base + (e.at || 0), "buzz", 0.4]);
    });
    n.kids.forEach((k) => kumpul(k, base));
  }
  const semua = isi.concat(bawah);
  itemsAtas.concat(semua).forEach((n) => kumpul(n, 0));
  ADG.forEach((A, i) => { if (i) SFX.push([A.at - 0.05, "whoosh", 0.3]); A.items.forEach((n) => kumpul(n, A.at)); });
  if (PETA) { SFX.push([PETA.at, "swish", 0.3]); PETA.aktif.forEach(([s]) => SFX.push([s, "pop", 0.45])); }
  (SPEC.efek_suara || []).forEach(([t, j, v]) => SFX.push([t, j, v == null ? 0.5 : v]));  // efek bebas: [[detik|"@kata", jenis, volume]]
  window.__sfx = SFX.sort((a, b) => a[0] - b[0]);

  window.__durasi = SPEC.durasi || Math.round((Math.max(0, ...semua.map((n) => n.at), ...ADG.map((A) => A.at + 1), ...SUB.map((f) => f.t1), ...SFX.map((x) => x[0])) + (SPEC.ekor || 3.2)) * 10) / 10;
  DUR = window.__durasi;

  // ledakan konfeti / kilau (partikel dihitung dari waktu, tanpa keadaan)
  const fx = document.getElementById("fx");
  function ledakan(L, t) {
    const d = t - L.t;
    if (d < 0 || d > 1.8) { L.d.forEach((x) => (x.style.opacity = 0)); return; }
    if (!L.ada) {
      L.ada = true;
      const r = el("div"), b = L.node.getBoundingClientRect(), rr = rng(Math.round(L.t * 100) + 7);
      L.cx = b.left + b.width / 2; L.cy = b.top + b.height / 2;
      const n = L.jenis === "konfeti" ? 34 : 16, warna = ["#ff7a2f", "#22c3e6", "#ffe27a", "#2ea36a", "#ff6b9a", "#ffffff"];
      for (let i = 0; i < n; i++) {
        const p = el("i"), s = L.jenis === "konfeti" ? 12 + rr() * 12 : 14 + rr() * 16;
        if (L.jenis === "konfeti") p.style.cssText = `width:${s}px;height:${s * 0.5}px;background:${warna[i % 6]};border-radius:2px`;
        else { p.textContent = "✦"; p.style.cssText = `font-size:${s * 1.6}px;color:${warna[(i % 3) + 1]};text-shadow:0 0 12px rgba(255,255,255,.8);line-height:1`; }
        const ang = (L.jenis === "konfeti" ? -Math.PI / 2 + (rr() - 0.5) * 2.6 : rr() * Math.PI * 2), v = 380 + rr() * 520;
        p._q = { vx: Math.cos(ang) * v, vy: Math.sin(ang) * v, rot: rr() * 360, vr: (rr() - 0.5) * 900, g: L.jenis === "konfeti" ? 1500 : 200 };
        fx.appendChild(p); L.d.push(p);
      }
    }
    L.d.forEach((p) => {
      const q = p._q, x = L.cx + q.vx * d, y = L.cy + q.vy * d + 0.5 * q.g * d * d;
      p.style.opacity = clamp(1 - (d - 0.9) / 0.9); p.style.transform = `translate(${x}px,${y}px) rotate(${q.rot + q.vr * d}deg) scale(${L.jenis === "kilau" ? 1 - d / 2 : 1})`;
    });
  }

  // watermark nama kreator (tetap sepanjang video): SPEC.watermark = "Alzazali" | {teks, opasitas, x, y, posisi} | [beberapa]
  (Array.isArray(SPEC.watermark) ? SPEC.watermark : SPEC.watermark ? [SPEC.watermark] : []).forEach((W0) => {
    const W = typeof W0 === "string" ? { teks: W0 } : W0;
    const w = el("div", null, esc(W.teks));
    if ((W.posisi || "tengah") === "tengah")  // besar di tengah layar, sangat tipis (anti-potong)
      w.style.cssText = `position:absolute;left:0;right:0;top:${W.y || 900}px;text-align:center;z-index:50;font:800 ${W.ukuran || 120}px "DejaVu Sans",Arial,sans-serif;color:#fff;opacity:${W.opasitas || 0.15};letter-spacing:.06em;pointer-events:none`;
    else
      w.style.cssText = `position:absolute;left:${W.x || 44}px;top:${W.y || 124}px;z-index:50;font:800 34px "DejaVu Sans",Arial,sans-serif;color:#fff;opacity:${W.opasitas || 0.55};letter-spacing:.04em;text-shadow:0 2px 6px rgba(0,0,0,.55);pointer-events:none`;
    document.body.appendChild(w);
  });
  window.setT = (t) => {
    T = t;
    itemsAtas.forEach((n) => perbarui(n, t)); semua.forEach((n) => perbarui(n, t));
    ADG.forEach((A) => perbaruiAdegan(A, t)); perbaruiPeta(t); perbaruiSub(t); perbaruiTokoh(t);
    // kamera: zoom pelan + melayang
    const u = clamp(t / DUR);
    document.getElementById("papan").style.transform = `translate(${Math.sin(t * 0.55) * 7}px,${Math.cos(t * 0.42) * 6 - u * 10}px) scale(${1 + 0.04 * u}) rotate(${Math.sin(t * 0.3) * 0.18}deg)`;
    dk.forEach((o) => { o.d.style.transform = `translate(${Math.sin(t * o.w + o.ph) * o.a}px,${Math.cos(t * o.w * 0.8 + o.ph) * o.a}px) rotate(${o.rot + Math.sin(t * 0.4 + o.ph) * 3}deg)`; });
    LEDAK.forEach((L) => ledakan(L, t));
    let kl = 0; LEDAK.forEach((L) => { if (L.jenis === "konfeti") kl = Math.max(kl, 0.28 * clamp(1 - (t - L.t) / 0.22) * (t >= L.t ? 1 : 0)); });
    document.getElementById("kilat").style.opacity = kl;
  };
  window.setT(0);
})();
