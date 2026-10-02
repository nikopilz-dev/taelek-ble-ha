# Taelek BLE – kokeellinen Home Assistant -integraatio

Versio 0.1.2, 2.10.2026. Toteutus perustuu MAI Smart 1.0.17:n JavaScriptiin ja
2.0.3:n purettuun Hermes-bytecodeen. Fyysinen termostaatti on havaittu Bluetooth-
välityslaitteen kautta ja lisätty Home Assistantiin passiivisia mainoslukemia varten.
E-2001 BLE -testilaitteen GATT-luku toimii samassa ympäristössä. Ohjausta ja
lämpötilalukemien tarkkuutta ei ole vielä varmennettu.

## Mitä ensimmäinen versio tekee

- Löytää ehdokaslaitteet valmistajatunnuksella `0x048A` tai `Tael`-nimellä.
  Nimen perusteella hyväksytään vain yksi sopivan mittainen valmistajasanoma.
- Näyttää mainostetun lämpötilan sekä raakatilatavun, virheen ja laitetyypin koodit.
  Tila- ja relekentät jäävät tuntemattomiksi, kun laitteen bittitulkintaa ei ole varmennettu.
  Mainostettu lämpötila on tavallinen lämpötila-anturi; sitä ei nimetä lattialämpötilaksi.
- Säilyttää laitetunnuksen sarjanumeron perusteella; puuttuvalle sarjanumerolle käytetään osoitetta.
- Tarjoaa erikseen sallittavat GATT-lukemat: lattia-, ilma- ja ulkoinen lämpötila,
  asetuslämpötila, anturivirhekoodi sekä lämmitystila.
- Käyttää Home Assistantin Bluetooth-tietoja ja yhteyksiä tukevia välityslaitteita.
  Passiivinen osuus toimii myös ilman GATT-yhteyksiä.
- Ei kirjoita laitteen asetuksia eikä lähetä komentoja. Climate- ja number-entiteettejä ei vielä ole.

GATT on oletuksena pois käytöstä. Kun sen sallii, lukemat päivittyvät viiden minuutin
välein vain käytössä olevien GATT-entiteettien kuunnellessa. Yhteys avataan joka lukua
varten uudelleen ja suljetaan lopuksi. Ilma- ja ulkoisen lämpötilan entiteetit ovat aluksi
poistettu käytöstä. GATT-virhe ei muuta passiivisten anturien saatavuutta.

## Asennus HACSilla

