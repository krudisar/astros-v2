cd ..
docker image build -t astros:v2 .
docker tag astros:v2 krudisar/astros:v2
docker push krudisar/astros:v2
