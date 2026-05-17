#!/usr/bin/env python3
import os
import glob
import gzip
import sys
import re
from datetime import datetime

def parse_history_log(subcommand):

    log_dir = "/var/log/apt"
    log_files = glob.glob(os.path.join(log_dir, "history.log*"))
    
    log_files.sort(key=lambda x: (not x.endswith('log'), x), reverse=True)
    
    parsed_lines = []

    for file_path in log_files:
        try:
            if file_path.endswith('.gz'):
                f = gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore')
            else:
                f = open(file_path, 'r', encoding='utf-8', errors='ignore')
            
            current_entry = {}
            
            for line in f:
                line = line.strip()
                if not line:
                    if "Start-Date" in current_entry and "Commandline" in current_entry:
                        formatted = format_entry(current_entry, subcommand)
                        if formatted:
                            parsed_lines.append(formatted)
                    current_entry = {}
                    continue
                
                if ":" in line:
                    key, value = line.split(":", 1)
                    current_entry[key.strip()] = value.strip()
            
            if "Start-Date" in current_entry and "Commandline" in current_entry:
                formatted = format_entry(current_entry, subcommand)
                if formatted:
                    parsed_lines.append(formatted)
                    
            f.close()
        except PermissionError:
            print(f"エラー: {file_path} の読み込み権限がありません。sudo をつけて実行してください。", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"警告: {file_path} の処理中にエラーが発生しました: {e}", file=sys.stderr)

    parsed_lines.sort()
    return parsed_lines

def format_entry(entry, sc):
    cmdline = entry.get("Commandline", "")
    start_date = entry.get("Start-Date", "")
    
    if not (cmdline.startswith("apt ") or cmdline.startswith("apt-get ") or "aptitude" in cmdline):
        return None
    
    if ("AutoInstall=yes" in cmdline and sc == "simple"):
        return None
    
    try:
        dt = datetime.strptime(start_date, "%Y-%m-%d  %H:%M:%S")
        timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        timestamp = start_date

    parts = cmdline.split()
    clean_cmd = " ".join([p for p in parts if p not in ["sudo", "apt", "apt-get", "-y", "--assume-yes",]])

    return f"{timestamp} | {clean_cmd}"

def main():
    subcommand = ""
    if len(sys.argv) == 2:
        subcommand = sys.argv[1]
        if subcommand != 'simple' :
            print('無効なサブコマンドです。')
            return 1

    logs = parse_history_log(subcommand)
    
    if not logs:
        print("有効なインストール履歴が見つかりませんでした。")
        return
    
    output_content = "\n".join(logs) + "\n"
    
    print(output_content)
    
if __name__ == "__main__":
    main()