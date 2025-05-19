from openai import OpenAI

class DeepSeekClient:
    def __init__(self):
        self.api = "sk-zytfdmlmgpjzvgxbflesvkbbkxkrwvmbqzdrjtzalprovhml"
        self.client = OpenAI(api_key=self.api, base_url="https://api.siliconflow.cn/v1")

    def get_response(self, messages, model="deepseek-ai/DeepSeek-V2.5", stream=True):
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream
        )
        return response

    def get_comment(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            comment = f.read()
        return comment


# 使用示例
if __name__ == "__main__":
    deepseek_client = DeepSeekClient()
    file_path = r"../downloads/《中共中央关于党的百年奋斗重大成就和历史经验的决议》公布/《中共中央关于党的百年奋斗重大成就和历史经验的决议》公布_语音转文字.txt"
    with open(file_path, 'r', encoding='utf-8') as f:
        result = f.read()

    messages = [
        {"role": "system", "content": "please help me summary the result"},
        {"role": "user", "content": result},
    ]

    response = deepseek_client.get_response(messages)
    print(response)
