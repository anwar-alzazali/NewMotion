// Bot Telegram "Mesin KONTEN" (Cloudflare Worker `mesin-konten`).
// Asal: mesin-video/bot/worker.js (25 Okt - 31 Okt 2026). Dipindah ke repo ini 21 Nov 2026 (Tahap F1).
// Dibawa: webhook, chat pribadi, balas komentar, simpan ke repo. Baru: persetujuan video (Setujui/Tolak + alasan).
// TIDAK dibawa (keputusan pemilik): saldo/QRIS, proyek pengguna, rakit pengguna, Studio, naskah NGOPAI/iklan.
// Rahasia di Cloudflare (bukan di berkas): TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WEBHOOK_SECRET, GH_TOKEN,
// ANTHROPIC_API_KEY, GEMINI_API_KEY (opsional, dipakai dulu karena gratis), SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (riwayat chat & catatan biaya di schema `konten`).

export const ALASAN = {
  hook: "Hook lemah", visual: "Visual tidak sesuai", suara: "Suara/efek", dalil: "Dalil/isi",
  panjang: "Terlalu panjang", lain: "Lainnya",
};
const PENANDA_ALASAN = "📝 Alasan tolak";
const MODEL_CHAT = "claude-sonnet-4-5";
const KURS = (env) => Number(env.KURS || 16500);
const hargaModel = (m) => (/haiku/.test(m) ? [1, 5] : /opus/.test(m) ? [5, 25] : [3, 15]);

// ---------- fungsi murni (dites di bot/worker.test.mjs) ----------
export const idAman = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60);

/** callback_data -> {aksi, id, alasan}. Format: st:<id> | tl:<id> | al:<id>:<kode> | ub:<id> (ubah keputusan).
 *  Batas Telegram 64 byte. */
export function bacaTombol(data) {
  const [aksi, id, kode] = String(data || "").split(":");
  if (!["st", "tl", "al", "ub", "nl", "nr", "nb", "nu", "va", "vr", "fu"].includes(aksi) || !idAman(id) || idAman(id) !== id) return null;
  if (aksi === "al" && !ALASAN[kode]) return null;
  return { aksi, id, alasan: kode || null };
}

export const tombolPersetujuan = (id) => [[{ text: "✅ Setujui", callback_data: `st:${id}` }, { text: "❌ Tolak", callback_data: `tl:${id}` }]];
export const tombolAlasan = (id) => {
  const k = Object.keys(ALASAN).map((a) => ({ text: ALASAN[a], callback_data: `al:${id}:${a}` }));
  return [k.slice(0, 2), k.slice(2, 4), k.slice(4)];
};

export const tombolSesudah = (id, label) => [[{ text: label, callback_data: "x" }, { text: "↩️ Ubah", callback_data: `ub:${id}` }]];

/** Keputusan baru; keputusan sebelumnya (bila ada) disimpan di `riwayat` supaya perubahan pikiran ikut jadi data. */
export function catatanKeputusan(id, keputusan, alasan, catatan, waktu, lama = null) {
  const riwayat = lama ? [...(lama.riwayat || []), { keputusan: lama.keputusan, alasan: lama.alasan, catatan: lama.catatan, waktu: lama.waktu }] : [];
  return { video: id, keputusan, alasan: alasan ? ALASAN[alasan] || alasan : null, kode_alasan: alasan || null,
           catatan: catatan || null, waktu, ...(riwayat.length ? { riwayat } : {}) };
}

// ---------- antrean naskah (pekerjaan berat di workflow `naskah` -> newmotion/application/antrean_naskah.py) ----------
export const TAHAP = [["diterima", "Naskah diterima"], ["dalil", "Dalil diverifikasi"], ["tinjau", "Tinjauan naskah"],
  ["sutradara", "Pratinjau visual"], ["tinjau_visual", "Tinjauan visual"], ["narasi", "TTS/Narasi"], ["render", "Render final"], ["periksa", "Pemeriksaan"], ["kirim", "Dikirim untuk persetujuan"]];
const IKON = { selesai: "✅", jalan: "⏳", gagal: "❌", tunggu: "⏸", belum: "▫️" };
/** HARUS identik dengan newmotion/application/antrean_naskah.py kartu() (fixture tests/data/kartu_status.json). */
export function kartuStatus(st) {
  const b = [`🎬 ${st.judul || st.id}`];
  for (const [k, label] of TAHAP) {
    const ket = (st.ket || {})[k];
    b.push(`${IKON[st.tahap[k] || "belum"]} ${label}${ket ? " — " + ket : ""}`);
  }
  return b.join("\n");
}
export function tombolKartu(st) {
  const i = st.id;
  if (st.tahap.tinjau === "selesai" && st.tahap.sutradara === "gagal"
      && !["jalan", "selesai"].includes(st.tahap.tinjau_visual)) {
    return [[{ text: "🔁 Ulangi pratinjau visual", callback_data: `nu:${i}` }],
            [{ text: "🏠 Menu", callback_data: "menu" }]];
  }
  // Produksi final (narasi + render) gagal: boleh dicoba ulang; audio yang sudah dibuat dipakai ulang.
  if (st.tahap.tinjau_visual === "selesai" && [st.tahap.narasi, st.tahap.render].includes("gagal"))
    return [[{ text: "🔁 Ulangi produksi final", callback_data: `fu:${i}` }],
            [{ text: "🏠 Menu", callback_data: "menu" }]];
  if (["belum", "jalan"].includes(st.tahap.tinjau) && st.tahap.dalil === "selesai")
    return [[{ text: "✅ Lanjut", callback_data: `nl:${i}` }, { text: "✏️ Revisi", callback_data: `nr:${i}` }],
            [{ text: "❌ Batal", callback_data: `nb:${i}` }, { text: "🏠 Menu", callback_data: "menu" }]];
  // Naskah gagal tersusun/divalidasi: jangan buntu, beri jalan revisi.
  if (st.tahap.diterima === "gagal")
    return [[{ text: "✏️ Revisi", callback_data: `nr:${i}` }, { text: "❌ Batal", callback_data: `nb:${i}` }],
            [{ text: "🏠 Menu", callback_data: "menu" }]];
  // Dalil gagal: naskah tidak boleh lanjut ke visual. Pilihan hanya revisi atau batal.
  if (["belum", "jalan"].includes(st.tahap.tinjau) && st.tahap.dalil === "gagal")
    return [[{ text: "✏️ Revisi dalil", callback_data: `nr:${i}` }, { text: "❌ Batal", callback_data: `nb:${i}` }],
            [{ text: "🏠 Menu", callback_data: "menu" }]];
  return [[{ text: "🏠 Menu", callback_data: "menu" }]];
}
export function statusBaru(id, judul, sumber, chat) {
  const tahap = Object.fromEntries(TAHAP.map(([k]) => [k, "belum"]));
  tahap.diterima = "jalan";
  // Antrean lama tetap eksplisit memakai Kisah Islami sampai genre lain siap.
  return { id, judul, sumber, chat, genre: "kisah_islami", konteks_konten: "islami", tahap, ket: { diterima: "mengantre di GitHub Actions…" }, dibuat: new Date().toISOString() };
}
export function idAntrean(teks, waktu = new Date()) {
  const w = new Date(waktu.getTime() + 7 * 3600e3).toISOString();  // WIB
  const tgl = w.slice(2, 10).replace(/-/g, "") + "-" + w.slice(11, 16).replace(":", "");
  const kata = idAman(String(teks).split(/\s+/).slice(0, 4).join(" ")).slice(0, 28).replace(/-+$/, "");
  return `${tgl}${kata ? "-" + kata : ""}`;
}

