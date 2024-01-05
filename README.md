# Parnet Renderer

We render PartNet Mobility to 2D images to train 2D vision model. Dataset link [https://sapien.ucsd.edu/browse]()

# Dependency

- BlenderProc [https://github.com/DLR-RM/BlenderProc]()

## How to use

1. Adapt the newly downloaded `URDF` file. (Only run it once.)
```
python urdf_fixer.py --data_dir=${data_dir}
```
 
1. Rendering image first.
```
blenderproc run render_robot.py --data_name=${data_id}
```

2. Label the image
```
python joint_label.py --data_name=${data_id}
```

3. Check the result
```
blenderproc vis coco -b output/coco_data/${data_id}/
```

## Trouble Shoot

1. If install `yurdfpy` has problem, check this [https://blender.stackexchange.com/questions/81740/python-h-missing-in-blender-python]()


## Limitation
1. We currently only support 1 layer of link.