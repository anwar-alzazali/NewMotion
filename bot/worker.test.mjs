// node --test bot/
import test from "node:test";
import assert from "node:assert/strict";
import { bacaTombol, tombolPersetujuan, tombolAlasan, tombolSesudah, idAman, catatanKeputusan, bolehAkses, ALASAN } from "./worker.js";

test("tombol persetujuan dapat dibaca balik dan muat batas 64 byte Telegram", () => {
  const id = idAman("2026-11-21 Nuh Mengejek / versi 2");
  for (const b of [...tombolPersetujuan(id).flat(), ...tombolAlasan(id).flat()]) {
    assert.ok(new TextEncoder().encode(b.callback_data).length <= 64);
    assert.ok(bacaTombol(b.callback_data));
  }
  assert.deepEqual(bacaTombol(`st:${id}`), { aksi: "st", id, alasan: null });
  assert.deepEqual(bacaTombol(`al:${id}:hook`), { aksi: "al", id, alasan: "hook" });
  assert.deepEqual(bacaTombol(`va:${id}`), { aksi: "va", id, alasan: null });
  assert.deepEqual(bacaTombol(`vr:${id}`), { aksi: "vr", id, alasan: null });
  assert.deepEqual(bacaTombol(`nu:${id}`), { aksi: "nu", id, alasan: null });
});

test("data tombol asing atau berbahaya ditolak", () => {
  for (const d of ["", "x", "nom:10000", "st:../../etc", "al:abc:ngawur", "st:A B", "uji:ok"]) assert.equal(bacaTombol(d), null, d);
});

test("catatan keputusan berisi alasan yang terbaca", () => {
  const c = catatanKeputusan("nuh-1", "ditolak", "visual", null, "2026-11-21T00:00:00Z");
  assert.equal(c.alasan, ALASAN.visual); assert.equal(c.kode_alasan, "visual"); assert.equal(c.keputusan, "ditolak");
});

test("hanya pemilik yang boleh memakai bot", () => {
  assert.ok(bolehAkses({ TELEGRAM_CHAT_ID: "123\n" }, 123));
  assert.ok(!bolehAkses({ TELEGRAM_CHAT_ID: "123" }, 456));
});

test("keputusan bisa diubah dan keputusan lama tersimpan di riwayat", () => {
  const id = "nuh-1";
  const ub = tombolSesudah(id, "✅ Disetujui").flat().find((b) => b.callback_data.startsWith("ub:"));
  assert.deepEqual(bacaTombol(ub.callback_data), { aksi: "ub", id, alasan: null });
  const a = catatanKeputusan(id, "disetujui", null, null, "t1");
  const b = catatanKeputusan(id, "ditolak", "hook", null, "t2", a);
  const c = catatanKeputusan(id, "disetujui", null, null, "t3", b);
  assert.equal(c.keputusan, "disetujui");
  assert.deepEqual(c.riwayat.map((r) => r.keputusan), ["disetujui", "ditolak"]);
  assert.equal(c.riwayat[1].alasan, ALASAN.hook);
  assert.equal(a.riwayat, undefined);
});

import { readFileSync } from "node:fs";
import { kartuStatus, tombolKartu, idAntrean, statusBaru } from "./worker.js";

test("kartu status bot identik dengan versi Python (fixture bersama)", () => {
  const f = JSON.parse(readFileSync(new URL("../tests/data/kartu_status.json", import.meta.url)));
  assert.equal(kartuStatus(f.status), f.teks);
  // Fixture berstatus dalil gagal: tidak boleh ada Lanjut, hanya Revisi/Batal.
  const tombol = tombolKartu(f.status).flat().map((b) => b.callback_data);
  assert.ok(!tombol.includes(`nl:${f.status.id}`));
  assert.ok(tombol.includes(`nr:${f.status.id}`) && tombol.includes(`nb:${f.status.id}`));
});

test("tombol Lanjut hanya muncul bila semua dalil lolos", () => {
  const st = { id: "uji-dalil", tahap: { tinjau: "jalan", dalil: "selesai" }, ket: {} };
  assert.equal(tombolKartu(st)[0][0].callback_data, "nl:uji-dalil");
  for (const dalil of ["gagal", "jalan", "belum"])
    assert.ok(!tombolKartu({ ...st, tahap: { ...st.tahap, dalil } }).flat().some((b) => b.callback_data === "nl:uji-dalil"));
});

test("naskah yang gagal divalidasi tidak buntu: ada Revisi dan Batal", () => {
  const st = { id: "uji-gagal", tahap: { diterima: "gagal", dalil: "belum", tinjau: "belum" }, ket: {} };
  const t = tombolKartu(st).flat().map((b) => b.callback_data);
  assert.ok(t.includes("nr:uji-gagal") && t.includes("nb:uji-gagal") && !t.includes("nl:uji-gagal"));
});

