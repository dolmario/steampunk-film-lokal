"""Erzeugt shots.json: 36 Einstellungen, 5 Akte.

Bewegungsregeln für die Modelle: Personen stehen, sitzen oder lehnen; Handlung wird über Kamera, Maschinen,
Licht und Schnitt erzählt. Kein Laufen, Treppensteigen, Hämmern oder Handarbeit in Nahaufnahme.
Die Gefahr ist eine riesige Dampf-Spinne aus Messing (eigene Konstruktion, leichte Frontier-Anmutung).
"""
import json
from pathlib import Path

S = []


def s(akt, titel, fig, bild, bew, text=""):
    S.append({"id": len(S) + 1, "akt": akt, "titel": titel, "figuren": fig, "bild": bild,
              "bewegung": bew, "weiter": False, "sprechertext": text})


SPINNE = ("an enormous eight-legged steam-powered brass automaton with a bulbous riveted boiler body, glowing amber lens eyes "
          "and a wide copper smokestack on its back")

# Akt 1: Vorspann, die Gefahr
s(1, "Messingbrunn im Morgenlicht", [], "wide view of the steampunk frontier town of Messingbrunn at dawn, copper rooftops, brass towers, wooden boardwalks, thin steam rising, a dusty prairie behind the town wall", "slow aerial push-in over the rooftops, steam curling upward, warm sunrise light, a distant bell chime and soft wind", "Messingbrunn, die Stadt aus Messing und Dampf.")
s(1, "Staub am Horizont", [], "wide view across a dusty prairie at dawn, a huge cloud of dust and steam on the horizon, long shadows, low golden sun", "slow push-in on the horizon, the dust cloud rolls closer, a low distant rumble", "Doch an diesem Morgen bebt der Boden.")
s(1, "Die Silhouette", [], f"far away on a ridge the silhouette of {SPINNE}, backlit by the sunrise, steam rising from its smokestack", "very slow zoom-in, steam drifts, the huge silhouette stands still, deep rumbling", "Ein Kriegsautomat ist erwacht.")
s(1, "Glühende Augen", [], f"close view of the glowing amber lens eyes and riveted brass head of {SPINNE}, steam venting from its joints", "slow push-in, the amber eyes pulse, steam vents, a low mechanical growl", "Eine Spinne aus Messing, so hoch wie ein Turm.")
s(1, "Die Stadt schaut hin", [], "townsfolk in wide-brimmed hats standing still on a wooden boardwalk, staring toward the horizon in silence, dust in the air", "static shot, dust and a hat brim flutter in the wind, distant rumbling, a bell rings once", "Die Stadt hält den Atem an.")
s(1, "Die Spinne kommt näher", [], f"wide establishing shot over the town wall, {SPINNE} larger on the horizon marching toward Messingbrunn, golden sky, empty sky in the upper third", "slow gentle push-in, dust rises from the horizon, rumbling grows", "")

# Akt 2: Der Auftrag
s(2, "Der Ratssaal", ["elara", "mira"], "the two sisters stand side by side in a vaulted council hall with brass chandeliers and tall arched windows, serious expressions, medium wide shot", "slow dolly-in on the sisters, chandelier light flickers, the sisters stand still and look forward, murmuring crowd and echo", "Der Bürgermeister ruft die beiden Schwestern.")
s(2, "Der Auftrag", ["elara"], "medium close-up of Elara listening gravely, a rolled blueprint held out toward her from the edge of the frame, council hall behind her", "she holds a steady serious gaze, a lock of hair moves slightly, steady medium close-up, quiet room tone", "Elara und Mira sollen die Stadt retten.")
s(2, "Mira lächelt", ["mira"], "medium close-up of Mira with a confident half smile, council hall blurred behind her", "she keeps a steady confident gaze with a small smile, only her hair moves slightly, steady camera, soft room tone")
s(2, "Der Balkon", ["elara", "mira"], "the sisters stand side by side at a balcony railing seen from slightly behind and aside, looking out at the distant dust cloud, wind in their hair, warm light", "slow orbit around the sisters, wind moves their hair and lace, they stand still, distant rumbling", "Keine Zeit zu verlieren.")

