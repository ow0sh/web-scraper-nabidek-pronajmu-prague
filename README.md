# Web Scraper Nabídek Pronájmu
Hlídá nové nabídky na populárních realitních serverech.

[**Docker image (aktuální z master větvě) - `janch32/web-scraper-nabidek-pronajmu`**](https://hub.docker.com/r/janch32/web-scraper-nabidek-pronajmu)

*Tato aplikace je aktuálně nastavená pro hledání pronájmu bytů v Praze.*

Nicméně je možné při spuštění aplikace nakonfigurovat, které  **dispozice bytu** (počet místností) hledat.

## Podporované realitní servery
- EuroBydlení
- iDNES Reality
- REALCITY
- realingo
- Remax
- Sreality
- UlovDomov
- BezRealitky

## Spuštění
- Lze spustit lokálně nebo v Dockeru
- **Lokální spuštění**
    - Je vyžadován **Python 3.11+**
    - Před prvním spuštěním nainstalujte závislosti `make install` (vytvoří se lokální virtuální prostředí `.venv`)
    - Vytvořte si lokální soubor `.env.local` a nastavte v něm všechny požadované parametry (minimálně však Telegram bot token, cílový chat a požadované dispozice bytu)
    - následně je možné spustit `make run` nebo v debug režimu `make debug`
- **Spuštění v Dockeru**
    - Přiložená Docker Compose konfigurace souží pro vývoj. Stačí ji spustit příkazem `docker-compose up -d` (má zapnutý debug mód)
    - K dispozici je také sestavený Docker obraz v Ducker Hub, vždy aktuální s master větví - [`janch32/web-scraper-nabidek-pronajmu`](https://hub.docker.com/r/janch32/web-scraper-nabidek-pronajmu)
    - Kromě toho je možné vytvořit "produkční" Docker image díky `Dockerfile`. Při spuštění kontejneru je nutné nastavit všechny požadované env proměnné (ne v v .env.local!)

Aplikace při prvním spuštění nevypíše žádné nabídky, pouze si stáhne seznam těch aktuálních. Poté každých 30 mint (nastavitelné přes env proměnné) kontroluje nové nabídky na realitních serverech a ty přeposílá do Telegram chatu. Ve stejném chatu průběžně upravuje stavovou zprávu s časem poslední aktualizace a posílá tam i chybová hlášení. Aplikace nemusí běžet pořád, po opětovném spuštění pošle všechny nové nabídky od posledního spuštění.

## Konfigurace přes Env proměnné
- `TELEGRAM_BOT_TOKEN` - Token Telegram bota získaný přes `@BotFather`.
- `TELEGRAM_CHAT_ID` - ID cílového Telegram chatu, kam se mají posílat nabídky, stavové zprávy i chyby programu.
- `DISPOSITIONS` - Obsahuje seznam dispozic oddělených čárkou. Např.: `DISPOSITIONS=2+kk,2+1,others`
- `MIN_PRICE` - Volitelná minimální cena nájmu v Kč. Nabídky s nižší cenou se přeskočí.
- `MAX_PRICE` - Volitelná maximální cena nájmu v Kč. Nabídky s vyšší cenou se přeskočí.

### Seznam dostupných hodnot parametru `DISPOSITIONS`
- `1+kk`
- `1+1`
- `2+kk`
- `2+1`
- `3+kk`
- `3+1`
- `4+kk`
- `4+1`
- `5++` (5+kk a více místností)
- `others` (jiné, atypické nebo neznámé velikosti)

### Další konfigurovatelné Env proměnné
Tyto hodnoty jsou nastavené pro bězné použití a není potřeba ji měnit. Zde je každopádně popis těchto hodnot.
- `DEBUG` (boolean, výchozí vypnuto). Aktivuje režim ladění aplikace, především podrobnějšího výpisu do konzole. Vhodné pro vývoj.
- `FOUND_OFFERS_FILE` Cesta k souboru, kam se ukládají dříve nalezené nabídky. Aplikace si soubor vytvoří, ale složka musí existovat. Pokud aplikace nebyla nějakou dobu spuštěna (řádově týdny) je dobré tento soubor smazat - aplikace by toto vyhodnotila jako velké množství nových nabídek a zaspamovala by Telegram chat.
- `REFRESH_INTERVAL_DAYTIME_MINUTES` - interval po který se mají stáhnout nejnovější nabídky Výchozí 30min, doporučeno minimálně 10min
- `REFRESH_INTERVAL_NIGHTTIME_MINUTES` - noční interval stahování nabídek. Jde o čas mezi 22h-6h. Výchozí 90min, doporučeno vyšší než denní interval
