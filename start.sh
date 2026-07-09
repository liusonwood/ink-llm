#!/bin/bash
# 1. 进入工作目录
cd /home/admin/kindle-llm
# 2. 激活虚拟环境
source venv/bin/activate
# 3. 设置英伟达 API KEY
export NVIDIA_API_KEY="nvapi-***"
# 4. (可选) 设置模型名称
export NVIDIA_MODEL_NAME="mistralai/mistral-small-4-119b-2603"
# 5. 启动服务
python app.py
