# GATT-kenttätestit ilman uusia integraatioversioita

## 0.1.9: kirjoitus aiemmasta saman session lukupuskurista

`write_cached` ottaa puskurin aiemmasta `read`-vaiheesta, jonka nollasta alkava
indeksi annetaan `source_step`-kentässä. UUID:n pitää olla sama. Lähde tarkistetaan
ennen yhteyden avaamista; välimuisti on vain tämän kutsun sisäinen ja sisältää
muuttumattoman kopion alkuperäisestä luvusta. Myöhempi saman UUID:n luku ei korvaa
vanhaa indeksiviitettä. Yhteyden päättyessä välimuisti poistuu.

Vaihe ei lue Bluetoothia uudelleen. Ilman `offset`/`hex`-kenttiä se kirjoittaa
koko alkuperäisen puskurin. Jos haluat muuttaa tavut, anna molemmat kentät;
muut tavut säilyvät. `response` toimii kuten tavallisessa writessä. Vastauksessa
ovat `source_step`, `original_hex` ja `written_hex`, jotka säilytetään yksityisesti.

Alkuluvulle voi antaa `expected_length` ja/tai `expected_hex`. Epätäsmäävä
tulos palautetaan raakana, mutta kaikki seuraavat vaiheet pysähtyvät. Kellon
automaattinen prelude tapahtuu ennen näitä tarkistuksia, ellei `sync_time: false`.
Aseta kaikki tarvittavat vartioidut alkuluvut ennen ensimmäistä kirjoitusta.

```yaml
action: taelek.debug_gatt
data:
  config_entry_id: YOUR_TAELEK_CONFIG_ENTRY_ID
  sync_time: false
  steps:
    - operation: read
      uuid: 2be32db1-5f6b-5bd8-8238-d6dfb1649000
      expected_length: 16
    - operation: write_cached
      uuid: 2be32db1-5f6b-5bd8-8238-d6dfb1649000
      source_step: 0
      offset: 2
      hex: "6400"
      response: true
```

Kirjoitukset suoritetaan edelleen peräkkäin odottaen BLE-kutsujen valmistumista.
Tämä ei jäljittele Androidin rinnakkaista kutsujen käynnistämistä. Ei automaattista
confirmationia, uudelleenyhdistämistä, palautusta tai kirjoitusretryä.

## 0.1.8: kuittauksen odotus samassa yhteydessä

`wait_for_continue` pysäyttää vaihelistan samaan Bluetooth-yhteyteen. Se ei
lähetä mitään kuittausta automaattisesti. Odotus kestää enintään1–180sekuntia
(oletus120); listassa saa olla yksi odotus. Timeout, abort tai integraation purku
sulkee yhteyden. Jo kirjoitettuja asetuksia ei palauteta automaattisesti.

Anna kutsulle uusi UUID `session_id`. Käytä toista Toiminnot-välilehteä
`taelek.debug_gatt_control`-kutsuille: `status`, `continue` tai `abort`. Ne eivät
avaa uutta BLE-yhteyttä eivätkä synkronoi kelloa. `continue` suorittaa vain jo
etukäteen määritellyt jäljellä olevat vaiheet, kerran. Se hyväksytään vain odotuksen
aikana samalla session_id:llä. Väärä tunniste, ennenaikainen tai toistettu kuittaus
hylätään. Käytettyä tunnistetta ei voi käyttää uudelleen saman integraatiolatauksen
aikana. Pollaus ja muut aktiiviset kokeet estetään pidetyn session aikana;
passiivisten mainosten vastaanotto jatkuu.

Kirjoitukseton mekanismin esimerkki (vaihda tunniste uuteen UUID:hen joka kerta):

