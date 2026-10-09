# Authentifizierung und Anfrageablauf

Stand: geprüfter Zuschauerquellstand vom 09.10.2026. Dieses Repository enthält einen lokalen Python-ComfyUI-Client und implementiert keine Benutzeranmeldung, Passwortdatenbank, Rollen, Sessions, OAuth-, JWT- oder API-Key-Verwaltung. Die separate ComfyUI-Installation und deren Erweiterungen sind nicht Teil dieser Codeprüfung.

## Komponenten

- `START-SELBSTLAEUFER.cmd`: liest ComfyUI-Pfade und die Modell-/Geräteauswahl aus Umgebungsvariablen. Dies sind Konfigurationswerte, keine Zugangsdaten.
- `runner/selbstlaeufer.py`: stellt eine URL `http://127.0.0.1:<port>` zusammen und verweigert einen bereits belegten Port.
- `runner/clips_einzeln.py`: startet eigenes ComfyUI mit `--listen 127.0.0.1`. Unter Windows prüft es die Prozessbaumzugehörigkeit des Portbesitzers. Dies ist lokale Prozesskontrolle, keine Authentifizierung eines API-Benutzers. Auf anderen Betriebssystemen entfällt diese Windows-Prüfung.
- `runner/lib.py`: HTTP-Anfragen und Dateiübertragung mittels `urllib.request`.

## Anfrageablauf

1. Start und Bereitschaftsprüfung: `GET /system_stats`.
2. Referenz- oder Startbild: `POST /upload/image`, multipart mit Bilddatei und `overwrite=true`.
3. Workflow starten: `POST /prompt` mit JSON `{"prompt": graph}`.
4. Zurückgegebene `prompt_id` verwenden, um `GET /history/<prompt_id>` bis zum Abschluss abzufragen.
5. Ausgabedateien mit `GET /view?filename=...&type=...&subfolder=...` herunterladen.
6. Bei entsprechendem Aufruf: `POST /free` für Cache-/Modellspeicherfreigabe.

## Zugangsdaten, Tokens und andere Kennungen

Der Client setzt Content-Type-Header, aber keine Authorization-Header, Bearer-Tokens oder Login-Cookies. Er speichert oder erneuert keine Anmeldetokens und verwaltet keine Logout-/Widerrufslogik. Ein automatisch erzeugter UUID-Wert dient ausschließlich als multipart-Grenze. Die `prompt_id` ist eine Auftragskennung, kein im Client geprüftes Zugriffstoken. SHA256-Werte in Bild-/Clipmetadaten dienen der Erkennung geänderter Eingaben und Ergebnisse, nicht der Passwortspeicherung oder Authentifizierung.

Der Standardstart bindet ComfyUI an die lokale Loopback-Adresse; andere lokale Programme können den Endpunkt grundsätzlich ebenfalls ansprechen. Einzelne Schrittskripte akzeptieren eine frei angegebene `--server`-URL; der Client prüft diese nicht auf Loopback und fügt auch dann keine Authentifizierung hinzu. Dieses Paket stellt keine abgesicherte öffentliche Web-API bereit. Modellgewichte müssen separat aus den Originalquellen bezogen werden; ein eventuell dort benötigtes Konto oder Downloadtoken wird vom Runner nicht verarbeitet.

Codebelege: `runner/lib.py` (HTTP-Helfer), `runner/clips_einzeln.py` (Bindung und Portbesitzerprüfung), `runner/selbstlaeufer.py` (Start und Weitergabe der lokalen URL), `START-SELBSTLAEUFER.cmd` (Konfiguration).
