TOKEN=$(curl -s -X POST http://192.168.207.129:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")


CONV_ID=$(curl -s -X POST http://192.168.207.129:8000/api/v1/chat/conversations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"第一个对话"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

echo "会话ID: $CONV_ID"

# 发送消息
curl -s -X POST http://192.168.207.129:8000/api/v1/chat/conversations/$CONV_ID/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content":"你好，请介绍一下你自己"}' | python3 -m json.tool

# 3. 跑全部测试
pytest tests/ -v
