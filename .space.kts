/**
* JetBrains Space Automation
* This Kotlin-script file lets you automate build activities
* For more info, see https://www.jetbrains.com/help/space/automation.html
*/

job("Build and push Docker") {
    parameters {
        secret("private-key", "{{ project:VPS_KEY }}")
    }
    host("Build and push a Docker image") {
        fileInput {
            source = FileSource.Text("{{ private-key }}")
            localPath = "/root/.ssh/id_rsa"
        }

        shellScript {
            content = """
                set -e
                pwd
                chmod 0400 /root/.ssh/id_rsa
                cat  /root/.ssh/id_rsa |cut -c 1-5
                ls -l /root/.ssh/id_rsa
                ssh -i /root/.ssh/id_rsa -o "StrictHostKeyChecking=no" {{ project:VPS_USERNAME }}@{{ project:VPS_HOST }} -p {{ project:VPS_PORT }} {{ project:VPS_CMD }}
            """
        }
    }
}

