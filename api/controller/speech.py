import os
from typing import List
import tempfile

from fastapi import FastAPI
from pydantic import BaseModel
import concurrent.futures

from api.data.client import SpeechDatabaseClient, AudioSegmentDatabaseClient
from api.data.shortcuts import get_object_or_404
from api.data.tables import Speech, AudioSegment
from api.data.enums import AnalysisRecordType

from api.service.analysis_record import AnalysisRecordService

from api.service.aws.s3 import S3Service
from api.service.ffmpeg_service import merge_webm_files_to_wav, wav_to_mp3
from api.service.clova_service import clova_stt_send
from api.service.audio_analysis_service import (
    get_db_analysis,
    get_f0_analysis,
)

app = FastAPI()


speech_db_client = SpeechDatabaseClient()
audio_segment_db_client = AudioSegmentDatabaseClient()

analysis_record_service = AnalysisRecordService()
s3_service = S3Service()


class Analysis1(BaseModel):
    """
    ## 클로바로 넘겨줄 값
    callback_url : stt 결과를 전송할 dalcom endpoint
    download_url : stt 입력 파일이 저장된 object의 presigned url
    ## wasak에서 쓸 값
    upload_key : wasak에서 합친 오디오 파일(full audio)을 업로드할 key @
    """

    callback_url: str
    upload_key: str
    download_url: str


@app.post("/{speech_id}/analysis-1")
def trigger_analysis_1(speech_id: int, dto: Analysis1):
    """
    ## STT 결과가 필요 없는 음성 분석 수행
    1. DB에서 speech_id에 물려있는 audio_segments의 S3 경로들을 가져온다.
    2. S3에서 해당 경로들의 파일들을 다운로드한다.
    3. 해당 파일들을 wav로 합친다.
    4-1. Clova에 STT Request를 보낸다. (용량 최적화를 위해 추후 mp3로 보내야 할 수도 있음.)
    4-2. wav파일로 dB Analysis
        4-2-1. 결과 DB 저장
    4-3. wav파일로 f0 Analysis
        4-3-1. 결과 DB 저장
    4-4. wav -> mp3 변환
        4-4-1. 변환된 mp3파일 S3 업로드
        4-4-2. 변환된 mp3파일 삭제
    5. 모든 작업 후 wav 파일 삭제
    """
    # 1. DB에서 speech_id에 물려있는 audio_segments의 S3 경로들을 가져온다.
    target_speech: Speech = get_object_or_404(
        speech_db_client, [Speech.id.bool_op("=")(speech_id)]
    )

    audio_segments: List[
        AudioSegment
    ] = audio_segment_db_client.select_audio_segments_of(target_speech)

    # 2. S3에서 해당 경로들의 파일들을 다운로드한다.
    audio_segment_file_paths = []
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        for audio_segment in audio_segments:
            key = audio_segment.get_key()
            file_path = os.path.join(tmp_dir_path, key)
            audio_segment_file_paths.append(file_path)

            s3_service.download_object(audio_segment.get_full_path(), file_path)

        # key의 맨 앞자리에 timestamp가 들어 있으므로 정렬함
        audio_segment_file_paths.sort()

        # 3. 해당 파일들을 wav로 합친다.
        merged_wav_file_path = merge_webm_files_to_wav(audio_segment_file_paths)

    # 직렬 작업 필요한 것들 하나의 함수로 wrapping
    def db_analysis_and_save_db():
        result = get_db_analysis(merged_wav_file_path)
        analysis_record_service.save_analysis_result(
            target_speech, AnalysisRecordType.DECIBEL, result
        )

    def f0_analysis_and_save_db():
        result = get_f0_analysis(merged_wav_file_path)
        analysis_record_service.save_analysis_result(
            target_speech, AnalysisRecordType.HERTZ, result
        )

    def convert_wav_to_mp3_and_upload_s3_and_remove_mp3():
        mp3_path = wav_to_mp3(merged_wav_file_path)
        s3_service.upload_object(mp3_path, dto.upload_key)
        mp3_path.unlink()

    clova_stt_send(merged_wav_file_path, dto.callback_url)
    print("STT done")

    result = get_db_analysis(merged_wav_file_path)
    analysis_record_service.save_analysis_result(
        target_speech, AnalysisRecordType.DECIBEL, result
    )
    print("DECIBEL done")

    result = get_f0_analysis(merged_wav_file_path)
    analysis_record_service.save_analysis_result(
        target_speech, AnalysisRecordType.HERTZ, result
    )

    print("HERTZ done")

    mp3_path = wav_to_mp3(merged_wav_file_path)
    s3_service.upload_object(mp3_path, dto.upload_key)
    mp3_path.unlink()

    print("Mp3 Upload done")

    merged_wav_file_path.unlink()

    # with concurrent.futures.ProcessPoolExecutor() as executor:
    #     futures = {
    #         # 4-1. Clova에 STT Request를 보낸다.
    #         executor.submit(clova_stt_send, merged_wav_file_path, dto.callback_url),
    #         # 4-2. wav파일로 dB Analysis 후 DB 저장
    #         executor.submit(db_analysis_and_save_db),
    #         # 4-3. wav파일로 f0 Analysis 후 DB 저장
    #         executor.submit(f0_analysis_and_save_db),
    #         # 4-4. wav -> mp3 변환, S3에 업로드 후 삭제
    #         executor.submit(convert_wav_to_mp3_and_upload_s3_and_remove_mp3),
    #     }

    #     # FIXME: 비동기 결과로 수행할 작업 있으면 아래 코드 사용, 없으면 삭제 요망
    #     # for future in concurrent.futures.as_completed(futures):
    #     #     print(future.result())  # or store the result, handle exceptions, etc.

    #     # 5. 모든 작업 후 wav 파일 삭제
    #     merged_wav_file_path.unlink()


@app.post("/{speech_id}/analysis-2")
def trigger_analysis_2():
    return None
