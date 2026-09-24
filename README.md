<p align="center">
  <img src="assets/meu-logo.png" alt="Mersin Üniversitesi" width="140" />
</p>

<h1 align="center">Deneyap Kart Web Agent — Linux</h1>

<p align="center">
  Deneyap Blok web arayüzü ile Deneyap kartlar arasında websocket köprüsü kuran
  masaüstü ajanın <b>Linux portu</b> (Debian/Ubuntu/antiX tested).
  <br />
  <a href="https://github.com/deneyapkart/Deneyap-Kart-Web">Windows orijinali (deneyapkart/Deneyap-Kart-Web)</a> temel alınmıştır.
</p>

<p align="center">
  <b>Mersin Üniversitesi</b> kapsamında,
  <br />
  Proje Yürütücüsü Dr. Öğr. Üyesi <b>Erman Uzun</b> önderliğinde geliştirilmiştir.
</p>

---

## Ne yapar?

Blok tabanlı Deneyap arayüzünden gelen komutları `arduino-cli` ile karta taşır.
Frontend ile `ws://localhost:49182` (ana kanal) ve `ws://localhost:49183`
(seri monitör) üzerinden konuşur. Orijinal protokolle birebir uyumludur,
web tarafında değişiklik gerekmez.

- Kod derleme ve karta yükleme
- Yükleme seçenekleri (fqbn parametreleri)
- Seri monitör (okuma + yazma)
- Kütüphane arama / kurma
- Deneyap core sürümü değiştirme
- Kart takma/çıkarma algılama

Desteklenen kartlar: Deneyap Kart, Deneyap Mini, Deneyap Kart 1A,
Deneyap Kart G, Deneyap Mini v2, Deneyap Kart 1A v2.

## Hızlı başlangıç

```bash
sudo apt install -y python3-venv python3-pip python3-tk python3-serial xdg-utils curl
curl -fsSL https://downloads.arduino.cc/arduino-cli/arduino-cli_0.35.3_Linux_64bit.tar.gz -o /tmp/arduino-cli.tgz
sudo tar xzf /tmp/arduino-cli.tgz -C /usr/local/bin arduino-cli
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/python main.py --no-tray
```

Sonra Deneyap Blok sayfasını açıp kartı seçin (`/dev/ttyUSB0` vb.) ve yükleyin.
Bayraklar: `--no-tray` (traysiz mod), `--no-setup` (ilk kurulumu atla).
Teknik detaylar için [`README_LINUX.md`](README_LINUX.md).

## Proje ekibi

- **Proje Yürütücüsü:** Dr. Öğr. Üyesi Erman Uzun — Mersin Üniversitesi
- **Geliştirme:** Mersin Üniversitesi kapsamında yürütülmüştür.

## Kaynak ve lisans

- Windows orijinali: [deneyapkart/Deneyap-Kart-Web](https://github.com/deneyapkart/Deneyap-Kart-Web)
  (teşekkürler @kinkintama ve @DogushC). Bu repo onun Linux portudur.
- Lisans: **GPLv3** (`LICENSE`), orijinal projeden devralınmıştır.

## Katkı

Hata bildirimi ve pull request'lere açık. Lütfen sürüm notlarında
test ettiğiniz dağıtımı ve kartı belirtin.