export const bolehAkses = (env, dariId) => String(dariId) === String(env.TELEGRAM_CHAT_ID).trim();

// ---------- Telegram & GitHub ----------
const TG = (env, metode, body) =>
  fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${metode}`, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
  }).then((r) => r.json());

const kirim = (env, teks, tombol) =>
  TG(env, "sendMessage", { chat_id: env.CHAT || env.TELEGRAM_CHAT_ID, text: teks, ...(tombol ? { reply_markup: { inline_keyboard: tombol } } : {}) });

const GH = (env, path, opsi = {}) =>
  fetch(`https://api.github.com/repos/${env.GH_REPO}${path}`, {
    ...opsi,
    headers: { authorization: `Bearer ${env.GH_TOKEN}`, accept: "application/vnd.github+json", "user-agent": "mesin-konten", ...(opsi.headers || {}) },
  });

function keBase64(buf) {
  let s = ""; const b = new Uint8Array(buf);
  for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode(...b.subarray(i, i + 0x8000));
  return btoa(s);
}

async function simpanTeks(env, path, isi, pesan) {
  const lama = await GH(env, `/contents/${path}?ref=${env.GH_BRANCH}`);
  const sha = lama.ok ? (await lama.json()).sha : undefined;
  const r = await GH(env, `/contents/${path}`, { method: "PUT", body: JSON.stringify({ message: pesan, content: keBase64(new TextEncoder().encode(isi)), branch: env.GH_BRANCH, ...(sha ? { sha } : {}) }) });
  if (!r.ok) throw new Error("GitHub simpan " + r.status);
}

