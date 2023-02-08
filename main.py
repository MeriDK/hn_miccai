import wandb

import torch
from torch.nn import BCEWithLogitsLoss
from torch.utils.data import DataLoader
from torchvision import transforms

from utils import build_model
from dataset import KidneyDataset
from trainer import Trainer


def run_experiment(model_name, pretrained):

    # set up random seed for reproducibility
    torch.manual_seed(42)

    # set up augmentation
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomRotation(degrees=(-30, 30)),
            transforms.RandomResizedCrop(224, ratio=(1.0, 1.0), scale=(0.9, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ]),
    }

    # all changeable parameters should be specified here
    wandb.config.update({
        'batch_size': 32,
        'num_epochs': 50,
        'threshold': 0.5,
        'loss': 'BCE',
        'model_name': model_name,   # 'swin'/'vit' + '_'  + 'small', 'tiny', 'base' || 'resnet' + '18'/'50'
        'lr': 10 ** -5,
        'weight_decay': 0.1,
        'freeze': False,
        'freeze_until': 'layer3',
        'device': 'cuda',
        'pretrained': pretrained,
        'data_transforms': data_transforms
    })

    # setup model
    model = build_model(wandb.config)
    model = model.to(wandb.config['device'])

    # create train and valid datasets
    train_dataset = KidneyDataset('SickKids_train.csv', data_transforms['train'])
    valid_dataset = KidneyDataset('SickKids_valid.csv', data_transforms['train'])

    # pass datasets to pytorch loaders
    train_loader = DataLoader(train_dataset, batch_size=wandb.config['batch_size'])
    valid_loader = DataLoader(valid_dataset, batch_size=wandb.config['batch_size'])

    # set up loss function
    if wandb.config['loss'] == 'BCE':
        criterion = BCEWithLogitsLoss()
    else:
        raise NotImplementedError(f'Unknown loss')

    # set up optimizer
    optimizer = torch.optim.Adam(params=model.parameters(), lr=wandb.config['lr'],
                                 weight_decay=wandb.config['weight_decay'])

    # create and run trainer
    Trainer(config=wandb.config, model=model, criterion=criterion, optimizer=optimizer).run(
        train_loader, valid_loader
    )


if __name__ == '__main__':

    # init wandb
    wandb.init(project="hn_miccai", entity="meridk")

    # 'resnet18/50/152' 'swin_small/tiny/base' 'vit_small/tiny/base'
    run_experiment(model_name='vit_tiny', pretrained=True)

    # explicitly end wandb
    wandb.finish()