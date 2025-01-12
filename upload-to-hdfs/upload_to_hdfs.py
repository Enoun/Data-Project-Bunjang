import os
import subprocess

# 업로드 할 데이터가 있는 파일과 HDFS 경로 설정
local_directories = {
    "mans_category": "/opt/airflow/data-pipeline-project/airflow-project/shared/collectedData/mans_category/",
    "woman_category": "/opt/airflow/data-pipeline-project/airflow-project/shared/collectedData/woman_category/"
}

mans_category_path = "/user/dataPipeline/mans_category"
woman_category_path = "/user/dataPipeline/woman_category"

os.environ["HADOOP_CONF_DIR"] = "/usr/local/hadoop/etc/hadoop"
os.environ["PATH"] = os.environ["PATH"] + ":/usr/local/hadoop/bin:/usr/local/hadoop/sbin"

upload_log = "/opt/airflow/data-pipeline-project/upload-to-hdfs/upload_log.txt"

# 로그 파일 확인 후 업로드 기록이 없는 파일만 업로드
def upload_to_hdfs(local_directory, hdfs_directory):
    # 로그 파일 생성
    if not os.path.exists(upload_log):
        open(upload_log, 'w').close()

    with open(upload_log, 'r') as f:
        uploaded_files = f.read().splitlines()

    # HDFS 디렉터리 생성 (존재하지 않는 경우)
    try:
        subprocess.run(
            ["/usr/local/hadoop/bin/hdfs", "dfs", "-mkdir", "-p", "/user/dataPipeline"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"HDFS 디렉터리 생성 실패: {hdfs_directory}, Error: {e}")

    # 파일 업로드
    for filename in os.listdir(local_directory):
        local_file_path = os.path.join(local_directory, filename)
        hdfs_file_path = f"{hdfs_directory}/{filename}"

        if filename not in uploaded_files:
            try:
                # HDFS 파일 업로드
                subprocess.run(
                    ["hdfs", "dfs", "-put", "-f", local_file_path, hdfs_file_path],
                    check=True
                )
                print(f"업로드 성공: {filename} -> {hdfs_file_path}")

                # 로그 파일에 업로드한 파일 기록
                with open(upload_log, 'a') as log:
                    log.write(filename + "\n")
            except subprocess.CalledProcessError as e:
                print(f"업로드 실패: {filename}, Error: {e}")
            except Exception as e:
                print(f"파일 업로드 중 오류 발생: {filename}, Error: {str(e)}")

upload_to_hdfs(local_directories["mans_category"], mans_category_path)
upload_to_hdfs(local_directories["woman_category"], woman_category_path)