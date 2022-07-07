import pygame
from time import time
from random import randint, choice
import sys
import ai


GAME_ID = randint(0, 99999)  # on genere un id aléatoire pour differencier les parties
GAME_START = time()  # timestamp du début de la partie, pour ajuster la vitesse de la gravité
SAVE_RESULTS = False  # sauvegarder les resultats de chaque génération dans un fichier texte
AI_MODE = True  # true pour faire jouer les ia, false pour jouer soi-même
FAST_AI = False  # true pour que l'ia force la piece vers le bas dès qu'elle est bien placée


def show(m, score):  # fonction pour l'affichage du jeu
    screen.fill((0, 0, 0))  # on remplit l'écran de noir
    if not started:
        screen.blit(pygame.transform.scale(pygame.image.load("res/start_screen.png"), (screen.get_width(), screen.get_height())), (0, 0))
        if time() % 2 <= 1.25:
            screen.blit(pygame.transform.scale(pygame.image.load("res/press_start.png"), (screen.get_width(), screen.get_height())), (0, 0))
        return
    for y in range(len(m)):  # et on parcoure la matrice en ajoutant les textures correspondantes
        for x in range(len(m[y])):
            if m[y][x] != 0:
                screen.blit(colors[m[y][x]-1], (x*size, y*size))
    # affichage du score
    current_x = 5
    for a in str(int(score)):
        img = pygame.image.load("res/numbers/" + a + ".png")
        screen.blit(img, (current_x, 5))
        current_x += img.get_width() + 2



def gen_image(size):  # charger les images à la bonne taille
    res = []
    for a in ["blue", "cyan", "green", "magenta", "orange", "red", "yellow"]:
        img = pygame.image.load("res/blocks/" + a + ".png")
        if size != 16:
            img = pygame.transform.scale(img, (size, size))
        res.append(img)
    return res


def place(m, piece, x, y, color, moving):  # fonction pour placer une piece à des coordonnées, si possible
    global game_over
    mo = []
    for a in range(len(piece)):  # premiere boucle pour verifier les emplacements disponibles
        for b in range(len(piece[a])):
            if piece[a][b] == 1:
                if m[y+a][x+b] != 0:  # si un emplacement est déjà pris, la partie est terminée
                    game_over = True
                    return
    for a in range(len(piece)):  # seconde boucle pour placer la piece
        for b in range(len(piece[a])):
            if piece[a][b] == 1:
                m[y+a][x+b] = color
                mo.append((x+b, y+a))
    moving.extend(mo)  # on met à jour la liste des pieces qui bougent


def spawn_piece(m, pieces, colors, moving):  # faire apparaitre une piece aléatoire
    global next_piece
    col = randint(0, len(colors) - 1)
    mid = len(m[0]) // 2 - len(pieces[next_piece][0]) // 2
    place(m, pieces[next_piece], mid, 0, col, moving)
    next_piece = randint(0, len(pieces) - 1)


def apply_gravity(m, moving):  # appliquer la gravité à la piece en train de bouger
    for x, y in moving:  # premiere boucle pour verifier les emplacements disponibles
        if y+1 >= len(m) or (m[y+1][x] != 0 and (x, y+1) not in moving):
            if AI_MODE or time() - last_move > 5 * move_tick:
                moving.clear()
            return
    # on met à jour les positions de la pièce qui bouge
    color = 0
    for x, y in moving:
        color = m[y][x]
        m[y][x] = 0
    for a in range(len(moving)):
        moving[a] = (moving[a][0], moving[a][1]+1)
    for x, y in moving:
        m[y][x] = color

def move(m, moving, dir):  # False: gauche, True; droite, bouger la piece sur le coté
    global last_move
    d = 1 if dir else -1
    for x, y in moving:  # premiere boucle pour verifier les emplacements disponibles
        if x+d >= len(m[0]) or x+d < 0 or (m[y][x+d] != 0 and (x+d, y) not in moving):
            return
    color = 0
    # on met à jour les positions de la pièce qui bouge
    for x, y in moving:
        color = m[y][x]
        m[y][x] = 0
    for a in range(len(moving)):
        moving[a] = (moving[a][0]+d, moving[a][1])
    for x, y in moving:
        m[y][x] = color
    last_move = time()

