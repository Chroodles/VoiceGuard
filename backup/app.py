from flask import Flask, request, send_file, render_template
import numpy as np
import librosa
import soundfile as sf
from scipy.fft import fft, ifft
from pydub import AudioSegment
import io
import os

app = Flask(__name__)

def load_audio(file):
    if file.filename.lower().endswith('.mp3'):
        audio = AudioSegment.from_mp3(file)
        sr = audio.frame_rate
        audio = audio.set_channels(1)  # Convert to mono
        audio = np.array(audio.get_array_of_samples(), dtype=np.float32) / 32768.0
    elif file.filename.lower().endswith('.wav'):
        audio, sr = librosa.load(file, sr=None)
    else:
        raise ValueError("Unsupported file format")
    return audio, sr

def save_audio(audio, sr, file):
    output = io.BytesIO()
    if file.filename.lower().endswith('.mp3'):
        # Save as WAV first, then convert to MP3
        wav_path = 'temp.wav'
        sf.write(wav_path, audio, sr)
        audio_segment = AudioSegment.from_wav(wav_path)
        audio_segment.export(output, format='mp3')
        os.remove(wav_path)  # Clean up temporary WAV file
    elif file.filename.lower().endswith('.wav'):
        sf.write(output, audio, sr)
    else:
        raise ValueError("Unsupported file format")
    output.seek(0)
    return output

def apply_spectral_watermark(audio, sr, amplitude=0.02):
    D = librosa.stft(audio)
    watermark = np.sin(2 * np.pi * np.linspace(0, 1, D.shape[0]) * 20)
    D_watermarked = D + amplitude * watermark[:, np.newaxis]
    return librosa.istft(D_watermarked)

def add_perturbation(signal, perturbation_level=0.05):
    perturbation = np.random.normal(0, perturbation_level, len(signal))
    return signal + perturbation * 0.005

def normalize_audio(audio):
    max_amplitude = np.max(np.abs(audio))
    if max_amplitude > 0:
        audio = audio / max_amplitude
    return audio

def apply_compression(audio, threshold=0.1, ratio=4):
    audio = np.clip(audio, -threshold, threshold)
    audio = audio / ratio
    return np.clip(audio, -1, 1)

def apply_distortion(audio, intensity=0.1):
    return np.tanh(audio * intensity)

def normalize_volume(audio, target_level=0.07):
    max_amplitude = np.max(np.abs(audio))
    if max_amplitude > 0:
        scale_factor = target_level / max_amplitude
        audio *= scale_factor
    return audio

def process_audio(input_file, perturbation_level, watermark_amplitude, compression_threshold, compression_ratio, distortion_intensity, volume_target):
    audio, sr = load_audio(input_file)

    # Apply techniques with settings
    audio = apply_spectral_watermark(audio, sr, watermark_amplitude)
    audio = add_perturbation(audio, perturbation_level)
    audio = apply_compression(audio, compression_threshold, compression_ratio)
    audio = apply_distortion(audio, distortion_intensity)
    audio = normalize_volume(audio, volume_target)

    return save_audio(audio, sr, input_file)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        perturbation_level = float(request.form.get('perturbation_level', 0.05))
        watermark_amplitude = float(request.form.get('watermark_amplitude', 0.02))
        compression_threshold = float(request.form.get('compression_threshold', 0.1))
        compression_ratio = float(request.form.get('compression_ratio', 4))
        distortion_intensity = float(request.form.get('distortion_intensity', 0.1))
        volume_target = float(request.form.get('volume_target', 0.07))

        if file:
            processed_audio = process_audio(
                file,
                perturbation_level,
                watermark_amplitude,
                compression_threshold,
                compression_ratio,
                distortion_intensity,
                volume_target
            )
            return send_file(processed_audio, as_attachment=True, download_name='processed_audio.mp3')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