```yaml
action: taelek.debug_gatt
data:
  config_entry_id: "YOUR_TAELEK_CONFIG_ENTRY_ID"
  session_id: "6d2e7a81-e7f9-4c9f-a1bd-81cd6201bf90"
  sync_time: false
  steps:
    - operation: read
      uuid: 2be32db1-5f6b-4cbd-8843-8d6dfb164900
    - operation: wait_for_continue
      timeout: 120
    - operation: read
      uuid: 2be32db1-5f6b-4cbd-8843-8d6dfb164900
```

Toisessa välilehdessä tarkista ensin `status`. Kun operaattori on nimenomaisesti
kuitannut jatkamisen, muuta operationiksi `continue`; keskeytykseen `abort`:

```yaml
action: taelek.debug_gatt_control
data:
  config_entry_id: "YOUR_TAELEK_CONFIG_ENTRY_ID"
  session_id: "6d2e7a81-e7f9-4c9f-a1bd-81cd6201bf90"
  operation: status
```

Status palauttaa phase-arvon ja odotukseen mennessä kerätyn result-vastauksen.
Continue/abort-vastaus kertoo vain ohjauspyynnön hyväksymisestä; varsinainen
GATT-tulos tulee alkuperäiseen kutsuun ja lopuksi status-kutsuun. Jatko ei
uudelleenyhdistä katkennutta BLE-linkkiä eikä retrytä kirjoituksia. Käyttöliittymän
odotusvirhe ei itsessään todista session päättyneen: tarkista status ennen uusia
operaatioita. Säilytetään vain viimeisimmän pidetyn session tulos, ei pysyvää lokia.

Vaihevastaukset sisältävät UTC `started_at`/`completed_at`-ajat. Write sisältää
`written_hex`; patch myös `original_hex`. Nämä voivat sisältää verkkoavaimia:
ne palautetaan vain kutsujalle, eikä niitä kirjata integraation lokiin. Säilytä
raakavastaukset yksityisesti ja poista tunnisteet/avaimet ennen julkaisemista.

Tämä on testityökalu, ei varmennettu termostaatin tallennus-/ECO-ohjaus.

Versio 0.1.6 lisää HA-toiminnon `taelek.debug_gatt`. Sen jälkeen kokeen
UUID:t, tavut ja vaiheet annetaan toimintokutsussa. Uutta koodia tai painiketta
ei tarvita kutakin koetta varten. Tämä ei ole aktiivisen ECO:n valmis ohjaus.

Versiosta 0.1.7 jokainen aktiivinen sessio lähettää oletuksena kellonajan kerran
ennen pyydettyjä vaiheita. Tämä näkyy vastauksen erillisessä `clock_sync`-kentässä.
Kellovirhe keskeyttää session ilman uusintaa tai piilotettua ohitusta. Debug-kutsun
`sync_time: false` jättää kellokirjoituksen pois A/B-kokeita varten; se ei poista
normaalia taustapollausta. Katso [CLOCK_SYNC.md](CLOCK_SYNC.md).

Päivitä integraatio kerran HACSilla ja käynnistä HA uudelleen. Ota sen asetuksista
käyttöön **GATT-lukemat** ja **raaka GATT-debuggaus**. Debuggaus on oletuksena pois.
Avaa **Kehittäjän työkalut → Toiminnot → YAML**. Valitse oman laitteen Taelek-entry.
Korvaa esimerkkien `YOUR_TAELEK_CONFIG_ENTRY_ID` sen tunnisteella. Tarkat laitetunnisteet
säilytetään paikallisissa muistiinpanoissa, eivät julkisessa dokumentaatiossa.

Pelkkä tilan luku (ei kirjoitusta):

```yaml
action: taelek.debug_gatt
data:
  config_entry_id: "YOUR_TAELEK_CONFIG_ENTRY_ID"
  sync_time: false
  steps:
    - operation: read
      uuid: 2be32db1-5f6b-4cbd-8843-8d6dfb164900
```

Esimerkki erikseen pyydetystä NORMAL-komennosta ja takaisinluvusta:

