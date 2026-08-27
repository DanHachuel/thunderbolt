"""Generate long Azure Speech V2 audio through conservative sequential chunks.

The Azure real-time TTS endpoint limits the produced audio of one request to
10 minutes.  This helper deliberately stays far below that limit, adjusts the
text budget for slow voices, and concatenates the completed segments locally.
Secrets are read only from environment variables and are never printed.
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


# Azure documents a 600000 ms maximum for real-time TTS.  This is an internal
# character budget, not a claim that characters map to a fixed duration.  The
# deliberately conservative ceiling leaves room for slow voices, pauses and
# punctuation before the service limit can be approached.
MAX_CHUNK_CHARACTERS = 900
MIN_CHUNK_CHARACTERS = 180
RETRY_COUNT = 3


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Synthesize Azure Speech V2 audio in conservative chunks."
    )
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


def split_text(text: str, limit: int | None = None) -> list[str]:
    """Split paragraphs and sentences without sending an oversized request."""
    try:
        effective_limit = int(limit if limit is not None else MAX_CHUNK_CHARACTERS)
    except (TypeError, ValueError):
        effective_limit = MAX_CHUNK_CHARACTERS
    effective_limit = max(1, effective_limit)
    normalized = re.sub(r"\r\n?", "\n", text).strip()
    if not normalized:
        return []
    pieces = [
        part.strip()
        for part in re.split(r"\n+|(?<=[.!?。！？；;])\s+", normalized)
        if part.strip()
    ]
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        for fragment in _split_long_piece(piece, effective_limit):
            candidate = f"{current} {fragment}".strip()
            if current and len(candidate) > effective_limit:
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


def chunk_character_limit(rate: float) -> int:
    """Return a conservative text budget adjusted to the requested speech rate."""
    normalized_rate = _normalise_rate(rate)
    # A slow rate stretches the audio, so reduce the text budget proportionally.
    # A fast rate is capped: the service limit is not a reason to send huge SSML.
    return max(
        MIN_CHUNK_CHARACTERS,
        min(MAX_CHUNK_CHARACTERS, int(round(MAX_CHUNK_CHARACTERS * normalized_rate))),
    )


def _build_ssml(text: str, voice: str, rate: float) -> str:
    parts = voice.split("-", 2)
    locale = "-".join(parts[:2]) if len(parts) >= 2 else "en-US"
    escaped_voice = escape(voice, {'"': "&quot;"})
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{escape(locale)}">'
        f'<voice name="{escaped_voice}">'
        f'<prosody rate="{_normalise_rate(rate):g}">{escape(text)}</prosody>'
        "</voice></speak>"
    )


def _synthesise_chunk(
    speechsdk, text: str, voice: str, rate: float, target: Path
) -> None:
    speech_key = os.environ.get("AZURE_SPEECH_KEY", "").strip()
    region = os.environ.get("AZURE_SPEECH_REGION", "").strip()
    if not speech_key or not region:
        raise RuntimeError(
            "Azure Speech SDK V2 requer AZURE_SPEECH_KEY e AZURE_SPEECH_REGION."
        )
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=region)
    speech_config.speech_synthesis_voice_name = voice
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
    )
    audio_config = speechsdk.audio.AudioOutputConfig(
        filename=str(target), use_default_speaker=False
    )
    synthesizer = speechsdk.SpeechSynthesizer(
        audio_config=audio_config, speech_config=speech_config
    )
    try:
        result = synthesizer.speak_ssml_async(_build_ssml(text, voice, rate)).get()
    finally:
        synthesizer.close()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = getattr(
            getattr(result, "cancellation_details", None), "error_details", ""
        )
        reason = str(details or getattr(result, "reason", "unknown"))
        raise RuntimeError(
            f"Azure Speech SDK V2 não concluiu um segmento: {reason[:500]}"
        )
    if not target.is_file() or target.stat().st_size <= 0:
        raise RuntimeError(
            "Azure Speech SDK V2 terminou sem produzir o áudio do segmento."
        )


def generate(text: str, voice: str, rate: float, output: Path) -> int:
    import azure.cognitiveservices.speech as speechsdk
    from pydub import AudioSegment

    ffmpeg_binary = os.environ.get("IMAGEIO_FFMPEG_EXE", "").strip() or shutil.which(
        "ffmpeg"
    )
    if not ffmpeg_binary:
        try:
            import imageio_ffmpeg

            ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_binary = ""
    if not ffmpeg_binary:
        raise RuntimeError(
            "FFmpeg não está disponível para concatenar os segmentos Azure Speech V2."
        )
    AudioSegment.converter = ffmpeg_binary

    normalized_rate = _normalise_rate(rate)
    limit = chunk_character_limit(normalized_rate)
    chunks = split_text(text, limit=limit)
    if not chunks:
        raise RuntimeError("O roteiro não contém texto para síntese Azure Speech.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix="azure-v2-chunks-", dir=str(output.parent)
    ) as temporary:
        temporary_path = Path(temporary)
        segment_paths: list[Path] = []
        for index, chunk in enumerate(chunks, start=1):
            segment_path = temporary_path / f"segment-{index:04d}.mp3"
            last_error: Exception | None = None
            for attempt in range(1, RETRY_COUNT + 1):
                try:
                    segment_path.unlink(missing_ok=True)
                    _synthesise_chunk(
                        speechsdk, chunk, voice, normalized_rate, segment_path
                    )
                    last_error = None
                    break
                except Exception as exc:  # Azure SDK exposes provider-specific classes.
                    last_error = exc
                    if attempt < RETRY_COUNT:
                        time.sleep(2 ** (attempt - 1))
            if last_error is not None:
                raise RuntimeError(
                    f"Falha no segmento Azure Speech {index}/{len(chunks)}: {last_error}"
                ) from last_error
            segment_paths.append(segment_path)
            print(f"AZURE_CHUNK_PROGRESS={index}/{len(chunks)}", flush=True)

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
    print(f"AZURE_CHUNK_CHARACTER_LIMIT={chunk_character_limit(args.rate)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
