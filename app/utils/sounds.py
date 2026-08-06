try:
    import winsound
except ImportError:
    winsound = None


def play_success_sound():
    if winsound:
        winsound.MessageBeep(winsound.MB_OK)


def play_error_sound():
    if winsound:
        winsound.MessageBeep(winsound.MB_ICONHAND)