test("id antrean aman, pendek, dan tombolnya terbaca", () => {
  const id = idAntrean("Nabi Hud dan Kaum 'Ad — azab angin", new Date("2026-11-21T09:05:00Z"));
  assert.equal(id, "261121-1605-nabi-hud-dan-kaum");
  for (const a of ["nl", "nr", "nb", "va", "vr"]) assert.deepEqual(bacaTombol(`${a}:${id}`), { aksi: a, id, alasan: null });
  const st = statusBaru(id, "x", "ide", 1);
  assert.equal(st.tahap.diterima, "jalan");
  assert.ok(tombolKartu(st).flat().every((b) => b.callback_data === "menu"));
});

import { keGemini, pilihModelGemini, labelBiaya } from "./worker.js";

test("pesan format Claude diubah ke format Gemini (teks, gambar, peran)", () => {
  const g = keGemini("sistem", [
    { role: "user", content: [{ type: "image", source: { type: "base64", media_type: "image/jpeg", data: "QUJD" } }, { type: "text", text: "balas" }] },
    { role: "assistant", content: "oke" },
  ]);
  assert.equal(g.systemInstruction.parts[0].text, "sistem");
  assert.deepEqual(g.contents[0].parts[0], { inline_data: { mime_type: "image/jpeg", data: "QUJD" } });
  assert.equal(g.contents[0].parts[1].text, "balas");
  assert.equal(g.contents[1].role, "model");
});

test("model Gemini: dua flash terbaru lalu satu lite", () => {
  assert.deepEqual(pilihModelGemini(["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3.0-flash", "gemini-2.0-flash-lite"]),
    ["gemini-3.0-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite"]);
});

test("label biaya menandai penyedia", () => {
  assert.equal(labelBiaya({ idr: 0, model: "gemini-2.5-flash" }), "Rp0 · Gemini");
  assert.equal(labelBiaya({ idr: 12, model: "claude-sonnet-4-5" }), "≈Rp12 · Claude");
});

test("pratinjau gagal menampilkan tombol ulang, tetapi status jalan/selesai tidak", () => {
  const dasar = { id: "uji-pratinjau", tahap: { tinjau: "selesai", sutradara: "gagal", tinjau_visual: "belum", dalil: "selesai" }, ket: {} };
  assert.equal(tombolKartu(dasar)[0][0].callback_data, "nu:uji-pratinjau");
  assert.equal(tombolKartu({ ...dasar, tahap: { ...dasar.tahap, tinjau_visual: "jalan" } })[0][0].callback_data, "menu");
  assert.equal(tombolKartu({ ...dasar, tahap: { ...dasar.tahap, tinjau_visual: "selesai" } })[0][0].callback_data, "menu");
});

test("produksi final gagal memberi tombol ulangi", async () => {
  const { tombolKartu, bacaTombol } = await import("./worker.js");
  const st = { id: "a1", tahap: { tinjau: "selesai", dalil: "selesai", sutradara: "selesai", tinjau_visual: "selesai", narasi: "gagal", render: "belum" } };
  const t = tombolKartu(st);
  assert.equal(t[0][0].callback_data, "fu:a1");
  assert.deepEqual(bacaTombol("fu:a1"), { aksi: "fu", id: "a1", alasan: null });
});

import { cekPapan } from "./worker.js";

test("papan manual: JSON rusak atau kosong ditolak, papan bershot diterima", () => {
  assert.match(cekPapan("{rusak"), /tidak terbaca/);
  assert.match(cekPapan("[]"), /objek/);
  assert.match(cekPapan("{}"), /kosong/);
  assert.equal(cekPapan(JSON.stringify({ cerita: { shot: [{ at: 0 }] } })), null);
});

import { bacaHasil, gabungStatistik, tombolHasil } from "./worker.js";

test("statistik: format bebas dibaca, singkatan rb/k/jt, persen opsional", () => {
  assert.deepEqual(bacaHasil("tiktok h1 12rb 850 40 12 35%"), { platform: "tiktok", hari: 1, tayang: 12000, suka: 850, komentar: 40, bagikan: 12, tuntas: 35 });
  assert.deepEqual(bacaHasil("FB h7 1,2jt 3.400 210 95"), { platform: "facebook", hari: 7, tayang: 1200000, suka: 3400, komentar: 210, bagikan: 95, tuntas: null });
  assert.equal(bacaHasil("tiktok 7 1.5k 100 5 2 22,5%").tuntas, 22.5);
  assert.equal(bacaHasil("tiktok 7 1.5k 100 5 2").tayang, 1500);
  assert.ok(bacaHasil("h1 100 2 3 4").galat);
  assert.ok(bacaHasil("tiktok h3 100 2 3 4").galat);
  assert.ok(bacaHasil("tiktok h1 100 2").galat);
  assert.equal(bacaTombol("sh:abc-1").aksi, "sh");
  assert.equal(tombolHasil("abc")[0][0].callback_data, "sh:abc");
});

test("statistik: catatan platform+hari yang sama ditimpa, lainnya tetap", () => {
  let s = gabungStatistik(null, { platform: "tiktok", hari: 1, tayang: 10 }, "w1");
  s = gabungStatistik(s, { platform: "facebook", hari: 1, tayang: 5 }, "w2");
  s = gabungStatistik(s, { platform: "tiktok", hari: 1, tayang: 99 }, "w3");
  assert.equal(s.catatan.length, 2);
  assert.equal(s.catatan.find((c) => c.platform === "tiktok").tayang, 99);
});
