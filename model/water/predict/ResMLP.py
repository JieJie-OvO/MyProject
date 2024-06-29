import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
import torch.nn.functional as F

class Block(nn.Module):
    def __init__(self, in_dim, out_dim):
        super(Block, self).__init__()
        self.mlp = nn.Sequential(
            nn.Linear(in_dim, out_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

    def forward(self, x):
        x = self.mlp(x)
        return x

class ResMLP(nn.Module):
    def __init__(self, in_dim = 9, out_dim = 5):
        super(ResMLP, self).__init__()

        self.mlp = nn.Sequential(
            Block(in_dim, 14),
            Block(14, 28),
            nn.Linear(28,out_dim)
        )
    
    def forward(self,x):
        x = self.mlp(x)
        return F.softmax(x, dim=1)