GitHub-repo: [nikopilz-dev/taelek-ble-ha](https://github.com/nikopilz-dev/taelek-ble-ha).

1. Avaa **HACS → ⋮ → Mukautetut tietovarastot / Custom repositories**.
2. Syötä `https://github.com/nikopilz-dev/taelek-ble-ha` ja valitse tyypiksi **Integration**.
3. Etsi **Taelek BLE** ja lataa integraatio. HACS asentaa
   `custom_components/taelek`-kansion ja hallitsee myöhemmät päivitykset.
4. Käynnistä Home Assistant uudelleen ja lisää **Taelek BLE** kohdasta
   **Asetukset → Laitteet ja palvelut → Lisää integraatio**, kun laite on sähköissä
   ja Bluetoothin havaittavissa.

Repoa käytetään omana HACS-tietovarastona; sitä ei ole lisätty HACS-oletusluetteloon.
Ilman GitHub Release -julkaisua HACS asentaa oletushaaran sisällön.
Ks. [HACS: omat tietovarastot](https://www.hacs.dev/docs/faq/custom_repositories/)
ja [integraation rakenne](https://www.hacs.dev/docs/publish/integration/).

## Manuaalinen asennus

1. Pura `dist/taelek-ble-0.1.2.zip` Home Assistantin asetuskansioon.
   Tuloksena pitää olla `<config>/custom_components/taelek/manifest.json`.
   Voit myös kopioida tämän projektin `custom_components/taelek`-kansion samaan paikkaan.
2. Käynnistä Home Assistant uudelleen. Bluetooth-integraation ja käytettävän sovittimen
   tai välityslaitteen on oltava asennettuina.
3. Hyväksy Bluetooth-löytö tai valitse **Asetukset → Laitteet ja palvelut → Lisää integraatio
   → Taelek BLE**. Manuaalinen lisäys käyttää jo havaittujen laitteiden luetteloa.
4. Ota halutessasi integraation asetuksista kokeelliset GATT-lukemat käyttöön.

Versio 0.1.2 on ladattu aidossa Home Assistantissa: Bluetooth-löytö, laitteen lisäys,
passiivinen mainoslämpötila ja GATT-lukemat toimivat. Tila-/relebittejä ja
lämpötilan tarkkuutta ei ole vielä varmennettu.
ZIP on kokeellinen kehitysversio.

### Korjaus versiossa 0.1.1

Integraatio käyttää HA:n Bluetooth-integraation asentamia Bleak- ja
`bleak-retry-connector`-versioita. Erillinen 4.7.1-lukitus esti lataamisen HA:ssa,
jonka pakettirajoitus vaati versiota 4.7.0. Jos lisäys antoi virheen
**Config flow could not be loaded: 500**, lataa uusin oletushaaran versio HACSista
ja käynnistä Home Assistant uudelleen.

### GATT-varmennus versiossa 0.1.2

Mainostettu lämpötila ja GATT-asetuslämpötila ovat nyt tavallisia lämpötila-antureita.
GATT-yhteys välityslaitteen kautta on testattu: lattialämpötilan ja asetuslämpötilan
lukeminen onnistuu. Lattialämpötilan tarkkuutta ei ole vielä vertailtu erilliseen mittariin.
Diagnostiikassa ovat operationMode-raakatila, ECO-ohjelmavalinta, laiteohjelmiston
versiokoodi ja mahdolliset productButtons-tiedot. Refresh GATT -painike päivittää
lukemat pyynnöstä. Valinnaisen lisätiedon lukuvika ei hylkää onnistunutta State A -lukua.

Tavoitteena on käyttöönotto ja ohjaus suoraan HA:n kautta. Testilaite palauttaa
laitetyypin `0x22`, firmware-koodin `54`, toimintatilan `0` ja ECO-ohjelmavalinnan `1`.
Merkkivalo on käyttäjän mukaan punainen. Nämä ovat yhden laitteen havaintoja,
eivät kaikkia saman tyypin laitteita koskevia codec-sääntöjä.

[Taelekin Homey-ohje](https://taelek.fi/Documents/easy_manual_homey.pdf) kuvaa
nupillisen laitteen etäohjauksen ECO-tilan ja ECO-asetuslämpötilan kautta.
Ohje ei sisällä Bluetooth-komennon UUID:tä tai tavuja. `productParamB.ecoMode`
valitsee manuaali-/viikko-ohjelman; sitä ei käytetä aktiivisen ECO:n kytkimenä.
ECO ON/OFF -kirjoitustesti odottaa täsmällistä komentotietoa ja takaisinluvun
varmennusta. MAI Smartia tai muuta ohjaussovellusta ei edellytetä tähän testiin.

`ecoMode` tarkoittaa ohjelmavalintaa (1 = manuaalinen, 2 = viikko-ohjelma), eikä sitä
esitetä aktiivisen ECO-tilan kytkimenä. Taelekin [Homey-ohje](https://taelek.fi/Documents/easy_manual_homey.pdf)
vahvistaa näyttöttömien mallien ECO-tilaan ja ECO-tavoitelämpötilaan perustuvan
etäohjaustavan. Sen tarkkaa GATT-komentoa selvitetään; versio 0.1.2 ei vielä kirjoita.

## Laitteen ominaisuudet ja epäselvät tulkinnat

Sovellusversio ei määritä laitteen wire-formaattia. Protokollaprofiilin valinta on poistettu
käyttöliittymästä ja vanha tallennettu valinta poistetaan integraation latauksessa.
Mainossanoman bittitulkinta ja GATT-lattialämpötilan etumerkillisyys ovat kirjastossa
erillisiä capability-ominaisuuksia. `capabilities_for_device` on automaattisen valinnan
laajennuskohta myöhemmin varmennetuille laitetyyppi- ja firmware-säännöille.

Hermes-koodi ei osoita erillistä vanhojen ja uusien termostaattien haaraa näille
kahdelle ominaisuudelle. Siksi mitään termostaattityyppiä, myöskään tuntematonta
E-2001-ehdokasta, ei nyt automaattisesti sidota kumpaankaan epävarmaan tulkintaan.

| Kenttä | Aineistossa havaitut tulkinnat | Integraation nykyinen toiminta |
|---|---|---|
| Mainoksen tila | high nibble tai bitit 4–6 | Tuntematon; raakatavu näkyy |
| Mainoksen rele | bitit 0–1 tai bitti 7 | Tuntematon; raakatavu näkyy |
| GATT-lattialämpötila | uint16 LE tai int16 LE / 10 | Arvo vain, jos tulkinnat yhtyvät eli raw < 0x8000 |
| Lämpötilan raw FFFF | Mahdollinen puuttuva anturi | Tuntematon ennen etumerkkimuunnosta |

Raaka GATT-sanoma säilytetään `StateA.raw_data`-kentässä. `FFFF` ei koskaan muutu
validiksi −0,1 °C lukemaksi, myöskään signed-codecin erillisissä testeissä.
Puuttuvan anturin tarkkaa merkitystä ei silti väitetä laitteella varmennetuksi.
GATT-antureiden −50…100 °C suodatin on vain ylimääräinen uskottavuustarkistus.

Tunnetut ECO_PLUG-, 3phase- ja MSC-laitteet hylätään Bluetooth-löydössä ja jätetään pois
manuaalisesta valintalistasta. Niille ei avata termostaatin GATT-yhteyttä. Tuntemattomat
tyypit sallitaan `BASE/UNKNOWN`-ehdokkaina tulevaa laitetestausta varten.
Nimimatcher on HA:n sääntöjen mukainen `Tael*`; valmistajatunnusmatcher säilyy rinnalla.

## Kehitys ja testit

`src/taelek_ble` on itsenäinen, ilman BLE-riippuvuuksia käytettävä kirjasto.
Integraation sisäinen `taelek_ble` on sama kirjasto kopioituna, koska pakettia ei ole
julkaistu pakettirekisteriin. Muokkaa kirjaston lähdettä `src`-kansiossa ja päivitä kopio:

```text
python tools/vendor_library.py
python -m pytest tests -q
ruff check src custom_components tools tests tests_ha
python tools/package_integration.py
```

Tarvitaan Python 3.12 tai uudempi. Testiriippuvuudet saa komennolla `pip install -e .[dev]`.
Paikallinen Windows-ympäristö on `.venv`-kansiossa.

GitHub Actions ajaa yksikkötestit, lint- ja muotoilutarkistukset sekä rakentaa
asennus-ZIPin ladattavaksi työnkulun artefaktina. Se ei vielä aja `tests_ha`-testejä
oikeassa Home Assistantissa. Virtuaaliympäristö, APK:t, kokonaiset purkutulokset
ja ladatut analyysityökalut on rajattu Gitin ulkopuolelle.

Paikalliset testit kattavat protokollan, lyhyet sanomat, erilliset havaitut wire-tulkinnat,
varattujen tavujen säilymisen, yhteyksien sulkemisen myös virheessä ja peruutuksessa,
löydön ja kaksoislöydön käsittelyn sekä integraation callback- ja entiteettilogiikan.
HA-rajapinnat korvataan Windows-yksikkötesteissä testikaksoisilla. Tämä ei varmista
Home Assistantin lataajaa, tapahtumasilmukkaa tai entiteettirekisteriä.

`tests_ha` sisältää erilliset oikean Home Assistantin config-flow-testit. Niitä ei
ole ajettu tässä ympäristössä. Aja ne Linuxissa Home Assistantin tukemalla Pythonilla:

```text
pip install pytest-homeassistant-custom-component
python -m pytest tests_ha -q
```

## Seuraava varmennus

1. Aja oikean Home Assistantin testit ja tarkista asennus, optioiden muuttaminen sekä purku.
2. Kun laite kytketään sähköihin, tallenna mainoksen valmistajatunnus, nimi, raakasanoma ja GATT-UUID:t.
3. Varmenna raakasanomasta tila- ja relebitit sekä GATT-lattialämpötilan etumerkillisyys.
   Lisää tämän perusteella itsenäiset capability-säännöt; älä päättele niitä appiversiosta.
4. Selvitä puuttuvien anturien arvot, laitteen versio ja välityslaitteen GATT-toiminta.
5. Lisää asetusmuutokset vasta laitteella varmennetun read-modify-write-, kuittaus- ja
   takaisinlukumenettelyn jälkeen.

Purkutulokset ja poikkeamat alkuperäisestä protokollakuvauksesta löytyvät
`protocol/V2_VALIDATION.md`-tiedostosta. Alkuperäisiä lähtöaineistoja ei ole muokattu.
Home Assistant -rajapinnat tarkistettiin [Bluetooth-ohjeista](https://developers.home-assistant.io/docs/bluetooth/),
[Bluetooth API -ohjeista](https://developers.home-assistant.io/docs/core/bluetooth/api/)
ja [core-lähdekoodista](https://github.com/home-assistant/core).
