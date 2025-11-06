#!/usr/bin/env python3
"""
Standalone skrypt do rozpoznawania mówców przez analizę barwy głosu (MFCC + pitch)
Nie wymaga ładowania RAGSystem - działa na czystym audio
"""

import json
import numpy as np
import librosa
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import re

def extract_audio_features(audio_path, segments):
    """Ekstraktuje cechy audio (MFCC + pitch + energy) dla każdego segmentu"""
    
    print(f"[AUDIO] Wczytywanie pliku audio...")
    audio_data, sr = librosa.load(str(audio_path), sr=16000)
    print(f"[AUDIO] Wczytano: {len(audio_data)/sr:.1f}s, {sr}Hz")
    
    segment_features = []
    valid_segments = []
    
    print(f"[FEATURES] Ekstrakcja cech dla {len(segments)} segmentów...")
    
    for i, seg in enumerate(segments):
        # Wyciągnij timestamp z contentu
        match = re.search(r'\[(\d+):(\d+) - (\d+):(\d+)\]', seg['content'])
        if not match:
            continue
            
        start_min, start_sec = int(match.group(1)), int(match.group(2))
        end_min, end_sec = int(match.group(3)), int(match.group(4))
        
        start_time = start_min * 60 + start_sec
        end_time = end_min * 60 + end_sec
        
        # Wyciągnij fragment audio
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        
        if end_sample > start_sample and end_sample <= len(audio_data):
            segment_audio = audio_data[start_sample:end_sample]
            
            # Minimum 0.4s do analizy
            if len(segment_audio) > sr * 0.4:
                try:
                    # MFCC (Mel-frequency cepstral coefficients) - barwa głosu
                    mfcc = librosa.feature.mfcc(
                        y=segment_audio, 
                        sr=sr, 
                        n_mfcc=13
                    )
                    mfcc_mean = np.mean(mfcc, axis=1)
                    mfcc_std = np.std(mfcc, axis=1)
                    
                    # Pitch (F0) - wysokość głosu
                    pitches, magnitudes = librosa.piptrack(
                        y=segment_audio, 
                        sr=sr
                    )
                    pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
                    pitch_std = np.std(pitches[pitches > 0]) if np.any(pitches > 0) else 0
                    
                    # Energy - energia głosu
                    energy = np.mean(librosa.feature.rms(y=segment_audio))
                    
                    # Spectral centroid - "jasność" dźwięku
                    spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=segment_audio, sr=sr))
                    
                    # Połącz cechy (31 wymiarów total)
                    features = np.concatenate([
                        mfcc_mean,      # 13
                        mfcc_std,       # 13
                        [pitch_mean, pitch_std, energy, spectral_centroid]  # 4
                    ])
                    
                    segment_features.append(features)
                    valid_segments.append(i)
                    
                    if (i + 1) % 20 == 0:
                        print(f"   Przeanalizowano {i+1}/{len(segments)} segmentów...")
                        
                except Exception as e:
                    print(f"   Błąd segment {i}: {e}")
    
    print(f"[FEATURES] ✅ Przeanalizowano {len(valid_segments)}/{len(segments)} segmentów")
    return segment_features, valid_segments


def cluster_speakers(features, valid_segments, distance_threshold=2.0):
    """Klastruje segmenty według podobieństwa głosu"""
    
    if len(features) < 2:
        return {i: "SPEAKER_0" for i in valid_segments}
    
    features_array = np.array(features)
    
    # Normalizacja
    scaler = StandardScaler()
    features_normalized = scaler.fit_transform(features_array)
    
    print(f"[CLUSTERING] Grupowanie podobnych głosów...")
    print(f"   Features shape: {features_normalized.shape}")
    print(f"   Distance threshold: {distance_threshold}")
    
    # Hierarchical clustering
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        linkage='ward'
    )
    labels = clustering.fit_predict(features_normalized)
    
    unique_speakers = len(set(labels))
    print(f"[CLUSTERING] ✅ Wykryto {unique_speakers} mówców")
    
    # Mapuj segmenty do mówców
    speaker_map = {}
    for seg_idx, speaker_id in zip(valid_segments, labels):
        speaker_map[seg_idx] = f"SPEAKER_{speaker_id}"
    
    # Statystyki
    speaker_counts = {}
    for speaker in speaker_map.values():
        speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
    
    print(f"[CLUSTERING] Rozkład segmentów:")
    for speaker in sorted(speaker_counts.keys()):
        print(f"   {speaker}: {speaker_counts[speaker]} segmentów")
    
    return speaker_map


