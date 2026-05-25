import os
import hashlib
import shutil
from pathlib import Path


def parse_resume(file_path: str, file_ext: str) -> str:
    """解析简历文件，提取文本内容"""
    file_ext = file_ext.lower()

    if file_ext == ".txt":
        return _parse_txt(file_path)
    elif file_ext == ".pdf":
        return _parse_pdf(file_path)
    elif file_ext in [".doc", ".docx"]:
        return _parse_doc(file_path)
    else:
        return f"不支持的文件格式: {file_ext}，请上传 TXT、PDF 或 Word 文件"


def _parse_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_pdf(file_path: str) -> str:
    """解析 PDF 文件"""
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except ImportError:
            return "PDF 解析库未安装，请安装 pypdf 或 PyPDF2"

    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def _parse_doc(file_path: str) -> str:
    """解析 Word 文件"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text.strip()
    except ImportError:
        return "Word 解析库未安装，请安装 python-docx"


async def save_upload_file(upload_file, upload_dir: str = "uploads/resumes") -> tuple[str, str]:
    """保存上传文件，返回 (文件路径, 文件扩展名)"""
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    # 用 MD5 避免中文文件名问题
    file_ext = Path(upload_file.filename).suffix.lower()
    safe_name = hashlib.md5(upload_file.filename.encode()).hexdigest() + file_ext
    file_path = upload_path / safe_name

    # UploadFile 是异步文件，需要用异步方式读取
    with open(file_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)

    return str(file_path), file_ext