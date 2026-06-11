.PHONY: up up-fd-jdk21 down logs exploit-tomcat exploit-jetty exploit-fd-tomcat-jdk21 exploit-fd-jetty-jdk21 info info-fd-jdk21

up:
	docker compose up --build -d

up-fd-jdk21:
	docker compose up --build -d attacker-fd tomcat-jdk21-fd jetty-jdk21-fd

down:
	docker compose down --remove-orphans

logs:
	docker compose logs -f

exploit-tomcat:
	./exploit/exploit_tomcat.sh

exploit-jetty:
	./exploit/exploit_jetty.sh

exploit-fd-tomcat-jdk21:
	./exploit/exploit_fd_tomcat_jdk21.sh

exploit-fd-jetty-jdk21:
	./exploit/exploit_fd_jetty_jdk21.sh

info:
	@curl -s http://localhost:18080/info; printf '\n'
	@curl -s http://localhost:18081/info; printf '\n'

info-fd-jdk21:
	@curl -s http://localhost:28080/info; printf '\n'
	@curl -s http://localhost:28081/info; printf '\n'
