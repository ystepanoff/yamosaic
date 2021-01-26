from PIL import Image
import numpy as np
import os
import sys
import random
import imghdr
import argparse


def read_tiles(tiles_dir):
    tiles = []
    for file in os.listdir(tiles_dir):
        path = os.path.abspath(os.path.join(tiles_dir, file))
        try:
            with open(path, 'rb') as f:
                tile = Image.open(f)
                tile.load()
                tiles.append(tile)
        except:
            print('Invalid image file: {}'.format(path))
    return tiles


def get_tile_filenames(tiles_dir):
    filenames = []
    for file in os.listdir(tiles_dir):
        path = os.path.abspath(os.path.join(tiles_dir, file))
        try:
            if imghdr.what(path):
                filenames.append(path)
        except:
            print('Invalid image file: {}'.format(path))
    return filenames


def rgb_average(image):
    img = np.array(image)
    w, h, d = img.shape
    return tuple(np.average(img.reshape(w * h, d), axis=0))


def split_image(image, size):
    W, H = image.size[0], image.size[1]
    m, n = size
    w, h = W // n, H // m

    img_list = []
    for j in range(m):
        for i in range(n):
            img_list.append(image.crop((i * w, j * h, (i + 1) * w, (j + 1) * h)))
    return img_list


def best_index(input_avg, avgs):
    avg = input_avg
    index = 0
    min_index = 0
    min_dist = float('inf')

    for v in avgs:
        dist = sum([(v[i] - avg[i]) ** 2 for i in range(3)])
        if dist < min_dist:
            min_dist = dist
            min_index = index
        index += 1
    return min_index


def create_grid(images, dimensions):
    m, n = dimensions
    assert m * n == len(images)

    w = max([img.size[0] for img in images])
    h = max([img.size[1] for img in images])

    grid = Image.new('RGB', (n * w, m * h))
    for index in range(len(images)):
        row = index // n
        col = index - n * row
        grid.paste(images[index], (col * w, row * h))
    return grid


def create_mosaic(target, input_images, grid_size, reuse=True):
    print('Splitting the image...')
    target_images = split_image(target, grid_size)

    print('Matching the tiles...')
    output_images = []
    count = 0
    batch_size = len(target_images) // 10

    avgs = []
    for img in input_images:
        avgs.append(rgb_average(img))

    for img in target_images:
        avg = rgb_average(img)
        match_index = best_index(avg, avgs)
        output_images.append(input_images[match_index])
        
        if count > 0 and batch_size > 10 and count % batch_size == 0:
            print('Processed {0} of {1}...'.format(count, len(target_images)))
            
        count += 1

        if not reuse:
            input_images.remove(match)

    print('Creating mosaic...')
    return create_grid(output_images, grid_size)


def main():
    parser = argparse.ArgumentParser(description='Yet another photomosaic creator.')
    parser.add_argument('--target-image', dest='target_image', required=True)
    parser.add_argument('--tiles-dir', dest='tiles_dir', required=True)
    parser.add_argument('--grid-size', nargs=2, dest='grid_size', required=True)
    parser.add_argument('--output-file', dest='output_file', required=False)

    args = parser.parse_args()

    target_image = Image.open(args.target_image)

    print('Reading tiles...')
    tiles = read_tiles(args.tiles_dir)
    if tiles == []:
        print('Could not find any image tiles in {}. Aborting.'.format(args.tile_dir))
        exit()

    random.shuffle(tiles)
    grid_size = (int(args.grid_size[0]), int(args.grid_size[1]))

    output_file = args.output_file if args.output_file else 'output.png'

    reuse_tiles = True
    
    resize_input = True

    print('Creating mosaic...')
    if not reuse_tiles:
        if grid_size[0] * grid_size[1] > len(tiles):
            print('Grid size is less than the number of images. Aborting')
            exit()

    if resize_input:
        print('Scaling the tiles...')
        dim = (target_image.size[0] // grid_size[1], target_image.size[1] // grid_size[0])
        print('Maximal tile dimensions: ({0}, {1}).'.format(dim[0], dim[1]))
        for img in tiles:
            img.thumbnail(dim)

    mosaic = create_mosaic(target_image, tiles, grid_size, reuse_tiles)
    mosaic.save(output_file, 'PNG')

    print('Saved output to {}.'.format(output_file))
    print('Done.')


if __name__ == '__main__':
    main()
