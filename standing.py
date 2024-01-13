import os
import json
import glob
import copy
import bisect

SCENE_FRAMES_RANGE = range(501)


def load_json(filename):
    with open(filename, 'r') as fh:
        data = json.load(fh)
    return data


def save_json(data, filename):
    with open(filename, 'w') as fh:
        json.dump(data, fh, indent=3)


def search_bbox(labels: list, obj_id: int) -> dict:
    """
    根据指定的object id搜索bbox。二分法搜索。.
    """
    index = len(labels) // 2

    if obj_id == int(labels[index]['obj_id']):
        return labels[index]

    if obj_id < int(labels[index]['obj_id']):
        return search_bbox(labels[:index], obj_id)
    else:
        return search_bbox(labels[index:], obj_id)


def insert_bbox(labels, obj_ids, obj_id, inserted_bbox):
    """把bbox按id顺序插入labels中"""
    insert_index = bisect.bisect_left(obj_ids, obj_id)
    labels.insert(insert_index, inserted_bbox)
    obj_ids.insert(insert_index, obj_id)


def add_standing_bbox(label_dir: str,
                      frame_id: int,
                      anchor_bbox: dict) -> None:
    """
    向指定帧中添加静态bbox。
    """
    filename = os.path.join(label_dir, str(frame_id).zfill(6) + '.json')
    labels = load_json(filename)
    obj_id = int(anchor_bbox['obj_id'])
    obj_ids = [int(obj['obj_id']) for obj in labels]
    if obj_id in obj_ids:
        obj_index = obj_ids.index(obj_id)
        labels[obj_index] = anchor_bbox
    else:
        insert_bbox(labels, obj_ids, obj_id, anchor_bbox)

    save_json(labels, filename)


def set_standing(label_dir: str,
                 obj_id: int,
                 starting_fr: int,
                 ending_fr: int,
                 anchor_fr: int = -1) -> None:
    # starting_fr/ending_fr: 静止object的标的帧。
    if anchor_fr == -1:
        anchor_fr = starting_fr
    filename = os.path.join(label_dir, str(anchor_fr).zfill(6) + '.json')

    anchor_bbox = search_bbox(load_json(filename), obj_id)
    if 'annotator' in anchor_bbox:
        anchor_bbox.pop('annotator')

    for frame_id in range(starting_fr, ending_fr + 1):
        add_standing_bbox(label_dir, frame_id, anchor_bbox)

    print(f'Add static bboxes for OBJECT {obj_id} from FRAME {starting_fr} to {ending_fr}.')


def del_bboxs(label_dir: str,
             obj_id: int,
             starting_fr: int,
             ending_fr: int) -> None:
    """删除连续帧中的指定object"""
    for frame_id in range(starting_fr, ending_fr + 1):
        filename = os.path.join(label_dir, str(frame_id).zfill(6) + '.json')
        labels = load_json(filename)
        obj_ids = [int(obj['obj_id']) for obj in labels]
        if obj_id in obj_ids:
            labels.pop(obj_ids.index(obj_id))

        save_json(labels, filename)

    print(f'Delete bboxes of OBJECT {obj_id} from FRAME {starting_fr} to {ending_fr}.')


def finalize_obj(label_dir: str, obj_id: int) -> None:
    pass


def align_height(label_dir: str,
                 obj_id: int,
                 starting_fr: int,
                 ending_fr: int,
                 anchor_fr: int = -1) -> None:
    if anchor_fr == -1:
        anchor_fr = starting_fr
    filename = os.path.join(label_dir, str(anchor_fr).zfill(6) + '.json')

    anchor_bbox = search_bbox(load_json(filename), obj_id)
    z = anchor_bbox['psr']['position']['z']

    for frame_id in range(starting_fr, ending_fr + 1):
        filename = os.path.join(label_dir, str(frame_id).zfill(6) + '.json')
        labels = load_json(filename)
        for obj in labels:
            if int(obj['obj_id']) == obj_id:
                obj['psr']['position']['z'] = z
                break
        save_json(labels, filename)

    print(f'Align height of OBJECT {obj_id} from FRAME {starting_fr} to {ending_fr}.')


