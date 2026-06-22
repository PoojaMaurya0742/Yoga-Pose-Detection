import sys
import os
import uuid

def run_voice():
    try:
        from gtts import gTTS
        import pygame
        import warnings
        warnings.filterwarnings("ignore")
        
        text = sys.argv[1]
        language = sys.argv[2]
        
        lang_code = 'hi' if language == 'Hindi' else 'en'
        tld = 'co.in' if language == 'Hindi' else 'us'
        
        tts = gTTS(text=text, lang=lang_code, tld=tld, slow=False)
        
        unique_id = uuid.uuid4().hex
        audio_file = f"temp_voice_{unique_id}.mp3"
        tts.save(audio_file)
        
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.quit()
        if os.path.exists(audio_file):
            os.remove(audio_file)
            
    except Exception as e:
        pass

if __name__ == '__main__':
    run_voice()