def rotate(m, moving):  # faire tourner la pièce sur elle-même
    if moving == []: return
    global last_move
    # on collecte des informations qui nous seront utiles
    min_x, min_y, max_x, max_y = moving[0][0], moving[0][1], moving[0][0], moving[0][1]
    for x, y in moving[1:]:
        if x < min_x:
            min_x = x
        if x > max_x:
            max_x = x
        if y < min_y:
            min_y = y
        if y > max_y:
            max_y = y
    center_x, center_y = (min_x + max_x) // 2, (min_y + max_y) // 2
    if center_x == 0:
        center_x = 1
    for x, y in moving:  # premiere boucle pour verifier les emplacements disponibles
        delta_x, delta_y = center_x - x, center_y - y
        new_x, new_y = center_x - delta_y, center_y + delta_x
        if new_x >= len(m[0]) or new_x < 0 or new_y < 0 or new_y >= len(m) or \
        (m[new_y][new_x] != 0 and (new_x, new_y) not in moving):
            return
    # on met à jour les positions de la pièce qui bouge
    for x, y in moving:
        color = m[y][x]
        m[y][x] = 0
    for a in range(len(moving)):
        x, y = moving[a]
        delta_x, delta_y = center_x - x, center_y - y
        new_x, new_y = center_x - delta_y, center_y + delta_x
        moving[a] = (new_x, new_y)
    for x, y in moving:
        m[y][x] = color
    last_move = time()

def delete_line(m, line, moving):  # supprimer une ligne et en créer un nouvelle en haut de la matrice
    m.pop(line)
    m.insert(0, [0] * len(m[0]))
    for a in range(len(moving)):
        moving[a] = (moving[a][0], moving[a][1]+1)

def check_lines(m, moving):  # vérifier la matrice de jeu et supprimer toutes les lignes pleines
    global score
    count = 0
    for y in range(len(m)):  # on parcoure chaque ligne en vérifiant si elle est pleine
        ok = True
        for x in range(len(m[y])):
            if m[y][x] == 0 or (x, y) in moving:
                ok = False
                break
        if ok:
            delete_line(m, y, moving)  # si elle est pleine, on la supprime et on met à jour le compte
            count += 1
    score += [0, 100, 300, 500, 800][count]  # on ajoute le score correspondant au nombre de lignes supprimées


def force_down(m, moving):  # amener la piece au plus bas qu'elle peut être à sa position x
    while True:  # on applique simplement la fonction de gravité en boucle, jusqu'à ce que la piece soit bloquée
        for x, y in moving:
            if y+1 >= len(m) or (m[y+1][x] != 0 and (x, y+1) not in moving):
                if AI_MODE or time() - last_move > 5 * move_tick:
                    moving.clear()
                return
        color = 0
        for x, y in moving:
            color = m[y][x]
            m[y][x] = 0
        for a in range(len(moving)):
            moving[a] = (moving[a][0], moving[a][1]+1)
        for x, y in moving:
            m[y][x] = color

def reset():  # reset la partie pour passer à la suivante
    global score, matrix, moving, game_over, printed_score, score_step
    score = 0
    matrix = [[0] * width for a in range(height)]
    moving = []
    spawn_piece(matrix, pieces, colors, moving)
    game_over = False
    printed_score = 0
    score_step = 0

def save(file, gen):  # sauvegarder les données des IA, pour faire les excel
    res = "gen " + str(gen) + ":\n"
    for a in agents:
        res += str(a.fitness) + "\n"
    res += "\n"
    open(file, "a+").write(res)


def handle_event(event):  # gestion des évènements (entrées clavier, ...)
    global FAST_AI, started
    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
        sys.exit()
    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP:
            rotate(matrix, moving)
        elif event.key == pygame.K_m:
            agents[current_agent].info()
        elif event.key == pygame.K_p:
            FAST_AI = not FAST_AI
        elif event.key == pygame.K_LEFT and time() - last_move_tick > move_tick:
            move(matrix, moving, False)
        elif event.key == pygame.K_RIGHT and time() - last_move_tick > move_tick:
            move(matrix, moving, True)
        elif event.key == pygame.K_SPACE:
            if not started:
                started = True


width, height = 10, 18  # taille du jeu
size = 32  # taille de chaque case, en pixel

pieces = [  # matrice de chaque piece existante
    [ [1, 1],
      [1, 1] ],
    [ [0, 1, 0],
      [1, 1, 1] ],
    [ [1, 0],
      [1, 0],
      [1, 1] ],
    [ [0, 1],
      [0, 1],
      [1, 1] ],
    [ [0, 1, 1],
      [1, 1, 0] ],
    [ [1, 1, 0],
      [0, 1, 1] ],
    [ [1], [1], [1], [1]],
]
colors = gen_image(size)


# initialisation
display = pygame.init()

