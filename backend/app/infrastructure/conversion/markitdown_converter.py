import subprocess
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)

class MarkitdownConverter:
    """MarkItDownライブラリを使用してファイルをMarkdownに変換するクラス"""

    def __init__(self, markitdown_path: str = "markitdown"):
        self.markitdown_path = markitdown_path

    def convert(self, input_path: Path, output_dir: Path) -> Path:
        """
        指定されたファイルをMarkdownに変換する。

        Args:
            input_path: 変換するファイルのパス
            output_dir: 変換後のファイルを保存するディレクトリ

        Returns:
            変換後のMarkdownファイルのパス

        Raises:
            Exception: 変換に失敗した場合
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        output_dir.mkdir(parents=True, exist_ok=True)

        # markitdownコマンドの実行
        # markitdown <input_file> -o <output_file>
        expected_output_filename = f"{input_path.name}.md"
        output_file = output_dir / expected_output_filename
        command = [self.markitdown_path, str(input_path), "-o", str(output_file)]

        try:
            logger.info(f"Running markitdown conversion: {' '.join(command)}")
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5分でタイムアウト
            )
            logger.info(f"Markitdown output: {result.stdout}")

            # 出力ファイルが存在するか確認
            if not output_file.exists():
                # 出力ファイルが見つからない場合、stdoutから探す
                # 例: "Successfully converted test.pdf to /path/to/output/test.pdf.md"
                output_path_from_log = self._find_path_in_logs(result.stdout, output_dir)
                if output_path_from_log and output_path_from_log.exists():
                    return output_path_from_log
                raise FileNotFoundError(f"Conversion successful, but output file not found at {output_file}")

            return output_file

        except FileNotFoundError:
            logger.error("markitdown command not found. Make sure it is installed and in the system's PATH.")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Markitdown conversion failed with exit code {e.returncode}")
            logger.error(f"Stderr: {e.stderr}")
            raise Exception(f"Markdown conversion failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("Markitdown conversion timed out.")
            raise Exception("Markdown conversion timed out.")

    def _find_path_in_logs(self, logs: str, output_dir: Path) -> Path | None:
        """ログから出力ファイルパスを抽出する"""
        # "Successfully converted ... to [path]" のようなログを想定
        match = re.search(r"to\s+([\/\w.-]+)", logs)
        if match:
            path_str = match.group(1)
            # パスが絶対パスでない場合、出力ディレクトリを基準にする
            if not path_str.startswith('/'):
                return output_dir / path_str
            return Path(path_str)
        return None