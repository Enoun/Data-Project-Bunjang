import os
import subprocess

# 업로드 데이터가 있는 디렉터리와 HDFS 경로 설정
local_directories = {
    "mans_category": "/Users/data-project/data-pipeline-project/collectedData/mans_category/",
    "woman_category": "/Users/data-project/data-pipeline-project/collectedData/woman_category/"
}
hdfs_directory = "/user/dataPipeline/collectedData/"
upload_log = "/Users/data-project/data-pipeline-project/upload_log.txt"


# 로그 파일을 확인한 후 업로드 기록이 없는 파일만 업로드
def upload_to_hdfs(local_directory):
    if not os.path.exists(upload_log):
        open(upload_log, 'w').close()  # 로그 파일이 없으면 생성

    with open(upload_log, 'r') as f:
        uploaded_files = f.read().splitlines()

    for filename in os.listdir(local_directory):
        local_file_path = os.path.join(local_directory, filename)  # 수정된 부분

        if filename not in uploaded_files:
            hdfs_path = os.path.join(hdfs_directory, filename) # HDFS에 파일 업로드
            subprocess.run(["hdfs", "dfs", "-put", local_file_path, hdfs_path])

            # 로그 파일에 업로드한 파일 기록
            with open(upload_log, 'a') as log:
                log.write(filename + "\n")
            print(f"Uploaded {filename} to HDFS.")

# 실행 (두 개의 디렉터리에 대해 업로드)
for directory in local_directories.values():
    upload_to_hdfs(directory)