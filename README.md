# 🎙️ Haydar - Akıllı Türkçe Sesli Komut ve Dinamik Ada Asistanı

Haydar; mikrofonunuzdan gelen Türkçe konuşmaları **Google Speech API** ile metne dönüştüren, **RapidFuzz** ile %70+ benzerlik skoruyla eşleştiren ve Windows üzerinde klavye/fare kısayollarını otomatik çalıştıran modern bir sesli masaüstü otomasyon asistanıdır.

---

## 🛡️ Sadece "Haydar" Dediğinizde Devreye Girer (Wake-Word)

- **Yanlış Tetiklemelere Son:** Yanınızda biri konuşurken veya bir video izlerken Haydar asla araya girmez.
- **Nasıl Çalışır?** Komutlarınızın başına **"Haydar"** demeniz yeterlidir:
  - *"Haydar 15 saniye ileri sar"*
  - *"Haydar video dursun"*
  - *"Haydar ses artsın"*
  - *"Haydar masaüstüne dön"*
- **Sadece *"Haydar"*** derseniz ada tepeden inip **"👋 Efendim? Dinliyorum..."** der ve **7 saniye boyunca uyanık kalarak** komut vermenizi bekler! Hemen kapanmaz, siz konuşunca komutunuzu yerine getirir.

---

## 🌊 Canlı Ses Dalgaları (Audio Waveform Visualizer)

- Siz konuştukça ses seviyenizi anlık olarak analiz eden **4 barlık dinamik ve canlı yeşil ekolayzer** animasyonu çalışır.
- Ses tonunuzun şiddetine göre barlar yükselip alçalır, konuşmadığınızda sakin bir nefes alma ritmine geçer.

---

## 🤖 Gemini AI / Akıllı Sohbet Entegrasyonu

Haydar artık sadece klavye kısayollarını tetiklemekle kalmaz; tanımlı olmayan bir şey sorduğunuzda yapay zeka ile yanıtlar:
- *"Haydar saat kaç?"* -> `14:35`
- *"Haydar bugün günlerden ne?"* -> `Cuma, 16 Ekim 2026`
- *"Haydar gökyüzü neden mavi?"* -> Gemini AI ile akıllı ve özlü Türkçe yanıt
- Yanıtlar Dinamik Ada üzerinde şık bir mor/mavi AI rozetiyle gösterilir ve birkaç saniye sonra ada kapanır.

> **Gemini API Anahtarı Nasıl Eklenir?**
> `config/commands.json` dosyasını açıp `"gemini_api_key": "AIzaSy..."` alanına Google AI Studio anahtarınızı yazabilir veya ortam değişkeni olarak `GEMINI_API_KEY` tanımlayabilirsiniz. Anahtar olmasa dahi saat/tarih gibi temel komutlar yerel olarak anında çalışır.

---

## 🏝️ Otomatik Gizlenen Dinamik Ada (Dynamic Island)

- **Göz Yormaz, Ekranda Sürekli Durmaz:** Normalde ada ekranın üst çerçevesinin arkasında gizlidir, ekranınız %100 temiz kalır.
- **"Haydar" Dediğinizde Ekrana İner:** Siz *"Haydar ..."* dediğiniz an ekranın üstünden akıcı bir yaylanma animasyonuyla aşağı iner.
- **Canlı Geri Bildirim:** Duyduğu Türkçe metni yazar (*"15 saniye ileri sar"*, *"video dursun"*).
- **Yeşil Rozet & Otomatik Kaybolma:** Komutu başarıyla çalıştırdığında yeşil parlamayla eylemi gösterir (`[ Sağ Ok x3 ]`) ve **1.8 saniye sonra kendiliğinden tekrar yukarı kayıp kaybolur**.
- **%100 Sessiz Çalışma:** Rahatsız edici bip sesleri tamamen kaldırılmıştır.

---

## 🚀 Nasıl Başlatılır?

Masaüstündeki **`haydar`** klasöründe:
- **`baslat.bat`** dosyasına çift tıklayın. Siyah konsol penceresi açılmaz; Haydar arka planda sessizce mikrofonu dinlemeye geçer.