// ---------- Supabase (riwayat chat & catatan biaya; schema konten yang sudah ada) ----------
const alamatDB = (env) => String(env.SUPABASE_URL || "").trim().replace(/\/+$/, "").replace(/\/rest\/v1$/, "");
const DB = (env, path, opsi = {}) =>
  fetch(`${alamatDB(env)}/rest/v1/${path}`, { ...opsi, headers: { apikey: env.SUPABASE_SERVICE_ROLE_KEY, authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`, "accept-profile": "konten", "content-profile": "konten", "content-type": "application/json", prefer: "return=representation", ...(opsi.headers || {}) } });
async function ambilPengaturan(env, kunci) {
  if (!env.SUPABASE_URL) return null;
  const r = await DB(env, `pengaturan?kunci=eq.${kunci}&select=nilai`);
  return r.ok ? ((await r.json())[0] || {}).nilai || null : null;
}
async function simpanPengaturan(env, kunci, nilai) {
  if (!env.SUPABASE_URL) return;
  const r = await DB(env, "pengaturan", { method: "POST", headers: { prefer: "resolution=merge-duplicates,return=representation" }, body: JSON.stringify({ kunci, nilai }) });
  if (!r.ok) throw new Error("DB pengaturan " + r.status);
}
const catatBiaya = (env, layanan, token, idr) => env.SUPABASE_URL
  ? DB(env, "biaya_log", { method: "POST", body: JSON.stringify({ pengguna_id: env.DARI, layanan, penyedia: "claude", satuan: "token", jumlah: token, biaya_idr: idr }) }).catch(() => {})
  : Promise.resolve();

async function claude(env, body) {
  if (!env.ANTHROPIC_API_KEY) throw new Error("Kunci Claude belum dipasang di Worker.");
  const r = await fetch("https://api.anthropic.com/v1/messages", { method: "POST", headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error("Claude " + r.status);
  const j = await r.json();
  const masuk = (j.usage || {}).input_tokens || 0, keluar = (j.usage || {}).output_tokens || 0;
  const [hm, hk] = hargaModel(body.model);
  return { jawab: (j.content || []).map((c) => c.text || "").join("").trim() || "(kosong)", token: masuk + keluar,
           idr: Math.round(((masuk * hm + keluar * hk) / 1e6) * KURS(env)) };
}

// ---------- Gemini gratis dulu, Claude cadangan (pola sama dengan antrean naskah) ----------
// Pesan memakai format Claude ({role, content: string | [{type:"text"|"image"}]}); diubah ke format Gemini.
export const keGemini = (system, messages) => ({
  ...(system ? { systemInstruction: { parts: [{ text: system }] } } : {}),
  contents: messages.map((m) => ({
    role: m.role === "assistant" ? "model" : "user",
    parts: (typeof m.content === "string" ? [{ type: "text", text: m.content }] : m.content).map((c) =>
      c.type === "image" ? { inline_data: { mime_type: c.source.media_type, data: c.source.data } } : { text: c.text || "" }),
  })),
});
export const pilihModelGemini = (nama) => {
  const flash = [], lite = [];
  for (const n of nama) {
    const m = /^gemini-(\d+(?:\.\d+)?)-flash(-lite)?$/.exec(n);
    if (m) (m[2] ? lite : flash).push([parseFloat(m[1]), n]);
  }
  const urut = (a) => a.sort((x, y) => y[0] - x[0]).map((x) => x[1]);
  return [...urut(flash).slice(0, 2), ...urut(lite).slice(0, 1)];
};
let modelGemini = null;  // disimpan selama isolate hidup
async function daftarModelGemini(env) {
  if (env.GEMINI_MODEL) return [env.GEMINI_MODEL];
  if (modelGemini) return modelGemini;
  // Isolate baru sering muncul: simpan daftar model sehari di Supabase supaya tidak bertanya ke Google tiap pesan.
  try {
    const s = JSON.parse((await ambilPengaturan(env, "gemini_model")) || "null");
    if (s && Date.now() - s.waktu < 864e5 && s.daftar?.length) return (modelGemini = s.daftar);
  } catch { /* abaikan, ambil ulang */ }
  const r = await fetch("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200", { headers: { "x-goog-api-key": env.GEMINI_API_KEY } });
  if (!r.ok) throw new Error("Gemini models " + r.status);
  const j = await r.json();
  const nama = (j.models || []).filter((m) => (m.supportedGenerationMethods || []).includes("generateContent")).map((m) => String(m.name).replace(/^models\//, ""));
  modelGemini = pilihModelGemini(nama);
  if (!modelGemini.length) throw new Error("Tidak ada model Gemini flash");
  await simpanPengaturan(env, "gemini_model", JSON.stringify({ waktu: Date.now(), daftar: modelGemini })).catch(() => {});
  return modelGemini;
}
async function gemini(env, body) {
  let galat = null;
  for (const model of await daftarModelGemini(env)) {
    // Worker hanya punya ~30 dtk sesudah membalas webhook: pikir dibuat ringan dan tiap panggilan dibatasi waktunya.
    const pikir = /^gemini-2\./.test(model) ? { thinkingBudget: 0 } : { thinkingLevel: "low" };
    const badan = JSON.stringify({ ...keGemini(body.system, body.messages),
      generationConfig: { maxOutputTokens: Math.max(4096, body.max_tokens || 0), thinkingConfig: pikir } });
    let r;
    try {
      r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
        method: "POST", headers: { "x-goog-api-key": env.GEMINI_API_KEY, "content-type": "application/json" }, body: badan,
        signal: AbortSignal.timeout(12000) });
    } catch (e) { galat = new Error(`Gemini ${model} ${e.name === "TimeoutError" ? "lewat 12 dtk" : e.message}`); continue; }
    if (!r.ok) { galat = new Error(`Gemini ${model} ${r.status} ${(await r.text()).slice(0, 120)}`); continue; }  // 429/5xx -> model berikutnya
    const j = await r.json();
    const jawab = (((j.candidates || [])[0] || {}).content || {}).parts?.map((x) => x.text || "").join("").trim();
    if (!jawab) { galat = new Error(`Gemini ${model} kosong`); continue; }
    const u = j.usageMetadata || {};
    return { jawab, token: (u.promptTokenCount || 0) + (u.candidatesTokenCount || 0), idr: 0, model };
  }
  throw galat || new Error("Gemini gagal");
}
// Coba Gemini (gratis); bila tak ada kunci atau gagal, pakai Claude.
async function tanyaAI(env, body) {
  TG(env, "sendChatAction", { chat_id: env.CHAT || env.TELEGRAM_CHAT_ID, action: "typing" }).catch(() => {});  // tanda "sedang mengetik"
  if (env.GEMINI_API_KEY && env.AI_UTAMA !== "claude") {
    try { return await gemini(env, body); } catch (e) { console.log("gemini gagal, pakai Claude:", e.message); }
  }
  return { ...(await claude(env, body)), model: body.model };
}
export const labelBiaya = (h) => (h.idr ? `≈Rp${h.idr}` : "Rp0") + ` · ${/gemini/.test(h.model || "") ? "Gemini" : "Claude"}`;

// ---------- chat pribadi ----------
const SISTEM_CHAT = (tgl) => `Kamu asisten pribadi Anwar Alzazali (Indonesia, zona Asia/Jakarta). Hari ini ${tgl}. Jawab santai, singkat, langsung inti; beri langkah konkret. Jujur: bila tidak yakin atau butuh data terbaru, katakan, jangan ngarang. Anggaran rendah, utamakan gratis/murah. Jangan minta kunci/token.`;

async function chatPribadi(env, teks) {
  const model = env.MODEL_CHAT || MODEL_CHAT, kunci = "chat_" + env.DARI;
  let riwayat = []; try { riwayat = JSON.parse((await ambilPengaturan(env, kunci)) || "[]"); } catch { riwayat = []; }
  riwayat.push({ role: "user", content: teks.slice(0, 4000) }); riwayat = riwayat.slice(-12);
  while (riwayat.length && riwayat[0].role !== "user") riwayat.shift();
  const tgl = new Date().toLocaleDateString("id-ID", { timeZone: "Asia/Jakarta", dateStyle: "full" });
  const h = await tanyaAI(env, { model, max_tokens: 1500, system: SISTEM_CHAT(tgl), messages: riwayat });
  riwayat.push({ role: "assistant", content: h.jawab });
  await simpanPengaturan(env, kunci, JSON.stringify(riwayat.slice(-12))).catch(() => {});
  if (h.idr) await catatBiaya(env, "chat", h.token, h.idr);
  const ekor = `\n\n${labelBiaya(h)} · ${h.token} token`;
  for (let i = 0; i < h.jawab.length; i += 3800) await kirim(env, h.jawab.slice(i, i + 3800) + (i + 3800 >= h.jawab.length ? ekor : ""));
}

// ---------- balas komentar ----------
const SISTEM_KOMENTAR = `Kamu membantu Anwar Alzazali membalas komentar di akun TikTok/FB "Alzazali | Kisah Islami" (kisah Islami dalam animasi, setiap kisah dengan sumber Al-Qur'an dan hadits; seri Padang Mahsyar 1-6, dll). Gambar = tangkapan layar komentar.
Balas HANYA dengan JSON (tanpa teks lain): [{"nama":"...","komentar":"ringkas, maks 80 huruf","balasan":["...","..."],"catatan":"opsional, sangat singkat"}]
Aturan balasan: bahasa Indonesia santai-sopan, maksimal 2 kalimat (maks 220 huruf), boleh 1 emoji 🤍; 2 pilihan untuk pertanyaan/komentar panjang, 1 pilihan untuk komentar pendek. Komentar "aamiin"/stiker/"pertama"/emoji saja: balasan [] dan catatan "cukup like". Dalil HANYA yang kamu yakin benar (QS surah:ayat atau HR perawi + nomor); ragu = tanpa nomor + "wallahu a'lam". Hukum/fatwa/masalah pribadi: jawab sebatas kisah + sumber, sarankan tanya ustaz. SARA/antaragama: singkat sesuai dalil, tanpa menilai agama lain. Provokasi/hinaan: balasan [] dan catatan "abaikan/hapus". Pertanyaan bagus untuk video balasan: catatan "💡 cocok video balasan". Jangan mengarang isi video.
Bila ditanya kenapa tokoh digambar begitu: ini ADAB saluran (pilihan penghormatan, bukan klaim hukum): Allah tidak digambarkan; nabi hanya pilar cahaya (khusus nabi, agar kedudukan nabi tidak disamakan dengan siapa pun); malaikat cahaya bentuk lain; sahabat bertubuh manusia dengan wajah cahaya (wajah tidak digambar sebagai penghormatan); orang saleh lain digambar sebagai manusia biasa. Jelaskan santun, tidak menyalahkan pendapat lain.`;

async function balasKomentar(env, fileId, catatan) {
  const info = await TG(env, "getFile", { file_id: fileId });
  if (!info.ok) return kirim(env, "Gagal mengambil gambar dari Telegram.");
  const unduhan = await fetch(`https://api.telegram.org/file/bot${env.TELEGRAM_BOT_TOKEN}/${info.result.file_path}`);
  if (!unduhan.ok) throw new Error("Unduhan Telegram gagal: " + unduhan.status);
  const buf = await unduhan.arrayBuffer();
  if (buf.byteLength > 20 * 1024 * 1024) throw new Error("Berkas melebihi batas 20 MB.");
  const isi = [{ type: "image", source: { type: "base64", media_type: "image/jpeg", data: keBase64(buf) } },
               { type: "text", text: catatan ? "Catatan dari Anwar: " + catatan : "Buatkan draf balasan." }];
  const h = await tanyaAI(env, { model: env.MODEL_CHAT || MODEL_CHAT, max_tokens: 1200, system: SISTEM_KOMENTAR, messages: [{ role: "user", content: isi }] });
  if (h.idr) await catatBiaya(env, "komentar", h.token, h.idr);
  let daftar = null; try { const m = h.jawab.match(/\[[\s\S]*\]/); daftar = JSON.parse(m ? m[0] : h.jawab); } catch { daftar = null; }
  if (!Array.isArray(daftar)) { for (let i = 0; i < h.jawab.length; i += 3800) await kirim(env, h.jawab.slice(i, i + 3800)); return kirim(env, labelBiaya(h)); }
  for (const k of daftar) {  // satu pesan per komentar; tombol Salin sekali ketuk
    const bl = (k.balasan || []).filter(Boolean).map((x) => String(x).slice(0, 256));
    let teks = `💬 ${k.nama || "?"}: ${k.komentar || ""}`;
    bl.forEach((x, i) => { teks += `\n\n${i + 1}. ${x}`; });
    if (k.catatan) teks += `\n\n📝 ${k.catatan}`;
    await kirim(env, teks, bl.length ? [bl.map((x, i) => ({ text: `📋 Salin ${i + 1}`, copy_text: { text: x } }))] : undefined);
  }
  await kirim(env, `✅ ${daftar.length} komentar · ${labelBiaya(h)}`);
}

async function dispatch(env, workflow, inputs) {
  const r = await GH(env, `/actions/workflows/${workflow}/dispatches`, { method: "POST", body: JSON.stringify({ ref: env.GH_BRANCH, inputs }) });
  if (!r.ok) throw new Error(`GitHub Actions ${r.status} (token perlu izin Actions: Read and write)`);
}
const PENANDA_NASKAH = "📝 Tempel naskah", PENANDA_IDE = "💡 Ide naskah", PENANDA_REVISI = "✏️ Catatan revisi";

async function kirimKartu(env, st) {
  const body = { chat_id: env.CHAT, text: kartuStatus(st), reply_markup: { inline_keyboard: tombolKartu(st) } };
  if (st.pesan_kartu) { const r = await TG(env, "editMessageText", { ...body, message_id: st.pesan_kartu }); if (r.ok || /not modified/.test(r.description || "")) return st; }
  const r = await TG(env, "sendMessage", body);
  if (r.ok) st.pesan_kartu = r.result.message_id;
  return st;
}
const simpanStatus = (env, st) => simpanTeks(env, `antrean/${st.id}/status.json`, JSON.stringify(st, null, 1) + "\n", `Antrean ${st.id}: status`);

async function antreanBaru(env, mode, teks) {
  teks = String(teks || "").trim();
  if (teks.length < (mode === "ide" ? 3 : 40)) return kirim(env, mode === "ide" ? "Idenya terlalu pendek." : "Naskahnya terlalu pendek. Tempel naskah lengkapnya.");
  const id = idAntrean(mode === "ide" ? teks : teks.replace(/^judul\s*:\s*/i, ""));
  const st = await kirimKartu(env, statusBaru(id, mode === "ide" ? teks.slice(0, 60) : "", mode, env.CHAT));
  await simpanTeks(env, `antrean/${id}/masukan.txt`, teks + "\n", `Antrean ${id}: masukan (${mode})`);
  await simpanStatus(env, st);
  await dispatch(env, "naskah.yml", { id, mode });
}

export function cekPapan(isi) {
  let spek;
  try { spek = JSON.parse(isi); } catch (e) { return "JSON tidak terbaca: " + String(e.message || e).slice(0, 150); }
  if (!spek || typeof spek !== "object" || Array.isArray(spek)) return "Papan harus berupa objek JSON.";
  if (!(spek.cerita && Array.isArray(spek.cerita.shot) && spek.cerita.shot.length) && !spek.kartu && !spek.adegan)
    return "Papan kosong: tidak ada cerita.shot, kartu, atau adegan.";
  return null;
}

async function papanManual(env, nama, isi) {
  if (isi.length > 900000) return kirim(env, "Berkas JSON terlalu besar (maks ±900 KB).");
  const salah = cekPapan(isi);
  if (salah) return kirim(env, "❌ " + salah);
  const id = idAntrean("manual " + nama);
  const spek = `antrean/${id}/papan_manual.json`;
  await simpanTeks(env, spek, isi, `Antrean ${id}: papan manual`);
  await dispatch(env, "manual.yml", { spek, kirim: "true" });
  return kirim(env, `🧾 Papan manual diterima (${id}). Dirender tanpa LLM: render → periksa → video dikirim ke sini (±5–10 menit).\nRujukan relatif di JSON dibaca dari mesin-video/papan/kisah/, sama seperti mahsyar1.json.`);
}

async function renderPapanRepo(env, nama) {
  const n = String(nama || "").trim().replace(/\.json$/i, "");
  if (!/^[A-Za-z0-9_-]{1,60}$/.test(n)) return kirim(env, "Pakai: /papan <nama> — mis. /papan mahsyar1 (berkas di mesin-video/papan/kisah/). Atau kirim berkas .json langsung.");
  await dispatch(env, "manual.yml", { spek: `mesin-video/papan/kisah/${n}.json`, kirim: "true" });
  return kirim(env, `🧾 Render papan ${n}.json dimulai tanpa LLM. Video dan hasil periksa dikirim ke sini (±5–10 menit).`);
}

async function ubahAntrean(env, q, t) {
  const st = await bacaJsonRepo(env, `antrean/${t.id}/status.json`);
  if (!st) return TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: "Antrean tidak ditemukan" });
  st.pesan_kartu = q.message ? q.message.message_id : st.pesan_kartu;
  if (t.aksi === "nu" && !(st.tahap.tinjau === "selesai" && st.tahap.sutradara === "gagal"
      && !["jalan", "selesai"].includes(st.tahap.tinjau_visual))) {
    return TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: "Pratinjau belum berstatus gagal atau sudah selesai; tidak diulang." });
  }
  if (t.aksi === "nl" && st.tahap.tinjau !== "jalan") {
    return TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: "Naskah ini sudah diproses; pratinjau tidak dibuat ulang." });
  }
  // Pengaman sisi server: tombol Lanjut lama (sebelum perbaikan) tetap tidak boleh meloloskan dalil gagal.
  if (t.aksi === "nl" && st.tahap.dalil !== "selesai") {
    return TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: "Dalil belum lolos semua. Revisi naskahnya dulu.", show_alert: true });
  }
  if (t.aksi === "nr") {
    await TG(env, "answerCallbackQuery", { callback_query_id: q.id });
    return tanya(env, { chat_id: env.CHAT, text: `${PENANDA_REVISI} [${t.id}]\nBalas pesan ini dengan catatan perbaikannya (mis. "hook kurang kuat, mulai dari azabnya").`, reply_markup: { force_reply: true, input_field_placeholder: "catatan revisi" } });
  }
  if (t.aksi !== "nu") {
    st.tahap.tinjau = t.aksi === "nl" ? "selesai" : "gagal";
    st.ket = { ...(st.ket || {}), tinjau: t.aksi === "nl" ? "disetujui" : "dibatalkan" };
  }
  if (t.aksi === "nl" || t.aksi === "nu") {
    st.tahap.sutradara = "jalan";
    st.tahap.tinjau_visual = "belum";
    st.ket.sutradara = t.aksi === "nu" ? "mengulangi pratinjau setelah kegagalan sebelumnya" : "menyusun pratinjau visual tanpa TTS";
  }
  st.diperbarui = new Date().toISOString();
  await simpanStatus(env, st);
  await TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: t.aksi === "nl" ? "Naskah disetujui; pratinjau visual dimulai" : t.aksi === "nu" ? "Pratinjau visual dicoba ulang" : "Dibatalkan" });
  if (t.aksi === "nl" || t.aksi === "nu") {
    try { await dispatch(env, "visual.yml", { id: t.id }); }
    catch (e) { st.tahap.sutradara = "gagal"; st.ket.sutradara = "gagal memulai pratinjau: " + String(e.message || e).slice(0, 120); await simpanStatus(env, st); }
  }
  return kirimKartu(env, st);
}

