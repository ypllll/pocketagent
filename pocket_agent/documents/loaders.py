"""
现在写的loader文件，是文档解析，是RAG流水线的第一步，要把PDF/TXT/MD文件变成纯文本
"""

from pathlib import Path
from pypdf import PdfReader
TEXT_SUFFIXES = [".txt", ".md"]
PDF_SUFFIX = [".pdf"]

def load_text_file(path:Path)->str:
    p=Path(path)
    return p.read_text(encoding="utf-8")
   
def load_pdf(path:Path)->str:
    p=Path(path)
    reader=PdfReader(path)
    content=[]
    for i,page in enumerate(reader.pages):
        text=page.extract_text()
        if not text:
            content.append(f"第{i+1}页：内容是图片版")
        else:
            content.append(f"第{i+1}页：{text}")
    return "\n".join(content)


def load_document(path:str|Path)->str:
    p=Path(path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在，文件路径：{p}")
    if p.suffix.lower() in TEXT_SUFFIXES:
        return load_text_file(p)
    if p.suffix.lower() in PDF_SUFFIX:
        return load_pdf(p)
    raise ValueError(f"不支持的文件类型，仅支持{TEXT_SUFFIXES + PDF_SUFFIX}，文件路径：{p}")
    
            
