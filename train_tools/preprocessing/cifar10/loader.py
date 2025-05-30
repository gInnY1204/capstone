import torch
import torch.utils.data as data
import torchvision.transforms as transforms
import numpy as np

from .datasets import CIFAR10_truncated


class Cutout:
    def __init__(self, length):
        self.length = length

    def __call__(self, img):
        h, w = img.size(1), img.size(2)
        mask = np.ones((h, w), np.float32)
        y = np.random.randint(h)
        x = np.random.randint(w)

        y1 = np.clip(y - self.length // 2, 0, h)
        y2 = np.clip(y + self.length // 2, 0, h)
        x1 = np.clip(x - self.length // 2, 0, w)
        x2 = np.clip(x + self.length // 2, 0, w)

        mask[y1:y2, x1:x2] = 0.0
        mask = torch.from_numpy(mask)
        mask = mask.expand_as(img)
        img *= mask

        return img


def _data_transforms_cifar10():
    CIFAR_MEAN = [0.49139968, 0.48215827, 0.44653124]
    CIFAR_STD = [0.24703233, 0.24348505, 0.26158768]

    train_transforms = transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(CIFAR_MEAN, CIFAR_STD),
        ]
    )
    train_transforms.transforms.append(Cutout(16))

    valid_transforms = transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.ToTensor(),
            transforms.Normalize(CIFAR_MEAN, CIFAR_STD),
        ]
    )

    return train_transforms, valid_transforms


def get_all_targets_cifar10(root, train=True):
    dataset = CIFAR10_truncated(root=root, train=train)
    all_targets = dataset.targets
    return all_targets


def get_dataloader_cifar10(root, train=True, batch_size=50, dataidxs=None):
    train_transforms, valid_transforms = _data_transforms_cifar10()
    dataset = CIFAR10_truncated(
        root,
        train=train,
        dataidxs=dataidxs,
        transform=train_transforms if train else valid_transforms,
    )
    dataloader = data.DataLoader(
        dataset, batch_size=batch_size, shuffle=True if train else False, num_workers=5
    )

    return dataloader
