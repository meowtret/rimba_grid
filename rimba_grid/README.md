# Rimba Grid

Plugin QGIS untuk membuat grid koordinat di **Print Layout** dengan label gaya peta Indonesia:

- **BT / BB** — Bujur Timur / Bujur Barat
- **LU / LS** — Lintang Utara / Lintang Selatan

Contoh label: `122°56'00" BT`, `0°42'00" LS`.

## Pemasangan

1. QGIS → **Plugins → Manage and Install Plugins → Install from ZIP**.
2. Pilih `rimba_grid.zip`, klik **Install Plugin**.
3. Ikon Rimba Grid muncul di toolbar QGIS dan di toolbar Layout Designer.

## Cara pakai

1. Buat layout dan item peta seperti biasa.
2. Klik ikon **Rimba Grid**.
3. Pilih **Layout** dan **Item peta**.
4. Pada **Grid**:
   - `➕ Buat grid baru`: grid EPSG:4326 baru dibuat lengkap dengan interval, bingkai, dan label.
   - `✎ <nama grid>`: grid yang sudah ada diubah. Centang **Hanya ganti label** bila gaya grid lama (interval, bingkai, huruf) ingin dipertahankan dan cukup labelnya saja yang jadi BT/LS.
5. Atur interval (atau klik **Hitung otomatis dari luas peta**), format label, dan tampilan.
6. Klik **Terapkan**. Perubahan bisa dibatalkan dengan Ctrl+Z di Layout Designer.

## Catatan

- Label disimpan sebagai **ekspresi kustom** grid layout. Proyek tetap menampilkan BT/LS walau dibuka di komputer yang tidak memasang plugin ini.
- Nilai 0° (ekuator/meridian nol) ditulis tanpa akhiran.
- Grid berproyeksi (misalnya UTM) tidak bisa diberi label BT/LS. Plugin akan memberi peringatan; hilangkan centang "Hanya ganti label" agar grid dialihkan ke EPSG:4326.
- Pengaturan terakhir disimpan otomatis.

## Format yang tersedia

| Format | Contoh |
|---|---|
| Derajat-menit-detik | `122°56'00" BT` |
| Derajat-menit | `122°56' BT` / `122°56,5' BT` |
| Derajat desimal | `122,9333° BT` |

Lisensi: GPL-2.0 atau yang lebih baru.
