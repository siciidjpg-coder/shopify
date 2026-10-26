# Havainnointipilotti, 26.10.2026

Tämä versio kerää kilpailijahavaintoja. Se ei kirjoita Shopifyhin eikä lähetä sähköpostia.

## Oikealla datalla testattu

- `python monitor.py --catalog /polku/shopify-sample.json` haki robots.txt-tiedostot ja kaksi julkista tuotesivua tunnistettavalla HKIPriceMonitor-käyttäjäagentilla.
- Kahdesta suomalaisesta kaupasta löytyi yhteensä 12 varianttihavaintoa yhdelle Portwest 2201 -mallille (kuusi kokoa kummassakin).
- 200 Shopify-variantin aiemmasta otoksesta löytyi viisi täsmälleen vastaavaa kelvollista SKU:ta. Kuudennen SKU sisältää näkymättömän merkin; sitä ei siivottu automaattisesti.
- Molemmat lähteet ilmoittivat L- ja XL-koot loppuneiksi. Suojaintukun varianttikohtainen verollinen hinta oli 48,95 EUR. Turun Turvavarusteen 26,36 EUR oli veroton hinta, jota ei hyväksytty verolliseksi.
- Hyväksyttyjä hintamuutosehdotuksia: **0**. Valmistaja-, pakkaus- ja varianttivarmennus on kesken. Yhden lähteen puuttuvaa verollista hintaa ei saa ohittaa ja väittää toista lähdettä Suomen halvimmaksi.

Havainnot ovat yhden ajon tuloksia, eivät pysyviä hintatietoja. Koko sivun sisältöä tai kaupan tuoteotosta ei tallenneta julkiseen repositorioon.

## Tunnisteiden selvitys

Valmistajan Portwest Technical Data 2201 -lomake yhdistää seuraavat tunnisteet:

| SKU | EAN13 |
| --- | --- |
| 2201WHRS | 5036108106677 |
| 2201WHRM | 5036108106684 |
| 2201WHRL | 5036108106691 |
| 2201WHRXL | 5036108106707 |
| 2201WHRXXL | 5036108106714 |
| 2201WHRXXXL | 5036108106721 |

Lähde: valmistajan lomake, päivätty 25.2.2026, https://m.media-amazon.com/images/I/71CU13F2txL.pdf . Ristiintarkistus: https://static.thesafetysupplycompany.co.uk/2201WHR.pdf . Lomakkeiden GTIN/DUN14-kuljetuspakkauskoodeja ei käytetä yksittäisen vaatteen EAN13-koodina. Shopify-tunnisteita ei ole muutettu. Valmistajalta suoraan saatu ajantasainen varianttisyöte on suositeltava ennen laajentamista.

## Lähteet ja rajat

- https://www.turunturvavaruste.fi/tuote/elintarviketeollisuusmallisto/
- https://www.turunturvavaruste.fi/tilausehdot/ (hinnat oletusarvoisesti verottomia; yritysmyynti)
- https://www.suojaintukku.fi/portwest-2201-elintarvikehyvaksytty-haalari/
- https://www.suojaintukku.fi/verkkokaupan-ehdot/

Keruu koskee vain konfiguraatiossa olevia tuotesivuja. Tämä ei ole koko Suomen kattava automaattinen tuotehaku. Robots.txt tarkistetaan jokaisella ajolla, pyyntöjen välissä odotetaan vähintään kaksi sekuntia, uudelleenohjauksia ei seurata ja tuntematon sivurakenne hylätään. Lähteiden käyttöehdot on tarkistettava uudelleen ennen laajamittaista keruuta. Kokonaisten kuvausten ja kuvien kopiointi ei kuulu pilottiin.

## Testaus ja käyttöönotto

40 yksikkötestiä läpäisty. Hintojen laskenta, simuloitu hinnanmuutos ja palautus, täsmälleen/yli 15 prosentin raja, hintalukko, katkaisin, virheet ja saman tapahtuman uusinta testattu. `change_simulator.py` on vain muistissa toimiva testiympäristö; sillä ei voi tehdä oikeita Shopify-kirjoituksia. Sähköposti muodostetaan luonnokseksi, sitä ei lähetetä.

`render.yaml` valmistelee 15 minuutin havaintoajon Frankfurtissa. Ajo päättyy viimeistään 180 sekunnin timeoutiin. Render estää yhden cron-palvelun päällekkäiset ajot. Hintakirjoituksia ei ole ajopolussa, ja `ENABLE_PRICE_WRITES=true` keskeyttää ohjelman. Havaintojen keruun voi katkaista asettamalla `MONITOR_PAUSED=true` ja ottamalla ympäristömuutoksen käyttöön. Render-palvelua ei ole luotu.

Cronin vähimmäismaksu on 1 USD/kk; 512 MB -cronin laskentahinta on 0,00016 USD/min. 31 päivän kuukaudessa 15 minuutin välein tehtävät enintään kolmen minuutin ohjelma-ajot vastaavat noin 1,43 USD laskentaa. Pilotin arvio on noin 1–2 USD/kk ennen veroja; käynnistymisen lisäaika ja ylimääräiset ajot voivat nostaa summaa. Tämä ei ole hintakatto. Lähteet: https://render.com/docs/cronjobs ja https://render.com/articles/render-vs-netlify . Maksullisen palvelun luonti odottaa käyttäjän hyväksyntää. Cronin paikallinen tulostiedosto ei ole pysyvä; havainnot kirjataan myös palvelulokiin. Tuotantokirjoitukset tarvitsevat erillisen pysyvän auditointitietokannan.

## Vielä puuttuu ennen automaattihinnoittelua

Valmistaja-/pakkausvarmennettu kilpailijasyöte, oikea palvelimelta tehtävä Shopify-lukutesti, tuotantokelpoinen kirjoitusadapteri ja auditointi/palautus, eristetty oikea kirjoitustesti, todennettu sähköpostipalvelu ja toimitustesti, Merchant Center -hinnan päivityksen varmennus sekä käyttäjän lopullinen aktivointilupa. Havaintopilotin julkaisu ei ratkaise näitä eikä aktivoi hinnoittelua.
