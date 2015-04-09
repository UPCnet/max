# -*- coding: utf-8 -*-
import os
import re


EXIF_ROTATIONS = {
    3: 180,
    6: -90,
    8: -270
}


def rotate_image_by_EXIF(image):
    """
        Images with rotation will have a value in field 274. If we don't know how much
        we have to rotate or we don't have the value, will make no changes to the image.
    """
    exif_data = image._getexif() if hasattr(image, '_getexif') else {}
    exif_rotation_identifier = exif_data.get(274, None) if isinstance(exif_data, dict) else None
    exif_rotation = EXIF_ROTATIONS.get(exif_rotation_identifier, 0)

    if exif_rotation:
        return image.rotate(exif_rotation)
    return image


SPLITTERS = {
    'people': re.compile(r'^(.{2})'),
    'contexts': re.compile(r'^(.{2})(.{2})(.{2})')
}


def get_avatar_folder(base_folder, context='', identifier='', size=''):
    """
        Returns the right folder for the given parameters set, and
        creates the folder if is missing.
    """
    id_splitter = SPLITTERS.get(context)

    if id_splitter:
        match = id_splitter.search(identifier)
        splitter_parts = match.groups() if match else []
    else:
        splitter_parts = []

    avatar_path_parts = [
        base_folder,
        context, size
    ]

    avatar_path_parts.extend(splitter_parts)

    avatar_path = os.path.join(*avatar_path_parts)

    if not os.path.exists(avatar_path):
        os.makedirs(avatar_path)
    return avatar_path.rstrip('/')
