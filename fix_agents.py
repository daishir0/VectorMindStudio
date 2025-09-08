#!/usr/bin/env python3
"""
エージェントクラスのOpenAI API呼び出しを修正するスクリプト
"""
import re
import os
from pathlib import Path

def fix_agent_file(file_path):
    """エージェントファイルのchat_completion呼び出しを修正"""
    print(f"修正中: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # chat_completionの呼び出しパターンを検索して置換
    patterns = [
        # パターン1: 複数行のchat_completion呼び出し
        (
            r'(\s+)(\w+)\s*=\s*await\s+openai_client\.chat_completion\(\s*\n\s*messages=\[\s*\n\s*\{[^}]+\},\s*\n\s*\{[^}]+\}\s*\n\s*\],\s*\n\s*model="([^"]+)",\s*\n\s*max_tokens=\d+,\s*\n\s*temperature=[\d.]+\s*\n\s*\)',
            lambda m: f'{m.group(1)}full_prompt = f"{{system_prompt}}\\n\\n{{user_prompt}}"\n{m.group(1)}result = await openai_client.generate_text(\n{m.group(1)}    prompt=full_prompt,\n{m.group(1)}    model="{m.group(3)}"\n{m.group(1)})\n{m.group(1)}{m.group(2)} = result.get("content", "")'
        ),
        # パターン2: 単純なchat_completion呼び出し
        (
            r'(\s+)(\w+)\s*=\s*await\s+openai_client\.chat_completion\(',
            lambda m: f'{m.group(1)}full_prompt = f"{{system_prompt}}\\n\\n{{user_prompt}}"\n{m.group(1)}result = await openai_client.generate_text(\n{m.group(1)}    prompt=full_prompt,\n{m.group(1)}    model="gpt-4o-mini"\n{m.group(1)})\n{m.group(1)}{m.group(2)} = result.get("content", "")'
        )
    ]
    
    modified = False
    for pattern, replacement in patterns:
        if callable(replacement):
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
        else:
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if new_content != content:
            content = new_content
            modified = True
    
    # より単純なアプローチ: chat_completionを含む行を手動で置換
    if 'chat_completion' in content:
        lines = content.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if 'await openai_client.chat_completion(' in line:
                # chat_completion呼び出しを発見
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                
                # 変数名を抽出
                var_match = re.search(r'(\w+)\s*=\s*await\s+openai_client\.chat_completion', line)
                if var_match:
                    var_name = var_match.group(1)
                    
                    # 置換行を生成
                    new_lines.append(f'{indent_str}full_prompt = f"{{system_prompt}}\\n\\n{{user_prompt}}"')
                    new_lines.append(f'{indent_str}result = await openai_client.generate_text(')
                    new_lines.append(f'{indent_str}    prompt=full_prompt,')
                    new_lines.append(f'{indent_str}    model="gpt-4o-mini"')
                    new_lines.append(f'{indent_str})')
                    new_lines.append(f'{indent_str}{var_name} = result.get("content", "")')
                    
                    # messages=... の部分をスキップ
                    while i + 1 < len(lines) and (')' not in lines[i + 1] or lines[i + 1].strip() == ')'):
                        i += 1
                    if i + 1 < len(lines) and ')' in lines[i + 1]:
                        i += 1  # 閉じ括弧の行もスキップ
                    
                    modified = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            i += 1
        
        if modified:
            content = '\n'.join(new_lines)
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"修正完了: {file_path}")
    else:
        print(f"修正不要: {file_path}")

def main():
    """メイン処理"""
    agent_files = [
        'backend/app/services/agents/reference_agent.py',
        'backend/app/services/agents/logic_validator_agent.py',
        'backend/app/services/agents/summary_agent.py',
        'backend/app/services/research_discussion_service.py'
    ]
    
    base_dir = Path('/home/ec2-user/hirashimallc/17_pj-VectorMindStudio/VectorMindStudio')
    
    for file_path in agent_files:
        full_path = base_dir / file_path
        if full_path.exists():
            fix_agent_file(full_path)
        else:
            print(f"ファイルが見つかりません: {full_path}")

if __name__ == '__main__':
    main()