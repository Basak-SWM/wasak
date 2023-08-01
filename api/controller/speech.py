import os
from pathlib import Path
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

    # ==========================================================================================
    # WARNING : STT 실행 결과 확인을 위해 임시로 STT까지만 동기 방식으로 실행되도록 함
    # TODO : @Poxios가 비동기 로직 구현 완료하면, 아래 부분 삭제하고 아래 주석 처리된 부분을 수행하는 코드로 대체할 것!
    # ==========================================================================================

    try:
        # tempfile 라이브러리 사용, pathlib로 경로 관리
        tmp_dir_context = tempfile.TemporaryDirectory()
        tmp_dir_path = Path(tmp_dir_context.name)

        # 1. DB에서 speech_id에 물려있는 audio_segments의 S3 경로들을 가져온다.
        target_speech: Speech = get_object_or_404(
            speech_db_client, [Speech.id.bool_op("=")(speech_id)]
        )

        audio_segments: List[
            AudioSegment
        ] = audio_segment_db_client.select_audio_segments_of(target_speech)

        # 2. S3에서 해당 경로들의 파일들을 다운로드한다.
        audio_segment_file_paths = []

        for audio_segment in audio_segments:
            key = audio_segment.get_key()
            file_path = tmp_dir_path / key
            audio_segment_file_paths.append(str(file_path))
            s3_service.download_object(audio_segment.get_full_path(), file_path)

        # key의 맨 앞자리에 timestamp가 들어 있으므로 정렬함
        audio_segment_file_paths.sort()

        # 3. 해당 파일들을 wav로 합친다.
        merged_wav_file_path = merge_webm_files_to_wav(audio_segment_file_paths)

        # 4. 병합된 wav 파일을 mp3로 변환하여 S3에 업로드한다.
        mp3_path = wav_to_mp3(merged_wav_file_path)
        s3_service.upload_object(mp3_path, dto.upload_key)
        mp3_path.unlink()

        # 직렬 작업 필요한 것들 하나의 함수로 wrapping
        success = clova_stt_send(dto.download_url, dto.callback_url)
        if not success:
            raise Exception("STT Failed")

        # TODO : 분석 시작

        # 5. 모든 작업 후 wav 파일 삭제
        merged_wav_file_path.unlink()
        result = True

    except Exception as e:
        # TODO: Advanced error handling
        print("Error Occurred: ", (e))
        print(e.__traceback__)

    finally:
        tmp_dir_context.cleanup()
        return result
    # ==========================================================================================

    def async_wrapper(executor):
        try:
            # tempfile 라이브러리 사용, pathlib로 경로 관리
            tmp_dir_context = tempfile.TemporaryDirectory()
            tmp_dir_path = Path(tmp_dir_context.name)

            # 1. DB에서 speech_id에 물려있는 audio_segments의 S3 경로들을 가져온다.
            target_speech: Speech = get_object_or_404(
                speech_db_client, [Speech.id.bool_op("=")(speech_id)]
            )

            audio_segments: List[
                AudioSegment
            ] = audio_segment_db_client.select_audio_segments_of(target_speech)

            # 2. S3에서 해당 경로들의 파일들을 다운로드한다.
            audio_segment_file_paths = []

            for audio_segment in audio_segments:
                key = audio_segment.get_key()
                file_path = tmp_dir_path / key
                audio_segment_file_paths.append(str(file_path))
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
                return True

            def f0_analysis_and_save_db():
                result = get_f0_analysis(merged_wav_file_path)
                analysis_record_service.save_analysis_result(
                    target_speech, AnalysisRecordType.HERTZ, result
                )
                return True

            def convert_wav_to_mp3_and_upload_s3_and_remove_mp3():
                mp3_path = wav_to_mp3(merged_wav_file_path)
                s3_service.upload_object(mp3_path, dto.upload_key)
                mp3_path.unlink()
                return True

            futures = {
                # 4-1. Clova에 STT Request를 보낸다.
                executor.submit(clova_stt_send, merged_wav_file_path, dto.callback_url),
                # 4-2. wav파일로 dB Analysis 후 DB 저장
                executor.submit(db_analysis_and_save_db),
                # 4-3. wav파일로 f0 Analysis 후 DB 저장
                executor.submit(f0_analysis_and_save_db),
                # 4-4. wav -> mp3 변환, S3에 업로드 후 삭제
                executor.submit(convert_wav_to_mp3_and_upload_s3_and_remove_mp3),
            }
            concurrent.futures.wait(futures)

            # 5. 모든 작업 후 wav 파일 삭제
            merged_wav_file_path.unlink()
            result = True

        except Exception as e:
            # TODO: Advanced error handling
            print("Error Occurred: ", (e))

        finally:
            tmp_dir_context.cleanup()
            return result

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(async_wrapper, executor)
    return "success"


@app.post("/{speech_id}/analysis-2")
def trigger_analysis_2():
    return None
