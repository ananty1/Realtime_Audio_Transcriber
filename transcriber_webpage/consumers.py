from channels.generic.websocket import AsyncWebsocketConsumer
from dotenv import load_dotenv

from deepgram import Deepgram 
from typing import Dict
import os 
load_dotenv()
import json 
import time


class TranscriptConsumer(AsyncWebsocketConsumer):
        dg_client = Deepgram(os.getenv('DEEPGRAM_API_KEY'))
        
        start_time = 0
        
        async def get_transcript(self, data: Dict) -> None:
            if 'channel' in data:
                transcript = data['channel']['alternatives'][0]['transcript']
                accuracy = data['channel']['alternatives'][0]['confidence']
                audio_time = data['start']+data['duration']

                if transcript:
                    latency = time.time()-audio_time-self.start_time

                    response_data = {
                        'transcript': transcript,
                        'accuracy': accuracy,
                        'latency':latency
                    }
                    response_json = json.dumps(response_data)
                    await self.send(response_json)


        async def connect_to_deepgram(self):
            try:
                self.start_time=time.time()
                connection_start = time.time()
                self.socket = await self.dg_client.transcription.live({'punctuate': True, 'interim_results': False})
                connection_end = time.time()
                connection_time= connection_end-connection_start
                print("Startime:",self.start_time,"connection time:",connection_time)
                self.start_time = self.start_time+connection_time
                print("Update start time",self.start_time)
                self.socket.registerHandler(self.socket.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
                self.socket.registerHandler(self.socket.event.TRANSCRIPT_RECEIVED, self.get_transcript)
                

            except Exception as e:
                raise Exception(f'Could not open socket: {e}')

        async def connect(self):
            await self.connect_to_deepgram()
            # self.room_group_name = "transcription_group"
            await self.accept()


        async def disconnect(self, close_code):
            # await self.channel_layer.group_discard(
            #     self.room_group_name,
            #     self.channel_name
            # )
            await self.close()

        async def receive(self, bytes_data):
            self.socket.send(bytes_data)