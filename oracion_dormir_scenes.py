# Escenas del largo YOUTUBE 16:9 "oracion-dormir-gracias" (antes de dormir, dando gracias).
# 16:9, voz jorge -8%, BGM, SIN CTA (el largo no lleva CTA; el short sí).
#
# ALTERNANCIA DE RECURSOS (regla del canal):
#   - "stock": True        → video de Pexels (fondo animado)
#   - "stock_photo": True  → foto de Pexels (imagen estática real)
#   - (sin flag)           → imagen generada IA
# Las imagenes IA alternan protagonista HOMBRE / MUJER orando (no solo mujeres).
# Las busquedas de Pexels NO deben devolver menores (filtro en pexels_stock).
#
# TEMATICA: noche / dormir / lamparita calida / cama / paz / refugio.
# REGLA 2026-08-29 (usuario): los recursos NO deben aludir al islam (tunicas blancas,
# alfombras de rezo, prostrracion, mezquita) ni a iconografia catolica (crucifijos, imagenes).
# Para eso los prompts IA anclan occidente-neutral (ropa de dormir, dormitorio sin imagenes
# religiosas, manos juntas al pecho) y los q de Pexels son PRIMEROS PLANOS de manos en oracion
# (asi no se ve cuerpo entero con vestimenta religiosa o fondo de mezquita).
#
# motion: alternar zoom-in/pan/zoom-out con ritmo, sutil.


