import time
import os
import pygame
import math
from .const import white, gray, green, blue, red, black
from .const import ScaleCoff
from .const import LibPath
from .const import ICON_SIZE

class ScreenProcessor:
    def __init__(self, queue, config):
        self.queue = queue
        self.obs = {}
        self.display_size = config.get("display_size", (1600, 900))
        self.screen = pygame.display.set_mode(self.display_size)      # 创建screen

        self.clock = pygame.time.Clock()

        # 字体设置
        self.text_color      = config.get("text_color", black)
        self.font_size       = config.get("fontsize", 15)

        # 加载背景图片
        self.bg_path         = config.get("bg_img", None)
        self.bg_img          = self.load_img(self.bg_path)

        # 经纬度坐标转换
        self.central_lon     = config.get("central_lon", None)
        self.central_lat     = config.get("central_lat", None)

        # 缩放管理
        self.origin_x = config["range_x"]
        self.origin_y = config["range_y"]
        self.scale = 1.0
        self.range_x = [self.origin_x[0], self.origin_x[1]]
        self.range_y = [self.origin_y[0], self.origin_y[1]]
        self.scale_k = (self.range_x[1] - self.range_x[0]) / self.display_size[0]
        
        # 鼠标
        self.mouse_moving = False
        self.mlast_pos = None

        # 图标默认大小
        self.icon_size = ICON_SIZE

        # 调整比例
        self.scale_fix()
        # 加载图标
        self.init_icon()
        # 加载字体
        self.init_text()

    def scale_fix(self):
        self.x_bias, self.map_width = self.range_x[0], self.range_x[1] - self.range_x[0]
        self.y_bias, self.map_height = self.range_y[0], self.range_y[1] - self.range_y[0]
        self.display_width , self.display_height = self.display_size
        self.x_fix = lambda x : (x - self.x_bias) / self.map_width * self.display_width
        self.y_fix = lambda x : ( 1 - (x - self.y_bias) / self.map_height ) * self.display_height
        self.x_unfix = lambda x : x / self.display_width * self.map_width + self.x_bias
        self.y_unfix = lambda x : (1 - x / self.display_height) * self.map_height + self.y_bias
        self.scale_k = (self.range_x[1] - self.range_x[0]) / self.display_size[0]
        if self.bg_img:
            self.background = pygame.transform.scale(self.bg_img, [ i / self.scale for i in self.display_size])

    def scale_magnify(self):
        if self.scale < .1:
            return
        self.scale *= ScaleCoff
        pos = pygame.mouse.get_pos()
        x, y = self.to_map(pos)

        xl = x - (x - self.x_bias)  * ScaleCoff
        xr = xl + self.map_width * ScaleCoff

        yl = y - (y - self.y_bias) * ScaleCoff
        yr = yl + self.map_height * ScaleCoff

        self.range_x = [xl, xr]
        self.range_y = [yl, yr]
        self.scale_fix()

    def scale_minify(self):
        if self.scale >= ScaleCoff:
            self.scale = 1.0
            self.range_x = [self.origin_x[0], self.origin_x[1]]
            self.range_y = [self.origin_y[0], self.origin_y[1]]
            self.scale_fix()
            return

        self.scale /= ScaleCoff
        pos = pygame.mouse.get_pos()
        x, y = self.to_map(pos)

        xl = self.x_bias - ((x - self.x_bias)  / ScaleCoff - (x - self.x_bias))
        xl = max(self.origin_x[0], xl)
        xr = xl + self.map_width / ScaleCoff
        xr = min(self.origin_x[1], xr)
        xl = xr - self.map_width / ScaleCoff

        yl = self.y_bias - (y - self.y_bias)  / ScaleCoff + (y - self.y_bias)
        yl = max(self.origin_y[0], yl)
        yr = yl + self.map_height / ScaleCoff
        yr = min(self.origin_y[1], yr)
        yl = yr - self.map_width / ScaleCoff

        self.range_x = [xl, xr]
        self.range_y = [yl, yr]
        self.scale_fix()

    # 将地图上的坐标映射到窗口上
    def from_map(self, position):
        x = self.x_fix(position[0])
        y = self.y_fix(position[1])
        return [x, y]

    # 将窗口上的坐标映射到地图某个坐标
    def to_map(self, position):
        x = self.x_unfix(position[0])
        y = self.y_unfix(position[1])
        return [x, y]

    # 将地图上的坐标转换为经纬度
    def to_lon_lat(self, position):
        x = position[0]
        y = position[1]
        if not self.central_lat or not self.central_lon:
            return position
        lat = y / 111000 + self.central_lat 
        lon = x / 111000 / math.cos(min(abs(lat), abs(self.central_lat )) * math.pi / 180) + self.central_lon
        return [lon, lat]

    def fix_screen_by_mouse(self, text_size=12):
        pos = pygame.mouse.get_pos()
        map_pos = self.to_map(pos)
        [lon, lat] = self.to_lon_lat(map_pos)
        message = f"({round(lat, 4)}, {round(lon, 4)})"
        text_render = self.text[text_size].render(message, True, self.text_color)
        text_width, text_height = text_render.get_width(), text_render.get_height()
        tpos = [pos[0] - text_width / 2, pos[1] - text_height / 2 ]
        self.screen.blit(text_render, tpos)

    def fix_screen_by_obs(self, obs):
        for unit in obs.get("units", []):
            self.fix_screen_by_unit(unit)
        for unit in obs.get("others", []):
            pass

    def init_text(self):
        fontpath = f"{LibPath}/fonts/msyh.ttc"
        self.text = {fontsize: pygame.font.Font(fontpath, fontsize) for fontsize in range(8, 61)}
        #self.text.set_bold(True)

    def init_icon(self):
        self.dicon = {}
        self.icons = {"red": {}, "blue":{}, "white":{}}
        for side in ['red', 'blue', 'white']:
            pngs = os.listdir(f"{LibPath}/icons/{side}")
            for icon_file in pngs:
                img_path = f"{LibPath}/icons/{side}/{icon_file}"
                icon_name = icon_file.split('.')[0]
                self.icons[side][icon_name] = pygame.image.load(img_path).convert_alpha()
                # self.icons[side][icon_name] = pygame.transform.scale(pygame.image.load(img_path), self.icon_size)
            img_path = f"{LibPath}/icons/{side}/obj.png"
            self.dicon[side] = pygame.transform.scale(pygame.image.load(img_path), self.icon_size)
        self.mouse_cursor = pygame.transform.scale(self.icons['white']['nock'], (15, 15))

    def get_image(self, icon, side):
        return self.icons[side].get(icon, self.dicon[side])

    def fix_screen_by_unit(self, unit):
        name = unit.get('name', '')
        icon = unit.get('icon', name)
        side = unit.get('side', 'white')
        uid = unit.get('uid', -1)
        pos = self.from_map(unit['position'])
        if not self.range_x[0] <= unit['position'][0] <= self.range_x[1] or not self.range_y[0] <= unit['position'][1] <= self.range_y[1]:
            return
        cirsize = unit.get("cirsize", 0)
        rect = unit.get("rect", None)
        iconsize = unit.get('iconsize', -1)
        fontsize = unit.get('textsize',15)
        rotate = 0 - unit.get('course', 0)
        fontsize = min(int(fontsize/(self.scale ** .5)), 60)


        #sfc_infos = []

        # 图标
        img = self.get_image(icon, side)
        if iconsize != -1:
            iconsize = int(iconsize/(self.scale **.5))
            img = pygame.transform.scale(img, (iconsize, iconsize))

        if rotate:
            img = pygame.transform.rotate(img, rotate)

        img_width, img_height= img.get_width(), img.get_height()
        img_pos = [pos[0] - img_width / 2, pos[1] - img_height / 2]
        self.screen.blit(img, img_pos)

        # 名称
        message = f"{name}-{uid}" if name and uid!=-1 else name if name else ""
        text_render = self.text[fontsize].render(message, True, self.text_color)
        text_width, text_height = text_render.get_width(), text_render.get_height()
        tpos = [pos[0] - text_width / 2, pos[1] - img_height / 2 - text_height ]
        self.screen.blit(text_render, tpos)

        # 圆圈
        if cirsize:
            pygame.draw.circle(self.screen, blue if side == 'blue' else red , pos, cirsize/self.scale_k, 1)
        # 矩形
        if rect:
            points = [self.from_map(p) for p in rect]
            pygame.draw.polygon(self.screen, blue if side == 'blue' else red, points, 1)

    def fix_mouse_img(self):
        x, y = pygame.mouse.get_pos()
        #隐藏鼠标
        x -= self.mouse_cursor.get_width() / 2
        y -= self.mouse_cursor.get_height() / 2
        #用其他图形代替鼠标
        self.screen.blit(self.mouse_cursor, (x, y))

    def fix_screen_bg(self):
        if not self.bg_img:
            self.screen.fill(white)
        else:
            pos = self.from_map([self.origin_x[0], self.origin_y[1]])
            self.screen.blit(self.background, pos)

    def fix_move(self):
        if self.mouse_moving == False:
            self.mlast_pos = None
            return
        mpos = pygame.mouse.get_pos()
        if self.mlast_pos != None:
            last_pos = self.to_map(self.mlast_pos)
            pos = self.to_map(mpos)
            dx = last_pos[0] - pos[0]
            dx = min(max(dx, self.origin_x[0] - self.range_x[0]), self.origin_x[1] - self.range_x[1])
            dy = last_pos[1] - pos[1]
            dy = min(max(dy, self.origin_y[0] - self.range_y[0]), self.origin_y[1] - self.range_y[1])

            self.range_x = [i + dx for i in self.range_x]
            self.range_y = [i + dy for i in self.range_y]
            self.scale_fix()

        self.mlast_pos = mpos

    def check_event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:  # 按压按键
                if event.button == 4:   # 滚轮向下
                    self.scale_magnify()
                elif event.button == 5: # 滚轮向上
                    self.scale_minify()
                elif event.button == 1: # 左键
                    self.mouse_moving = True
            elif event.type == pygame.MOUSEBUTTONUP:    # 松开按键
                self.mouse_moving = False

    def update_info(self):
        if not self.queue.empty():
            self.obs = self.queue.get()
        self.fix_screen_bg()
        # processor.fix_mouse_img()
        self.fix_move()
        self.fix_screen_by_obs(self.obs)
        self.fix_screen_by_mouse()
        self.fix_fps()
    
    def fix_fps(self):
        message = f"fps : {self.fps}"
        text_render = self.text[self.font_size].render(message, True, self.text_color)
        tpos = [0,0]
        self.screen.blit(text_render, tpos)
    
    def running(self):
        now_tick = 0
        while True:
            if now_tick % 100 == 0:
                self.fps = int(self.clock.get_fps())
            now_tick += 1 
            self.clock.tick_busy_loop(200)
            self.check_event()
            self.update_info()
            pygame.display.flip()

    @staticmethod
    def load_img(img_path):
        try :
            bg_img = None if not img_path else pygame.image.load(img_path)
        except Exception as e:
            bg_img = None
            print(f"Load Back Image Failed! path: [{img_path}]")
        return bg_img

def bye(signum, frame):
    print("call Bye Bye!!! ")
    exit()

def pipeline(queue, config):
    import signal
    import traceback
    signal.signal(signal.SIGTERM, bye)

    while queue.empty():
        time.sleep(.01)

    pygame.init()
    pygame.display.set_caption("pyshow")              # 指定display的title

    try:
        screen_processor = ScreenProcessor(queue, config)
        screen_processor.running()
    except Exception as e:
        print(f"Exception : \n{e} \n{traceback.format_exc()}")
        import sys
        print("call Sys.exit !!!!!!!")
        sys.exit()
