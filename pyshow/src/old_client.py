import pygame, sys, os
from pygame.locals import *
import math


class draw():
    #初始化一个窗口,需要输入地图左下角和右上角的坐标，窗口宽度默认为1000，高度会根据地图长宽比进行计算
    def __init__(self, xrange, yrange, window_width = 1000):
        pygame.init()
        self.xrange = xrange
        self.yrange = yrange
        self.maplong = xrange[1] - xrange[0]
        self.mapwidth = yrange[1] - yrange[0]
        if not fullscreen:
            self.windowsize = [window_width, int(self.mapwidth * window_width / self.maplong)]
        else:
            full_width, full_height = pygame.display.list_modes()[0]
            temp_height = int(self.mapwidth * full_width / self.maplong)
            temp_width = int(self.maplong * full_height / self.mapwidth)
            if temp_height <= full_height:
                self.windowsize = [full_width, temp_height]
            else:
                self.windowsize = [temp_width, full_height]
        self.screen = pygame.display.set_mode(self.windowsize)
        pygame.display.set_caption("test")

        ################ chen add ####################
        self.bg = pygame.image.load(__file__[:-7] + "img/sea.png").convert()
        self.bg = pygame.transform.scale(self.bg, self.windowsize)




    # 将地图上的坐标映射到窗口上
    def map2window(self, position):
        scale = self.maplong / self.windowsize[0] / (1 + times)
        position[0] /= scale
        position[1] /= scale
        position[0] -= (self.xrange[0] / scale - translatex * 50)
        position[1] -= (self.yrange[0] / scale - translatey * 50)
        position[1] = self.windowsize[1] - position[1]
        return position

    # 将窗口上的坐标映射到地图某个坐标
    def window2map(self, position):
        scale = self.maplong / self.windowsize[0] / (1 + times)
        position[1] = self.windowsize[1] - position[1]
        position[0] *= scale
        position[1] *= scale
        position[0] += (self.xrange[0] - translatex * scale * 50)
        position[1] += (self.yrange[0] - translatey * scale * 50)
        return position


    #查找对应单元的图片位于哪个目录下
    def find_img_path(self, side, icon):
        path = __file__[:-7] + "img/" +side
        dirs = os.listdir(path)
        picname = icon + ".png"
        for file in dirs:
            if file == picname:
                return path + "/" + picname
        return path + "/" + side + ".png"


    #将地图的某一边切分成比较整的数，返回在某点切分组成的列表
    def devision(self, length):
        div_list = []
        a = int(str(length)[:2])
        lenzero = pow(10, len(str(length)) - 2)
        if a >= 10 and a < 30:
            for i in range(a):
                div_list.append(i * lenzero)
        elif a >= 30 and a < 50:
            num = a // 5 + int(a % 5 != 0)
            for i in range(num):
                div_list.append(i * 5 * lenzero)
        else:
            num = a // 10 + int(a % 10 != 0)
            for i in range(num):
                div_list.append(i * lenzero * 10)
        if div_list[-1] != length:
            div_list.append(length)
        return div_list


    #对显示窗口画一些边框，考虑到显示窗口不是一个正方形
    def show_border(self):
        block_x = self.devision(self.maplong)
        for i in range(len(block_x)):
            block_x[i] += self.xrange[0]
        block_y = self.devision(self.mapwidth)
        for i in range(len(block_y)):
            block_y[i] += self.yrange[0]

        for i in range(len(block_x)):
            pygame.draw.line(self.screen, gray, self.map2window([block_x[i], block_y[0]]), self.map2window([block_x[i], block_y[-1]]), 1)
        for i in range(len(block_y)):
            pygame.draw.line(self.screen, gray, self.map2window([block_x[0], block_y[i]]), self.map2window([block_x[-1],block_y[i]]), 1)


    #在指定位置显示一些消息
    def show_message(self, message, position, size, color=red):
        fontpath = __file__[:-7] + "simhei.ttf"
        text = pygame.font.Font(fontpath, size)
        text_render = text.render(message, True, white, color)
        pos = [position[0] - text_render.get_width() / 2, position[1] - text_render.get_height()/2 ]
        self.screen.blit(text_render, pos)


    #将一个单位的一些东西进行输出
    def show_unit(self, unit):
        name = unit['name']
        icon = unit['icon']
        pos = unit['position']
        side = unit['side']

        angle = unit.get('angle', 0)
        arc = unit.get('arc', 0)
        id = unit.get('id',-1)
        cirsize = unit.get('cirsize', 0)

        # 将坐标进行转换，找到对应图标的位置
        pos = self.map2window(pos)
        img_path = self.find_img_path(side, icon)

        # 绘制图标，判断是否需要旋转，生成新的旋转后的图标，然后再进行绘制
        # 如果需要有侦察范围的话，再在外面画个圈
        img = pygame.image.load(img_path).convert_alpha()
        imgwidth = img.get_width()
        imgheight = img.get_height()
        pos = [pos[0] - imgwidth / 2, pos[1] - imgheight / 2]
        if angle != 0:
            img = pygame.transform.rotate(img, angle)
        self.screen.blit(img, pos)
        if cirsize:
            pygame.draw.circle(self.screen, red, pos, cirsize, 1)
        if arc:
            pygame.draw.arc(self.screen, black, [pos[0],pos[1]-5,200,200],0,math.pi,1)

        # 在对应图标上显示该单位的 name 和 id
        if id == -1:
            tmp = name
        else:
            tmp = name + "-" + str(id)
        self.show_message(tmp, (pos[0]+imgwidth/2, pos[1] - imgheight/2+12), 14, color=red if side=='red' else blue)


    # 实时显示鼠标位置
    def show_mouse_pos(self):
        [mx, my] = self.window2map(pygame.mouse.get_pos())
        [mx, my] = [int(mx), int(my)]
        self.show_message(str([mx, my]), [x, y], 15)


    def show(self, obs, message_list = []):
        #self.screen.fill(white)
        self.screen.blit(self.bg, (0,0))
        self.show_border()
        self.show_mouse_pos()

        #在窗口右上角显示一些别的自己想要输出的信息
        for i in range(len(message_list)):
            self.show_message(message_list[i], [self.windowsize[0]*0.7, self.windowsize[1]*0.05 + i * 20], 15)

        #显示每个单位
        for unit in obs:
            self.show_unit(unit)

        #可以让你点击窗口上的关闭来结束，按下 空格键 进行全屏转换，方向键会使地图进行移动，按下 q 键会使地图放大， w 会缩小
        for event in pygame.event.get():
            global fullscreen, times, translatex, translatey
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_SPACE:
                fullscreen = not fullscreen
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    times += 0.1
                elif event.button == 5:
                    if times >= -0.5:
                        times -= 0.1
            if event.type == pygame.KEYDOWN:
                if event.key == K_DOWN:
                    translatey -= 1
                elif event.key == K_UP:
                    translatey += 1
                elif event.key == K_LEFT:
                    translatex -= 1
                elif event.key == K_RIGHT:
                    translatex += 1
                elif event.key == K_w:
                        times += 0.1
                elif event.key == K_s:
                    if times >= -0.5:
                        times -= 0.1

        #进行窗口界面的更新
        pygame.display.update()
