import pygame
import os
import time

# FORCE Pi 5 to use the GPU directly
os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
os.environ['SDL_VIDEO_DOUBLEBUFFER'] = '1'

def show_bmo():
    # Explicitly initialize the display only
    try:
        pygame.display.init()
    except Exception as e:
        print(f"Failed to init display: {e}")
        return

    #  MUST use the current hardware resolution (For pi 5)
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    
    try:
        face = pygame.image.load('/home/bmo/assets/faces/bmo_face_01.png')
        face = pygame.transform.scale(face, (info.current_w, info.current_h))
        screen.blit(face, (0, 0))
        pygame.display.flip()
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()

if __name__ == "__main__":
    show_bmo()
