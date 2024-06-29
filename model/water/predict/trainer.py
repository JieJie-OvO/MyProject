from getdata import WaterDataset, getdata_from_xlsx
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
from ResMLP import ResMLP



def trainer(path, filepath, in_dim=7, out_dim=5,epochs=100, device='cpu',lr = 0.01, load=False):
    model = ResMLP(in_dim, out_dim)
    if load:
        model.load_state_dict(torch.load(path))
    model = model.to(device)
    model.train()
    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.5)
    criterion = nn.CrossEntropyLoss()
    criterion = criterion.to(device)

    datas = getdata_from_xlsx(filepath)
    waterdataset = WaterDataset(datas)
    dataloader = DataLoader(waterdataset, batch_size=16, shuffle=True)
    for i in range(epochs):
        total_loss = 0
        for step, onedata in enumerate(dataloader):
            data,target = onedata
            # print(target)
            # print(data)
            data = data.to(device)
            target = target.to(device)
            optimizer.zero_grad()
            output = model(data)

            loss = criterion(output, target)
            total_loss += loss.item()
            loss.backward()  
            optimizer.step()

        print("finish:{}    Loss:{}".format(i, total_loss/len(dataloader)))
    torch.save(model.state_dict(),path)

def test(path, filepath, in_dim=7, out_dim=5, device='cpu'):
    model = ResMLP(in_dim, out_dim)
    model.load_state_dict(torch.load(path))
    model = model.to(device)
    model.eval()
    datas = getdata_from_xlsx(filepath)
    waterdataset = WaterDataset(datas)
    dataloader = DataLoader(waterdataset, batch_size=16, shuffle=False)
    correct = 0
    total = 0
    for step, onedata in enumerate(dataloader):
        data,target = onedata
        data = data.to(device)
        target = target.to(device)
        output = model(data)
        pred = output.data.max(1)[1]
        # print(pred)
        # print(target)
        total += target.size(0)
        correct += pred.eq(target.data).cpu().sum()
    print('Accuracy of the network on the test data: %d %%' % (100 * correct / total))