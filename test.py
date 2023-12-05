import yourdfpy
data_name = '47645'  # '102145', '47645'
data_file = f'test_data/{data_name}/mobility.urdf'

# -------------------------- Utils Functions -------------------------- #


def load_urdfs(fnames, load_fn):
    results = {fname: None for fname in fnames}
    for fname in fnames:
        try:
            x = load_fn(fname)
            results[fname] = x
        except:
            print("Problems loading: ", fname)
            pass
    print(sum([1 for x, y in results.items() if y is not None]), "/", len(fnames))
    return results


def locate_joint_children(urdf, joint_type="revolute"):
    """Locate the child link for all revolute joints in urdf"""
    for joint in urdf.robot.joints:
        if joint.type == joint_type:
            yield joint.child
        elif joint.type == "fixed":
            yield joint.child
        elif joint.type == "prismatic":
            yield joint.child


def build_link_to_visual_map(urdf):
    """Build a map from link name to visual mesh"""
    link_to_visual = {}
    for link in urdf.robot.links:
        if link.name not in link_to_visual:
            link_to_visual[link.name] = []
        for visual in link.visuals:
            link_to_visual[link.name].append(visual.name)
    return link_to_visual


def build_visual_to_link_map(urdf):
    """Build a map from visual name to link name"""
    visual_to_link = {}
    for link in urdf.robot.links:
        for visual in link.visuals:
            visual_to_link[visual.name] = link.name
    return visual_to_link


urdfs = load_urdfs([data_file], yourdfpy.URDF.load)
urdf = urdfs[data_file]

link_to_visual = build_link_to_visual_map(urdf)

for link in locate_joint_children(urdf, joint_type="prismatic"):
    print(link)