def _scenes_original():
    return [
        {"ai": 'A man in his fifties sitting on the edge of his bed at night in a modern cozy bedroom, wearing simple pyjamas, eyes gently closed, calm and still, hands gently clasped on his lap in a simple prayer, soft warm lamplight from the bedside table, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man in pyjamas sitting on bed hands clasped in prayer', "text": 'Oración antes de dormir, [1000] dando gracias a Dios. [1200] Antes de dormir, [600] detén por unos minutos todo lo que estás haciendo. [1200]', "motion": 'zoom-in', "stock": True},
        {"ai": 'A woman in her fifties by a window at night in a cozy bedroom, wearing a simple nightgown, hands gently clasped together at her chest in a quiet prayer, eyes gently closed, taking a slow deep breath, soft warm lamplight, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman hands clasped in prayer closeup', "text": 'Deja por un momento las preocupaciones de mañana. [600] Respira profundamente… [1500]', "motion": 'pan-left'},
        {"ai": 'A man in his fifties standing by a window at night in a cozy bedroom, wearing a simple bathrobe, hands gently joined in prayer at his chest, eyes gently closed, soft warm lamplight, reverent and still, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man hands together in prayer closeup', "text": 'Y ponte en la presencia de Dios. [1200] Dios está aquí. [1500]', "motion": 'zoom-in', "stock_photo": True},
        {"ai": 'A man in his fifties seated at the edge of his bed at night, wearing simple pyjamas, hands gently joined together in prayer, profile view, soft warm nightlight beside the bed, trusting and safe,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'closeup of praying hands beside a bed', "text": 'Aunque no puedas verlo, [600] aunque hoy hayas tenido un día difícil, [600] Él ha estado contigo. [1200]', "motion": 'pan-right', "stock": True},
        {"ai": 'A woman in her fifties seated at the edge of her bed at night, wearing a simple nightgown, hands gently joined in prayer, head slightly bowed, quiet humble atmosphere, warm low lamplight, gentle and open,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman praying hands together closeup', "text": 'Puedes comenzar esta noche simplemente diciendo: [1200] Señor, aquí estoy. [1500]', "motion": 'zoom-out'},
        {"ai": 'A man in his fifties in a dark quiet bedroom at night, wearing simple pyjamas, palms gently open facing upward receiving soft warm light, eyes closed, hopeful and calm, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'open palms hands prayer closeup', "text": 'Espíritu Santo, ven. [1200] Ven a mi corazón en este momento. [1200] Ayúdame a estar en paz. [1200]', "motion": 'zoom-in'},
        {"ai": 'A man in his fifties seated at the edge of his bed at night in a cozy bedroom, wearing simple pyjamas, hands gently joined in prayer, eyes closed, releasing what troubles his mind, soft warm lamplight, at peace,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'closeup of two hands joined together in prayer', "text": 'Aparta de mi mente todo aquello que me inquieta. [1500]', "motion": 'pan-left', "stock": True},
        {"ai": 'A man in his fifties seated at the edge of his bed at night, wearing simple pyjamas, hands together in prayer, three-quarter view, quiet cozy night room with soft warm lamp, restful and safe,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man praying at his bedside closeup', "text": 'Ayúdame a dejar por unos minutos las preocupaciones, [600] los pendientes y todo aquello que no puedo resolver esta noche. [1500]', "motion": 'zoom-in', "stock_photo": True},
        {"ai": 'A woman in her fifties seated at the edge of her bed at night, wearing a simple nightgown, hands gently joined in prayer, surrounded by a soft warm glow, grateful and humble,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman praying grateful hands closeup', "text": 'Ilumina mi corazón para reconocer cuánto has hecho por mí durante este día. [1200] Y enséñame a agradecer. [1200]', "motion": 'zoom-out', "stock_photo": True},
        {"ai": 'A man in his fifties seated at the edge of his bed at night, wearing simple pyjamas, hands gently joined in prayer, grateful for the day that is ending, soft warm lamplight, reverent,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'closeup of two hands joined together in prayer', "text": 'Señor, gracias por este día que termina. [1200] Gracias por haberme permitido llegar hasta aquí. [1200]', "motion": 'zoom-in', "stock": True},
        {"ai": 'A man in his fifties seated on his bed at night in a cozy bedroom, wearing simple pyjamas, hands gently joined in prayer over his heart, eyes gently closed, grateful calm, soft warm lamplight, restful, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man hands joined prayer chest closeup', "text": 'Gracias por la vida. [1200] Gracias por mi cuerpo, [600] por mi respiración, [600] por este momento de descanso. [1200]', "motion": 'pan-right'},
        {"ai": 'A woman in her fifties seated at the edge of her bed at night, wearing a simple nightgown, hands gently together in prayer, grateful for her home and her rest, soft warm lamplight, tender and thankful,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman praying grateful home hands closeup', "text": 'Gracias por el lugar donde puedo dormir esta noche. [1200] Gracias por el alimento que recibí. [1200]', "motion": 'zoom-in', "stock_photo": True},
        {"ai": 'A man in his fifties seated at the edge of his bed at night in a cozy bedroom, wearing simple pyjamas, hands gently joined in prayer, softly grateful for his loved ones, warm lamplight, caring and tender,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man praying hands closeup night', "text": 'Gracias por las personas que estuvieron cerca de mí. [1500]', "motion": 'pan-left', "stock": True},
        {"ai": 'A woman in her fifties seated beside her bed at night in a cozy bedroom, wearing a simple nightgown, hands gently together in prayer, eyes lowered, remembering small good moments with gratitude, warm lamplight, calm, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman seated praying hands together', "text": 'Gracias también por aquellas pequeñas cosas que quizás pasé por alto: [1200] por una conversación, [600] por una sonrisa, [600] por un mensaje… [1200]', "motion": 'zoom-in', "stock_photo": True},
        {"ai": 'A man in his fifties by a window at night in a cozy bedroom, a soft grateful expression, hands gently clasped in a quiet prayer at his chest, warm glow, peaceful and tender, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'closeup of praying hands warm light', "text": 'por un momento de tranquilidad, [600] por algo que salió bien, [600] por una dificultad que pude superar. [1200]', "motion": 'pan-right'},
        {"ai": 'A woman in her fifties seated at the edge of her bed at night, wearing a simple nightgown, hands gently joined, warm grateful into the night, soft lamplight, tender thankful mood,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'closeup of two hands joined together in prayer', "text": 'Gracias, Señor. [1200] Porque incluso en los días que parecen ordinarios, [600] hay muchos motivos para agradecer. [1500]', "motion": 'zoom-out', "stock_photo": True},
        {"ai": 'A woman in her fifties sitting on her bed at night in a cozy bedroom, wearing a simple nightgown, eyes closed, holding a comforting cup of tea, reflective honest mood, soft warm lamplight, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman holding tea cup hands closeup', "text": 'Y también quiero darte gracias por lo que hoy no entendí. [1200] Por aquello que me preocupó. [1200]', "motion": 'zoom-in', "stock_photo": True},
        {"ai": 'A man in his fifties with a thoughtful expression by a window at night in a cozy bedroom, wearing a simple bathrobe, hands gently clasped in prayer, soft moonlight and warm lamp, letting go of what hurt, gentle, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man pensive hands clasped closeup', "text": 'Por las situaciones que me hicieron sufrir. [1200] Por las cosas que no salieron como esperaba. [1200]', "motion": 'pan-left', "stock_photo": True},
        {"ai": 'A woman in her fifties seated at the edge of her bed at night, wearing a simple nightgown, palms gently open facing upward in surrender toward soft warm light, trusting,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman open hands prayer closeup', "text": 'Tal vez todavía no comprendo para qué ocurrieron. [1200] Pero esta noche quiero recordar que no tengo que entenderlo todo para ponerlo en tus manos. [1500]', "motion": 'zoom-in', "stock_photo": True},
        {"ai": 'A man in his fifties sitting on his bed at night in a cozy bedroom, wearing simple pyjamas, hands together in prayer, eyes closed, resting calm expression, soft warm glow in a quiet room, at peace, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man hands together prayer restful closeup', "text": 'Tú conoces mi vida. [1200] Tú conoces mis luchas. [1200] Tú conoces aquello que nadie más conoce. [1200] Y por eso puedo descansar en ti. [1500]', "motion": 'zoom-out'},
        {"ai": 'A woman in her fifties with folded hands at her chest, wearing a simple nightgown in a quiet night bedroom, gentle remorseful humble mood, soft warm light, tender, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman folded hands prayer closeup', "text": 'Señor, también quiero pedirte perdón. [1200] Perdóname por las veces que hoy actué mal. [1200]', "motion": 'zoom-in'},
        {"ai": 'A man in his fifties sitting on the edge of his bed at night in a cozy bedroom, wearing simple pyjamas, hands together in a humble prayer, eyes closed, reflective honest expression, warm lamplight, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man humble prayer hands closeup', "text": 'Por las palabras que pudieron herir. [1200] Por mis impaciencias. [1200] Por mis pensamientos equivocados. [1200]', "motion": 'pan-right'},
        {"ai": 'A woman in her fifties with eyes closed in a cozy night bedroom, wearing a simple nightgown, one hand gently over her heart, soft regretful honest mood, warm low light, peaceful reconciliation, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman hand on heart prayer closeup', "text": 'Por las veces que hice aquello que sabía que no estaba bien. [1500]', "motion": 'zoom-in', "stock": True},
        {"ai": 'A man in his fifties seated at the edge of the bed in a cozy night bedroom, wearing simple pyjamas, hands gently folded, humble and open, soft warm light, gentle merciful mood, tender,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'closeup of two hands joined together in prayer', "text": 'Perdóname también por las veces que pude hacer el bien y no lo hice. [1200] Ten misericordia de mí. [1200]', "motion": 'pan-left', "stock": True},
        {"ai": 'A woman in her fifties seated at the edge of her bed at night, wearing a simple nightgown, hands together in prayer, hopeful for a new beginning, soft warm glow of a new morning through the curtain, tender,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman praying hopeful hands closeup', "text": 'Limpia mi corazón y ayúdame a comenzar nuevamente mañana. [1500]', "motion": 'zoom-in', "stock_photo": True},
        {"ai": 'A man in his fifties seated at the edge of his bed at night, wearing simple pyjamas, hands joined in prayer, releasing resentment, eyes closed, soft warm lamplight, released and at peace,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man praying releasing hands closeup', "text": 'Y enséñame también a perdonar a quienes me hicieron daño. [1200] No quiero llevar a la cama el peso del resentimiento. [1200] Quiero descansar dejando todo en tus manos. [1500]', "motion": 'zoom-out', "stock": True},
        {"ai": 'A woman in her fifties with hands gently clasped in prayer, grateful adoring expression, soft warm light in a cozy night bedroom, wearing a simple nightgown, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman grateful praying hands closeup', "text": 'Señor, gracias porque no estoy solo. [1200] Gracias por tu presencia. [1200]', "motion": 'zoom-in'},
        {"ai": 'A woman in her fifties asleep peacefully in a cozy bedroom at night, wearing a simple nightgown, covered by a soft blanket, gentle warm light from the nightstand, safe and cared for, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman sleeping peacefully in bed closeup', "text": 'Gracias por cuidarme incluso cuando yo no me doy cuenta. [1200] Gracias por protegerme. [1200]', "motion": 'pan-right', "stock": True},
        {"ai": 'A man in his fifties sitting up in bed at night in a cozy bedroom, wearing simple pyjamas, gently holding his own hands in comfort, supported and held, soft warm lamplight, comforted, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man holding his own hands comfort closeup', "text": 'Gracias por sostenerme en los momentos en que siento que no puedo más. [1500]', "motion": 'zoom-in'},
        {"ai": 'A woman in her fifties seated at the edge of her bed at night, wearing a simple nightgown, hands joined in prayer, humble and strong, soft warm glow, refuge and strength,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'closeup of two hands joined together in prayer', "text": 'Tú eres bueno. [1200] Tú eres mi refugio. [1200] Tú eres mi fortaleza. [1200]', "motion": 'zoom-out'},
        {"ai": 'A man in his fifties by a night window in a cozy bedroom, wearing a bathrobe, hands gently joined in prayer, looking softly at a moonlit sky, trusting heart, calm, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man praying hands by window closeup', "text": 'Y esta noche quiero recordar que mi vida no depende solamente de mis fuerzas. [1500]', "motion": 'pan-left', "stock_photo": True},
        {"ai": 'A woman in her fifties seated at the edge of her bed at night, wearing a simple nightgown, hands joined in prayer, trusting what she cannot control, soft warm lamplight, peaceful and steady,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman praying trusting hands closeup', "text": 'Hay cosas que no puedo controlar. [600] Hay problemas que no puedo resolver. [600] Hay respuestas que todavía no tengo. [1200] Pero tú sigues siendo Dios. [1200] Y puedo confiar en ti. [1500]', "motion": 'zoom-in', "stock": True},
        {"ai": 'A man in his fifties seated at the edge of his bed at night, wearing simple pyjamas, hands joined in prayer, offering up his worries, soft warm lamplight, releasing and trusting,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man offering worries prayer hands', "text": 'Por eso, Señor, esta noche te entrego mis preocupaciones. [1200] Te entrego aquello que me quita el sueño. [1200]', "motion": 'zoom-in', "stock": True},
        {"ai": 'A man in his fifties seated at the edge of his bed at night, wearing simple pyjamas, hands joined in prayer, offering up his work and studies, soft warm lamplight, letting go,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'closeup of two hands joined together in prayer', "text": 'Te entrego mis problemas familiares. [600] Mis preocupaciones económicas. [600] Mi trabajo. [600] Mis estudios. [1200]', "motion": 'pan-right', "stock": True},
        {"ai": 'A woman in her fifties sitting on her bed at night in a cozy bedroom, wearing a simple nightgown, hands gently open, releasing worries about relationships and health, soft warm light, trusting, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman open hands releasing closeup', "text": 'Mi futuro. [600] Mis relaciones. [600] Mi salud. [600] Mis decisiones. [1200]', "motion": 'zoom-in', "stock_photo": True},
        {"ai": 'A man in his fifties in a dark quiet bedroom at night, wearing simple pyjamas, palms gently open facing upward, softly surrendering everything, soft warm glow, trusting and open, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'open palms surrender prayer closeup', "text": 'Todo aquello que llevo dentro y que quizás ni siquiera sé cómo explicar. [1200] Lo pongo delante de ti. [1500]', "motion": 'zoom-out', "stock_photo": True},
        {"ai": 'A woman in her fifties seated at the edge of her bed at night, wearing a simple nightgown, hands joined in prayer, head bowed, releasing her burdens, soft warm lamplight, relieved and peaceful,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman head bowed prayer hands closeup', "text": 'No quiero seguir cargándolo esta noche. [1500]', "motion": 'pan-left', "stock_photo": True},
        {"ai": 'A man in his fifties seated at the foot of his bed at night in a cozy bedroom, wearing simple pyjamas, hands joined in prayer, asking for his path to be opened, soft warm lamplight, hopeful and trusting,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'closeup of two hands joined together in prayer', "text": 'Haz conmigo lo que yo no puedo hacer. [1200] Abre los caminos que tengan que abrirse. [1200] Cierra aquellos que no me convienen. [1500]', "motion": 'zoom-in', "stock": True},
        {"ai": 'A woman in her fifties with hands gently together in prayer, patient calm expression, soft warm light in a cozy night bedroom, wearing a simple nightgown, waiting with trust, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman patient praying hands closeup', "text": 'Dame sabiduría para tomar buenas decisiones. [1200] Y dame paciencia para esperar cuando todavía no sea el momento. [1500]', "motion": 'pan-right'},
        {"ai": "A man in his fifties seated at the edge of his bed at night, wearing simple pyjamas, hands joined in prayer, placing himself in God's hands, soft warm safe light, caring,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail", "q": 'man placing trust prayer hands', "text": 'Señor, me pongo en tus manos. [1200] Cuida de mí mientras duermo. [1200] Cuida de las personas que amo. [1200]', "motion": 'zoom-in', "stock_photo": True},
        {"ai": 'A woman in her fifties seated at the edge of her bed at night, wearing a simple nightgown, hands joined in prayer, praying for her home and her loved ones, warm lamplight, tender and protective,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman praying home protection hands', "text": 'Protege mi hogar. [600] Dale descanso a mi mente. [600] Dale paz a mi corazón. [1200]', "motion": 'zoom-out', "stock": True},
        {"ai": 'A man in his fifties standing by a night window in a cozy bedroom, wearing simple pyjamas, hands joined in prayer, soft first light of dawn beginning to rise, hopeful and grateful, warm tones,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man praying dawn hands closeup', "text": 'Y si mañana despierto, [600] ayúdame a recibir ese nuevo día como un regalo. [1500]', "motion": 'zoom-in', "stock": True},
        {"ai": 'A woman in her fifties seated at the edge of the bed in a cozy night bedroom, wearing a simple nightgown, hands joined in prayer, soft warm light, learning to trust more, serene,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman learning trust prayer hands', "text": 'Enséñame a confiar más en ti. [1200] A preocuparme menos por aquello que no puedo controlar. [1200]', "motion": 'pan-left'},
        {"ai": 'A man in his fifties with open hands in a gentle action of doing good, soft warm glow, wearing simple pyjamas in a cozy night bedroom, loving and forgiving, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man open hands kindness closeup', "text": 'A hacer el bien que sí puedo hacer. [600] A amar mejor. [600] A perdonar. [600] A agradecer. [1200]', "motion": 'zoom-in'},
        {"ai": 'A woman in her fifties seated at the edge of her bed at night, wearing a simple nightgown, hands joined in prayer, looking up softly with trust, sensed and cared for, warm lamplight,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'closeup of two hands joined together in prayer', "text": 'Y a recordar que nunca estoy fuera de tu mirada. [1500]', "motion": 'zoom-out', "stock_photo": True},
        {"ai": 'A woman in her fifties seated on the edge of her bed at night in a cozy bedroom, wearing a simple nightgown, hands joined in prayer, eyes closed, at rest, soft warm lamplight, calm without answers, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman seated edge of bed praying', "text": 'Ahora puedo descansar. [1200] No necesito resolver mi vida esta noche. [600] No necesito tener todas las respuestas. [1500]', "motion": 'zoom-in', "stock": True},
        {"ai": 'A man in his fifties in a cozy night bedroom, wearing simple pyjamas, hands gently resting on his lap, letting go of what he could not do, soft warm glow, gentle and at ease, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man hands resting letting go closeup', "text": 'Por hoy, hice lo que pude. [1200] Y lo que no pude hacer, Señor, [600] lo dejo en tus manos. [1500]', "motion": 'pan-right'},
        {"ai": 'A man in his fifties seated at the edge of his bed at night, wearing simple pyjamas, hands joined in prayer, full of gratitude, soft warm lamplight, tender and calm,, standing on the floor (not on a prayer mat), plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'man grateful prayer hands closeup', "text": 'Gracias por este día. [600] Gracias por la vida. [600] Gracias por tu amor. [600] Gracias por tu cuidado. [1200]', "motion": 'zoom-in', "stock": True},
        {"ai": 'A woman in her fifties with hands joined in prayer at her chest, eyes closed, final serene closing moment, soft warm nightlight in a cozy bedroom, wearing a simple nightgown, at rest in God, plain modern cozy bedroom without religious images or crosses, intimate observational photography, photorealistic, high detail', "q": 'woman final serene prayer hands closeup', "text": 'Quédate conmigo esta noche. [1200] Y permite que mi corazón descanse en ti. [1500] Amén. [1500]', "motion": 'zoom-out'},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# B-ROLL 2026-08-30 (decisión del usuario): mezcla 33% / 33% / 33%.
#   - 33% personas orando (palmas juntas, verificado con qwen25-vl).
#         . Las conservadas (KEEP) ya están descargadas y verificadas.
#         . Las nuevas (PRAYING_PEX) se traen de Pexels con queries en inglés
#           y se verifican antes de usar.
#   - 33% videitos de Pexels de MONTAÑAS CON SOL EN EL HORIZONTE (sin personas).
#   - 33% fotos de Pexels de MONTAÑAS CON SOL EN EL HORIZONTE.
#   Sin iconografía católica ni alusión al islam (alfombra, túnica, hijab, etc.).
# índices 0-based (eNN -> i = NN-1).
# ─────────────────────────────────────────────────────────────────────────────
_KEEP_ORANDO = {1, 6, 10, 13, 14, 19, 26, 28, 38, 45, 47, 48}
_PRAYING_PEX = {0, 2, 3, 4}                 # e01, e03, e04, e05
_MONTANA_VIDEO = {5, 8, 11, 15, 17, 20, 22, 24, 27, 30, 32, 34, 36, 39, 41, 43, 46}
_MONTANA_FOTO = {7, 9, 12, 16, 18, 21, 23, 25, 29, 31, 33, 35, 37, 40, 42, 44}

# Queries en inglés para Pexels de "persona orando" (verificar neutralidad).
PRAYER_QUERIES = [
    "person praying hands together",
    "man praying hands folded",
    "woman praying hands clasped",
    "hands folded prayer closeup",
]

MONTAÑA_SUNSET = [
    "sunset mountains horizon",
    "mountain peaks sunset",
    "golden hour mountain range",
    "sunset over mountains",
    "mountain ridge sunset",
    "dusk mountains",
    "mountains sunset sky",
    "snowy mountain sunset",
    "mountain silhouette sunset",
    "sunset valley mountains",
    "alpine sunset",
    "mountain lake sunset",
    "sunset horizon mountains",
    "mountain sunset clouds",
    "golden sunset mountains",
    "mountain peaks golden hour",
    "sunset mountain landscape",
    "hills sunset horizon",
    "mountain range sunset light",
    "dusk mountain ridge",
    "sunset behind mountains",
    "mountains warm sunset",
    "snow mountain golden light",
    "mountain horizon dusk",
    "sunset panoramic mountains",
    "mountain summit sunset",
    "evening mountains",
    "sunset over mountain lake",
    "mountain sky sunset clouds",
    "grand sunset mountains",
    "sunset mountain meadow",
    "mountain sunset warm",
    "red sky mountains sunset",
    "mountains at sunset",
    "golden mountain horizon sunset",
    "mountain silhouette warm sunset",
    "canyon mountains sunset",
    "snowy peaks sunset glow",
    "mountain evening light",
    "sunset hills valleys",
    "mountain sunset orange",
]
MONTAÑA_SUNRISE = [
    "sunrise mountains horizon",
    "sunrise over mountains",
    "morning sun mountains",
    "mountain sunrise valley",
    "sunrise peaks mountain range",
    "dawn mountains sunlight",
    "sunrise over mountain lake",
    "morning light mountain summit",
]


def _mountains_query(i):
    pool = MONTAÑA_SUNRISE if i >= 41 else MONTAÑA_SUNSET
    return pool[i % len(pool)]


def _override_media(sc, i):
    """Asigna el recurso visual según el reparto 33/33/33 (y neutralidad)."""
    sc = dict(sc)
    if i in _KEEP_ORANDO:
        return sc
    if i in _PRAYING_PEX:
        sc["stock_photo"] = True
        sc.pop("stock", None)
        sc.pop("ai", None)
        sc["q"] = PRAYER_QUERIES[i % len(PRAYER_QUERIES)]
        return sc
    if i in _MONTANA_VIDEO:
        sc["stock"] = True
        sc.pop("stock_photo", None)
        sc.pop("ai", None)
        sc["q"] = _mountains_query(i)
        return sc
    # foto de montaña
    sc["stock_photo"] = True
    sc.pop("stock", None)
    sc.pop("ai", None)
    sc["q"] = _mountains_query(i)
    return sc


def scenes():
    return [_override_media(s, i) for i, s in enumerate(_scenes_original())]