async function putuskanVisual(env, q, t) {
  const st = await bacaJsonRepo(env, `antrean/${t.id}/status.json`);
  if (!st || st.tahap?.tinjau_visual !== "jalan") {
    return TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: "Pratinjau visual tidak ditemukan atau sudah diputuskan." });
  }
  const setuju = t.aksi === "va";
  st.tahap.tinjau_visual = setuju ? "selesai" : "gagal";
  st.ket = { ...(st.ket || {}), tinjau_visual: setuju
    ? "disetujui pemilik; TTS boleh dilanjutkan"
    : "ditolak pemilik; TTS diblokir sampai visual direvisi" };
  if (setuju) {
    st.tahap.narasi = "jalan";
    st.ket.narasi = "narasi ElevenLabs dan render final berjalan di GitHub Actions…";
  }
  st.diperbarui = new Date().toISOString();
  await simpanStatus(env, st);
  if (setuju) {
    try { await dispatch(env, "final.yml", { id: t.id }); }
    catch (e) {
      st.tahap.narasi = "gagal"; st.ket.narasi = `gagal memulai produksi final: ${String(e.message || e).slice(0, 120)}`;
      await simpanStatus(env, st);
    }
  }
  await TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: setuju ? "Visual disetujui" : "Visual ditolak; TTS tetap diblokir" });
  await kirimKartu(env, st);
  if (!setuju) return kirim(env, `Visual ${t.id} ditolak. TTS dan render final diblokir. Perbaiki naskah atau adegan dalam antrean baru; regenerasi visual otomatis dari catatan penolakan belum tersedia.`);
  return kirim(env, st.tahap.narasi === "gagal"
    ? `Visual ${t.id} disetujui, tetapi produksi final gagal dimulai. Tekan "Ulangi produksi final" di kartu.`
    : `Visual ${t.id} disetujui. Narasi dan render final sedang dibuat; video bersuara dikirim ke sini bila selesai.`);
}