---

## 🛑 Nasıl Kapatılır?

Haydar'ı sonlandırmak için **3 pratik yöntem** mevcuttur:

1. **🗣️ Sesli Olarak:** Mikrofona *"Haydarı kapat"* veya *"Asistanı kapat"* demeniz yeterlidir. Ada *"Görüşmek üzere..."* deyip kendini kapatır.
2. **🖱️ Masaüstünden (Tek Tıkla):** Klasördeki **`kapat.bat`** dosyasına çift tıklayarak anında sonlandırabilirsiniz.
3. **🕒 Sistem Tepsisinden:** Windows saatinin yanındaki (bildirim alanı) yeşil Haydar simgesine sağ tıklayıp **"❌ Haydar'dan Çıkış"** seçeneğine tıklayabilirsiniz.

---

## 🎯 Hazır Gelen Temel Komutlar

| Sesli Komut / Örnekler | Tetiklenen Eylem | Tuş Kombinasyonu |
| :--- | :--- | :--- |
| **"masaüstüne dön"**, **"masaüstü"** | Masaüstünü göster/gizle | `Win + D` |
| **"ileriye sar"**, **"5 saniye ileri sar"** | Medyayı 5 saniye ileri sarar | `Sağ Ok (Right)` (1 kez) |
| **"10 saniye ileri sar"** | Medyayı 10 saniye ileri sarar | `Sağ Ok (Right)` (2 kez) |
| **"15 saniye ileri sar"**, **"on beş saniye ileri"** | Medyayı 15 saniye ileri sarar | `Sağ Ok (Right)` (3 kez) |
| **"30 saniye ileri sar"** | Medyayı 30 saniye ileri sarar | `Sağ Ok (Right)` (6 kez) |
| **"geriye sar"**, **"5 saniye geri sar"** | Medyayı 5 saniye geri sarar | `Sol Ok (Left)` (1 kez) |
| **"15 saniye geri sar"** | Medyayı 15 saniye geri sarar | `Sol Ok (Left)` (3 kez) |
| **"video dursun"**, **"durdur"**, **"oynat"** | Medyayı duraklat / oynat | `Boşluk (Space)` |
| **"tam ekran"**, **"ekranı kapla"** | Tam ekrana geç / çık | `F` |
| **"ses artsın"**, **"sesi aç"**, **"ses yükselsin"** | Sistem sesini artırır | `Volume Up` |
| **"ses azalsın"**, **"sesi kıs"**, **"ses kısılsın"** | Sistem sesini kısar | `Volume Down` |
| **"sesi kapat"**, **"sustur"** | Sesi kapat / aç | `Volume Mute` |
| **"pencereyi kapat"**, **"uygulamayı kapat"** | Aktif pencereyi kapatır | `Alt + F4` |
| **"uygulama değiştir"**, **"sonraki pencere"** | Pencereler arası geçiş | `Alt + Tab` |
| **"yeni sekme"** | Tarayıcıda yeni sekme açar | `Ctrl + T` |
| **"sekmeyi kapat"** | Tarayıcı sekmesini kapatır | `Ctrl + W` |
| **"sayfayı yenile"** | Sayfayı yeniden yükler | `F5` |
| **"saat kaç"**, **"tarih ne"** | Tarih ve saat bilgisi | `Dinamik Ada Yanıtı` |
| **Genel sorular (Gemini AI)** | Yapay zeka ile yanıtlar | `Dinamik Ada AI Yanıtı` |
| **"haydarı kapat"**, **"asistanı kapat"** | Haydar uygulamasından çıkar | `Çıkış` |

---

## ⚙️ Yeni Komut Ekleme (`config/commands.json`)

Yeni bir komut eklemek için `config/commands.json` dosyasını düzenleyebilirsiniz. Sistem tepsisindeki simgeye sağ tıklayıp **"⚙️ Komutları Düzenle"** seçeneğini seçerek dosyayı hemen açabilirsiniz.

---

## 🧪 Testleri Çalıştırma

```powershell
.venv\Scripts\pytest.exe -v
```
