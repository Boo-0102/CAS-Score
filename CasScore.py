import sys
import cv2
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QMessageBox, QMainWindow
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import uic
import csv
from myui import Ui_CasScore

def cv2_to_qpixmap(img, label_width, label_height):
    # 将OpenCV的图像转换为QImage
    img = cv2.resize(img, (label_width, label_height))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    qimg = QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QImage.Format_RGB888)
    # 将QImage转换为QPixmap
    qpixmap = QPixmap.fromImage(qimg)
    return qpixmap


def read_contrastAndmsk_img(i, contrast_img_path, mask_img_path):
    contrast_image = None
    mask_image = None

    # 读取contrast中的第i张图片
    if os.path.exists(contrast_img_path):
        contrast_files = sorted([f for f in os.listdir(contrast_img_path) if
                                 os.path.isfile(os.path.join(contrast_img_path, f))])
        if contrast_files and i < len(contrast_files):
            contrast_img_path = os.path.join(contrast_img_path, contrast_files[i])  # 拼接路径
            contrast_image = cv2.imread(contrast_img_path)

    # 读取mask中的第i张图片
    if os.path.exists(mask_img_path):
        mask_files = sorted([f for f in os.listdir(mask_img_path) if
                             os.path.isfile(os.path.join(mask_img_path, f))])
        if mask_files and i < len(mask_files):
            mask_img_path = os.path.join(mask_img_path, mask_files[i])
            mask_image = cv2.imread(mask_img_path)

    return mask_image, contrast_image


def read_gen_img(model_index, i, gen_img_path_list):
    img_path = None
    gen_image = None
    gen_img_path = gen_img_path_list[model_index]
    # 读取gen中的第x个model的第i张图片  
    if os.path.exists(gen_img_path):
        gen_files = sorted([f for f in os.listdir(gen_img_path) if
                            os.path.isfile(os.path.join(gen_img_path, f))])
        if gen_files and i < len(gen_files):
            img_path = os.path.join(gen_img_path, gen_files[i])
            gen_image = cv2.imread(img_path)

    return img_path, gen_image



