kindle llm chat

1.stat

run:
# 1. 赋予可执行权限
chmod +x start.sh

# 2. 再次尝试运行
./start.sh

background:	nohup ./start.sh > output.log 2>&1 &
kill:	pkill -f app.py