```yaml
action: taelek.debug_gatt
data:
  config_entry_id: "YOUR_TAELEK_CONFIG_ENTRY_ID"
  steps:
    - operation: read
      uuid: 2be32db1-5f6b-4cbd-8843-8d6dfb164900
    - operation: write
      uuid: 2be32db1-5f6b-5bd8-8a38-d6dfb1649000
      hex: "84"
      response: true
    - operation: delay
      seconds: 1
    - operation: read
      uuid: 2be32db1-5f6b-4cbd-8843-8d6dfb164900
```

`write` hyväksyy minkä tahansa täyden characteristic-UUID:n ja enintään 512 tavun
hex-merkkijonon. Lainaa hex aina YAMLissa: `"84"`, `"83"` tai `"64 00"`.
`response: true` käyttää write-with-responsea; `false` write-without-responsea.
Bluetooth-kuittaus ei osoita komennon semanttista onnistumista.

`patch` lukee kentän ja korvaa vain annetut tavut; se säilyttää muut kentät,
myös pidemmän sanoman loppuosan. Esimerkiksi Param B:n manualEco-tavoitteen
10 °C koe (ei ECO-päällekytkentää eikä tallennuskuittausta):

```yaml
action: taelek.debug_gatt
data:
  config_entry_id: "YOUR_TAELEK_CONFIG_ENTRY_ID"
  steps:
    - operation: read
      uuid: 2be32db1-5f6b-5bd8-8238-d6dfb1649000
    - operation: patch
      uuid: 2be32db1-5f6b-5bd8-8238-d6dfb1649000
      offset: 2
      hex: "64 00"
    - operation: read
      uuid: 2be32db1-5f6b-5bd8-8238-d6dfb1649000
```

Offset lasketaan nollasta. Palautukseen tee erillinen patch alkuperäisillä tavuilla;
19 °C on `"be 00"`, 25 °C `"fa 00"`. Wrapper ei muista tai palauta raakakirjoituksia
automaattisesti. Kokeile vain täsmällisesti määriteltyä muutosta kerrallaan.

Kaikki vaiheet tarkistetaan ennen yhteyden avaamista. Lista suoritetaan samalla
yhteydellä järjestyksessä, samalla lukolla kuin normaali GATT-luku. Yhteys suljetaan
lopuksi myös virheessä. Enintään 32 vaihetta, yksittäinen odotus 0–5 sekuntia ja
yhteensä enintään 20 sekuntia odotuksia; koko yhteyden määräaika on 45 sekuntia.
Ei automaattista kirjoitusta, save confirmationia tai epäonnistuneen kirjoituksen
uusintaa. Tallenna kuittausvaihe listaan vain, kun kokeen tarkoitus on lähettää se.

Vastaus sisältää `success`, `steps` ja virheessä `error_type`, `error`, `retry: none`.
Lukuvaiheen `hex` on lukematon tulkinta eli täsmälleen vastaanotetut tavut.
Kirjoituksen `completed` tarkoittaa BLE-kutsun valmistumista. Jos kirjoitus epäonnistuu,
sen status on `write attempted; effect may be unknown`; seuraavia vaiheita ei tehdä.
Jos takaisinluku epäonnistuu, aiemmat onnistuneet vaiheet pysyvät vastauksessa.
Vaiheiden indeksit alkavat nollasta. Raakatuloksia ei julkaista anturien attribuutteina
eikä kirjoiteta lokiin; Param B:n lukutulos voi sisältää verkkoavaimen.

Automaatiossa vastaanota tulos `response_variable: gatt_result` -kentällä.
Kehittäjän työkaluissa tulos näytetään toimintokutsun vastauksessa. Palvelu vaatii
vastauksen vastaanoton. Integraation purku tai debug-valinnan poistaminen estää kutsut.
Olemassa olevat passiiviset mainosanturit eivät riipu debug-kokeen onnistumisesta.
