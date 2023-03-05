import time
import pygame
import os
from .const import white, gray, green, blue, red, black
from .const import ScaleCoff
from .const import LibPath
from .const import ICON_SIZE

class ScreenProcessor:
    def __init__(self, screen, range_x, range_y, window_size, tcolor=black, bg_img=None):
        self.tcolor = tcolor
        self.screen = screen
        self.bg_img = bg_img
        self.origin_x = range_x
        self.origin_y = range_y
        self.window_size = window_size
        self.scale_k = (range_x[1] - range_x[0]) / self.window_size[0]
        self.scale = 1.0
        self.mouse_moving = False
        self.mlast_pos = None

        self.icon_size = ICON_SIZE

        self.range_x = range_x
        self.range_y = range_y
        self.scale_fix()
        self.init_image()
        self.init_text()

    def scale_fix(self):
        self.x_bias, self.map_width = self.range_x[0], self.range_x[1] - self.range_x[0]
        self.y_bias, self.map_height = self.range_y[0], self.range_y[1] - self.range_y[0]
        self.display_width , self.display_height = self.window_size
        self.x_fix = lambda x : (x - self.x_bias) / self.map_width * self.display_width
        self.y_fix = lambda x : ( 1 - (x - self.y_bias) / self.map_height ) * self.display_height
        self.x_unfix = lambda x : x / self.display_width * self.map_width + self.x_bias
        self.y_unfix = lambda x : (1 - x / self.display_height) * self.map_height + self.y_bias
        self.scale_k = (self.range_x[1] - self.range_x[0]) / self.window_size[0]
        if self.bg_img:
            self.background = pygame.transform.scale(self.bg_img, [ i / self.scale for i in self.window_size])

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

    def fix_screen_by_mouse(self, text_size=12):
        pos = pygame.mouse.get_pos()
        #print('mouse is in ', pos)
        [mx, my] = self.to_map(pos)
        message = f"{int(mx)}, {int(my)}"
        text_render = self.text[text_size].render(message, True, self.tcolor)
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

    def init_image(self):
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
        # sfc_infos.append([img, img_pos])
        self.screen.blit(img, img_pos)

        # 名称
        message = f"{name}-{uid}" if name and uid!=-1 else name if name else ""
        text_render = self.text[fontsize].render(message, True, self.tcolor)
        text_width, text_height = text_render.get_width(), text_render.get_height()
        tpos = [pos[0] - text_width / 2, pos[1] - img_height / 2 - text_height ]
        # sfc_infos.append([text_render, tpos])
        self.screen.blit(text_render, tpos)
        #self.screen.draw.text(message, img_pos)

        # 圆圈
        if cirsize:
            pygame.draw.circle(self.screen, blue if side == 'blue' else red , pos, cirsize/self.scale_k, 3)

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


def bye(signum, frame):
    print("Bye Bye")
    exit()

def pipeline(queue, config):
    import signal
    signal.signal(signal.SIGTERM, bye)

    try :
        range_x = config["range_x"]
        range_y = config["range_y"]
        display_size = config.get("display_size", [800, 600])
    except Exception as e:
        raise Exception("Please Point the Maps Limit and Display Size")

    while True:
        if queue.empty():
            time.sleep(.01)
        else:
            break
    pygame.init()
    clock = pygame.time.Clock()

    #pygame.mouse.set_visible(False)
    windowSize = [800, 800] #generator.gen_winsize(config)      # 窗口大小处理
    screen = pygame.display.set_mode(display_size)    # 创建screen
    pygame.display.set_caption("PipeLine")          # 指定display的title

    bg_path = config.get("bg_img", None)
    try :
        bg_img = None if not bg_path else pygame.image.load(bg_path)
    except Exception as e:
        bg_img = None
        print(f"Load Back Image Failed! path: [{bg_path}]")

    tcolor = config.get("tcolor", black)
    fontsize = config.get("fontsize", 12)
    processor = ScreenProcessor(screen, range_x, range_y, display_size, tcolor, bg_img)

    old_obs, obs = None, None
    now_tick = 0 
    try:
        while True:
            now_tick += 1 
            clock.tick_busy_loop(200)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        processor.scale_magnify()
                    elif event.button == 5:
                        processor.scale_minify()
                    elif event.button == 1:
                        processor.mouse_moving = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    processor.mouse_moving = False

            if not queue:
                print('Error : queue is None')
                exit()
            elif queue.empty():
                pass 
            else:
                obs = queue.get()
            processor.fix_screen_bg()
            # processor.fix_mouse_img()
            processor.fix_move()
            processor.fix_screen_by_obs(obs)
            processor.fix_screen_by_mouse()
            pygame.display.flip()
            if now_tick % 100 == 0:
                fps = clock.get_fps()
                print(f'fps is {fps} , tick is {now_tick} ')
    except Exception as e:
        print(f"Exception : \n{e}")
        exit()
    print('pipeline Over')


if '__main__' == __name__:
    from multiprocessing import SimpleQueue, Queue, Process
    queue = Queue()
    config = {
        "range_x": [0, 1000],
        "range_y": [0, 1000],
        "display_size": [800, 800]
    }
    #
    #pipeline(queue, config)
    pshow = Process(target=pipeline, args=(queue, config,))
    pshow.damon = True
    pshow.start()
    print("Start Finished")
    times = 0
    while True:
        times+=2
        obs = {
            "units": [
                {
                    "name": "plane",
                    "uid": i,
                    "position": [(times+i*200) %1000, (times+i*300) % 1000],
                    "side": "blue",
                }
                for i in range(5)
            ]
        }
        queue.put(obs)
        time.sleep(.02)
