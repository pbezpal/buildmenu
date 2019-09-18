pipeline {
    agent { label 'centos' }
    parameters {
        string defaultValue: 'rpmbuild -bb -D "prj_version ${VERSION}" -D "prj_build ${BUILD_NUMBER}" -D "src_dir ${WORKSPACE}" roschat-snmp.spec', description: '', name: 'BUILD_CMD', trim: true
        string defaultValue: 'ssh://10.10.199.35/opt/git/firelink/managment-system-snmp', description: '', name: 'GIT_URL', trim: true
        string defaultValue: 'master', name: 'BRANCH', description: '', trim: true
        string defaultValue: '0.0.0', name: 'VERSION', description: '', trim: true
        string defaultValue: 'server', name: 'TYPE', description: '', trim: true
    }
    stages {
        stage('Clean work directory') {
            // agent { label 'centos' }
            steps {
                sh 'rm -rf *'
            }
        }
        stage('Get sources') {
            // agent { label 'centos' }
            steps {
                git branch: '${BRANCH}', credentialsId: 'git_passwd', url: "${GIT_URL}"
            }
        }
        stage('Build') {
            // agent { label 'centos' } 
            steps {
                sh "$BUILD_CMD"
            }
        }
        stage('Copy to storage') {
            // agent { label 'centos' }
            steps {
                sh "sshpass -p '34appterr21' ssh jenkins@10.10.199.31 'test -d /ftp/releases/RosChat/server/Pipeline_test/ || mkdir /ftp/releases/RosChat/server/Pipeline_test/'"
                sh "sshpass -p '34appterr21' rsync -r -e ssh ${WORKSPACE}/result/* jenkins@10.10.199.31:/ftp/releases/RosChat/${TYPE}/${JOB_NAME}/\$(date +'%d.%m.%Y_%H:%M')_${VERSION}-${BUILD_NUMBER}/"
            }
        }
    }
}