async function ulangiFinal(env, q, t) {
  const st = await bacaJsonRepo(env, `antrean/${t.id}/status.json`);
  if (!st || st.tahap?.tinjau_visual !== "selesai" || ![st.tahap.narasi, st.tahap.render].includes("gagal")) {
    return TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: "Tidak ada produksi final gagal untuk antrean ini." });
  }
  st.tahap.narasi = st.tahap.narasi === "selesai" ? "selesai" : "jalan";
  if (st.tahap.render === "gagal") st.tahap.render = "belum";
  st.ket = { ...(st.ket || {}), render: "produksi final diulang…" };
  st.diperbarui = new Date().toISOString();
  await simpanStatus(env, st);
  await dispatch(env, "final.yml", { id: t.id });
  await TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: "Produksi final diulang" });
  return kirimKartu(env, st);
}

async function revisiAntrean(env, id, catatan) {
  const st = await bacaJsonRepo(env, `antrean/${id}/status.json`);
  if (!st) return kirim(env, "Antrean tidak ditemukan.");
  await simpanTeks(env, `antrean/${id}/catatan.txt`, catatan + "\n", `Antrean ${id}: catatan revisi`);
  st.tahap.diterima = "jalan"; st.ket = { ...(st.ket || {}), diterima: "revisi mengantre…" };
  await kirimKartu(env, st); await simpanStatus(env, st);
  await dispatch(env, "naskah.yml", { id, mode: "revisi" });
}

