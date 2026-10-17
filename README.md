# 🎙️ Haydar - Akıllı Türkçe Sesli Komut ve Dinamik Ada Asistanı

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows 10/11" />
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/UI-PyQt6%20Dynamic%20Island-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6" />
  <img src="https://img.shields.io/badge/NLP-RapidFuzz%20%2B%20TR%20Norm-FF6F00?style=for-the-badge" alt="RapidFuzz" />
  <img src="https://img.shields.io/badge/Web_Bridge-Manifest%20V3-00B4D8?style=for-the-badge" alt="Web Bridge" />
  <img src="https://img.shields.io/badge/Tests-12%20Passed-brightgreen?style=for-the-badge" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License" />
</p>

**Haydar**, mikrofonunuzdan gelen Türkçe konuşmaları anlık olarak metne dönüştüren, gelişmiş Türkçe metin normalizasyonu ve **RapidFuzz** benzerlik algoritmasıyla komutları eşleştiren, Windows üzerinde klavye/fare kısayollarını ve tarayıcı DOM eylemlerini otonom gerçekleştiren modern bir masaüstü asistanıdır.

Apple'ın Dynamic Island konseptinden ilham alan şık, donanım ivmeli **PyQt6 arayüzü**, canlı ses dalgaları, durum rozetleri, akıllı Alt+Tab pencere seçicisi, kesintisiz **Sürekli Dinleme (Toggle)** modu ve **yerleşik tarayıcı eklentisi (Web Bridge)** ile tamamen kullanıcı dostudur.

---

## ✨ Öne Çıkan Özellikler

### 🛡️ 1. Wake-Word Koruması ("Haydar")
- **Yanlış Tetiklemelere Son:** Arka planda video oynatılırken veya ortamda konuşulurken Haydar istemsizce komut çalıştırmaz.
- **İki Aşamalı veya Tek Hamlede Dinleme:**
  - *"Haydar"* dediğinizde ada ekranın tepesinden süzülerek iner, **"👋 Efendim? Dinliyorum..."** der ve **7 saniye boyunca** vereceğiniz komutu bekler.
  - Veya doğrudan tek nefeste komut verebilirsiniz: *"Haydar video dursun"*, *"Haydar sonraki bölüm"*, *"Haydar 15 saniye ileri sar"*.

### ⚡ 2. Sürekli Dinleme Toggle Modu ("Haydar dinle" / "Haydar dinleme") (Yeni!)
- **"Haydar dinle" (veya "dinle", "sürekli dinle"):** Haydar kesintisiz dinleme moduna geçer.
  - Dinamik Ada göz alıcı **elektrik moru (Electric Violet)** temaya bürünür ve **`[ Sürekli Dinleme ]`** rozetini gösterir.
  - Bu modda her komutun başında *"Haydar"* demenize gerek kalmaz! Arka arkaya *"sesi aç"*, *"sonraki bölüm"*, *"videoyu durdur"*, *"pencere değiştir"* diyebilirsiniz.
  - Haydar komutları icra ettikten sonra uykuya dalmaz, sürekli dinlemeye devam eder.
- **"Haydar dinleme" (veya "dinleme", "dinlemeyi durdur"):**
  - Sürekli dinleme modunu kapatır ve Dinamik Ada kehribar uyarısıyla **`[ Wake Word: Haydar ]`** normal moduna döner.

### 🌐 3. Haydar Web Bridge - Akıllı Tarayıcı Kontrolü
- **Yerel WebSocket Köprüsü:** Haydar, arka planda güvenli ve hafif bir `ws://127.0.0.1:8765` sunucusu çalıştırır. Tarayıcı eklentisi doğrudan bağlanır.
- **Evrensel Video ve Film Başlatıcı (Yeni!):**
  - *"Haydar videoyu aç"*, *"videoyu başlat"*, *"filmi başlat"*, *"videoyu oynat"*, *"videoyu bul"*:
  - Film, dizi ve anime sitelerinde player açılmadığında veya sahte kapaklar/büyük oynat butonları arkasında kaldığında Haydar sayfayı tarar.
  - HTML5 `<video>` etiketlerini, Video.js, JWPlayer, Plyr büyük play butonlarını, "Filmi Başlat/İzle" butonlarını ve Vidmoly/Doodstream gibi gömülü iframe playerlarını anında bulup ekrana odaklar ve oynatmayı başlatır!
