from pathlib import Path
from typing import List
import tempfile

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from api.data.client import SpeechDatabaseClient, AudioSegmentDatabaseClient
from api.data.shortcuts import get_object_or_404
from api.data.tables import Speech, AudioSegment
from api.data.enums import AnalysisRecordType

from api.service.analysis_record import AnalysisRecordService

from api.service.aws.s3 import S3Service
from api.service.speech import SpeechService
from api.service.ffmpeg_service import (
    merge_webm_files_binary_concat,
    wav_to_mp3,
    webm_to_wav,
)
from api.service.clova_service import clova_stt_send
from api.service.audio_analysis_service import (
    get_db_analysis,
    get_f0_analysis,
)
from api.service.stt_analysis_service import (
    get_average_lpm,
    get_lpm_by_sentence,
    get_ptl_ratio,
    get_ptl_by_sentence,
)

app = FastAPI()


speech_db_client = SpeechDatabaseClient()
audio_segment_db_client = AudioSegmentDatabaseClient()

analysis_record_service = AnalysisRecordService()
s3_service = S3Service()
speech_service = SpeechService()


class Analysis1Dto(BaseModel):
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


def analysis1_async_wrapper(presentation_id: int, speech_id: int, dto: Analysis1Dto):
    """
    ## STT 결과가 필요 없는 음성 분석 수행
    1. DB에서 speech_id에 물려있는 audio_segments의 S3 경로들을 가져온다.
    2. S3에서 해당 경로들의 파일들을 다운로드한다.
    3. 해당 파일들을 wav로 합친다.
    4-1. Clova에 STT Request를 보낸다. (용량 최적화를 위해 추후 mp3로 보내야 할 수도 있음.)
    4-2. wav파일로 f0 Analysis
    4-3. wav파일로 dB Analysis
    4-4. wav -> mp3 변환
        4-4-1. 변환된 mp3파일 S3 업로드
        4-4-2. 변환된 mp3파일 삭제
    5. 모든 작업 후 wav 파일 삭제
    """

    try:
        # tempfile 라이브러리 사용, pathlib로 경로 관리
        tmp_dir_context = tempfile.TemporaryDirectory()
        tmp_dir_path = Path(tmp_dir_context.name)

        # 1. DB에서 speech_id에 물려있는 audio_segments의 S3 경로들을 가져온다.
        target_speech: Speech = get_object_or_404(
            speech_db_client,
            [
                Speech.presentation_id.bool_op("=")(presentation_id),
                Speech.id.bool_op("=")(speech_id),
            ],
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

        # 3. 해당 파일들을 하나의 webm으로 합친 후에 wav로 변환
        merged_webm_file_path = merge_webm_files_binary_concat(audio_segment_file_paths)
        target_wav_file_path = webm_to_wav(merged_webm_file_path)
        merged_webm_file_path.unlink()

        # 4. 병합된 wav 파일을 mp3로 변환하여 S3에 업로드한다.
        mp3_path = wav_to_mp3(target_wav_file_path)
        url = s3_service.upload_object(mp3_path, dto.upload_key)
        full_audio_path = dto.download_url.split("?")[0]
        speech_service.update_full_audio_s3_url(target_speech, full_audio_path)
        mp3_path.unlink()

        # 4-2. wav파일로 f0(Hz) Analysis
        result = get_f0_analysis(target_wav_file_path)
        analysis_record_service.save_analysis_result(
            presentation_id, speech_id, AnalysisRecordType.HERTZ, result
        )

        # 4-3. wav파일로 dB Analysis
        result = get_db_analysis(target_wav_file_path)
        analysis_record_service.save_analysis_result(
            presentation_id, speech_id, AnalysisRecordType.DECIBEL, result
        )

        success = clova_stt_send(dto.download_url, dto.callback_url)
        if not success:
            raise Exception("STT Failed")

        # 5. 모든 작업 후 wav 파일 삭제
        target_wav_file_path.unlink()

    except Exception as e:
        # TODO: Advanced error handling
        print("Error Occurred: ", (e))
        print(e.__traceback__)

    finally:
        tmp_dir_context.cleanup()


@app.post("/{presentation_id}/speech/{speech_id}/analysis-1")
def trigger_analysis_1(
    presentation_id: int,
    speech_id: int,
    dto: Analysis1Dto,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(analysis1_async_wrapper, presentation_id, speech_id, dto)
    return "success"


def analysis2_async_wrapper(presentation_id: int, speech_id: int):
    """
    ## STT 결과가 필요한 음성 분석 수행
    1. S3에서 p.id / s.id로 STT 결과 json을 받아온다.
    2-1. 휴지 분석 수행
    2-2. LPM 분석 수행
    """
    # 1. S3에서 p.id / s.id로 STT 결과 json을 받아온다.
    stt_key = f"{presentation_id}/{speech_id}/analysis/STT.json"
    stt_script = s3_service.download_json_object(stt_key)

    # 2. STT 결과를 kiwi를 이용하여 문장 별로 분할하여 재조합한다.
    concatenated_script = speech_service.get_aligned_script(stt_script)
    analysis_record_service.save_analysis_result(
        presentation_id, speech_id, AnalysisRecordType.STT, concatenated_script
    )

    # 3-1. 휴지 분석 수행
    result = get_ptl_by_sentence(concatenated_script)
    analysis_record_service.save_analysis_result(
        presentation_id, speech_id, AnalysisRecordType.PAUSE, result
    )
    print("[LOG] 3-1. 휴지 분석 수행 완료")

    # 3-2. LPM 분석 수행
    result = get_lpm_by_sentence(concatenated_script)
    analysis_record_service.save_analysis_result(
        presentation_id, speech_id, AnalysisRecordType.LPM, result
    )
    print("[LOG] 3-2. LPM 분석 수행 완료")

    # 3-3. Average 휴지 (PTL) 분석 수행
    result = get_ptl_ratio(concatenated_script)
    analysis_record_service.save_analysis_result(
        presentation_id, speech_id, AnalysisRecordType.PAUSE_RATIO, result
    )
    print("[LOG] 3-3. Average 휴지 (PTL) 분석 수행 완료")

    # 3-4. Average LPM 분석 수행
    result = get_average_lpm(concatenated_script)
    analysis_record_service.save_analysis_result(
        presentation_id, speech_id, AnalysisRecordType.LPM_AVG, result
    )

    print("[LOG] 3-4. Average LPM 분석 수행 완료")


@app.post("/{presentation_id}/speech/{speech_id}/analysis-2")
def trigger_analysis_2(
    presentation_id: int, speech_id: int, background_tasks: BackgroundTasks
):
    background_tasks.add_task(analysis2_async_wrapper, presentation_id, speech_id)
    return "success"