def align_rotation(label_dir: str,
                   obj_id: int,
                   starting_fr: int,
                   ending_fr: int,
                   anchor_fr: int = -1) -> None:
    if anchor_fr == -1:
        anchor_fr = starting_fr
    filename = os.path.join(label_dir, str(anchor_fr).zfill(6) + '.json')

    anchor_bbox = search_bbox(load_json(filename), obj_id)
    rotation = (anchor_bbox['psr']['rotation']['x'],
                anchor_bbox['psr']['rotation']['y'],
                anchor_bbox['psr']['rotation']['z'])

    for frame_id in range(starting_fr, ending_fr + 1):
        filename = os.path.join(label_dir, str(frame_id).zfill(6) + '.json')
        labels = load_json(filename)
        for obj in labels:
            if int(obj['obj_id']) == obj_id:
                (obj['psr']['rotation']['x'],
                 obj['psr']['rotation']['y'],
                 obj['psr']['rotation']['z']) = rotation
                break
        save_json(labels, filename)

    print(f'Align rotation of OBJECT {obj_id} from FRAME {starting_fr} to {ending_fr}.')


def align_size(label_dir: str,
               obj_id: int,
               starting_fr: int,
               ending_fr: int,
               anchor_fr: int = -1) -> None:
    if anchor_fr == -1:
        anchor_fr = starting_fr
    filename = os.path.join(label_dir, str(anchor_fr).zfill(6) + '.json')

    anchor_bbox = search_bbox(load_json(filename), obj_id)
    size = (anchor_bbox['psr']['scale']['x'],
                anchor_bbox['psr']['scale']['y'],
                anchor_bbox['psr']['scale']['z'])

    for frame_id in range(starting_fr, ending_fr + 1):
        filename = os.path.join(label_dir, str(frame_id).zfill(6) + '.json')
        labels = load_json(filename)
        for obj in labels:
            if int(obj['obj_id']) == obj_id:
                (obj['psr']['scale']['x'],
                 obj['psr']['scale']['y'],
                 obj['psr']['scale']['z']) = size
                break
        save_json(labels, filename)

    print(f'Align size of OBJECT {obj_id} from FRAME {starting_fr} to {ending_fr}.')


def merge(label_dir, main_obj_id, mgd_obj_id):
    for frame_id in SCENE_FRAMES_RANGE:
        filename = os.path.join(label_dir, str(frame_id).zfill(6) + '.json')
        labels = load_json(filename)
        obj_ids = [int(obj['obj_id']) for obj in labels]
        if mgd_obj_id in obj_ids:
            mgd_obj_pos = obj_ids.index(mgd_obj_id)
            obj_ids.pop(mgd_obj_pos)
            mgd_obj = labels.pop(mgd_obj_pos)
            if main_obj_id not in obj_ids:
                mgd_obj['obj_id'] = str(main_obj_id)
                insert_bbox(labels, obj_ids, main_obj_id, mgd_obj)

            save_json(labels, filename)

    print(f'Merge OBJECT {main_obj_id} with OBJECT {mgd_obj_id}.')



if __name__=="__main__":
    # label_dir = os.path.join('koko', 'MAPATHON', 'measurement4_0', 'label')
    label_dir = os.path.join('data', 'measurement4_0_3', 'label')
    # label_path = os.path.join(label_dir, '000009.json')
    # labels = load_json(label_path)[:10]

    # print(labels)

    # obj_id = 3425
    # starting_fr = 90
    # ending_fr = 193
    # del_bboxs(label_dir = label_dir,
    #           obj_id = obj_id,
    #           starting_fr = starting_fr,
    #           ending_fr = ending_fr)

    obj_id = 301
    starting_fr = 176
    ending_fr = 219
    anchor_fr = 220

    set_standing(label_dir=label_dir, obj_id=obj_id, starting_fr=starting_fr, ending_fr=ending_fr, anchor_fr=anchor_fr)

    # align_height(label_dir=label_dir, obj_id=obj_id, starting_fr=starting_fr, ending_fr=ending_fr, anchor_fr=anchor_fr)

    # align_rotation(label_dir=label_dir, obj_id=obj_id, starting_fr=starting_fr, ending_fr=ending_fr, anchor_fr=anchor_fr)

    # align_size(label_dir=label_dir, obj_id=obj_id, starting_fr=starting_fr, ending_fr=ending_fr, anchor_fr=anchor_fr)

    # main_obj_id = 6238
    # mgd_obj_id = 548347

    # merge(label_dir, main_obj_id, mgd_obj_id)
