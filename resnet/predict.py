import json

import torch
from PIL import Image, ImageFont, ImageDraw
from torchvision import transforms
import matplotlib.pyplot as plt
import numpy as np
from model import resnet34
import cv2
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def viz(module, input):
    x = input[0][0]
    # 最多显示4张图
    min_num = np.minimum(4, x.size()[0])
    for i in range(min_num):
        plt.subplot(1, 4, i + 1)
        plt.imshow(x[i])
    plt.show()


def main():
    result_path = 'run/exp' + str(len(os.listdir('run/')) + 1)
    # device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    device = torch.device('cpu')

    data_transform = transforms.Compose(
        [transforms.Resize(256),
         transforms.CenterCrop(224),
         transforms.ToTensor(),
         transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    # load image
    # path = 'grab_data/1'
    # imglist = os.listdir(path)
    # for i in range(len(imglist)):
    #     img_1 = Image.open(path + '/' + imglist[i])  # 原图
    #     img = Image.open(path + '/' + imglist[i])
    #
    #     # [N, C, H, W]
    #     img = data_transform(img)
    #
    #     # expand batch dimension
    #     img = torch.unsqueeze(img, dim=0)
    #
    #     # read class_indict
    #     json_path = 'class_indices.json'
    #     assert os.path.exists(json_path), "file: '{}' dose not exist.".format(json_path)
    #
    #     json_file = open(json_path, "r")
    #     class_indict = json.load(json_file)
    #
    #     # create model
    #     model = resnet34(num_classes=13).to(device)
    #
    #     # load model weights
    #     weights_path = "resNet34.pth"
    #     assert os.path.exists(weights_path), "file: '{}' dose not exist.".format(weights_path)
    #
    #     model.load_state_dict(torch.load(weights_path, map_location=device))
    #
    #     # prediction
    #     model.eval()
    #
    #     with torch.no_grad():
    #         # predict class
    #         output = torch.squeeze(model(img.to(device))).cpu()
    #         predict = torch.softmax(output, dim=0)
    #         predict_cla = torch.argmax(predict).numpy()
    #
    #     print_res = "class: {}   prob: {:.3}".format(class_indict[str(predict_cla)],
    #                                                  predict[predict_cla].numpy())
    #     # print(print_res)
    #     font = ImageFont.truetype('GBK.ttf', 100)
    #     img_0 = Image.new('RGB', (img_1.size[0], 150), (255, 255, 255))
    #     draw = ImageDraw.Draw(img_0)
    #     draw.text((0, 0), print_res, (255, 0, 0), font)
    #     image = np.vstack((img_0, img_1))
    #
    #     if os.path.exists(result_path):
    #         cv2.imwrite(result_path + '/' + imglist[i], cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    #     else:
    #         os.makedirs(result_path)
    #         cv2.imwrite(result_path + '/' + imglist[i], cv2.cvtColor(image, cv2.COLOR_RGB2BGR))

    # plt.title(print_res)
    # print(print_res)
    # end = time.time()
    # print(end - start)
    # plt.show(
    img_path = "grab_data/1/hqfimg_0144.jpg"
    assert os.path.exists(img_path), "file: '{}' dose not exist.".format(img_path)
    img_1 = Image.open(img_path)
    img = img_1
    # plt.imshow(img)
    # [N, C, H, W]
    img = data_transform(img)
    # expand batch dimension
    img = torch.unsqueeze(img, dim=0)

    # read class_indict
    json_path = 'class_indices.json'
    assert os.path.exists(json_path), "file: '{}' dose not exist.".format(json_path)

    json_file = open(json_path, "r")
    class_indict = json.load(json_file)

    # create model
    model = resnet34(num_classes=13).to(device)

    # 创建hook钩子函数，查看中间特征图
    for name, m in model.named_modules():
        # if not isinstance(m, torch.nn.ModuleList) and \
        #         not isinstance(m, torch.nn.Sequential) and \
        #         type(m) in torch.nn.__dict__.values():
        # 这里只对卷积层的feature map进行显示
        if isinstance(m, torch.nn.Conv2d):
            m.register_forward_pre_hook(viz)

    # load model weights
    weights_path = "resNet34.pth"
    assert os.path.exists(weights_path), "file: '{}' dose not exist.".format(weights_path)
    model.load_state_dict(torch.load(weights_path, map_location=device))

    # prediction
    model.eval()
    with torch.no_grad():
        # predict class
        output = torch.squeeze(model(img.to(device))).cpu()
        predict = torch.softmax(output, dim=0)
        predict_cla = torch.argmax(predict).numpy()

    print_res = "class: {}   prob: {:.3}".format(class_indict[str(predict_cla)],
                                                 predict[predict_cla].numpy())

    font = ImageFont.truetype('GBK.ttf', 100)
    img_0 = Image.new('RGB', (img_1.size[0], 150), (255, 255, 255))
    draw = ImageDraw.Draw(img_0)
    draw.text((0, 0), print_res, (255, 0, 0), font)
    image = np.vstack((img_0, img_1))

    if os.path.exists(result_path):
        cv2.imwrite(result_path + '/' + img_path.split('/')[2], cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    else:
        os.makedirs(result_path)
        cv2.imwrite(result_path + '/' + img_path.split('/')[2], cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


if __name__ == '__main__':
    main()