# Akt 3: Die Erfindung in der Werkstatt
s(3, "Die Werkstatt", ["elara", "mira"], "cluttered Victorian inventor workshop with brass gears, workbenches, hanging Edison bulbs and a glowing forge, both sisters standing at a table with blueprints, wide shot", "slow lateral dolly, sparks drift up from the forge, bulbs sway slightly, the sisters stand still looking at the table, warm crackle", "In der Werkstatt beginnt die Arbeit.")
s(3, "Elara entwirft", ["elara"], "medium close-up of Elara leaning on a drafting table with a pencil resting on a blueprint of a brass coil, goggles pushed up in her hair, warm lamp light", "she looks down at the blueprint with a steady gaze, small breathing movement, dust motes in the lamp light, quiet scratching sounds")
s(3, "Mira am Feuer", ["mira"], "medium shot of Mira standing beside a glowing forge with her arms at her sides, forge glow on her face", "the forge glow flickers on her face, she stands still with a steady gaze, her hair moves slightly, crackling fire")
s(3, "Schutzbrille", ["elara"], "close-up of Elara with her brass goggles resting on her forehead, determined steady gaze at the camera, warm rim light", "she holds a steady gaze, a tiny breathing movement, warm light flickers softly, quiet workshop sounds")
s(3, "Der Entwurf", [], "close-up of a blueprint of a brass coil on a workbench, scattered brass parts, a pencil and a compass, warm lamp light", "slow dolly along the blueprint, dust motes drift, a small gear on the table slowly turns, soft ticking")
s(3, "Die Spule", [], "a brass Tesla-style aether coil with a glowing blue crystal core on the workbench, thin blue sparks arcing between copper rings", "slow orbit around the coil, blue arcs crackle between the rings, the glow pulses, rising electric hum")
s(3, "Das Gespräch", ["elara", "mira"], "medium two-shot of the sisters standing close and talking calmly about the plan, workshop behind them", "they stand still and look at each other with calm expressions, tiny head movements, steady two-shot, warm room tone")
s(3, "Der Kristall", [], "close-up of a glowing blue aether crystal sitting in a brass housing, light spilling over cream lace on the table", "the crystal glow pulses brighter, soft rising hum, reflections shimmer on brass")
s(3, "Mira, stolz", ["mira"], "portrait of Mira leaning back against a workbench with her arms crossed, proud steady gaze, forge glow behind her", "slow push-in, she holds a steady gaze, her hair moves slightly in a warm draft, forge crackle")
s(3, "Die Waffe ist fertig", [], "the finished aether coil mounted on a brass steam wagon, glowing blue crystal core, polished copper rings, soft steam, hero shot", "slow orbit around the machine, the crystal glows steadily, steam wisps, a gentle electric hum")
s(3, "Gemeinsam", ["elara", "mira"], "medium two-shot of the sisters standing shoulder to shoulder with proud looks, warm workshop light", "they stand still with proud confident expressions, a tiny head movement, steady two-shot, warm room tone")
s(3, "Elara, Heldin", ["elara"], "heroic portrait of Elara leaning on the workshop doorframe, golden backlight, brocade and lace catching the light, calm confident gaze", "slow push-in, her hair and lace lift slightly in a warm draft, golden dust motes drift")

# Akt 4: Die Rettung
s(4, "Der Dampfwagen", [], "the brass steam wagon carrying the glowing aether coil rolling along a wooden boardwalk street, townsfolk in wide-brimmed hats stepping aside, golden morning light", "tracking shot alongside the wagon, steam puffs from the chimney, the wheels turn, crowd noise and a steam whistle", "Jetzt zählt jede Minute.")
s(4, "Auf dem Kutschbock", ["elara", "mira"], "the sisters sit side by side on the driver's bench of the steam wagon, looking ahead with determined faces, the aether coil glowing behind them", "the wagon rolls on, the sisters sit still looking ahead, wind in their hair, steady medium shot, steam hiss")
s(4, "Am Stadttor", [], f"wide view from the town wall, {SPINNE} towering over the prairie just outside the gate, dust and steam, low golden sun", "slow push-in, the machine's legs move slowly in the distance, dust rises, a deep metallic rumble")
s(4, "Der Stampfer", [], f"low-angle view of a huge brass leg of {SPINNE} slowly stepping down into the dust of the main street, wooden planks splintering, dust cloud", "slow low-angle shot, the huge leg lowers into the dust, a dust cloud billows, a deep thud, planks creak")
s(4, "Elara an der Spule", ["elara"], "medium close-up of Elara standing at the aether coil control panel with brass levers, blue glow on her face, determined steady gaze", "the blue glow pulses on her face, she keeps a steady gaze, her hair lifts slightly, rising electric hum")
s(4, "Der Blitz", [], f"a thick blue lightning arc leaps from the copper rings of the aether coil to the brass body of {SPINNE}, blue light flooding the street", "the arc crackles and strikes the machine, blue light flashes across the street, loud electric crackle, steam bursts")
s(4, "Die Spinne erstarrt", [], f"{SPINNE} frozen mid-step, its amber lens eyes flickering and going dark, blue sparks running over its brass body", "the amber eyes flicker and fade, sparks crawl over the metal, the machine stands motionless, the rumble dies away")
s(4, "Dampf entweicht", [], f"{SPINNE} sinking slowly to rest, venting long plumes of harmless white steam into the morning sky, calm light", "the machine settles slowly, long white plumes of steam rise, calm rumble, bells begin to ring", "Die Stadt ist gerettet.")

# Akt 5: Freude
s(5, "Die Menge jubelt", [], "the town square full of cheering townspeople in wide-brimmed hats, hats thrown into the air, golden light, joyful atmosphere", "camera glides over the cheering crowd, hats fly up, cheering and applause")
s(5, "Dank", ["elara", "mira"], "the sisters stand on the town hall steps while the mayor in a frock coat tips his hat toward them, crowd behind, warm light", "the mayor tips his hat, the sisters smile with relief and stay still, applause rising", "Messingbrunn dankt seinen Heldinnen.")
s(5, "Abendlicht", ["elara", "mira"], "the sisters stand at the railing of an airship deck at sunset, golden light, the town and airships below, relaxed proud expressions", "slow orbit around the sisters, hair and lace moving in the breeze, they stand still, wind and distant bells")
s(5, "Schwestern", ["elara", "mira"], "the sisters stand shoulder to shoulder smiling warmly on the airship deck, golden backlight", "they stand still smiling, soft golden light, wind in their hair, steady two-shot")
s(5, "Feuerwerk", [], "night sky over Messingbrunn with fireworks above the brass towers, airships glowing with lanterns, reflections in the canal", "fireworks burst over the skyline, airships drift past, distant cheers")
s(5, "Ende", [], "wide final shot of Messingbrunn at dusk, calm steam over the rooftops, the dormant brass spider silhouette resting on the ridge, airships on the horizon", "slow pull-back, the town lights twinkle, a gentle bell chime and soft wind", "Ende.")

ziel = Path(__file__).with_name("shots.json")
ziel.write_text(json.dumps({"titel": "Die Schwestern von Messingbrunn", "shots": S}, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(S), "Einstellungen")