- **Dizilerde & Videolarda Otomasyon:**
  - *"Haydar sonraki bölüm"* (veya *"sıradaki bölüm"*): YouTube, Netflix, yerli/yabancı dizi ve anime sitelerindeki "Sonraki Bölüm" butonunu anında bulup tıklar!
  - *"Haydar introyu atla"*: Netflix ve video oynatıcılardaki intro/jenerik atlama butonuna tıklar.
  - *"Haydar reklamı geç"*: YouTube ve web video oynatıcılarındaki reklam atlama butonuna basar.
  - *"Haydar aşağı kaydır"* / *"yukarı kaydır"*: Sayfayı yumuşak bir animasyonla akıcı şekilde kaydırır.
- **Dinamik Buton Tıklama ("Haydar tıkla [X]"):**
  - *"Haydar tıkla abone ol"*, *"Haydar sepete ekle butonuna bas"*, *"Haydar tıkla sonraki sayfa"* gibi ifadeleri sayfadaki tüm buton, link ve metinlerde arar ve tıklar.
- **Görsel Vurgu Efekti:** Sayfada tıklanan butonun veya oynatıcının üzerinde 1 saniyeliğine neon zümrüt yeşili bir parlama halkası görünür.
- **Dinamik Ada Geri Bildirimi:** Eylem gerçekleştiğinde ada yeşil parlayarak **`🎯 "Video Oynatıcı" başlatıldı [ Web Extension ]`** rozeti gösterir.

### 🪟 3. Akıllı Alt+Tab Pencere Seçici
- **Pencereleri Ekrana Sabitleme:** *"Haydar pencere değiştir"* (veya *"Haydar pencereleri göster"*, *"Haydar alt tab"*) dediğinizde Windows görev değiştiriciyi ekranda açık tutar (`Ctrl + Alt + Tab`).
- **Görsel & Sesli Etkileşim:** Dinamik Ada gök mavisi renge bürünerek **`🪟 Pencereler açıldı... Kaçıncı pencere? [ Alt + Tab ]`** uyarısıyla 8 saniyelik dinleme periyoduna geçer.
- **Sesle Pencere Seçimi:**
  - *"5. pencere"*, *"3"*, *"ikinci pencere"*, *"üçüncü"*, *"ilk pencere"* dediğinizde o pencereyi otomatik odaklar ve açar.
  - İsterseniz tek seferde: *"Haydar 5. pencere"* veya *"Haydar 3. pencereye geç"* diyerek doğrudan geçiş yapabilirsiniz.
  - *"İptal"* veya *"vazgeç"* derseniz pencere menüsünü kapatıp geri çekilir.

### 🌊 4. Canlı Ses Dalgaları (Audio Waveform Visualizer)
- Siz konuştukça ses seviyenizi gerçek zamanlı analiz eden **4 barlık dinamik ekolayzer**.
- Konuşma şiddetinize göre barlar ritmik olarak yükselip alçalır; konuşmadığınızda sakin bir nefes alma animasyonuna geçer.

### 🏝️ 5. Otomatik Gizlenen Dinamik Ada (HUD)
- **Temiz Ekran:** Boşta dururken ekranın üst kenarında gizlenir, ekran alanınızı işgal etmez.
- **Animasyonlu Durum Geçişleri:**
  - **Siyah / Nötr:** Dinleme ve bekleme durumunda.
  - **Zümrüt Yeşili:** Komut başarıyla algılandığında ve yürütüldüğünde (`[ Sağ Ok x3 ]`, `[ Web Extension ]`, `[ Win + D ]`).
  - **Gök Mavisi:** Alt+Tab pencere seçim modunda.
  - **Mercan Kırmızısı:** Eşleşmeyen veya anlaşılamayan ses girişlerinde.
