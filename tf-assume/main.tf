variable "aws_region" {
  default = "eu-west-2"
} # London

variable "aws_profile" {
  default = "gds-users"
}

variable "public_key_path" {
  description = "Enter the path to the SSH Public Key to add to AWS."
  default     = "~/.ssh/id_rsa.pub"
}

variable "instance_type" {
  default = "t2.micro"
}

variable "username" {
  default = "user"
}

provider "aws" {
  region  = "${var.aws_region}"
  profile = "${var.aws_profile}"
}

resource "aws_security_group" "allow_ssh_from_gds" {
  name_prefix = "CyberSecurity-Tooling-SecurityGroup-SSH"
  description = "Allow inbound SSH traffic from GDS IPs"

  ingress = {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"

    cidr_blocks = [
      "213.86.153.212/32",
      "213.86.153.213/32",
      "213.86.153.214/32",
      "213.86.153.235/32",
      "213.86.153.236/32",
      "213.86.153.237/32",
      "85.133.67.244/32",
    ]
  }
}

resource "aws_security_group" "allow_all_outbound" {
  name_prefix = "CyberSecurity-Tooling-SecurityGroup-outbound"
  description = "Allow all outbound traffic"

  egress = {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_instance" "box" {
  ami               = "${data.aws_ami.ubuntu.id}"
  availability_zone = "${var.aws_region}a"
  instance_type     = "${var.instance_type}"

  security_groups = [
    "${aws_security_group.allow_ssh_from_gds.name}",
    "${aws_security_group.allow_all_outbound.name}",
  ]

  key_name = "${aws_key_pair.auth.key_name}"

  provisioner "remote-exec" {
    inline = [
      "sudo locale-gen en_GB.UTF-8",
      "sudo apt-get -y update",
      "sudo apt-get -y install python-dev",
    ]

    connection {
      type  = "ssh"
      user  = "ubuntu"
      agent = true
    }
  }

  tags {
    Name = "CyberSecurity-Tooling-EC2"
  }
}

resource "aws_key_pair" "auth" {
  key_name   = "cyber-security-key-${var.username}"
  public_key = "${file(var.public_key_path)}"
}

output "ec2_ip" {
  value = "${aws_instance.box.public_ip}"
}
