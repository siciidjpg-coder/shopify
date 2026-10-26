# HKI Group Store – kilpailijahintaseuranta

**Tila: kehitys-/esikatseluversio. EI automaattista tuotantohinnoittelua.**

**Nykyinen käyttöpäätös:** kehitys ja testaus tehdään paikallisesti ilman maksullisia palveluita. Render-julkaisu on peruttu; palvelua ei luotu. `render.yaml` on vain käyttämätön vaihtoehtoinen määritys, eikä sitä pidä ottaa käyttöön ilman uutta lupaa.

`comparison.py` tarkistaa valmistajan viitetunnisteita ja estää vertailun hyväksymisen, jos lähteitä puuttuu, havainto on vanhentunut tai variantti/verollinen hinta on varmentamatta. Viivakoodin korjaustarve raportoidaan ehdokkaana; kaupan koodeja ei muuteta. 46 paikallista testiä läpäisty. Paikallinen testaus ei edellytä Renderiä, sähköpostipalvelua tai Shopify-kirjoituksia.

Uusin testattu havaintopilotti ja sen rajat: [PILOT_STATUS.md](PILOT_STATUS.md).
Kilpailijahavaintojen keruu: `python monitor.py`. Tämä lukee kaksi hyväksytyn host-listan tuotesivua, tarkistaa robots.txt:n ja tallentaa havainnot `output/observations.json`-tiedostoon. Tuloksia ei syötetä automaattisesti hinnankirjoitukseen. Valinnainen `--catalog /polku/shopify-sample.json` etsii SKU-ehdokkaat aiemmasta Shopify-otoksesta; otoksen hinnat eivät ole reaaliaikainen varmennus.

Kauppa: https://hkigroupstore.fi

## Toteutetut osat
- `pricing.py`: valitsee halvimman vahvistetun kilpailijahinnan, tekee hinnankorotus- ja alennusehdotukset sekä merkitsee yli 15 %:n laskut.
- Tiukat hyväksyntäsäännöt: hyväksytty kilpailijaverkkotunnus, vahvistettu sama variantti, varastossa oleva tuote, verollinen EUR-hinta ja enintään 2 tuntia vanha havainto.
- `shopify_read.py`: lukee variantin Shopify Admin API:sta ympäristömuuttujien avulla (ilman kirjoitusoikeuksia).
- `shopify_preview.py`: varmistaa Shopifyn nykyisen SKU:n, hinnan ja verollisuuden ennen ehdotuksen hyväksymistä.
- `shopify_auth.py`: lukuyhteys käyttää automaattisesti uusiutuvaa client credentials -tokenia, kun sovelluksen ympäristömuuttujat on asetettu. Kiinteä token on edelleen vaihtoehto vanhoille asennuksille. Tunnistusvirhe ei vaihda automaattisesti toiseen tunnukseen.
- `identity.py`: GTIN-pituuden ja tarkistusnumeron validointi, näkymättömien SKU-merkkien hylkäys sekä tiukka varianttivertailu. GTIN-arvon `.0`-päätettä ei poisteta automaattisesti. Varianttivertailun kytkentä keruuseen odottaa oikeaa tietolähdettä.
- Yksikkötestit ja GitHub Actions -määritys: testit noin kuuden tunnin välein. GitHubin ajojen onnistumista ei ole vielä vahvistettu.

## Ei vielä toteutettu tai varmennettu
- Suomen kilpailijatuotteiden laajamittainen automaattinen löytö ja koko-/väri-/pakkaustäsmäytys.
- Tuoreiden ja käyttöehtojen mukaisesti kerättyjen hintahavaintojen tuotantosyöte.
- Shopify Admin API:n erillinen palvelintunnus, tuotantokirjoitukset, auditointi ja palautus.
- Sähköpostipalvelun käyttö ja toimituksen vahvistaminen osoitteeseen info@hkigroup.fi.
- Google Merchant Centerin tuotefeedin tarkistus sekä päästä päähän -testit.
- Pysyvä 15 minuutin ajastus hintojen keruulle ja kirjoittamiselle.

## Käyttö
Python 3.12. Testit: `python -m unittest discover -p 'test_*.py'`.

Palvelinkäytössä aseta salaisuushallinnassa `SHOPIFY_SHOP_DOMAIN`, `SHOPIFY_CLIENT_ID` ja `SHOPIFY_CLIENT_SECRET`. Tällöin `SHOPIFY_ADMIN_TOKEN` ei ole tarpeen. Älä syötä salaisuuksia komentoriville. Tokenin uusiminen, lukuyhteyden kytkentä ja tunnisteiden virhetapaukset on testattu simuloiduilla vastauksilla; tämän koodiversion palvelimelta tehtävää oikeaa lukutestiä ei vielä ole varmennettu.

Read-only laskenta:
`python pricing.py verified_competitors.csv --allowed-domain esimerkkikilpailija.fi --output proposals.json`

Read-only Shopify-esikatselu:
`SHOPIFY_SHOP_DOMAIN=OMA-KAUPPA.myshopify.com SHOPIFY_ADMIN_TOKEN=... python shopify_preview.py verified_competitors.csv --allowed-domain esimerkkikilpailija.fi`

Älä laita tokenia komennon historiaan tai julkiseen repositorioon: käytä salattuja ympäristömuuttujia. `verified_competitors.csv` tarvitsee sarakkeet: variant_id,sku,current_price,competitor,competitor_url,competitor_price,verified_same_variant,verified_vat_included,currency,in_stock,checked_at,product_name.

**Huomio:** Koodi ei vielä itsessään varmista tuotteen EAN-/GTIN-täsmäävyyttä eikä suomalaisuutta. `verified_same_variant` ja hyväksyttyjen verkkotunnusten lista ovat erillisen luotettavan tarkistusprosessin vastuulla. Niitä ei pidä automaattisesti asettaa arvoon true pelkän nimen tai verkkotunnuksen perusteella.

## Julkaisuportit
1. Toimiva ja sallittu kilpailijahintojen tuotantosyöte sekä todistetusti täsmäävät variantit.
2. Shopify Admin API -tunnuksen turvallinen asetushallinta ja lukutesti.
3. Hintakirjoitusten, rollbackin, auditoinnin ja sähköpostin turvallinen testaaminen.
4. Merchant Center -synkronoinnin varmistus.
5. Erillinen käyttäjän hyväksyntä ennen oikeita automaattisia hintamuutoksia tai maksullisia palveluita.

Ei säilytetä API-avaimia, salasanoja, tilausdataa tai asiakastietoja tässä julkisessa repositoriossa.
