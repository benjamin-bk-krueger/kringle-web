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
        dockerBuildPush {
            // by default, the step runs not only 'docker build' but also 'docker push'
            // to disable pushing, add the following line:
            // push = false

            // path to Docker context (by default, context is working dir)
            // context = "docker"
            // path to Dockerfile relative to the project root
            // if 'file' is not specified, Docker will look for it in 'context'/Dockerfile
            // file = "docker/config/Dockerfile"
            // build-time variables
            // args["HTTP_PROXY"] = "http://10.20.30.2:1234"
            // image labels
            labels["vendor"] = "Ben Krueger <sayhello@blk8.de>"
            // to add a raw list of additional build arguments, use
            // extraArgsForBuildCommand = listOf("...")
            // to add a raw list of additional push arguments, use
            // extraArgsForPushCommand = listOf("...")
            // image tags
            tags {
                // use current job run number as a tag - '0.0.run_number'
                +"krueger.registry.jetbrains.space/p/kringle/containers/kringle-web:1.0.${"$"}JB_SPACE_EXECUTION_NUMBER"
            }
        }
        shellScript {
            fileInput {
                source = FileSource.Text("{{ private-key }}")
                localPath = "/root/.ssh/id_rsa"
            }
            content = """
                set -e
                ssh {{ project:VPS_USERNAME }}@{{ project:VPS_HOST }} -p {{ project:VPS_PORT }} {{ project:VPS_CMD }}
            """
        }
    }
}

