from LSTM_fish import *

# 超参数
input_size = 3
hidden_size = 100
num_layers = 2
output_size = 2
epochs = 200
lr = 5e-4

model = LSTM(input_size, hidden_size, num_layers, output_size).to(device)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=lr)

def train(X_train,Y_train,epochs=epochs,lr=lr,save=True,index=0):
    X_train, Y_train = X_train.to(device), Y_train.to(device)
    for epoch in range(epochs):
        model.train()
        outputs = model(X_train)
        optimizer.zero_grad()
        loss = criterion(outputs, Y_train)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch + 1}/{epochs}], Loss: {loss.item():.6f}')
    if save:
        if not os.path.exists(SAVE_PATH):
            os.makedirs(SAVE_PATH)
        torch.save(model.state_dict(), f'{SAVE_PATH}/fish_{index}.pth')
    return model

def test(model,X_test,Y_test,scaler_Y):
    X_test, Y_test = X_test.to(device), Y_test.to(device)
    model.eval()
    with torch.no_grad():
        predictions = model(X_test)
        loss = criterion(predictions, Y_test)
        print(f'Test Loss: {loss.item():.6f}')
    # 反归一化预测结果
    predictions = scaler_Y.inverse_transform(predictions.cpu().numpy())
    return predictions

if __name__ == '__main__':
    for i in range(len(TOP3)):
        X_train, Y_train, X_test, Y_test, scaler_x, scaler_y = train_test_split(get_fish_data(TOP3[i]))
        model = train(X_train, Y_train, epochs=epochs, lr=lr, save=True, index=i)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        predictions = test(model, X_test, Y_test,scaler_y)



