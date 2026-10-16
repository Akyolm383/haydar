# 🎙️ Haydar - Akıllı Türkçe Sesli Komut ve Dinamik Ada Asistanı

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows 10/11" />
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/UI-PyQt6%20Dynamic%20Island-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6" />
  <img src="https://img.shields.io/badge/NLP-RapidFuzz%20%2B%20TR%20Norm-FF6F00?style=for-the-badge" alt="RapidFuzz" />
  <img src="https://img.shields.io/badge/Tests-8%20Passed-brightgreen?style=for-the-badge" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License" />
</p>

**Haydar**, mikrofonunuzdan gelen Türkçe konuşmaları anlık olarak metne dönüştüren, gelişmiş Türkçe metin normalizasyonu ve **RapidFuzz** benzerlik algoritmasıyla komutları eşleştiren, Windows üzerinde klavye ve sistem eylemlerini otonom gerçekleştiren modern bir masaüstü asistanıdır.

Apple'ın Dynamic Island konseptinden ilham alan şık, donanım ivmeli **PyQt6 arayüzü**, canlı ses dalgaları, durum rozetleri ve akıllı Alt+Tab pencere seçicisi ile tamamen kullanıcı dostudur.

---

## ✨ Öne Çıkan Özellikler

### 🛡️ 1. Wake-Word Koruması ("Haydar")
- **Yanlış Tetiklemelere Son:** Arka planda video oynatılırken veya ortamda konuşulurken Haydar istemsizce komut çalıştırmaz.
- **İki Aşamalı veya Tek Hamlede Dinleme:**
  - *"Haydar"* dediğinizde ada ekranın tepesinden süzülerek iner, **"👋 Efendim? Dinliyorum..."** der ve **7 saniye boyunca** vereceğiniz komutu bekler.
  - Veya doğrudan tek nefeste komut verebilirsiniz: *"Haydar video dursun"*, *"Haydar 15 saniye ileri sar"*.

### 🪟 2. Akıllı Alt+Tab Pencere Seçici (Yeni!)
- **Pencereleri Ekrana Sabitleme:** *"Haydar pencere değiştir"* (veya *"Haydar pencereleri göster"*, *"Haydar alt tab"*) dediğinizde Windows görev değiştiriciyi ekranda açık tutar (`Ctrl + Alt + Tab`).
- **Görsel & Sesli Etkileşim:** Dinamik Ada gök mavisi renge bürünerek **`🪟 Pencereler açıldı... Kaçıncı pencere? [ Alt + Tab ]`** uyarısıyla 8 saniyelik dinleme periyoduna geçer.
- **Sesle Pencere Seçimi:**
  - *"5. pencere"*, *"3"*, *"ikinci pencere"*, *"üçüncü"*, *"ilk pencere"* dediğinizde o pencereyi otomatik odaklar ve açar.
  - İsterseniz tek seferde: *"Haydar 5. pencere"* veya *"Haydar 3. pencereye geç"* diyerek doğrudan geçiş yapabilirsiniz.
  - *"İptal"* veya *"vazgeç"* derseniz pencere menüsünü kapatıp geri çekilir.

### 🌊 3. Canlı Ses Dalgaları (Audio Waveform Visualizer)
- Siz konuştukça ses seviyenizi gerçek zamanlı analiz eden **4 barlık dinamik ekolayzer**.
- Konuşma şiddetinize göre barlar ritmik olarak yükselip alçalır; konuşmadığınızda sakin bir nefes alma animasyonuna geçer.

### 🏝️ 4. Otomatik Gizlenen Dinamik Ada (HUD)
- **Temiz Ekran:** Boşta dururken ekranın üst kenarında gizlenir, ekran alanınızı işgal etmez.
- **Animasyonlu Durum Geçişleri:**
  - **Siyah / Nötr:** Dinleme ve bekleme durumunda.
  - **Zümrüt Yeşili:** Komut başarıyla algılandığında ve yürütüldüğünde (`[ Sağ Ok x3 ]`, `[ Win + D ]`).
  - **Gök Mavisi:** Alt+Tab pencere seçim modunda.
  - **Mercan Kırmızısı:** Eşleşmeyen veya anlaşılamayan ses girişlerinde.
- **Otomatik Gizlenme:** Komut icra edildikten sonra 1.8 saniye içinde kendiliğinden yukarı kayarak kaybolur.
- **%100 Sessiz Çalışma:** Rahatsız edici sistem bip sesleri kapalıdır.

### 🎵 5. Spotify Derin Masaüstü Entegrasyonu
- Spotify arka planda veya simge durumunda olsa bile ortam tuşları üzerinden kesintisiz çalışır.
- Akıllı çakışma koruması: *"Haydar müziği kapat"* veya *"şarkıyı kapat"* dendiğinde asistan kendini kapatmaz; yalnızca Spotify'ı duraklatır.