- **Otomatik Gizlenme:** Komut icra edildikten sonra 1.8 saniye içinde kendiliğinden yukarı kayarak kaybolur.
- **%100 Sessiz Çalışma:** Rahatsız edici sistem bip sesleri kapalıdır.

### 🎵 6. Spotify Derin Masaüstü Entegrasyonu
- Spotify arka planda veya simge durumunda olsa bile ortam tuşları üzerinden kesintisiz çalışır.
- Akıllı çakışma koruması: *"Haydar müziği kapat"* veya *"şarkıyı kapat"* dendiğinde asistan kendini kapatmaz; yalnızca Spotify'ı duraklatır.

---

## 🎯 Desteklenen Sesli Komutlar Tablosu

| Kategori | Sesli Komut Örnekleri | Çalıştırılan Eylem | Karşılık / Rozet |
| :--- | :--- | :--- | :--- |
| **Sürekli Dinleme (Toggle)** | *"Haydar dinle"*, *"sürekli dinle"*, *"dinle"* | Sürekli aktif dinlemeyi açar (Wake-word gereksizleşir) | `[ Sürekli Dinleme ]` |
| | *"Haydar dinleme"*, *"dinleme"*, *"dinlemeyi durdur"* | Sürekli dinlemeyi kapatır, Wake-word moduna döner | `[ Wake Word: Haydar ]` |
| **Tarayıcı & Web Bridge** | *"Haydar videoyu aç"*, *"videoyu başlat"*, *"filmi başlat"* | Sayfadaki video oynatıcıyı bulur ve başlatır | `[ Web Extension ]` |
| | *"Haydar sonraki bölüm"*, *"sıradaki bölüm"* | Dizide/videoda sonraki bölüme geçer | `[ Web Extension ]` |
| | *"Haydar önceki bölüm"*, *"bir önceki bölüm"* | Önceki bölüme geçer | `[ Web Extension ]` |
| | *"Haydar introyu atla"*, *"jeneriği atla"* | Video introsunu / jeneriğini atlar | `[ Web Extension ]` |
| | *"Haydar reklamı geç"*, *"reklamı atla"* | Video reklamını anında geçer | `[ Web Extension ]` |
| | *"Haydar aşağı kaydır"*, *"sayfayı aşağı kaydır"* | Sayfayı yumuşakça aşağı kaydırır | `[ Web Extension ]` |
| | *"Haydar yukarı kaydır"*, *"yukarı çık"* | Sayfayı yukarı kaydırır | `[ Web Extension ]` |
| | *"Haydar tıkla [Hedef]"*, *"abone ol butonuna bas"* | Sayfadaki belirtilen butonu bulur ve tıklar | `[ Web Extension ]` |
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
| **Tarayıcı Sekmeleri** | *"Haydar yeni sekme"*, *"yeni sekme aç"* | Tarayıcıda yeni sekme açar | `Ctrl + T` |
| | *"Haydar sekmeyi kapat"* | Mevcut sekmeden çıkar | `Ctrl + W` |
| | *"Haydar sayfayı yenile"* | Sayfayı tekrar yükler | `F5` |
| **Sistem** | *"Haydarı kapat"*, *"asistanı kapat"* | Haydar uygulamasından güvenle çıkar | `Çıkış` |

---

## 🧩 Tarayıcı Eklentisinin Kurulumu (Chrome / Edge / Brave)

Haydar'ın tarayıcıdaki butonları bulup tıklayabilmesi için eklentiyi 1 dakikada tarayıcınıza ekleyebilirsiniz:

1. Tarayıcınızın adres çubuğuna şunu yazın ve Enter'a basın:
   - **Chrome için:** `chrome://extensions`
   - **Edge için:** `edge://extensions`
   - **Brave için:** `brave://extensions`