async function daftarStatus(env) {
  const r = await GH(env, `/contents/antrean?ref=${env.GH_BRANCH}`);
  if (!r.ok) return kirim(env, "Belum ada naskah di antrean.", MENU);
  const dirs = (await r.json()).filter((x) => x.type === "dir").map((x) => x.name).sort().reverse().slice(0, 8);
  const baris = [];
  for (const d of dirs) {
    const st = await bacaJsonRepo(env, `antrean/${d}/status.json`);
    if (!st) continue;
    const aktif = TAHAP.find(([k]) => ["jalan", "gagal", "tunggu"].includes(st.tahap[k])) || TAHAP.findLast(([k]) => st.tahap[k] === "selesai");
    const [k, label] = aktif || TAHAP[0];
    baris.push(`${IKON[st.tahap[k]]} ${st.judul || st.id}\n    ${label}${(st.ket || {})[k] ? " — " + st.ket[k] : ""}`);
  }
  return kirim(env, baris.length ? "📊 Antrean terbaru\n\n" + baris.join("\n\n") : "Belum ada naskah di antrean.", MENU);
}

const MENU = [[{ text: "📝 Naskah", callback_data: "mn" }, { text: "💡 Ide", callback_data: "mi" }],
              [{ text: "📊 Status", callback_data: "ms" }, { text: "❓ Bantuan", callback_data: "mb" }]];
// Pesan "balas paksa" (force_reply) yang tidak dijawab membuat bar "Membalas Mesin KONTEN" muncul terus.
// Karena itu id pesan tanya disimpan, dan dihapus begitu pemilik melakukan hal lain.
async function tanya(env, body) {
  const r = await TG(env, "sendMessage", body);
  if (r.ok) await simpanPengaturan(env, "tanya_" + env.DARI, String(r.result.message_id)).catch(() => {});
  return r;
}
async function bersihkanTanya(env, kecuali) {
  const id = await ambilPengaturan(env, "tanya_" + env.DARI).catch(() => null);
  if (!id || String(id) === String(kecuali || "")) return;
  await TG(env, "deleteMessage", { chat_id: env.CHAT, message_id: Number(id) });
  await simpanPengaturan(env, "tanya_" + env.DARI, "").catch(() => {});
}
const tanyaNaskah = (env) => tanya(env, { chat_id: env.CHAT, text: `${PENANDA_NASKAH}\nBalas pesan ini dengan naskah lengkapnya (atau kirim berkas .txt/.md dengan keterangan "naskah"). Narasi Anda tidak akan diubah; dalil yang disebut akan diverifikasi.`, reply_markup: { force_reply: true, input_field_placeholder: "tempel naskah" } });
const tanyaIde = (env) => tanya(env, { chat_id: env.CHAT, text: `${PENANDA_IDE}\nBalas pesan ini dengan topik/idenya (mis. "Nabi Hud dan kaum 'Ad"). AI menulis naskah (Gemini gratis; cadangan Claude ±Rp500), lalu dalilnya diverifikasi.`, reply_markup: { force_reply: true, input_field_placeholder: "topik" } });

