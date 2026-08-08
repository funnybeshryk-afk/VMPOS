import io
import math
import struct
import threading
import wave

try:
    import winsound
except ImportError:
    winsound = None

_SAMPLE_RATE = 44100
_FADE_SECONDS = 0.005


def _tone_samples(frequency, duration_ms, volume=0.5):
    """Отсчёты одного чистого синусоидального тона (int16, моно).

    Короткий линейный fade-in/fade-out (~5 мс) на границах — без
    него чистый синус обрывается резко и слышен как щелчок на
    старте и в конце ноты.
    """

    sample_count = int(_SAMPLE_RATE * duration_ms / 1000)
    fade_samples = max(1, min(int(_SAMPLE_RATE * _FADE_SECONDS), sample_count // 2))

    samples = []

    for i in range(sample_count):
        envelope = 1.0

        if i < fade_samples:
            envelope = i / fade_samples
        elif i > sample_count - fade_samples:
            envelope = (sample_count - i) / fade_samples

        value = math.sin(2 * math.pi * frequency * i / _SAMPLE_RATE)
        samples.append(int(value * envelope * volume * 32767))

    return samples


def _silence_samples(duration_ms):
    return [0] * int(_SAMPLE_RATE * duration_ms / 1000)


def _play_tones(*tones):
    """Проигрывает один или несколько тонов подряд: (частота_Гц, длительность_мс).

    Все тона склеиваются в один WAV-буфер в памяти и проигрываются
    ОДНИМ вызовом PlaySound. Если звать PlaySound несколько раз
    подряд с SND_ASYNC, Windows обрывает предыдущий асинхронный звук
    вместо того, чтобы поставить его в очередь — поэтому "два тона"
    можно получить только склеив их заранее, а не двумя вызовами.

    SND_ASYNC вместе с SND_MEMORY модуль winsound запрещает в
    принципе (RuntimeError: "Cannot play asynchronously from
    memory") — Python не может гарантировать, что байтовый буфер
    доживёт до конца воспроизведения в другом потоке. Поэтому
    проигрываем синхронным вызовом, но в отдельном daemon-потоке —
    UI при этом не блокируется, а буфер жив, пока жив сам поток.
    """

    if not winsound:
        return

    samples = []

    for index, (frequency, duration_ms) in enumerate(tones):
        if index > 0:
            samples.extend(_silence_samples(20))

        samples.extend(_tone_samples(frequency, duration_ms))

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(_SAMPLE_RATE)
        wav_file.writeframes(
            struct.pack(f"<{len(samples)}h", *samples)
        )

    threading.Thread(
        target=winsound.PlaySound,
        args=(buffer.getvalue(), winsound.SND_MEMORY),
        daemon=True,
    ).start()


def play_add_sound():
    """Mahsulot korzinaga qo'shilganda / shtrix-kod skanerlanganda."""
    _play_tones((880, 100))


def play_payment_sound():
    """To'lov muvaffaqiyatli yakunlanganda — ikkita ko'tarilib boruvchi ton."""
    _play_tones((880, 110), (1318, 160))


def play_error_sound():
    if winsound:
        winsound.MessageBeep(winsound.MB_ICONHAND)
