"""Generate long Azure Speech V2 audio by synthesizing safe sequential chunks.

This helper runs inside the MoneyPrinterTurbo uv project so it can use the
same Azure Speech SDK and audio dependencies as the installed engine. Secrets
are read only from environment variables and are never printed.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.sax.saxutils import escape


MAX_CHUNK_CHARACTERS = 1800
RETRY_COUNT = 3


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synthesize Azure Speech V2 audio in safe chunks.")
    parser.add_argument("--text-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--rate", type=float, default=1.0)
    return parser


def _split_long_piece(piece: str, limit: int) -> list[str]:
    piece = " ".join(piece.split())
    if len(piece) <= limit:
        return [piece]
    words = piece.split(" ")
    chunks: list[str] = []
    current = ""
    for word in words:
        if len(word) > limit:
            if current:
                chunks.append(current)
                current = ""
            for start in range(0, len(word), limit):
                chunks.append(word[start : start + limit])
            continue
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > limit:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def split_text(text: str, limit: int = MAX_CHUNK_CHARACTERS) -> list[str]:
    """Split paragraphs and sentences without sending a 10-minute request."""
    normalized = re.sub(r"\r\n?", "\n", text).strip()
    if not normalized:
        return []
    pieces = [part.strip() for part in re.split(r"\n+|(?<=[.!?。！？；;])\s+", normalized) if part.strip()]
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        for fragment in _split_long_piece(piece, limit):
            candidate = f"{current} {fragment}".strip()
            if current and len(candidate) > limit:
                chunks.append(current)
                current = fragment
            else:
                current = candidate
    if current:
        chunks.append(current)
    return chunks


def _normalise_rate(value: float) -> float:
    try:
        rate = float(value)
    except (TypeError, ValueError):
        rate = 1.0
    return max(0.25, min(4.0, rate))


def _build_ssml(text: str, voice: str, rate: float) -> str:
    locale = "-".join(voice.split("-", 2)[:2]) if len(voice.split("-", 2)) >= 2 else "en-US"
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{escape(locale)}">'
        f'<voice name="{escape(voice, {"\"": "&quot;"})}">'
        f'<prosody rate="{_normalise_rate(rate):g}">{escape(text)}</prosody>'
        "</voice></speak>"
    )


def _synthesise_chunk(speechsdk, text: str, voice: str, rate: float, target: Path) -> None:
    speech_key = os.environ.get("AZURE_SPEECH_KEY", "").strip()
    region = os.environ.get("AZURE_SPEECH_REGION", "").strip()
    if not speech_key or not region:
        raise RuntimeError("Azure Speech SDK V2 requer AZURE_SPEECH_KEY e AZURE_SPEECH_REGION.")
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=region)
    speech_config.speech_synthesis_voice_name = voice
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
    )
    audio_config = speechsdk.audio.AudioOutputConfig(filename=str(target), use_default_speaker=False)
    synthesizer = speechsdk.SpeechSynthesizer(audio_config=audio_config, speech_config=speech_config)
    try:
        result = synthesizer.speak_ssml_async(_build_ssml(text, voice, rate)).get()
    finally:
        synthesizer.close()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = getattr(getattr(result, "cancellation_details", None), "error_details", "")
        reason = str(details or getattr(result, "reason", "unknown"))
        raise RuntimeError(f"Azure Speech SDK V2 não concluiu um segmento: {reason[:500]}")
    if not target.is_file() or target.stat().st_size <= 0:
        raise RuntimeError("Azure Speech SDK V2 terminou sem produzir o áudio do segmento.")


def generate(text: str, voice: str, rate: float, output: Path) -> int:
    import azure.cognitiveservices.speech as speechsdk
    from pydub import AudioSegment

    ffmpeg_binary = os.environ.get("IMAGEIO_FFMPEG_EXE", "").strip() or shutil.which("ffmpeg")
    if not ffmpeg_binary:
        try:
            import imageio_ffmpeg

            ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_binary = ""
    if ffmpeg_binary:
        AudioSegment.converter = ffmpeg_binary
    else:
        raise RuntimeError("FFmpeg não está disponível para concatenar os segmentos Azure Speech V2.")

    chunks = split_text(text)
    if not chunks:
        raise RuntimeError("O roteiro não contém texto para síntese Azure Speech.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="azure-v2-chunks-", dir=str(output.parent)) as temporary:
        temporary_path = Path(temporary)
        segment_paths: list[Path] = []
        for index, chunk in enumerate(chunks, start=1):
            segment_path = temporary_path / f"segment-{index:04d}.mp3"
            last_error: Exception | None = None
            for attempt in range(1, RETRY_COUNT + 1):
                try:
                    _synthesise_chunk(speechsdk, chunk, voice, rate, segment_path)
                    last_error = None
                    break
                except Exception as exc:  # Azure SDK exposes provider-specific exception classes.
                    last_error = exc
                    if attempt < RETRY_COUNT:
                        time.sleep(2 ** (attempt - 1))
            if last_error is not None:
                raise RuntimeError(f"Falha no segmento Azure Speech {index}/{len(chunks)}: {last_error}") from last_error
            segment_paths.append(segment_path)

        combined = AudioSegment.empty()
        for segment_path in segment_paths:
            combined += AudioSegment.from_file(segment_path, format="mp3")
        combined.export(output, format="mp3", bitrate="192k")
    if not output.is_file() or output.stat().st_size <= 0:
        raise RuntimeError("A concatenação Azure Speech V2 não produziu áudio válido.")
    return len(chunks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    text = args.text_file.read_text(encoding="utf-8")
    try:
        count = generate(text, args.voice, args.rate, args.output)
    except Exception as exc:
        print(f"Azure Speech V2 chunked synthesis failed: {exc}", file=sys.stderr)
        return 1
    print(f"AZURE_CHUNKED_AUDIO={args.output.resolve()}")
    print(f"AZURE_CHUNK_COUNT={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