// ---------- persetujuan video ----------
async function bacaJsonRepo(env, path) {
  const r = await GH(env, `/contents/${path}?ref=${env.GH_BRANCH}`);
  if (!r.ok) return null;
  try { const j = await r.json(); return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(j.content.replace(/\n/g, "")), (c) => c.charCodeAt(0)))); }
  catch { return null; }
}

async function catatPersetujuan(env, id, keputusan, alasan, catatan) {
  const lama = await bacaJsonRepo(env, `data/persetujuan/${id}.json`);
  const isi = catatanKeputusan(id, keputusan, alasan, catatan, new Date().toISOString(), lama);
  await simpanTeks(env, `data/persetujuan/${id}.json`, JSON.stringify(isi, null, 1) + "\n",
                   `Persetujuan ${id}: ${keputusan}${isi.alasan ? " (" + isi.alasan + ")" : ""}`);
  return isi;
}

async function tandaiPesan(env, q, teks, id) {  // tombol diganti hasil keputusan + tombol Ubah
  const m = q.message; if (!m) return;
  await TG(env, "editMessageReplyMarkup", { chat_id: m.chat.id, message_id: m.message_id, reply_markup: { inline_keyboard: tombolSesudah(id, teks) } });
}

async function tanganiTombol(env, q) {
  const sederhana = { menu: () => kirim(env, "🏠 Menu utama", MENU), mn: () => tanyaNaskah(env), mi: () => tanyaIde(env),
                      ms: () => daftarStatus(env), mb: () => kirim(env, BANTUAN, MENU) };
  if (sederhana[q.data]) { await TG(env, "answerCallbackQuery", { callback_query_id: q.id }); return sederhana[q.data](); }
  const t = bacaTombol(q.data);
  if (t && ["nl", "nr", "nb", "nu"].includes(t.aksi)) return ubahAntrean(env, q, t);
  if (t && ["va", "vr"].includes(t.aksi)) return putuskanVisual(env, q, t);
  if (t && t.aksi === "fu") return ulangiFinal(env, q, t);
  if (!t) return TG(env, "answerCallbackQuery", { callback_query_id: q.id });
  if (t.aksi === "st") {
    await catatPersetujuan(env, t.id, "disetujui");
    await TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: "Tercatat: disetujui" });
    return tandaiPesan(env, q, "✅ Disetujui", t.id);
  }
  if (t.aksi === "ub") {  // kembalikan pilihan; keputusan lama tetap tersimpan sampai diganti
    await TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: "Pilih keputusan baru" });
    return TG(env, "editMessageReplyMarkup", { chat_id: q.message.chat.id, message_id: q.message.message_id, reply_markup: { inline_keyboard: tombolPersetujuan(t.id) } });
  }
  if (t.aksi === "tl") {
    await TG(env, "answerCallbackQuery", { callback_query_id: q.id });
    return TG(env, "editMessageReplyMarkup", { chat_id: q.message.chat.id, message_id: q.message.message_id, reply_markup: { inline_keyboard: tombolAlasan(t.id) } });
  }
  // al: alasan dipilih
  if (t.alasan === "lain") {
    await TG(env, "answerCallbackQuery", { callback_query_id: q.id });
    await tandaiPesan(env, q, "❌ Ditolak: menunggu alasan", t.id);
    return tanya(env, { chat_id: env.CHAT, text: `${PENANDA_ALASAN} [${t.id}]\nBalas pesan ini dengan alasannya.`, reply_markup: { force_reply: true, input_field_placeholder: "alasan penolakan" } });
  }
  await catatPersetujuan(env, t.id, "ditolak", t.alasan);
  await TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: "Tercatat: ditolak" });
  return tandaiPesan(env, q, `❌ Ditolak: ${ALASAN[t.alasan]}`, t.id);
}

const BANTUAN = `Mesin KONTEN (pribadi)
• 📝 Naskah: tempel naskah jadi (atau kirim berkas .txt/.md berketerangan "naskah"). Dirapikan ke format mesin tanpa mengubah narasi, dalilnya diverifikasi, lalu dikirim balik untuk Anda cek.
• 💡 Ide: tulis topik, AI menyusun naskah (Gemini gratis; bila gagal, Claude ±Rp500), dalil diverifikasi, Anda cek.
• Setelah naskah disetujui, bot membuat pratinjau visual MP4 tanpa TTS. Tinjau blocking, aksi, tokoh, latar, dan kamera; pilih Setujui visual atau Revisi visual. TTS belum dimulai sebelum visual disetujui.
• Video baru datang dengan tombol ✅ Setujui / ❌ Tolak. Tolak → pilih alasan (atau "Lainnya" lalu ketik). Berubah pikiran? Ketuk ↩️ Ubah. Keputusan tersimpan di repo (keputusan lama ikut tercatat) dan jadi bahan belajar mesin.
• 🧾 Jalur manual (tanpa LLM): kirim berkas .json papan tulisan tangan (format seperti mahsyar1.json), atau /papan <nama> untuk papan yang sudah ada di repo. Langsung render → periksa → video dikirim. Narasi dipakai bila JSON merujuk berkas suaranya.
• Balas komentar: kirim tangkapan layar komentar (tanpa keterangan, atau keterangan "k" + catatan, mis. "k jawab singkat").
• Tanya apa saja: ketik pesan biasa. /reset = hapus riwayat obrolan.`;

const PERINTAH = [{ command: "menu", description: "Menu utama" }, { command: "naskah", description: "Kirim naskah jadi" },
  { command: "ide", description: "Ide jadi naskah" }, { command: "status", description: "Lihat proses antrean" },
  { command: "papan", description: "Render papan JSON di repo tanpa LLM" },
  { command: "bantuan", description: "Cara pakai" }, { command: "reset", description: "Hapus riwayat obrolan" }];

