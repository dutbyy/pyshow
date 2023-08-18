from src.api import RenderApi
import random
import time

def rand_gen():
    pos = [random.randrange(0, 1000) for _ in range(4)]
    obs = [
        {
            "name": "飞机" if uid % 2 else "坦克",
            "uid": uid,
            "position": [ random.randrange(400,410)  for _ in range(2)],
            "side": "blue" if uid % 2 else "red",
            "type": "飞机" if uid % 2 else "坦克",
            "icon": "plane" if uid % 2 else "tank",
            "cirsize": 200,
        }
        for uid in range(2)
    ]
    yield {"units": obs}
    dir1 = [0, 0]
    dir2 = [0, 0]
    for _ in range(30):
        for i in range(2):
            obs[i]['position'][0] += 3 * (-1)**(dir1[i] + i)
            if  obs[i]['position'][0] <= 10 or obs[i]['position'][0] >= 990:
                dir1[i] += 1
            obs[i]['position'][1] += 5 * (-1)**(dir2[i] + i)
            if obs[i]['position'][1] >= 790 or  obs[i]['position'][1] <= 10:
                dir2[i] += 1
        yield {"units": obs}

def test_api():
    config = {
        "range_x": [0, 1000],
        "range_y": [0, 800],
        "display_size": [1000, 800],
        #"bg_img": "./map_back.png"
    }
    render = RenderApi(config)
    render.init()
    for i in range(10):
        print(i)
        gen = rand_gen()
        for obs in gen:
            render.update(obs)

if __name__ == '__main__':
    while True:
        try:
            test_api()
            print('t api')
        except:
            time.sleep(.5)
