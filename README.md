# Otopark Plaka Tanıma

Raspberry Pi 5 + Raspberry Pi AI Camera ile araçların giriş-çıkış saatlerini kaydeder.

## Kurulum (Raspberry Pi OS, 64-bit)

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y imx500-all python3-picamera2
sudo reboot

python3 -m venv --system-site-packages .venv   # picamera2'yi görebilmek için
source .venv/bin/activate
pip install -r requirements.txt
```

## Kullanım

```bash
python -m otopark          # sistemi başlat
python -m otopark --preview  # sistemi canlı görüntüyle başlat
python -m otopark.report   # son kayıtları listele
python -m pytest           # testleri çalıştır
```

### Canlı önizleme

`--preview` ile başlatınca tarayıcıda `http://<pi-ip-adresi>:8000` adresini açın
(Pi'nin kendisinde `http://localhost:8000`; IP'yi `hostname -I` gösterir).
Görüntüde FPS, kare başına işlem süresi, okunan plakalar ve son giriş/çıkışlar yer alır.
Plaka kutularının renkleri: sarı = doğrulanıyor (ör. 2/3), yeşil = onaylandı,
kırmızı = geçersiz format, gri = düşük güven. Kimse izlemiyorken görüntü işlenmez.
Port `config.py` içindeki `preview_port` ayarıdır. Yayın aynı ağdaki herkese açıktır.

### Hız ayarları

- `detector_model`: Varsayılan `yolo-v9-t-256` hızlıdır. Uzaktaki küçük plakalar
  kaçıyorsa `yolo-v9-t-384-license-plate-end2end` kullanın.
- `region`: Sadece araçların geçtiği bölgeyi işler, ör. `(0.25, 0.4, 0.75, 1.0)`.
  Değerler görüntüye oranladır (sol, üst, sağ, alt). Önizlemede mavi çerçeveyle görünür.
  Bölge daraldıkça plaka modele daha büyük gider; 256 modelle birlikte kullanın.

Ayarlar `otopark/config.py` içindedir. Kayıtlar `otopark.db` (SQLite) dosyasında tutulur.

## Mimari

```
Kamera -> PlateReader (FastALPR) -> TurkishPlateValidator -> PlateConfirmer -> GateService -> VisitRepository
```

| Modül                | Sorumluluk                                            |
|----------------------|-------------------------------------------------------|
| `camera.py`          | Kameradan kare almak                                  |
| `plate_reader.py`    | Hazır modelle karedeki plakaları okumak               |
| `plate_validator.py` | OCR metnini düzeltmek, Türk plaka formatına göre doğrulamak |
| `plate_confirmer.py` | Birkaç karede tutarlı okunan plakayı onaylamak        |
| `gate_service.py`    | Onaylanan plakayı giriş mi çıkış mı diye karara bağlamak |
| `visit_repository.py`| Kayıtları SQLite'ta saklamak                          |
| `plate_monitor.py`   | Yukarıdakileri tek akışta birleştirmek                |
| `preview.py`         | Canlı görüntüyü okuma bilgileriyle tarayıcıya yayınlamak |
