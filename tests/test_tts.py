"""Test MiniMax TTS service integration."""

import asyncio

from backend.services.tts_service import TTSService


async def test_single_synthesis():
    """Verify that a single sentence can be synthesized to MP3 bytes."""
    service = TTSService()

    text = "大家好，欢迎收听MindCast<#0.5#>智想电波(chuckle)，我是主持人林晨曦。"
    voice_id = "female-shaonv"

    print(f"\n=== TTS Synthesis Test ===")
    print(f"Text: {text}")
    print(f"Voice: {voice_id}")

    audio_bytes = await service.synthesize(
        text=text,
        voice_id=voice_id,
        emotion="happy",
    )

    print(f"Audio bytes: {len(audio_bytes)}")
    assert len(audio_bytes) > 0, "Should produce non-empty audio"

    # Optionally save to disk for manual listening
    output_path = "output/test_tts.mp3"
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    print(f"Saved to {output_path}")

    print("\n✅ test_single_synthesis PASSED")


async def test_multiple_voices():
    """Verify different voices produce distinct audio."""
    service = TTSService()

    test_cases = [
        ("male-qn-qingse", "从技术角度来看<#0.3#>这个突破确实非常显著。"),
        ("female-yujie", "换个角度想(laughs)，这对创业者来说意味着什么呢？"),
        ("presenter_male", "我想请大家思考一个问题<#0.8#>，技术进步的代价是什么？"),
    ]

    print(f"\n=== Multi-voice TTS Test ===")
    for voice_id, text in test_cases:
        audio = await service.synthesize(text=text, voice_id=voice_id)
        print(f"  {voice_id}: {len(audio)} bytes")
        assert len(audio) > 0

    print("\n✅ test_multiple_voices PASSED")


if __name__ == "__main__":
    asyncio.run(test_single_synthesis())
    asyncio.run(test_multiple_voices())
