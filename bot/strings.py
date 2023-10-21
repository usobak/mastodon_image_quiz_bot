'''Messages published by the bot.'''

FOOTER = '\nMás info en mi perfil.\n#bot'

NEW_CLUE = 'Pista {}/{} ¿Conoces este juego? 🤔 Escribe el título en los comentarios y a ver si aciertas.' + FOOTER

LAST_CLUE = '¡Última oportunidad!\n' + NEW_CLUE + FOOTER

NEW_GAME_SOON = '¿Has jugado a este juego? ¿Qué te parece?\nEn unos minutos empezará una nueva ronda.' + FOOTER

SOLUTION_FOUND = '¡Alguien ha encontrado la solución! 😎\nEl título es: {}\n' + NEW_GAME_SOON
SOLUTION_NOT_FOUND = '¡Qué pena! Nadie ha adivinado el título. 😩 \nEl juego es: {}\n' + NEW_GAME_SOON
