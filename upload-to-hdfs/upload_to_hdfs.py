import os
import subprocess

# 업로드 할 데이터가 있는 파일과 HDFS 경로 설정
local_directories = {
    "mans_category": "/opt/airflow/data-project/data-pipeline-project/collectedData/mans_category/",
    "woman_category": "/opt/airflow/data-project/data-pipeline-project/collectedData/woman_category/"
}

mans_category_path = "/user/dataPipeline/collectedData/mans_category"
woman_category_path = "/user/dataPipeline/collectedData/woman_category"

upload_log = "/opt/airflow/data-project/data-pipeline-project/upload-to-hdfs/upload_log.txt"


# 로그 파일을 확인한 후 업로드 기록이 없는 파일만 업로드
def upload_to_hdfs(local_directory, category_path):
    if not os.path.exists(upload_log):
        open(upload_log, 'w').close()  # 로그 파일이 없으면 생성

    with open(upload_log, 'r') as f:
        uploaded_files = f.read().splitlines()

    subprocess.run(["hdfs", "dfs", "-mkdir", "-p", category_path], check=True)

    for filename in os.listdir(local_directory):
        local_file_path = os.path.join(local_directory, filename)  # 수정된 부분

        if filename not in uploaded_files:
            try:
                hdfs_path = os.path.join(category_path, filename) # HDFS에 파일 업로드
                result = subprocess.run(
                    ["hdfs", "dfs", "-put", local_file_path, hdfs_path],
                    check=True, capture_output=True, text=True
                )
                print(result.stdout)

                # 로그파일에 업로드한 파일 기록
                with open(upload_log, 'a') as log:
                    log.write(filename + "\n")
                print(f"업로드 성공 {filename} to {hdfs_path}")
            except subprocess.CalledProcessError as e:
                print(f"업로드 실패 {filename} to HDFS, Error: {e.stderr}")
                continue


upload_to_hdfs(local_directories["mans_category"], mans_category_path)
upload_to_hdfs(local_directories["woman_category"], woman_category_path)