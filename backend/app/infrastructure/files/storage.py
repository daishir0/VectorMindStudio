from pathlib import Path
from app.core.config import settings

def get_base_storage_dir() -> Path:
    # The storage dir is relative to the backend directory
    backend_root = Path(__file__).parent.parent.parent
    return backend_root / settings.STORAGE_DIR

def get_originals_dir() -> Path:
    """オリジナルファイルを保存するディレクトリパスを取得"""
    path = get_base_storage_dir() / "originals"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_converted_dir() -> Path:
    """変換後ファイルを保存するディレクトリパスを取得"""
    path = get_base_storage_dir() / "converted"
    path.mkdir(parents=True, exist_ok=True)
    return path

def ensure_storage_dirs():
    """ストレージディレクトリが存在することを確認・作成する"""
    return get_originals_dir(), get_converted_dir()