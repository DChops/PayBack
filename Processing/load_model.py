import torch
import torch
import torch.nn.functional as F
from torch.nn import Softmax, Linear
from torch_geometric.nn import SAGEConv, global_max_pool
from torch_geometric.transforms import ToUndirected
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
import networkx
import numpy as np
import torch

def load_model(model_path="mod.pt"):
    PATH = model_path
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = Net(310, [256, 256, 64, 32, 32], 4).to(device)
    model.load_state_dict(torch.load(PATH,map_location=device))
    model.eval()

    return model


class Net(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(Net, self).__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels[0])
        self.conv2 = SAGEConv(hidden_channels[0], hidden_channels[1])
        self.conv3 = SAGEConv(hidden_channels[1], hidden_channels[2])

        self.full1 = Linear(hidden_channels[2], hidden_channels[3])
        self.full2 = Linear(hidden_channels[3], hidden_channels[4])
        self.softmax = Linear(hidden_channels[4], out_channels)

        self.lin_news = Linear(in_channels, out_channels)

        self.lin_cat = Linear(2 * out_channels, 1)

    def forward(self, x, edge_index, batch):
        h = self.conv1(x, edge_index).relu()
        h = self.conv2(h, edge_index).relu()
        h = self.conv3(h, edge_index).relu()

        h = global_max_pool(h, batch)

        h = self.full1(h).relu()
        h = self.full2(h).relu()
        h = self.softmax(h).relu()

        ### For the root node (article) features
        root = (batch[1:] - batch[:-1]).nonzero(as_tuple=False).view(-1)
        root = torch.cat([root.new_zeros(1), root + 1], dim=0)
        news = x[root]
        news = self.lin_news(news).relu()

        output = self.lin_cat(torch.cat([h, news], dim=-1))

        return torch.sigmoid(output)

def get_processed_data(graph):
    node = list(graph.nodes)
    node.remove(0)
    fro = np.array([i[0] for i in graph.edges])
    to = np.array([i[1] for i in graph.edges])
    replacements={}
    replacements[0] = 0

    for i in range(0,len(node)):
        replacements[node[i]] = i+1
    
    for i in range(len(fro)):
        fro[i] = float(replacements[fro[i]])
        to[i] = float(replacements[to[i]])
    edge_index=torch.from_numpy(np.array([fro,to]))

    return edge_index.type(torch.long)

def predict_all(model,data,edge_index):

    data = Data(x=data.type(torch.float32),edge_index=edge_index)
    test = DataLoader([data],batch_size=1,shuffle=False)
    for d in test:
        soln = torch.reshape(predict(model=model,data=d),(-1,))

    return soln
    

@torch.no_grad()
def predict(model,data):
  return model(data.x,data.edge_index,data.batch)
