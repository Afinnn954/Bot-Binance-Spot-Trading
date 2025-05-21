# SpotAI Trading Bot 🤖📈

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-Powered-blue.svg)](https://core.telegram.org/bots/api)
[![Binance API](https://img.shields.io/badge/Binance%20API-Integrated-yellow.svg)](https://binance-docs.github.io/apidocs/spot/en/)
[![Gemini AI](https://img.shields.io/badge/Gemini%20AI-Enhanced-purple.svg)](https://ai.google.dev/)

**SpotAI** is an automated cryptocurrency spot trading bot that interacts with Binance. It's controlled via Telegram and offers various trading modes, whale detection, and AI-powered dynamic trading parameter suggestions using Google's Gemini AI.

---

**🌐 Language / Bahasa:**
* [English](#english)
* [Bahasa Indonesia](#bahasa-indonesia)

---

## English

### ✨ Introduction
SpotAI is designed to automate your spot trading strategies on the Binance exchange. With a user-friendly Telegram interface, you can configure, monitor, and manage trades. The bot supports both real and simulated (mock/testnet) trading, allowing for strategy testing before committing real funds. It also incorporates AI to provide dynamic trading parameters and can alert you to potential whale activities in the market.

### 🙏 Credits / Special Thanks
* **Concept & Development:** Telegram [Telegram @JoestarMojo](https://t.me/JoestarMojo)

 
### 🚀 Key Features
* **🤖 Telegram Bot Interface:** Easily control and monitor the bot through Telegram commands and inline buttons.
* **📊 Multiple Trading Modes:** Choose from predefined strategies like "Conservative Scalp," "Consistent Drip," "Balanced Growth," and "Momentum Rider," each with unique risk/reward parameters.
* **🧠 AI-Powered Dynamic Mode:** Utilizes Google's Gemini AI to analyze market data (k-lines, RSI, EMA, Bollinger Bands) and suggest optimal Take Profit, Stop Loss, and Max Trade Time for trades.
* **🐳 Whale Detection:** (Currently mock) Generates simulated large transaction alerts. Can be configured to automatically trade based on these alerts or notify the admin.
* **📈 Market Analyzer:** Fetches real-time or mock market data, identifies top trending, high-volume, and potentially profitable BNB-based pairs.
* **🔄 Automated Trading:**
    * Automatically selects pairs based on volume and price change criteria.
    * Places BUY or SELL orders on Binance.
    * Monitors active trades for Take Profit, Stop Loss, or Max Trade Time.
* **💰 Real & Simulated Trading:**
    * Supports live trading on Binance Mainnet.
    * Supports paper trading on Binance Testnet.
    * Includes a mock mode for simulating trades with virtual price movements if no API keys are provided or if real trading is off.
* **📊 Daily Statistics & Limits:**
    * Tracks daily performance: total trades, wins, losses, profit percentage, and profit in BNB.
    * Configurable daily profit targets and loss limits to manage risk.
* **⚙️ Rich Configuration:** Extensive settings adjustable via Telegram commands or environment variables.
* **🌍 Multi-Language Support:** Interface available in English and Indonesian. Language can be changed on-the-fly.
* **🔔 Notifications:** Get real-time updates on trades, alerts, and bot status directly on Telegram.

### ✅ Advantages
* **Automation:** Set up your strategies and let the bot handle the execution, 24/7.
* **AI-Enhanced Decisions:** Leverage AI for dynamic trade parameter adjustments, potentially adapting to market conditions.
* **Risk Management:** Built-in Stop Loss, Daily Loss Limits, and precise trade amount configurations.
* **User-Friendly:** Easy to manage through a familiar Telegram interface.
* **Flexible:** Suitable for both beginners (with mock/testnet modes) and experienced traders.
* **Informative:** Provides insights into market trends, pair performance, and trade history.
* **Open & Customizable:** As a Python-based project, it can be further customized to fit specific needs.

### ⚠️ Risks and Disclaimer
* **Financial Risk:** Trading cryptocurrencies is inherently risky. This bot does **NOT** guarantee profits and can lead to financial losses. Use it at your own risk.
* **API Key Security:** You are responsible for the security of your Binance API keys. Ensure they are stored securely and have appropriate permissions.
* **Software Bugs:** While developed with care, the software may contain bugs that could lead to unexpected behavior or losses. Test thoroughly in mock or testnet mode.
* **Market Volatility:** Cryptocurrencies are highly volatile. Sudden market crashes or spikes can lead to significant losses, even with stop-loss mechanisms.
* **AI Imperfection:** AI-generated advice is based on historical data and patterns and is not infallible. It should not be considered financial advice.
* **Connectivity:** The bot requires a stable internet connection and uninterrupted access to Binance and Telegram APIs.
* **No Guarantee:** Past performance is not indicative of future results. The bot's effectiveness depends on its configuration, market conditions, and the chosen strategies.

### 🛠️ Prerequisites
* Python 3.8+
* `pip` (Python package installer)
* A Telegram Account
* A Telegram Bot Token (get from [BotFather](https://t.me/botfather))
* Binance Account (for live/testnet trading)
    * Binance API Key and Secret Key (with trading permissions enabled for spot)
* Google Gemini AI API Key (optional, for AI features - get from [Google AI Studio](https://aistudio.google.com/))

### ⚙️ Configuration
The bot can be configured using environment variables (recommended for sensitive data) or by directly modifying the `CONFIG` dictionary in the script.

**Environment Variables:**
* `TELEGRAM_BOT_TOKEN`: Your Telegram Bot token.
* `ADMIN_USER_IDS`: Your numeric Telegram User ID(s), comma-separated (e.g., "123456789,987654321"). The bot will only respond to commands from these admins.
* `BINANCE_API_KEY`: Your Binance API Key.
* `BINANCE_API_SECRET`: Your Binance API Secret.
* `GEMINI_API_KEY`: Your Google Gemini AI API Key.

**Key Configuration Parameters (within the script or via `/set` command):**
* `trading_pair`: Default trading pair (e.g., "BNBUSDT").
* `amount`: Fixed amount for trades (e.g., 0.01 BNB).
* `use_percentage` & `trade_percentage`: Use a percentage of your BNB balance for trades.
* `take_profit`, `stop_loss`: Default percentages for take profit and stop loss (overridden by trading modes or AI mode).
* `trading_enabled`: Master switch for enabling/disabling trading.
* `whale_detection`, `whale_threshold`, `auto_trade_on_whale`: Settings for whale detection.
* `trading_mode`: Default trading mode (e.g., "balanced_growth").
* `max_trade_time`: Maximum duration for a trade before it's closed automatically.
* `auto_select_pairs`: Enable/disable automatic selection of trading pairs.
* `use_testnet`: Set to `true` to use Binance Testnet, `false` for Mainnet.
* `use_real_trading`: Set to `true` to execute real trades, `false` for simulation (mock trades if API keys are invalid or `use_testnet` is also false). Mock mode is automatically true if `use_real_trading` is false.
* `ai_dynamic_mode`: Enable/disable AI-driven dynamic TP/SL/MaxTime.

### 🚀 Setup and Running the Bot
1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Afinnn954/Bot-Binance-Spot-Trading.git
    cd Bot-Binance-Spot-Trading
    ```
2.  **Install Dependencies:**
    Create a `requirements.txt` file with the following content:
    ```
    python-telegram-bot
    requests
    pandas
    pandas-ta
    google-generativeai
    asyncio
    ```
    Then install them:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set Up Environment Variables:**
    Create a `.env` file in the project root (optional, or set them system-wide):
    ```env
    TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
    ADMIN_USER_IDS="YOUR_TELEGRAM_USER_ID"
    BINANCE_API_KEY="YOUR_BINANCE_API_KEY"
    BINANCE_API_SECRET="YOUR_BINANCE_API_SECRET"
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```
    

4.  **Language Files:**
    Ensure you have `lang_en.json` and `lang_id.json` in the same directory as the bot script. These files contain the text strings for multi-language support. If they are missing, the bot might log errors and default to basic English messages for critical parts.

5.  **Run the Bot:**
    
    ```bash
    python spotAI.py
    ```

### 🤖 How to Use (Telegram Commands)
Interact with your bot on Telegram using these commands (only admins can use them):
* `/start`: Initializes the bot and shows the main menu.
* `/language`: Allows you to change the bot's language (English/Indonesian).
* `/help`: Displays a list of all available commands and their descriptions.
* `/status`: Shows the current operational status of the bot, trading engine, active trades, and daily statistics.
* `/config`: View the current bot configuration settings.
* `/set <parameter> <value>`: Modify a specific configuration parameter (e.g., `/set amount 0.05`).
* `/trades`: View a list of recent active and completed trades.
* `/whales`: (If mock enabled) Show recent mock whale transaction alerts.
* `/stats`: Display detailed daily trading statistics.
* `/setpercentage [on/off] [value]`: Enable/disable and set the percentage of BNB balance for trades.
* `/bnbpairs`: List BNB-based pairs from market data.
* `/whaleconfig`: Configure whale detection settings (toggle detection, auto-trade, strategy, threshold).
* `/volume`: Show top pairs by trading volume. Allows quick trading from buttons.
* `/trending`: Show top trending pairs by price change. Allows quick trading from buttons.
* `/modes`: Display details of available trading modes and their parameters.
* `/starttrade`: Start the trading engine. Prompts to select a trading mode.
* `/stoptrade`: Stop the trading engine and automated trading.
* `/enablereal`: Enable real trading with your Binance account (disables mock mode). Requires API keys and mainnet.
* `/disablereal`: Disable real trading and switch to mock/simulation mode.
* `/balance`: Fetch and display your current asset balances from Binance.
* `/testapi`: Test the connection and authentication with the Binance API.
* `/toggletestnet`: Switch between using Binance Testnet and Mainnet for API calls.
* `/setaimode`: Toggle the AI Dynamic Mode for trade parameters.

### 📈 Trading Modes Explained
The bot offers several predefined trading modes, each with different settings for Take Profit (TP), Stop Loss (SL), Max Trade Time, Volume Threshold, Price Change Threshold, and Max Concurrent Trades:
* **Conservative Scalp:** Aims for very small, frequent profits with tight stop losses. Requires high liquidity.
    * *R/R ~1:1.5*
* **Consistent Drip:** Focuses on small, consistent gains with a tight stop loss.
    * *R/R ~1:1.25*
* **Balanced Growth:** A moderate approach with balanced profit targets and controlled risk.
    * *R/R ~1:1.33*
* **Momentum Rider:** Attempts to catch small market momentums or trends with larger take profit targets and controlled stop losses.
    * *R/R ~1:1.75*

You can select a mode when starting trades or set a default mode in the configuration. The parameters of the selected mode will automatically apply to new trades unless AI Dynamic Mode is active.

### 🧠 AI Dynamic Mode
When enabled (`/setaimode` or `ai_dynamic_mode: true` in config), the bot utilizes Google's Gemini AI to determine trade parameters (Take Profit %, Stop Loss %, Max Trade Time) dynamically for each new trade.
* **Process:**
    1.  Fetches recent k-line (candlestick) data for the selected pair.
    2.  Calculates technical indicators like RSI, EMA, Bollinger Bands.
    3.  Constructs a prompt with current market data, candlestick info, and indicators.
    4.  Sends the prompt to the Gemini AI model.
    5.  Parses the AI's JSON response containing suggested `tp_percentage`, `sl_percentage`, `max_trade_time_seconds`, and a `rationale`.
    6.  Applies these parameters to the new trade.
* **Caching:** AI advice is cached for a configurable duration (default 5 minutes) to avoid excessive API calls for the same pair.
* **Fallback:** If AI fails to provide advice or an error occurs, the bot will fall back to the parameters of the currently selected manual trading mode.
* **Notification:** When AI parameters are used, the trade notification will include the AI's rationale.

### 🐳 Whale Detection
The whale detection feature monitors for (currently mock) large transactions.
* **Mock Alerts:** In mock mode, the bot generates random large buy/sell transactions for existing pairs.
* **Notifications:** When a mock whale transaction is detected, an alert is sent to the admin(s) on Telegram with details like token, amount, value, type, and potential impact.
* **Interactive Alerts:** Notifications include buttons to "Follow Whale" (create a trade in the same direction as the whale, or opposite if `counter_whale` strategy is set) or "Ignore Whale".
* **Auto-Trading:** Can be configured (`auto_trade_on_whale`) to automatically initiate a trade based on the whale alert and the defined `trading_strategy` ("follow_whale" or "counter_whale").
* **Configuration:** Threshold for what constitutes a "whale" amount (in BNB equivalent for mock data) is configurable.

### 🌍 Multi-Language Support
The bot supports multiple languages for its Telegram interface.
* **Supported Languages:** English (en) and Indonesian (id).
* **Mechanism:** Uses JSON files (`lang_en.json`, `lang_id.json`) for translations.
* **Switching Language:** Use the `/language` command to switch between available languages. The selected language is stored per user (chat\_id).
* **Fallback:** If a translation key is not found for the user's selected language, it falls back to English. If not found in English either, the key itself is returned.

---

## Bahasa Indonesia

### ✨ Pendahuluan
SpotAI dirancang untuk mengotomatiskan strategi perdagangan spot Anda di bursa Binance. Dengan antarmuka Telegram yang ramah pengguna, Anda dapat mengonfigurasi, memantau, dan mengelola perdagangan. Bot ini mendukung perdagangan riil dan simulasi (mock/testnet), memungkinkan pengujian strategi sebelum menggunakan dana riil. Bot ini juga menggabungkan AI untuk menyediakan parameter perdagangan dinamis dan dapat memberi tahu Anda tentang potensi aktivitas whale di pasar.

### 🙏 Kredit / Terima Kasih Khusus
* **Konsep & Pengembangan:** Telegram [Telegram @JoestarMojo](https://t.me/JoestarMojo)

 
### 🚀 Fitur Utama
* **🤖 Antarmuka Bot Telegram:** Kontrol dan pantau bot dengan mudah melalui perintah Telegram dan tombol inline.
* **📊 Mode Perdagangan Beragam:** Pilih dari strategi yang telah ditentukan seperti "Conservative Scalp," "Consistent Drip," "Balanced Growth," dan "Momentum Rider," masing-masing dengan parameter risiko/imbalan yang unik.
* **🧠 Mode Dinamis Berbasis AI:** Memanfaatkan Google Gemini AI untuk menganalisis data pasar (k-line, RSI, EMA, Bollinger Bands) dan menyarankan Take Profit, Stop Loss, dan Waktu Perdagangan Maksimal yang optimal untuk perdagangan.
* **🐳 Deteksi Whale:** (Saat ini mock) Menghasilkan lansiran transaksi besar yang disimulasikan. Dapat dikonfigurasi untuk berdagang secara otomatis berdasarkan lansiran ini atau memberi tahu admin.
* **📈 Penganalisis Pasar:** Mengambil data pasar riil atau mock, mengidentifikasi pasangan berbasis BNB yang sedang tren teratas, volume tinggi, dan berpotensi menguntungkan.
* **🔄 Perdagangan Otomatis:**
    * Secara otomatis memilih pasangan berdasarkan kriteria volume dan perubahan harga.
    * Menempatkan order BELI atau JUAL di Binance.
    * Memantau perdagangan aktif untuk Take Profit, Stop Loss, atau Batas Waktu Perdagangan Maksimal.
* **💰 Perdagangan Riil & Simulasi:**
    * Mendukung perdagangan langsung di Binance Mainnet.
    * Mendukung perdagangan kertas di Binance Testnet.
    * Menyertakan mode mock untuk menyimulasikan perdagangan dengan pergerakan harga virtual jika tidak ada kunci API yang disediakan atau jika perdagangan riil nonaktif.
* **📊 Statistik & Batas Harian:**
    * Melacak kinerja harian: total perdagangan, kemenangan, kerugian, persentase keuntungan, dan keuntungan dalam BNB.
    * Target keuntungan harian dan batas kerugian yang dapat dikonfigurasi untuk mengelola risiko.
* **⚙️ Konfigurasi Kaya Fitur:** Pengaturan ekstensif yang dapat disesuaikan melalui perintah Telegram atau variabel lingkungan.
* **🌍 Dukungan Multi-Bahasa:** Antarmuka tersedia dalam bahasa Inggris dan Indonesia. Bahasa dapat diubah secara langsung.
* **🔔 Notifikasi:** Dapatkan pembaruan waktu-nyata tentang perdagangan, lansiran, dan status bot langsung di Telegram.

### ✅ Keunggulan
* **Otomatisasi:** Atur strategi Anda dan biarkan bot menangani eksekusi, 24/7.
* **Keputusan yang Ditingkatkan AI:** Manfaatkan AI untuk penyesuaian parameter perdagangan dinamis, berpotensi beradaptasi dengan kondisi pasar.
* **Manajemen Risiko:** Stop Loss bawaan, Batas Kerugian Harian, dan konfigurasi jumlah perdagangan yang presisi.
* **Ramah Pengguna:** Mudah dikelola melalui antarmuka Telegram yang familiar.
* **Fleksibel:** Cocok untuk pemula (dengan mode mock/testnet) dan pedagang berpengalaman.
* **Informatif:** Memberikan wawasan tentang tren pasar, kinerja pasangan, dan riwayat perdagangan.
* **Terbuka & Dapat Disesuaikan:** Sebagai proyek berbasis Python, dapat disesuaikan lebih lanjut untuk kebutuhan spesifik.

### ⚠️ Risiko dan Penafian
* **Risiko Finansial:** Perdagangan mata uang kripto secara inheren berisiko. Bot ini **TIDAK** menjamin keuntungan dan dapat menyebabkan kerugian finansial. Gunakan dengan risiko Anda sendiri.
* **Keamanan Kunci API:** Anda bertanggung jawab atas keamanan kunci API Binance Anda. Pastikan disimpan dengan aman dan memiliki izin yang sesuai.
* **Bug Perangkat Lunak:** Meskipun dikembangkan dengan hati-hati, perangkat lunak mungkin mengandung bug yang dapat menyebabkan perilaku tak terduga atau kerugian. Uji secara menyeluruh dalam mode mock atau testnet.
* **Volatilitas Pasar:** Mata uang kripto sangat fluktuatif. Kehancuran atau lonjakan pasar yang tiba-tiba dapat menyebabkan kerugian signifikan, bahkan dengan mekanisme stop-loss.
* **Ketidaksempurnaan AI:** Saran yang dihasilkan AI didasarkan pada data dan pola historis dan tidak sempurna. Ini tidak boleh dianggap sebagai nasihat keuangan.
* **Konektivitas:** Bot memerlukan koneksi internet yang stabil dan akses tanpa gangguan ke API Binance dan Telegram.
* **Tidak Ada Jaminan:** Kinerja masa lalu tidak menunjukkan hasil di masa depan. Efektivitas bot bergantung pada konfigurasi, kondisi pasar, dan strategi yang dipilih.

### 🛠️ Prasyarat
* Python 3.8+
* `pip` (penginstal paket Python)
* Akun Telegram
* Token Bot Telegram (dapatkan dari [BotFather](https://t.me/botfather))
* Akun Binance (untuk perdagangan live/testnet)
    * Kunci API dan Kunci Rahasia Binance (dengan izin perdagangan diaktifkan untuk spot)
* Kunci API Google Gemini AI (opsional, untuk fitur AI - dapatkan dari [Google AI Studio](https://aistudio.google.com/))

### ⚙️ Konfigurasi
Bot dapat dikonfigurasi menggunakan variabel lingkungan (disarankan untuk data sensitif) atau dengan memodifikasi kamus `CONFIG` secara langsung dalam skrip.

**Variabel Lingkungan:**
* `TELEGRAM_BOT_TOKEN`: Token Bot Telegram Anda.
* `ADMIN_USER_IDS`: ID Pengguna Telegram numerik Anda, dipisahkan koma (mis., "123456789,987654321"). Bot hanya akan merespons perintah dari admin ini.
* `BINANCE_API_KEY`: Kunci API Binance Anda.
* `BINANCE_API_SECRET`: Rahasia API Binance Anda.
* `GEMINI_API_KEY`: Kunci API Google Gemini AI Anda.

**Parameter Konfigurasi Utama (dalam skrip atau melalui perintah `/set`):**
* `trading_pair`: Pasangan perdagangan default (mis., "BNBUSDT").
* `amount`: Jumlah tetap untuk perdagangan (mis., 0.01 BNB).
* `use_percentage` & `trade_percentage`: Gunakan persentase dari saldo BNB Anda untuk perdagangan.
* `take_profit`, `stop_loss`: Persentase default untuk take profit dan stop loss (diganti oleh mode perdagangan atau mode AI).
* `trading_enabled`: Saklar utama untuk mengaktifkan/menonaktifkan perdagangan.
* `whale_detection`, `whale_threshold`, `auto_trade_on_whale`: Pengaturan untuk deteksi whale.
* `trading_mode`: Mode perdagangan default (mis., "balanced_growth").
* `max_trade_time`: Durasi maksimum untuk perdagangan sebelum ditutup secara otomatis.
* `auto_select_pairs`: Aktifkan/nonaktifkan pemilihan pasangan perdagangan otomatis.
* `use_testnet`: Atur ke `true` untuk menggunakan Binance Testnet, `false` untuk Mainnet.
* `use_real_trading`: Atur ke `true` untuk mengeksekusi perdagangan riil, `false` untuk simulasi (perdagangan mock jika kunci API tidak valid atau `use_testnet` juga false). Mode mock secara otomatis true jika `use_real_trading` false.
* `ai_dynamic_mode`: Aktifkan/nonaktifkan TP/SL/MaxTime dinamis yang digerakkan AI.

### 🚀 Pengaturan dan Menjalankan Bot
1.  **Klon Repositori:**
    ```bash
    git clone https://github.com/Afinnn954/Bot-Binance-Spot-Trading.git
    cd Bot-Binance-Spot-Trading
    ```
2.  **Instal Dependensi:**
    Buat file `requirements.txt` dengan konten berikut:
    ```
    python-telegram-bot
    requests
    pandas
    pandas-ta
    google-generativeai
    asyncio
    ```
    Kemudian instal:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Atur Variabel Lingkungan:**
    Buat file `.env` di root proyek (opsional, atau atur secara sistem-wide):
    ```env
    TELEGRAM_BOT_TOKEN="TOKEN_BOT_TELEGRAM_ANDA"
    ADMIN_USER_IDS="ID_PENGGUNA_TELEGRAM_ANDA"
    BINANCE_API_KEY="KUNCI_API_BINANCE_ANDA"
    BINANCE_API_SECRET="RAHASIA_API_BINANCE_ANDA"
    GEMINI_API_KEY="KUNCI_API_GEMINI_AI_ANDA"
    ```
    

4.  **File Bahasa:**
    Pastikan Anda memiliki `lang_en.json` dan `lang_id.json` di direktori yang sama dengan skrip bot. File-file ini berisi string teks untuk dukungan multi-bahasa. Jika hilang, bot mungkin mencatat kesalahan dan default ke pesan bahasa Inggris dasar untuk bagian-bagian penting.

5.  **Jalankan Bot:**
    
    ```bash
    python spotAI.py
    ```

### 🤖 Cara Penggunaan (Perintah Telegram)
Berinteraksi dengan bot Anda di Telegram menggunakan perintah ini (hanya admin yang dapat menggunakannya):
* `/start`: Menginisialisasi bot dan menampilkan menu utama.
* `/language`: Memungkinkan Anda mengubah bahasa bot (Inggris/Indonesia).
* `/help`: Menampilkan daftar semua perintah yang tersedia dan deskripsinya.
* `/status`: Menunjukkan status operasional bot saat ini, mesin perdagangan, perdagangan aktif, dan statistik harian.
* `/config`: Melihat pengaturan konfigurasi bot saat ini.
* `/set <parameter> <nilai>`: Mengubah parameter konfigurasi tertentu (mis., `/set amount 0.05`).
* `/trades`: Melihat daftar perdagangan aktif dan selesai baru-baru ini.
* `/whales`: (Jika mock diaktifkan) Tampilkan lansiran transaksi whale mock baru-baru ini.
* `/stats`: Menampilkan statistik perdagangan harian terperinci.
* `/setpercentage [on/off] [nilai]`: Mengaktifkan/menonaktifkan dan mengatur persentase saldo BNB untuk perdagangan.
* `/bnbpairs`: Daftar pasangan berbasis BNB dari data pasar.
* `/whaleconfig`: Konfigurasi pengaturan deteksi whale (aktifkan deteksi, perdagangan otomatis, strategi, ambang batas).
* `/volume`: Tampilkan pasangan teratas berdasarkan volume perdagangan. Memungkinkan perdagangan cepat dari tombol.
* `/trending`: Tampilkan pasangan tren teratas berdasarkan perubahan harga. Memungkinkan perdagangan cepat dari tombol.
* `/modes`: Menampilkan detail mode perdagangan yang tersedia dan parameternya.
* `/starttrade`: Memulai mesin perdagangan. Meminta untuk memilih mode perdagangan.
* `/stoptrade`: Menghentikan mesin perdagangan dan perdagangan otomatis.
* `/enablereal`: Mengaktifkan perdagangan riil dengan akun Binance Anda (menonaktifkan mode mock). Memerlukan kunci API dan mainnet.
* `/disablereal`: Menonaktifkan perdagangan riil dan beralih ke mode mock/simulasi.
* `/balance`: Mengambil dan menampilkan saldo aset Anda saat ini dari Binance.
* `/testapi`: Menguji koneksi dan otentikasi dengan API Binance.
* `/toggletestnet`: Beralih antara menggunakan Binance Testnet dan Mainnet untuk panggilan API.
* `/setaimode`: Mengaktifkan/menonaktifkan Mode Dinamis AI untuk parameter perdagangan.

### 📈 Penjelasan Mode Perdagangan
Bot ini menawarkan beberapa mode perdagangan yang telah ditentukan, masing-masing dengan pengaturan berbeda untuk Take Profit (TP), Stop Loss (SL), Waktu Perdagangan Maksimal, Ambang Batas Volume, Ambang Batas Perubahan Harga, dan Perdagangan Bersamaan Maksimal:
* **Conservative Scalp:** Bertujuan untuk keuntungan yang sangat kecil dan sering dengan stop loss yang ketat. Membutuhkan likuiditas tinggi.
    * *R/R ~1:1.5*
* **Consistent Drip:** Berfokus pada keuntungan kecil yang konsisten dengan stop loss yang ketat.
    * *R/R ~1:1.25*
* **Balanced Growth:** Pendekatan moderat dengan target keuntungan yang seimbang dan risiko terkontrol.
    * *R/R ~1:1.33*
* **Momentum Rider:** Mencoba menangkap momentum pasar kecil atau tren dengan target take profit yang lebih besar dan stop loss terkontrol.
    * *R/R ~1:1.75*

Anda dapat memilih mode saat memulai perdagangan atau mengatur mode default dalam konfigurasi. Parameter mode yang dipilih akan secara otomatis berlaku untuk perdagangan baru kecuali Mode Dinamis AI aktif.

### 🧠 Mode Dinamis AI
Saat diaktifkan (`/setaimode` atau `ai_dynamic_mode: true` dalam konfigurasi), bot menggunakan Google Gemini AI untuk menentukan parameter perdagangan (Take Profit %, Stop Loss %, Waktu Perdagangan Maksimal) secara dinamis untuk setiap perdagangan baru.
* **Proses:**
    1.  Mengambil data k-line (candlestick) terbaru untuk pasangan yang dipilih.
    2.  Menghitung indikator teknis seperti RSI, EMA, Bollinger Bands.
    3.  Menyusun prompt dengan data pasar saat ini, info candlestick, dan indikator.
    4.  Mengirim prompt ke model Gemini AI.
    5.  Mem-parsing respons JSON dari AI yang berisi saran `tp_percentage`, `sl_percentage`, `max_trade_time_seconds`, dan `rationale` (alasan).
    6.  Menerapkan parameter ini ke perdagangan baru.
* **Caching:** Saran AI disimpan dalam cache untuk durasi yang dapat dikonfigurasi (default 5 menit) untuk menghindari panggilan API yang berlebihan untuk pasangan yang sama.
* **Fallback:** Jika AI gagal memberikan saran atau terjadi kesalahan, bot akan kembali ke parameter mode perdagangan manual yang sedang dipilih.
* **Notifikasi:** Ketika parameter AI digunakan, notifikasi perdagangan akan menyertakan alasan dari AI.

### 🐳 Deteksi Whale
Fitur deteksi whale memantau (saat ini mock) transaksi besar.
* **Lansiran Mock:** Dalam mode mock, bot menghasilkan transaksi beli/jual besar secara acak untuk pasangan yang ada.
* **Notifikasi:** Ketika transaksi whale mock terdeteksi, lansiran dikirim ke admin di Telegram dengan detail seperti token, jumlah, nilai, jenis, dan potensi dampak.
* **Lansiran Interaktif:** Notifikasi menyertakan tombol untuk "Ikuti Whale" (membuat perdagangan searah dengan whale, atau berlawanan jika strategi `counter_whale` diatur) atau "Abaikan Whale".
* **Perdagangan Otomatis:** Dapat dikonfigurasi (`auto_trade_on_whale`) untuk secara otomatis memulai perdagangan berdasarkan lansiran whale dan `trading_strategy` yang ditentukan ("follow_whale" atau "counter_whale").
* **Konfigurasi:** Ambang batas untuk apa yang dianggap sebagai jumlah "whale" (dalam ekuivalen BNB untuk data mock) dapat dikonfigurasi.

### 🌍 Dukungan Multi-Bahasa
Bot mendukung beberapa bahasa untuk antarmuka Telegramnya.
* **Bahasa yang Didukung:** Inggris (en) dan Indonesia (id).
* **Mekanisme:** Menggunakan file JSON (`lang_en.json`, `lang_id.json`) untuk terjemahan.
* **Mengganti Bahasa:** Gunakan perintah `/language` untuk beralih antar bahasa yang tersedia. Bahasa yang dipilih disimpan per pengguna (chat\_id).
* **Fallback:** Jika kunci terjemahan tidak ditemukan untuk bahasa yang dipilih pengguna, maka akan kembali ke bahasa Inggris. Jika juga tidak ditemukan dalam bahasa Inggris, kunci itu sendiri yang akan dikembalikan.

---

*Disclaimer: This bot is provided as-is, without any warranty. Trading cryptocurrencies involves significant risk of loss. Use this software at your own risk. The developers are not responsible for any financial losses incurred.*

*Penafian: Bot ini disediakan apa adanya, tanpa jaminan apa pun. Perdagangan mata uang kripto melibatkan risiko kerugian yang signifikan. Gunakan perangkat lunak ini dengan risiko Anda sendiri. Pengembang tidak bertanggung jawab atas kerugian finansial yang terjadi.*