---

## 🎯 Desteklenen Sesli Komutlar Tablosu

| Kategori | Sesli Komut Örnekleri | Çalıştırılan Eylem | Tuş / Sistem Karşılığı |
| :--- | :--- | :--- | :--- |
| **Pencere & Masaüstü** | *"Haydar pencere değiştir"*, *"Haydar alt tab"* | Alt+Tab açar ve pencere numarası sorar | `Ctrl + Alt + Tab` (Seçim Modu) |
| | *"5. pencere"*, *"beşinci pencere"*, *"2. pencere"* | Seçilen N. pencereye odaklanır | `Alt + (Tab x N)` |
| | *"Haydar 5. pencere"*, *"Haydar 3. pencereye geç"* | Doğrudan N. pencereye geçiş yapar | `Alt + (Tab x N)` (Tek Seferde) |
| | *"Haydar masaüstüne dön"*, *"masaüstü"* | Masaüstünü gösterir veya gizler | `Win + D` |
| | *"Haydar pencereyi kapat"*, *"uygulamayı kapat"* | Aktif pencereyi sonlandırır | `Alt + F4` |
| **Medya & Video** | *"Haydar video dursun"*, *"oynat"*, *"durdur"* | Medyayı duraklatır / devam ettirir | `Space` |
| | *"Haydar 5 saniye ileri sar"*, *"ileriye sar"* | 5 saniye ileri sarar | `Right` (1 kez) |
| | *"Haydar 10 saniye ileri sar"* | 10 saniye ileri sarar | `Right` (2 kez) |
| | *"Haydar 15 saniye ileri sar"*, *"on beş saniye"* | 15 saniye ileri sarar | `Right` (3 kez) |
| | *"Haydar 30 saniye ileri sar"* | 30 saniye ileri sarar | `Right` (6 kez) |
| | *"Haydar 5 saniye geri sar"*, *"geriye sar"* | 5 saniye geri sarar | `Left` (1 kez) |
| | *"Haydar 15 saniye geri sar"* | 15 saniye geri sarar | `Left` (3 kez) |
| | *"Haydar tam ekran"*, *"ekranı kapla"* | Tam ekran moduna geçer / çıkar | `F` |
| **Ses Denetimi** | *"Haydar ses artsın"*, *"sesi yükselt"*, *"sesi aç"* | Sistem sesini 3 kademe artırır | `Volume Up x3` |
| | *"Haydar ses azalsın"*, *"sesi kıs"* | Sistem sesini 3 kademe kısar | `Volume Down x3` |
| | *"Haydar sesi kapat"*, *"sustur"* | Sesi tamamen kapatır / açar | `Volume Mute` |
| **Spotify** | *"Haydar spotify aç"*, *"spotifayı aç"* | Spotify uygulamasını başlatır | `spotify:` |
| | *"Haydar şarkıyı durdur"*, *"müzik çal"* | Şarkıyı oynatır / duraklatır | `Media Play/Pause` |
| | *"Haydar sonraki şarkı"*, *"şarkıyı geç"* | Sıradaki parçaya atlar | `Media Next Track` |
| | *"Haydar önceki şarkı"*, *"baştan çal"* | Önceki parçaya döner | `Media Prev Track` |
| | *"Haydar karışık çal"*, *"karıştır"* | Karışık çalmayı açar / kapatır | `Ctrl + S` |
| | *"Haydar şarkıyı tekrarla"* | Tekrar çalmayı açar / kapatır | `Ctrl + R` |
| | *"Haydar şarkıyı beğen"*, *"beğenilenlere ekle"* | Çalan parçayı beğenir | `Alt + Shift + B` |
| **Tarayıcı** | *"Haydar yeni sekme"*, *"yeni sekme aç"* | Tarayıcıda yeni sekme açar | `Ctrl + T` |
| | *"Haydar sekmeyi kapat"* | Mevcut sekmeden çıkar | `Ctrl + W` |
| | *"Haydar sayfayı yenile"* | Sayfayı tekrar yükler | `F5` |
| **Sistem** | *"Haydarı kapat"*, *"asistanı kapat"* | Haydar uygulamasından güvenle çıkar | `Çıkış` |

---

## 🚀 Kurulum (Adım Adım)

### Gereksinimler
- **İşletim Sistemi:** Windows 10 veya Windows 11 (64-bit)
- **Python Sürümü:** Python 3.10, 3.11 veya 3.12
- Çalışır durumda bir mikrofon

### 1. Depoyu Klonlayın
```powershell
git clone https://github.com/Akyolm383/haydar.git
cd haydar
```

