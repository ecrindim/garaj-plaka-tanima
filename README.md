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
python -m otopark.report   # son kayıtları listele
python -m pytest           # testleri çalıştır
```

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
