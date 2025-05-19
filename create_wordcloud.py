import logging
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud

class WordCloudGenerator:
    def __init__(self):
        logging.getLogger('jieba').setLevel(logging.WARNING)
        self.FONT_PATH = "font/STZHONGS.TTF"

    def generate_word_frequency_and_cloud(self, data, save_words_prefix, file_path):
        # 将每行内容格式化为字典，存入 data 列表
        # splitlines() 方法将字符串 data 按换行符分割成多个行，返回一个包含每行内容的列表。
        data_list = [data.strip() for data in data.splitlines() if data.strip()]
        # 统计每个元素出现的次数
        word_freq = Counter(data_list)
        # 创建词云生成器实例

        self.generate_word_cloud(word_freq, save_words_prefix, file_path)

    def generate_word_cloud(self, word_freq, save_words_prefix, file_path):
        """
        使用 sorted 函数对列表进行排序，排序依据是每个元组的第二个元素
        WordCloud 是 wordcloud 库中的一个类，用于创建词云对象。
        font_path=self.FONT_PATH：指定词云中文字使用的字体文件路径，确保中文等非 ASCII 字符能够正常显示。
        width=800 和 height=400：设置词云图像的宽度和高度。
        background_color='white'：设置词云图像的背景颜色为白色。
        max_words=600：设置词云中最多显示的单词数量。
        colormap='viridis'：设置词云的颜色映射，这里使用 viridis 颜色映射。
        contour_color='steelblue' 和 contour_width=1：设置词云的轮廓颜色为钢蓝色，轮廓宽度为 1 像素。
        generate_from_frequencies(top_20_word_freq)：根据 top_20_word_freq 字典中的词频信息生成词云。
        """
        top_50_word_freq = {word: freq for word, freq in
                            sorted(word_freq.items(), key=lambda item: item[1], reverse=True)[:50]}
        wordcloud = WordCloud(
            font_path=self.FONT_PATH,
            width=800,
            height=400,
            background_color='white',
            max_words=600,
            colormap='viridis',
            contour_color='steelblue',
            contour_width=1
        ).generate_from_frequencies(top_50_word_freq)

        # Save word cloud image
        plt.figure(figsize=(10, 5), facecolor='white')
        plt.imshow(wordcloud, interpolation='bilinear')

        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(f"{file_path}/文字云_{save_words_prefix}.png", format='png', dpi=300)
        plt.close()
