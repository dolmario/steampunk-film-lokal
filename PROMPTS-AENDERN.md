# Eigene Figuren und Szenen: nur Prompts ändern

Der Film entsteht aus zwei Textdateien. Alles andere rechnet `START-SELBSTLAEUFER.cmd` selbst.

- `story\figuren.json`: Stil (`stil`), Ort (`ort`) und je Figur Gesicht, Körper, Kleidung und Erkennungsmerkmale. Der Text jeder Figur steht wörtlich in jedem Bild-Prompt, das hält die Person über alle Einstellungen gleich.
- `story\shots.json`: je Einstellung `bild` (was im Standbild zu sehen ist), `bewegung` (was sich im 5-Sekunden-Clip bewegt) und `figuren` (welche Figuren im Bild stehen).

Ablauf bei jedem Start: Figurenreferenzen, Standbilder, Clips, Rohschnitt `film_roh.mp4`. Neben jedem Bild und Clip liegt eine `.json`-Datei mit einem Hash des Prompts. Ändert sich ein Text, rechnet der nächste Start nur die betroffenen Teile neu; die alten Dateien wandern in einen Unterordner `alt_ersetzt\` (bei Clips unter `clips\`, bei Standbildern unter `bilder\standbilder\`) oder bei Figurenreferenzen nach `bilder\figuren\<name>\alt_<Zeit>\`.

- `bewegung` einer Einstellung geändert: nur ihr Clip (getestet; das Standbild bleibt).
- `bild` oder `figuren` einer Einstellung geändert: ihr Standbild und danach ihr Clip (so gebaut, einzeln nicht durchgespielt).
- Text einer Figur geändert: die Referenzen der Figur, alle Standbilder mit ihr und deren Clips (getestet am Beispiel Haar bei Mira: neue Referenzen, 12 Standbilder, danach Clip für Clip).
- Stil geändert: alles.
- Bildmodell gewechselt (`set MODELL=dev` oder zurück): alle Figurenreferenzen und Standbilder, danach alle Clips.

Tipps: Bewegung ruhig halten (fester Blick, keine schnellen Kopfdrehungen, kein Laufen, keine Handarbeit), sonst entstehen Artefakte. Leuchten im Prompt kann Augen zum Leuchten bringen; Licht lieber als "light on her cheek" beschreiben. Ein Clip dauert je nach Grafikkarte 1 bis 8 Minuten.

Nur einen Teil rechnen: `python runner\clips_einzeln.py --geraet <name> --comfyui <ComfyUI-Ordner> --shots 27 --neu` (Clip neu) und `python runner\schritt2_standbilder.py --geraet <name> --shots 27 --neu` (Standbild neu, ComfyUI muss laufen).

Hinweis: ComfyUI muss mit `--disable-pinned-memory` laufen, sonst liefert LTX-2.5 graues Rauschen oder bricht ab. Der Selbstläufer startet es selbst so, je Clip frisch.

Der Film ist stumm. Sprecherin, Musik und Effekte kommen im Schnittprogramm dazu.
