# GATT-kenttätestit ilman uusia integraatioversioita

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
