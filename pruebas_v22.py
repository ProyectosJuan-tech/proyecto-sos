"""
PRUEBA REAL V2.2 — dos producciones extremo a extremo con render real.

  A: SHORT 9:16 · tema "superar el perfeccionismo" · fe+psicología · YouTube ·
     entendido por el sistema (plataforma dada, CTA auto del engine).
  B: VIDEO 16:9 · tema distinto ("poner límites sin sentir culpa") · YouTube ·
     comportamiento storytelling largo, CTA auto del engine.

System-driven: no se pasan escenas manuales, ni imágenes manuales, ni CTA manual.
Solo tema + idea (+ plataforma/tipo). El resto lo decide la capa V2.2.
"""

import json
import os

import production_intelligence as pi

OUT = "pruebas_v22"
os.makedirs(OUT, exist_ok=True)

PRODUCTIONS = [
    {
        "name": "A_short_perfeccionismo",
        "tema": "superar el perfeccionismo",
        "idea": ("Dejar de perseguir una perfección imposible y aprender a soltar "
                 "sin culpa; para quien cree, Dios no exige una versión perfecta "
                 "de ti para amarte."),
        "plataforma": "youtube",
        "tipo": "short",
    },
    {
        "name": "B_video_limites",
        "tema": "poner límites sin sentir culpa",
        "idea": ("Aprender a decir no con respeto, sin cargar con la culpa ajena; "
                 "cuidarte no te hace egoísta."),
        "plataforma": "youtube",
        "tipo": "video",
    },
]


def main():
    all_reports = {}
    for prod in PRODUCTIONS:
        print(f"\n{'='*70}\nPRODUCCIÓN: {prod['name']}\n{'='*70}")
        try:
            rep = pi.produce_v2(
                tema=prod["tema"],
                idea=prod["idea"],
                plataforma=prod["plataforma"],
                tipo=prod["tipo"],
                render=True,
            )
            all_reports[prod["name"]] = rep
            md = pi.ProductionReport.markdown_blocks(rep)
            print("\n" + md)
            with open(os.path.join(OUT, f"{prod['name']}.report.md"), "w",
                      encoding="utf-8") as f:
                f.write(md)
        except Exception as e:
            print(f"\nERROR en {prod['name']}: {e}")
            all_reports[prod['name']] = pi.ProductionReport.error(
                "producción", str(e), accion="revisar red/imágenes y reintentar")
            with open(os.path.join(OUT, f"{prod['name']}.ERROR.txt"), "w",
                      encoding="utf-8") as f:
                f.write(str(e))

    with open(os.path.join(OUT, "reports_v22.json"), "w", encoding="utf-8") as f:
        json.dump(all_reports, f, ensure_ascii=False, indent=2)

    print("\n\nRESUMEN:")
    for name, rep in all_reports.items():
        print(f"  {name}: mp4={rep.get('mp4')} qa={rep.get('qa')}")


if __name__ == "__main__":
    main()
