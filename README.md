# HKI Group Store – kilpailijahintaseuranta

Avoin lähdekoodirepositorio HKI Group Storen kilpailijahintaseurannalle. **Ei tuotantovalmiina.**

## Turvallinen käyttöönotto
- Ohjelma toimii oletusarvoisesti vain esikatselutilassa.
- Vertailuun hyväksytään vain varmistetut suomalaiset kilpailijatuotteet, joiden koko, väri, pakkaus ja ALV on tarkistettu.
- Hintaehdotus vastaa halvinta hyväksyttyä verollista kilpailijahintaa. Hinnat voivat laskea tai nousta.
- Yli 15 % lasku merkitään sähköpostihälytyksen ehdokkaaksi (info@hkigroup.fi), mutta sähköpostia ei lähetetä tällä esikatselulla.
- Älä lisää tähän julkiseen repositorioon Shopify API -avaimia, sähköpostitunnuksia tai asiakastietoja.
- Julkisten kilpailijasivujen luku edellyttää käyttöehtojen ja robots.txt:n noudattamista sekä hyväksyttyjä tuotemappauksia.

## Käyttö
Python 3.12. Suorita testit: `python -m unittest discover -p "test_*.py"`.

Esikatselu: `python pricing.py verified_competitors.csv --output proposals.json`.

Lähtötiedostossa tulee olla sarakkeet: variant_id,sku,current_price,competitor,competitor_url,competitor_price,verified_same_variant,in_stock,checked_at,product_name.

## Tilanne
Tämä GitHub-julkaisu on vain turvallinen hintalaskennan lähtöversio, ei automaattinen hintojen muuttaja. Kilpailijahintojen automaattinen keruu, Shopify-kirjoitukset, sähköpostilähetykset ja Merchant Center -varmennus vaativat erilliset päästä päähän -testit ennen tuotantoa.
