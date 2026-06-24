
#S3 Bucket 
resource "aws_s3_bucket" "artifacts_store" {
  bucket = "my-tf-pipeline-bucket-store"

  tags = {
    Name        = "${var.project_name}-s3"
    Environment = "Dev"
  }
}
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}


#IAM role - permissions
resource "aws_iam_role" "security" {
  name = "${var.project_name}-iam"


  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = ["codebuild.amazonaws.com", "codepipeline.amazonaws.com"]
        }
      },
    ]
  })

  tags = {
    tag-key = "tag-value"
  }
}
resource "aws_iam_role_policy_attachment" "runTerraform" {
  role               = aws_iam_role.security.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}


#Code PipeLine Set Up 
resource "aws_codepipeline" "codepipeline" {
  name     = "${var.project_name}-codepipeline"
  role_arn = aws_iam_role.security.arn

  artifact_store {
    location = aws_s3_bucket.artifacts_store.bucket
    type     = "S3"

  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn    = var.codestar_connection_arn
        FullRepositoryId = "VerticalRelevance/kafka-cluster-tf"
        BranchName       = "main"
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]
      version          = "1"

      configuration = {
        ProjectName = "${var.project_name}-Build"
      }
    }
  }
}


#Code Build
resource "aws_codebuild_project" "codeBuild" {
  name          = "${var.project_name}-Build"
  description   = "Pipeline test"
  build_timeout = 5
  service_role  = aws_iam_role.security.arn
  



  artifacts {
    type = "CODEPIPELINE"
  }
  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux2-x86_64-standard:4.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
        name  = "AWS_DEFAULT_REGION"
        value = "us-east-2"
  }

  }
  source {
    type            = "CODEPIPELINE"
    buildspec       = "buildspec.yml"
  }
  

}