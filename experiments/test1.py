import subprocess
import sys

# Ultra-simple subprocess approach
def subprocess_tts(text, voice="en-US-JennyNeural", filename="output.mp3"):
    script = f'''
import asyncio
import edge_tts
import platform

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def main():
    communicate = edge_tts.Communicate("{text}", "{voice}")
    await communicate.save("{filename}")
    print("Success!")

asyncio.run(main())
'''
    
    try:
        result = subprocess.run([sys.executable, "-c", script], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Generated: {filename}")
        else:
            print(f"❌ Error: {result.stderr}")
    except Exception as e:
        print(f"❌ Exception: {e}")

# Test it
subprocess_tts("Hello world!Hello world! Hello world! Hello world! Hello world!", filename="subprocess_test.mp3")


'''
communicate = edge_tts.Communicate(text, "en-US-JennyNeural")  # Friendly female
communicate = edge_tts.Communicate(text, "en-US-GuyNeural")    # Warm male
communicate = edge_tts.Communicate(text, "en-GB-LibbyNeural")  # British female
communicate = edge_tts.Communicate(text, "en-AU-NatashaNeural") # Australian female


communicate = edge_tts.Communicate(text, "fr-FR-DeniseNeural")  # French female
communicate = edge_tts.Communicate(text, "es-ES-ElviraNeural")  # Spanish female
communicate = edge_tts.Communicate(text, "de-DE-KatjaNeural")   # German female
communicate = edge_tts.Communicate(text, "ja-JP-NanamiNeural")  # Japanese female
communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural") # Chinese female
'''