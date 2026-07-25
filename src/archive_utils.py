"""
Archive & Compression utilities for weg.
Supports background zip, tar.gz creation, and extraction.
"""

import os
import zipfile
import tarfile

def create_zip_archive(target_paths, output_zip_path):
    output_zip_path = os.path.abspath(output_zip_path)
    if not output_zip_path.endswith('.zip'):
        output_zip_path += '.zip'

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in target_paths:
            if not os.path.exists(p):
                continue
            if os.path.isdir(p):
                base_dir = os.path.dirname(p)
                for root, dirs, files in os.walk(p):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, base_dir)
                        zf.write(full_path, rel_path)
            else:
                zf.write(p, os.path.basename(p))

    return output_zip_path

def create_tar_archive(target_paths, output_tar_path):
    output_tar_path = os.path.abspath(output_tar_path)
    if not output_tar_path.endswith(('.tar.gz', '.tgz')):
        output_tar_path += '.tar.gz'

    with tarfile.open(output_tar_path, 'w:gz') as tf:
        for p in target_paths:
            if not os.path.exists(p):
                continue
            arcname = os.path.basename(p)
            tf.add(p, arcname=arcname)

    return output_tar_path

def extract_archive(archive_path, dest_dir):
    archive_path = os.path.abspath(archive_path)
    dest_dir = os.path.abspath(dest_dir)

    if archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zf:
            zf.extractall(dest_dir)
        return True, f"Extracted ZIP '{os.path.basename(archive_path)}'"
    elif archive_path.endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tar.xz', '.tar')):
        with tarfile.open(archive_path, 'r:*') as tf:
            tf.extractall(dest_dir)
        return True, f"Extracted TAR archive '{os.path.basename(archive_path)}'"

    return False, f"Unsupported archive format '{archive_path}'"
