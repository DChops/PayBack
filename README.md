# PayBack
Fake News Detection as a Service, built with the State-Of-The-Art User Preference Aware GNNs

## Datasets
We utilised the Politifact & Gossicop Datasets available publicly using the UPFD() class in pytorch_geometric.datasets.

A brief summary of the datasets is as follows:
| Data  | #Graphs  | #Fake News| #Total Nodes  | #Total Edges  | #Avg. Nodes per Graph  |
|-------|--------|--------|--------|--------|--------|
| Politifact | 314   |   157    |  41,054  | 40,740 |  131 |
| Gossipcop |  5464  |   2732   |  314,262  | 308,798  |  58  |

## Research Papers Referenced
<ul>
  <li> Yingtong Dou et al., "User Preference Aware Fake News Detection", July 2021, Retrieved via: https://arxiv.org/abs/2104.12259
  <li> Yi Han et al., "Graph Neural Networks with Continual Learning for Fake News Detection from Social Media", August 2020, Retrieved via: https://arxiv.org/abs/2007.03316
  <li> Rex Ying et al., "Hierarchical Graph Prepresentation Learning with Differentiable Pooling", Feb 2019, Retrieved via: https://arxiv.org/abs/1806.08804
<ul>
