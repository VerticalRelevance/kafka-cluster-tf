
data "aws_ami" "amzn-linux-2023-ami" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_instance" "EC2" {
  ami           = data.aws_ami.amzn-linux-2023-ami.id
  instance_type = var.instance_type
  subnet_id     = module.vpc.public_subnets[0]
  vpc_security_group_ids = [aws_security_group.kafka_sec.id] 
  key_name = var.key_pair_name
  user_data = file("${path.module}/scripts/user_data.sh")
  associate_public_ip_address = true


  tags = {
    Name = "${var.project_name}-kafka"
  }
}