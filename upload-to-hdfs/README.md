# Data-Project-Bunjang
Non AWS server Project

이 코드는 로컬 디렉터리에 저장된 데이터를 HDFS로 업로드하는 Python 스크립트입니다. 데이터는 남성 카테고리(mans_category)와 여성 카테고리(woman_category)로 나뉘어 있으며, HDFS 경로에 저장됩니다.

주요 기능
• 업로드 대상 파일 및 경로 설정:
    mans_category와 woman_category 각각에 대해 로컬 디렉터리와 HDFS 경로를 지정합니다.
• 환경 변수 설정:
    HADOOP_CONF_DIR와 PATH 환경 변수를 설정해 Hadoop 명령어와 설정 파일이 올바르게 동작하도록 구성합니다.
• 로그 파일 관리:
    업로드된 파일의 기록을 upload_log.txt에 저장하여, 중복 업로드를 방지합니다.
• HDFS 디렉터리 생성:
    초기에 HDFS 디렉터리가 없으면 생성합니다. 이를 통해 에러가 발생하지 않도록 HDFS상의 경로를 미리 준비합니다.
• 파일 업로드:
    로컬 디렉터리에서 파일을 읽어, HDFS경로로 업로드합니다.
    업로드가 성공한다면 로그 파일에 기록하고, 실패 시 오류 메시지를 출력합니다.

실행 결과
• 데이터는 HDFS의 /user/dataPipeline/mans_category와 /user/dataPipeline/woman_category 경로에 저장됩니다.
• 업로드된 파일의 이름은 upload_log.txt에 기록됩니다.
• 중복 업로드를 방지하기 위해 이미 업로드된 파일은 건너뜁니다.