def apply_speaker_labels(transcription_file, audio_file, output_file, distance_threshold=2.0):
    """Aplikuje rozpoznanie mówców do transkrypcji"""
    
    # Wczytaj transkrypcję
    with open(transcription_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    segments = data['transkrypcja']
    
    # Ekstraktuj cechy audio
    features, valid_segments = extract_audio_features(audio_file, segments)
    
    # Klasteruj
    speaker_map = cluster_speakers(features, valid_segments, distance_threshold)
    
    # Aplikuj labele
    print(f"\n[APPLY] Aplikowanie labelek mówców...")
    for i, seg in enumerate(segments):
        if i in speaker_map:
            speaker = speaker_map[i]
        else:
            # Segmenty bez analizy (za krótkie) - użyj najbliższego
            speaker = "SPEAKER_0"
        
        # Zamień w contencie
        seg['content'] = re.sub(
            r'\[SPEAKER_\d+\]',
            f'[{speaker}]',
            seg['content']
        )
        seg['speaker'] = speaker
    
    # Statystyki
    final_speakers = {}
    for seg in segments:
        speaker = seg.get('speaker', 'UNKNOWN')
        final_speakers[speaker] = final_speakers.get(speaker, 0) + 1
    
    data['statystyki_mowcow'] = {
        'liczba_mowcow': len(final_speakers),
        'rozklad': final_speakers,
        'metoda': 'MFCC + Pitch + Energy (hierarchical clustering)'
    }
    
    # Zapisz
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[SAVE] ✅ Zapisano: {output_file}")
    
    return final_speakers


if __name__ == "__main__":
    print("="*80)
    print("ROZPOZNAWANIE MÓWCÓW - ANALIZA BARWY GŁOSU")
    print("="*80)
    
    # Rozmowa 1
    print("\n" + "="*80)
    print("📁 ROZMOWA (1).mp3")
    print("="*80)
    
    speakers1 = apply_speaker_labels(
        transcription_file='test/rozmowa_1_transkrypcja.json',
        audio_file='test/sample_test_file/rozmowa (1).mp3',
        output_file='test/rozmowa_1_SPEAKERS.json',
        distance_threshold=12.0  # Wyższy = mniej mówców (typowo 2-4 osoby)
    )
    
    print(f"\n✅ Wykryto {len(speakers1)} mówców:")
    for speaker in sorted(speakers1.keys()):
        print(f"   {speaker}: {speakers1[speaker]} segmentów")
    
    # Rozmowa 2
    print("\n\n" + "="*80)
    print("📁 ROZMOWA (2).mp3")
    print("="*80)
    
    speakers2 = apply_speaker_labels(
        transcription_file='test/rozmowa_2_transkrypcja.json',
        audio_file='test/sample_test_file/rozmowa (2).mp3',
        output_file='test/rozmowa_2_SPEAKERS.json',
        distance_threshold=15.0  # Wyższy dla dłuższej rozmowy (typowo 2-3 osoby)
    )
    
    print(f"\n✅ Wykryto {len(speakers2)} mówców:")
    for speaker in sorted(speakers2.keys()):
        print(f"   {speaker}: {speakers2[speaker]} segmentów")
    
    print("\n" + "="*80)
    print("✅ ZAKOŃCZONO - pliki zapisane:")
    print("   - test/rozmowa_1_SPEAKERS.json")
    print("   - test/rozmowa_2_SPEAKERS.json")
    print("="*80)

PYEOF

