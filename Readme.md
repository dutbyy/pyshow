# 机制注意
    1. pyshow 为单开一个子进程，用于开启pygame渲染
    2. 主进程只需要在态势更新时， 使用render.update(data) 更新态势，子进程会更新当前的状态
    3. 目前的帧数为50帧，调用update的频率建议不要超过33(fps)
    
# Windows :
    在linux, ubuntu, windows下均测试通过
    由于使用了multiprocessing
    windows下使用时，请确认使用 (if __name__ == '__main__') 明确指定程序入口. (否则会导致异常)
    


# 使用方式

1. 指定渲染参数
    ```
    config = {
        "range_x": [0, 1000],           // x轴范围
        "range_y": [0, 800],            // y轴范围
        "display_size": [1000, 800],    // 窗口大小
        #"bg_img": "./map_back.png"     // 选填, 背景图片
    }
    ```

2. 创建RenderApi示例, 并初始化
    ```
    render = RenderApi(config)
    render.init()
    ```
    
3. 准备渲染数据
    ```
    units = [
        {
            "name": "Demo"                      // 单位名称
            "uid": 1,                           // 单位id 渲染单位名称-id                        
            "position": [0.0, 0.0],             // 原始态势坐标
            "side": "blue" if True else "red",  // 支持red / blue 用于图标选择
            "icon": "plane",                    // 支持的图标在icons下, 可以自行增加图标(只支持png)
            // "cirsize": 200,                  // 选填, 单位画圈，圈的大小为原始态势大小
        }
    ]
    data = {"units": units}
    ```
4. 更新态势
    ```
    while True:
        # 更新data
        render.update(data)
    ```
