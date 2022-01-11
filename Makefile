install:
	pip install -r requirements.txt

build:
	docker build -t ec2-deamon .

run: clean
	docker run --restart always --name ec2-deamon -it --env-file .env ec2-deamon

clean:
	docker stop ec2-deamon
	docker rm ec2-deamon