class MyWindow(QMainWindow, Ui_CasScore):

    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 初始化UI界面
        self.score1 = 0
        self.score2 = 0
        self.score3 = 0
        self.gen_path = None  # 标签的第一个量为图片路径
        self.current_index = 0  # 在这里初始化current_index
        self.model_index = 0  # 用于切换model 取值 0 - 4
        self.contrast_img_path = r"D:\score2\dist\CasScore\_internal\CAS_Datasets\Contrast"
        self.mask_img_path = r"D:\score2\dist\CasScore\_internal\CAS_Datasets\Mask"
        self.gen_img_path1 = r"D:\score2\dist\CasScore\_internal\CAS_Datasets\Gen\model1"  # 5个model
        self.gen_img_path2 = r"D:\score2\dist\CasScore\_internal\CAS_Datasets\Gen\model2"
        self.gen_img_path3 = r"D:\score2\dist\CasScore\_internal\CAS_Datasets\Gen\model3"
        self.gen_img_path4 = r"D:\score2\dist\CasScore\_internal\CAS_Datasets\Gen\model4"
        self.gen_img_path5 = r"D:\score2\dist\CasScore\_internal\CAS_Datasets\Gen\model5"
        self.gen_img_path_list = [self.gen_img_path1, self.gen_img_path2, self.gen_img_path3,
                                  self.gen_img_path4, self.gen_img_path5]

        self.next_button = self.next  # next按钮
        self.next_button.clicked.connect(self.change_img)  # 按next切下一张图,并清空score
        self.save_button = self.save  # save按钮
        self.save_button.clicked.connect(self.save_to_txt_and_csv)  # 按save保存score
        self.jump_button = self.jump  # jump按钮
        self.jump_button.clicked.connect(self.jump_to_index)  # 按下跳到指定页面
        self.page_input = self.page  # 用户输入的要跳转的页码
        self.index1 = self.index1_score  # 四个Qslider用于存放四个指标的分数
        self.index2 = self.index2_score
        self.index3 = self.index3_score
        self.show_score1 = self.ui_score1  # 把四个分数显示到界面上
        self.show_score2 = self.ui_score2  # 把四个分数显示到界面上
        self.show_score3 = self.ui_score3  # 把四个分数显示到界面上
        self.show_score1.setText(str(self.score1))  # 显示第一个指标拖动条的当前值
        self.show_score2.setText(str(self.score2))  # 显示第二个指标拖动条的当前值
        self.show_score3.setText(str(self.score3))  # 显示第三个指标拖动条的当前值

        # 连接QSlider的valueChanged信号到槽函数，以实时获取滑块的值
        self.index1.valueChanged.connect(self.update_index_score)
        self.index2.valueChanged.connect(self.update_index_score)
        self.index3.valueChanged.connect(self.update_index_score)

        self.index_label = self.index_label  # index_label用于显示当前图片是第几张
        self.width1 = self.Mask.width()  # Mask与Contrast的大小是一样的
        self.height1 = self.Mask.height()
        self.width2 = self.Gen.width()  # Gen图片的大小
        self.height2 = self.Gen.height()
        self.display_images()
        self.load_index()  # 记住每次打分后页码

    def update_index_score(self):

        # 更新分数
        self.score1 = self.index1.value()
        self.score2 = self.index2.value()
        self.score3 = self.index3.value()
        self.show_score1.setText(str(self.score1))  # 显示第一个指标拖动条的当前值
        self.show_score2.setText(str(self.score2))  # 显示第二个指标拖动条的当前值
        self.show_score3.setText(str(self.score3))  # 显示第三个指标拖动条的当前值

    def display_images(self):
        mask_image, contrast_image = read_contrastAndmsk_img(self.current_index, self.contrast_img_path,
                                                             self.mask_img_path)
        self.gen_path, gen_image = read_gen_img(self.model_index, self.current_index, self.gen_img_path_list)
        self.Mask.setPixmap(cv2_to_qpixmap(mask_image, self.width1, self.height1))  # 显示mask图片
        self.Contrast.setPixmap(cv2_to_qpixmap(contrast_image, self.width1, self.height1))  # 显示contrast图片
        self.Gen.setPixmap(cv2_to_qpixmap(gen_image, self.width2, self.height2))  # 显示Gen图片
        self.index_label.setText(
            f"Index: {self.model_index * 713 + self.current_index + 1} / 3565 ")  # 显示当前图片的索引 1-3565

    """
    i 从0到712 current index也是0 到712 但输入是从1到713
    """

    def change_img(self):  # 按next触发
        if all(x == 0 for x in [self.score1, self.score2, self.score3]):
            QMessageBox.information(self, "！", "还没打分捏🙏", QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes)
        else:
            # 每次换图片将所有 QSlider 的值设置为 0
            self.index1.setValue(0)
            self.index2.setValue(0)
            self.index3.setValue(0)
            if self.current_index == 712:  # current_index: 0-712
                # 尝试切换到下一个模型
                if self.model_index < 5:
                    if self.model_index == 4 and self.current_index == 712:  # 最后一张
                        QMessageBox.information(self, "！", "完成啦😄", QMessageBox.Yes | QMessageBox.No,
                                                     QMessageBox.Yes)
                    else:
                        self.model_index += 1  # 切换到下一个模型
                        self.current_index = 0  # 重置图片索引
                        self.display_images()  # 更新显示的图片
                else:
                    print("over!")

            else:
                self.current_index += 1  # 增加索引以显示下一张图片
                self.display_images()  # 更新显示的图片


    def jump_to_index(self):
        # 从输入框获取索引，并尝试转换为整数
        try:
            # index 0到3564 713*5
            index = int(self.page_input.text())
            # 确保索引在有效范围内
            if 1 <= index <= 3565:
                self.model_index = (index - 1) // 713
                self.current_index = (index - 1) % 713
                self.display_images()
                self.index1.setValue(0)
                self.index2.setValue(0)
                self.index3.setValue(0)
                self.page_input.clear()
            else:
                QMessageBox.information(self, "！", "请输入1-3565哦😄", QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)
        except ValueError:
            print("Please enter a valid integer.")

    def save_to_txt_and_csv(self):  # 按save触发
        scores = [str(self.score1), str(self.score2), str(self.score3)]
        if all(x == '0' for x in scores):  # 如果所有的分数都是0
            QMessageBox.information(self, "！", "不可以全给0分哦🙏", QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes)
        else:
            filename_txt = 'score.txt'
            filename_csv = 'score.csv'
            # 构建要写入的字符串
            scores_str = f"{self.gen_path}, " + ', '.join(scores) + '\n'
            # 检查文件是否存在，如果不存在则创建并写入，如果存在则读取并检查是否重复
            if os.path.exists(filename_txt):
                with open(filename_txt, 'r') as file:
                    # 读取文件内容
                    content = file.readlines()
                if scores_str not in content:  # 不在里面开追加模式
                    with open(filename_txt, 'a') as file:
                        file.write(scores_str)
            else:
                # 文件不存在，直接写入
                with open(filename_txt, 'w') as file:
                    file.write(scores_str)

            # 将文本文件转换为CSV
            with open(filename_txt, 'r') as txt_file, open(filename_csv, 'w', newline='') as csv_file:
                # 创建CSV写入器
                csv_writer = csv.writer(csv_file)
                # 逐行读取文本文件
                for line in txt_file:
                    # 假设文本文件中的每一行都是逗号分隔的值
                    values = line.strip().split(', ')
                    # 写入CSV文件
                    csv_writer.writerow(values)

    def load_index(self):
        if os.path.exists('score.txt'):
            with open('score.txt', 'r') as file:
                lines = file.readlines()
                num_lines = len(lines)
                num = num_lines
                self.model_index = num // 713
                self.current_index = (num % 713)
                self.display_images()


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())
