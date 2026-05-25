import os
import hashlib
import asyncio
import subprocess
import shutil
from pathlib import Path


class DigitalHumanService:
    """数字人播报服务"""

    def __init__(self):
        self.video_output_dir = "static/videos"
        self.audio_output_dir = "static/audio"
        self.avatar_output_dir = "static/avatars"
        os.makedirs(self.video_output_dir, exist_ok=True)
        os.makedirs(self.audio_output_dir, exist_ok=True)
        os.makedirs(self.avatar_output_dir, exist_ok=True)

        # TTS 配置
        self.edge_tts_available = self._check_edge_tts()

        # 检查 ffmpeg
        self.ffmpeg_available = self._check_ffmpeg()

        # 默认 Avatar（如果用户没有上传）
        self.default_avatar = os.path.join(self.avatar_output_dir, "default_avatar.png")

        # 如果默认头像不存在，创建一个简单的灰色 placeholder
        if not os.path.exists(self.default_avatar):
            self._create_default_avatar()

    def _check_edge_tts(self) -> bool:
        try:
            import edge_tts
            return True
        except ImportError:
            return False

    def _check_ffmpeg(self) -> bool:
        """检查 ffmpeg 是否可用"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _create_default_avatar(self):
        """创建默认头像占位符"""
        try:
            # 使用 PIL 创建简单灰色圆形头像
            from PIL import Image, ImageDraw

            size = 512
            img = Image.new('RGB', (size, size), color=(200, 200, 200))
            draw = ImageDraw.Draw(img)

            # 画一个简单的圆形代表头部
            draw.ellipse([128, 64, 384, 320], fill=(150, 150, 150))

            # 画身体
            draw.ellipse([64, 320, 448, 480], fill=(100, 100, 100))

            img.save(self.default_avatar)
        except ImportError:
            # 如果没有 PIL，创建一个空文件
            with open(self.default_avatar, 'wb') as f:
                f.write(b'')

    async def generate_video(self, text: str, avatar: str = "default") -> str:
        """
        生成数字人播报视频
        流程: TTS -> 音频 -> Wav2Lip/FFmpeg -> 视频
        """
        # 1. TTS 合成音频
        audio_path = await self._tts(text)
        if not audio_path or not os.path.exists(audio_path):
            return ""

        # 2. 获取 Avatar 路径
        avatar_path = self._get_avatar_path(avatar)
        if not avatar_path or not os.path.exists(avatar_path):
            # 如果没有有效 avatar，返回音频文件路径（前端可播放音频）
            return audio_path

        # 3. 生成视频
        video_path = await self._generate_video_with_ffmpeg(avatar_path, audio_path)

        return video_path if video_path else audio_path

    def _get_avatar_path(self, avatar: str) -> str:
        """获取 Avatar 文件路径"""
        if avatar == "default" or not avatar:
            return self.default_avatar

        # 检查是否是用户上传的 avatar
        user_avatar = os.path.join(self.avatar_output_dir, f"{avatar}.png")
        if os.path.exists(user_avatar):
            return user_avatar

        return self.default_avatar

    async def _tts(self, text: str) -> str:
        """文字转语音"""
        safe_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        audio_file = f"{self.audio_output_dir}/tts_{safe_hash}.mp3"

        if os.path.exists(audio_file):
            return audio_file

        try:
            if self.edge_tts_available:
                return await self._edge_tts(text, audio_file)
            else:
                return await self._edge_tts_subprocess(text, audio_file)
        except Exception as e:
            print(f"TTS 生成失败: {e}")
            return ""

    async def _edge_tts(self, text: str, output_file: str) -> str:
        """使用 edge-tts 库"""
        import edge_tts

        # 清理标点符号，避免 TTS 朗读标点
        clean_text = self._clean_text_for_tts(text)

        communicate = edge_tts.Communicate(clean_text, voice="zh-CN-XiaoxiaoNeural")
        await communicate.save(output_file)
        return output_file

    def _clean_text_for_tts(self, text: str) -> str:
        """清理文本中的标点符号，避免 TTS 朗读"""
        import re
        # 移除标点符号，edge-tts 默认不会读这些
        punct_to_remove = '，。？！：；""''（）【】《》、|·~@#$%^&*+=<>/\\'
        for p in punct_to_remove:
            text = text.replace(p, '')
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    async def _edge_tts_subprocess(self, text: str, output_file: str) -> str:
        """通过 subprocess 调用 edge-tts"""
        try:
            result = subprocess.run(
                ["edge-tts", "--text", text, "--write-media", output_file, "--voice", "zh-CN-XiaoxiaoNeural"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and os.path.exists(output_file):
                return output_file
        except Exception as e:
            print(f"edge-tts subprocess failed: {e}")
        return ""

    async def _generate_video_with_ffmpeg(
        self,
        avatar_path: str,
        audio_path: str
    ) -> str:
        """
        使用 ffmpeg 生成视频（静态图 + 音频）
        如果有 Wav2Lip，会尝试使用 Wav2Lip
        """
        if not self.ffmpeg_available:
            print("ffmpeg 不可用，无法生成视频")
            return ""

        safe_hash = hashlib.md5(audio_path.encode()).hexdigest()[:8]
        video_file = f"{self.video_output_dir}/video_{safe_hash}.mp4"

        if os.path.exists(video_file):
            return video_file

        try:
            # 使用 ffmpeg 将静态图和音频合成为视频
            # -loop 1: 循环图片
            # -i avatar: 输入图片
            # -i audio: 输入音频
            # -c:v libx264: H.264 编码
            # -tune stillimage: 优化静态图像
            # -c:a aac: 音频编码
            # -shortest: 使用最短的时长（音频）
            # -pix_fmt yuv420p: 兼容性子啊

            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", avatar_path,
                "-i", audio_path,
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-pix_fmt", "yuv420p",
                "-vf", "scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2",
                video_file
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode == 0 and os.path.exists(video_file):
                return video_file
            else:
                print(f"ffmpeg 错误: {result.stderr}")
                return ""

        except Exception as e:
            print(f"视频生成失败: {e}")
            return ""

    async def _run_wav2lip(
        self,
        avatar_path: str,
        audio_path: str,
        output_path: str
    ) -> bool:
        """
        运行 Wav2Lip 生成视频（如果可用）
        需要先安装 Wav2Lip 和模型
        """
        # 检查是否有 Wav2Lip 命令
        try:
            result = subprocess.run(
                ["python", "-c", "import wav2lip"],
                capture_output=True,
                text=True,
                timeout=5
            )
            has_wav2lip = result.returncode == 0
        except Exception:
            has_wav2lip = False

        if not has_wav2lip:
            # 尝试调用 wav2lip 相关命令
            # 这需要用户已经正确安装了 Wav2Lip
            pass

        return False

    async def generate_audio_only(self, text: str) -> str:
        """仅生成音频（用于流式播报）"""
        return await self._tts(text)

    async def upload_avatar(self, file_content: bytes, filename: str) -> str:
        """上传 Avatar 图片"""
        safe_name = hashlib.md5(filename.encode()).hexdigest()[:8]
        ext = os.path.splitext(filename)[1].lower() or ".png"
        avatar_path = os.path.join(self.avatar_output_dir, f"{safe_name}{ext}")

        with open(avatar_path, 'wb') as f:
            f.write(file_content)

        return safe_name  # 返回 avatar ID