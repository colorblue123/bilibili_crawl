import os
from funasr import AutoModel
import ffmpeg
from datetime import timedelta, datetime


class ConvertText:

    def __init__(self):
        home_directory = os.getcwd()
        asr_model_path = os.path.join(home_directory, "modelscope", "hub", "iic",
                                      "speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch")
        asr_model_revision = "v2.0.4"
        vad_model_path = os.path.join(home_directory, "modelscope", "hub", "iic",
                                      "speech_fsmn_vad_zh-cn-16k-common-pytorch")
        vad_model_revision = "v2.0.4"
        punc_model_path = os.path.join(home_directory, "modelscope", "hub", "iic",
                                       "punc_ct-transformer_zh-cn-common-vocab272727-pytorch")
        punc_model_revision = "v2.0.4"
        spk_model_path = os.path.join(home_directory, "modelscope", "hub", "iic",
                                      "speech_campplus_sv_zh-cn_16k-common")
        spk_model_revision = "v2.0.4"
        ngpu = 1
        device = "cuda"
        ncpu = 4
        # 初始化模型
        self.model = AutoModel(
            model=asr_model_path,
            model_revision=asr_model_revision,
            vad_model=vad_model_path,
            vad_model_revision=vad_model_revision,
            punc_model=punc_model_path,
            punc_model_revision=punc_model_revision,
            spk_model=spk_model_path,
            spk_model_revision=spk_model_revision,
            ngpu=ngpu,
            ncpu=ncpu,
            device=device,
            disable_pbar=True,
            disable_log=True,
            disable_update=True
        )

    def to_date(self, milliseconds):
        """将时间戳转换为SRT格式的时间"""
        time_obj = timedelta(milliseconds=milliseconds)
        return f"{time_obj.seconds // 3600:02d}:{(time_obj.seconds // 60) % 60:02d}:{time_obj.seconds % 60:02d}.{time_obj.microseconds // 1000:03d}"

    def to_milliseconds(self, time_str):
        time_obj = datetime.strptime(time_str, "%H:%M:%S.%f")
        time_delta = time_obj - datetime(1900, 1, 1)
        milliseconds = int(time_delta.total_seconds() * 1000)
        return milliseconds

    def transcribe_audio(self, audio_path):
        """转写音频文件为文字"""
        try:
            # 音频预处理
            audio_bytes, _ = (
                ffmpeg.input(audio_path, threads=0, hwaccel='cuda')
                .output("-", format="wav", acodec="pcm_s16le", ac=1, ar=16000)
                .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
            )
            # 语音识别
            res = self.model.generate(input=audio_bytes, batch_size_s=300, is_final=True, sentence_timestamp=True)
            rec_result = res[0]
            asr_result_text = rec_result['text']  # 完整转写文本
            sentences = []

            # 处理句子信息
            for sentence in rec_result["sentence_info"]:
                start = self.to_date(sentence["start"])  # 开始时间
                end = self.to_date(sentence["end"])  # 结束时间
                text = sentence["text"]  # 句子文本

                if sentences:
                    # 合并相同说话人的句子
                    sentences[-1]["text"] += " " + text
                    sentences[-1]["end"] = end
                else:
                    # 添加新句子
                    sentences.append({"text": text, "start": start, "end": end})

            return asr_result_text, sentences
        except Exception as e:
            print(f"转写失败: {e}")
            return None, None


