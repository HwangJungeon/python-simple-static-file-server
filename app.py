from flask import Flask, send_file, request
import mimetypes
import logging
from logging.handlers import RotatingFileHandler
import os
import time
from datetime import datetime
import pytz
import psutil  # 메모리 사용 정보를 얻기 위해 사용

app = Flask(__name__)

log_timezone = pytz.timezone('Asia/Seoul')

# 로그 설정
log_file_path = 'app.log'
handler = RotatingFileHandler(log_file_path, maxBytes=10000, backupCount=10)
handler.setLevel(logging.INFO)

# 로그 형식 지정
formatter = logging.Formatter('[%(asctime)s] [%(ip)s] [%(levelname)s] [%(endpoint)s] [%(response_time)s ms] [%(memory_usage)s MB] [%(user_agent)s] [%(message)s]')
formatter.converter = lambda *args: datetime.now(log_timezone).timetuple() 

handler.setFormatter(formatter)

app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

def is_valid_user_agent(user_agent):
    allowed_user_agents = ["Mozilla", "Chrome", "Safari"]
    return any(agent in user_agent for agent in allowed_user_agents)

@app.route('/<path:file_path>')
def get_user_file(file_path):
    start_time = time.time()  # 요청 처리 시작 시간 기록

    user_agent = request.headers.get('User-Agent')

    if not is_valid_user_agent(user_agent):
        app.logger.warning(f"[Forbidden] [User-Agent: {user_agent}] [IP: {request.remote_addr}] Request to {file_path}")
        return "Forbidden", 403

    if os.path.exists(file_path):
        # 파일 유형을 동적으로 가져오기
        file_mime_type, _ = mimetypes.guess_type(file_path)

        # 로깅
        end_time = time.time()  # 요청 처리 종료 시간 기록
        elapsed_time = round((end_time - start_time) * 1000, 2)  # 응답 시간 계산 및 기록
        memory_usage = round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 2)  # 메모리 사용량 계산 및 기록

        log_message = f"[File requested: {file_path}] [Mime Type: {file_mime_type}]"
        app.logger.info(log_message, extra={
            'ip': request.remote_addr,
            'user_agent': user_agent,
            'endpoint': request.endpoint,
            'response_time': elapsed_time,
            'memory_usage': memory_usage
        })

        return send_file(file_path, mimetype=file_mime_type)
    else:
        # 파일이 존재하지 않으면 대체 파일 전송
        alternative_file_path = 'error.png'

        # 로깅
        end_time = time.time()  # 요청 처리 종료 시간 기록
        elapsed_time = round((end_time - start_time) * 1000, 2)  # 응답 시간 계산 및 기록
        memory_usage = round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 2)  # 메모리 사용량 계산 및 기록

        log_message = f"[File not found: {file_path}] [Sending alternative file]"
        app.logger.warning(log_message, extra={
            'ip': request.remote_addr,
            'user_agent': user_agent,
            'endpoint': request.endpoint,
            'response_time': elapsed_time,
            'memory_usage': memory_usage
        })

        return send_file(alternative_file_path, mimetype='image/png')

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