async function tangani(env0, u) {
  const q = u.callback_query, msg = u.message;
  const dari = q ? q.from : msg && msg.from;
  if (!dari || (msg && msg.chat.type !== "private")) return;
  const env = { ...env0, CHAT: q ? (q.message && q.message.chat.id) || dari.id : msg.chat.id, DARI: dari.id };
  if (!bolehAkses(env, dari.id)) {
    if (q) return TG(env, "answerCallbackQuery", { callback_query_id: q.id, text: "Bot pribadi." });
    return kirim(env, "Maaf, ini bot pribadi.");
  }
  await bersihkanTanya(env, msg && msg.reply_to_message ? msg.reply_to_message.message_id : null);
  if (q) return tanganiTombol(env, q);
  const balasKe = msg.reply_to_message && (msg.reply_to_message.text || "");
  if (balasKe && msg.text && balasKe.startsWith(PENANDA_NASKAH)) return antreanBaru(env, "tempel", msg.text);
  if (balasKe && msg.text && balasKe.startsWith(PENANDA_IDE)) return antreanBaru(env, "ide", msg.text);
  if (balasKe && msg.text && balasKe.startsWith(PENANDA_REVISI)) {
    const id = idAman((/\[([^\]]+)\]/.exec(balasKe) || [])[1]);
    if (id) return revisiAntrean(env, id, msg.text.trim().slice(0, 2000));
  }
  const dok = msg.document;
  // Jalur manual: papan JSON tulisan tangan langsung dirender, tanpa LLM.
  if (dok && /\.json$/i.test(dok.file_name || "")) {
    const info = await TG(env, "getFile", { file_id: dok.file_id });
    if (!info.ok) return kirim(env, "Gagal mengambil berkas.");
    const isi = await (await fetch(`https://api.telegram.org/file/bot${env.TELEGRAM_BOT_TOKEN}/${info.result.file_path}`)).text();
    return papanManual(env, dok.file_name.replace(/\.json$/i, ""), isi);
  }
  if (dok && /^naskah/i.test((msg.caption || "").trim()) && /\.(txt|md)$/i.test(dok.file_name || "")) {
    const info = await TG(env, "getFile", { file_id: dok.file_id });
    if (!info.ok) return kirim(env, "Gagal mengambil berkas.");
    const isi = await (await fetch(`https://api.telegram.org/file/bot${env.TELEGRAM_BOT_TOKEN}/${info.result.file_path}`)).text();
    return antreanBaru(env, "tempel", isi.slice(0, 30000));
  }
  if (balasKe && balasKe.startsWith(PENANDA_ALASAN) && msg.text) {
    const id = idAman((/\[([^\]]+)\]/.exec(balasKe) || [])[1]);
    if (id) { await catatPersetujuan(env, id, "ditolak", "lain", msg.text.trim().slice(0, 1000)); return kirim(env, `Tercatat: ${id} ditolak — ${msg.text.trim().slice(0, 200)}`); }
  }
  const foto = msg.photo ? msg.photo[msg.photo.length - 1].file_id : null;
  const cap = (msg.caption || "").trim();
  if (foto && (!cap || /^(k|komen|komentar)(\b|$)/i.test(cap))) return balasKomentar(env, foto, cap.replace(/^(k|komen|komentar)\s*:?\s*/i, ""));
  const teks = (msg.text || "").trim();
  if (!teks) return;
  const t = teks.split(/\s+/)[0].toLowerCase().split("@")[0];
  const sisa = teks.slice(teks.split(/\s+/)[0].length).trim();
  if (t === "/start" || t === "/menu") { await TG(env, "setMyCommands", { commands: PERINTAH }); return kirim(env, "🏠 Menu utama", MENU); }
  if (t === "/bantuan") return kirim(env, BANTUAN, MENU);
  if (t === "/naskah") return sisa.length > 40 ? antreanBaru(env, "tempel", sisa) : tanyaNaskah(env);
  if (t === "/ide") return sisa ? antreanBaru(env, "ide", sisa) : tanyaIde(env);
  if (t === "/status") return daftarStatus(env);
  if (t === "/papan") return renderPapanRepo(env, sisa);
  if (t === "/reset") { await simpanPengaturan(env, "chat_" + env.DARI, "[]"); return kirim(env, "Riwayat obrolan dihapus."); }
  if (teks.startsWith("/")) return kirim(env, "Perintah tidak dikenal. /bantuan");
  return chatPribadi(env, teks);
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (url.pathname === "/pasang" && env.WEBHOOK_SECRET && url.searchParams.get("k") === env.WEBHOOK_SECRET) {
      const a = await TG(env, "setWebhook", { url: `${url.origin}/tg`, secret_token: env.WEBHOOK_SECRET, allowed_updates: ["message", "callback_query"] });
      const b = await TG(env, "setMyCommands", { commands: PERINTAH });
      return Response.json({ webhook: a.ok, perintah: b.ok });
    }
    if (url.pathname === "/cek" && env.WEBHOOK_SECRET && url.searchParams.get("k") === env.WEBHOOK_SECRET) {
      // Diagnosa AI tanpa membuka rahasia: model mana yang menjawab, berapa lama, galatnya apa.
      const mulai = Date.now(), hasil = { gemini_kunci: !!env.GEMINI_API_KEY, claude_kunci: !!env.ANTHROPIC_API_KEY };
      try { const h = await gemini(env, { system: "Jawab satu kata.", messages: [{ role: "user", content: "tes" }] }); hasil.gemini = { model: h.model, jawab: h.jawab.slice(0, 40) }; }
      catch (e) { hasil.gemini_galat = String(e.message || e).slice(0, 300); }
      hasil.detik = (Date.now() - mulai) / 1000;
      return Response.json(hasil);
    }
    if (url.pathname === "/tg" && req.method === "POST") {
      if (req.headers.get("x-telegram-bot-api-secret-token") !== env.WEBHOOK_SECRET) return new Response("no", { status: 403 });
      const u = await req.json();
      ctx.waitUntil(tangani(env, u).catch((e) => kirim(env, "Galat: " + String(e.message || e).slice(0, 200)).catch(() => {})));
      return new Response("ok");
    }
    return new Response("mesin-konten");
  },
};
