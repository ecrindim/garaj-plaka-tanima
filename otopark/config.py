from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Sistemin tüm ayarları tek yerde."""

    database_path: Path = Path("otopark.db")

    # Hazır eğitilmiş modeller (FastALPR)
    # 256 hızlıdır; uzaktaki küçük plakalar kaçıyorsa 384'e dönülebilir.
    detector_model: str = "yolo-v9-t-256-license-plate-end2end"
    ocr_model: str = "cct-xs-v2-global-model"

    # Kamera
    frame_size: tuple[int, int] = (1280, 720)
    # Kareler arası ek bekleme. 0 = olabildiğince hızlı; işlemciyi
    # rahatlatmak gerekirse artırılabilir (ör. 0.1).
    frame_interval_seconds: float = 0.0

    # Sadece bu bölge işlenir: (sol, üst, sağ, alt), görüntü boyutuna oranla 0.0-1.0.
    # Ör. (0.25, 0.4, 0.75, 1.0) = ortadaki yarı genişlik, alttaki %60.
    # None = görüntünün tamamı. Önizlemede mavi çerçeveyle gösterilir.
    region: tuple[float, float, float, float] | None = None

    # Canlı önizleme (python -m otopark --preview)
    preview_port: int = 8000

    # Okuma güvenilirliği
    min_confidence: float = 0.6
    votes_required: int = 3          # Plaka onaylanmadan önce kaç kez okunmalı
    vote_window_seconds: float = 3.0  # Bu okumalar kaç saniye içinde olmalı

    # Onaylanan plaka bu kadar saniye hiç görülmezse yeniden algılanabilir.
    # (Bariyerde bekleyen aracın tekrar tekrar kaydedilmesini önler.)
    quiet_period_seconds: float = 30.0
