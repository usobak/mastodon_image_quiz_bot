'''Messages published by the bot.'''

FOOTER = '\nMás info en mi perfil.\n#bot'

NEW_CLUE = 'Pista {}/{} ¿Conoces este juego? 🤔 Escribe el título en los comentarios y a ver si aciertas.' + FOOTER

LAST_CLUE = '¡Última oportunidad!\n' + NEW_CLUE + FOOTER

SOLUTION_FOUND = '¡Alguien ha encontrado la solución! 😎\nEl título es: {}' + FOOTER
SOLUTION_NOT_FOUND = '¡Qué pena! Nadie ha adivinado el título. 😩 \nEl juego es: {}' + FOOTER
