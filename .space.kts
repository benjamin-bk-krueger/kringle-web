/**
* JetBrains Space Automation
* This Kotlin-script file lets you automate build activities
* For more info, see https://www.jetbrains.com/help/space/automation.html
*/

job("Build and push Docker") {
    docker {
        build {
            context = "docker"
            file = "./Dockerfile"
            labels["vendor"] = "benjamin.krueger"
        }

        push("krueger.registry.jetbrains.space/p/kringle/containers/kringle-web") {
            // use current job run number as a tag - '0.0.run_number'
            tags("0.0.\$JB_SPACE_EXECUTION_NUMBER")
        }
    }
}