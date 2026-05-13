"""
测试WebSocket流式聊天是否正常工作
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/chat/stream/test_user"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功!")
            
            # 发送测试消息
            await websocket.send(json.dumps({"message": "你好"}))
            print("📤 已发送消息: 你好")
            
            # 接收响应
            chunk_count = 0
            full_response = ""
            
            async for message in websocket:
                data = json.loads(message)
                
                if data['type'] == 'typing':
                    print("⌨️  正在输入...")
                elif data['type'] == 'chunk':
                    chunk_count += 1
                    full_response += data['data']
                    if chunk_count % 10 == 0:  # 每10个字符打印一次
                        print(f"📝 收到 {chunk_count} 个字符...")
                elif data['type'] == 'complete':
                    print(f"\n✅ 完成! 共收到 {chunk_count} 个字符")
                    print(f"💬 完整回复: {full_response[:100]}...")
                    break
            
            print("\n🎉 WebSocket流式聊天测试通过!")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("\n💡 请确保:")
        print("   1. 后端正在运行: uvicorn main:app --reload")
        print("   2. 端口8000未被占用")

if __name__ == "__main__":
    print("=" * 50)
    print("WebSocket流式聊天测试")
    print("=" * 50)
    asyncio.run(test_websocket())
