import yourdfpy
data_file =  'test_data/102145/mobility.urdf'

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

urdfs = load_urdfs([data_file], yourdfpy.URDF.load)
urdfs[data_file].show()