# affichage
screen_width, screen_height = width*size, height*size
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Teris")
pygame.display.set_icon(pygame.image.load("res/blocks/red.png"))


# ticks
last_gravity_tick = 0
gravity_tick = 0.3  # temps entre chaque application de gravité
fast_gravity_tick = 0.075  # temps entre chaque application de gravité, quand la touche du bas est préssée
last_frame_tick = 0
frame_tick = 1 / 24  # temps entre chaque image
last_move_tick = 0
move_tick = 0.15  # temps entre chaque mouvement
last_move = time()
last_ai_tick = 0
ai_tick = 0.001  # temps entre chaque tick de l'IA


# jeu
score = 0  # score actuel
matrix = [[0] * width for a in range(height)]  # matrice du jeu
moving = []  # liste des positions des pieces qui bougent
next_piece = randint(0, len(pieces) - 1)  # prochaine piece à apparaitre
spawn_piece(matrix, pieces, colors, moving)  # on fait apparaitre la première piece
game_over = False  # partie terminée ou non
printed_score = 0  # score affiché
score_step = 0  # pour l'affichage du score


# intelligence artificielle
gen_count = 0  # génération actuelle
gen_size = 50  # nombre d'individus par génération
current_agent = 0  # individu actuel
agents = [ai.Agent("Agent " + str(a + 1)) for a in range(gen_size)]  # liste des agents
started = False

# un agent très bon, retirer le commentaire et mettre ai_mode à true pour le voir jouer
# agents[0].weights =[-0.144548640072046, -0.02174555821043643, 0.3430094734753558, -0.607158577374197]


while True:  # boucle principale
    for event in pygame.event.get():  # gestion des entrées clavier etc.
        handle_event(event)
    
    # mise à jour de la vitesse de gravité
    gravity_tick = max(0.075, 0.3 - (score//500)*0.05)
    
    # gestion des inputs
    if (started and not game_over) and time() - last_move_tick > move_tick:
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            move(matrix, moving, False)
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            move(matrix, moving, True)
        last_move_tick = time()
    
    # si aucune piece n'est en train de bouger, en ajouter une nouvelle
    if (started and not game_over) and moving == []:
        spawn_piece(matrix, pieces, colors, moving)
    
    # appliquer la gravité quand nécessaire
    if (started and not game_over) and ((pygame.key.get_pressed()[pygame.K_DOWN] and time() - last_gravity_tick > fast_gravity_tick) or time() - last_gravity_tick > gravity_tick):
        apply_gravity(matrix, moving)
        last_gravity_tick = time()
        check_lines(matrix, moving)
    
    # afficher une nouvelle image à l'écran
    if time() - last_frame_tick > frame_tick:
        printed_score = min(score, printed_score + (score - score_step)/60)
        if printed_score == score:
            score_step = score
        show(matrix, printed_score)
        pygame.display.flip()
        last_frame_tick = time()
    
    # faire fonctionner l'IA
    if moving != [] and (started and not game_over) and time() - last_ai_tick > ai_tick and AI_MODE:
        check_lines(matrix, moving)
        # placement de la piece
        x, rot = agents[current_agent].best_move(matrix, moving, pieces[next_piece])
        for a in range(rot):
            rotate(matrix, moving)  # ajustement de la rotation
        if rot != 0:
            apply_gravity(matrix, moving)  # sans cette ligne, la piece se bloque parfois
        if moving != []:
            current_x = min(moving, key=lambda a: a[0])[0]
            mo = False if x < current_x else True
            for a in range(abs(x - current_x)):  # ajustement de la position
                move(matrix, moving, mo)
        if FAST_AI and rot == 0:
            force_down(matrix, moving)  # si le mode rapide est activé, une fois la pièce bien placée, on la force en bas
        last_ai_tick = time()

    elif game_over:  # une fois que l'agent a perdu la partie
        # on met à jour son fitness, et on passe au suivant
        agents[current_agent].fitness = score
        print(agents[current_agent].fitness)
        current_agent += 1

        if current_agent >= len(agents): # si tous les agents de la génération ont été testés
            # on passe à la génération suivante
            gen_count += 1
            if SAVE_RESULTS:
                save("save" + str(GAME_ID) + ".txt", gen_count)
            agents = sorted(agents, key=lambda a: a.fitness)
            print("current gen:", gen_count)
            print("best agent:")
            agents[-1].info()
            agents = agents[-5:]
            for a in range(gen_size - 5):
                agents.append(choice(agents[:5]).child(choice(agents[:5])))
            current_agent = 0

        reset()  # on reset la partie, avant de faire jouer le prochain agent
