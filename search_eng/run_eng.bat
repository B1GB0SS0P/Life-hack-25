docker run --rm ^
             -d -p 8080:8080 ^
             -v "%cd%/searxng:/etc/searxng" ^
             -e "BASE_URL=http://localhost:8080/" ^
             -e "INSTANCE_NAME=my-instance" ^
             searxng/searxng