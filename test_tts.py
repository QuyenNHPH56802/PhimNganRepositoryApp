import asyncio
import sys
sys.path.insert(0, 'apps/api/python')

from translator_api.providers.tts.edge import EdgeTtsProvider
from translator_api.providers.tts.base import TtsInput, TtsProviderConfig
from translator_api.providers.base import ProviderContext
from translator_api.storage_pkg.local import LocalStorage

async def test():
    storage = LocalStorage()
    ctx = ProviderContext(project_id='test', storage=storage)
    provider = EdgeTtsProvider()
    inp = TtsInput(
        text='Xin chào',
        voice_profile_id='vi-VN-HoaiMyNeural',
        output_storage_prefix='test',
        config=TtsProviderConfig(voice_id='vi-VN-HoaiMyNeural')
    )
    try:
        result = await provider.run(inp, ctx=ctx)
        print(f'Success: {result.audio_storage_key}')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(test())
