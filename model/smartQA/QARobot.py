'''
@Project ：dataProcess.py 
@File    ：QARobot.py
@Author  ：Minhao Cao
@Date    ：2024/6/29 上午10:11 
'''
import openai
from openai import OpenAI

API_KEY = "sk-OsscLrq0PePtkUb7B104F456Db1941F48906B9F824D1CdB4"
openai.api_key = API_KEY

class SmartQARobot:
    def __init__(self):
        self.API_KEY = API_KEY
        self.client = OpenAI(
            base_url="https://api.chatgptid.net/v1",
            api_key=self.API_KEY
        )

    def API(self, question):
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"{question}."}
            ]
        )
        return completion.choices[0].message.content


if __name__ == '__main__':
    robot = SmartQARobot()
    print(robot.API("html网页怎么对markdown进行渲染"))