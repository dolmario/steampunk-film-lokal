# Öffentlicher Download: tatsächlicher GPU-Vollauf vom 10.10.2026

Testcommit: `69f60db697c5b4930192c2b0d917621082cb88b7`.
Download-ZIP SHA256: `15c8a7fe52ef6e57396486b64624492c957fe43eff4ed02af5582e8dbdfb1a95`.
Der frisch heruntergeladene ZIP enthielt 28 Textdateien. Vor und nach dem Lauf wurden alle Dateihashes gegen den veröffentlichten Stand geprüft. Getesteter Code unverändert, neues leeres Ausgabeverzeichnis, keine Mediencache-Übernahme.

## Umgebung und Aufruf

GMKtec EVO-X2, AMD Strix Halo / Ryzen AI Max+ 395, Radeon 8060S. Bestehende ComfyUI-Installation 0.38.0, PyTorch 2.9.1+rocm7.2.1, vorhandene Modellgewichte. FLUX.2-klein-4B-FP8 und LTX-2.5 mit int8-Transformer.
Aufruf: `python runner/selbstlaeufer.py --geraet evo-fresh-public-20261010 --comfyui <vorhandenes-ComfyUI> --modell klein4 --seed 11`.
Vor Start wurden bestehende lokale Modell-/Medienprozesse, Listener, Locks, Queues und GPU-Aktivität geprüft. Während der Produktion lief keine konkurrierende von uns gestartete Modellarbeit. Der Runner startete sein eigenes ComfyUI auf dem lokalen Port8189 und beendete nur seinen eigenen Prozessbaum.

## Ergebnis

- 6 neue Figurenreferenzen, 36 neue Standbilder, 36 gültige Clips und Rohschnitt; Runner Exitcode0.
- 36 Clip-Versuche; 0 Wiederholungsversuche.
- Mittlere erfolgreiche Clipzeit 430.0s; Minimum 381.9s, Maximum 447.4s.
- Summe der erfolgreichen Clipzeiten: 4 h 18 min 1 s.
- Gesamte gemessene Wandzeit einschließlich Figuren, Bilder, Modellstarts, Prüfungen und Rohschnitt: 4 h 49 min 46 s.
- Höchster gemeldeter GPU-Speicherwert: 44501MiB; niedrigster gemeldeter freier RAM-Wert während der Clips: 3MiB. Diese beobachteten Werte sind keine Zusicherung für andere Speicherkonfigurationen.
- Jeder Clip: 121 Bilder bei24fps. Rohschnitt: 181.458s,1920×1080,24fps,ohneTon.
- Rohschnitt SHA256: `17ad10f95b97eb20b01f5bc8fa7c3259b79a36a376d84f9327d90b11ff543bec`.
- Vollständiger Clip-Decode im öffentlichen Runner, Clip-/Startbild-SHA-Bindungen, Prüfung von drei Bildern pro Clip und separater vollständiger Rohschnitt-Decode bestanden.
- Der spätere Dokumentationscommit verändert keine generierenden Python-Skripte, Story oder Workflow-Vorlagen des Testcommits.

Originalmessung: [evo-fresh-public-20261010.jsonl](messung/beispiele/evo-fresh-public-20261010.jsonl). Die ältere [Drei-Rechner-Messung](messung/beispiele/drei-rechner.csv) bleibt separat und unverändert.

## Was dieser Test belegt und welche Grenzen bleiben

Belegt ist der vollständige Durchlauf des frischen öffentlichen Code-Downloads auf der vorhandenen EVO-X2-Installation. Eine Neuinstallation, ein identischer Test auf anderen Karten, eine menschliche kontinuierliche Sichtung oder perfektes Aussehen aller Figuren sind damit nicht belegt.
Der Runner prüft technisch gültige Videos und die Startbildnähe; er bewertet keine perfekte Anatomie, Gesichtsdetails oder Kostümkontinuität. Sichtbare Modellartefakte können bestehen. Die drei Stichprobenbilder sind keine Prüfung sämtlicher Frames. Der Rohschnitt skaliert auf16:9; Finalfilme können eine andere Bildrate verwenden.
Die zusätzliche fertige Musikfilmfassung nutzt ältere Bestauswahl und gezielt erzeugte neue Bildvorlagen. Sie ist vom ungeänderten Standard-Rohschnitt dieses Tests getrennt. Modellgewichte, private Stimmen, Bandfreigaben und lokale Zugangstokens sind nicht Bestandteil dieses Repos.

## Tatsächlich vorgenommene Bildsichtung

Codex hat drei Kontaktbögen mit allen36 Clip-Mittelpunkten und die Originalgröße der Frames04,09 und36 angesehen. Die Stichprobe enthält keine leeren Bilder oder graues Rauschen, aber sichtbare Modell-/Storyfehler: Stoff im Präriebild02, Brokat/Spitze an der Maschine04, Stirn-/Wangenpunkte bei Mira, wechselnde Accessoires, noch leuchtende Augen in30 und eine kleine Maschine auf einem stoffbedeckten Dach in36. Acht korrekte Beine und vollständige Kostüm-/Handlungsstabilität sind damit nicht nachgewiesen. Es wurde weder jedes Einzelbild noch der ganze Film kontinuierlich menschlich abgenommen.

Das technische Bestehen des Standardlaufs und die gezielt verbesserte Musikfilmfassung sind getrennte Ergebnisse. Die bessere bisherige Auswahl wird durch diesen Standardtest nicht automatisch ersetzt.

## English summary

The public ZIP at commit `69f60db697c5b4930192c2b0d917621082cb88b7` completed an actual GPU run on the existing EVO-X2 installation:6 character references,36 new stills,36 valid clips,and a rough cut. Generating code and input definitions were unchanged;previous media outputs were not reused. Fresh installation and perfect visual continuity are not claimed. The new documentation commit changes only docs and adds the measured evidence.
