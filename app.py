import os
import sys
from flask import Flask, request, Response, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import requests
import urllib.parse

import time

app = Flask(__name__)

UPLOAD_FOLDER = os.path.realpath('uploads')
if not os.path.exists(UPLOAD_FOLDER):
    print(f"Error: ディレクトリ '{UPLOAD_FOLDER}' が存在しません")
    sys.exit(1)


# 日本語文字化け対策
app.config['JSON_AS_ASCII'] = False
app.json.ensure_ascii = False

@app.route('/')
def hello():
    return 'hello'


TIMEOUT = 5

@app.route('/proxy/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    print("request.content_type: " + str(request.content_type))
    print("request.content_length: " + str(request.content_length))
    content_length = request.headers.get('content-length')
    print("content-length: " + str(type(content_length)) + str(content_length)) #TODO

    #if request.content_length is None or request.content_length > 10000:
    #    return Response(response='!!!!!!!!!!!!!', status=500)
    try:
        # /proxy を除去して自身と接続して proxy
        target_url = urllib.parse.urljoin(request.host_url, path)
        print(target_url)

        # list to dict
        headers_dict = dict(request.headers)
        print("/proxy/: " + str(type(headers_dict)) + str(headers_dict))
        # 転送しないヘッダを除去
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection',
                            'user-agent']
        # dict
        headers1 = {name: value for (name, value) in headers_dict.items()
                    if name.lower() not in excluded_headers}

        if request.method == 'GET':
            reqres = requests.get(
                target_url,
                params=request.args,
                stream=True,
                timeout=TIMEOUT
            )
        elif request.method in ('POST', 'PUT', 'DELETE'):
            if request.files:
                # multipart/form-data の場合
                files = {}
                for field_name, file in request.files.items():
                    files[field_name] = (file.filename, file.stream, file.content_type)
                reqres = requests.request(
                    method=request.method,
                    url=target_url,
                    data=request.form, # フォーム
                    files=files, # ファイル
                    stream=True,
                    timeout=TIMEOUT
                )
            else:
                class StreamData():
                    def __iter__(self):
                        return self

                    def __next__(self):
                        chunk = request.stream.read(8192)
                        if not chunk:
                            raise StopIteration
                        return chunk

                    def __len__(self):
                        return int(content_length)

                # 単純データ
                reqres = requests.request(
                    method=request.method,
                    url=target_url,
                    headers=headers1,
                    data=StreamData(),
                    params=request.args,
                    timeout=TIMEOUT
                )
        else:
            return "Method Not Allowed", 405

        # 転送しないヘッダを除去
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        # list
        headers2 = [(name, value) for (name, value) in reqres.raw.headers.items()
                   if name.lower() not in excluded_headers]

        reqres.raise_for_status()

        def generate():
            for chunk in reqres.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        return Response(generate(), status=reqres.status_code, headers=headers2)
    except requests.exceptions.RequestException as e:
        print(f"Proxy error: {e}")
        return f"Proxy error: {e}", 500
    except Exception as e:
        print(f"Internal Server Error: {e}")
        return "Internal Server Error", 500


@app.route('/dl/<filename>')
def download_file(filename):
    try:
        # ファイル名のサニタイズ
        safe_filename = secure_filename(filename)
        if safe_filename != filename:
            return "Invalid filename", 400

        print(UPLOAD_FOLDER)
        print(safe_filename)
        return send_from_directory(UPLOAD_FOLDER, safe_filename, as_attachment=True)
    except FileNotFoundError:
        return "File not found.", 404
    except Exception as e:
        return f"An error occurred: {e}", 500


@app.route('/ul/<filename>', methods=['PUT', 'POST'])
def upload_file(filename):
    print("upload_file content-length", str(request.headers.get("content-length")))
    print("upload_file request.content_length", str(request.content_length))
    print("upload_file content_type", str(request.content_type))
    headers_dict = dict(request.headers)
    print("/ul/: " + str(type(headers_dict)) + str(headers_dict))
    #time.sleep(5)
    try:
        #if request.content_length == 0:
        #    return jsonify({'message': 'ファイルが空です'}), 400

        safe_filename = secure_filename(filename)
        if safe_filename != filename:
            return "Invalid filename", 400

        filepath = os.path.join(UPLOAD_FOLDER, safe_filename)

        with open(filepath, 'wb') as f:
            while True:
                chunk = request.stream.read(4096)
                if not chunk:
                    break
                f.write(chunk)

        return jsonify({'message': 'ファイルがアップロードされました', 'filename': filename}), 200

    except Exception as e:
        return jsonify({'message': f'ファイルの保存に失敗しました: {e}'}), 500


@app.route('/ulmp', methods=['POST'])
def upload_file_multipart():
    if 'file' not in request.files:
        return jsonify({'message': 'ファイルがありません'}), 400

    f_in = request.files['file']

    if f_in.filename == '':
        return jsonify({'message': 'ファイル名がありません'}), 400

    # ファイル名のサニタイズ
    filename = secure_filename(f_in.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        # ファイル名を指定して保存方法
        # f_in.save(filepath)
        # または、チャンクごとに書き込む方法
        with open(filepath, 'wb') as f_out:
            while True:
                chunk = f_in.stream.read(4096)
                if not chunk:
                    break
                f_out.write(chunk)
        return jsonify({'message': 'ファイルがアップロードされました', 'filename': filename}), 200
    except Exception as e:
        return jsonify({'message': f'ファイルの保存に失敗しました: {e}'}), 500



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    #app.run(debug=True)
