import os
import subprocess
import requests

# 업로드 할 데이터가 있는 파일과 HDFS 경로 설정
local_directories = {
    "mans_category": "/opt/airflow/data-pipeline-project/collectedData/mans_category/",
    "woman_category": "/opt/airflow/data-pipeline-project/collectedData/woman_category/"
}

mans_category_path = "/user/dataPipeline/collectedData/mans_category"
woman_category_path = "/user/dataPipeline/collectedData/woman_category"

upload_log = "/opt/airflow/data-pipeline-project/upload-to-hdfs/upload_log.txt"
webhdfs_url = "http://namenode:9870/webhdfs/v1"
user = "hdfs"

# 로그 파일을 확인한 후 업로드 기록이 없는 파일만 업로드
def upload_to_hdfs(local_directory, category_path):
    if not os.path.exists(upload_log):
        open(upload_log, 'w').close()  # 로그 파일이 없으면 생성

    with open(upload_log, 'r') as f:
        uploaded_files = f.read().splitlines()

    # HDFS 디렉터리 생성 (존재하지 않는 경우)
    mkdir_response = requests.put(
        f"{webhdfs_url}{category_path}?op=MKDIRS&user.name={user}"
    )
    if mkdir_response.status_code not in [200, 201]:
        print(f"디렉터리 생성 실패: {category_path}, Error: {mkdir_response.content}")

    for filename in os.listdir(local_directory):
        local_file_path = os.path.join(local_directory, filename)

        if filename not in uploaded_files:
            try:
                hdfs_path = f"{hdfs_directory}/{filename}"
                # WebHDFS 파일 업로드
                create_response = requests.put(
                    f"{webhdfs_url}{hdfs_path}?op=CREATE&overwrite=true&user.name={user}",
                    allow_redirects=False
                )

                if 'location' in create_response.headers:
                    redirect_url = create_response.headers['location']
                    with open(local_file_path, 'rb') as file_data:
                        upload_response = requests.put(redirect_url, data=file_data)
                        if upload_response.status_code == 201:
                            print(f"업로드 성공: {filename} -> {hdfs_path}")
                            # 로그파일에 업로드한 파일 기록
                            with open(upload_log, 'a') as log:
                                log.write(filename + "\n")
                        else:
                            print(f"업로드 실패: {filename}, Error: {upload_response.content}")
                else:
                    print(f"업로드 요청 실패: {filename}, Error: {create_response.content}")

            except Exception as e:
                print(f"파일 업로드 중 오류 발생: {filename}, Error: {str(e)}")
                continue

upload_to_hdfs(local_directories["mans_category"], mans_category_path)
upload_to_hdfs(local_directories["woman_category"], woman_category_path)