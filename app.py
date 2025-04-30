from flask import Flask, render_template, request, jsonify, flash
import requests
import json
import os
from urllib.parse import quote
from flask_wtf.csrf import CSRFProtect
import re

app = Flask(__name__)
# 環境変数から秘密鍵を取得（設定されていない場合はデフォルト値を使用）
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('CSRF_SECRET_KEY', os.urandom(24))
csrf = CSRFProtect(app)

def validate_latex(latex):
    """LaTeXの入力値を検証する"""
    if not latex or not latex.strip():
        return False, "数式が入力されていません"
    
    # 危険なコマンドをチェック
    dangerous_commands = [
        r'\\input', r'\\include', r'\\write', r'\\openout',
        r'\\read', r'\\openin', r'\\write', r'\\openout',
        r'\\catcode', r'\\def', r'\\let', r'\\newcommand'
    ]
    
    for cmd in dangerous_commands:
        if re.search(cmd, latex):
            return False, "使用できないコマンドが含まれています"
    
    return True, ""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        latex = request.form.get('latex', '').strip()
        
        # 入力値の検証
        is_valid, error_message = validate_latex(latex)
        if not is_valid:
            flash(error_message, 'error')
            return render_template('index.html', error=error_message)
        
        try:
            # KaTeXのCDNを使用してSVGを生成
            katex_url = f"https://latex.codecogs.com/svg.image?{quote(latex)}"
            response = requests.get(katex_url, timeout=10)  # タイムアウトを設定
            
            if response.status_code == 200:
                return render_template('index.html', latex=latex, image_url=katex_url)
            else:
                flash("画像の生成に失敗しました", 'error')
                return render_template('index.html', error="画像の生成に失敗しました")
                
        except requests.Timeout:
            flash("サーバーの応答が遅いため、タイムアウトしました", 'error')
            return render_template('index.html', error="サーバーの応答が遅いため、タイムアウトしました")
        except requests.RequestException as e:
            flash(f"エラーが発生しました: {str(e)}", 'error')
            return render_template('index.html', error=f"エラーが発生しました: {str(e)}")
        except Exception as e:
            flash(f"予期せぬエラーが発生しました: {str(e)}", 'error')
            return render_template('index.html', error=f"予期せぬエラーが発生しました: {str(e)}")
    
    return render_template('index.html')

if __name__ == '__main__':
    # 本番環境では環境変数からポートを取得
    port = int(os.environ.get('PORT', 5000))
    # 本番環境ではデバッグモードを無効化
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 