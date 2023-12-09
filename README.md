# Dependency

- BlenderProc [https://github.com/DLR-RM/BlenderProc]()

## How to use

1. Rendering image first.
```
blenderproc run render_robot.py
```

2. Label the image
```
python joint_label.py
```


## Trouble Shoot

1. If install `yurdfpy` has problem, check this [https://blender.stackexchange.com/questions/81740/python-h-missing-in-blender-python]()


## Limitation
1. We currently only support 1 layer of link.