2. Sağ üst köşedeki **"Geliştirici modu" (Developer mode)** anahtarını açın.
3. Sol üstte beliren **"Paketlenmemiş öğe yükle" (Load unpacked)** butonuna tıklayın.
4. Açılan dosya seçim penceresinde projenin içindeki **`browser_extension`** klasörünü seçin.
5. Hazır! Artık Haydar çalışırken tarayıcınızdaki aktif sekmeyi sesle yönetebilirsiniz.

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

---

## 🎮 Kullanım ve Başlatma

### Yöntem 1: Çift Tıklayarak (Önerilen)
- Proje klasöründeki **`baslat.bat`** dosyasına çift tıklayın. Konsol penceresi görünmez; Haydar arka planda sessizce başlar, hem ses tanımayı hem de yerel Web Bridge sunucusunu devreye sokar.

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
├── browser_extension/     # Manifest V3 Chrome/Edge/Brave Eklentisi
│   ├── manifest.json      # Eklenti izin ve yapılandırması
│   ├── background.js      # WebSocket istemcisi ve sekme mesaj yönlendirici
│   ├── content.js         # DOM arama motoru, özel seçiciler ve tıklama yöneticisi
│   ├── styles.css         # Yeşil parlama / vurgu animasyonu
│   └── icons/             # 16x16, 48x48, 128x128 eklenti ikonları
├── config/
│   └── commands.json      # Komutlar, tetikleyiciler, kısayollar ve eşik değerleri
├── core/
│   ├── executor.py        # Klavye/fare eylemleri, Alt+Tab ve Web Bridge çağrıları
│   ├── listener.py        # Mikrofon dinleme ve Google Speech API ses ayrıştırıcı
│   ├── matcher.py         # Türkçe NLP normalizasyon, sayı & buton hedefi ayrıştırma
│   └── web_bridge.py      # Yerel WebSocket sunucusu (ws://127.0.0.1:8765)
├── ui/
│   └── island.py          # PyQt6 Dinamik Ada HUD, animasyonlar ve ekolayzer
├── utils/
│   ├── sound.py           # Opsiyonel ses efektleri motoru
│   └── ui.py              # Zengin konsol çıktıları (Rich)
├── tests/
│   ├── test_config.py     # commands.json yapı ve doğrulama testleri
│   ├── test_matcher.py    # NLP, fuzzy eşleşme, pencere seçimi ve dinamik buton testleri
│   └── test_web_bridge.py # WebSocket sunucu yaşam döngüsü testleri
├── baslat.bat             # Arka plan başlatıcı (pythonw)
├── kapat.bat              # Tek tıkla sonlandırıcı
├── requirements.txt       # Python paket bağımlılıkları
├── pytest.ini             # Pytest konfigürasyonu
└── README.md              # Kapsamlı dokümantasyon
```

---

## 🧪 Testleri Çalıştırma

Tüm testleri otomatik olarak çalıştırmak için:

```powershell
.venv\Scripts\pytest.exe -v
```

Çıktı:
```text
tests/test_config.py::test_commands_json_structure PASSED                [  9%]
tests/test_matcher.py::test_turkish_normalization PASSED                 [ 18%]
tests/test_matcher.py::test_wake_word_mode_activation PASSED             [ 27%]
tests/test_matcher.py::test_continuous_mode PASSED                       [ 36%]
tests/test_matcher.py::test_unrelated_sentence_does_not_match PASSED     [ 45%]
tests/test_matcher.py::test_spotify_commands PASSED                      [ 54%]
tests/test_matcher.py::test_extract_window_number PASSED                 [ 63%]
tests/test_matcher.py::test_window_switcher_command PASSED               [ 72%]
tests/test_matcher.py::test_extract_browser_click_target PASSED          [ 81%]
tests/test_matcher.py::test_browser_commands PASSED                      [ 90%]
tests/test_web_bridge.py::test_web_bridge_server_lifecycle PASSED        [100%]

============================= 11 passed in 1.23s ==============================
```

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında sunulmaktadır.