### 2. Sanal Ortamı Oluşturun ve Aktive Edin
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Bağımlılıkları Yükleyin
```powershell
pip install -r requirements.txt
```

> **Not (PyAudio Kurulumu):** Eğer `pyaudio` derleme hatası alırsanız, `pip install pipwin && pipwin install pyaudio` kullanabilir veya doğrudan hazır `.whl` paketini yükleyebilirsiniz.

---

## 🎮 Kullanım ve Başlatma

### Yöntem 1: Çift Tıklayarak (Önerilen)
- Proje klasöründeki **`baslat.bat`** dosyasına çift tıklayın. Konsol penceresi görünmez; Haydar arka planda sessizce başlar ve sistem tepsisine yerleşir.

### Yöntem 2: Konsoldan
```powershell
python main.py
```

### 🛑 Haydar'ı Kapatma
1. **Sesle:** Mikrofona *"Haydarı kapat"* veya *"Asistanı kapat"* demeniz yeterlidir.
2. **Tek Tıkla:** Klasördeki **`kapat.bat`** dosyasına çift tıklayabilirsiniz.
3. **Sistem Tepsisinden:** Windows bildirim alanındaki yeşil simgeye sağ tıklayıp **"❌ Haydar'dan Çıkış"** diyebilirsiniz.

---

## 🛠️ Mimari ve Proje Yapısı

```
haydar/
├── config/
│   └── commands.json      # Komutlar, tetikleyiciler, kısayollar ve eşik değerleri
├── core/
│   ├── executor.py        # Klavye/fare eylemleri ve Alt+Tab pencere yöneticisi
│   ├── listener.py        # Mikrofon dinleme ve Google Speech API ses ayrıştırıcı
│   └── matcher.py         # Türkçe metin normalizasyonu, sayı ayrıştırma ve RapidFuzz
├── ui/
│   └── island.py          # PyQt6 Dinamik Ada HUD, animasyonlar ve ekolayzer
├── utils/
│   ├── sound.py           # Opsiyonel ses efektleri motoru
│   └── ui.py              # Zengin konsol çıktıları (Rich)
├── tests/
│   ├── test_config.py     # commands.json yapı ve doğrulama testleri
│   └── test_matcher.py    # NLP normalizasyon, fuzzy eşleşme ve pencere seçim testleri
├── baslat.bat             # Arka plan başlatıcı (pythonw)
├── kapat.bat              # Tek tıkla sonlandırıcı
├── requirements.txt       # Python paket bağımlılıkları
├── pytest.ini             # Pytest konfigürasyonu
└── README.md              # Dokümantasyon
```

---

## ⚙️ Özel Komut Ekleme (`config/commands.json`)

Yeni bir komut veya kısayol eklemek oldukça pratiktir. Sistem tepsisindeki Haydar simgesine sağ tıklayıp **"⚙️ Komutları Düzenle"** seçeneğini kullanabilir veya `config/commands.json` dosyasını doğrudan düzenleyebilirsiniz:

```json
{
  "id": "open_calculator",
  "description": "Hesap makinesini açar",
  "triggers": [
    "hesap makinesini aç",
    "hesap makinesi",
    "hesap makinesini başlat"
  ],
  "action_type": "run",
  "command": "calc.exe",
  "threshold": 70
}
```

Desteklenen eylem türleri (`action_type`):
- `hotkey`: Çoklu tuş kombinasyonu (`["win", "d"]`, `["ctrl", "t"]`)
- `press`: Tekil tuş basımı veya tekrarlı basım (`["right"]`, `repeat: 3`)
- `open`: URL veya protokol açma (`"spotify:"`, `"https://youtube.com"`)
- `run`: Sistem komutu veya uygulama çalıştırma
- `window_switcher`: Windows Alt+Tab akıllı pencere seçici
- `exit`: Haydar asistanından güvenle çıkış

---

## 🧪 Testleri Çalıştırma

Tüm testleri otomatik olarak çalıştırmak için:

```powershell
.venv\Scripts\pytest.exe -v
```

Çıktı:
```text
tests/test_config.py::test_commands_json_structure PASSED
tests/test_matcher.py::test_turkish_normalization PASSED
tests/test_matcher.py::test_wake_word_mode_activation PASSED
tests/test_matcher.py::test_continuous_mode PASSED
tests/test_matcher.py::test_unrelated_sentence_does_not_match PASSED
tests/test_matcher.py::test_spotify_commands PASSED
tests/test_matcher.py::test_extract_window_number PASSED
tests/test_matcher.py::test_window_switcher_command PASSED

============================== 8 passed in 0.40s ==============================
```

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında sunulmaktadır. Dilediğiniz gibi geliştirebilir ve kullanabilirsiniz.
