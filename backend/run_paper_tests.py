#!/usr/bin/env python3
"""
論文執筆機能のテスト実行スクリプト
"""
import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """論文執筆機能のテストを実行"""
    
    # カレントディレクトリをバックエンドルートに設定
    backend_root = Path(__file__).parent
    os.chdir(backend_root)
    
    print("🧪 論文執筆機能のテスト開始")
    print("=" * 50)
    
    # テストファイル一覧
    test_files = [
        "tests/test_paper_repository.py",
        "tests/test_agents.py", 
        "tests/test_papers_api.py",
        "tests/test_paper_integration.py"
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_files = []
    
    for test_file in test_files:
        print(f"\n📝 実行中: {test_file}")
        print("-" * 30)
        
        try:
            # pytestを実行
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file,
                "-v",
                "--tb=short",
                "--disable-warnings"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {test_file}: 成功")
                # 成功したテストの数を数える（概算）
                output_lines = result.stdout.split('\n')
                passed_count = len([line for line in output_lines if '::' in line and 'PASSED' in line])
                total_tests += passed_count
                passed_tests += passed_count
            else:
                print(f"❌ {test_file}: 失敗")
                print(f"エラー出力:\n{result.stdout}\n{result.stderr}")
                failed_files.append(test_file)
                # 失敗したテストも総数にカウント
                output_lines = result.stdout.split('\n')
                test_count = len([line for line in output_lines if '::' in line and ('PASSED' in line or 'FAILED' in line)])
                total_tests += test_count
                
        except Exception as e:
            print(f"❌ {test_file}: 実行エラー - {e}")
            failed_files.append(test_file)
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("🎯 テスト結果サマリー")
    print("=" * 50)
    print(f"総テスト数: {total_tests}")
    print(f"成功: {passed_tests}")
    print(f"失敗: {total_tests - passed_tests}")
    
    if failed_files:
        print(f"\n❌ 失敗したテストファイル:")
        for file in failed_files:
            print(f"  - {file}")
        return False
    else:
        print("\n🎉 全てのテストが成功しました!")
        return True

def check_dependencies():
    """必要な依存関係をチェック"""
    print("🔍 依存関係チェック中...")
    
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "httpx",
        "sqlalchemy",
        "fastapi"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 不足しているパッケージ: {', '.join(missing_packages)}")
        print("以下のコマンドでインストールしてください:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 全ての依存関係が満たされています")
    return True

def main():
    """メイン関数"""
    print("📚 VectorMindStudio 論文執筆機能 テストスイート")
    print("=" * 60)
    
    # 依存関係チェック
    if not check_dependencies():
        sys.exit(1)
    
    # テスト実行
    success = run_tests()
    
    if success:
        print("\n✨ 論文執筆機能のテストが全て完了しました!")
        print("🚀 PRの準備ができています!")
        sys.exit(0)
    else:
        print("\n💥 一部のテストが失敗しました")
        print("🔧 エラーを修正してから再実行してください")
        sys.exit(1)

if __name__ == "__main__":
    main()