FROM harbor.zkj.poc/library/jdk1.8.0_231:20210408

MAINTAINER CI_HELPER
LABEL desc=java后端打包镜像

ENV TZ "Asia/Shanghai"
ENV LANG en_US.UTF-8

WORKDIR /app/


ADD {_archive_path} ./
EXPOSE 8080

CMD ['/bin/bash']